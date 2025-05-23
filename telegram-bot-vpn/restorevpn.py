#!/usr/bin/env python3
import os
import subprocess
import sys
import time
import requests
import zipfile
from pathlib import Path

# Konfigurasi warna ANSI untuk tampilan terminal
class Warna:
    RED = '\033[1;91m'
    GREEN = '\033[1;92m'
    YELLOW = '\033[1;93m'
    BLUE = '\033[1;94m'
    CYAN = '\033[1;96m'
    NC = '\033[0m'  # Reset warna

def baca_konfigurasi_bot():
    """Membaca konfigurasi Telegram bot dari file database"""
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

def kirim_notifikasi_telegram(key, chat_id):
    """Mengirim notifikasi restore berhasil ke Telegram"""
    time.sleep(2)
    
    timeout = 10
    url = f"https://api.telegram.org/bot{key}/sendMessage"
    
    pesan = """
━━━━━━━━━━※❆※━━━━━━━━━━
𓈃 RESTORE VPS BERHASIL 𓈃
━━━━━━━━━━※❆※━━━━━━━━━━
✅ Restore VPS Sukses!
📌 VPS telah dikembalikan seperti semula.
━━━━━━━━━━※❆※━━━━━━━━━━
"""
    
    payload = {
        'chat_id': chat_id,
        'disable_web_page_preview': 1,
        'text': pesan.strip(),
        'parse_mode': 'html'
    }
    
    try:
        response = requests.post(url, data=payload, timeout=timeout)
        if response.status_code == 200:
            print(f"{Warna.GREEN}Notifikasi Telegram berhasil dikirim{Warna.NC}")
        else:
            print(f"{Warna.RED}Gagal mengirim notifikasi Telegram: {response.status_code}{Warna.NC}")
    except requests.exceptions.RequestException as e:
        print(f"{Warna.RED}Error mengirim notifikasi Telegram: {e}{Warna.NC}")

def tampilkan_progress(pesan, persentase):
    """Menampilkan progress bar dengan animasi"""
    # Membuat progress bar visual berdasarkan persentase
    if persentase <= 10:
        bar = "■□□□□□□□□□"
    elif persentase <= 40:
        bar = "■■■■□□□□□□"
    elif persentase <= 80:
        bar = "■■■■■■■■□□"
    else:
        bar = "■■■■■■■■■■"
    
    print(f"\r📂 {Warna.GREEN}{pesan}{Warna.NC}   [{bar}] {persentase}%", end="", flush=True)
    time.sleep(2)

