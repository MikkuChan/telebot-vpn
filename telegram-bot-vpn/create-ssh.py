#!/usr/bin/env python3
"""
create-ssh: Otomatisasi pembuatan akun SSH dengan password random/custom via CLI
Cara pakai:
1) python3 create_ssh.py {username} {day} {limit_data_GB} {limit_ip}                (password random)
2) python3 create_ssh.py {username} {password} {day} {limit_data_GB} {limit_ip}     (password custom)
"""

import sys
import os
import subprocess
import requests
import random
import string
import json
import urllib.parse
from datetime import datetime, timedelta
import pwd
import re

# Konstanta warna
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    NC = '\033[0m'

def get_server_ip():
    """Mendapatkan IP address server"""
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
    """Cek permission VPS"""
    try:
        myip = get_server_ip()
        if not myip:
            print(f"{Colors.RED}Tidak dapat mendapatkan IP server{Colors.NC}")
            sys.exit(1)
        
        # Mendapatkan tanggal server
        response = requests.get('https://google.com/', timeout=10, allow_redirects=False)
        date_header = response.headers.get('Date', '')
        
        if date_header:
            server_date = datetime.strptime(date_header, '%a, %d %b %Y %H:%M:%S %Z')
            date_list = server_date.strftime('%Y-%m-%d')
        else:
            date_list = datetime.now().strftime('%Y-%m-%d')
        
        # Cek permission
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
        
        print(f"{Colors.RED}IP tidak terdaftar!{Colors.NC}")
        sys.exit(1)
        
    except Exception as e:
        print(f"{Colors.RED}Error saat cek permission: {e}{Colors.NC}")
        sys.exit(1)

def get_server_info():
    """Mendapatkan informasi server (domain, city, ISP)"""
    info = {
        'ip': get_server_ip(),
        'domain': 'localhost',
        'city': 'N/A',
        'isp': 'N/A'
    }
    
    try:
        # Baca domain
        if os.path.exists('/etc/xray/domain'):
            with open('/etc/xray/domain', 'r') as f:
                info['domain'] = f.read().strip()
        
        # Baca city
        if os.path.exists('/etc/xray/city'):
            with open('/etc/xray/city', 'r') as f:
                info['city'] = f.read().strip()
        
        # Baca ISP
        if os.path.exists('/etc/xray/isp'):
            with open('/etc/xray/isp', 'r') as f:
                info['isp'] = f.read().strip()
                
    except Exception:
        pass
    
    return info

def generate_random_password(length=10):
    """Generate password random"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def check_user_exists(username):
    """Cek apakah user sudah ada"""
    try:
        pwd.getpwnam(username)
        return True
    except KeyError:
        return False

def create_system_user(username, password, days):
    """Membuat user sistem dengan expiry date"""
    try:
        # Hitung tanggal expiry
        exp_date = datetime.now() + timedelta(days=int(days))
        exp_str = exp_date.strftime('%Y-%m-%d')
        
        # Buat user dengan expiry date
        subprocess.run([
            'useradd', '-e', exp_str, '-s', '/bin/false', '-M', username
        ], check=True)
        
        # Set password
        process = subprocess.Popen(['passwd', username], stdin=subprocess.PIPE, 
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        process.communicate(input=f"{password}\n{password}\n".encode())
        
        return True
    except subprocess.CalledProcessError:
        return False

def set_ip_limit(username, iplimit):
    """Set limit IP untuk user"""
    if int(iplimit) > 0:
        limit_dir = '/etc/kyt/limit/ssh/ip'
        os.makedirs(limit_dir, exist_ok=True)
        with open(f'{limit_dir}/{username}', 'w') as f:
            f.write(str(iplimit))

def set_quota_limit(username, quota):
    """Set limit quota data untuk user"""
    if not os.path.exists('/etc/ssh'):
        os.makedirs('/etc/ssh')
    
    # Konversi GB ke bytes
    quota_num = int(re.sub(r'[^0-9]', '', str(quota)))
    if quota_num != 0:
        quota_bytes = quota_num * 1024 * 1024 * 1024
        with open(f'/etc/ssh/{username}', 'w') as f:
            f.write(str(quota_bytes))

def update_ssh_database(username, password, quota, iplimit, expe):
    """Update database SSH"""
    db_file = '/etc/ssh/.ssh.db'
    
    # Buat direktori jika belum ada
    if not os.path.exists('/etc/ssh'):
        os.makedirs('/etc/ssh')
    if not os.path.exists(db_file):
        open(db_file, 'a').close()
    
    # Hapus entry user yang sudah ada
    if os.path.exists(db_file):
        with open(db_file, 'r') as f:
            lines = f.readlines()
        
        with open(db_file, 'w') as f:
            for line in lines:
                if not (line.startswith('#ssh#') and username in line):
                    f.write(line)
    
    # Tambah entry user baru
    with open(db_file, 'a') as f:
        f.write(f"#ssh# {username} {password} {quota} {iplimit} {expe}\n")

def create_account_file(username, password, server_info, days, expe, tnggl):
    """Membuat file akun SSH"""
    content = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Format SSH OVPN Account
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Username         : {username}
Password         : {password}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IP               : {server_info['ip']}
Host             : {server_info['domain']}
Port OpenSSH     : 443, 80, 22
Port Dropbear    : 443, 109
Port Dropbear WS : 443, 109
Port SSH UDP     : 1-65535
Port SSH WS      : 80, 8080, 8081-9999
Port SSH SSL WS  : 443
Port SSL/TLS     : 400-900
Port OVPN WS SSL : 443
Port OVPN SSL    : 443
Port OVPN TCP    : 1194
Port OVPN UDP    : 2200
BadVPN UDP       : 7100, 7300, 7300
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Aktif Selama     : {days} Hari
Dibuat Pada      : {tnggl}
Berakhir Pada    : {expe}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Payload WSS   : GET wss://BUG.COM/ HTTP/1.1[crlf]Host: {server_info['domain']}[crlf]Upgrade: websocket[crlf][crlf] 
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OVPN Download : https://{server_info['domain']}:81/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
    
    file_path = f'/var/www/html/ssh-{username}.txt'
    with open(file_path, 'w') as f:
        f.write(content)

def send_telegram_ssh(username, password, quota, iplimit, days, tnggl, expe, server_info):
    """Kirim notifikasi Telegram dengan style premium"""
    try:
        # Baca konfigurasi bot (sama seperti TROJAN)
        with open('/etc/telegram_bot/bot_token', 'r') as f:
            bot_token = f.read().strip()
        with open('/etc/telegram_bot/chat_id', 'r') as f:
            chat_id = f.read().strip()
        
        text = f"""<b>━━━━━ 𝙎𝙎𝙃/𝙊𝙑𝙋𝙉 𝙋𝙍𝙀𝙈𝙄𝙐𝙈 ━━━━━</b>

