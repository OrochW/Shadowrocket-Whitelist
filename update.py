import requests
import re
import ipaddress

# 配置参数
WHITELIST_URL = "https://raw.githubusercontent.com/entr0pia/SwitchyOmega-Whitelist/master/white-list.sorl"
OUTPUT_FILE = "shadowrocket.conf"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def fetch_rules(url):
    """获取远程规则文件"""
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"🚨 规则获取失败: {str(e)}")
        exit(1)

def parse_ip_rules(line):
    """解析IP/CIDR规则"""
    # 处理标准CIDR格式
    if '/' in line:
        try:
            ipaddress.ip_network(line, strict=False)
            return [line]
        except ValueError:
            return []
    
    # 处理通配符格式 10.*.*.*
    if re.match(r"^(\d+|\*)\.(\d+|\*)\.(\d+|\*)\.(\d+|\*)$", line):
        parts = line.split('.')
        cidr = 32
        for i, p in enumerate(parts):
            if p == '*':
                cidr = i * 8
                break
        base_ip = '.'.join([p if p != '*' else '0' for p in parts])
        return [f"{base_ip}/{cidr}"]
    
    return []

def parse_domain_rules(line):
    """解析域名规则"""
    line = line.lower().strip('.*')
    
    # 处理通配域名
    if line.startswith('*'):
        return [f"DOMAIN-SUFFIX,{line[2:]}"]
    
    # 处理精确域名
    if re.match(r"^([a-z0-9-]+\.)*[a-z]{2,}$", line):
        return [f"DOMAIN,{line}"]
    
    return []

def generate_config(rules):
    """生成Shadowrocket配置"""
    config = [
        "#!MANUAL-UPDATE-FROM:SwitchyOmega-Whitelist",
        "#!REPO: github.com/yourname/yourrepo",
        "[Rule]"
    ]
    
    # 白名单规则
    for rule in rules:
        config.append(f"{rule},DIRECT")
    
    # 默认代理规则（必须放在最后）
    config.extend([
        "DOMAIN-KEYWORD,google,PROXY",
        "DOMAIN-SUFFIX,blogspot.com,PROXY",
        "FINAL,PROXY"
    ])
    
    with open(OUTPUT_FILE, 'w') as f:
        f.write('\n'.join(config))

if __name__ == "__main__":
    # 获取并解析规则
    raw_rules = fetch_rules(WHITELIST_URL)
    parsed_rules = []
    
    for line in raw_rules.split('\n'):
        line = line.strip()
        if not line or line.startswith(('//', ';')):
            continue
        
        # 优先解析IP规则
        ip_rules = parse_ip_rules(line)
        if ip_rules:
            parsed_rules.extend([f"IP-CIDR,{r}" for r in ip_rules])
            continue
        
        # 解析域名规则
        domain_rules = parse_domain_rules(line)
        parsed_rules.extend(domain_rules)
    
    # 生成配置文件
    generate_config(parsed_rules)
    print(f"✅ 生成成功！包含 {len(parsed_rules)} 条白名单规则")
