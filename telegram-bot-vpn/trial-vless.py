#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import random
import string
import requests
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote

class Colors:
    """Kelas untuk warna terminal"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

class VLessTrialCreator:
    def __init__(self):
        """Inisialisasi konfigurasi"""
        self.setup_config()
        self.setup_server_info()
        self.setup_user_config()
        
    def setup_config(self):
        """Setup konfigurasi Telegram bot"""
        try:
            # Baca konfigurasi bot dari file
            with open('/etc/bot/.bot.db', 'r') as f:
                for line in f:
                    if line.startswith('#bot# '):
                        parts = line.strip().split(' ')
                        if len(parts) >= 3:
                            self.bot_key = parts[1]
                            self.chat_id = parts[2]
                            break
            
            self.telegram_timeout = 10
            self.telegram_url = f"https://api.telegram.org/bot{self.bot_key}/sendMessage"
            
        except FileNotFoundError:
            print(f"{Colors.RED}Error: File konfigurasi bot tidak ditemukan!{Colors.NC}")
            sys.exit(1)
        except Exception as e:
            print(f"{Colors.RED}Error membaca konfigurasi bot: {e}{Colors.NC}")
            sys.exit(1)
    
    def setup_server_info(self):
        """Setup informasi server"""
        try:
            # Baca domain
            with open('/etc/xray/domain', 'r') as f:
                self.domain = f.read().strip()
            
            # Dapatkan IP dan informasi server
            self.server_ip = self.get_server_ip()
            self.city = self.get_city_info()
            self.isp = self.get_isp_info()
            
        except FileNotFoundError:
            print(f"{Colors.RED}Error: File domain tidak ditemukan!{Colors.NC}")
            sys.exit(1)
        except Exception as e:
            print(f"{Colors.RED}Error mendapatkan informasi server: {e}{Colors.NC}")
            sys.exit(1)
    
    def setup_user_config(self):
        """Setup konfigurasi user default"""
        self.masa_aktif = 1  # hari (untuk expired config, real expired 60 menit)
        self.quota = 1  # GB
        self.ip_limit = 10
        self.aktif_menit = 60
    
    def get_server_ip(self):
        """Mendapatkan IP server"""
        try:
            response = requests.get('https://ifconfig.me', timeout=10)
            return response.text.strip()
        except:
            return "Unknown"
    
    def get_city_info(self):
        """Mendapatkan informasi kota"""
        try:
            response = requests.get('https://ipinfo.io/city', timeout=10)
            return response.text.strip() or "-"
        except:
            return "-"
    
    def get_isp_info(self):
        """Mendapatkan informasi ISP"""
        try:
            response = requests.get('https://ipinfo.io/org', timeout=10)
            org_info = response.text.strip()
            # Ambil bagian setelah spasi pertama (skip AS number)
            parts = org_info.split(' ', 1)
            return parts[1] if len(parts) > 1 else "-"
        except:
            return "-"
    
    def generate_username(self):
        """Generate username acak"""
        numbers = ''.join(random.choices(string.digits, k=4))
        return f"trial{numbers}"
    
    def generate_uuid(self):
        """Generate UUID"""
        try:
            with open('/proc/sys/kernel/random/uuid', 'r') as f:
                return f.read().strip()
        except:
            # Fallback jika file tidak tersedia
            import uuid
            return str(uuid.uuid4())
    
    def get_dates(self):
        """Generate tanggal pembuatan dan expired"""
        today = datetime.now()
        exp_date = today + timedelta(days=self.masa_aktif)
        
        tgl_buat = today.strftime("%d %b, %Y")
        tgl_exp = exp_date.strftime("%d %b, %Y")
        exp_format = exp_date.strftime("%Y-%m-%d")
        
        return tgl_buat, tgl_exp, exp_format
    
    def update_xray_config(self, username, uuid_str, exp_format):
        """Update konfigurasi Xray untuk VLESS"""
        try:
            config_file = '/etc/xray/config.json'
            
            # Entry baru untuk vless
            vless_entry = f'#& {username} {exp_format}\\n}},{{"id": "{uuid_str}","email": "{username}"'
            
            # Update config untuk vless
            cmd1 = f"sed -i '/#vless$/a\\{vless_entry}' {config_file}"
            subprocess.run(cmd1, shell=True, check=True)
            
            # Update config untuk vlessgrpc
            cmd2 = f"sed -i '/#vlessgrpc$/a\\{vless_entry}' {config_file}"
            subprocess.run(cmd2, shell=True, check=True)
            
            return True
        except Exception as e:
            print(f"{Colors.RED}Error updating Xray config: {e}{Colors.NC}")
            return False
    
    def generate_vless_links(self, username, uuid_str):
        """Generate VLESS links"""
        # VLESS TLS WebSocket
        vless_tls = f"vless://{uuid_str}@{self.domain}:443?path=/vless&security=tls&encryption=none&type=ws#{username}"
        
        # VLESS Non-TLS WebSocket
        vless_ntls = f"vless://{uuid_str}@{self.domain}:80?path=/vless&encryption=none&type=ws#{username}"
        
        # VLESS gRPC
        vless_grpc = f"vless://{uuid_str}@{self.domain}:443?mode=gun&security=tls&encryption=none&type=grpc&serviceName=vless-grpc&sni={self.domain}#{username}"
        
        return vless_tls, vless_ntls, vless_grpc
    
    def create_clash_config(self, username, uuid_str, link_tls, link_ntls, link_grpc):
        """Buat file konfigurasi Clash/OpenClash untuk VLESS"""
        config_content = f"""━━━━━━━━━━━━━━━━━━━━━
  Format For Clash
