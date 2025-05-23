#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script untuk menghapus akun SSH/OpenVPN
Mengirim notifikasi Telegram & log otomatis (menggunakan password, bukan UUID)
Compatible dengan Python 3.6+
"""

import os
import sys
import subprocess
import requests
import json
import urllib.parse
from datetime import datetime

class Colors:
    """Kelas untuk mendefinisikan warna terminal"""
    RED = "\033[31m"
    YELLOW = "\033[33m"
    NC = '\033[0m'
    YELL = '\033[0;33m'
    BRED = '\033[1;31m'
    GREEN = '\033[0;32m'
    ORANGE = '\033[33m'
    BGWHITE = '\033[0;100;37m'

def clear_screen():
    """Membersihkan layar terminal"""
    os.system('clear')

def get_user_info(username):
    """Mendapatkan informasi user dari sistem"""
    try:
        # Mengecek apakah user ada
        result = subprocess.run(['getent', 'passwd', username], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            return None
            
        # Mendapatkan informasi expiry date
        chage_result = subprocess.run(['chage', '-l', username], 
                                    capture_output=True, text=True)
        exp_date = "never"
        if chage_result.returncode == 0:
            for line in chage_result.stdout.split('\n'):
                if "Account expires" in line:
                    exp_date = line.split(": ")[1].strip()
                    break
        
        # Mendapatkan status password
        passwd_result = subprocess.run(['passwd', '-S', username], 
                                     capture_output=True, text=True)
        status = "Unknown"
        if passwd_result.returncode == 0:
            status = passwd_result.stdout.split()[1]
            
        return {
            'username': username,
            'exp_date': exp_date,
            'status': status
        }
    except Exception as e:
        print(f"Error getting user info: {e}")
        return None

def get_user_password_hash(username):
    """Mendapatkan hash password user dari /etc/shadow"""
    try:
        with open('/etc/shadow', 'r') as f:
            for line in f:
                if line.startswith(f"{username}:"):
                    parts = line.strip().split(':')
                    if len(parts) >= 2:
                        password_hash = parts[1]
                        if password_hash:
                            return password_hash
                        break
        return "(tidak diketahui, password terenkripsi)"
    except Exception as e:
        print(f"Error reading shadow file: {e}")
        return "(tidak diketahui, password terenkripsi)"

def display_users():
    """Menampilkan daftar user SSH/OpenVPN"""
    print(f"{Colors.ORANGE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.NC}")
    print(f"{Colors.ORANGE}{Colors.BGWHITE}            MEMBER SSH OPENVPN            {Colors.NC}")
    print(f"{Colors.ORANGE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.NC}")
    print("USERNAME          EXP DATE          ")
    print(f"{Colors.ORANGE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.NC}")
    
    try:
        with open('/etc/passwd', 'r') as f:
            for line in f:
                parts = line.strip().split(':')
                if len(parts) >= 4:
                    username = parts[0]
                    uid = int(parts[2])
                    
                    if uid >= 1000 and username != 'nobody':
                        user_info = get_user_info(username)
                        if user_info:
                            exp_display = user_info['exp_date'] if user_info['exp_date'] != "never" else "never"
                            status_indicator = "(Locked)" if user_info['status'] == "L" else ""
                            print(f"{username:<17} {exp_display:<17} {status_indicator}")
    except Exception as e:
        print(f"Error reading passwd file: {e}")
    
    print(f"{Colors.ORANGE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.NC}")

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

def send_telegram_notification(username, password_hash, exp_date, system_info):
    """Mengirim notifikasi ke Telegram"""
    try:
        # Membaca token bot dan chat ID
        with open('/etc/telegram_bot/bot_token', 'r') as f:
            bot_token = f.read().strip()
        with open('/etc/telegram_bot/chat_id', 'r') as f:
            chat_id = f.read().strip()
        
        # Menyiapkan message
        message = f"""<b>━━━━━━━━━━━ DELETE SSH ACCOUNT ━━━━━━━━━━━</b>
