import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from config import BOT_TOKEN, OWNER_ID, DEFAULT_PRICING, QRIS
import db
import vpn_utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = user.id
    if not db.get_user(user_id):
        db.set_user(user_id, {"saldo": 0, "role": "user", "trial_used": 0, "trial_time": 0})
    keyboard = [
        [InlineKeyboardButton("Daftar", callback_data="daftar")],
        [InlineKeyboardButton("Cek Harga", callback_data="cekharga")],
        [InlineKeyboardButton("Topup", callback_data="topup")],
        [InlineKeyboardButton("Cek Saldo", callback_data="ceksaldo")],
        [InlineKeyboardButton("Trial", callback_data="trial")],
        [InlineKeyboardButton("Order", callback_data="order")],
        [InlineKeyboardButton("Owner", url=f"https://t.me/{OWNER_ID}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Selamat datang di Bot Autoorder VPN!", reply_markup=reply_markup)

def menu_button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    data = query.data
    if data == "daftar":
        query.edit_message_text("Kamu sudah terdaftar otomatis!")
    elif data == "cekharga":
        harga = db.get_settings().get("pricing", DEFAULT_PRICING)
        msg = "Harga VPN:\n"
        for tipe, v in harga.items():
            msg += f"- {tipe}: Rp{v['harga']:,} (limit IP: {v['limit_ip']}, limit data: {v['limit_data']}GB, {v['masa_aktif']} hari)\n"
        query.edit_message_text(msg)
    elif data == "ceksaldo":
        user = db.get_user(user_id)
        saldo = user.get("saldo", 0)
        query.edit_message_text(f"Saldo kamu: Rp{saldo:,}")
    elif data == "topup":
        keyboard = [
            [InlineKeyboardButton("25.000", callback_data="topup25000")],
            [InlineKeyboardButton("50.000", callback_data="topup50000")],
            [InlineKeyboardButton("100.000", callback_data="topup100000")],
            [InlineKeyboardButton("Batal", callback_data="batal")]
        ]
        query.edit_message_text("Pilih nominal topup:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif data.startswith("topup"):
        nominal = data.replace("topup", "")
        qris_url = QRIS[nominal]
        context.user_data["topup_nominal"] = nominal
        query.edit_message_text(f"Silakan scan QRIS di bawah, lalu upload bukti transfer.\nNominal: Rp{nominal}")
        context.bot.send_photo(chat_id=user_id, photo=qris_url)
        context.user_data["awaiting_topup"] = True
    elif data == "trial":
        from time import time
        user = db.get_user(user_id)
        if user["trial_used"] >= 2 and (time() - user["trial_time"]) < 3*24*3600:
            query.edit_message_text("Kuota trial kamu habis, coba lagi setelah 3 hari.")
        else:
            msg = vpn_utils.create_account("HP", "vmess", "random", "UUID_RANDOM", DEFAULT_PRICING["HP"], user_id)
            user["trial_used"] = user.get("trial_used", 0) + 1
            user["trial_time"] = time()
            db.set_user(user_id, user)
            query.edit_message_text("Akun trial berhasil dibuat:\n"+msg)
    elif data == "order":
        keyboard = [
            [InlineKeyboardButton("HP", callback_data="order_HP")],
            [InlineKeyboardButton("Openwrt", callback_data="order_Openwrt")],
            [InlineKeyboardButton("Batal", callback_data="batal")]
        ]
        query.edit_message_text("Pilih tipe:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif data.startswith("order_"):
        tipe = data.replace("order_", "")
        context.user_data["order_tipe"] = tipe
        keyboard = [
            [InlineKeyboardButton("Trojan", callback_data="proto_trojan")],
            [InlineKeyboardButton("VLESS", callback_data="proto_vless")],
            [InlineKeyboardButton("VMESS", callback_data="proto_vmess")],
            [InlineKeyboardButton("SSH", callback_data="proto_ssh")],
            [InlineKeyboardButton("Batal", callback_data="batal")]
        ]
        query.edit_message_text("Pilih protokol:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif data.startswith("proto_"):
        proto = data.replace("proto_", "")
        context.user_data["order_proto"] = proto
        if proto in ["vmess", "vless", "trojan"]:
            keyboard = [
                [InlineKeyboardButton("UUID Custom", callback_data="uuid_custom")],
                [InlineKeyboardButton("UUID Random", callback_data="uuid_random")],
                [InlineKeyboardButton("Batal", callback_data="batal")]
            ]
            query.edit_message_text("Pilih UUID:", reply_markup=InlineKeyboardMarkup(keyboard))
        elif proto == "ssh":
            keyboard = [
                [InlineKeyboardButton("Password Custom", callback_data="pass_custom")],
                [InlineKeyboardButton("Password Random", callback_data="pass_random")],
                [InlineKeyboardButton("Batal", callback_data="batal")]
            ]
            query.edit_message_text("Pilih password:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == "uuid_custom":
        query.edit_message_text("Silakan masukkan UUID custom:")
        context.user_data["awaiting_uuid"] = True
    elif data == "uuid_random":
        tipe = context.user_data["order_tipe"]
        proto = context.user_data["order_proto"]
        paket = db.get_settings().get("pricing", DEFAULT_PRICING)[tipe]
        user = db.get_user(user_id)
        if user["saldo"] < paket["harga"]:
            query.edit_message_text(f"Saldo tidak cukup (Rp{paket['harga']:,})")
            return
        user["saldo"] -= paket["harga"]
        db.set_user(user_id, user)
        msg = vpn_utils.create_account(tipe, proto, "random", vpn_utils.generate_uuid(), paket, user_id)
        query.edit_message_text("Order sukses:\n"+msg)
    elif data == "pass_custom":
        query.edit_message_text("Silakan masukkan password custom:")
        context.user_data["awaiting_pass"] = True
    elif data == "pass_random":
        tipe = context.user_data["order_tipe"]
        proto = context.user_data["order_proto"]
        paket = db.get_settings().get("pricing", DEFAULT_PRICING)[tipe]
        user = db.get_user(user_id)
        if user["saldo"] < paket["harga"]:
            query.edit_message_text(f"Saldo tidak cukup (Rp{paket['harga']:,})")
            return
        user["saldo"] -= paket["harga"]
        db.set_user(user_id, user)
        msg = vpn_utils.create_account(tipe, proto, "random", "", paket, user_id)
        query.edit_message_text("Order sukses:\n"+msg)
    elif data == "batal":
        query.edit_message_text("Dibatalkan.")

def process_user_input(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    text = update.message.text
    if context.user_data.get("awaiting_uuid"):
        tipe = context.user_data["order_tipe"]
        proto = context.user_data["order_proto"]
        uuid_val = text.strip()
        paket = db.get_settings().get("pricing", DEFAULT_PRICING)[tipe]
        user = db.get_user(user_id)
        if user["saldo"] < paket["harga"]:
            update.message.reply_text(f"Saldo tidak cukup (Rp{paket['harga']:,})")
            return
        user["saldo"] -= paket["harga"]
        db.set_user(user_id, user)
        msg = vpn_utils.create_account(tipe, proto, "custom", uuid_val, paket, user_id)
        update.message.reply_text("Order sukses:\n"+msg)
        context.user_data["awaiting_uuid"] = False
    elif context.user_data.get("awaiting_pass"):
        tipe = context.user_data["order_tipe"]
        proto = context.user_data["order_proto"]
        passwd = text.strip()
        paket = db.get_settings().get("pricing", DEFAULT_PRICING)[tipe]
        user = db.get_user(user_id)
        if user["saldo"] < paket["harga"]:
            update.message.reply_text(f"Saldo tidak cukup (Rp{paket['harga']:,})")
            return
        user["saldo"] -= paket["harga"]
        db.set_user(user_id, user)
        msg = vpn_utils.create_account(tipe, proto, "custom", passwd, paket, user_id)
        update.message.reply_text("Order sukses:\n"+msg)
        context.user_data["awaiting_pass"] = False
    elif context.user_data.get("awaiting_topup"):
        photo = update.message.photo[-1].file_id if update.message.photo else None
        nominal = context.user_data.get("topup_nominal")
        db.add_topup({"user_id": user_id, "file_id": photo, "nominal": nominal, "status": "pending"})
        admins = db.load_db()["admins"]
        for admin in admins:
            context.bot.send_message(admin, f"Topup baru dari {user_id}\nNominal: {nominal}")
            if photo:
                context.bot.send_photo(admin, photo=photo)
            keyboard = [
                [InlineKeyboardButton("Approve", callback_data=f"approve_{user_id}_{nominal}"),
                 InlineKeyboardButton("Tolak", callback_data=f"tolak_{user_id}_{nominal}")]
            ]
            context.bot.send_message(admin, "Approve topup?", reply_markup=InlineKeyboardMarkup(keyboard))
        update.message.reply_text("Bukti topup dikirim, tunggu konfirmasi admin.")
        context.user_data["awaiting_topup"] = False

def panel(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if not (user_id == OWNER_ID or db.is_admin(user_id)):
        return update.message.reply_text("Kamu bukan admin.")
    keyboard = [
        [InlineKeyboardButton("Tambah/Kurangi Saldo", callback_data="admin_saldo")],
        [InlineKeyboardButton("Lihat Semua User", callback_data="admin_lihatuser")],
        [InlineKeyboardButton("Ubah Harga", callback_data="admin_harga")],
        [InlineKeyboardButton("Backup & Restore", callback_data="admin_backup")],
        [InlineKeyboardButton("Fixcert/Restart", callback_data="admin_fixcert")],
        [InlineKeyboardButton("Statistik", callback_data="admin_stats")],
        [InlineKeyboardButton("Tambah Admin", callback_data="admin_addadmin")],
        [InlineKeyboardButton("Cek User", callback_data="admin_cekuser")],
        [InlineKeyboardButton("Delete User", callback_data="admin_deluser")],
        [InlineKeyboardButton("Kembali", callback_data="batal")]
    ]
    update.message.reply_text("Panel Admin:", reply_markup=InlineKeyboardMarkup(keyboard))

def admin_button(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    if not (user_id == OWNER_ID or db.is_admin(user_id)):
        query.answer("Bukan admin!", show_alert=True)
        return
    data = query.data
    if data == "admin_saldo":
        query.edit_message_text("Kirim format: saldo userid nominal (+/-). Contoh: saldo 123456 10000 atau saldo 123456 -5000")
        context.user_data["awaiting_admin_saldo"] = True
    elif data == "admin_lihatuser":
        dbu = db.load_db()["users"]
        msg = "User:\n"
        for uid, u in dbu.items():
            msg += f"{uid}: Saldo Rp{u.get('saldo',0):,}, Role: {u.get('role','user')}\n"
        query.edit_message_text(msg)
    elif data == "admin_harga":
        query.edit_message_text("Kirim format: harga HP 12000 atau harga Openwrt 17000")
        context.user_data["awaiting_admin_harga"] = True
    elif data == "admin_backup":
        msg = vpn_utils.backup()
        query.edit_message_text("Backup:\n"+msg)
    elif data == "admin_fixcert":
        msg = vpn_utils.fixcertvpn() + "\n" + vpn_utils.restart_service()
        query.edit_message_text("Fixcert & restart:\n"+msg)
    elif data == "admin_stats":
        orders = db.get_orders()
        users = db.load_db()["users"]
        msg = f"Statistik:\nOrder: {len(orders)}\nUser aktif: {len(users)}"
        query.edit_message_text(msg)
    elif data == "admin_addadmin":
        query.edit_message_text("Kirim format: addadmin USERID")
        context.user_data["awaiting_admin_addadmin"] = True
    elif data == "admin_cekuser":
        keyboard = [
            [InlineKeyboardButton("SSH", callback_data="cekuser_ssh")],
            [InlineKeyboardButton("VMESS", callback_data="cekuser_vmess")],
            [InlineKeyboardButton("VLESS", callback_data="cekuser_vless")],
            [InlineKeyboardButton("TROJAN", callback_data="cekuser_trojan")],
            [InlineKeyboardButton("Batal", callback_data="batal")]
        ]
        query.edit_message_text("Pilih protokol cek user:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif data.startswith("cekuser_"):
        proto = data.replace("cekuser_", "")
        msg = vpn_utils.cek_user(proto)
        query.edit_message_text(msg)
    elif data == "admin_deluser":
        query.edit_message_text("Format: deluser protokol username (contoh: deluser vmess user123)")
        context.user_data["awaiting_admin_deluser"] = True
    elif data == "batal":
        query.edit_message_text("Dibatalkan.")

def process_admin_input(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    text = update.message.text
    if context.user_data.get("awaiting_admin_saldo"):
        try:
            _, uid, nominal = text.split()
            uid = int(uid)
            nominal = int(nominal)
            user = db.get_user(uid) or {}
            user["saldo"] = user.get("saldo", 0) + nominal
            db.set_user(uid, user)
            update.message.reply_text(f"Sukses update saldo user {uid}: Rp{user['saldo']:,}")
        except Exception as e:
            update.message.reply_text(f"Format salah. {e}")
        context.user_data["awaiting_admin_saldo"] = False
    elif context.user_data.get("awaiting_admin_harga"):
        try:
            _, tipe, nominal = text.split()
            settings = db.get_settings()
            if "pricing" not in settings:
                settings["pricing"] = DEFAULT_PRICING.copy()
            settings["pricing"][tipe]["harga"] = int(nominal)
            db.update_settings(settings)
            update.message.reply_text(f"Harga {tipe} diubah jadi Rp{nominal}")
        except Exception as e:
            update.message.reply_text(f"Format salah. {e}")
        context.user_data["awaiting_admin_harga"] = False
    elif context.user_data.get("awaiting_admin_addadmin"):
        try:
            _, uid = text.split()
            uid = int(uid)
            db.add_admin(uid)
            update.message.reply_text(f"User {uid} ditambahkan jadi admin.")
        except Exception as e:
            update.message.reply_text(f"Format salah. {e}")
        context.user_data["awaiting_admin_addadmin"] = False
    elif context.user_data.get("awaiting_admin_deluser"):
        try:
            _, proto, username = text.split()
            result = vpn_utils.del_user(proto, username)
            update.message.reply_text(result)
        except Exception as e:
            update.message.reply_text(f"Format salah. {e}")
        context.user_data["awaiting_admin_deluser"] = False

def approve_topup(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    if not (query.from_user.id == OWNER_ID or db.is_admin(query.from_user.id)):
        query.answer("Bukan admin!", show_alert=True)
        return
    if data.startswith("approve_"):
        _, uid, nominal = data.split("_")
        user = db.get_user(uid)
        user["saldo"] = user.get("saldo", 0) + int(nominal)
        db.set_user(uid, user)
        query.edit_message_text(f"Topup user {uid} Rp{nominal} diapprove.")
        context.bot.send_message(uid, f"Topup kamu Rp{nominal} sudah masuk.")
    elif data.startswith("tolak_"):
        _, uid, nominal = data.split("_")
        query.edit_message_text(f"Topup user {uid} Rp{nominal} ditolak.")
        context.bot.send_message(uid, f"Topup kamu Rp{nominal} ditolak.")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("panel", panel))
    dp.add_handler(CallbackQueryHandler(menu_button, pattern="^(daftar|cekharga|topup|ceksaldo|trial|order|order_.*|proto_.*|uuid_custom|uuid_random|pass_custom|pass_random|batal)$"))
    dp.add_handler(CallbackQueryHandler(admin_button, pattern="^admin_.*|batal$"))
    dp.add_handler(CallbackQueryHandler(approve_topup, pattern="^(approve_|tolak_).*"))
    dp.add_handler(MessageHandler(Filters.text & (~Filters.command), process_user_input))
    dp.add_handler(MessageHandler(Filters.text & (~Filters.command), process_admin_input))
    dp.add_handler(MessageHandler(Filters.photo, process_user_input))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()