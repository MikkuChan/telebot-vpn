#!/usr/bin/env python3
"""
create-vless: Otomatisasi pembuatan akun VLESS dengan/atau tanpa custom UUID via perintah
Cara pakai:
1) python create_vless.py {username} {day} {limit_data_GB} {limit_ip}
2) python create_vless.py {username} {uuid} {day} {limit_data_GB} {limit_ip}
"""

import sys
import os
import json
import subprocess
import uuid as uuid_module
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta
import re

# --- WARNA & VARIABEL DASAR ---
class Colors:
    RED = "\033[31m"
    YELLOW = "\033[33m"
    NC = '\033[0m'
    GREEN = '\033[0;32m'

def get_external_ip():
    """Mendapatkan IP eksternal"""
    try:
        with urllib.request.urlopen('https://ipv4.icanhazip.com', timeout=10) as response:
            return response.read().decode().strip()
    except:
        try:
            with urllib.request.urlopen('https://ifconfig.me', timeout=10) as response:
                return response.read().decode().strip()
        except:
            return "0.0.0.0"

def check_permission():
    """Cek permission VPS"""
    try:
        myip = get_external_ip()
        data_ip = "https://raw.githubusercontent.com/MikkuChan/instalasi/main/register"
        
        # Get server date
        req = urllib.request.Request('https://google.com/')
        with urllib.request.urlopen(req) as response:
            date_header = response.headers.get('Date', '')
        
        if date_header:
            # Parse date from header
            from datetime import datetime
            import email.utils
            date_tuple = email.utils.parsedate(date_header)
            if date_tuple:
                server_date = datetime(*date_tuple[:6])
                date_list = server_date.strftime("%Y-%m-%d")
            else:
                date_list = datetime.now().strftime("%Y-%m-%d")
        else:
            date_list = datetime.now().strftime("%Y-%m-%d")
        
        # Check IP registration
        with urllib.request.urlopen(data_ip, timeout=10) as response:
            data = response.read().decode()
            for line in data.split('\n'):
                if myip in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        useexp = parts[2]
                        if date_list > useexp:
                            print(f"{Colors.RED}Permission Denied!{Colors.NC}")
                            sys.exit(1)
                        return True
        
        print(f"{Colors.RED}Permission Denied!{Colors.NC}")
        sys.exit(1)
        
    except Exception as e:
        print(f"{Colors.RED}Error checking permission: {e}{Colors.NC}")
        sys.exit(1)

def get_domain():
    """Mendapatkan domain dari konfigurasi"""
    try:
        with open('/etc/xray/domain', 'r') as f:
            return f.read().strip()
    except Exception:
        return get_external_ip()

def get_location_info():
    """Mendapatkan informasi lokasi server"""
    try:
        with urllib.request.urlopen('https://ipinfo.io/json', timeout=10) as response:
            data = json.loads(response.read().decode())
            return {
                'city': data.get('city', 'Tidak diketahui'),
                'org': data.get('org', 'Tidak diketahui')
            }
    except:
        return {'city': 'Tidak diketahui', 'org': 'Tidak diketahui'}

