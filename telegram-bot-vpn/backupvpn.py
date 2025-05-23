#!/usr/bin/env python3
import os
import subprocess
import sys
import time
import zipfile
import requests
import smtplib
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Konfigurasi warna ANSI
class Warna:
    CYAN = '\033[1;96m'
    GREEN = '\033[1;92m'
    YELLOW = '\033[1;93m'
    RED = '\033[1;91m'
    NC = '\033[0m'  # Reset warna

def baca_konfigurasi_bot():
    """Membaca konfigurasi bot dari file database"""
    try:
        with open('/etc/bot/.bot.db', 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            if line.startswith('#bot# '):
                parts = line.strip().split(' ')
                if len(parts) >= 3:
                    key = parts[1]
                    chat_id = parts[2]
                    return key, chat_id
        
        raise ValueError("Konfigurasi bot tidak ditemukan")
    except FileNotFoundError:
        print(f"{Warna.RED}Error: File konfigurasi bot tidak ditemukan di /etc/bot/.bot.db{Warna.NC}")
        sys.exit(1)
    except Exception as e:
        print(f"{Warna.RED}Error membaca konfigurasi bot: {e}{Warna.NC}")
        sys.exit(1)

def jalankan_perintah(perintah, capture_output=False):
    """Menjalankan perintah shell dengan penanganan error"""
    try:
        if capture_output:
            result = subprocess.run(perintah, shell=True, capture_output=True, text=True)
            return result.stdout.strip() if result.returncode == 0 else None
        else:
            result = subprocess.run(perintah, shell=True, check=True)
            return True
    except subprocess.CalledProcessError as e:
        print(f"{Warna.RED}Perintah gagal: {perintah}{Warna.NC}")
        return False
    except Exception as e:
        print(f"{Warna.RED}Error tak terduga: {e}{Warna.NC}")
        return False

def dapatkan_ip_publik():
    """Mendapatkan IP publik VPS"""
    try:
        response = requests.get('https://ipv4.icanhazip.com', timeout=10)
        return response.text.strip()
    except:
        # Fallback jika gagal
        ip = jalankan_perintah("curl -sS ipv4.icanhazip.com", capture_output=True)
        return ip if ip else "Unknown"

def dapatkan_domain():
    """Membaca domain dari file konfigurasi"""
    try:
        with open('/etc/xray/domain', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"{Warna.RED}File domain tidak ditemukan di /etc/xray/domain{Warna.NC}")
        return "Unknown"
    except Exception as e:
        print(f"{Warna.RED}Error membaca file domain: {e}{Warna.NC}")
        return "Unknown"

def dapatkan_email():
    """Mendapatkan atau meminta email untuk backup"""
    email_file = '/root/email'
    
    try:
        with open(email_file, 'r') as f:
            email = f.read().strip()
        if email:
            return email
    except FileNotFoundError:
        pass
    
    # Jika email tidak ada, minta input dari user
    os.system('clear')
    print(f"{Warna.CYAN}Masukkan Email Untuk Menerima Backup{Warna.NC}")
    print("━━━━━━━━━━━━━━※❆※━━━━━━━━━━━━━━━━")
    email = input("📧 Input Email: ").strip()
    print("━━━━━━━━━━━━━━※❆※━━━━━━━━━━━━━━━━")
    
    # Simpan email ke file
    try:
        with open(email_file, 'w') as f:
            f.write(email)
    except Exception as e:
        print(f"{Warna.RED}Error menyimpan email: {e}{Warna.NC}")
    
    return email

def tampilkan_progress(pesan, persentase):
    """Menampilkan progress bar dengan animasi"""
    # Membuat progress bar visual
    total_bars = 10
    filled_bars = int((persentase / 100) * total_bars)
    empty_bars = total_bars - filled_bars
    
    bar = "■" * filled_bars + "□" * empty_bars
    
    print(f"\r📂 {Warna.GREEN}{pesan}{Warna.NC}   [{bar}] {persentase}%", end="", flush=True)
    time.sleep(2)

def siapkan_folder_backup():
    """Menyiapkan folder backup dengan menghapus yang lama"""
    backup_path = Path('/root/backup')
    
    # Hapus folder backup lama jika ada
    if backup_path.exists():
        jalankan_perintah("rm -rf /root/backup")
    
    # Buat folder backup baru
    backup_path.mkdir(exist_ok=True)
    return backup_path

def salin_file_sistem(backup_path):
    """Menyalin file-file sistem penting"""
    file_sistem = [
        '/etc/passwd',
        '/etc/group', 
        '/etc/shadow',
        '/etc/gshadow'
    ]
    
    for file_path in file_sistem:
        if Path(file_path).exists():
            jalankan_perintah(f"cp {file_path} {backup_path}/")

def salin_konfigurasi(backup_path):
    """Menyalin file-file konfigurasi aplikasi"""
    folder_config = [
        '/etc/xray',
        '/etc/kyt',
        '/etc/vmess',
        '/etc/vless', 
        '/etc/trojan',
        '/etc/shadowshocks'
    ]
    
    for folder in folder_config:
        if Path(folder).exists():
            folder_name = Path(folder).name
            jalankan_perintah(f"cp -r {folder} {backup_path}/{folder_name}")

def buat_zip_backup(ip, tanggal):
    """Membuat file ZIP dari backup"""
    os.chdir('/root')
    nama_file = f"{ip}-{tanggal}.zip"
    
    # Buat ZIP file
    with zipfile.ZipFile(nama_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        backup_path = Path('/root/backup')
        for file_path in backup_path.rglob('*'):
            if file_path.is_file():
                # Hitung path relatif untuk struktur ZIP
                relative_path = file_path.relative_to(Path('/root'))
                zipf.write(file_path, relative_path)
    
    return nama_file

def upload_ke_google_drive(nama_file):
    """Upload file backup ke Google Drive menggunakan rclone"""
    # Upload ke Google Drive
    upload_success = jalankan_perintah(f"rclone copy '/root/{nama_file}' dr:backup/")
    
    if not upload_success:
        print(f"{Warna.RED}Gagal upload ke Google Drive{Warna.NC}")
        return None
    
    # Dapatkan link download
    url = jalankan_perintah(f"rclone link dr:backup/{nama_file}", capture_output=True)
    
    if url and 'id=' in url:
        # Extract ID dari URL
        try:
            file_id = url.split('id=')[1].split('&')[0]
            download_link = f"https://drive.google.com/u/4/uc?id={file_id}&export=download"
            return download_link
        except:
            return url
    
    return url

def kirim_email_backup(email, ip, domain, tanggal, link):
    """Mengirim email notifikasi backup"""
    pesan_email = f"""
━━━━━━━━━━━━━━※❆※━━━━━━━━━━━━━━━━
🔹 BACKUP VPS BERHASIL 🔹
━━━━━━━━━━━━━━※❆※━━━━━━━━━━━━━━━━
📌 IP VPS       : {ip}
🌐 DOMAIN       : {domain}
📅 TANGGAL      : {tanggal}
━━━━━━━━━━━━━━※❆※━━━━━━━━━━━━━━━━
📂 LINK BACKUP :  
{link}
━━━━━━━━━━━━━━※❆※━━━━━━━━━━━━━━━━
✅ Backup selesai!  
📌 Simpan link ini dan gunakan untuk restore di VPS baru.
"""
    
    # Kirim email menggunakan perintah mail
    try:
        process = subprocess.Popen(['mail', '-s', 'Backup Data', email], 
                                 stdin=subprocess.PIPE, text=True)
        process.communicate(input=pesan_email)
        return process.returncode == 0
    except Exception as e:
        print(f"{Warna.RED}Error mengirim email: {e}{Warna.NC}")
        return False

def kirim_notifikasi_telegram(key, chat_id, ip, domain, tanggal, link):
    """Mengirim notifikasi ke Telegram"""
    timeout = 10
    url = f"https://api.telegram.org/bot{key}/sendMessage"
    
    pesan = f"""
━━━━━━━━━━※ ·❆· ※━━━━━━━━━━
𓈃 BACKUP VPS BERHASIL 𓈃
━━━━━━━━━━※ ·❆· ※━━━━━━━━━━
📌 IP VPS       : {ip}
🌐 DOMAIN       : {domain}
📅 TANGGAL      : {tanggal}
━━━━━━━━━━※ ·❆· ※━━━━━━━━━━
📂 LINK BACKUP :  
{link}
━━━━━━━━━━※ ·❆· ※━━━━━━━━━━
✅ Backup selesai!  
📌 Simpan link ini dan gunakan untuk restore di VPS baru, Onii-Chan.
"""
    
    payload = {
        'chat_id': chat_id,
        'disable_web_page_preview': 1,
        'text': pesan.strip(),
        'parse_mode': 'html'
    }
    
    try:
        response = requests.post(url, data=payload, timeout=timeout)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"{Warna.RED}Error mengirim notifikasi Telegram: {e}{Warna.NC}")
        return False

def bersihkan_file_sementara(nama_file):
    """Membersihkan file backup lokal"""
    try:
        # Hapus folder backup
        jalankan_perintah("rm -rf /root/backup")
        
        # Hapus file ZIP
        if Path(f"/root/{nama_file}").exists():
            os.remove(f"/root/{nama_file}")
    except Exception as e:
        print(f"{Warna.RED}Error membersihkan file: {e}{Warna.NC}")

def tampilkan_hasil_akhir(ip, domain, tanggal, link):
    """Menampilkan hasil akhir backup"""
    os.system('clear')
    print(f"{Warna.YELLOW}━━━━━━━━━━━━━━※❆※━━━━━━━━━━━━━━━━{Warna.NC}")
    print(f"🔹 {Warna.CYAN}BACKUP VPS BERHASIL{Warna.NC} 🔹")
    print(f"{Warna.YELLOW}━━━━━━━━━━━━━━※❆※━━━━━━━━━━━━━━━━{Warna.NC}")
    print(f"📌 {Warna.GREEN}IP VPS       : {Warna.NC}{ip}")
    print(f"🌐 {Warna.GREEN}DOMAIN       : {Warna.NC}{domain}")
    print(f"📅 {Warna.GREEN}TANGGAL      : {Warna.NC}{tanggal}")
    print(f"📂 {Warna.GREEN}LINK BACKUP  : {Warna.NC}{link}")
    print(f"{Warna.YELLOW}━━━━━━━━━━━━━━※❆※━━━━━━━━━━━━━━━━{Warna.NC}")
    print(f"✅ {Warna.GREEN}Backup selesai! Simpan link ini untuk restore di VPS baru.{Warna.NC}")

def main():
    """Fungsi utama"""
    try:
        # Baca konfigurasi bot
        key, chat_id = baca_konfigurasi_bot()
        
        # Dapatkan informasi VPS
        ip = dapatkan_ip_publik()
        domain = dapatkan_domain()
        tanggal = datetime.now().strftime("%Y-%m-%d")
        
        # Dapatkan email
        email = dapatkan_email()
        
        # Tampilkan header proses backup
        os.system('clear')
        print(f"{Warna.YELLOW}━━━━━━━━━━━━━━※❆※━━━━━━━━━━━━━━━━{Warna.NC}")
        print(f"🔹 {Warna.CYAN}MEMULAI PROSES BACKUP...{Warna.NC}")
        print(f"{Warna.YELLOW}━━━━━━━━━━━━━━※❆※━━━━━━━━━━━━━━━━{Warna.NC}")
        time.sleep(1)
        
        # Proses backup dengan progress bar
        backup_path = siapkan_folder_backup()
        
        tampilkan_progress("Menyalin file sistem", 10)
        salin_file_sistem(backup_path)
        
        tampilkan_progress("Menyalin file konfigurasi", 40)  
        salin_konfigurasi(backup_path)
        
        tampilkan_progress("Kompresi file backup", 80)
        nama_file = buat_zip_backup(ip, tanggal)
        
        tampilkan_progress("Mengunggah ke Google Drive", 100)
        link = upload_ke_google_drive(nama_file)
        
        print(f"\n✅ {Warna.GREEN}Backup berhasil!{Warna.NC}")
        time.sleep(1)
        
        # Kirim email notifikasi
        kirim_email_backup(email, ip, domain, tanggal, link)
        
        # Bersihkan file sementara
        bersihkan_file_sementara(nama_file)
        
        # Tampilkan hasil akhir
        tampilkan_hasil_akhir(ip, domain, tanggal, link)
        
        # Kirim notifikasi Telegram
        kirim_notifikasi_telegram(key, chat_id, ip, domain, tanggal, link)
        
        print(f"\n{Warna.GREEN}Proses backup selesai!{Warna.NC}")
        
    except KeyboardInterrupt:
        print(f"\n{Warna.RED}Proses dibatalkan oleh user{Warna.NC}")
        sys.exit(1)
    except Exception as e:
        print(f"{Warna.RED}Error tak terduga: {e}{Warna.NC}")
        sys.exit(1)

if __name__ == "__main__":
    main()