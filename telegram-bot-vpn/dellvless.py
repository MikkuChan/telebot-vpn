#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script untuk menghapus akun VLESS
Mengirim notifikasi Telegram & log otomatis
Compatible dengan Python 3.6+
"""

import os
import sys
import json
import re
import requests
import subprocess
import urllib.parse
import shutil
from datetime import datetime

class Colors:
    """Kelas untuk mendefinisikan warna terminal"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    NC = '\033[0m'
    BGWHITE = '\033[0;100;37m'

def clear_screen():
    """Membersihkan layar terminal"""
    os.system('clear')

def count_vless_clients():
    """Menghitung jumlah client VLESS dari config.json"""
    try:
        with open('/etc/xray/config.json', 'r') as f:
            content = f.read()
        
        # Mencari pattern #& untuk menghitung client VLESS
        pattern = r'^#& '
        matches = re.findall(pattern, content, re.MULTILINE)
        return len(matches)
    except FileNotFoundError:
        print(f"{Colors.RED}File config.json tidak ditemukan!{Colors.NC}")
        return 0
    except Exception as e:
        print(f"{Colors.RED}Error reading config.json: {e}{Colors.NC}")
        return 0

def get_user_info(username):
    """Mendapatkan informasi user dari config.json"""
    try:
        with open('/etc/xray/config.json', 'r') as f:
            content = f.read()
        
        # Mencari pattern untuk user VLESS
        pattern = rf'^#& {re.escape(username)} (.+)$'
        matches = re.findall(pattern, content, re.MULTILINE)
        
        if not matches:
            return None
        
        exp_date = matches[0].strip()
        
        # Mencari UUID/id
        lines = content.split('\n')
        uuid = None
        
        for i, line in enumerate(lines):
            if f"#& {username} {exp_date}" in line:
                # Mencari id dalam beberapa baris setelahnya
                for j in range(i+1, min(i+10, len(lines))):
                    if '"id"' in lines[j]:
                        # Extract id dari line
                        id_match = re.search(r'"id"\s*:\s*"([^"]+)"', lines[j])
                        if id_match:
                            uuid = id_match.group(1)
                            break
                break
        
        return {
            'username': username,
            'exp_date': exp_date,
            'uuid': uuid if uuid else "Tidak ditemukan"
        }
    except FileNotFoundError:
        print(f"{Colors.RED}File config.json tidak ditemukan!{Colors.NC}")
        return None
    except Exception as e:
        print(f"{Colors.RED}Error reading config.json: {e}{Colors.NC}")
        return None

