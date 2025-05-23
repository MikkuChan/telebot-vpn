BOT_TOKEN = "7923489458:AAHYRKCmySlxbXgtbBaUlk7wgujYhBHG6aw"
OWNER_ID = 6243379861  # ganti dengan ID Telegram owner bot

# Default harga & limit
DEFAULT_PRICING = {
    "HP": {
        "harga": 10000,
        "limit_ip": 10,
        "limit_data": 500,
        "masa_aktif": 30
    },
    "Openwrt": {
        "harga": 15000,
        "limit_ip": 20,
        "limit_data": 700,
        "masa_aktif": 30
    }
}

# QRIS URL
QRIS = {
    "25000": "https://raw.githubusercontent.com/MikkuChan/payments/main/qr25K.png",
    "50000": "https://raw.githubusercontent.com/MikkuChan/payments/main/qr50K.png",
    "100000": "https://raw.githubusercontent.com/MikkuChan/payments/main/qr100K.png"
}