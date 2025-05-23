import json
from threading import Lock

DB_FILE = "db.json"
db_lock = Lock()

def load_db():
    try:
        with db_lock, open(DB_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"users": {}, "orders": [], "admins": [], "settings": {}, "topups": []}

def save_db(data):
    with db_lock, open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Helper: get/set user, saldo, admin, dsb
def get_user(user_id):
    db = load_db()
    return db["users"].get(str(user_id))

def set_user(user_id, user_data):
    db = load_db()
    db["users"][str(user_id)] = user_data
    save_db(db)

def add_admin(user_id):
    db = load_db()
    if user_id not in db["admins"]:
        db["admins"].append(user_id)
        save_db(db)

def is_admin(user_id):
    db = load_db()
    return user_id in db["admins"]

def add_order(order):
    db = load_db()
    db["orders"].append(order)
    save_db(db)

def get_orders():
    db = load_db()
    return db["orders"]

def update_settings(settings):
    db = load_db()
    db["settings"] = settings
    save_db(db)

def get_settings():
    db = load_db()
    return db.get("settings", {})

def add_topup(topup):
    db = load_db()
    db["topups"].append(topup)
    save_db(db)

def update_user(user_id, key, value):
    db = load_db()
    user = db["users"].setdefault(str(user_id), {})
    user[key] = value
    save_db(db)