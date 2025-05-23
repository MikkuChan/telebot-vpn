#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import uuid
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

class TrojanCreator:
    def __init__(self):
        self.setup_config()
        self.setup_server_info()
        self.setup_account_settings()

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
            try:
                response = requests.get('https://ifconfig.me', timeout=10)
                self.MYIP = response.text.strip()
            except:
                self.MYIP = "Unknown"
            
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
        self.masaaktif = 1  # hari
        self.Quota = 1      # GB
        self.iplimit = 10   # IP limit
        self.aktif_menit = 60  # menit

    def generate_account_info(self):
        """Generate informasi akun baru"""
        # Generate username dengan 4 digit random
        random_digits = ''.join(random.choices(string.digits, k=4))
        self.user = f"trial{random_digits}"
        
        # Generate UUID
        self.uuid = str(uuid.uuid4())
        
        # Generate tanggal expired
        exp_date = datetime.now() + timedelta(days=self.masaaktif)
        self.exp = exp_date.strftime("%Y-%m-%d")
        self.expe = exp_date.strftime("%d %b, %Y")
        self.tnggl = datetime.now().strftime("%d %b, %Y")

    def update_xray_config(self):
        """Update konfigurasi Xray"""
        try:
            config_path = '/etc/xray/config.json'
            
            # Backup konfigurasi
            subprocess.run(['cp', config_path, f'{config_path}.backup'], check=True)
            
            # Baca konfigurasi saat ini
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Template untuk trojan websocket
            trojan_ws_entry = f'#! {self.user} {self.exp}\n' + \
                            f'}},{{"password": "{self.uuid}","email": "{self.user}"}}'
            
            # Template untuk trojan gRPC
            trojan_grpc_entry = f'#! {self.user} {self.exp}\n' + \
                              f'}},{{"password": "{self.uuid}","email": "{self.user}"}}'
            
            # Update konfigurasi untuk trojan websocket
            content = re.sub(
                r'(#trojanws\$)',
                f'\\1\n{trojan_ws_entry}',
                content
            )
            
            # Update konfigurasi untuk trojan gRPC
            content = re.sub(
                r'(#trojangrpc\$)',
                f'\\1\n{trojan_grpc_entry}',
                content
            )
            
            # Tulis konfigurasi yang sudah diupdate
            with open(config_path, 'w') as f:
                f.write(content)
            
            print("✅ Konfigurasi Xray berhasil diupdate")
            
        except Exception as e:
            print(f"{Colors.RED}Error updating Xray config: {e}{Colors.NC}")
            # Restore backup jika ada error
            try:
                subprocess.run(['cp', f'{config_path}.backup', config_path], check=True)
            except:
                pass
            raise

    def restart_services(self):
        """Restart layanan yang diperlukan"""
        try:
            # Restart Xray
            subprocess.run(['systemctl', 'restart', 'xray'], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            
            # Restart Nginx
            subprocess.run(['systemctl', 'restart', 'nginx'], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            
            print("✅ Layanan berhasil direstart")
            
        except Exception as e:
            print(f"{Colors.RED}Error restarting services: {e}{Colors.NC}")
            raise

    def generate_trojan_links(self):
        """Generate link Trojan"""
        # Link Trojan WebSocket
        self.trojanlink = (
            f"trojan://{self.uuid}@{self.domain}:443?"
            f"path=%2Ftrojan-ws&security=tls&host={self.domain}&"
            f"type=ws&sni={self.domain}#{self.user}"
        )
        
        # Link Trojan gRPC
        self.trojanlink1 = (
            f"trojan://{self.uuid}@{self.domain}:443?"
            f"mode=gun&security=tls&type=grpc&serviceName=trojan-grpc&"
            f"sni={self.domain}#{self.user}"
        )

    def create_clash_config(self):
        """Buat file konfigurasi Clash/OpenClash"""
        try:
            clash_config = f"""━━━━━━━━━━━━━━━━━━━━━
   Format For Clash
━━━━━━━━━━━━━━━━━━━━━
# Format Trojan GO/WS

- name: Trojan-{self.user}-GO/WS
  server: {self.domain}
  port: 443
  type: trojan
  password: {self.uuid}
  network: ws
  sni: {self.domain}
  skip-cert-verify: true
  udp: true
  ws-opts:
    path: /trojan-ws
    headers:
        Host: {self.domain}

# Format Trojan gRPC

- name: Trojan-{self.user}-gRPC
  type: trojan
  server: {self.domain}
  port: 443
  password: {self.uuid}
  udp: true
  sni: {self.domain}
  skip-cert-verify: true
  network: grpc
  grpc-opts:
    grpc-service-name: trojan-grpc

━━━━━━━━━━━━━━━━━━━━━
Link Akun Trojan 
━━━━━━━━━━━━━━━━━━━━━
Link WS          : 
{self.trojanlink}
━━━━━━━━━━━━━━━━━━━━━
Link GRPC        : 
{self.trojanlink1}
━━━━━━━━━━━━━━━━━━━━━

"""
            
            # Buat direktori jika belum ada
            os.makedirs('/var/www/html', exist_ok=True)
            
            # Tulis file konfigurasi
            with open(f'/var/www/html/trojan-{self.user}.txt', 'w') as f:
                f.write(clash_config)
            
            print("✅ File konfigurasi Clash berhasil dibuat")
            
        except Exception as e:
            print(f"{Colors.RED}Error creating Clash config: {e}{Colors.NC}")
            raise

    def restart_cron(self):
        """Restart layanan cron"""
        try:
            subprocess.run(['service', 'cron', 'restart'], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except Exception as e:
            print(f"{Colors.RED}Error restarting cron: {e}{Colors.NC}")

    def setup_quota_and_ip_limit(self):
        """Setup batasan quota dan IP"""
        try:
            # Buat direktori yang diperlukan
            os.makedirs('/etc/trojan', exist_ok=True)
            os.makedirs('/etc/kyt/limit/trojan/ip', exist_ok=True)
            
            # Set IP limit
            with open(f'/etc/kyt/limit/trojan/ip/{self.user}', 'w') as f:
                f.write(str(self.iplimit))
            
            # Set quota (konversi GB ke bytes)
            quota_bytes = self.Quota * 1024 * 1024 * 1024
            with open(f'/etc/trojan/{self.user}', 'w') as f:
                f.write(str(quota_bytes))
            
            print("✅ Quota dan IP limit berhasil diatur")
            
        except Exception as e:
            print(f"{Colors.RED}Error setting quota and IP limit: {e}{Colors.NC}")
            raise

    def save_to_database(self):
        """Simpan data ke database"""
        try:
            db_path = '/etc/trojan/.trojan.db'
            
            # Buat direktori jika belum ada
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            # Hapus entry yang sudah ada untuk user ini
            if os.path.exists(db_path):
                with open(db_path, 'r') as f:
                    lines = f.readlines()
                
                # Filter out existing user
                filtered_lines = [line for line in lines if not re.search(rf'\b{self.user}\b', line)]
                
                with open(db_path, 'w') as f:
                    f.writelines(filtered_lines)
            
            # Tambah entry baru
            db_entry = f"### {self.user} {self.exp} {self.uuid} {self.Quota} {self.iplimit}\n"
            with open(db_path, 'a') as f:
                f.write(db_entry)
            
            print("✅ Data berhasil disimpan ke database")
            
        except Exception as e:
            print(f"{Colors.RED}Error saving to database: {e}{Colors.NC}")
            raise

    def create_telegram_message(self):
        """Buat pesan untuk Telegram"""
        self.telegram_text = f"""<b>━━━━━━ 𝙏𝙍𝙊𝙅𝘼𝙉 𝙋𝙍𝙀𝙈𝙄𝙐𝙈 ━━━━━━</b>

<b>👤 𝙐𝙨𝙚𝙧 𝘿𝙚𝙩𝙖𝙞𝙡𝙨</b>
┣ <b>Username</b>   : <code>{self.user}</code>
┣ <b>UUID/PASSWORD</b>       : <code>{self.uuid}</code>
┣ <b>Quota</b>      : <code>{self.Quota} GB</code>
┣ <b>Status</b>     : <code>Aktif {self.masaaktif} hari</code>
┣ <b>Dibuat</b>     : <code>{self.tnggl}</code>
┗ <b>Expired</b>    : <code>{self.expe}</code>

<b>🌎 𝙎𝙚𝙧𝙫𝙚𝙧 𝙄𝙣𝙛𝙤</b>
┣ <b>Domain</b>     : <code>{self.domain}</code>
┣ <b>IP</b>         : <code>{self.MYIP}</code>
┣ <b>Location</b>   : <code>{self.CITY}</code>
┗ <b>ISP</b>        : <code>{self.ISP}</code>

<b>🔗 𝘾𝙤𝙣𝙣𝙚𝙘𝙩𝙞𝙤𝙣</b>
┣ <b>TLS Port</b>        : <code>400-900</code>
┣ <b>Network</b>         : <code>ws, grpc</code>
┣ <b>Path</b>            : <code>/trojan-ws</code>
┗ <b>gRPC Service</b>    : <code>trojan-grpc</code>

<b>━━━━━ 𝙏𝙍𝙊𝙅𝘼𝙉 𝙋𝙧𝙚𝙢𝙞𝙪𝙢 𝙇𝙞𝙣𝙠𝙨 ━━━━━</b>
<b>📍 𝙒𝙎 𝙏𝙇𝙎</b>
<pre>{self.trojanlink}</pre>
<b>📍 𝙜𝙍𝙋𝘾</b>
<pre>{self.trojanlink1}</pre>

<b>📥 𝘾𝙤𝙣𝙛𝙞𝙜 𝙁𝙞𝙡𝙚 (Clash/OpenClash):</b>
https://{self.domain}:81/trojan-{self.user}.txt

<b>✨ 𝙏𝙤𝙤𝙡𝙨 & 𝙍𝙚𝙨𝙤𝙪𝙧𝙘𝙚𝙨</b>
┣ <a href='https://vpntech.my.id/converteryaml'>YAML Converter</a>
┗ <a href='https://vpntech.my.id/auto-configuration'>Auto Configuration</a>

<b>❓ 𝘽𝙪𝙩𝙪𝙝 𝘽𝙖𝙣𝙩𝙪𝙖𝙣?</b>
<a href='https://t.me/085727035336'>Klik di sini untuk chat Admin</a>

<b>━━━━━━━━━ 𝙏𝙝𝙖𝙣𝙠 𝙔𝙤𝙪 ━━━━━━━━</b>"""

    def create_terminal_message(self):
        """Buat pesan untuk terminal"""
        self.terminal_text = f"""━━━━━━━━━━━ 𝙉𝙀𝙒 𝙏𝙍𝙊𝙅𝘼𝙉 𝙋𝙍𝙀𝙈𝙄𝙐𝙈 𝘼𝘾𝘾𝙊𝙐𝙉𝙏 ━━━━━━━━━━━

👤 𝙐𝙨𝙚𝙧 𝘿𝙚𝙩𝙖𝙞𝙡𝙨
┣ Username   : {self.user}
┣ Password   : {self.uuid}
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
┣ TLS Port        : 400-900
┣ Network         : ws, grpc
┣ Path            : /trojan-ws
┣ gRPC Service    : trojan-grpc
┣ Security        : tls
┗ SNI             : {self.domain}

🚀 𝙏𝙍𝙊𝙅𝘼𝙉 𝙋𝙧𝙚𝙢𝙞𝙪𝙢 𝙇𝙞𝙣𝙠𝙨
• WS TLS
{self.trojanlink}
• gRPC
{self.trojanlink1}

📥 𝘾𝙤𝙣𝙛𝙞𝙜 𝙁𝙞𝙡𝙚 (Clash/OpenClash):
https://{self.domain}:81/trojan-{self.user}.txt

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
        """Fungsi utama untuk membuat akun Trojan"""
        try:
            print("🚀 Memulai pembuatan akun Trojan Premium...")
            
            # Generate informasi akun
            self.generate_account_info()
            print(f"✅ Username: {self.user}")
            
            # Update konfigurasi Xray
            self.update_xray_config()
            
            # Restart layanan
            self.restart_services()
            
            # Generate link Trojan
            self.generate_trojan_links()
            print("✅ Link Trojan berhasil dibuat")
            
            # Buat file konfigurasi Clash
            self.create_clash_config()
            
            # Restart cron
            self.restart_cron()
            
            # Setup quota dan IP limit
            self.setup_quota_and_ip_limit()
            
            # Simpan ke database
            self.save_to_database()
            
            # Buat pesan
            self.create_telegram_message()
            self.create_terminal_message()
            
            # Tampilkan di terminal
            self.display_terminal_output()
            
            # Kirim ke Telegram
            self.send_telegram_message()
            
            print(f"\n{Colors.CYAN}✅ Akun Trojan Premium berhasil dibuat!{Colors.NC}")
            
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
        
        # Buat instance TrojanCreator dan jalankan
        creator = TrojanCreator()
        creator.create_account()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}❌ Proses dibatalkan oleh user{Colors.NC}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.NC}")
        sys.exit(1)

if __name__ == "__main__":
    main()