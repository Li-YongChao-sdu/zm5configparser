"""从 4399 造梦西游入口页解析并下载当前主文件 main.swf。"""
import re
import urllib.parse
import urllib.request
from pathlib import Path

PAGE = 'https://www.4399.com/flash/zmhj.htm?g=5'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0 Safari/537.36',
    'Referer': PAGE,
}


def fetch(url):
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def resolve_swf_url(html):
    """入口页用 JS 拼接地址：main.swf?path=<目录>&v=<版本>，需还原完整 query。"""
    match = re.search(r"'([^']*/main\.swf)", html)
    if not match:
        raise RuntimeError('未在入口页中找到主文件地址')
    path = match.group(1)
    directory = path.rsplit('main.swf', 1)[0]
    suffix = re.search(r"var\s+swf\s*=\s*'[^']*'\s*\+\s*path\s*\+\s*\"([^\"]*)\"", html)
    tail = suffix.group(1) if suffix else ''
    dir_url = urllib.parse.urljoin(PAGE, directory)
    return urllib.parse.urljoin(PAGE, path) + '?path=' + urllib.parse.quote(dir_url, safe=':/') + tail


def main():
    html = fetch(PAGE).decode('gb2312', 'ignore')
    swf_url = resolve_swf_url(html)
    print('主文件地址：%s' % swf_url)
    data = fetch(swf_url)
    output = Path('main.swf')
    output.write_bytes(data)
    print('已保存：%s（%d 字节）' % (output.resolve(), len(data)))


if __name__ == '__main__':
    main()
