import requests
import re
import ipaddress

WHITELIST_URL = "https://raw.githubusercontent.com/entr0pia/SwitchyOmega-Whitelist/master/white-list.sorl"
ADBLOCK_URL = "https://raw.githubusercontent.com/217heidai/adblockfilters/main/rules/adblockclash.list"
OUTPUT_FILE = "shadowrocket.conf"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def wildcard_to_cidr(ip_wildcard):
    """将通配符IP转换为CIDR格式"""
    parts = ip_wildcard.split('.')
    if len(parts) != 4:
        return None
    
    cidr = 32
    for i, part in enumerate(parts):
        if part == '*':
            cidr = i * 8
            break
    else:
        return None
    
    base_ip = []
    for j in range(4):
        if j < i:
            base_ip.append(parts[j])
        else:
            base_ip.append('0')
    
    try:
        network = ipaddress.ip_network(f"{'.'.join(base_ip)}/{cidr}", strict=False)
        return str(network)
    except ValueError:
        return None

def parse_domain(line):
    """智能解析域名规则"""
    line = line.strip().lower()
    
    if line.startswith('*.'):
        domain = line[2:]
        if re.match(r"^([a-z0-9-]+\.)*[a-z]{2,}$", domain):
            return f"DOMAIN-SUFFIX,{domain}"
    
    elif re.match(r"^([a-z0-9-]+\.)+[a-z]{2,}$", line):
        return f"DOMAIN,{line}"
    
    elif '*' in line:
        keyword = line.replace('*', '').strip('.')
        if keyword:
            return f"DOMAIN-KEYWORD,{keyword}"
    
    return None

def generate_merged_rules():
    try:
        headers = {"User-Agent": USER_AGENT}
        
        # ================= 处理白名单规则 =================
        white_response = requests.get(WHITELIST_URL, headers=headers, timeout=15)
        white_response.raise_for_status()
        
        direct_rules = []
        seen = set()
        
        for line in white_response.text.splitlines():
            line = line.strip()
            if not line or line.startswith(('//', ';')):
                continue

            # 处理IP规则
            if re.match(r"^(\d+|\*)(\.(\d+|\*)){3}$", line):
                cidr = wildcard_to_cidr(line)
                if cidr and cidr not in seen:
                    direct_rules.append(f"IP-CIDR,{cidr},DIRECT")
                    seen.add(cidr)
                continue

            # 处理域名规则
            rule = parse_domain(line)
            if rule and rule not in seen:
                direct_rules.append(f"{rule},DIRECT")
                seen.add(rule)

        # ================= 处理广告拦截规则 =================
        ad_response = requests.get(ADBLOCK_URL, headers=headers, timeout=15)
        ad_response.raise_for_status()
        
        reject_rules = []
        for line in ad_response.text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            reject_rules.append(f"{line},Reject")

        # ================= 生成最终配置文件 =================
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write("#!name=AutoMergedRules\n")
            f.write("[Rule]\n")
            
            # 白名单直连规则
            f.write("\n".join(direct_rules))
            
            # 广告拦截规则
            f.write("\n\n")
            f.write("\n".join(reject_rules))
            
            # 代理规则示例
            f.write("\n\n# 常用代理规则\n")
            f.write("DOMAIN-SUFFIX,google.com,PROXY\n")
            f.write("DOMAIN-SUFFIX,youtube.com,PROXY\n")
            
            # 最终规则
            f.write("\nFINAL,PROXY\n")

        print(f"✅ 生成成功！包含：\n"
              f"- {len(direct_rules)} 条直连规则\n"
              f"- {len(reject_rules)} 条拦截规则\n"
              f"- 3 条示例代理规则")
        
    except Exception as e:
        print(f"❌ 生成失败: {str(e)}")
        exit(1)

if __name__ == "__main__":
    generate_merged_rules()
