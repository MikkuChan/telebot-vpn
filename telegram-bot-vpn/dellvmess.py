#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Python untuk menghapus akun VMESS
Konversi dari script Bash ke Python
Kompatibel dengan Python 3.6+
"""

import sys
import re
import os
import subprocess
import json
import urllib.parse
import urllib.request
from datetime import datetime

# Warna untuk output terminal
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    NC = '\033[0m'  # No Color
    BGWHITE = '\033[0;100;37m'

def clear_screen():
    """Membersihkan layar terminal"""
    os.system('clear')

def print_colored(text, color=Colors.NC):
    """Print text dengan warna"""
    print(f"{color}{text}{Colors.NC}")

def read_file(file_path):
    """Membaca file dan mengembalikan isi sebagai string"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except FileNotFoundError:
        return None
    except Exception as e:
        print_colored(f"Error membaca file {file_path}: {e}", Colors.RED)
        return None

def write_file(file_path, content):
    """Menulis content ke file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        return True
    except Exception as e:
        print_colored(f"Error menulis file {file_path}: {e}", Colors.RED)
        return False

def count_clients():
    """Menghitung jumlah client dari config.json"""
    config_content = read_file("/etc/xray/config.json")
    if not config_content:
        return 0
    
    # Hitung pattern "### " di awal baris
    pattern = r'^### '
    matches = re.findall(pattern, config_content, re.MULTILINE)
    return len(matches)

def get_user_info(username):
    """Mendapatkan informasi user (exp dan uuid)"""
    config_content = read_file("/etc/xray/config.json")
    if not config_content:
        return None, None
    
    # Cari expiry date
    exp_pattern = rf'^### {re.escape(username)} (.+)$'
    exp_match = re.search(exp_pattern, config_content, re.MULTILINE)
    exp = exp_match.group(1) if exp_match else None
    
    if not exp:
        return None, None
    
    # Cari UUID
    lines = config_content.split('\n')
    user_line_found = False
    uuid = None
    
    for i, line in enumerate(lines):
        if f"### {username} {exp}" in line:
            user_line_found = True
            continue
        
        if user_line_found and '"id"' in line:
            # Extract UUID dari baris seperti: "id": "uuid-string"
            id_match = re.search(r'"id"\s*:\s*"([^"]+)"', line)
            if id_match:
                uuid = id_match.group(1)
                break
    
    return exp, uuid

def remove_user_from_config(username, exp):
    """Menghapus user dari config.json"""
    config_content = read_file("/etc/xray/config.json")
    if not config_content:
        return False
    
    lines = config_content.split('\n')
    new_lines = []
    skip_lines = False
    
    for line in lines:
        if f"### {username} {exp}" in line:
            skip_lines = True
            continue
        
        if skip_lines and line.strip() == "},":
            skip_lines = False
            continue
        
        if not skip_lines:
            new_lines.append(line)
    
    new_content = '\n'.join(new_lines)
    return write_file("/etc/xray/config.json", new_content)

def remove_user_from_db(username, exp):
    """Menghapus user dari database vmess"""
    db_content = read_file("/etc/vmess/.vmess.db")
    if not db_content:
        return True
    
    lines = db_content.split('\n')
    new_lines = [line for line in lines if f"### {username} {exp}" not in line]
    new_content = '\n'.join(new_lines)
    return write_file("/etc/vmess/.vmess.db", new_content)

def remove_user_files(username):
    """Menghapus file-file terkait user"""
    try:
        # Hapus folder user
        if os.path.exists(f"/etc/vmess/{username}"):
            subprocess.run(f"rm -rf /etc/vmess/{username}", shell=True, check=True)
        
        # Hapus file limit
        if os.path.exists(f"/etc/kyt/limit/vmess/ip/{username}"):
            subprocess.run(f"rm -rf /etc/kyt/limit/vmess/ip/{username}", shell=True, check=True)
        
        return True
    except Exception as e:
        print_colored(f"Error menghapus file user: {e}", Colors.RED)
        return False

def restart_xray():
    """Restart service xray"""
    try:
        subprocess.run("systemctl restart xray", shell=True, check=True,
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        print_colored(f"Error restart xray: {e}", Colors.RED)
        return False

def get_server_info():
    """Mendapatkan informasi server"""
    try:
        # Ambil IP
        response = urllib.request.urlopen("https://ifconfig.me", timeout=10)
        myip = response.read().decode().strip()
    except:
        myip = "Tidak diketahui"
    
    try:
        # Ambil City
        response = urllib.request.urlopen("https://ipinfo.io/city", timeout=10)
        city = response.read().decode().strip()
    except:
        city = "Tidak diketahui"
    
    try:
        # Ambil ISP
        response = urllib.request.urlopen("https://ipinfo.io/org", timeout=10)
        isp = response.read().decode().strip()
    except:
        isp = "Tidak diketahui"
    
    # Ambil domain
    domain = read_file("/etc/xray/domain") or "Tidak diketahui"
    
    return myip, city, isp, domain

def send_telegram_notification(username, uuid, exp, domain, myip, city, isp):
    """Mengirim notifikasi ke Telegram"""
    try:
        bot_token = read_file("/etc/telegram_bot/bot_token")
        chat_id = read_file("/etc/telegram_bot/chat_id")
        
        if not bot_token or not chat_id:
            print_colored("Bot token atau chat ID tidak ditemukan", Colors.YELLOW)
            return False
        
        text = f"""