<b>👤 𝙐𝙨𝙚𝙧 𝘿𝙚𝙩𝙖𝙞𝙡𝙨</b>
┣ <b>Username</b>   : <code>{username}</code>
┣ <b>Password</b>   : <code>{password}</code>
┣ <b>Quota</b>      : <code>{quota} GB</code>
┣ <b>Status</b>     : <code>Aktif {days} hari</code>
┣ <b>Dibuat</b>     : <code>{tnggl}</code>
┗ <b>Expired</b>    : <code>{expe}</code>

<b>🌎 𝙎𝙚𝙧𝙫𝙚𝙧 𝙄𝙣𝙛𝙤</b>
┣ <b>Domain</b>     : <code>{server_info['domain']}</code>
┣ <b>IP</b>     : <code>{server_info['ip']}</code>
┣ <b>Location</b>   : <code>{server_info['city']}</code>
┗ <b>ISP</b>        : <code>{server_info['isp']}</code>

<b>🔌 𝘾𝙤𝙣𝙣𝙚𝙘𝙩𝙞𝙤𝙣</b>
┣ <b>Port OpenSSH</b>     : <code>443, 80, 22</code>
┣ <b>Port Dropbear</b>    : <code>443, 109</code>
┣ <b>Port SSH WS</b>      : <code>80,8080,8081-9999</code>
┣ <b>Port SSH SSL WS</b>  : <code>443</code>
┣ <b>Port SSH UDP</b>     : <code>1-65535</code>
┣ <b>Port SSL/TLS</b>     : <code>400-900</code>
┣ <b>Port OVPN WS SSL</b> : <code>443</code>
┣ <b>Port OVPN TCP</b>    : <code>1194</code>
┣ <b>Port OVPN UDP</b>    : <code>2200</code>
┗ <b>BadVPN UDP</b>       : <code>7100,7300,7300</code>

<b>⚡ 𝙋𝙖𝙮𝙡𝙤𝙖𝙙 𝙒𝙎</b>
<code>GET / HTTP/1.1[crlf]Host: [host][crlf]Connection: Upgrade[crlf]User-Agent: [ua][crlf]Upgrade: websocket[crlf][crlf]</code>

<b>⚡ 𝙋𝙖𝙮𝙡𝙤𝙖𝙙 𝙒𝙎𝙎</b>
<code>GET wss://BUG.COM/ HTTP/1.1[crlf]Host: {server_info['domain']}[crlf]Upgrade: websocket[crlf][crlf]</code>

<b>📥 𝙊𝙑𝙋𝙉 𝘿𝙤𝙬𝙣𝙡𝙤𝙖𝙙</b>
<code>https://{server_info['domain']}:81/</code>

<b>📝 𝙎𝙖𝙫𝙚 𝙇𝙞𝙣𝙠 𝘼𝙠𝙪𝙣</b>
https://{server_info['domain']}:81/ssh-{username}.txt

