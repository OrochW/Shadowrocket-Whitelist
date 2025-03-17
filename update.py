import requests
import re
import time

whitelist_url = "https://raw.githubusercontent.com/entr0pia/SwitchyOmega-Whitelist/master/white-list.sorl"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Accept": "text/plain"
}

def fetch_whitelist(url, retries=3, delay=5):
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.text
            else:
                print(f"⚠️ Attempt {attempt + 1} failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1} error: {str(e)}")
        time.sleep(delay)
    return None

def parse_ip_wildcard(ip_str):
    """ Convert IP wildcard to CIDR """
    parts = ip_str.split('.')
    if len(parts) != 4:
        return None
    
    cidr_mask = 32
    for i, part in enumerate(parts):
        if part == '*':
            cidr_mask = i * 8
            break
    else:
        return None  # No wildcard found
    
    # Build base IP
    base_ip = []
    for j in range(4):
        if j < i:
            base_ip.append(parts[j])
        else:
            base_ip.append('0')
    
    return f"{'.'.join(base_ip)}/{cidr_mask}"

# Fetch PAC content
pac_content = fetch_whitelist(whitelist_url)
if not pac_content:
    print("❌ Failed to fetch whitelist")
    exit(1)

# Processing logic
domains = set()
ip_cidrs = set()

for line in pac_content.splitlines():
    line = line.strip()
    if not line or line.startswith(('//', ';')):
        continue
    
    # Process IP wildcards (e.g. 10.*.*.*)
    if re.match(r'^\d+\.\d+\.\d+\.\d+$', line.replace('*', '0')):
        cidr = parse_ip_wildcard(line)
        if cidr:
            ip_cidrs.add(cidr)
            continue
    
    # Process domain wildcards (e.g. *.cn)
    if line.startswith('*.'):
        domain = line[2:]
        if re.match(r'^[\w.-]+\.[a-zA-Z]{2,}$', domain):
            domains.add(domain)
            continue
    
    # Process normal domains
    match = re.search(r'([\w.-]+\.[a-zA-Z]{2,})$', line)
    if match:
        domains.add(match.group(1))

if not domains and not ip_cidrs:
    print("❌ No valid rules parsed!")
    exit(1)

# Generate Shadowrocket config
with open("shadowrocket.conf", "w") as f:
    f.write("#!name=ProxyBypass\n[Rule]\n")
    for domain in sorted(domains):
        f.write(f"DOMAIN-SUFFIX,{domain},DIRECT\n")
    for cidr in sorted(ip_cidrs):
        f.write(f"IP-CIDR,{cidr},DIRECT\n")

print(f"✅ Generated {len(domains)} domains + {len(ip_cidrs)} IPs")