def send_telegram(user, domain, uuid, quota, iplimit, masaaktif, tnggl, expe, vlesslink1, vlesslink2, vlesslink3):
    """Kirim notifikasi ke Telegram"""
    try:
        # Read bot token and chat ID
        if not os.path.exists('/etc/telegram_bot/bot_token') or not os.path.exists('/etc/telegram_bot/chat_id'):
            return False
            
        with open('/etc/telegram_bot/bot_token', 'r') as f:
            bot_token = f.read().strip()
        with open('/etc/telegram_bot/chat_id', 'r') as f:
            chat_id = f.read().strip()
        
        if not bot_token or not chat_id:
            return False
        
        location = get_location_info()
        myip = get_external_ip()
        
        text = f"""<b>━━━━━━ 𝙑𝙇𝙀𝙎𝙎 𝙋𝙍𝙀𝙈𝙄𝙐𝙈 ━━━━━━</b>

<b>👤 𝙐𝙨𝙚𝙧 𝘿𝙚𝙩𝙖𝙞𝙡𝙨</b>
┣ <b>Username</b>   : <code>{user}</code>
┣ <b>UUID</b>       : <code>{uuid}</code>
┣ <b>Quota</b>      : <code>{quota} GB</code>
┣ <b>Status</b>     : <code>Aktif {masaaktif} hari</code>
┣ <b>Dibuat</b>     : <code>{tnggl}</code>
┗ <b>Expired</b>    : <code>{expe}</code>

<b>🌎 𝙎𝙚𝙧𝙫𝙚𝙧 𝙄𝙣𝙛𝙤</b>
┣ <b>Domain</b>     : <code>{domain}</code>
┣ <b>IP</b>         : <code>{myip}</code>
┣ <b>Location</b>   : <code>{location['city']}</code>
┗ <b>ISP</b>        : <code>{location['org']}</code>

<b>🔗 𝘾𝙤𝙣𝙣𝙚𝙘𝙩𝙞𝙤𝙣</b>
┣ <b>TLS Port</b>        : <code>400-900</code>
┣ <b>Non-TLS Port</b>    : <code>80, 8080, 8081-9999</code>
┣ <b>Network</b>         : <code>ws, grpc</code>
┣ <b>Path</b>            : <code>/vless</code>
┣ <b>gRPC Service</b>    : <code>vless-grpc</code>
┗ <b>Encryption</b>        : <code>none</code>

<b>━━━━━ 𝙑𝙇𝙀𝙎𝙎 𝙋𝙧𝙚𝙢𝙞𝙪𝙢 𝙇𝙞𝙣𝙠𝙨 ━━━━━</b>
<b>📍 𝙒𝙎 𝙏𝙇𝙎</b>
<pre>{vlesslink1}</pre>
<b>📍 𝙒𝙎 𝙉𝙤𝙣-𝙏𝙇𝙎</b>
<pre>{vlesslink2}</pre>
<b>📍 𝙜𝙍𝙋𝘾</b>
<pre>{vlesslink3}</pre>

<b>📥 𝘾𝙤𝙣𝙛𝙞𝙜 𝙁𝙞𝙡𝙚 (Clash/OpenClash):</b>
https://{domain}:81/vless-{user}.txt

<b>✨ 𝙏𝙤𝙤𝙡𝙨 & 𝙍𝙚𝙨𝙤𝙪𝙧𝙘𝙚𝙨</b>
┣ <a href='https://vpntech.my.id/converteryaml'>YAML Converter</a>
┗ <a href='https://vpntech.my.id/auto-configuration'>Auto Configuration</a>

<b>❓ 𝘽𝙪𝙩𝙪𝙝 𝘽𝙖𝙣𝙩𝙪𝙖𝙣?</b>
<a href='https://t.me/085727035336'>Klik di sini untuk chat Admin</a>

<b>━━━━━━━━━ 𝙏𝙝𝙖𝙣𝙠 𝙔𝙤𝙪 ━━━━━━━━</b>"""

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'disable_web_page_preview': '1',
            'text': text,
            'parse_mode': 'html'
        }
        
        req_data = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(url, data=req_data, method='POST')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.getcode() == 200
            
    except Exception as e:
        print(f"Warning: Failed to send Telegram notification: {e}")
        return False

