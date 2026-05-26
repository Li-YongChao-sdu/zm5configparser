from bs4 import BeautifulSoup
import requests

if __name__ == "__main__":
    header = {"User-Agent": "Mozilla/5.0 (Windows; U; zh-CN) AppleWebKit/533.19.4 (KHTML, like Gecko) AdobeAIR/3.4|4399.air.wd|4399.zm5.air"}
    res = requests.get("https://www.4399.com/flash/zmhj2.htm",headers=header)
    soup = BeautifulSoup(res.content,"html.parser")
    
    print("正在搜索游戏链接...")
    link = None
    
    # 尝试多种可能的匹配模式
    for a_tag in soup.find_all('a'):
        img_tag = a_tag.find('img')
        if img_tag:
            img_src = img_tag.get('src', '')
            print(f"找到图片: {img_src}")
            # 修改匹配条件：查找包含 "5_" 的图片（造梦西游5）
            if '/5_' in img_src or '5.png' in img_src:
                link = a_tag['href']
                print(f"找到游戏链接: {link}")
                break
    
    if link is None:
        print("未找到游戏链接，尝试查找所有链接...")
        for a_tag in soup.find_all('a'):
            href = a_tag.get('href', '')
            text = a_tag.get_text()
            if 'zm5' in href.lower() or '造梦西游5' in text or '造梦西游' in text:
                link = href
                print(f"找到可能的游戏链接: {link}")
                break
    
    if link is None:
        print("仍未找到游戏链接")
        exit()
    
    res = requests.get(link,headers=header)
    res.encoding = "gb2312"
    soup = BeautifulSoup(res.content,"html.parser")
    embed_tag = soup.find("embed")
    if embed_tag is None:
        print("未找到embed标签")
        exit()
    
    swf_name = embed_tag["src"]
    swf_url = link[:link.rfind("/") + 1] + swf_name
    res = requests.get(swf_url,headers=header)
    print(swf_name)
    with open(swf_name,"wb+") as file:
        file.write(res.content)
    exit()