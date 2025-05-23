#!/usr/bin/env python3
"""
create-trojan: Automation for creating TROJAN accounts via CLI
Usage:
1) python3 create_trojan.py {username} {day} {limit_data_GB} {limit_ip}               (UUID random)
2) python3 create_trojan.py {username} {uuid} {day} {limit_data_GB} {limit_ip}        (UUID custom)
"""

import sys
import os
import subprocess
import json
import uuid
import requests
import urllib.parse
from datetime import datetime, timedelta
import re

# Color constants
class Colors:
    RED = "\033[31m"
    YELLOW = "\033[33m"
    GREEN = "\033[0;32m"
    NC = '\033[0m'

def get_server_ip():
    """Get server IP address"""
    try:
        response = requests.get('https://ipv4.icanhazip.com', timeout=10)
        return response.text.strip()
    except:
        try:
            response = requests.get('https://ifconfig.me', timeout=10)
            return response.text.strip()
        except:
            return None

def check_permission():
    """Check server permission"""
    try:
        myip = get_server_ip()
        if not myip:
            print(f"{Colors.RED}Cannot get server IP{Colors.NC}")
            sys.exit(1)
        
        # Get server date
        response = requests.get('https://google.com/', timeout=10, allow_redirects=False)
        date_header = response.headers.get('Date', '')
        
        if date_header:
            server_date = datetime.strptime(date_header, '%a, %d %b %Y %H:%M:%S %Z')
            date_list = server_date.strftime('%Y-%m-%d')
        else:
            date_list = datetime.now().strftime('%Y-%m-%d')
        
        # Check permission
        data_ip = "https://raw.githubusercontent.com/MikkuChan/instalasi/main/register"
        response = requests.get(data_ip, timeout=10)
        
        for line in response.text.split('\n'):
            if myip in line:
                parts = line.split()
                if len(parts) >= 3:
                    useexp = parts[2]
                    if date_list > useexp:
                        print(f"{Colors.RED}Permission Denied!{Colors.NC}")
                        sys.exit(1)
                    return myip
        
        print(f"{Colors.RED}IP not registered!{Colors.NC}")
        sys.exit(1)
        
    except Exception as e:
        print(f"{Colors.RED}Error checking permission: {e}{Colors.NC}")
        sys.exit(1)

def get_domain():
    """Get domain from configuration"""
    try:
        # Try to read from ipvps.conf
        if os.path.exists('/var/lib/kyt/ipvps.conf'):
            with open('/var/lib/kyt/ipvps.conf', 'r') as f:
                for line in f:
                    if line.startswith('IP='):
                        ip = line.split('=')[1].strip().strip('"\'')
                        if ip:
                            return ip
        
        # Fallback to domain file
        if os.path.exists('/etc/xray/domain'):
            with open('/etc/xray/domain', 'r') as f:
                return f.read().strip()
        
        # If no domain file, use IP
        return get_server_ip()
        
    except Exception:
        return get_server_ip()

def get_location_info():
    """Get server location information"""
    try:
        response = requests.get('https://ipinfo.io/json', timeout=10)
        location = response.json()
        return {
            'city': location.get('city', 'Unknown'),
            'isp': location.get('org', 'Unknown'),
            'ip': get_server_ip()
        }
    except:
        return {
            'city': 'Unknown',
            'isp': 'Unknown', 
            'ip': get_server_ip()
        }