def remove_user_from_config(username, exp_date):
    """Menghapus user dari config.json"""
    try:
        with open('/etc/xray/config.json', 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        new_lines = []
        skip_block = False
        
        for line in lines:
            if f"#& {username} {exp_date}" in line:
                skip_block = True
                continue
            elif skip_block and line.strip() == "},":
                skip_block = False
                continue
            elif not skip_block:
                new_lines.append(line)
        
        # Menulis kembali config.json
        with open('/etc/xray/config.json', 'w') as f:
            f.write('\n'.join(new_lines))
        
        return True
    except Exception as e:
        print(f"{Colors.RED}Error removing user from config.json: {e}{Colors.NC}")
        return False

def remove_user_from_db(username, exp_date):
    """Menghapus user dari database vless"""
    try:
        db_file = '/etc/vless/.vless.db'
        if not os.path.exists(db_file):
            return True
        
        with open(db_file, 'r') as f:
            lines = f.readlines()
        
        # Filter out the user line
        new_lines = []
        for line in lines:
            if not line.strip().startswith(f"#& {username} {exp_date}"):
                new_lines.append(line)
        
        # Menulis kembali database
        with open(db_file, 'w') as f:
            f.writelines(new_lines)
        
        return True
    except Exception as e:
        print(f"{Colors.RED}Error removing user from database: {e}{Colors.NC}")
        return False

def remove_user_files(username):
    """Menghapus file-file user"""
    try:
        # Menghapus folder user
        user_folder = f'/etc/vless/{username}'
        if os.path.exists(user_folder):
            shutil.rmtree(user_folder)
        
        # Menghapus file limit
        limit_file = f'/etc/kyt/limit/vless/ip/{username}'
        if os.path.exists(limit_file):
            os.remove(limit_file)
        
        return True
    except Exception as e:
        print(f"{Colors.RED}Error removing user files: {e}{Colors.NC}")
        return False

def restart_xray():
    """Restart service xray"""
    try:
        result = subprocess.run(['systemctl', 'restart', 'xray'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"{Colors.RED}Error restarting xray: {e}{Colors.NC}")
        return False

def get_system_info():
    """Mendapatkan informasi sistem"""
    try:
        # Mendapatkan IP eksternal
        ip_response = requests.get('https://ifconfig.me', timeout=10)
        myip = ip_response.text.strip() if ip_response.status_code == 200 else "Tidak diketahui"
        
        # Mendapatkan informasi lokasi
        try:
            location_response = requests.get('https://ipinfo.io/json', timeout=10)
            if location_response.status_code == 200:
                location_data = location_response.json()
                city = location_data.get('city', 'Tidak diketahui')
                isp = location_data.get('org', 'Tidak diketahui')
            else:
                city = "Tidak diketahui"
                isp = "Tidak diketahui"
        except:
            city = "Tidak diketahui"
            isp = "Tidak diketahui"
        
        # Mendapatkan domain
        try:
            with open('/etc/xray/domain', 'r') as f:
                domain = f.read().strip()
        except:
            domain = "Tidak diketahui"
            
        return {
            'ip': myip,
            'city': city,
            'isp': isp,
            'domain': domain
        }
    except Exception as e:
        print(f"Error getting system info: {e}")
        return {
            'ip': "Tidak diketahui",
            'city': "Tidak diketahui", 
            'isp': "Tidak diketahui",
            'domain': "Tidak diketahui"
        }

def send_telegram_notification(username, uuid, exp_date, system_info):
    """Mengirim notifikasi ke Telegram"""
    try:
        # Membaca token bot dan chat ID
        with open('/etc/telegram_bot/bot_token', 'r') as f:
            bot_token = f.read().strip()
        with open('/etc/telegram_bot/chat_id', 'r') as f:
            chat_id = f.read().strip()
        
        # Menyiapkan message
        message = f"""<b>━━━━━━━━━━━ DELETE VLESS ACCOUNT ━━━━━━━━━━━</b>
<b>Client Name</b> : <code>{username}</code>
<b>UUID</b>        : <code>{uuid}</code>
<b>Expired On</b>  : <code>{exp_date}</code>
<b>Domain</b>      : <code>{system_info['domain']}</code>
<b>VPS IP</b>      : <code>{system_info['ip']}</code>
<b>City</b>        : <code>{system_info['city']}</code>
<b>ISP</b>         : <code>{system_info['isp']}</code>
<b>Status</b>      : <code>DELETED</code>
<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"""
        
        # Mengirim message
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error sending Telegram notification: {e}")
        return False

def write_log(username, uuid, exp_date):
    """Menulis log ke file"""
    try:
        log_dir = "/etc/user-create"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        log_file = os.path.join(log_dir, "user.log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_content = f"""━━━━━━━━━━━ DELETE VLESS ACCOUNT ━━━━━━━━━━━
┣ Timestamp  : {timestamp}
┣ Username   : {username}
┣ UUID       : {uuid}
┣ Expired On : {exp_date}
┣ Status     : DELETED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_content + '\n\n')
        
        print(log_content)
        return True
        
    except Exception as e:
        print(f"Error writing log: {e}")
        return False

def main():
    """Fungsi utama"""
    # Mengecek apakah script dijalankan sebagai root
    if os.geteuid() != 0:
        print(f"{Colors.RED}Script ini harus dijalankan sebagai root!{Colors.NC}")
        sys.exit(1)
    
    # Mengecek argument
    if len(sys.argv) != 2:
        print(f"{Colors.YELLOW}Usage: {sys.argv[0]} {{username}}{Colors.NC}")
        sys.exit(1)
    
    username = sys.argv[1].strip()
    
    # Mengecek jumlah client
    client_count = count_vless_clients()
    if client_count == 0:
        clear_screen()
        print(f"{Colors.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.NC}")
        print(f"{Colors.BGWHITE}        Delete Vless Account       {Colors.NC}")
        print(f"{Colors.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.NC}")
        print("")
        print("Anda Tidak Memiliki Member Vless!")
        print("")
        print(f"{Colors.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.NC}")
        sys.exit(1)
    
    # Mendapatkan informasi user
    user_info = get_user_info(username)
    if not user_info:
        print(f"{Colors.RED}User {username} tidak ditemukan!{Colors.NC}")
        sys.exit(1)
    
    exp_date = user_info['exp_date']
    uuid = user_info['uuid']
    
    # Mendapatkan informasi sistem
    system_info = get_system_info()
    
    # Menghapus user dari berbagai tempat
    print(f"{Colors.YELLOW}Menghapus user {username}...{Colors.NC}")
    
    success = True
    
    # Hapus dari config.json
    if not remove_user_from_config(username, exp_date):
        success = False
    
    # Hapus dari database
    if not remove_user_from_db(username, exp_date):
        success = False
    
    # Hapus file-file user
    if not remove_user_files(username):
        success = False
    
    # Restart xray
    if not restart_xray():
        print(f"{Colors.YELLOW}Warning: Gagal restart xray service{Colors.NC}")
    
    if success:
        # Kirim notifikasi Telegram
        if send_telegram_notification(username, uuid, exp_date, system_info):
            print(f"{Colors.GREEN}Notifikasi Telegram berhasil dikirim!{Colors.NC}")
        else:
            print(f"{Colors.YELLOW}Warning: Gagal mengirim notifikasi Telegram{Colors.NC}")
        
        # Tampilkan hasil
        clear_screen()
        print(f"{Colors.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.NC}")
        print("» Akun Vless Berhasil Dihapus!")
        print(f"{Colors.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.NC}")
        print(f"Client Name : {username}")
        print(f"UUID        : {uuid}")
        print(f"Expired On  : {exp_date}")
        print(f"{Colors.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.NC}")
        print("")
        
        # Tulis log
        write_log(username, uuid, exp_date)
        print("")
        
    else:
        print(f"{Colors.RED}Terjadi error saat menghapus user!{Colors.NC}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Program dihentikan oleh user.{Colors.NC}")
        sys.exit(0)
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.NC}")
        sys.exit(1)