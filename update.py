import requests
import re
import time

# 目标白名单 URL
whitelist_url = "https://raw.githubusercontent.com/entr0pia/SwitchyOmega-Whitelist/master/white-list.sorl"

# 添加 User-Agent 避免被拦截
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

# **第一步：删除注释**
cleaned_lines = []
for line in pac_content.split("\n"):
    line = line.strip()
    if not line or line.startswith("//") or line.startswith(";"):  # 去掉注释和空行
        continue
    cleaned_lines.append(line)

# **第二步：匹配有效域名**
domains = set()  # 用 set 去重
for line in cleaned_lines:
    # 更宽松的匹配方式，支持各种可能的写法
    match = re.search(r"([\w\.-]+\.[a-zA-Z]{2,})", line)
    if match:
        domain = match.group(1)
        # **如果规则是 `*.randomtext.*` 这种，就跳过**
        if domain.endswith(".*"):
            print(f"⚠️ 过滤掉无效域名：{domain}")
            continue
        domains.add(domain)

# **如果没有解析到任何域名，报错退出**
if not domains:
    print("❌ 未找到任何有效的域名！请检查 PAC 文件格式。")
    print("📜 PAC 文件内容（前 20 行）：")
    print("\n".join(cleaned_lines[:20]))  # 打印前 20 行，方便调试
    exit(1)

# **第三步：生成 Shadowrocket 规则**
output_file = "shadowrocket.conf"
with open(output_file, "w") as f:
    f.write("#!name=proxy_list\n")
    f.write("#!homepage=https://github.com/GMOogway/shadowrocket-rules\n")
    f.write("#!desc=Generated from SwitchyOmega PAC\n[Rule]\n")
    for domain in sorted(domains):  # 排序保证稳定
        f.write(f"DOMAIN-SUFFIX,{domain},DIRECT\n")

print(f"✅ 转换完成，共 {len(domains)} 条规则！已保存至 {output_file}")