def send_telegram(user, domain, user_uuid, quota, iplimit, masaaktif, tnggl, expe, trojanlink, trojanlink1):
    """Send account details to Telegram"""
    try:
        # Read bot configuration
        with open('/etc/telegram_bot/bot_token', 'r') as f:
            bot_token = f.read().strip()
        with open('/etc/telegram_bot/chat_id', 'r') as f:
            chat_id = f.read().strip()
        
        location_info = get_location_info()
        
        text = f"""<b>━━━━━━ 𝙏𝙍𝙊𝙅𝘼𝙉 𝙋𝙍𝙀𝙈𝙄𝙐𝙈 ━━━━━━</b>

<b>👤 𝙐𝙨𝙚𝙧 𝘿𝙚𝙩𝙖𝙞𝙡𝙨</b>
┣ <b>Username</b>   : <code>{user}</code>
┣ <b>UUID/PASSWORD</b>       : <code>{user_uuid}</code>
┣ <b>Quota</b>      : <code>{quota} GB</code>
┣ <b>Status</b>     : <code>Aktif {masaaktif} hari</code>
┣ <b>Dibuat</b>     : <code>{tnggl}</code>
┗ <b>Expired</b>    : <code>{expe}</code>

<b>🌎 𝙎𝙚𝙧𝙫𝙚𝙧 𝙄𝙣𝙛𝙤</b>
┣ <b>Domain</b>     : <code>{domain}</code>
┣ <b>IP</b>         : <code>{location_info['ip']}</code>
┣ <b>Location</b>   : <code>{location_info['city']}</code>
┗ <b>ISP</b>        : <code>{location_info['isp']}</code>

<b>🔗 𝘾𝙤𝙣𝙣𝙚𝙘𝙩𝙞𝙤𝙣</b>
┣ <b>TLS Port</b>        : <code>400-900</code>
┣ <b>Network</b>         : <code>ws, grpc</code>
┣ <b>Path</b>            : <code>/trojan-ws</code>
┗ <b>gRPC Service</b>    : <code>trojan-grpc</code>

<b>━━━━━ 𝙏𝙍𝙊𝙅𝘼𝙉 𝙋𝙧𝙚𝙢𝙞𝙪𝙢 𝙇𝙞𝙣𝙠𝙨 ━━━━━</b>
<b>📍 𝙒𝙎 𝙏𝙇𝙎</b>
<pre>{trojanlink}</pre>
<b>📍 𝙜𝙍𝙋𝘾</b>
<pre>{trojanlink1}</pre>

<b>📥 𝘾𝙤𝙣𝙛𝙞𝙜 𝙁𝙞𝙡𝙚 (Clash/OpenClash):</b>
https://{domain}:81/trojan-{user}.txt

<b>✨ 𝙏𝙤𝙤𝙡𝙨 & 𝙍𝙚𝙨𝙤𝙪𝙧𝙘𝙚𝙨</b>
┣ <a href='https://vpntech.my.id/converteryaml'>YAML Converter</a>
┗ <a href='https://vpntech.my.id/auto-configuration'>Auto Configuration</a>

<b>❓ 𝘽𝙪𝙩𝙪𝙝 𝘽𝙖𝙣𝙩𝙪𝙖𝙣?</b>
<a href='https://t.me/085727035336'>Klik di sini untuk chat Admin</a>

<b>━━━━━━━━━ 𝙏𝙝𝙖𝙣𝙠 𝙔𝙤𝙪 ━━━━━━━━</b>"""

        # Send to Telegram
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        
        requests.post(url, data=data, timeout=10)
        
    except Exception as e:
        print(f"Warning: Failed to send Telegram notification: {e}")

def update_xray_config(user, user_uuid, exp):
    """Update Xray configuration"""
    config_file = '/etc/xray/config.json'
    
    # Read current config
    with open(config_file, 'r') as f:
        content = f.read()
    
    # Add trojan WS user
    trojanws_pattern = r'(#trojanws\$)'
    trojanws_replacement = f'#! {user} {exp}\n}},{{"password": "{user_uuid}","email": "{user}"\n\\1'
    content = re.sub(trojanws_pattern, trojanws_replacement, content)
    
    # Add trojan gRPC user  
    trojangrpc_pattern = r'(#trojangrpc\$)'
    trojangrpc_replacement = f'#! {user} {exp}\n}},{{"password": "{user_uuid}","email": "{user}"\n\\1'
    content = re.sub(trojangrpc_pattern, trojangrpc_replacement, content)
    
    # Write back to file
    with open(config_file, 'w') as f:
        f.write(content)

