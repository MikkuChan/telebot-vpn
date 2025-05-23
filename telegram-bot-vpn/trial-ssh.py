#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import pwd
import spwd
import crypt
import random
import string
import requests
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

class Colors:
    RED = '\033[0;31m'
    NC = '\033[0m'
    CYAN = '\033[0;36m'
    YELLOW = '\033[1;93m'
    GREEN = '\033[42m'

class SSHOVPNCreator:
    def __init__(self):
        self.setup_config()
        self.check_permission()
        self.setup_server_info()
        self.setup_account_settings()

    def get_public_ip(self):
        """Mendapatkan IP publik server"""
        try:
            response = requests.get('https://ipv4.icanhazip.com', timeout=10)
            return response.text.strip()
        except:
            try:
                response = requests.get('https://ifconfig.me', timeout=10)
                return response.text.strip()
            except:
                return "Unknown"

    def check_permission(self):
        """Periksa permission script"""
        try:
            # Dapatkan IP server
            self.ipsaya = self.get_public_ip()
            
            # Dapatkan tanggal server Google
            try:
                response = requests.get('https://google.com/', 
                                      verify=False, 
                                      timeout=10, 
                                      allow_redirects=True)
                date_header = response.headers.get('date', '')
                if date_header:
                    # Parse tanggal dari header
                    from email.utils import parsedate_to_datetime
                    server_date = parsedate_to_datetime(date_header)
                    self.date_list = server_date.strftime("%Y-%m-%d")
                else:
                    self.date_list = datetime.now().strftime("%Y-%m-%d")
            except:
                self.date_list = datetime.now().strftime("%Y-%m-%d")
            
            # Periksa data IP dari repository
            try:
                data_ip_url = "https://raw.githubusercontent.com/MikkuChan/instalasi/main/register"
                response = requests.get(data_ip_url, timeout=10)
                
                if response.status_code == 200:
                    # Cari IP dalam data
                    for line in response.text.strip().split('\n'):
                        if self.ipsaya in line:
                            parts = line.split()
                            if len(parts) >= 3:
                                useexp = parts[2]  # Tanggal expired
                                
                                # Bandingkan tanggal
                                if self.date_list < useexp:
                                    print("✅ Permission check passed")
                                    return
                                else:
                                    self.show_permission_denied()
                                    return
                    
                    # IP tidak ditemukan dalam daftar
                    self.show_permission_denied()
                else:
                    print(f"{Colors.YELLOW}⚠️  Tidak dapat memeriksa permission, melanjutkan...{Colors.NC}")
                    
            except Exception as e:
                print(f"{Colors.YELLOW}⚠️  Error checking permission: {e}, melanjutkan...{Colors.NC}")
                
        except Exception as e:
            print(f"{Colors.RED}Error in permission check: {e}{Colors.NC}")

    def show_permission_denied(self):
        """Tampilkan pesan permission denied"""
        print(f"{Colors.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.NC}")
        print(f"{Colors.GREEN}          404 NOT FOUND AUTOSCRIPT          {Colors.NC}")
        print(f"{Colors.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.NC}")
        print("")
        print(f"            {Colors.RED}PERMISSION DENIED !{Colors.NC}")
        print(f"   {Colors.YELLOW}Your VPS{Colors.NC} {self.ipsaya} {Colors.YELLOW}Has been Banned{Colors.NC}")
        print(f"     {Colors.YELLOW}Buy access permissions for scripts{Colors.NC}")
        print(f"             {Colors.YELLOW}Contact Admin :{Colors.NC}")
        print(f"{Colors.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.NC}")
        sys.exit(0)

    def setup_config(self):
        """Setup konfigurasi Telegram bot"""
        try:
            with open('/etc/bot/.bot.db', 'r') as f:
                content = f.read()
            
            # Mencari CHATID dan KEY dari file config
            bot_line = None
            for line in content.split('\n'):
                if line.startswith('#bot# '):
                    bot_line = line
                    break
            
            if not bot_line:
                raise ValueError("Konfigurasi bot tidak ditemukan")
            
            parts = bot_line.split(' ')
            self.KEY = parts[1]
            self.CHATID = parts[2]
            self.TIME = 10
            self.URL = f"https://api.telegram.org/bot{self.KEY}/sendMessage"
            
        except Exception as e:
            print(f"{Colors.RED}Error membaca konfigurasi bot: {e}{Colors.NC}")
            sys.exit(1)

    def setup_server_info(self):
        """Setup informasi server"""
        try:
            # Baca domain
            with open('/etc/xray/domain', 'r') as f:
                self.domain = f.read().strip()
            
            # Dapatkan IP publik
            self.IP = self.get_public_ip()
            self.MYIP = self.IP
            
            # Dapatkan informasi lokasi
            try:
                response = requests.get('https://ipinfo.io/city', timeout=10)
                self.CITY = response.text.strip() if response.text.strip() else "-"
            except:
                self.CITY = "-"
            
            # Dapatkan informasi ISP
            try:
                response = requests.get('https://ipinfo.io/org', timeout=10)
                org_info = response.text.strip()
                if org_info:
                    # Ambil bagian setelah space pertama (skip AS number)
                    parts = org_info.split(' ', 1)
                    self.ISP = parts[1] if len(parts) > 1 else org_info
                else:
                    self.ISP = "-"
            except:
                self.ISP = "-"
                
        except Exception as e:
            print(f"{Colors.RED}Error mendapatkan informasi server: {e}{Colors.NC}")
            sys.exit(1)

    def setup_account_settings(self):
        """Setup pengaturan akun default"""
        self.Quota = 1      # GB
        self.iplimit = 10   # IP limit
        self.aktif_menit = 60  # menit

    def generate_account_info(self):
        """Generate informasi akun baru"""
        # Generate username dan password dengan 4 digit random
        random_digits_user = ''.join(random.choices(string.digits, k=4))
        random_digits_pass = ''.join(random.choices(string.digits, k=4))
        
        self.Login = f"trial{random_digits_user}"
        self.Pass = f"password{random_digits_pass}"
        
        # Generate tanggal
        self.tnggl = datetime.now().strftime("%d %b, %Y")
        self.expe = (datetime.now() + timedelta(days=1)).strftime("%d %b, %Y")

    def create_ssh_user(self):
        """Buat user SSH sistem"""
        try:
            # Tanggal expired (1 hari ke depan)
            exp_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            
            # Buat user dengan expired date
            cmd_useradd = [
                'useradd',
                '-e', exp_date,
                '-s', '/bin/false',
                '-M',
                self.Login
            ]
            
            subprocess.run(cmd_useradd, check=True, capture_output=True)
            
            # Set password untuk user
            # Menggunakan chpasswd untuk set password
            password_input = f"{self.Login}:{self.Pass}\n"
            proc = subprocess.Popen(['chpasswd'], stdin=subprocess.PIPE, 
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            proc.communicate(input=password_input.encode())
            
            if proc.returncode != 0:
                raise Exception("Failed to set password")
            
            # Dapatkan informasi expiry dari chage
            try:
                result = subprocess.run(['chage', '-l', self.Login], 
                                      capture_output=True, text=True, check=True)
                
                for line in result.stdout.split('\n'):
                    if 'Account expires' in line:
                        self.exp = line.split(': ')[1].strip()
                        break
                else:
                    self.exp = exp_date
            except:
                self.exp = exp_date
            
            print(f"✅ User SSH {self.Login} berhasil dibuat")
            
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}Error creating SSH user: {e}{Colors.NC}")
            # Cek apakah user sudah ada
            try:
                pwd.getpwnam(self.Login)
                print(f"{Colors.YELLOW}⚠️  User {self.Login} sudah ada, melanjutkan...{Colors.NC}")
                self.exp = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            except KeyError:
                raise
        except Exception as e:
            print(f"{Colors.RED}Error in SSH user creation: {e}{Colors.NC}")
            raise

    def setup_quota_and_ip_limit(self):
        """Setup batasan quota dan IP"""
        try:
            # Buat direktori yang diperlukan
            os.makedirs('/etc/ssh', exist_ok=True)
            
            # Set IP limit
            with open(f'/etc/ssh/{self.Login}_iplimit', 'w') as f:
                f.write(str(self.iplimit))
            
            # Set quota (konversi GB ke bytes)
            quota_bytes = self.Quota * 1024 * 1024 * 1024
            with open(f'/etc/ssh/{self.Login}_quota', 'w') as f:
                f.write(str(quota_bytes))
            
            print("✅ Quota dan IP limit berhasil diatur")
            
        except Exception as e:
            print(f"{Colors.RED}Error setting quota and IP limit: {e}{Colors.NC}")
            raise

    def save_to_database(self):
        """Simpan data ke database SSH"""
        try:
            db_path = '/etc/ssh/.ssh.db'
            
            # Buat file database jika belum ada
            Path(db_path).touch()
            
            # Hapus entry yang sudah ada untuk user ini
            if os.path.exists(db_path):
                with open(db_path, 'r') as f:
                    lines = f.readlines()
                
                # Filter out existing user
                filtered_lines = [line for line in lines if not re.search(rf'\b{self.Login}\b', line)]
                
                with open(db_path, 'w') as f:
                    f.writelines(filtered_lines)
            
            # Tambah entry baru
            db_entry = f"### {self.Login} {self.exp} {self.Pass} {self.Quota} {self.iplimit}\n"
            with open(db_path, 'a') as f:
                f.write(db_entry)
            
            print("✅ Data berhasil disimpan ke database SSH")
            
        except Exception as e:
            print(f"{Colors.RED}Error saving to SSH database: {e}{Colors.NC}")
            raise

    def create_config_file(self):
        """Buat file konfigurasi SSH/OVPN"""
        try:
            config_content = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Format SSH OVPN Account
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Username         : {self.Login}
Password         : {self.Pass}
Berakhir Pada    : 60 Menit
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IP               : {self.IP}
Host             : {self.domain}
Port OpenSSH     : 22
Port Dropbear    : 443, 109, 143
Port SSH UDP     : 7100,7200,7300
Port SSH WS      : 80, 8080, 8081-9999
Port SSH SSL WS  : 443
Port SSL/TLS     : 400-900
Port OVPN WS SSL : 443
Port OVPN SSL    : 443
Port OVPN TCP    : 1194
Port OVPN UDP    : 2200
BadVPN UDPGW     : 7100,7200,7300
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Payload WSS : GET wss://BUG.COM/ HTTP/1.1[crlf]Host: {self.domain}[crlf]Upgrade: websocket[crlf][crlf]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OVPN Download : https://{self.domain}:81/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Save Link Account: https://{self.domain}:81/ssh-{self.Login}.txt
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
            
            # Buat direktori jika belum ada
            os.makedirs('/var/www/html', exist_ok=True)
            
            # Tulis file konfigurasi
            with open(f'/var/www/html/ssh-{self.Login}.txt', 'w') as f:
                f.write(config_content)
            
            print("✅ File konfigurasi SSH/OVPN berhasil dibuat")
            
        except Exception as e:
            print(f"{Colors.RED}Error creating config file: {e}{Colors.NC}")
            raise

    def create_telegram_message(self):
        """Buat pesan untuk Telegram"""
        self.telegram_text = f"""<b>━━━━━ 𝙎𝙎𝙃/𝙊𝙑𝙋𝙉 𝙋𝙍𝙀𝙈𝙄𝙐𝙈 ━━━━━</b>

<b>👤 𝙐𝙨𝙚𝙧 𝘿𝙚𝙩𝙖𝙞𝙡𝙨</b>
┣ <b>Username</b>   : <code>{self.Login}</code>
┣ <b>Password</b>   : <code>{self.Pass}</code>
┣ <b>Quota</b>      : <code>{self.Quota} GB</code>
┣ <b>Status</b>     : <code>Aktif 1 hari</code>
┣ <b>Dibuat</b>     : <code>{self.tnggl}</code>
┗ <b>Expired</b>    : <code>{self.expe}</code>

<b>🌎 𝙎𝙚𝙧𝙫𝙚𝙧 𝙄𝙣𝙛𝙤</b>
┣ <b>Domain</b>     : <code>{self.domain}</code>
┣ <b>IP</b>     : <code>{self.IP}</code>
┣ <b>Location</b>   : <code>{self.CITY}</code>
┗ <b>ISP</b>        : <code>{self.ISP}</code>

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
<code>GET wss://BUG.COM/ HTTP/1.1[crlf]Host: {self.domain}[crlf]Upgrade: websocket[crlf][crlf]</code>

<b>📥 𝙊𝙑𝙋𝙉 𝘿𝙤𝙬𝙣𝙡𝙤𝙖𝙙</b>
<code>https://{self.domain}:81/</code>

<b>📝 𝙎𝙖𝙫𝙚 𝙇𝙞𝙣𝙠 𝘼𝙠𝙪𝙣</b>
https://{self.domain}:81/ssh-{self.Login}.txt

<b>━━━━━━━━━ 𝙏𝙝𝙖𝙣𝙠 𝙔𝙤𝙪 ━━━━━━━━</b>"""

    def create_terminal_message(self):
        """Buat pesan untuk terminal"""
        self.terminal_text = f"""━━━━━━━━━━━ 𝙉𝙀𝙒 𝙎𝙎𝙃 𝙋𝙍𝙀𝙈𝙄𝙐𝙈 𝘼𝘾𝘾𝙊𝙐𝙉𝙏 ━━━━━━━━━━━

👤 𝙐𝙨𝙚𝙧 𝘿𝙚𝙩𝙖𝙞𝙡𝙨
┣ Username   : {self.Login}
┣ Password   : {self.Pass}
┣ Quota      : {self.Quota} GB
┣ Limit IP   : {self.iplimit} IP
┣ Status     : Aktif 60 menit
┣ Dibuat     : {self.tnggl}
┗ Expired    : {self.expe}

🌎 𝙎𝙚𝙧𝙫𝙚𝙧 𝙄𝙣𝙛𝙤
┣ Domain     : {self.domain}
┣ VPS IP     : {self.MYIP}
┣ Location   : {self.CITY}
┗ ISP        : {self.ISP}

🔗 𝘾𝙤𝙣𝙣𝙚𝙘𝙩𝙞𝙤𝙣
┣ OpenSSH        : 22
┣ Dropbear       : 443, 109, 143
┣ SSL/TLS        : 400-900
┣ SSH WS TLS     : 443
┣ SSH WS NTLS    : 80, 8080, 8081-9999
┣ OVPN WS TLS    : 443
┣ OVPN WS NTLS   : 80, 8080, 8880
┣ PORT SSH UDP   : 7100,7200,7300
┣ Payload WSS    : GET wss://BUG.COM/ HTTP/1.1[crlf]Host: {self.domain}[crlf]Upgrade: websocket[crlf][crlf]
┗ OVPN Download  : https://{self.domain}:81/

📥 𝘾𝙤𝙣𝙛𝙞𝙜 𝙁𝙞𝙡𝙚 (Save Link Account):
https://{self.domain}:81/ssh-{self.Login}.txt

✨ 𝙏𝙤𝙤𝙡𝙨 & 𝙍𝙚𝙨𝙤𝙪𝙧𝙘𝙚𝙨
┣ https://vpntech.my.id/converteryaml
┗ https://vpntech.my.id/auto-configuration

❓ 𝘽𝙪𝙩𝙪𝙝 𝘽𝙖𝙣𝙩𝙪𝙖𝙣?
https://t.me/085727035336 (Klik untuk chat Admin)

━━━━━━━━━━━ 𝙏𝙝𝙖𝙣𝙠 𝙔𝙤𝙪 ━━━━━━━━━━━"""

    def send_telegram_message(self):
        """Kirim pesan ke Telegram"""
        try:
            payload = {
                'chat_id': self.CHATID,
                'disable_web_page_preview': 1,
                'text': self.telegram_text,
                'parse_mode': 'html'
            }
            
            response = requests.post(self.URL, data=payload, timeout=self.TIME)
            
            if response.status_code == 200:
                print("✅ Pesan berhasil dikirim ke Telegram")
            else:
                print(f"{Colors.RED}❌ Gagal mengirim pesan ke Telegram: {response.status_code}{Colors.NC}")
                
        except Exception as e:
            print(f"{Colors.RED}Error sending Telegram message: {e}{Colors.NC}")

    def display_terminal_output(self):
        """Tampilkan output di terminal"""
        # Clear screen
        os.system('clear')
        print(f"{Colors.CYAN}{self.terminal_text}{Colors.NC}")

    def create_account(self):
        """Fungsi utama untuk membuat akun SSH/OVPN"""
        try:
            print("🚀 Memulai pembuatan akun SSH/OVPN Premium...")
            
            # Generate informasi akun
            self.generate_account_info()
            print(f"✅ Username: {self.Login}")
            
            # Buat user SSH
            self.create_ssh_user()
            
            # Setup quota dan IP limit
            self.setup_quota_and_ip_limit()
            
            # Simpan ke database
            self.save_to_database()
            
            # Buat file konfigurasi
            self.create_config_file()
            
            # Buat pesan
            self.create_telegram_message()
            self.create_terminal_message()
            
            # Tampilkan di terminal
            self.display_terminal_output()
            
            # Kirim ke Telegram
            self.send_telegram_message()
            
            print(f"\n{Colors.CYAN}✅ Akun SSH/OVPN Premium berhasil dibuat!{Colors.NC}")
            
        except Exception as e:
            print(f"{Colors.RED}❌ Error dalam pembuatan akun: {e}{Colors.NC}")
            sys.exit(1)

def main():
    """Fungsi utama"""
    try:
        # Periksa apakah script dijalankan sebagai root
        if os.geteuid() != 0:
            print(f"{Colors.RED}❌ Script ini harus dijalankan sebagai root!{Colors.NC}")
            sys.exit(1)
        
        # Buat instance SSHOVPNCreator dan jalankan
        creator = SSHOVPNCreator()
        creator.create_account()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}❌ Proses dibatalkan oleh user{Colors.NC}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.NC}")
        sys.exit(1)

if __name__ == "__main__":
    main()