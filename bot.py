import ccxt
import os
import time
import requests
from datetime import datetime, timedelta

# CONFIG
GROWTH_THRESHOLD_UP = 0.04    # +4%
GROWTH_THRESHOLD_DOWN = -0.02 # -2%
VOLUME_INCREASE_THRESHOLD = 70.0  # +7000%
TIMEFRAME = '5m'
EXCHANGE = ccxt.coinbase()
SYMBOLS = [
    'AUCTION-USD', 'RLC-USD', 'TAIKO-USD', 'BAL-USD', 'POND-USD', 'CHILLGUY-USD', 'ABT-USD', 'AGLD-USD',
    # ... truncated for brevity ...
    'ZRX-USD'
]

# TELEGRAM CONFIG da variabili d'ambiente
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Memoria notifiche inviate: { (symbol, tipo_evento) : datetime_ultimo_invio }
notified_events = {}


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Errore invio Telegram: {e}")


def check_and_notify():
    global notified_events
    now = datetime.utcnow()

    for symbol in SYMBOLS:
        try:
            ohlcv = EXCHANGE.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=4)
            if len(ohlcv) < 4:
                continue

            old_candle, prev_candle, last_candle = ohlcv[-4], ohlcv[-2], ohlcv[-1]
            old_close, prev_close, last_close = old_candle[4], prev_candle[4], last_candle[4]
            old_vol, prev_vol, last_vol = old_candle[5], prev_candle[5], last_candle[5]

            price_change = (last_close - prev_close) / prev_close if prev_close > 0 else 0
            price_change_15 = (last_close - old_close) / old_close if old_close > 0 else 0
            volume_change = (last_vol - prev_vol) / prev_vol if prev_vol > 0 else 0

            def can_notify(key, cooldown=60):
                last = notified_events.get(key)
                return last is None or (now - last) > timedelta(minutes=cooldown)

            # Prezzo ↑ 5m
            if price_change >= GROWTH_THRESHOLD_UP:
                key = (symbol, 'price_up')
                if can_notify(key):
                    msg = (
                        f"🟢🟢🟢🟢📈 *{symbol} è salita del +{price_change*100:.2f}% in 5 minuti*\n"
                        f"💵 *Prezzo:* {prev_close:.4f} → {last_close:.4f} USD\n"
                        f"📊 *Differenza prezzo:* +{price_change*100:.2f}%\n"
                        f"🕒 *Orario:* {now.strftime('%Y-%m-%d %H:%M:%S')} UTC"
                    )
                    send_telegram_message(msg)
                    notified_events[key] = now

            # Prezzo ↑ 15m
            if price_change_15 >= GROWTH_THRESHOLD_UP:
                key = (symbol, 'price_up_15m')
                if can_notify(key):
                    msg = (
                        f"🟢🟢🟢🟢📈 *{symbol} è salita del +{price_change_15*100:.2f}% negli ultimi 15 minuti*\n"
                        f"💵 *Prezzo:* {old_close:.4f} → {last_close:.4f} USD\n"
                        f"📊 *Differenza prezzo:* +{price_change_15*100:.2f}%\n"
                        f"🕒 *Orario:* {now.strftime('%Y-%m-%d %H:%M:%S')} UTC"
                    )
                    send_telegram_message(msg)
                    notified_events[key] = now

            # Prezzo ↓ 5m
            elif price_change <= GROWTH_THRESHOLD_DOWN:
                key = (symbol, 'price_down')
                if can_notify(key):
                    pct = abs(price_change * 100)
                    msg = (
                        f"🔴🔴🔴🔴📉 *{symbol} è scesa del -{pct:.2f}% in 5 minuti*\n"
                        f"💵 *Prezzo:* {prev_close:.4f} → {last_close:.4f} USD\n"
                        f"📊 *Differenza prezzo:* -{pct:.2f}%\n"
                        f"🕒 *Orario:* {now.strftime('%Y-%m-%d %H:%M:%S')} UTC"
                    )
                    send_telegram_message(msg)
                    notified_events[key] = now

            # Volume ↑ ≥7000% + variaz. prezzo ≥±1.5%
            elif volume_change >= VOLUME_INCREASE_THRESHOLD:
                price_diff_pct = (last_close - prev_close) / prev_close * 100 if prev_close > 0 else 0
                if abs(price_diff_pct) >= 1.5:
                    key = (symbol, 'volume_up')
                    if can_notify(key):
                        color = "🟢" if price_diff_pct > 0 else "🔴"
                        msg = (
                            f"{color}🔊 *{symbol} volume ↑ +{volume_change*100:.2f}% in 5 minuti*\n"
                            f"📈 *Prezzo prima aumento volume:* {prev_close:.4f} USD\n"
                            f"📉 *Prezzo attuale:* {last_close:.4f} USD\n"
                            f"📊 *Differenza prezzo:* {price_diff_pct:+.2f}%\n"
                            f"🕒 *Orario:* {now.strftime('%Y-%m-%d %H:%M:%S')} UTC"
                        )
                        send_telegram_message(msg)
                        notified_events[key] = now

        except Exception as e:
            print(f"Errore con {symbol}: {e}")


def clean_memory():
    """Pulisce la memoria notifiche più vecchie di 12 ore"""
    now = datetime.utcnow()
    to_delete = [key for key, dt in notified_events.items() if (now - dt) > timedelta(hours=12)]
    for key in to_delete:
        del notified_events[key]


if __name__ == "__main__":
    print("Bot crypto monitor avviato...")
    while True:
        check_and_notify()
        clean_memory()
        time.sleep(240)  # aspetta 4 minuti prima del prossimo ciclo
