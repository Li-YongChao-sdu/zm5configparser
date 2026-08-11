import zlib
import lzma
import pyamf
import json
from pyamf.amf3 import ByteArray, DataInput
from pyamf.util import BufferedByteStream
from pyamf import ASObject, UndefinedType
import os
import shutil
from typing import Optional, Set

# ========== 压缩工具 对齐AS ByteArray ==========
class FlashCompress:
    @staticmethod
    def inflate(raw: bytes) -> bytes:
        dec = zlib.decompressobj(wbits=-zlib.MAX_WBITS)
        data = dec.decompress(raw)
        data += dec.flush()
        return data

    @staticmethod
    def uncompress_zlib(raw: bytes) -> bytes:
        return zlib.decompress(raw)

    @staticmethod
    def uncompress_lzma(raw: bytes) -> bytes:
        return lzma.decompress(raw)

# ========== AMF IO工具 ==========
def bytes_to_datainput(data: bytes) -> DataInput:
    stream = BufferedByteStream(data)
    decoded = pyamf.decode(stream)
    return DataInput(decoded)

def read_amf_object(data: bytes) -> Optional[ASObject]:
    try:
        di = bytes_to_datainput(data)
        return di.readObject()
    except Exception:
        return None

# ========== 修复递归：增加访问缓存，阻断循环引用 ==========
def amf_to_plain(obj, visited: dict = None):
    # visited: key=对象内存id, value=业务node.id
    if visited is None:
        visited = dict()
    obj_mem_id = id(obj)

    # 如果已经见过这个内存对象，返回引用标记，保留真实业务id
    if obj_mem_id in visited:
        return {"$ref": visited[obj_mem_id]}

    if isinstance(obj, pyamf.ASObject):
        res = {}
        # 优先取出业务id
        node_biz_id = obj.get("id")
        if node_biz_id is not None:
            visited[obj_mem_id] = node_biz_id
        
        for k, v in obj.items():
            if k == "parent":
                continue
            res[k] = amf_to_plain(v, visited)
        return res

    elif isinstance(obj, list):
        return [amf_to_plain(item, visited) for item in obj]
    elif isinstance(obj, dict):
        return {k: amf_to_plain(v, visited) for k, v in obj.items()}
    elif isinstance(obj, (bytes, bytearray)):
        return "<binary>"
    else:
        return obj

# ========== 复刻 AssetLoader.parseFz ==========
def parse_fz_bin(raw_bin: bytes) -> dict:
    fz_result = {}
    comp = FlashCompress()
    di_root = bytes_to_datainput(raw_bin)
    root_obj = di_root.readObject()
    sub_file_count = int(root_obj["fn"])

    for _ in range(sub_file_count):
        sub_raw = di_root.readObject()
        sub_deflate = comp.inflate(bytes(sub_raw))
        sub_info = read_amf_object(sub_deflate)
        if sub_info is None or isinstance(sub_info, UndefinedType):
            continue

        prefix = sub_info["prefixName"]
        ver = sub_info["ver"]
        data_bin = sub_info["data"]

        if ver == 2:
            lzma_data = comp.uncompress_lzma(bytes(data_bin))
            final_obj = read_amf_object(lzma_data)
            fz_result[prefix] = final_obj
        else:
            text_data = comp.uncompress_zlib(data_bin)
            fz_result[prefix] = text_data.decode("utf-8", errors="ignore")
    return fz_result

# ========== 主入口 ==========
def parse_cg_fz_file(file_path: str):
    if not os.path.exists(file_path):
        print(f"错误：文件 {file_path} 不存在")
        return

    with open(file_path, "rb") as f:
        all_bytes = f.read()

    data_dict = None
    # 优先全量解析，失败再截4字节重试
    try:
        data_dict = parse_fz_bin(all_bytes)
    except pyamf.DecodeError:
        print("全量解析失败，跳过前4字节缓存头重试")
        try:
            data_dict = parse_fz_bin(all_bytes[4:])
        except Exception as e:
            print("截头后依然解析失败：", e)
            return

    if not data_dict:
        print("未解析到任何配置数据")
        return

    file_name = os.path.basename(file_path)
    out_dir = f"cg_config_out_{file_name.split('.')[0]}"
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    # 导出JSON
    for key, val in data_dict.items():
        out_path = os.path.join(out_dir, f"{key}.json")
        plain_data = amf_to_plain(val)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(plain_data, f, indent=4, ensure_ascii=False)
        print(f"导出完成：{key}.json")
    print(f"\n全部解析完成，输出目录：{out_dir}")

# ========== 运行 ==========
if __name__ == "__main__":
    TARGET_FILE = "cg1_20260810_1.swf"
    parse_cg_fz_file(TARGET_FILE)