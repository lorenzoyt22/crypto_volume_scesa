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

# Memoria notifiche inviate: { (symbol, tipo_evento, extra) : datetime_ultimo_invio }
notified_events = {}

# Range alert
MIN_ALERT_PRICE = 1e-8
MAX_ALERT_PRICE = 1e12

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

def normalize_symbol_input(s):
    s = s.upper().strip().replace('/', '-')
    if '-' not in s:
        s = s + '-USD'
    return s

def fmt_price(p):
    p = float(p)
    if p >= 1:
        s = f"{p:.2f}"
    elif p >= 0.0001:
        s = f"{p:.6f}"
    else:
        s = f"{p:.8f}"
    return s.rstrip('0').rstrip('.')

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

            # /price SYMBOL   -> accept BTC / BTC-USD / BTC/USD
            if cmd == "/price" and len(parts) >= 2:
                sym_input = normalize_symbol_input(parts[1])
                try:
                    price = fetch_price(sym_input)
                    send_telegram_message(f"*{sym_input}* prezzo attuale: {fmt_price(price)} USD")
                except Exception as e:
                    send_telegram_message(f"Errore fetching price {sym_input}: {e}")

            # /alert SYMBOL PRICE  -> accept single symbol; only allow if in SYMBOLS
            elif cmd == "/alert" and len(parts) >= 3:
                sym_input = normalize_symbol_input(parts[1])
                try:
                    price_val = float(parts[2])
                    if not (MIN_ALERT_PRICE <= price_val <= MAX_ALERT_PRICE):
                        send_telegram_message(f"❗ Valore alert non valido. Range: {MIN_ALERT_PRICE} - {MAX_ALERT_PRICE}")
                        continue
                    if sym_input not in SYMBOLS:
                        send_telegram_message(f"❗ {sym_input} non è monitorato. Aggiungilo a SYMBOLS se vuoi.")
                        continue
                    alerts[sym_input] = price_val
                    save_alerts(alerts)
                    send_telegram_message(f"✅🟢 *Alert impostato:* {sym_input} → {fmt_price(price_val)} USD  ↗")
                except Exception as e:
                    send_telegram_message(f"Errore impostando alert: {e}")

            # /removealert SYMBOL
            elif cmd == "/removealert" and len(parts) >= 2:
                sym_input = normalize_symbol_input(parts[1])
                if sym_input in alerts:
                    del alerts[sym_input]
                    save_alerts(alerts)
                    send_telegram_message(f"🗑️ *Alert rimosso:* {sym_input}")
                    # rimuovo eventuali notifiche pregresse per quell'alert
                    to_del = [k for k in notified_events.keys() if k[0] == sym_input and k[1].startswith('alert_')]
                    for k in to_del:
                        notified_events.pop(k, None)
                else:
                    send_telegram_message(f"Nessun alert trovato per *{sym_input}*")

            # /listalerts
            elif cmd == "/listalerts":
                if not alerts:
                    send_telegram_message("Nessun alert impostato.")
                else:
                    lines = [f"*{s}*: {fmt_price(p)} USD" for s, p in alerts.items()]
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
            sym_ccxt = symbol.replace('-', '/')
            ohlcv = EXCHANGE.fetch_ohlcv(sym_ccxt, timeframe=TIMEFRAME, limit=2)
            if len(ohlcv) < 2:
                continue
            last = ohlcv[-1]
            prev = ohlcv[-2]
            last_close = float(last[4])
            prev_close = float(prev[4])
            price_change = (last_close - prev_close) / prev_close if prev_close != 0 else 0.0
            price_diff_pct = price_change * 100.0

            # 0) alert raggiunto rispetto al price impostato (trigger immediato)
            if symbol in alerts:
                alert_price = float(alerts[symbol])
                # crossing upward
                if last_close >= alert_price and prev_close < alert_price:
                    key = (symbol, f"alert_hit_{alert_price}")
                    if can_notify(key):
                        diff = last_close - alert_price
                        diff_pct = (diff / alert_price * 100.0) if alert_price != 0 else 0.0
                        msg = (
                            f"✅🟢 *ALERT RAGGIUNTO* {symbol}\n"
                            f"⚠️ *Alert impostato:* {fmt_price(alert_price)} USD\n"
                            f"💵 *Prezzo:* {fmt_price(prev_close)} → {fmt_price(last_close)} USD\n"
                            f"   *Scarto:* +{fmt_price(diff)} USD (+{diff_pct:.2f}%)\n"
                            f"🕒 *Orario:* {now.strftime('%Y-%m-%d %H:%M:%S')} UTC"
                        )
                        send_telegram_message(msg)
                        notified_events[key] = now
                # crossing downward (se vuoi notificare anche caduta sotto alert)
                elif last_close <= alert_price and prev_close > alert_price:
                    key = (symbol, f"alert_hit_{alert_price}")
                    if can_notify(key):
                        diff = last_close - alert_price
                        diff_pct = (diff / alert_price * 100.0) if alert_price != 0 else 0.0
                        msg = (
                            f"🔔🔻 *ALERT RAGGIUNTO (sotto)* {symbol}\n"
                            f"⚠️ *Alert impostato:* {fmt_price(alert_price)} USD\n"
                            f"💵 *Prezzo:* {fmt_price(prev_close)} → {fmt_price(last_close)} USD\n"
                            f"   *Scarto:* {fmt_price(diff)} USD ({diff_pct:.2f}%)\n"
                            f"🕒 *Orario:* {now.strftime('%Y-%m-%d %H:%M:%S')} UTC"
                        )
                        send_telegram_message(msg)
                        notified_events[key] = now

            # 1) salita prezzo > soglia
            if price_change >= GROWTH_THRESHOLD_UP:
                key = (symbol, 'price_up')
                if can_notify(key):
                    alert_info = ""
                    if symbol in alerts:
                        alert_price = float(alerts[symbol])
                        diff = last_close - alert_price
                        diff_pct = (diff / alert_price * 100.0) if alert_price != 0 else 0.0
                        sign = "+" if diff >= 0 else "-"
                        alert_info = (
                            f"\n\n⚠️ *Alert impostato:* {fmt_price(alert_price)} USD\n"
                            f"   *Scarto:* {sign}{fmt_price(abs(diff))} USD ({sign}{abs(diff_pct):.2f}%)"
                        )
                    msg = (
                        f"🟢📈 *{symbol} è salita del +{price_diff_pct:.2f}% in 5 minuti*\n"
                        f"💵 *Prezzo:* {fmt_price(prev_close)} → {fmt_price(last_close)} USD\n"
                        f"📊 *Differenza prezzo:* +{price_diff_pct:.2f}%\n"
                        f"🕒 *Orario:* {now.strftime('%Y-%m-%d %H:%M:%S')} UTC"
                        + alert_info
                    )
                    send_telegram_message(msg)
                    notified_events[key] = now

            # 2) discesa prezzo <= soglia
            if price_change <= GROWTH_THRESHOLD_DOWN:
                key = (symbol, 'price_down')
                if can_notify(key):
                    alert_info = ""
                    if symbol in alerts:
                        alert_price = float(alerts[symbol])
                        diff = last_close - alert_price
                        diff_pct = (diff / alert_price * 100.0) if alert_price != 0 else 0.0
                        sign = "+" if diff >= 0 else "-"
                        alert_info = (
                            f"\n\n⚠️ *Alert impostato:* {fmt_price(alert_price)} USD\n"
                            f"   *Scarto:* {sign}{fmt_price(abs(diff))} USD ({sign}{abs(diff_pct):.2f}%)"
                        )
                    msg = (
                        f"🔴📉 *{symbol} è scesa del -{abs(price_diff_pct):.2f}% in 5 minuti*\n"
                        f"💵 *Prezzo:* {fmt_price(prev_close)} → {fmt_price(last_close)} USD\n"
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
