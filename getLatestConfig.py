"""入口：下载并解包本周最新配置，输出到 cg_config_out_cg1_<日期>_<序号>。"""
import json

from configParser import sync


if __name__ == '__main__':
    print(json.dumps(sync(), ensure_ascii=False))