def create_clash_config(user, domain, user_uuid):
    """Create Clash configuration file"""
    config_content = f"""# Format TROJAN For Clash #
- name: Trojan-{user}-GO/WS
  server: {domain}
  port: 443
  type: trojan
  password: {user_uuid}
  network: ws
  sni: {domain}
  skip-cert-verify: true
  udp: true
  ws-opts:
    path: /trojan-ws
    headers:
        Host: {domain}
- name: Trojan-{user}-gRPC
  type: trojan
  server: {domain}
  port: 443
  password: {user_uuid}
  udp: true
  sni: {domain}
  skip-cert-verify: true
  network: grpc
  grpc-opts:
    grpc-service-name: trojan-grpc"""

    config_path = f'/var/www/html/trojan-{user}.txt'
    with open(config_path, 'w') as f:
        f.write(config_content)

def set_ip_limit(user, iplimit):
    """Set IP limit for user"""
    if iplimit > 0:
        limit_dir = '/etc/kyt/limit/trojan/ip'
        os.makedirs(limit_dir, exist_ok=True)
        with open(f'{limit_dir}/{user}', 'w') as f:
            f.write(str(iplimit))

def set_quota_limit(user, quota):
    """Set data quota limit for user"""
    if not os.path.exists('/etc/trojan'):
        os.makedirs('/etc/trojan')
    
    # Convert GB to bytes
    quota_num = int(re.sub(r'[^0-9]', '', str(quota)))
    if quota_num != 0:
        quota_bytes = quota_num * 1024 * 1024 * 1024
        with open(f'/etc/trojan/{user}', 'w') as f:
            f.write(str(quota_bytes))

def update_user_database(user, exp, user_uuid, quota, iplimit):
    """Update user database"""
    db_file = '/etc/trojan/.trojan.db'
    
    # Create database file if it doesn't exist
    if not os.path.exists('/etc/trojan'):
        os.makedirs('/etc/trojan')
    if not os.path.exists(db_file):
        open(db_file, 'a').close()
    
    # Remove existing user entry if exists
    if os.path.exists(db_file):
        with open(db_file, 'r') as f:
            lines = f.readlines()
        
        with open(db_file, 'w') as f:
            for line in lines:
                if not (line.startswith('###') and user in line):
                    f.write(line)
    
    # Add new user entry
    with open(db_file, 'a') as f:
        f.write(f"### {user} {exp} {user_uuid} {quota} {iplimit}\n")