<b>━━━━━━━━━━━ DELETE VMESS ACCOUNT ━━━━━━━━━━━</b>
<b>Client Name</b> : <code>{username}</code>
<b>UUID</b>        : <code>{uuid}</code>
<b>Expired On</b>  : <code>{exp}</code>
<b>Domain</b>      : <code>{domain}</code>
<b>VPS IP</b>      : <code>{myip}</code>
<b>City</b>        : <code>{city}</code>
<b>ISP</b>         : <code>{isp}</code>
<b>Status</b>      : <code>DELETED</code>
<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>
"""
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        data = {
            'chat_id': chat_id,
            'disable_web_page_preview': '1',
            'text': text.strip(),
            'parse_mode': 'html'
        }
        
        encoded_data = urllib.parse.urlencode(data).encode('utf-8')
        request = urllib.request.Request(url, data=encoded_data, method='POST')
        
        response = urllib.request.urlopen(request, timeout=10)
        return response.getcode() == 200
        
    except Exception as e:
        print_colored(f"Error mengirim notifikasi Telegram: {e}", Colors.YELLOW)
        return False

def log_deletion(username, uuid, exp):
    """Mencatat log penghapusan"""
    try:
        log_file = "/etc/user-create/user.log"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_content = f"""
━━━━━━━━━━━ DELETE VMESS ACCOUNT ━━━━━━━━━━━
┣ Timestamp  : {timestamp}
┣ Username   : {username}
┣ UUID       : {uuid}
┣ Expired On : {exp}
┣ Status     : DELETED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        
        # Buat direktori jika belum ada
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_content)
        
        return True
    except Exception as e:
        print_colored(f"Error menulis log: {e}", Colors.YELLOW)
        return False

def print_header():
    """Print header"""
    print_colored("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", Colors.YELLOW)
    print_colored(f"{Colors.BGWHITE}        Delete Vmess Account       {Colors.NC}")
    print_colored("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", Colors.YELLOW)

def print_success_message(username, uuid, exp):
    """Print pesan sukses"""
    print_colored("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", Colors.YELLOW)
    print_colored("» Akun Vmess Berhasil Dihapus!")
    print_colored("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", Colors.YELLOW)
    print(f"Client Name : {username}")
    print(f"UUID        : {uuid}")
    print(f"Expired On  : {exp}")
    print_colored("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", Colors.YELLOW)
    print()

def main():
    """Fungsi utama"""
    # Cek argumen
    if len(sys.argv) != 2:
        print_colored(f"Usage: {sys.argv[0]} {{username}}", Colors.YELLOW)
        sys.exit(1)
    
    username = sys.argv[1]
    
    # Cek apakah ada client
    client_count = count_clients()
    if client_count == 0:
        clear_screen()
        print_header()
        print()
        print("Anda Tidak Memiliki Member Vmess!")
        print()
        print_colored("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", Colors.YELLOW)
        sys.exit(1)
    
    # Ambil informasi user
    exp, uuid = get_user_info(username)
    if not exp or not uuid:
        print_colored(f"User {username} tidak ditemukan!", Colors.RED)
        sys.exit(1)
    
    # Hapus user dari berbagai tempat
    success = True
    
    # Hapus dari config
    if not remove_user_from_config(username, exp):
        print_colored("Error menghapus dari config", Colors.RED)
        success = False
    
    # Hapus dari database
    if not remove_user_from_db(username, exp):
        print_colored("Error menghapus dari database", Colors.RED)
        success = False
    
    # Hapus file user
    if not remove_user_files(username):
        print_colored("Error menghapus file user", Colors.RED)
        success = False
    
    # Restart xray
    if not restart_xray():
        print_colored("Error restart xray", Colors.RED)
        success = False
    
    if not success:
        print_colored("Terjadi error saat menghapus user", Colors.RED)
        sys.exit(1)
    
    # Ambil informasi server
    myip, city, isp, domain = get_server_info()
    
    # Kirim notifikasi Telegram
    send_telegram_notification(username, uuid, exp, domain, myip, city, isp)
    
    # Tulis log
    log_deletion(username, uuid, exp)
    
    # Tampilkan hasil
    clear_screen()
    print_success_message(username, uuid, exp)

if __name__ == "__main__":
    main()