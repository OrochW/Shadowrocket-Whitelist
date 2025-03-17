#!/usr/bin/env python3
import re
import requests
import ipaddress
from datetime import datetime

# 配置参数
WHITELIST_URL = "https://raw.githubusercontent.com/entr0pia/SwitchyOmega-Whitelist/master/white-list.sorl"
ADBLOCK_URL = "https://raw.githubusercontent.com/217heidai/adblockfilters/main/rules/adblockclash.list"
OUTPUT_FILE = "shadowrocket.conf"

def parse_ip(ip_str):
    """智能转换IP通配符为CIDR"""
    parts = ip_str.split('.')
    if len(parts) != 4 or parts.count('*') == 0:
        return None
    
    cidr = 32
    for i, part in enumerate(parts):
        if part == '*':
            cidr = i * 8
            parts[i:] = ['0']*(4-i)
            break
    
    try:
        return str(ipaddress.ip_network(f"{'.'.join(parts)}/{cidr}", strict=False))
    except:
        return None

def get_whitelist():
    """获取并处理白名单规则"""
    rules = set()
    try:
        res = requests.get(WHITELIST_URL, timeout=15)
        for line in res.text.splitlines():
            line = line.strip()
            if not line or line.startswith(('#', '!', '//', ';')): continue
            
            # 处理IP规则
            if re.match(r"^\d+\.\d+\.\d+\.\d+$", line) or '*' in line:
                if cidr := parse_ip(line):
                    rules.add(f"IP-CIDR,{cidr},DIRECT")
            
            # 处理域名规则
            elif re.match(r"^(\*\.)?[\w-]+\.[\w-]+", line):
                domain = line.split('/')[0].lstrip('*.')
                if '.' in domain:
                    rules.add(f"DOMAIN-SUFFIX,{domain},DIRECT")
    
    except Exception as e:
        print(f"白名单获取失败: {e}")
    
    return sorted(rules)

def get_adblock():
    """获取并处理广告规则"""
    rules = set()
    try:
        res = requests.get(ADBLOCK_URL, timeout=15)
        for line in res.text.splitlines():
            line = line.strip()
            if line.startswith("DOMAIN-SUFFIX,"):
                parts = line.split(',')
                if len(parts) >= 2 and '.' in parts[1]:
                    rules.add(f"{parts[0]},{parts[1]},REJECT")
    
    except Exception as e:
        print(f"广告规则获取失败: {e}")
    
    return sorted(rules)

def generate_config():
    config = f"""#!name=AutoRules
#!desc=最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

[General]
ipv6 = false
dns-server = https://doh.pub/dns-query
skip-proxy = localhost, *.local, e.crashlytics.com, captive.apple.com
bypass-system = true

[Rule]
# 直连白名单
"""
    config += "\n".join(get_whitelist())
    config += "\n\n# 广告拦截\n"
    config += "\n".join(get_adblock())
    config += "\n\nFINAL,PROXY"

    with open(OUTPUT_FILE, 'w') as f:
        f.write(config)

if __name__ == "__main__":
    generate_config()
    print("✅ 配置文件生成完成")