def restart_services():
    """Restart required services"""
    try:
        subprocess.run(['systemctl', 'restart', 'xray'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['systemctl', 'reload', 'xray'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['systemctl', 'reload', 'nginx'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['service', 'cron', 'restart'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to restart some services: {e}")

def write_log(user, user_uuid, quota, iplimit, masaaktif, tnggl, expe, domain, location_info, trojanlink, trojanlink1):
    """Write to log file"""
    log_dir = '/etc/user-create'
    os.makedirs(log_dir, exist_ok=True)
    log_file = f'{log_dir}/user.log'
    
    log_content = f"""━━━━━━━━━━━ TROJAN PREMIUM ACCOUNT ━━━━━━━━━━━
┣ Username   : {user}
┣ Password   : {user_uuid}
┣ Quota      : {quota} GB
┣ Limit IP   : {iplimit} IP
┣ Status     : Aktif {masaaktif} hari
┣ Dibuat     : {tnggl}
┗ Expired    : {expe}

🌎 Server Info
┣ Domain     : {domain}
┣ VPS IP     : {location_info['ip']}
┣ Location   : {location_info['city']}
┗ ISP        : {location_info['isp']}

🔌 Connection
┣ TLS Port        : 400-900
┣ Network         : ws, grpc
┣ Path            : /trojan-ws
┣ gRPC Service    : trojan-grpc
┗ Encryption      : tls

🚀 TROJAN Premium Links
• WS TLS : {trojanlink}
• gRPC   : {trojanlink1}

📥 Config File (Clash/OpenClash):
https://{domain}:81/trojan-{user}.txt

✨ Tools & Resources
┣ https://vpntech.my.id/converteryaml
┗ https://vpntech.my.id/auto-configuration

Aktif Selama : {masaaktif} hari
Dibuat Pada  : {tnggl}
Expired Pada : {expe}
━━━━━━━━━━━ Thank You ━━━━━━━━━━━

"""

    with open(log_file, 'a') as f:
        f.write(log_content)
    
    # Also print to console
    print(log_content)

def check_user_exists(user):
    """Check if user already exists in Xray config"""
    try:
        with open('/etc/xray/config.json', 'r') as f:
            content = f.read()
            return user in content
    except FileNotFoundError:
        return False

def create_trojan_user(user, user_uuid, masaaktif, quota, iplimit):
    """Main function to create TROJAN user"""
    
    # Calculate dates
    exp_date = datetime.now() + timedelta(days=int(masaaktif))
    exp = exp_date.strftime('%Y-%m-%d')
    expe = exp_date.strftime('%d %b, %Y')
    tnggl = datetime.now().strftime('%d %b, %Y')
    
    # Get domain and location info
    domain = get_domain()
    location_info = get_location_info()
    
    # Update Xray configuration
    update_xray_config(user, user_uuid, exp)
    
    # Create Clash configuration
    create_clash_config(user, domain, user_uuid)
    
    # Set limits
    set_ip_limit(user, int(iplimit))
    set_quota_limit(user, quota)
    
    # Update database
    update_user_database(user, exp, user_uuid, quota, iplimit)
    
    # Restart services
    restart_services()
    
    # Generate links
    trojanlink = f"trojan://{user_uuid}@{domain}:443?path=%2Ftrojan-ws&security=tls&host={domain}&type=ws&sni={domain}#{user}"
    trojanlink1 = f"trojan://{user_uuid}@{domain}:443?mode=gun&security=tls&type=grpc&serviceName=trojan-grpc&sni={domain}#{user}"
    
    # Send Telegram notification
    send_telegram(user, domain, user_uuid, quota, iplimit, masaaktif, tnggl, expe, trojanlink, trojanlink1)
    
    # Write to log
    write_log(user, user_uuid, quota, iplimit, masaaktif, tnggl, expe, domain, location_info, trojanlink, trojanlink1)

def main():
    """Main function"""
    # Check permission first
    myip = check_permission()
    
    # Parse arguments
    if len(sys.argv) == 5:
        # Format: username day limit_data_GB limit_ip (random UUID)
        user = sys.argv[1]
        masaaktif = sys.argv[2]
        quota = sys.argv[3]
        iplimit = sys.argv[4]
        user_uuid = str(uuid.uuid4())
        
    elif len(sys.argv) == 6:
        # Format: username uuid day limit_data_GB limit_ip (custom UUID)
        user = sys.argv[1]
        user_uuid = sys.argv[2]
        masaaktif = sys.argv[3]
        quota = sys.argv[4]
        iplimit = sys.argv[5]
        
    else:
        print(f"{Colors.YELLOW}Usage:{Colors.NC}")
        print(f"  python3 {sys.argv[0]} {{username}} {{day}} {{limit_data_GB}} {{limit_ip}}")
        print(f"  python3 {sys.argv[0]} {{username}} {{uuid}} {{day}} {{limit_data_GB}} {{limit_ip}}")
        sys.exit(1)
    
    # Check if user already exists
    if check_user_exists(user):
        print(f"{Colors.RED}User {user} sudah ada, silakan pilih username lain.{Colors.NC}")
        sys.exit(2)
    
    # Create the user
    create_trojan_user(user, user_uuid, masaaktif, quota, iplimit)

if __name__ == "__main__":
    main()