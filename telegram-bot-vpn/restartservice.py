#!/usr/bin/env python3
import os
import subprocess
import sys
import time

# Konfigurasi warna terminal
class Warna:
    GREEN = '\033[0;32m'
    NC = '\033[0;37m'  # Normal Color

def jalankan_perintah(perintah):
    """Menjalankan perintah sistem dengan penanganan error"""
    try:
        result = subprocess.run(perintah, shell=True, check=True, 
                              capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"{Warna.GREEN}Warning: Gagal menjalankan '{perintah}' - {e}{Warna.NC}")
        return False
    except Exception as e:
        print(f"{Warna.GREEN}Error tak terduga saat menjalankan '{perintah}': {e}{Warna.NC}")
        return False

def restart_service_systemctl(nama_service):
    """Restart service menggunakan systemctl"""
    print(f"{Warna.GREEN}Restarting {nama_service}...{Warna.NC}")
    return jalankan_perintah(f"systemctl restart {nama_service}")

def restart_service_initd(nama_service):
    """Restart service menggunakan /etc/init.d/"""
    print(f"{Warna.GREEN}Restarting {nama_service}...{Warna.NC}")
    return jalankan_perintah(f"/etc/init.d/{nama_service} restart")

def kelola_udp_service(nama_service):
    """Mengelola UDP service dengan disable, stop, enable, start"""
    print(f"{Warna.GREEN}Mengelola service {nama_service}...{Warna.NC}")
    
    # Disable service
    jalankan_perintah(f"systemctl disable {nama_service}")
    
    # Stop service  
    jalankan_perintah(f"systemctl stop {nama_service}")
    
    # Enable service
    jalankan_perintah(f"systemctl enable {nama_service}")
    
    # Start service
    jalankan_perintah(f"systemctl start {nama_service}")

def restart_semua_service():
    """Restart semua service sesuai urutan script asli"""
    
    # Clear screen
    os.system('clear')
    
    print("")
    print(f" {Warna.GREEN} Starting Restart All Service {Warna.NC}")
    time.sleep(2)
    
    # Daftar service untuk restart dengan systemctl
    systemctl_services = [
        'ws',
        'haproxy', 
        'xray',
        'openvpn'
    ]
    
    # Restart service dengan systemctl
    for service in systemctl_services:
        restart_service_systemctl(service)
    
    # Restart SSH dengan dua metode (init.d dan systemctl)
    restart_service_initd('ssh')
    restart_service_systemctl('ssh')
    
    # Daftar service untuk restart dengan /etc/init.d/
    initd_services = [
        'dropbear',
        'openvpn', 
        'fail2ban',
        'nginx'
    ]
    
    # Restart service dengan /etc/init.d/
    for service in initd_services:
        restart_service_initd(service)
    
    # Kelola UDP mini services dengan urutan khusus
    udp_services = [
        'udp-mini-1',
        'udp-mini-2', 
        'udp-mini-3'
    ]
    
    # Kelola setiap UDP service
    for udp_service in udp_services:
        kelola_udp_service(udp_service)
    
    print("")
    print(f" {Warna.GREEN} Back to menu in 2 sec {Warna.NC}")
    time.sleep(2)

def main():
    """Fungsi utama"""
    try:
        restart_semua_service()
        print(f"\n{Warna.GREEN}Semua service berhasil di-restart!{Warna.NC}")
        
    except KeyboardInterrupt:
        print(f"\n{Warna.GREEN}Proses dibatalkan oleh user{Warna.NC}")
        sys.exit(1)
    except Exception as e:
        print(f"{Warna.GREEN}Error tak terduga: {e}{Warna.NC}")
        sys.exit(1)

if __name__ == "__main__":
    main()