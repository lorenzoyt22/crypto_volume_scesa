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
SYMBOLS = ['AUCTION-USD', 'RLC-USD', 'TAIKO-USD', 'BAL-USD', 'POND-USD', 'CHILLGUY-USD', 'ABT-USD', 'AGLD-USD', 'NMR-USD', 'OCEAN-USD', 'CTSI-USD', 'AERGO-USD', 'MAGIC-USD', 
           'PRO-USD', 'DIA-USD', 'C98-USD', 'ACS-USD', 'CAT-USD', 'TAI-USD', 'CELR-USD', 'HFT-USD', 'TNSR-USD', 'GODS-USD', 'RARE-USD', 'FORT-USD', 'BOBA-USD', 'FWOG-USD', 'TOKEN-USD', 
           'STORJ-USD', 'TRU-USD', 'NCT-USD', 'OGN-USD', 'OXT-USD', 'MIGGLES-USD', 'RAD-USD', 'LOKA-USD', 'REZ-USD', 'PNG-USD', 'LMWR-USD', 'GTC-USD', 'CLV-USD', 'SD-USD', 'SWELL-USD', 
           'DYDX-USD', 'PYR-USD', 'WEN-USD', 'GME-USD', 'MLN-USD', 'GHST-USD', 'ARPA-USD', 'NKN-USD', 'BADGER-USD', 'ALCX-USD', 'IDEX-USD', 'ASM-USD', 'HOPR-USD', 'FARM-USD', 'MATH-USD', 
           'POLS-USD', 'BENJI-USD', 'RARI-USD', 'BLZ-USD', 'FIS-USD', 'SUKU-USD', 'VINU-USD', 'AVT-USD', 'VOXEL-USD', 'MDT-USD', 'AST-USD', 'FX-USD', 'GST-USD', 'BTRST-USD', 'HIGH-USD', 
           'PLA-USD', 'SHPING-USD', 'MKR-USD', 'BTC-USD', 'ETH-USD', 'XRP-USD', 'USDT-USD', 'BNB-USD', 'SOL-USD', 'USDC-USD', 'DOGE-USD', 'TRX-USD', 'ADA-USD', 'XLM-USD', 'SUI-USD', 'LINK-USD', 
           'HBAR-USD', 'BCH-USD', 'AVAX-USD', 'SHIB-USD', 'TON-USD', 'LTC-USD', 'DOT-USD', 'UNI-USD', 'PEPE-USD', 'AAVE-USD', 'CRO-USD', 'APT-USD', 'NEAR-USD', 'ICP-USD', 'ONDO-USD', 'ETC-USD', 
           'ALGO-USD', 'ENA-USD', 'ATOM-USD', 'VET-USD', 'POL-USD', 'ARB-USD', 'BONK-USD', 'RENDER-USD', 'TRUMP-USD', 'PENGU-USD', 'FET-USD', 'WLD-USD', 'SEI-USD', 'FIL-USD', 'QNT-USD', 'JUP-USD', 
           'SPX-USD', 'TIA-USD', 'INJ-USD', 'STX-USD', 'FLR-USD', 'OP-USD', 'IMX-USD', 'WIF-USD', 'GRT-USD', 'FLOKI-USD', 'CRV-USD', 'MSOL-USD', 'GALA-USD', 'JASMY-USD', 'MOG-USD', 'LDO-USD', 'ENS-USD', 
           'AERO-USD', 'PYTH-USD', 'XTZ-USD', 'JTO-USD', 'FLOW-USD', 'MANA-USD', 'MORPHO-USD', 'XCN-USD', 'HNT-USD', 'APE-USD', 'RLUSD-USD', 'STRK-USD', 'RSR-USD', 'KAVA-USD', 'EGLD-USD', '1INCH-USD', 
           'COMP-USD', 'AIOZ-USD', 'EIGEN-USD', 'AXS-USD', 'CHZ-USD', 'EOS-USD', 'WUSD-USD', 'KAITO-USD', 'AKT-USD', 'POPCAT-USD', 'WAXL-USD', 'SUPER-USD', 'MATIC-USD', 'CTC-USD', 'AMP-USD', 'ATH-USD', 
           'TURBO-USD', 'SAFE-USD', 'MEW-USD', 'LPT-USD', 'CVX-USD', 'DASH-USD', 'PNUT-USD', 'GLM-USD', 'MINA-USD', 'KSM-USD', 'ARKM-USD', 'ZRO-USD', 'BERA-USD', 'TOSHI-USD', 'SNX-USD', 'BAT-USD', 'ZRX-USD', 
           'BLUR-USD', 'ROSE-USD', 'IOTX-USD', 'NEIRO-USD', 'VTHO-USD', 'YFI-USD', 'CELO-USD', 'GIGA-USD', 'MOODENG-USD', 'COW-USD', 'TUSD-USD', 'TRAC-USD', 'ANKR-USD', 'WOO-USD', 'GMT-USD', 'IO-USD', 
           'SUSHI-USD', 'MASK-USD', 'PRIME-USD', 'XYO-USD', 'ZEN-USD', 'OSMO-USD', 'MELANIA-USD', 'RPL-USD', 'ME-USD', 'COTI-USD', 'SKL-USD', 'ILV-USD', 'BIGTIME-USD', 'METIS-USD', 'SWFTC-USD', 'REQ-USD', 
           'OMNI-USD', 'BAND-USD', 'ACH-USD', 'LQTY-USD', 'UMA-USD', 'BICO-USD', 'COOKIE-USD', 'LRC-USD', 'DEGEN-USD', 'POWR-USD', 'HONEY-USD', 'API3-USD', 'PUNDIX-USD', 'KNC-USD', 'AUDIO-USD', 'SPELL-USD', 
           'ACX-USD', 'CVC-USD', 'FIDA-USD', 'PONKE-USD', 'BNT-USD']

