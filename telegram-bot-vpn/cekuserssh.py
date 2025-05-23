#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cekuser-ssh: Script untuk melihat daftar user SSH (username, password-hash, expired) 
dan mengirim notifikasi ke Telegram
Kompatibel dengan Python 3.6+
"""

import os
import sys
import subprocess
import requests
from datetime import datetime
import pwd
import spwd

def baca_config_telegram():
    """Membaca konfigurasi bot token dan chat ID dari file"""
    try:
        with open('/etc/telegram_bot/bot_token', 'r') as f:
            bot_token = f.read().strip()
        with open('/etc/telegram_bot/chat_id', 'r') as f:
            chat_id = f.read().strip()
        return bot_token, chat_id
    except FileNotFoundError as e:
        print(f"❌ Error: File konfigurasi tidak ditemukan - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error membaca konfigurasi: {e}")
        sys.exit(1)

def dapatkan_tanggal_expired(username):
    """Mendapatkan tanggal expired akun user menggunakan chage"""
    try:
        result = subprocess.run(['chage', '-l', username], 
                              capture_output=True, text=True, check=True)
        
        for line in result.stdout.split('\n'):
            if 'Account expires' in line:
                expired_date = line.split(': ', 1)[1].strip()
                return expired_date if expired_date != 'never' else 'Never'
        return 'N/A'
    except subprocess.CalledProcessError:
        return 'N/A'
    except Exception:
        return 'Error'

def dapatkan_password_hash(username):
    """Mendapatkan password hash dari /etc/shadow"""
    try:
        shadow_entry = spwd.getspnam(username)
        password_hash = shadow_entry.sp_pwdp
        
        # Batasi panjang hash jika terlalu panjang
        if len(password_hash) > 40:
            return password_hash[:37] + "..."
        return password_hash
    except KeyError:
        return "No hash"
    except PermissionError:
        return "Access denied"
    except Exception:
        return "Error"

def dapatkan_daftar_user_ssh():
    """Mendapatkan daftar user SSH dengan UID >= 1000 dan bukan 'nobody'"""
    users = []
    
    try:
        for user_info in pwd.getpwall():
            username = user_info.pw_name
            uid = user_info.pw_uid
            
            # Filter user dengan UID >= 1000 dan bukan 'nobody'
            if uid >= 1000 and username != 'nobody':
                password_hash = dapatkan_password_hash(username)
                expired_date = dapatkan_tanggal_expired(username)
                
                users.append({
                    'username': username,
                    'password_hash': password_hash,
                    'expired': expired_date
                })
                
                # Tampilkan ke terminal dengan format yang rapi
                print(f"{username:<20} {password_hash:<44} {expired_date}")
    
    except Exception as e:
        print(f"❌ Error saat membaca daftar user: {e}")
        return []
    
    return users

def buat_pesan_telegram(users):
    """Membuat pesan yang akan dikirim ke Telegram dengan format HTML"""
    if not users:
        return "<b>📋 DAFTAR USER SSH</b>\n\n<i>Tidak ada user SSH yang ditemukan.</i>"
    
    header = "🔐 <b>DAFTAR USER SSH</b> 🔐"
    separator = "━" * 50
    
    # Header tabel
    table_header = "<code>Username         Password Hash                            Expired</code>"
    
    # Body tabel
    body_lines = []
    for user in users:
        username = user['username'][:15].ljust(15)  # Batasi dan padding
        password_hash = user['password_hash'][:36].ljust(36)  # Batasi dan padding
        expired = user['expired']
        
        line = f"<code>{username} {password_hash} {expired}</code>"
        body_lines.append(line)
    
    # Gabungkan semua bagian
    message_parts = [
        header,
        f"<code>{separator}</code>",
        table_header,
        f"<code>{separator}</code>",
        *body_lines,
        f"<code>{separator}</code>",
        f"<i>📊 Total user: {len(users)} | 📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</i>"
    ]
    
    return "\n".join(message_parts)

def kirim_ke_telegram(bot_token, chat_id, message):
    """Mengirim pesan ke Telegram"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }
    
    try:
        print("\n📤 Mengirim pesan ke Telegram...")
        response = requests.post(url, data=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Pesan berhasil dikirim ke Telegram!")
                return True
            else:
                print(f"❌ Telegram API Error: {result.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout: Koneksi ke Telegram terlalu lama")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error koneksi: {e}")
        return False
    except Exception as e:
        print(f"❌ Error tidak terduga: {e}")
        return False

def main():
    """Fungsi utama"""
    print("🔍 Script Cek User SSH - Python Version")
    print("=" * 50)
    
    # Cek apakah script dijalankan sebagai root
    if os.geteuid() != 0:
        print("⚠️  Warning: Script sebaiknya dijalankan sebagai root untuk akses penuh ke /etc/shadow")
    
    try:
        # Baca konfigurasi Telegram
        print("📖 Membaca konfigurasi Telegram...")
        bot_token, chat_id = baca_config_telegram()
        print("✅ Konfigurasi Telegram berhasil dibaca")
        
        # Header output terminal
        print(f"\n{'=' * 70}")
        print("📋 DAFTAR USER SSH")
        print(f"{'=' * 70}")
        print(f"{'Username':<20} {'Password Hash':<44} {'Expired'}")
        print(f"{'-' * 70}")
        
        # Dapatkan daftar user SSH
        users = dapatkan_daftar_user_ssh()
        
        if not users:
            print("ℹ️  Tidak ada user SSH yang ditemukan (UID >= 1000, bukan 'nobody')")
            return
        
        print(f"{'-' * 70}")
        print(f"📊 Total user SSH: {len(users)}")
        
        # Buat pesan untuk Telegram
        message = buat_pesan_telegram(users)
        
        # Kirim ke Telegram
        success = kirim_ke_telegram(bot_token, chat_id, message)
        
        if success:
            print("🎉 Proses selesai dengan sukses!")
        else:
            print("⚠️  Proses selesai tapi gagal mengirim ke Telegram")
            
    except KeyboardInterrupt:
        print("\n⚠️  Proses dibatalkan oleh user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error tidak terduga: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()