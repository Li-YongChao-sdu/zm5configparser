# zm5ConfigParser

造梦西游5（zmxy5）配置包下载、AMF 解包与 JSON 导出工具。脚本取自造五活动助手的配置更新模块，已去除 pyamf、requests、beautifulsoup4 依赖，只使用 Python 标准库。

## 功能

- 自动探测本周最新的 `cg1_YYYYMMDD_N.swf`
- 下载后按 AMF3 解包，LZMA / zlib 两种压缩格式都支持
- 每张配置表导出为独立 JSON
- 校验 `Pet`、`Shop`、`Dungeon`、`Activity`、`Prop` 五张关键表
- 输出目录不会覆盖旧配置，便于版本回退

## 环境

- Python 3.8+
- 无第三方依赖

## 运行

```console
python getLatestConfig.py
```

也可以直接运行解析模块：

```console
python configParser.py
```

输出目录：

```text
cg_config_out_cg1_<日期>_<序号>/
```

## 初始文件下载地址

### 主文件

入口页（页面内动态加载主 SWF）：

```text
https://www.4399.com/flash/zmhj.htm?g=5
```

当前页面版本的主文件直链（2026-09-24）：

```text
https://www.4399.com/images/zmhj/flash20260924/main.swf?path=https://www.4399.com/images/zmhj/flash20260924/&v=23
```

通用备用地址：

```text
https://www.4399.com/images/zmhj/flash/main.swf
```

自动获取并保存为 `main.swf`：

```console
python getLatestMainFile.py
```

### 配置文件

配置目录：

```text
https://sda.4399.com/4399swf/upload_swf/ftp22/csya/20170622/1/assets/data/
```

当前配置示例：

```text
https://sda.4399.com/4399swf/upload_swf/ftp22/csya/20170622/1/assets/data/cg1_20261026_1.swf
```

命名规则：

```text
cg1_<YYYYMMDD>_<序号>.swf
```

- 以 2026-10-26 为基准，每 7 天递增一个版本日期
- 周内热更时序号从 1 递增，脚本会探测 1~7
- 找不到本周配置时会向前回溯，最多 8 周

## 输出说明

解包完成后，关键表位于输出目录下：

- `Pet.json`
- `Shop.json`
- `Dungeon.json`
- `Activity.json`
- `Prop.json`

## 免责声明

本项目仅用于学习与研究游戏配置结构，不修改游戏文件，不提供账号、登录或充值相关功能。请自行遵守游戏服务条款。
