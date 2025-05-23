#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cekuser-vmess: Daftar user VMESS (username, uuid, expired) + kirim ke Telegram
Konversi dari Bash ke Python dengan peningkatan tampilan dan error handling
"""

import json
import re
import requests
import sys
from pathlib import Path
from datetime import datetime
import urllib.parse

class VmessUserChecker:
    def __init__(self):
        self.bot_token = self._read_file('/etc/telegram_bot/bot_token')
        self.chat_id = self._read_file('/etc/telegram_bot/chat_id')
        self.config_path = '/etc/xray/config.json'
        
    def _read_file(self, file_path):
        """Membaca file dan mengembalikan isinya, dengan error handling"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            print(f"❌ Error: File {file_path} tidak ditemukan!")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error membaca file {file_path}: {str(e)}")
            sys.exit(1)
    
    def _read_xray_config(self):
        """Membaca konfigurasi Xray"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"❌ Error: File konfigurasi Xray {self.config_path} tidak ditemukan!")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error membaca konfigurasi Xray: {str(e)}")
            sys.exit(1)
    
    def _extract_users(self, config_content):
        """Ekstrak daftar user VMESS dari konfigurasi Xray"""
        users = []
        lines = config_content.split('\n')
        
        for line in lines:
            # Cari baris yang dimulai dengan "### " (komentar user VMESS)
            if line.strip().startswith('### '):
                parts = line.strip().split()
                if len(parts) >= 3:
                    username = parts[1]
                    expired = parts[2]
                    users.append({'username': username, 'expired': expired})
        
        return users
    
    def _find_uuid_for_user(self, config_content, username):
        """Mencari UUID untuk user VMESS tertentu"""
        try:
            # Parse sebagai JSON untuk mendapatkan struktur yang tepat
            config_json = json.loads(config_content)
            
            # Cari dalam inbounds untuk konfigurasi VMESS
            for inbound in config_json.get('inbounds', []):
                if inbound.get('protocol') == 'vmess':
                    settings = inbound.get('settings', {})
                    clients = settings.get('clients', [])
                    
                    for client in clients:
                        # Cek berdasarkan email atau identifikasi lain
                        if client.get('email') == username:
                            return client.get('id', 'N/A')
                        # Atau cek jika username ada dalam string representasi client
                        if username in str(client):
                            return client.get('id', 'N/A')
            
            # Fallback: cari dengan regex seperti script bash asli
            pattern = rf'###\s+{re.escape(username)}'
            lines = config_content.split('\n')
            
            for i, line in enumerate(lines):
                if re.search(pattern, line):
                    # Cari 2 baris ke depan untuk "id" (UUID)
                    for j in range(i+1, min(i+3, len(lines))):
                        if '"id"' in lines[j]:
                            match = re.search(r'"id"\s*:\s*"([^"]+)"', lines[j])
                            if match:
                                return match.group(1)
            
            return 'N/A'
            
        except json.JSONDecodeError:
            # Jika tidak bisa parse JSON, gunakan regex fallback
            pattern = rf'###\s+{re.escape(username)}'
            lines = config_content.split('\n')
            
            for i, line in enumerate(lines):
                if re.search(pattern, line):
                    for j in range(i+1, min(i+3, len(lines))):
                        if '"id"' in lines[j]:
                            match = re.search(r'"id"\s*:\s*"([^"]+)"', lines[j])
                            if match:
                                return match.group(1)
            
            return 'N/A'
    
    def _format_terminal_output(self, users_data):
        """Format output untuk terminal dengan tabel yang rapi"""
        if not users_data:
            print("📋 Tidak ada user VMESS yang ditemukan.")
            return
        
        # Header
        header = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        title = "DAFTAR USER VMESS"
        
        print(f"\n🔍 {title}")
        print(header)
        print(f"{'USERNAME':<20} {'UUID':<36} {'EXPIRED':<12} {'STATUS':<10}")
        print("─" * 82)
        
        current_date = datetime.now()
        
        for user_data in users_data:
            username = user_data['username']
            uuid = user_data['uuid']
            expired = user_data['expired']
            
            # Cek status expired
            try:
                exp_date = datetime.strptime(expired, '%Y-%m-%d')
                if exp_date < current_date:
                    status = "❌ EXPIRED"
                else:
                    days_left = (exp_date - current_date).days
                    if days_left <= 3:
                        status = f"⚠️  {days_left}d left"
                    else:
                        status = "✅ ACTIVE"
            except:
                status = "❓ UNKNOWN"
            
            print(f"{username:<20} {uuid:<36} {expired:<12} {status:<10}")
        
        print(header)
        print(f"📊 Total user ditemukan: {len(users_data)}")
        print(f"📅 Dicek pada: {current_date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def _create_telegram_message(self, users_data):
        """Membuat pesan Telegram dengan format HTML yang rapi"""
        if not users_data:
            return "<b>📋 DAFTAR USER VMESS</b>\n\n❌ Tidak ada user yang ditemukan."
        
        # Header pesan
        header = "<b>🔍 DAFTAR USER VMESS</b>"
        separator = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        # Header tabel
        table_header = f"<code>{'USERNAME':<16} {'UUID':<36} {'EXPIRED':<10}</code>"
        
        # Body pesan
        body_lines = []
        current_date = datetime.now()
        active_count = 0
        expired_count = 0
        warning_count = 0
        
        for user_data in users_data:
            username = user_data['username'][:16]  # Potong jika terlalu panjang
            uuid = user_data['uuid'][:36]
            expired = user_data['expired']
            
            # Cek status untuk statistik
            try:
                exp_date = datetime.strptime(expired, '%Y-%m-%d')
                if exp_date < current_date:
                    expired_count += 1
                    status_emoji = "❌"
                else:
                    days_left = (exp_date - current_date).days
                    if days_left <= 3:
                        warning_count += 1
                        status_emoji = "⚠️"
                    else:
                        active_count += 1
                        status_emoji = "✅"
            except:
                status_emoji = "❓"
            
            # Format baris tabel
            formatted_line = f"<code>{username:<16} {uuid:<36} {expired:<10}</code> {status_emoji}"
            body_lines.append(formatted_line)
        
        # Statistik yang lebih detail
        stats = f"\n📊 <b>STATISTIK:</b>\n" \
                f"• Total User: {len(users_data)}\n" \
                f"• ✅ Active: {active_count}\n" \
                f"• ⚠️ Warning: {warning_count}\n" \
                f"• ❌ Expired: {expired_count}\n" \
                f"• 📅 Dicek: {current_date.strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Gabungkan semua bagian
        message_parts = [
            header,
            separator,
            table_header,
            separator[:30],
            *body_lines,
            separator,
            stats
        ]
        
        return "\n".join(message_parts)
    
    def _send_telegram_message(self, message):
        """Kirim pesan ke Telegram"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
            
            print("📤 Mengirim pesan ke Telegram...")
            
            response = requests.post(url, data=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    print("✅ Pesan berhasil dikirim ke Telegram!")
                    return True
                else:
                    print(f"❌ Gagal mengirim pesan: {result.get('description', 'Unknown error')}")
                    return False
            else:
                print(f"❌ HTTP Error {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ Timeout saat mengirim pesan ke Telegram (>10 detik)")
            return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Error saat mengirim pesan ke Telegram: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ Error tidak terduga: {str(e)}")
            return False
    
    def run(self):
        """Menjalankan proses utama"""
        print("🚀 Memulai pengecekan user VMESS...")
        
        # Baca konfigurasi Xray
        print("📖 Membaca konfigurasi Xray...")
        config_content = self._read_xray_config()
        
        # Ekstrak daftar user
        print("🔍 Mengekstrak daftar user VMESS...")
        users = self._extract_users(config_content)
        
        if not users:
            print("❌ Tidak ada user VMESS yang ditemukan dalam konfigurasi.")
            return
        
        # Cari UUID untuk setiap user
        print(f"🔑 Mencari UUID untuk {len(users)} user...")
        users_data = []
        
        for user in users:
            uuid = self._find_uuid_for_user(config_content, user['username'])
            users_data.append({
                'username': user['username'],
                'uuid': uuid,
                'expired': user['expired']
            })
        
        # Tampilkan di terminal
        self._format_terminal_output(users_data)
        
        # Buat dan kirim pesan Telegram
        telegram_message = self._create_telegram_message(users_data)
        success = self._send_telegram_message(telegram_message)
        
        if success:
            print("\n🎉 Proses selesai! Data user telah ditampilkan dan dikirim ke Telegram.")
        else:
            print("\n⚠️  Proses selesai dengan peringatan. Data ditampilkan tapi gagal dikirim ke Telegram.")

def main():
    """Fungsi utama"""
    try:
        checker = VmessUserChecker()
        checker.run()
    except KeyboardInterrupt:
        print("\n\n⏹️  Proses dibatalkan oleh user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error fatal: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()