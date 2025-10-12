import ccxt
import os
import time
import requests
import json
from datetime import datetime, timedelta, timezone

# CONFIG
GROWTH_THRESHOLD_UP = 0.04    # +4%
GROWTH_THRESHOLD_DOWN = -0.02 # -2%
TIMEFRAME = '5m'
EXCHANGE = ccxt.coinbase()
SYMBOLS = [
    'BTC-USD', 'ETH-USD', 'SOL-USD', 'PEPE-USD', 'DOGE-USD', 'TRX-USD', 'CVX-USD'
]

# TELEGRAM CONFIG da variabili d'ambiente
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Persistenza alerts e offset
ALERTS_FILE = "alerts.json"
TG_OFFSET_FILE = "tg_offset.txt"

# Memoria notifiche inviate: { (symbol, tipo_evento) : datetime_ultimo_invio }
notified_events = {}

def load_alerts():
    if os.path.exists(ALERTS_FILE):
        with open(ALERTS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_alerts(alerts):
    with open(ALERTS_FILE, "w") as f:
        json.dump(alerts, f)

alerts = load_alerts()

def read_tg_offset():
    if os.path.exists(TG_OFFSET_FILE):
        with open(TG_OFFSET_FILE, "r") as f:
            try:
                return int(f.read().strip())
            except:
                return None
    return None

def write_tg_offset(offset):
    with open(TG_OFFSET_FILE, "w") as f:
        f.write(str(offset))

def send_telegram_message(message):
    url = f"{TELEGRAM_API}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        resp = requests.post(url, data=data, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"Errore invio Telegram: {e}")

def can_notify(key, hours=12):
    dt = notified_events.get(key)
    if dt is None:
        return True
    return (datetime.now(timezone.utc) - dt) > timedelta(hours=hours)

def fetch_price(symbol):
    sym = symbol.replace('-', '/')
    try:
        ticker = EXCHANGE.fetch_ticker(sym)
        return float(ticker.get('last') or ticker.get('close') or 0.0)
    except Exception:
        ohlcv = EXCHANGE.fetch_ohlcv(sym, timeframe=TIMEFRAME, limit=1)
        if ohlcv:
            return float(ohlcv[-1][4])
        raise

def handle_telegram_commands():
    offset = read_tg_offset()
    params = {"timeout": 10}
    if offset:
        params["offset"] = offset
    try:
        resp = requests.get(f"{TELEGRAM_API}/getUpdates", params=params, timeout=15)
        resp.raise_for_status()
        updates = resp.json().get("result", [])
        for u in updates:
            update_id = u["update_id"]
            if update_id is not None:
                write_tg_offset(update_id + 1)
            msg = u.get("message") or u.get("edited_message")
            if not msg:
                continue
            text = msg.get("text", "").strip()
            if not text:
                continue
            parts = text.split()
            cmd = parts[0].lower()

            if cmd == "/price" and len(parts) >= 2:
                sym = parts[1].upper().replace('/', '-')
                try:
                    price = fetch_price(sym)
                    send_telegram_message(f"*{sym}* prezzo attuale: {price:.6f} USD")
                except Exception as e:
                    send_telegram_message(f"Errore fetching price {sym}: {e}")

            elif cmd == "/alert" and len(parts) >= 3:
                sym = parts[1].upper().replace('/', '-')
                try:
                    price_val = float(parts[2])
                    alerts[sym] = price_val
                    save_alerts(alerts)
                    send_telegram_message(f"Alert impostato: *{sym}* → {price_val:.6f} USD")
                except Exception as e:
                    send_telegram_message(f"Errore impostando alert: {e}")

            elif cmd == "/removealert" and len(parts) >= 2:
                sym = parts[1].upper().replace('/', '-')
                if sym in alerts:
                    del alerts[sym]
                    save_alerts(alerts)
                    send_telegram_message(f"Alert rimosso: *{sym}*")
                else:
                    send_telegram_message(f"Nessun alert trovato per *{sym}*")

            elif cmd == "/listalerts":
                if not alerts:
                    send_telegram_message("Nessun alert impostato.")
                else:
                    lines = [f"*{s}*: {p:.6f} USD" for s, p in alerts.items()]
                    send_telegram_message("Alert impostati:\n" + "\n".join(lines))

            else:
                help_msg = (
                    "Comandi:\n"
                    "/price SYMBOL\n"
                    "/alert SYMBOL PRICE\n"
                    "/removealert SYMBOL\n"
                    "/listalerts"
                )
                send_telegram_message(help_msg)
    except Exception as e:
        print(f"Errore handle_telegram_commands: {e}")

def check_and_notify():
    global notified_events, alerts
    now = datetime.now(timezone.utc)
    for symbol in SYMBOLS:
        try:
            sym = symbol.replace('-', '/')
            ohlcv = EXCHANGE.fetch_ohlcv(sym, timeframe=TIMEFRAME, limit=2)
            if len(ohlcv) < 2:
                continue
            last = ohlcv[-1]
            prev = ohlcv[-2]
            last_close = float(last[4])
            prev_close = float(prev[4])
            price_change = (last_close - prev_close) / prev_close if prev_close != 0 else 0.0
            price_diff_pct = price_change * 100.0

            alert_info = ""
            if symbol in alerts:
                alert_price = float(alerts[symbol])
                diff = last_close - alert_price
                diff_pct = (diff / alert_price * 100.0) if alert_price != 0 else 0.0
                sign = "+" if diff >= 0 else "-"
                alert_info = (
                    f"\n\n⚠️ *Alert impostato:* {alert_price:.6f} USD\n"
                    f"   *Scarto:* {sign}{abs(diff):.6f} USD ({sign}{abs(diff_pct):.2f}%)"
                )

            if price_change >= GROWTH_THRESHOLD_UP:
                key = (symbol, 'price_up')
                if can_notify(key):
                    msg = (
                        f"🟢📈 *{symbol} è salita del +{price_diff_pct:.2f}% in 5 minuti*\n"
                        f"💵 *Prezzo:* {prev_close:.6f} → {last_close:.6f} USD\n"
                        f"📊 *Differenza prezzo:* +{price_diff_pct:.2f}%\n"
                        f"🕒 *Orario:* {now.strftime('%Y-%m-%d %H:%M:%S')} UTC"
                        + alert_info
                    )
                    send_telegram_message(msg)
                    notified_events[key] = now

            if price_change <= GROWTH_THRESHOLD_DOWN:
                key = (symbol, 'price_down')
                if can_notify(key):
                    msg = (
                        f"🔴📉 *{symbol} è scesa del -{abs(price_diff_pct):.2f}% in 5 minuti*\n"
                        f"💵 *Prezzo:* {prev_close:.6f} → {last_close:.6f} USD\n"
                        f"📊 *Differenza prezzo:* -{abs(price_diff_pct):.2f}%\n"
                        f"🕒 *Orario:* {now.strftime('%Y-%m-%d %H:%M:%S')} UTC"
                        + alert_info
                    )
                    send_telegram_message(msg)
                    notified_events[key] = now

        except Exception as e:
            print(f"Errore con {symbol}: {e}")

def clean_memory():
    now = datetime.now(timezone.utc)
    to_delete = [key for key, dt in notified_events.items() if (now - dt) > timedelta(hours=12)]
    for key in to_delete:
        del notified_events[key]

if __name__ == "__main__":
    print("Bot crypto monitor avviato...")
    while True:
        try:
            handle_telegram_commands()
            check_and_notify()
            clean_memory()
        except Exception as e:
            print(f"Errore main loop: {e}")
        time.sleep(240)