━━━━━━━━━━━━━━━━━━━━━
# Format Vless WS TLS

- name: Vless-{username}-WS TLS
  server: {self.domain}
  port: 443
  type: vless
  uuid: {uuid_str}
  cipher: auto
  tls: true
  skip-cert-verify: true
  servername: {self.domain}
  network: ws
  ws-opts:
    path: /vless
    headers:
      Host: {self.domain}

# Format Vless WS Non TLS

- name: Vless-{username}-WS (CDN) Non TLS
  server: {self.domain}
  port: 80
  type: vless
  uuid: {uuid_str}
  cipher: auto
  tls: false
  skip-cert-verify: false
  servername: {self.domain}
  network: ws
  ws-opts:
    path: /vless
    headers:
      Host: {self.domain}
  udp: true

# Format Vless gRPC (SNI)

- name: Vless-{username}-gRPC (SNI)
  server: {self.domain}
  port: 443
  type: vless
  uuid: {uuid_str}
  cipher: auto
  tls: true
  skip-cert-verify: true
  servername: {self.domain}
  network: grpc
  grpc-opts:
    grpc-mode: gun
    grpc-service-name: vless-grpc

━━━━━━━━━━━━━━━━━━━━━
Link Akun Vless 
━━━━━━━━━━━━━━━━━━━━━
Link TLS      : 
{link_tls}
━━━━━━━━━━━━━━━━━━━━━
Link none TLS : 
{link_ntls}
━━━━━━━━━━━━━━━━━━━━━
Link GRPC     : 
{link_grpc}
━━━━━━━━━━━━━━━━━━━━━