# ===== TELEGRAM =====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ADMIN_USERNAME = "@TUO_NOME_UTENTE_ADMIN"  # modifica con il tuo username

# ===== FILE =====
ALERT_FILE = "alerts.json"
USERS_FILE = "users.json"

# ===== MEMORIE =====
alerts = {}
notified_events = {}  # {(symbol, tipo): datetime_ultimo_alert}
user_status = {}      # username -> {valid, expires, chat_id}

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

def can_notify(key):
    """Evita notifiche duplicate entro 12 ore"""
    now = datetime.now(timezone.utc)
    last = notified_events.get(key)
    if last and (now - last) < timedelta(hours=12):
        return False
    return True

def check_and_notify():
    global notified_events
    now = datetime.now(timezone.utc)

    for symbol in SYMBOLS:
        try:
            ohlcv = EXCHANGE.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=2)
            if len(ohlcv) < 2:
                continue
            prev_close, last_close = float(ohlcv[-2][4]), float(ohlcv[-1][4])
            price_change = (last_close - prev_close) / prev_close

            # Notifica rialzo
            if price_change >= GROWTH_THRESHOLD_UP and can_notify((symbol, "up")):
                msg = f"🟢 *{symbol} +{price_change*100:.2f}% in 5 min*\n💵 {fmt_price(prev_close)} → {fmt_price(last_close)} USD\n🕒 {now.strftime('%Y-%m-%d %H:%M:%S')} UTC"
                send_telegram_message(msg)
                notified_events[(symbol, "up")] = now

            # Notifica ribasso
            if price_change <= GROWTH_THRESHOLD_DOWN and can_notify((symbol, "down")):
                msg = f"🔴 *{symbol} {price_change*100:.2f}% in 5 min*\n💵 {fmt_price(prev_close)} → {fmt_price(last_close)} USD\n🕒 {now.strftime('%Y-%m-%d %H:%M:%S')} UTC"
                send_telegram_message(msg)
                notified_events[(symbol, "down")] = now

            # Alert manuale impostato dall'utente
            for sym, alert_price in list(alerts.items()):
                key = (sym, "alert")
                if key not in notified_events:
                    if (alert_price >= 0 and last_close >= alert_price) or (alert_price < 0 and last_close <= abs(alert_price)):
                        msg = f"✅🟢 *ALERT RAGGIUNTO* {sym}\n⚠️ Alert: {fmt_price(alert_price)} USD\n💵 Prezzo: {fmt_price(last_close)} USD\n📊 Scarto: {fmt_price(last_close - alert_price)} USD\n🕒 {now.strftime('%Y-%m-%d %H:%M:%S')} UTC"
                        send_telegram_message(msg)
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
        send_telegram_message(f"❌ Abbonamento scaduto o non registrato.\nPer assistenza contattare {ADMIN_USERNAME}", chat_id)
        return

    if not check_user_valid(username):
        send_telegram_message(f"❌ Abbonamento scaduto o non registrato.\nPer assistenza contattare {ADMIN_USERNAME}", chat_id)
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
            send_telegram_message(f"✅ Alert impostato: {sym} → {fmt_price(price_val)} USD", chat_id)
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

# ===== POLLING TELEGRAM =====
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
                    if username in user_status:
                        user_status[username]["chat_id"] = chat_id
                    process_message(username, chat_id, text)
        time.sleep(1)

# ===== LOOP PRINCIPALE =====
def main_loop():
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
    main_loop()
