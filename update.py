import requests
import re

# Step 1: 获取最新的 SwitchyOmega 白名单
whitelist_url = "https://raw.githubusercontent.com/entr0pia/SwitchyOmega-Whitelist/master/whitelist.pac"
response = requests.get(whitelist_url)
if response.status_code != 200:
    print("❌ 获取白名单失败！")
    exit(1)

pac_content = response.text

# Step 2: 提取域名
domains = re.findall(r'shExpMatch\(url, "([^"]+)"\)', pac_content)
cleaned_domains = [d.replace("*", "").lstrip(".") for d in domains]

# Step 3: 生成 Shadowrocket 规则
output_file = "shadowrocket.conf"
with open(output_file, "w") as f:
    for domain in cleaned_domains:
        f.write(f"DOMAIN-SUFFIX,{domain},DIRECT\n")

print(f"✅ 转换完成，共 {len(cleaned_domains)} 条规则！已保存至 {output_file}")