<b>Client Name</b> : <code>{username}</code>
<b>Password</b>    : <code>{password_hash}</code>
<b>Expired On</b>  : <code>{exp_date}</code>
<b>Domain</b>      : <code>{system_info['domain']}</code>
<b>VPS IP</b>      : <code>{system_info['ip']}</code>
<b>City</b>        : <code>{system_info['city']}</code>
<b>ISP</b>         : <code>{system_info['isp']}</code>
<b>Status</b>      : <code>DELETED</code>
<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"""
        
        # Encode message untuk URL
        encoded_message = urllib.parse.quote(message)
        
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

def write_log(username, password_hash, exp_date):
    """Menulis log ke file"""
    try:
        log_dir = "/etc/user-create"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        log_file = os.path.join(log_dir, "user.log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_content = f"""━━━━━━━━━━━ DELETE SSH ACCOUNT ━━━━━━━━━━━
┣ Timestamp  : {timestamp}
┣ Username   : {username}
┣ Password   : {password_hash}
┣ Expired On : {exp_date}
┣ Status     : DELETED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_content + '\n')
        
        # Juga tampilkan di console
        print(log_content)
        return True
        
    except Exception as e:
        print(f"Error writing log: {e}")
        return False

def delete_user(username):
    """Menghapus user dari sistem"""
    try:
        result = subprocess.run(['userdel', username], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error deleting user: {e}")
        return False

def main():
    """Fungsi utama"""
    # Mengecek apakah script dijalankan sebagai root
    if os.geteuid() != 0:
        print(f"{Colors.RED}Script ini harus dijalankan sebagai root!{Colors.NC}")
        sys.exit(1)
    
    # Membersihkan layar dan menampilkan header
    clear_screen()
    
    # Menampilkan daftar user
    display_users()
    
    print(f"{Colors.ORANGE}          » DELETE SSH OPENVPN «          {Colors.NC}")
    print(f"{Colors.ORANGE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.NC}")
    print()
    
    # Input username
    username = input("Ketik Usernamenya : ").strip()
    
    if not username:
        print(f"{Colors.RED}Username tidak boleh kosong!{Colors.NC}")
        return
    
    # Mengecek apakah user ada
    user_info = get_user_info(username)
    if not user_info:
        print(f"{Colors.RED}User '{username}' tidak ditemukan!{Colors.NC}")
        return
    
    # Mendapatkan informasi sebelum menghapus
    exp_date = user_info['exp_date']
    password_hash = get_user_password_hash(username)
    system_info = get_system_info()
    
    # Konfirmasi penghapusan
    print(f"\n{Colors.YELLOW}Informasi user yang akan dihapus:{Colors.NC}")
    print(f"Username: {username}")
    print(f"Expired: {exp_date}")
    print(f"Password Hash: {password_hash}")
    
    confirm = input(f"\n{Colors.YELLOW}Apakah Anda yakin ingin menghapus user ini? (y/N): {Colors.NC}")
    if confirm.lower() not in ['y', 'yes']:
        print(f"{Colors.YELLOW}Penghapusan dibatalkan.{Colors.NC}")
        return
    
    # Menghapus user
    print(f"\n{Colors.YELLOW}Menghapus user...{Colors.NC}")
    if delete_user(username):
        print(f"{Colors.GREEN}User '{username}' berhasil dihapus!{Colors.NC}")
        
        # Mengirim notifikasi Telegram
        print(f"{Colors.YELLOW}Mengirim notifikasi Telegram...{Colors.NC}")
        if send_telegram_notification(username, password_hash, exp_date, system_info):
            print(f"{Colors.GREEN}Notifikasi Telegram berhasil dikirim!{Colors.NC}")
        else:
            print(f"{Colors.RED}Gagal mengirim notifikasi Telegram!{Colors.NC}")
        
        # Menulis log
        print(f"{Colors.YELLOW}Menulis log...{Colors.NC}")
        if write_log(username, password_hash, exp_date):
            print(f"{Colors.GREEN}Log berhasil ditulis!{Colors.NC}")
        else:
            print(f"{Colors.RED}Gagal menulis log!{Colors.NC}")
            
    else:
        print(f"{Colors.RED}Gagal menghapus user '{username}'!{Colors.NC}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Program dihentikan oleh user.{Colors.NC}")
        sys.exit(0)
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.NC}")
        sys.exit(1)