"""
        
        try:
            # Pastikan direktori ada
            os.makedirs('/var/www/html', exist_ok=True)
            
            # Tulis file konfigurasi
            with open(f'/var/www/html/vless-{username}.txt', 'w') as f:
                f.write(config_content)
            
            return True
        except Exception as e:
            print(f"{Colors.RED}Error creating Clash config: {e}{Colors.NC}")
            return False
    
    def setup_limits(self, username):
        """Setup limit GB dan IP untuk VLESS"""
        try:
            # Buat direktori jika belum ada
            os.makedirs('/etc/vless', exist_ok=True)
            os.makedirs('/etc/kyt/limit/vless/ip', exist_ok=True)
            
            # Set limit IP
            with open(f'/etc/kyt/limit/vless/ip/{username}', 'w') as f:
                f.write(str(self.ip_limit))
            
            # Set quota (dalam bytes)
            quota_bytes = self.quota * 1024 * 1024 * 1024
            with open(f'/etc/vless/{username}', 'w') as f:
                f.write(str(quota_bytes))
            
            return True
        except Exception as e:
            print(f"{Colors.RED}Error setting up limits: {e}{Colors.NC}")
            return False
    
    def save_to_db(self, username, exp_format, uuid_str):
        """Simpan ke database VLESS"""
        try:
            db_file = '/etc/vless/.vless.db'
            
            # Hapus entry lama jika ada
            if os.path.exists(db_file):
                with open(db_file, 'r') as f:
                    lines = f.readlines()
                
                with open(db_file, 'w') as f:
                    for line in lines:
                        if username not in line:
                            f.write(line)
            
            # Tambah entry baru dengan format yang sesuai
            with open(db_file, 'a') as f:
                f.write(f"#& {username} {exp_format} {uuid_str} {self.quota} {self.ip_limit}\n")
            
            return True
        except Exception as e:
            print(f"{Colors.RED}Error saving to database: {e}{Colors.NC}")
            return False
    
    def restart_services(self):
        """Restart services yang diperlukan"""
        try:
            subprocess.run(['systemctl', 'restart', 'xray'], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['systemctl', 'restart', 'nginx'], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            print(f"{Colors.RED}Error restarting services: {e}{Colors.NC}")
            return False
    
    def send_telegram_message(self, message):
        """Kirim pesan ke Telegram"""
        try:
            data = {
                'chat_id': self.chat_id,
                'disable_web_page_preview': 1,
                'text': message,
                'parse_mode': 'html'
            }
            
            response = requests.post(
                self.telegram_url,
                data=data,
                timeout=self.telegram_timeout
            )
            
            return response.status_code == 200
        except Exception as e:
            print(f"{Colors.RED}Error sending Telegram message: {e}{Colors.NC}")
            return False
    
    def create_trial_account(self):
        """Fungsi utama untuk membuat akun VLESS trial"""
        print(f"{Colors.CYAN}Membuat akun VLESS trial...{Colors.NC}")
        
        # Generate data user
        username = self.generate_username()
        uuid_str = self.generate_uuid()
        tgl_buat, tgl_exp, exp_format = self.get_dates()
        
        print(f"{Colors.GREEN}Username: {username}{Colors.NC}")
        print(f"{Colors.GREEN}UUID: {uuid_str}{Colors.NC}")
        
        # Update konfigurasi Xray
        if not self.update_xray_config(username, uuid_str, exp_format):
            return False
        
        # Generate VLESS links
        link_tls, link_ntls, link_grpc = self.generate_vless_links(username, uuid_str)
        
        # Buat file Clash config
        if not self.create_clash_config(username, uuid_str, link_tls, link_ntls, link_grpc):
            return False
        
        # Restart services dulu sebelum setup limits
        if not self.restart_services():
            return False
        
        # Setup limits
        if not self.setup_limits(username):
            return False
        
        # Simpan ke database
        if not self.save_to_db(username, exp_format, uuid_str):
            return False
        
        # Buat pesan untuk Telegram
        telegram_message = f"""
<b>━━━━━━ 𝙑𝙇𝙀𝙎𝙎 𝙋𝙍𝙀𝙈𝙄𝙐𝙈 ━━━━━━</b>

<b>👤 𝙐𝙨𝙚𝙧 𝘿𝙚𝙩𝙖𝙞𝙡𝙨</b>
┣ <b>Username</b>   : <code>{username}</code>
┣ <b>UUID</b>       : <code>{uuid_str}</code>
┣ <b>Quota</b>      : <code>{self.quota} GB</code>
┣ <b>Status</b>     : <code>Aktif {self.masa_aktif} hari</code>
┣ <b>Dibuat</b>     : <code>{tgl_buat}</code>
┗ <b>Expired</b>    : <code>{tgl_exp}</code>

<b>🌎 𝙎𝙚𝙧𝙫𝙚𝙧 𝙄𝙣𝙛𝙤</b>
┣ <b>Domain</b>     : <code>{self.domain}</code>
┣ <b>IP</b>         : <code>{self.server_ip}</code>
┣ <b>Location</b>   : <code>{self.city}</code>
┗ <b>ISP</b>        : <code>{self.isp}</code>

<b>🔗 𝘾𝙤𝙣𝙣𝙚𝙘𝙩𝙞𝙤𝙣</b>
┣ <b>TLS Port</b>        : <code>400-900</code>
┣ <b>Non-TLS Port</b>    : <code>80, 8080, 8081-9999</code>
┣ <b>Network</b>         : <code>ws, grpc</code>
┣ <b>Path</b>            : <code>/vless</code>
┣ <b>gRPC Service</b>    : <code>vless-grpc</code>
┗ <b>Encryption</b>        : <code>none</code>

<b>━━━━━ 𝙑𝙇𝙀𝙎𝙎 𝙋𝙧𝙚𝙢𝙞𝙪𝙢 𝙇𝙞𝙣𝙠𝙨 ━━━━━</b>
<b>📍 𝙒𝙎 𝙏𝙇𝙎</b>
<code>{link_tls}</code>
<b>📍 𝙒𝙎 𝙉𝙤𝙣-𝙏𝙇𝙎</b>
<code>{link_ntls}</code>
<b>📍 𝙜𝙍𝙋𝘾</b>
<code>{link_grpc}</code>

