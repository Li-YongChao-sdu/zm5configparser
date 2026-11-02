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

注意：入口页加载的 `main.swf` 只是登录外壳，不是游戏主文件。真正的游戏主文件是带版本号的文件，例如当前为 `v4780.swf`。

入口页：

```text
https://www.4399.com/flash/zmhj.htm?g=5
```

入口页中的 `game_url_arr[5]` 指向当前版本游戏页：

```text
https://sda.4399.com/4399swf/upload_swf/ftp22/csya/20170622/1/v4780d.htm
```

游戏页内 `<param name="movie">` 指向当前主文件（2026-11-02 为 v4780）：

```text
https://sda.4399.com/4399swf/upload_swf/ftp22/csya/20170622/1/v4780.swf
```

版本号会随游戏更新变化，建议用脚本自动解析并下载，保存为与线上同名的 `v<版本号>.swf`：

```console
python getLatestMainFile.py
```

脚本流程：入口页 → `game_url_arr[5]` → 版本游戏页 → `<param name="movie">` → 下载主文件。下载时需带版本游戏页作 Referer，否则服务器只返回 23 KB 的域名校验占位 SWF。

### 反编译主文件（可选）

主文件是 SWF，可用 FFDec（JPEXS Free Flash Decompiler）反编译为 ActionScript 文件：

- 项目仓库：https://github.com/jindrapetrik/jpexs-decompiler
- 发布下载：https://github.com/jindrapetrik/jpexs-decompiler/releases

GUI 方式：用 FFDec 打开 `v4780.swf`，选择“工具 → 导出 → 导出脚本”，或右键选择导出 AS3。

命令行示例（Windows）：

```console
ffdec.bat -export script .\as_out .\v4780.swf
```

导出的 `.as` 文件可用于对照配置表结构；本仓库只解析配置，不修改主文件。

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
