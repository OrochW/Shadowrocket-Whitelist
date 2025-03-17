import requests
import re
import time

whitelist_url = "https://raw.githubusercontent.com/entr0pia/SwitchyOmega-Whitelist/master/white-list.sorl"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Accept": "text/plain"
}

def fetch_whitelist(url, retries=3, delay=5):
    """多次尝试获取白名单文件"""
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.text
            else:
                print(f"⚠️ 第 {attempt + 1} 次尝试失败，HTTP 状态码: {response.status_code} - {response.reason}")
        except requests.RequestException as e:
            print(f"⚠️ 第 {attempt + 1} 次尝试异常: {e}")
        time.sleep(delay)
    return None

# 获取白名单内容
pac_content = fetch_whitelist(whitelist_url)
if pac_content is None:
    print("❌ 获取白名单失败！请检查 URL 或网络连接。")
    exit(1)

# 调试：打印前 500 个字符检查格式
print(pac_content[:500])

# 可能需要调整解析逻辑
domains = re.findall(r'shExpMatch\(url, "([^"]+)"\)', pac_content)
if not domains:
    print("⚠️ 未提取到任何域名，尝试另一种解析方式")
    domains = [line.strip() for line in pac_content.split("\n") if line.strip() and not line.startswith("#")]

# 去除前缀 *
cleaned_domains = [d.replace("*", "").lstrip(".") for d in domains]

# 生成 Shadowrocket 规则
output_file = "shadowrocket.conf"
with open(output_file, "w") as f:
    for domain in cleaned_domains:
        f.write(f"DOMAIN-SUFFIX,{domain},DIRECT\n")

print(f"✅ 转换完成，共 {len(cleaned_domains)} 条规则！已保存至 {output_file}")