def create_vless_user(user, uuid, masaaktif, quota, iplimit):
    """Fungsi utama pembuatan user VLESS"""
    domain = get_domain()
    
    # Calculate expiry dates
    exp_date = datetime.now() + timedelta(days=int(masaaktif))
    exp = exp_date.strftime("%Y-%m-%d")
    expe = exp_date.strftime("%d %b, %Y")
    tnggl = datetime.now().strftime("%d %b, %Y")
    
    # Add to Xray config
    try:
        with open('/etc/xray/config.json', 'r') as f:
            content = f.read()
        
        # Add VLESS user
        vless_entry = f'#& {user} {exp}\n}},{{"id": "{uuid}","email" : "{user}"}}'
        content = content.replace('#vless$', f'#vless$\n{vless_entry}')
        
        # Add VLESS gRPC user
        vlessgrpc_entry = f'#& {user} {exp}\n}},{{"id": "{uuid}","email" : "{user}"}}'
        content = content.replace('#vlessgrpc$', f'#vlessgrpc$\n{vlessgrpc_entry}')
        
        with open('/etc/xray/config.json', 'w') as f:
            f.write(content)
            
    except Exception as e:
        print(f"{Colors.RED}Error updating Xray config: {e}{Colors.NC}")
        sys.exit(1)
    
    # Create VLESS links
    vlesslink1 = f"vless://{uuid}@bugmu.com:443/?type=ws&encryption=none&host={domain}&path=%2Fvless&security=tls&sni={domain}&fp=randomized#{user}"
    vlesslink2 = f"vless://{uuid}@bugmu.com:80/?type=ws&encryption=none&host={domain}&path=%2Fvless#{user}"
    vlesslink3 = f"vless://{uuid}@bugmu.com:443/?type=grpc&encryption=none&flow=&serviceName=vless-grpc&security=tls&sni={domain}#{user}"
    
    # Create Clash config file
    clash_config = f"""# FORMAT OpenClash #
# VLESS WS TLS
- name: Vless-{user}-WS TLS
  server: bugmu.com
  port: 443
  type: vless
  uuid: {uuid}
  cipher: auto
  tls: true
  skip-cert-verify: true
  servername: {domain}
  network: ws
  ws-opts:
    path: /vless
    headers:
      Host: {domain}
  udp: true

# VLESS WS NON TLS
- name: Vless-{user}-WS (CDN) Non TLS
  server: bugmu.com
  port: 80
  type: vless
  uuid: {uuid}
  cipher: auto
  tls: false
  skip-cert-verify: false
  servername: {domain}
  network: ws
  ws-opts:
    path: /vless
    headers:
      Host: {domain}
  udp: true

# VLESS gRPC
- name: Vless-{user}-gRPC (SNI)
  server: {domain}
  port: 443
  type: vless
  uuid: {uuid}
  cipher: auto
  tls: true
  skip-cert-verify: true
  servername: {domain}
  network: grpc
  grpc-opts:
    grpc-service-name: vless-grpc
  udp: true

# VLESS WS TLS
{vlesslink1}

# VLESS WS NON TLS
{vlesslink2}

# VLESS WS gRPC
{vlesslink3}
"""
    
    # Save Clash config
    os.makedirs('/var/www/html', exist_ok=True)
    with open(f'/var/www/html/vless-{user}.txt', 'w') as f:
        f.write(clash_config)
    
    # Set IP limit
    if int(iplimit) > 0:
        os.makedirs('/etc/kyt/limit/vless/ip', exist_ok=True)
        with open(f'/etc/kyt/limit/vless/ip/{user}', 'w') as f:
            f.write(str(iplimit))
    
    # Set data limit
    os.makedirs('/etc/vless', exist_ok=True)
    quota_num = int(re.sub(r'[^0-9]', '', str(quota)))
    if quota_num > 0:
        quota_bytes = quota_num * 1024 * 1024 * 1024
        with open(f'/etc/vless/{user}', 'w') as f:
            f.write(str(quota_bytes))
    
    # Update database
    db_file = '/etc/vless/.vless.db'
    os.makedirs('/etc/vless', exist_ok=True)
    
    # Remove existing entry if exists
    if os.path.exists(db_file):
        with open(db_file, 'r') as f:
            lines = f.readlines()
        
        with open(db_file, 'w') as f:
            for line in lines:
                if not (line.startswith('###') and user in line):
                    f.write(line)
    
    # Add new entry
    with open(db_file, 'a') as f:
        f.write(f"### {user} {exp} {uuid} {quota} {iplimit}\n")
    
    # Restart services
    try:
        subprocess.run(['systemctl', 'restart', 'xray'], check=False, capture_output=True)
        subprocess.run(['systemctl', 'restart', 'nginx'], check=False, capture_output=True)
    except Exception as e:
        print(f"Warning: Failed to restart some services: {e}")
    
    # Send Telegram notification
    send_telegram(user, domain, uuid, quota, iplimit, masaaktif, tnggl, expe, vlesslink1, vlesslink2, vlesslink3)
    
    # Create log
    log_file = "/etc/user-create/user.log"
    os.makedirs('/etc/user-create', exist_ok=True)
    
    location = get_location_info()
    myip = get_external_ip()
    
    log_content = f"""━━━━━━━━━━━ VLESS PREMIUM ACCOUNT ━━━━━━━━━━━
┣ Username   : {user}
┣ UUID       : {uuid}
┣ Quota      : {quota} GB
┣ Limit IP   : {iplimit} IP
┣ Status     : Aktif {masaaktif} hari
┣ Dibuat     : {tnggl}
┗ Expired    : {expe}

🌎 Server Info
┣ Domain     : {domain}
┣ VPS IP     : {myip}
┣ Location   : {location['city']}
┗ ISP        : {location['org']}

🔌 Connection
┣ TLS Port        : 400-900
┣ Non-TLS Port    : 80, 8080, 8081-9999
┣ Network         : ws, grpc
┣ Path            : /vless
┣ gRPC Service    : vless-grpc
┗ Encryption      : none

🚀 VLESS Premium Links
• WS TLS : {vlesslink1}
• WS Non-TLS : {vlesslink2}
• gRPC   : {vlesslink3}

📥 Config File (Clash/OpenClash):
https://{domain}:81/vless-{user}.txt

✨ Tools & Resources
┣ https://vpntech.my.id/converteryaml
┗ https://vpntech.my.id/auto-configuration

Aktif Selama : {masaaktif} hari
Dibuat Pada  : {tnggl}
Expired Pada : {expe}
━━━━━━━━━━━ Thank You ━━━━━━━━━━━
"""
    
    # Write and display log
    with open(log_file, 'a') as f:
        f.write(log_content + '\n')
    
    print(log_content)

def check_user_exists(username):
    """Cek apakah user sudah ada"""
    try:
        with open('/etc/xray/config.json', 'r') as f:
            content = f.read()
            return username in content
    except:
        return False

def main():
    """Fungsi utama program"""
    
    # Check permission
    check_permission()
    
    # Parse arguments
    if len(sys.argv) == 5:
        user = sys.argv[1]
        masaaktif = sys.argv[2]
        quota = sys.argv[3]
        iplimit = sys.argv[4]
        uuid = str(uuid_module.uuid4())
    elif len(sys.argv) == 6:
        user = sys.argv[1]
        uuid = sys.argv[2]
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
    
    # Validate inputs
    try:
        int(masaaktif)
        float(quota)
        int(iplimit)
    except ValueError:
        print(f"{Colors.RED}Error: Pastikan day, quota, dan limit_ip berupa angka yang valid{Colors.NC}")
        sys.exit(1)
    
    # Create VLESS user
    create_vless_user(user, uuid, masaaktif, quota, iplimit)

if __name__ == "__main__":
    main()