#!/usr/bin/env python3
import re
import requests
import ipaddress
from datetime import datetime

# ====================== 配置部分 ======================
WHITELIST_URL = "https://raw.githubusercontent.com/entr0pia/SwitchyOmega-Whitelist/master/white-list.sorl"
ADBLOCK_URL = "https://raw.githubusercontent.com/217heidai/adblockfilters/main/rules/adblockclash.list"
OUTPUT_FILE = "shadowrocket.conf"
USER_AGENT = "Mozilla/5.0 (compatible; Shadowrocket-Merger/1.0; +https://github.com/OrochW/Shadowrocket-Whitelist)"

# ====================== 模块1：固定配置生成器 ======================
def generate_general_config():
    """生成固定头部配置"""
    return f"""#!name=Shadowrocket-Merged
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

# ====================== 模块2：白名单处理器 ======================
class WhitelistProcessor:
    @staticmethod
    def parse_ip(ip_wildcard):
        """处理IP通配符 (如 192.168.*.* -> 192.168.0.0/16)"""
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

    @classmethod
    def get_rules(cls):
        """获取并处理白名单规则"""
        print("🔄 正在处理白名单规则...")
        rules = set()
        
        try:
            resp = requests.get(WHITELIST_URL, headers={'User-Agent': USER_AGENT}, timeout=15)
            resp.raise_for_status()
            
            for line in resp.text.split('\n'):
                line = line.strip()
                if not line or line.startswith(('//', ';')):
                    continue

                # 处理IP规则
                if re.match(r"^(\d+|\*)(\.(\d+|\*)){3}$", line):
                    if cidr := cls.parse_ip(line):
                        rules.add(f"IP-CIDR,{cidr},DIRECT")
                    continue

                # 处理域名规则
                domain = line.split('/')[0] if '/' in line else line
                if re.match(r"^([a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,63}$", domain):
                    rules.add(f"DOMAIN-SUFFIX,{domain},DIRECT")

        except Exception as e:
            print(f"⚠️ 白名单处理错误: {str(e)}")
        
        return sorted(rules)

# ====================== 模块3：AdBlock处理器 ======================
class AdBlockProcessor:
    @staticmethod
    def get_rules():
        """处理AdBlock规则文件并添加REJECT策略"""
        print("🔄 正在处理AdBlock规则...")
        headers = []
        rules = set()
        
        try:
            resp = requests.get(ADBLOCK_URL, headers={'User-Agent': USER_AGENT}, timeout=15)
            resp.raise_for_status()
            
            in_header = True
            for line in resp.text.split('\n'):
                line = line.strip()
                
                # 提取注释头
                if in_header:
                    if line.startswith('#'):
                        headers.append(line)
                        continue
                    else:
                        in_header = False
                        headers.append("\n# ================= 广告拦截规则 =================")
                
                # 处理有效规则并添加REJECT
                if line.startswith("DOMAIN-SUFFIX,"):
                    parts = line.split(',')
                    if len(parts) >= 2:
                        domain = parts[1].split('#')[0].strip()
                        if re.match(r"^([a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,63}$", domain):
                            rules.add(f"{parts[0]},{domain},REJECT")

        except Exception as e:
            print(f"⚠️ AdBlock处理错误: {str(e)}")
        
        return headers, sorted(rules)

# ====================== 主程序 ======================
def main():
    try:
        # 生成各模块内容
        general_config = generate_general_config()
        whitelist_rules = WhitelistProcessor.get_rules()
        adblock_headers, adblock_rules = AdBlockProcessor.get_rules()
        
        # 合并写入文件
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            # 写入固定配置
            f.write(general_config)
            
            # 写入白名单规则
            f.write("# ================= 直连白名单 =================\n")
            f.write("\n".join(whitelist_rules))
            
            # 写入AdBlock规则
            f.write("\n\n")
            f.write("\n".join(adblock_headers))
            f.write("\n")
            f.write("\n".join(adblock_rules))
            
            # 最终规则
            f.write("\n\nFINAL,PROXY")
        
        print(f"✅ 合并成功！规则统计：")
        print(f"- 直连规则: {len(whitelist_rules)} 条")
        print(f"- 广告规则: {len(adblock_rules)} 条 (已添加REJECT)")
        print(f"- 保留注释: {len(adblock_headers)} 行")

    except Exception as e:
        print(f"❌ 生成失败: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