<b>━━━━━━━━━ 𝙏𝙝𝙖𝙣𝙠 𝙔𝙤𝙪 ━━━━━━━━</b>"""

        # Kirim ke Telegram
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        
        requests.post(url, data=data, timeout=10)
        
    except Exception as e:
        print(f"Warning: Gagal mengirim notifikasi Telegram: {e}")

def write_log(username, password, quota, iplimit, days, tnggl, expe, server_info):
    """Tulis ke file log"""
    log_dir = '/etc/user-create'
    os.makedirs(log_dir, exist_ok=True)
    log_file = f'{log_dir}/user.log'
    
    log_content = f"""━━━━━━━━━━━ SSH/OVPN PREMIUM ACCOUNT ━━━━━━━━━━━
┣ Username   : {username}
┣ Password   : {password}
┣ Quota      : {quota} GB
┣ Limit IP   : {iplimit} IP
┣ Status     : Aktif {days} hari
┣ Dibuat     : {tnggl}
┗ Expired    : {expe}

🌎 𝙎𝙚𝙧𝙫𝙚𝙧 𝙄𝙣𝙛𝙤
┣ Domain     : {server_info['domain']}
┣ VPS IP     : {server_info['ip']}
┣ Location   : {server_info['city']}
┗ ISP        : {server_info['isp']}

🔌 𝘾𝙤𝙣𝙣𝙚𝙘𝙩𝙞𝙤𝙣
┣ Port OpenSSH     : 443, 80, 22
┣ Port Dropbear    : 443, 109
┣ Port SSH WS      : 80,8080,8081-9999
┣ Port SSH SSL WS  : 443
┣ Port SSH UDP     : 1-65535
┣ Port SSL/TLS     : 400-900
┣ Port OVPN WS SSL : 443
┣ Port OVPN TCP    : 1194
┣ Port OVPN UDP    : 2200
┗ BadVPN UDP       : 7100,7300,7300

⚡ Payload WS
GET / HTTP/1.1[crlf]Host: [host][crlf]Connection: Upgrade[crlf]User-Agent: [ua][crlf]Upgrade: websocket[crlf][crlf]

⚡ Payload WSS
GET wss://BUG.COM/ HTTP/1.1[crlf]Host: {server_info['domain']}[crlf]Upgrade: websocket[crlf][crlf]

📥 OVPN Download
https://{server_info['domain']}:81/

📝 Save Link Akun
https://{server_info['domain']}:81/ssh-{username}.txt

━━━━━━━━━━━ 𝙏𝙝𝙖𝙣𝙠 𝙔𝙤𝙪 ━━━━━━━━━━━

"""

    with open(log_file, 'a') as f:
        f.write(log_content)
    
    # Tampilkan juga di console
    print(log_content)

def create_ssh_user(username, password, days, quota, iplimit):
    """Fungsi utama untuk membuat user SSH"""
    
    # Hitung tanggal
    exp_date = datetime.now() + timedelta(days=int(days))
    expe = exp_date.strftime('%d %b, %Y')
    tnggl = datetime.now().strftime('%d %b, %Y')
    
    # Dapatkan info server
    server_info = get_server_info()
    
    # Buat user sistem
    if not create_system_user(username, password, days):
        print(f"{Colors.RED}Gagal membuat user sistem{Colors.NC}")
        sys.exit(1)
    
    # Set limit IP
    set_ip_limit(username, iplimit)
    
    # Set quota limit
    set_quota_limit(username, quota)
    
    # Update database
    update_ssh_database(username, password, quota, iplimit, expe)
    
    # Buat file akun
    create_account_file(username, password, server_info, days, expe, tnggl)
    
    # Kirim notifikasi Telegram
    send_telegram_ssh(username, password, quota, iplimit, days, tnggl, expe, server_info)
    
    # Tulis log
    write_log(username, password, quota, iplimit, days, tnggl, expe, server_info)

def main():
    """Fungsi utama"""
    # Cek permission dulu
    myip = check_permission()
    
    # Parse argumen
    if len(sys.argv) == 5:
        # Format: username day limit_data_GB limit_ip (password random)
        username = sys.argv[1]
        days = sys.argv[2]
        quota = sys.argv[3]
        iplimit = sys.argv[4]
        password = generate_random_password()
        
    elif len(sys.argv) == 6:
        # Format: username password day limit_data_GB limit_ip (password custom)
        username = sys.argv[1]
        password = sys.argv[2]
        days = sys.argv[3]
        quota = sys.argv[4]
        iplimit = sys.argv[5]
        
    else:
        print(f"{Colors.RED}Usage:{Colors.NC}")
        print(f"  python3 {sys.argv[0]} {{username}} {{day}} {{limit_data_GB}} {{limit_ip}}")
        print(f"  python3 {sys.argv[0]} {{username}} {{password}} {{day}} {{limit_data_GB}} {{limit_ip}}")
        sys.exit(1)
    
    # Cek apakah user sudah ada
    if check_user_exists(username):
        print(f"{Colors.RED}User {username} sudah ada, silakan pilih username lain.{Colors.NC}")
        sys.exit(2)
    
    # Buat user
    create_ssh_user(username, password, days, quota, iplimit)
    
    # Simulasi "Press Any Key To Back On Menu" seperti script asli
    print()
    input("Press Any Key To Back On Menu")

if __name__ == "__main__":
    main()