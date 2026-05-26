import requests
import datetime
import configParser

if __name__ == '__main__':
    server_pre = "https://sda.4399.com/4399swf/upload_swf/ftp22/csya/20170622/1/assets/data/cg1_"
    header = {"User-Agent": "Mozilla/5.0 (Windows; U; zh-CN) AppleWebKit/533.19.4 (KHTML, like Gecko) AdobeAIR/3.4|4399.air.wd|4399.zm5.air"}
    current_date = datetime.date.today()
    has_get = False
    file_name = ""
    for i in range(20):
        if has_get:
            break
        # 正确的日期计算：从今天开始，每次减去i天
        check_date = current_date - datetime.timedelta(days=i)
        date_str = check_date.strftime("%Y%m%d")
        
        for j in range(5,0,-1):
            if has_get:
                break
            url = server_pre + date_str + "_" + str(j) + ".swf"
            print(url)
            data = requests.get(url,headers=header)
            if data.status_code == 404:
                continue
            file_name = "./cg1_" + date_str + "_" + str(j) + ".swf"
            with open(file_name,"wb+") as f:
                f.write(data.content)
                f.close()
                has_get = True
    configParser.parseConfigFile(file_name)