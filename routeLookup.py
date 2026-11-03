"""路由抓包备用查询：启动 route_sniffer、导入导出、按路由查询。

仓库本身只解析配置包，不抓包。本模块用于在反编译或配置里找不到路由时，
借助 tools/route_sniffer 抓一次真实请求，并把结果整理成可查询的
routes_extra.json；不修改游戏文件，也不依赖第三方 Python 库。
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOOL_EXE = ROOT / 'tools' / 'route_sniffer' / 'route_sniffer.exe'
DATA_FILE = ROOT / 'routes_extra.json'
SENSITIVE = re.compile(
    r'token|cookie|password|passwd|session|secret|authorization|sign', re.I)
ROUTE_KEYS = ('routes', 'route_dict', 'items', 'records', 'data')


def scrub(value):
    """去掉常见敏感字段，避免把 token/cookie 写进本地路由表。"""
    if isinstance(value, dict):
        return {k: scrub(v) for k, v in value.items()
                if not SENSITIVE.search(str(k))}
    if isinstance(value, list):
        return [scrub(v) for v in value]
    if isinstance(value, str) and len(value) > 240:
        return value[:240] + '...'
    return value


def _looks_like_route(value):
    return isinstance(value, str) and ('.' in value or 'Handler' in value)


def normalize(value, source=''):
    """兼容 route_sniffer 可能导出的几种结构，摊平成 route 记录。"""
    rows = []
    if isinstance(value, list):
        for item in value:
            rows.extend(normalize(item, source))
        return rows
    if not isinstance(value, dict):
        return rows
    inner = next((value[key] for key in ROUTE_KEYS
                  if isinstance(value.get(key), (dict, list))), None)
    if inner is not None:
        rows.extend(normalize(inner, source))
        return rows
    route = value.get('route') or value.get('name') or value.get('path') or value.get('url')
    if _looks_like_route(route):
        request = (value.get('request') or value.get('params')
                   or value.get('args') or value.get('body'))
        response = (value.get('response') or value.get('result')
                    or value.get('reply'))
        rows.append({'route': route, 'request': scrub(request),
                     'response': scrub(response), 'source': source})
        return rows
    for route, detail in value.items():
        if not _looks_like_route(route):
            continue
        if isinstance(detail, dict):
            request = (detail.get('request') or detail.get('params')
                       or detail.get('args') or detail.get('body'))
            response = (detail.get('response') or detail.get('result')
                        or detail.get('reply'))
            if request is None and response is None:
                request = detail
        else:
            request, response = detail, None
        rows.append({'route': route, 'request': scrub(request),
                     'response': scrub(response), 'source': source})
    return rows


def read_records(path):
    text = path.read_text(encoding='utf-8-sig')
    try:
        value = json.loads(text)
        records = normalize(value, path.name)
    except json.JSONDecodeError:
        records = []
        for line in text.splitlines():
            if line.strip():
                records.extend(normalize(json.loads(line), path.name))
    return records


def load_all():
    if not DATA_FILE.exists():
        return {}
    return {row['route']: row for row in read_records(DATA_FILE)}


def cmd_import(path):
    if not path.exists():
        print('导入文件不存在：%s' % path)
        return 1
    rows = read_records(path)
    if not rows:
        print('没有识别到路由；支持 {"routes":{...}}、{route:{...}}、[{route:...}] 或 JSONL')
        return 1
    merged = load_all()
    for row in rows:
        old = merged.get(row['route']) or {}
        old.update({k: v for k, v in row.items()
                    if v not in (None, '', {}, [])})
        merged[row['route']] = old
    DATA_FILE.write_text(
        json.dumps({'routes': merged}, ensure_ascii=False, indent=2),
        encoding='utf-8')
    print('导入 %d 条，合并后 %d 条 -> %s' % (
        len(rows), len(merged), DATA_FILE.name))
    return 0


def match_routes(routes, keyword):
    keyword = keyword.lower()
    exact = [route for route in routes if route.lower() == keyword]
    if exact:
        return exact
    return sorted(route for route in routes if keyword in route.lower())


def cmd_route(keyword):
    routes = load_all()
    matches = match_routes(routes, keyword)
    if not matches:
        print('未找到路由：%s（先 --import 抓包导出文件）' % keyword)
        return 1
    for route in matches:
        row = routes[route]
        print('\n路由：%s' % route)
        if row.get('source'):
            print('来源：%s' % row['source'])
        print('请求：%s' % json.dumps(
            row.get('request'), ensure_ascii=False, indent=2))
        print('回包：%s' % json.dumps(
            row.get('response'), ensure_ascii=False, indent=2))
    return 0


def cmd_list(keyword=''):
    routes = sorted(load_all())
    if keyword:
        routes = [route for route in routes if keyword.lower() in route.lower()]
    if not routes:
        print('暂无路由记录；先运行 --sniff 抓包，再 --import 导出文件')
        return 0
    for route in routes:
        print(route)
    print('\n共 %d 条' % len(routes))
    return 0


def cmd_handlers():
    routes = sorted(load_all())
    if not routes:
        print('暂无路由记录；先运行 --sniff 抓包，再 --import 导出文件')
        return 0
    counts = {}
    for route in routes:
        parts = route.split('.')
        name = parts[1] if len(parts) > 1 else route
        counts[name] = counts.get(name, 0) + 1
    for name, count in sorted(counts.items()):
        print('%-32s %d' % (name, count))
    return 0


def cmd_sniff():
    if not TOOL_EXE.exists():
        print('未找到抓包工具：%s' % TOOL_EXE)
        return 1
    print('启动 route_sniffer；需要管理员权限，建议只在测试号或虚拟机使用。')
    subprocess.Popen([str(TOOL_EXE)], cwd=str(TOOL_EXE.parent))
    print('抓包结束后在工具里导出 JSON，再运行：')
    print('  python routeLookup.py --import <导出文件>')
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='路由抓包备用查询：route_sniffer 导出 -> routes_extra.json')
    parser.add_argument('--sniff', action='store_true', help='启动路由抓包工具')
    parser.add_argument('--import', dest='import_file', metavar='FILE',
                        help='导入 route_sniffer 导出的 JSON/JSONL')
    parser.add_argument('--route', metavar='NAME',
                        help='按路由名查询，支持包含匹配')
    parser.add_argument('--list', nargs='?', const='', metavar='KEYWORD',
                        help='列出路由，可按关键字过滤')
    parser.add_argument('--handlers', action='store_true',
                        help='按 Handler 分组统计')
    args = parser.parse_args(argv)
    if args.sniff:
        return cmd_sniff()
    if args.import_file:
        return cmd_import(Path(args.import_file))
    if args.route:
        return cmd_route(args.route)
    if args.list is not None:
        return cmd_list(args.list)
    if args.handlers:
        return cmd_handlers()
    parser.print_help()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
