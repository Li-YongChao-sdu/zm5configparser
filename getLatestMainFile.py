"""从 4399 造梦西游入口页解析当前版本化主文件（如 v4780.swf）并下载。

入口页的 main.swf 只是登录外壳，真正的游戏主文件由版本页加载：
入口页 game_url_arr[5] → v4780d.htm → <param name="movie" value="v4780.swf">。
"""
import re
import urllib.parse
import urllib.request
from pathlib import Path

PAGE = 'https://www.4399.com/flash/zmhj.htm?g=5'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0 Safari/537.36',
}


def fetch(url, referer=PAGE):
    headers = dict(HEADERS)
    if referer:
        headers['Referer'] = referer
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def game_page_url(html):
    """game_url_arr[5] 是造梦西游5当前版本的游戏页，如 .../v4780d.htm。"""
    match = re.search(r"game_url_arr\[5\]\s*=\s*'([^']+)'", html)
    if not match:
        raise RuntimeError('未在入口页中找到 game_url_arr[5]')
    return match.group(1)


def main():
    html = fetch(PAGE).decode('gb2312', 'ignore')
    page_url = game_page_url(html)
    print('版本游戏页：%s' % page_url)

    page = fetch(page_url).decode('gb2312', 'ignore')
    match = (re.search(r'name="movie"\s+value="([^"]+\.swf)"', page)
             or re.search(r'src="([^"]+\.swf)"', page))
    if not match:
        raise RuntimeError('未在版本游戏页中找到主文件地址')

    swf_url = urllib.parse.urljoin(page_url, match.group(1))
    name = urllib.parse.urlparse(swf_url).path.rsplit('/', 1)[-1]
    print('主文件地址：%s' % swf_url)

    data = fetch(swf_url, referer=page_url)
    output = Path(name)
    output.write_bytes(data)
    print('已保存：%s（%d 字节）' % (output.resolve(), len(data)))


if __name__ == '__main__':
    main()
