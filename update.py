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

def ip_wildcard_to_cidr(ip_wildcard):
    """将 IP 通配符格式转换为 CIDR 表示法"""
    parts = ip_wildcard.split('.')
    if len(parts) != 4:
        return None
    
    first_star = None
    for i, part in enumerate(parts):
        if part == '*':
            first_star = i
            break
    else:
        return None  # 没有通配符
    
    # 验证后续部分是否全为通配符
    for j in range(first_star, 4):
        if parts[j] != '*':
            return None
    
    # 构建 CIDR
    cidr = first_star * 8
    ip_parts = []
    for i in range(4):
        if i < first_star:
            ip_parts.append(parts[i])
        else:
            ip_parts.append('0')
    
    try:
        # 验证 IP 有效性
        for part in ip_parts:
            num = int(part)
            if num < 0 or num > 255:
                return None
    except ValueError:
        return None
    
    return f"{'.'.join(ip_parts)}/{cidr}"

# 获取白名单内容
pac_content = fetch_whitelist(whitelist_url)
if pac_content is None:
    print("❌ 获取白名单失败！请检查 URL 或网络连接。")
    exit(1)

# 第一步：清理注释和空行
cleaned_lines = []
for line in pac_content.split("\n"):
    line = line.strip()
    if not line or line.startswith(("//", ";")):
        continue
    cleaned_lines.append(line)

# 第二步：解析有效规则
domains = set()
ip_cidrs = set()

for line in cleaned_lines:
    # 优先处理 IP 通配符规则
    if re.match(r'^(\d+|\*)(\.(\d+|\*)){3}$', line):
        cidr = ip_wildcard_to_cidr(line)
        if cidr:
            ip_cidrs.add(cidr)
            continue
    
    # 处理域名规则
    match = re.search(r"(\*\.)?([\w\.-]+\.[a-zA-Z]{2,})", line)
    if match:
        wildcard, domain = match.groups()
        
        # 过滤包含后缀通配符的情况（如 .*）
        if domain.endswith(".*"):
            print(f"⚠️ 过滤无效域名: {domain}")
            continue
        
        # 处理通配符域名
        if wildcard:
            domains.add(domain)
        else:
            domains.add(domain)

# 验证解析结果
if not domains and not ip_cidrs:
    print("❌ 未找到任何有效规则！请检查文件格式。")
    print("📜 文件前 20 行内容:")
    print("\n".join(cleaned_lines[:20]))
    exit(1)

# 第三步：生成 Shadowrocket 规则
output_file = "shadowrocket.conf"
with open(output_file, "w") as f:
    f.write("#!name=Proxy Whitelist\n")
    f.write("#!desc=Generated from SwitchyOmega PAC\n")
    f.write("[Rule]\n")
    
    # 写入域名规则
    for domain in sorted(domains):
        f.write(f"DOMAIN-SUFFIX,{domain},DIRECT\n")
    
    # 写入 IP-CIDR 规则
    for cidr in sorted(ip_cidrs):
        f.write(f"IP-CIDR,{cidr},DIRECT\n")

total_rules = len(domains) + len(ip_cidrs)
print(f"✅ 转换成功！生成 {len(domains)} 条域名规则 + {len(ip_cidrs)} 条 IP 规则 = 总计 {total_rules} 条规则")
print(f"📁 输出文件: {output_file}")