def unduh_file_backup(url):
    """Mengunduh file backup dari URL yang diberikan"""
    try:
        print(f"{Warna.CYAN}Mengunduh dari: {Warna.NC}{url}")
        
        # Menggunakan requests untuk download
        response = requests.get(url, stream=True, timeout=300)  # 5 menit timeout
        response.raise_for_status()
        
        with open('backup.zip', 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return True
    except requests.exceptions.RequestException as e:
        print(f"\n{Warna.RED}Error mengunduh file: {e}{Warna.NC}")
        return False
    except Exception as e:
        print(f"\n{Warna.RED}Error tak terduga saat download: {e}{Warna.NC}")
        return False

def ekstrak_file_backup():
    """Mengekstrak file backup ZIP"""
    try:
        with zipfile.ZipFile('backup.zip', 'r') as zip_ref:
            zip_ref.extractall('/root')
        
        # Hapus file ZIP setelah ekstrak
        if Path('backup.zip').exists():
            os.remove('backup.zip')
        
        return True
    except zipfile.BadZipFile:
        print(f"\n{Warna.RED}Error: File backup rusak atau bukan file ZIP{Warna.NC}")
        return False
    except Exception as e:
        print(f"\n{Warna.RED}Error mengekstrak file: {e}{Warna.NC}")
        return False

def jalankan_perintah(perintah):
    """Menjalankan perintah sistem dengan penanganan error"""
    try:
        result = subprocess.run(perintah, shell=True, check=True, 
                              capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"{Warna.RED}Warning: Gagal menjalankan '{perintah}'{Warna.NC}")
        return False
    except Exception as e:
        print(f"{Warna.RED}Error menjalankan perintah: {e}{Warna.NC}")
        return False

def pulihkan_konfigurasi():
    """Memulihkan konfigurasi VPS dari backup"""
    backup_path = Path('/root/backup')
    
    if not backup_path.exists():
        print(f"\n{Warna.RED}Error: Folder backup tidak ditemukan{Warna.NC}")
        return False
    
    try:
        # Pindah ke direktori backup
        os.chdir('/root/backup')
        
        # Restore file sistem
        file_sistem = [
            ('passwd', '/etc/'),
            ('group', '/etc/'),
            ('shadow', '/etc/'),
            ('gshadow', '/etc/')
        ]
        
        for file_src, dest_dir in file_sistem:
            if Path(file_src).exists():
                jalankan_perintah(f"cp {file_src} {dest_dir}")
        
        # Restore folder konfigurasi
        folder_config = [
            ('kyt', '/etc/'),
            ('xray', '/etc/'),
            ('vmess', '/etc/'),
            ('vless', '/etc/'),
            ('trojan', '/etc/'),
            ('shodowshocks', '/etc/'),  # Tetap pakai 'shodowshocks' sesuai script asli
            ('html', '/var/www/'),
            ('crontab', '/etc/')
        ]
        
        for folder_src, dest_dir in folder_config:
            if Path(folder_src).exists():
                if folder_src == 'crontab':
                    # File biasa, bukan folder
                    jalankan_perintah(f"cp {folder_src} {dest_dir}")
                else:
                    # Folder
                    jalankan_perintah(f"cp -r {folder_src} {dest_dir}")
        
        return True
        
    except Exception as e:
        print(f"\n{Warna.RED}Error saat restore konfigurasi: {e}{Warna.NC}")
        return False

def bersihkan_file_sementara():
    """Membersihkan file backup sementara"""
    try:
        # Kembali ke root directory
        os.chdir('/root')
        
        # Hapus folder backup
        if Path('/root/backup').exists():
            jalankan_perintah("rm -rf /root/backup")
        
        # Hapus file ZIP jika masih ada
        if Path('/root/backup.zip').exists():
            os.remove('/root/backup.zip')
            
    except Exception as e:
        print(f"{Warna.RED}Warning: Gagal membersihkan file sementara: {e}{Warna.NC}")

def tampilkan_hasil_akhir():
    """Menampilkan hasil akhir restore"""
    os.system('clear')
    print(f"{Warna.YELLOW}━━━━━━━━━━━━━━━━※❆※━━━━━━━━━━━━━━━━{Warna.NC}")
    print(f"✅ {Warna.GREEN}RESTORE VPS SELESAI{Warna.NC}")
    print(f"{Warna.YELLOW}━━━━━━━━━━━━━━━━※❆※━━━━━━━━━━━━━━━━{Warna.NC}")
    print(f"🔄 {Warna.CYAN}VPS telah dikembalikan seperti semula.{Warna.NC}")
    print(f"{Warna.YELLOW}━━━━━━━━━━━━━━━━※❆※━━━━━━━━━━━━━━━━{Warna.NC}")

def main():
    """Fungsi utama"""
    try:
        # Cek argumen
        if len(sys.argv) < 2:
            print(f"{Warna.RED}❌ Link backup belum diberikan!{Warna.NC}")
            print("Cara pakai: python3 restore_vps.py {link backup}")
            sys.exit(1)
        
        url_backup = sys.argv[1]
        
        # Baca konfigurasi bot
        key, chat_id = baca_konfigurasi_bot()
        
        # Tampilkan header proses restore
        os.system('clear')
        print(f"{Warna.YELLOW}━━━━━━━━━━━━━━━━※❆※━━━━━━━━━━━━━━━━{Warna.NC}")
        print(f"🔄 {Warna.CYAN}MEMULAI PROSES RESTORE...{Warna.NC}")
        print(f"{Warna.YELLOW}━━━━━━━━━━━━━━━━※❆※━━━━━━━━━━━━━━━━{Warna.NC}")
        time.sleep(1)
        
        print(f"{Warna.CYAN}Menggunakan link backup:{Warna.NC} {url_backup}")
        print(f"{Warna.YELLOW}━━━━━━━━━━━━━━━━※❆※━━━━━━━━━━━━━━━━{Warna.NC}")
        
        # Proses restore dengan progress bar
        tampilkan_progress("Mengunduh file backup", 10)
        if not unduh_file_backup(url_backup):
            print(f"\n{Warna.RED}Gagal mengunduh file backup{Warna.NC}")
            sys.exit(1)
        
        tampilkan_progress("Mengekstrak file backup", 40)
        if not ekstrak_file_backup():
            print(f"\n{Warna.RED}Gagal mengekstrak file backup{Warna.NC}")
            sys.exit(1)
        
        tampilkan_progress("Memulihkan konfigurasi VPS", 80)
        if not pulihkan_konfigurasi():
            print(f"\n{Warna.RED}Gagal memulihkan konfigurasi{Warna.NC}")
            sys.exit(1)
        
        tampilkan_progress("Finalisasi proses restore", 100)
        
        # Kirim notifikasi Telegram
        kirim_notifikasi_telegram(key, chat_id)
        
        # Bersihkan file sementara
        bersihkan_file_sementara()
        
        # Tampilkan hasil akhir
        tampilkan_hasil_akhir()
        
        print(f"\n{Warna.GREEN}Proses restore selesai!{Warna.NC}")
        
    except KeyboardInterrupt:
        print(f"\n{Warna.RED}Proses dibatalkan oleh user{Warna.NC}")
        # Bersihkan file jika ada
        bersihkan_file_sementara()
        sys.exit(1)
    except Exception as e:
        print(f"{Warna.RED}Error tak terduga: {e}{Warna.NC}")
        # Bersihkan file jika ada
        bersihkan_file_sementara()
        sys.exit(1)

if __name__ == "__main__":
    main()