<b>📥 𝘾𝙤𝙣𝙛𝙞𝙜 𝙁𝙞𝙡𝙚 (Clash/OpenClash):</b>
https://{self.domain}:81/vless-{username}.txt

<b>✨ 𝙏𝙤𝙤𝙡𝙨 & 𝙍𝙚𝙨𝙤𝙪𝙧𝙘𝙚𝙨</b>
┣ <a href='https://vpntech.my.id/converteryaml'>YAML Converter</a>
┗ <a href='https://vpntech.my.id/auto-configuration'>Auto Configuration</a>

<b>❓ 𝘽𝙪𝙩𝙪𝙝 𝘽𝙖𝙣𝙩𝙪𝙖𝙣?</b>
<a href='https://t.me/085727035336'>Klik di sini untuk chat Admin</a>

<b>━━━━━━━━━ 𝙏𝙝𝙖𝙣𝙠 𝙔𝙤𝙪 ━━━━━━━━</b>
"""
        
        # Pesan untuk terminal
        terminal_message = f"""
━━━━━━━━━━━ 𝙉𝙀𝙒 𝙑𝙇𝙀𝙎𝙎 𝙋𝙍𝙀𝙈𝙄𝙐𝙈 𝘼𝘾𝘾𝙊𝙐𝙉𝙏 ━━━━━━━━━━━

👤 𝙐𝙨𝙚𝙧 𝘿𝙚𝙩𝙖𝙞𝙡𝙨
┣ Username   : {username}
┣ UUID       : {uuid_str}
┣ Quota      : {self.quota} GB
┣ Limit IP   : {self.ip_limit} IP
┣ Status     : Aktif {self.aktif_menit//60} jam
┣ Dibuat     : {tgl_buat}
┗ Expired    : {tgl_exp}

🌎 𝙎𝙚𝙧𝙫𝙚𝙧 𝙄𝙣𝙛𝙤
┣ Domain     : {self.domain}
┣ VPS IP     : {self.server_ip}
┣ Location   : {self.city}
┗ ISP        : {self.isp}

🔗 𝘾𝙤𝙣𝙣𝙚𝙘𝙩𝙞𝙤𝙣
┣ TLS Port        : 400-900
┣ Non-TLS Port    : 80, 8080, 8081-9999
┣ Network         : ws, grpc
┣ Path            : /vless
┣ gRPC Service    : vless-grpc
┣ Encryption      : none
┗ alterId         : 0

🚀 𝙑𝙇𝙀𝙎𝙎 𝙋𝙧𝙚𝙢𝙞𝙪𝙢 𝙇𝙞𝙣𝙠𝙨
• WS TLS
{link_tls}
• WS Non-TLS
{link_ntls}
• gRPC
{link_grpc}

📥 𝘾𝙤𝙣𝙛𝙞𝙜 𝙁𝙞𝙡𝙚 (Clash/OpenClash):
https://{self.domain}:81/vless-{username}.txt

✨ 𝙏𝙤𝙤𝙡𝙨 & 𝙍𝙚𝙨𝙤𝙪𝙧𝙘𝙚𝙨
┣ https://vpntech.my.id/converteryaml
┗ https://vpntech.my.id/auto-configuration

❓ 𝘽𝙪𝙩𝙪𝙝 𝘽𝙖𝙣𝙩𝙪𝙖𝙣?
https://t.me/085727035336 (Klik untuk chat Admin)

━━━━━━━━━━━ 𝙏𝙝𝙖𝙣𝙠 𝙔𝙤𝙪 ━━━━━━━━━━━
"""
        
        # Clear screen dan tampilkan hasil
        os.system('clear')
        print(f"{Colors.CYAN}{terminal_message}{Colors.NC}")
        
        # Kirim ke Telegram
        self.send_telegram_message(telegram_message)
        
        print(f"{Colors.GREEN}✅ Akun VLESS trial berhasil dibuat!{Colors.NC}")
        return True

def main():
    """Fungsi utama"""
    try:
        creator = VLessTrialCreator()
        creator.create_trial_account()
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}❌ Proses dibatalkan oleh user{Colors.NC}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.NC}")
        sys.exit(1)

if __name__ == "__main__":
    main()