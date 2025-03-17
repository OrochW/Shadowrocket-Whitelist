import requests
import re
import ipaddress

WHITELIST_URL = "https://raw.githubusercontent.com/entr0pia/SwitchyOmega-Whitelist/master/white-list.sorl"
OUTPUT_FILE = "shadowrocket.conf"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# 增强版IP通配符转换
def wildcard_to_cidr(ip_wildcard):
    parts = ip_wildcard.split('.')
    if len(parts) != 4:
        return None
    
    cidr = 32
    for i, part in enumerate(parts):
        if part == '*':
            cidr = i * 8
            break
    else:
        return None  # 无通配符
    
    # 构建基础IP
    base_ip = []
    for j in range(4):
        if j < i:
            base_ip.append(parts[j])
        else:
            base_ip.append('0' if j > i else '0')  # 处理连续通配符
    
    try:
        network = ipaddress.ip_network(f"{'.'.join(base_ip)}/{cidr}", strict=False)
        return str(network)
    except ValueError:
        return None

# 智能域名解析
def parse_domain(line):
    line = line.strip().lower()
    
    # 处理通配符前缀
    if line.startswith('*.'):
        domain = line[2:]
        if re.match(r"^([a-z0-9-]+\.)*[a-z]{2,}$", domain):
            return f"DOMAIN-SUFFIX,{domain}"
    
    # 处理精确域名
    elif re.match(r"^([a-z0-9-]+\.)+[a-z]{2,}$", line):
        return f"DOMAIN,{line}"
    
    # 处理关键词匹配
    elif '*' in line:
        keyword = line.replace('*', '').strip('.')
        if keyword:
            return f"DOMAIN-KEYWORD,{keyword}"
    
    return None

def generate_rules():
    try:
        # 获取原始规则
        raw = requests.get(WHITELIST_URL, headers={"User-Agent": USER_AGENT}, timeout=15).text
        
        direct_rules = []
        seen = set()  # 防重复
        
        for line in raw.split('\n'):
            line = line.strip()
            if not line or line.startswith(('//', ';')):
                continue

            # 处理IP规则
            if re.match(r"^(\d+|\*)(\.(\d+|\*)){3}$", line):
                cidr = wildcard_to_cidr(line)
                if cidr and cidr not in seen:
                    direct_rules.append(f"IP-CIDR,{cidr}")
                    seen.add(cidr)
                continue

            # 处理域名规则
            rule = parse_domain(line)
            if rule and rule not in seen:
                direct_rules.append(rule)
                seen.add(rule)

        # 写入配置文件（确保顺序正确）
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write("#!name=AutoWhitelist\n")
            f.write("[Rule]\n")
            
            # 白名单规则（必须在前）
            f.write("\n".join([
                f"{rule},DIRECT" 
                for rule in direct_rules
                if rule.startswith(('DOMAIN', 'IP-CIDR'))
            ]))
            
            # 代理规则模板（示例）
            f.write("\n\n# 代理规则\n")
            f.write("DOMAIN-SUFFIX,google.com,PROXY\n")
            f.write("DOMAIN-SUFFIX,youtube.com,PROXY\n")
            
            # 最终规则（必须最后）
            f.write("\nFINAL,PROXY")

        print(f"✅ 生成成功！包含 {len(direct_rules)} 条直连规则")
        
    except Exception as e:
        print(f"❌ 生成失败: {str(e)}")
        exit(1)

if __name__ == "__main__":
    generate_rules()
