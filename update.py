#!/usr/bin/env python3
import re
import requests
import ipaddress
from datetime import datetime

# ====================== 配置部分 ======================
WHITELIST_URL = "https://raw.githubusercontent.com/entr0pia/SwitchyOmega-Whitelist/master/white-list.sorl"
ADBLOCK_URL = "https://raw.githubusercontent.com/217heidai/adblockfilters/main/rules/adblockclash.list"
OUTPUT_FILE = "shadowrocket.conf"
USER_AGENT = "Mozilla/5.0 (compatible; Shadowrocket-Whitelist/1.0; +https://github.com/OrochW/Shadowrocket-Whitelist)"

# ====================== 固定配置模板 ======================
FIXED_CONFIG = f"""#!name=Shadowrocket-Whitelist
#!desc=Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

[General]
ipv6 = false
dns-server = https://doh.pub/dns-query, https://dns.alidns.com/dns-query
bypass-system = true
skip-proxy = 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, localhost, *.local, e.crashlytics.com, captive.apple.com
bypass-tun = 10.0.0.0/8,100.64.0.0/10,127.0.0.0/8,169.254.0.0/16,172.16.0.0/12,192.0.0.0/24,192.0.2.0/24,192.88.99.0/24,192.168.0.0/16,198.18.0.0/15,198.51.100.0/24,203.0.113.0/24,224.0.0.0/4,255.255.255.255/32
exclude-simple-hostnames = true
prefer-ipv6 = false
allow-wifi-access = false
proxy-test-url = http://cp.cloudflare.com/generate_204
test-timeout = 3
interface-mode = auto

[Host]
localhost = 127.0.0.1

[Rule]
"""

# ====================== 工具函数 ======================
def wildcard_to_cidr(ip_wildcard):
    """将通配符IP转换为CIDR格式"""
    try:
        parts = ip_wildcard.split('.')
        if len(parts) != 4:
            return None

        cidr = 32
        for i, part in enumerate(parts):
            if part == '*':
                cidr = i * 8
                parts[i:] = ['0']*(4-i)
                break

        network = ipaddress.ip_network('.'.join(parts) + '/' + str(cidr), strict=False)
        return str(network)
    except Exception as e:
        print(f"⚠️ IP转换失败 {ip_wildcard}: {str(e)}")
        return None

def is_valid_domain(domain):
    """严格验证域名有效性"""
    pattern = r"^([a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,63}$"
    return re.match(pattern, domain) is not None

# ====================== 规则处理器 ======================
def process_whitelist():
    """处理白名单规则"""
    print("🔄 正在处理白名单规则...")
    seen = set()
    rules = []
    
    try:
        resp = requests.get(WHITELIST_URL, headers={'User-Agent': USER_AGENT}, timeout=15)
        resp.raise_for_status()
        
        for line in resp.text.split('\n'):
            line = line.strip()
            if not line or line.startswith(('//', ';')):
                continue

            # 处理IP规则
            if re.match(r"^(\d+|\*)(\.(\d+|\*)){3}$", line):
                if cidr := wildcard_to_cidr(line):
                    rule = f"IP-CIDR,{cidr},DIRECT"
                    if rule not in seen:
                        rules.append(rule)
                        seen.add(rule)
                continue

            # 处理域名规则
            domain = line.split('/')[0] if '/' in line else line
            if is_valid_domain(domain):
                rule = f"DOMAIN-SUFFIX,{domain},DIRECT"
                if rule not in seen:
                    rules.append(rule)
                    seen.add(rule)
    
    except Exception as e:
        print(f"⚠️ 白名单处理错误: {str(e)}")
    
    return rules

def process_adblock():
    """处理现成Shadowrocket规则"""
    print("🔄 正在合并AdBlock规则...")
    adblock_header = []
    adblock_rules = []
    seen = set()
    
    try:
        resp = requests.get(ADBLOCK_URL, headers={'User-Agent': USER_AGENT}, timeout=15)
        resp.raise_for_status()
        
        in_header = True
        for line in resp.text.split('\n'):
            line = line.strip()
            
            # 提取注释头信息
            if in_header:
                if line.startswith('#'):
                    adblock_header.append(line)
                    continue
                else:
                    in_header = False
                    adblock_header.append("# ================= 广告拦截规则 =================")
            
            # 处理有效规则
            if line.startswith("DOMAIN-SUFFIX,"):
                domain = line.split(',')[1].strip()
                if is_valid_domain(domain):
                    rule = f"DOMAIN-SUFFIX,{domain}"  # 保留原始格式
                    if rule not in seen:
                        adblock_rules.append(rule)
                        seen.add(rule)
    
    except Exception as e:
        print(f"⚠️ AdBlock规则处理错误: {str(e)}")
    
    return adblock_header, adblock_rules

# ====================== 主生成逻辑 ======================
def generate_config():
    try:
        # 处理各规则源
        whitelist_rules = process_whitelist()
        adblock_header, adblock_rules = process_adblock()
        
        # 生成配置文件
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            # 写入固定配置
            f.write(FIXED_CONFIG)
            
            # 写入白名单规则
            f.write("# ================= 直连规则 =================\n")
            f.write("\n".join(whitelist_rules))
            
            # 写入AdBlock规则
            f.write("\n\n")
            f.write("\n".join(adblock_header))
            f.write("\n")
            f.write("\n".join(adblock_rules))
            
            # 最终兜底规则
            f.write("\n\nFINAL,PROXY")
        
        print(f"✅ 生成成功！包含：")
        print(f"- 直连规则: {len(whitelist_rules)} 条")
        print(f"- 广告规则: {len(adblock_rules)} 条")
        
    except Exception as e:
        print(f"❌ 生成失败: {str(e)}")
        exit(1)

if __name__ == "__main__":
    generate_config()
