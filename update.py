import requests
import re

# 目标 URL
whitelist_url = "https://raw.githubusercontent.com/entr0pia/SwitchyOmega-Whitelist/master/whitelist.pac"

# 添加 User-Agent 避免被拦截
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

# 发送请求
response = requests.get(whitelist_url, headers=headers)

# 检查是否成功
if response.status_code != 200:
    print(f"❌ 获取白名单失败！HTTP 状态码: {response.status_code}")
    exit(1)

pac_content = response.text

# 解析 PAC 规则
domains = re.findall(r'shExpMatch\(url, "([^"]+)"\)', pac_content)
cleaned_domains = [d.replace("*", "").lstrip(".") for d in domains]

# 生成 Shadowrocket 规则
output_file = "shadowrocket.conf"
with open(output_file, "w") as f:
    for domain in cleaned_domains:
        f.write(f"DOMAIN-SUFFIX,{domain},DIRECT\n")

print(f"✅ 转换完成，共 {len(cleaned_domains)} 条规则！已保存至 {output_file}")
