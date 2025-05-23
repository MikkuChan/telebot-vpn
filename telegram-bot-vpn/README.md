# Bot Telegram Autoorder VPN (User & Admin Panel)

Bot Telegram ini berfungsi sebagai sistem autoorder VPN (multi protokol: SSH, VMESS, VLESS, TROJAN) dengan fitur panel user/admin, topup saldo, notifikasi, dan sepenuhnya menggunakan tombol (inline button).  
Seluruh logic pembuatan/cek/hapus akun VPN dll dihandle oleh script Python yang sudah ada pada repo ini, sehingga mudah dikembangkan dan diintegrasikan!

---

## 📁 Struktur Folder

```
telegram-bot-vpn/
│
├── bot.py            # Main bot Telegram (handler menu user/admin, tombol)
├── config.py         # Konfigurasi bot (token, owner, harga default, link QRIS)
├── db.py             # Database sederhana (file JSON)
├── vpn_utils.py      # Wrapper panggil script VPN (create, cek, hapus, backup, restore, dll)
├── db.json           # File database otomatis
├── create-ssh.py, create-vmess.py, dst  # Script Python auto VPN kamu
└── requirements.txt  # Dependensi Python
```

---

## 🚀 Cara Instalasi & Menjalankan

1. **Clone repo & masuk ke folder:**
   ```sh
   git clone https://github.com/MikkuChan/telegram-bot-vpn.git
   cd telegram-bot-vpn
   ```

2. **Install dependensi Python:**
   ```sh
   pip install -r requirements.txt
   ```

3. **Edit `config.py`:**  
   - Isi `BOT_TOKEN` dengan token bot Telegram kamu.
   - Isi `OWNER_ID` dengan id Telegram owner/admin utama.

4. **Pastikan semua script VPN (.py) ada di folder yang sama dengan `bot.py`.**

5. **Jalankan bot:**
   ```sh
   python3 bot.py
   ```

---

## 📝 Fitur Utama

### Menu User (via tombol):
- **/daftar** — Daftar otomatis (langsung terdaftar)
- **/cekharga** — Lihat harga & detail paket VPN
- **/topup** — Pilih nominal, dapat QRIS, lalu upload bukti (admin approve)
- **/ceksaldo** — Cek saldo aktif
- **/trial** — Dapat akun trial (3 hari, max 2x, reset tiap 3 hari)
- **/order** — Order akun (pilih tipe, protokol, UUID/password custom/random, otomatis generate akun via script)
- **/owner** — Menuju chat owner bot

### Panel Admin (`/panel`):
- Tambah/kurangi saldo user
- Lihat semua user & saldo
- Ubah harga/limit paket VPN
- Backup & restore data
- Fix cert VPN, restart service
- Statistik order & user aktif
- Notifikasi & approve topup user
- Unlimited pembuatan akun & trial
- Multi admin (owner bisa tambah admin baru)
- Cek user & hapus user (SSH, VMESS, VLESS, TROJAN)

---

## 🛠️ Dependensi

- Python 3.6+
- [python-telegram-bot==13.15](https://pypi.org/project/python-telegram-bot/13.15/)
- requests

Install otomatis dengan:
```sh
pip install -r requirements.txt
```

---

## 💡 Tips

- Pastikan semua script auto VPN (`create-ssh.py`, `create-vmess.py`, dst) **bisa dijalankan manual** (`python3 script.py ...`).
- Jika ingin dijalankan 24 jam di VPS: pakai `tmux`, `screen`, atau buat service systemd.
- File database user/saldo/order: `db.json` (jangan hapus).
- File QRIS (gambar): gunakan link raw GitHub sesuai nominal di `config.py`.

---

## 🤝 Credits & Lisensi

- Bot & sistem autoorder dikembangkan oleh [MikkuChan](https://github.com/MikkuChan)
- Script Python auto VPN: by MikkuChan
- Bebas dikembangkan untuk keperluan pribadi/komersial

---

## ❓ Bantuan / Tanya-Jawab

Jika ada error, request fitur, atau ingin konsultasi, silakan hubungi owner bot (via `/owner` di dalam bot) atau buka [issue](https://github.com/MikkuChan/telegram-bot-vpn/issues) di GitHub.

---