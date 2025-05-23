import subprocess
import uuid
import os
from datetime import datetime

# Lokasi script kamu, bisa diubah kalau beda folder
SCRIPT_PATH = os.path.abspath(os.path.dirname(__file__)) + "/"

def run_script(script, args):
    """Jalankan script Python eksternal dan ambil output"""
    cmd = ["python3", os.path.join(SCRIPT_PATH, script)] + [str(a) for a in args]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error: {e}"

# ---------- CREATE ACCOUNT ----------
def create_account(akun_type, protokol, custom_type, custom_value, paket, user_id):
    """
    akun_type: HP/Openwrt
    protokol: ssh/vmess/vless/trojan
    custom_type: custom/random
    custom_value: isi UUID/password custom atau RANDOM
    paket: dict harga, limit_ip, limit_data, masa_aktif
    user_id: id user telegram (bisa jadi username akun)
    """
    day = paket.get("masa_aktif", 30)
    limit_data = paket.get("limit_data", 500)
    limit_ip = paket.get("limit_ip", 10)
    username = f"user{user_id}_{datetime.now().strftime('%d%m%H%M')}"  # username unik
    
    # SSH
    if protokol == "ssh":
        if custom_type == "custom":
            password = custom_value
            args = [username, password, day, limit_data, limit_ip]
        else:  # random
            args = [username, day, limit_data, limit_ip]
        return run_script("create-ssh.py", args)
    # VMESS
    elif protokol == "vmess":
        if custom_type == "custom":
            uuid_val = custom_value
            args = [username, uuid_val, day, limit_data, limit_ip]
        else:
            args = [username, day, limit_data, limit_ip]
        return run_script("create-vmess.py", args)
    # VLESS
    elif protokol == "vless":
        if custom_type == "custom":
            uuid_val = custom_value
            args = [username, uuid_val, day, limit_data, limit_ip]
        else:
            args = [username, day, limit_data, limit_ip]
        return run_script("create-vless.py", args)
    # TROJAN
    elif protokol == "trojan":
        if custom_type == "custom":
            uuid_val = custom_value
            args = [username, uuid_val, day, limit_data, limit_ip]
        else:
            args = [username, day, limit_data, limit_ip]
        return run_script("create-trojan.py", args)
    else:
        return "Protokol tidak dikenali!"

# ---------- CEK USER ----------
def cek_user(protokol):
    """
    protokol: ssh/vmess/vless/trojan
    """
    if protokol == "ssh":
        return run_script("cekuserssh.py", [])
    elif protokol == "vmess":
        return run_script("cekuservmess.py", [])
    elif protokol == "vless":
        return run_script("cekuservless.py", [])
    elif protokol == "trojan":
        return run_script("cekusertrojan.py", [])
    else:
        return "Protokol tidak dikenali!"

# ---------- DELETE USER ----------
def del_user(protokol, username):
    """
    protokol: ssh/vmess/vless/trojan
    username: nama user yang akan dihapus
    """
    if protokol == "ssh":
        return run_script("dellssh.py", [username])
    elif protokol == "vmess":
        return run_script("dellvmess.py", [username])
    elif protokol == "vless":
        return run_script("dellvless.py", [username])
    elif protokol == "trojan":
        return run_script("delltrojan.py", [username])
    else:
        return "Protokol tidak dikenali!"

# ---------- BACKUP ----------
def backup():
    return run_script("backupvpn.py", [])

# ---------- RESTORE ----------
def restore(link_backup):
    # link_backup: URL link Google Drive backup
    return run_script("restorevpn.py", [link_backup])

# ---------- FIXCERT VPN (SSL renewal) ----------
def fixcertvpn():
    return run_script("fixcertvpn.py", [])

# ---------- RESTART SERVICE VPN ----------
def restart_service():
    return run_script("restartservice.py", [])

# ---------- UTILITY: Generate UUID ----------
def generate_uuid():
    return str(uuid.uuid4())

# ---------- UTILITY: Generate random username (optional) ----------
def random_username(prefix="user"):
    return f"{prefix}{datetime.now().strftime('%d%m%H%M%S')}"

# ---------- EXAMPLE USAGE (for debugging, not for production) ----------
if __name__ == "__main__":
    # print(backup())
    # print(restore("https://drive.google.com/u/4/uc?id=EXAMPLE_ID&export=download"))
    # print(cek_user("vless"))
    # print(del_user("ssh", "user12345"))
    # print(fixcertvpn())
    # print(restart_service())
    # print(create_account("HP", "vmess", "random", "", {"masa_aktif": 30, "limit_data": 500, "limit_ip": 10, "harga": 10000}, 12345))
    pass