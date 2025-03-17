import requests
import re
import time

# Step 1: 获取最新的 SwitchyOmega 白名单
whitelist_url = "https://raw.githubusercontent.com/entr0pia/SwitchyOmega-Whitelist/master/whitelist.pac"

def fetch_whitelist(url, retries=3, backoff_factor=2):
    for i in range(retries):
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            print(f"❌ 获取白名单失败！状态码: {response.status_code}，重试 {i+1}/{retries} 次")
            time.sleep(backoff_factor * (i + 1))
    return None

pac_content = fetch_whitelist(whitelist_url)
if pac_content is None:
    print("❌ 无法获取白名单，已尝试多次。")
    exit(1)

# Step 2: 提取域名
domains = re.findall(r'shExpMatch\(url, "([^"]+)"\)', pac_content)
cleaned_domains = [d.replace("*", "").lstrip(".") for d in domains]

 ▋
