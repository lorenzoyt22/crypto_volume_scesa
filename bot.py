import ccxt
import os
import time
import json
import requests
from datetime import datetime, timezone, timedelta
from threading import Thread

# ===== CONFIG =====
TIMEFRAME = '5m'
GROWTH_THRESHOLD_UP = 0.04
GROWTH_THRESHOLD_DOWN = -0.02
CHECK_INTERVAL = 200  # secondi
EXCHANGE = ccxt.coinbase()
SYMBOLS = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'PEPE-USD', 'DOGE-USD', 'TRX-USD', 'CVX-USD']

# ===== TELEGRAM =====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ADMIN_USERNAME = "@TUO_NOME_UTENTE_ADMIN"  # modifica con il tuo username

# ===== FILE =====
ALERT_FILE = "alerts.json"
USERS_FILE = "users.json"

# ===== MEMORIE =====
alerts = {}
notified_events = {}
user_status = {}  # username -> {valid, expires, chat_id}

# ===== FUNZIONI UTILI =====
def fmt_price(p):
    p = float(p)
    if p >= 1:
        s = f"{p:.2f}"
    elif p >= 0.0001:
        s = f"{p:.6f}"
    else:
        s = f"{p:.8f}"
    return s.rstrip('0').rstrip('.') if '.' in s else s

def normalize_symbol_input(s):
    s = s.upper().strip().replace('/', '-')
    if '-' not in s:
        s += '-USD'
    return s

def load_json(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

def send_telegram_message(message, chat_id=None, keyboard=False):
    if chat_id is None:
        chat_id = TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    if keyboard:
        data["reply_markup"] = {
            "keyboard": [
                ["/price", "/alert"],
                ["/listalerts", "/removealert"]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
    try:
        requests.post(url, json=data, timeout=10)
    except Exception as e:
        print("Errore invio Telegram:", e)

# ===== UTENTI =====
def load_users():
    global user_status
    users = load_json(USERS_FILE)
    now = datetime.now(timezone.utc)
    for username, info in users.items():
        expires = datetime.fromisoformat(info["expires"])
        user_status[username] = {
            "valid": now <= expires,
            "expires": expires,
            "chat_id": info.get("chat_id")
        }

def check_user_valid(username):
    return username in user_status and user_status[username]["valid"]

def update_user_status():
    now = datetime.now(timezone.utc)
    changed = False
    for u, info in user_status.items():
        if info["valid"] and now > info["expires"]:
            info["valid"] = False
            changed = True
    if changed:
        users = {u: {"expires": info["expires"].isoformat(), "chat_id": info["chat_id"]} for u, info in user_status.items()}
        save_json(USERS_FILE, users)

# ===== ALERT =====
def load_alerts():
    global alerts
    alerts = load_json(ALERT_FILE)

def save_alerts():
    save_json(ALERT_FILE, alerts)

def check_and_notify():
    global notified_events
    now = datetime.now(timezone.utc)
    for symbol, alert_price in list(alerts.items()):
        try:
            ticker = EXCHANGE.fetch_ticker(symbol)
            current_price = ticker["last"]

            key = (symbol, "alert")
            if key not in notified_events and (
                (alert_price >= 0 and current_price >= alert_price) or
                (alert_price < 0 and current_price <= abs(alert_price))
            ):
                send_telegram_message(
                    f"✅🟢 *ALERT RAGGIUNTO* {symbol}\n"
                    f"⚠️ Alert: {fmt_price(alert_price)} USD\n"
                    f"💵 Prezzo: {fmt_price(current_price)} USD\n"
                    f"📊 Scarto: {fmt_price(current_price - alert_price)} USD\n"
                    f"🕒 {now.strftime('%Y-%m-%d %H:%M:%S')} UTC"
                )
                notified_events[key] = now
        except Exception as e:
            print(f"Errore fetch {symbol}: {e}")

# ===== COMANDI TELEGRAM =====
def process_message(username, chat_id, text):
    parts = text.strip().split()
    if not parts:
        return

    cmd = parts[0].lower()
    if cmd == "/help":
        send_telegram_message(
            f"❌ Abbonamento scaduto o non registrato.\nPer assistenza contattare {ADMIN_USERNAME}",
            chat_id=chat_id
        )
        return

    if not check_user_valid(username):
        send_telegram_message(
            f"❌ Abbonamento scaduto o non registrato.\nPer assistenza contattare {ADMIN_USERNAME}",
            chat_id=chat_id
        )
        return

    if cmd == "/price" and len(parts) >= 2:
        sym = normalize_symbol_input(parts[1])
        try:
            ticker = EXCHANGE.fetch_ticker(sym)
            price = ticker["last"]
            send_telegram_message(f"💰 *{sym}* prezzo attuale: {fmt_price(price)} USD", chat_id)
        except Exception as e:
            send_telegram_message(f"Errore ottenendo prezzo per {sym}: {e}", chat_id)

    elif cmd == "/alert" and len(parts) >= 3:
        sym = normalize_symbol_input(parts[1])
        try:
            price_val = float(parts[2])
            if sym not in SYMBOLS:
                send_telegram_message(f"❗ {sym} non è monitorata.", chat_id)
                return
            alerts[sym] = price_val
            save_alerts()
            send_telegram_message(f"✅🟢 Alert impostato: {sym} → {fmt_price(price_val)} USD ↗", chat_id)
        except Exception as e:
            send_telegram_message(f"Errore impostando alert: {e}", chat_id)

    elif cmd == "/removealert" and len(parts) >= 2:
        sym = normalize_symbol_input(parts[1])
        if sym in alerts:
            del alerts[sym]
            save_alerts()
            send_telegram_message(f"🗑️ Alert rimosso per {sym}", chat_id)
        else:
            send_telegram_message(f"❗ Nessun alert per {sym}", chat_id)

    elif cmd == "/listalerts":
        if not alerts:
            send_telegram_message("Nessun alert impostato.", chat_id)
        else:
            msg = "📋 Alert attivi:\n" + "\n".join(f"• {s}: {fmt_price(p)} USD" for s, p in alerts.items())
            send_telegram_message(msg, chat_id)

# ===== GET UPDATES =====
def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    try:
        res = requests.get(url, params=params, timeout=35)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print("Errore getUpdates:", e)
    return {}

# ===== MAIN LOOP =====
def telegram_polling():
    update_id = None
    while True:
        updates = get_updates(update_id)
        if "result" in updates:
            for item in updates["result"]:
                update_id = item["update_id"] + 1
                message = item.get("message", {})
                text = message.get("text", "")
                chat_id = message.get("chat", {}).get("id")
                username = message.get("from", {}).get("username", "")

                if text and username:
                    # memorizza chat_id dell'utente
                    if username in user_status:
                        user_status[username]["chat_id"] = chat_id
                    process_message(username, chat_id, text)
        time.sleep(1)

def price_checker():
    while True:
        check_and_notify()
        update_user_status()
        time.sleep(CHECK_INTERVAL)

# ===== AVVIO =====
if __name__ == "__main__":
    load_users()
    load_alerts()
    print("Bot avviato (senza notifiche volume)...")
    Thread(target=telegram_polling, daemon=True).start()
    price_checker()
