import pyamf
import os, shutil, json
from pyamf.amf3 import ByteArray,DataInput
from pyamf.util import BufferedByteStream
from pyamf import ASObject,DecodeError,UndefinedType

class DataCompression():
    """
    压缩方法类
    """
    def inflate(self,byte:bytes)->bytes:
        """ByteArray.inflate()"""
        import zlib
        self.decompressor = zlib.decompressobj(wbits=-zlib.MAX_WBITS)
        ba = self.decompressor.decompress(byte)
        ba += self.decompressor.flush()
        return ba
    
    def deflate(self,byte:bytes)->bytes:
        """ByteArray.deflate()"""
        import zlib
        self.decompressor = zlib.decompressobj(wbits=-zlib.MAX_WBITS)
        ba = self.decompressor.decompress(byte)
        ba += self.decompressor.compress()
        return ba
    
    def compress_zlib(self,byte:bytes)->bytes:
        """ByteArray.compress()"""
        import zlib
        return zlib.compress(byte)
    
    def decompress_zlib(self,byte:bytes)->bytes:
        """ByteArray.uncompress()"""
        import zlib
        return zlib.decompress(byte)
    
    def compress_lzma(self,byte:bytes)->bytes:
        """ByteArray.compress("CompressionAlgorithm.lzma")"""
        import lzma
        return lzma.compress(byte)
    
    def decompress_lzma(self,byte:bytes)->bytes:
        """ByteArray.uncompress("CompressionAlgorithm.lzma")"""
        import lzma
        return lzma.decompress(byte)

def build_fz_item(fz_dict, prefix_name, data):
    fz_dict[prefix_name] = data

def read_object_from_bytes(amf_data:bytes)->ASObject:
    """
    从二进制数据中直接读取出ASObject
    """
    try:
        return trans_bytes_to_io(amf_data).readObject()
    except DecodeError:
        return None

def trans_bytes_to_io(amf_data:bytes)->DataInput:
    """
    将二进制数据转换为IDataInput类
    """
    a = BufferedByteStream(amf_data)
    return DataInput(pyamf.decode(a))

def parse_config(config_bin:bytes)->dict:
    fz_dict = {}
    compressor = DataCompression()
    data_stream = trans_bytes_to_io(config_bin)
    as_object = data_stream.readObject()
    for _ in range(as_object["fn"]):
        ba = ByteArray(data_stream.readObject())
        ba_ori = bytes(ba)
        ba_de = compressor.inflate(ba_ori)
        as_object = read_object_from_bytes(ba_de)
        if as_object is None or isinstance(as_object,UndefinedType):
            continue
        elif as_object["ver"] in ["2",2]:
            config_data = compressor.decompress_lzma(bytes(as_object["data"]))
            build_fz_item(fz_dict,as_object["prefixName"],read_object_from_bytes(config_data))
        else:
            config_data = compressor.decompress_zlib(as_object["data"])
            build_fz_item(fz_dict,as_object["prefixName"],str(config_data))
        print("解析:",as_object["prefixName"])
    return fz_dict
    
def parseConfigFile(input_file:str)->dict:
    input_file = input_file.replace("\\","/").replace("./","").replace("/","")
    output_dir = "splitConfig" + input_file[input_file.find("_"):input_file.find(".")]

    if not os.path.exists(input_file):
        print("请检查文件路径")
        exit()

    with open(input_file, "rb") as file:
        amf_data = file.read()
        file.close()
    parsed_data = parse_config(amf_data)
    
    shutil.rmtree(output_dir,True)
    os.makedirs(output_dir,777,True)

    for key in parsed_data.keys():
        print("写出:", key + "json")
        try:
            with open(os.path.join(output_dir, key + '.json'), "+w", encoding='utf-8') as f:
                f.write(json.dumps(
                parsed_data.get(key,{}),
                ensure_ascii=False,
                indent=4))
        except ValueError as e:
            print(f"跳过 {key}（循环引用错误: {str(e)}）")
            continue  # 继续处理下一个key

    print("配置解析完成")
    exit()

if __name__ == "__main__":
    input_file = "cg1_20250714_1.swf"
    output_dir = "splitConfig" + input_file[input_file.find("_"):input_file.find(".")]

    if not os.path.exists(input_file):
        print("请检查文件路径")
        exit()

    with open(input_file, "rb") as file:
        amf_data = file.read()
        file.close()
    parsed_data = parse_config(amf_data)
    
    shutil.rmtree(output_dir,True)
    os.makedirs(output_dir,777,True)

    for key in parsed_data.keys():
        print("写出:", key + "json")
        with open(os.path.join(output_dir, key + '.json'), "+w", encoding='utf-8') as f:
            f.write(json.dumps(parsed_data.get(key,{}), ensure_ascii=False, indent=4))
    
    print("配置解析完成")
    exit()
