import ccxt
import os
import time
import requests
from datetime import datetime, timedelta

# CONFIG
GROWTH_THRESHOLD_UP = 0.04    # +4%
GROWTH_THRESHOLD_DOWN = -0.02 # -2%
VOLUME_INCREASE_THRESHOLD = 0.25  # +25%
TIMEFRAME = '5m'
EXCHANGE = ccxt.coinbasepro()  # meglio coinbasepro per dati completi
SYMBOLS = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'ADA-USD']

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
            ohlcv = EXCHANGE.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=3)
            if len(ohlcv) < 3:
                print(f"[{symbol}] dati insufficienti")
                continue

            # Prelievo dati: 
            # Prendiamo le ultime 2 barre per valutare variazione tra due intervalli 5m
            old_candle = ohlcv[-3]
            prev_candle = ohlcv[-2]
            last_candle = ohlcv[-1]

            # Dati prezzi e volume
            old_close = old_candle[4]
            prev_close = prev_candle[4]
            last_close = last_candle[4]

            old_volume = old_candle[5]
            prev_volume = prev_candle[5]
            last_volume = last_candle[5]

            # Calcolo variazioni prezzo su intervallo 5m (ultime due barre)
            price_change = (last_close - prev_close) / prev_close
            # Calcolo variazioni volume
            volume_change = (last_volume - prev_volume) / prev_volume if prev_volume > 0 else 0

            # Funzione per controllo cooldown  (per evitare spam messaggi troppo ravvicinati)
            def can_notify(event_key, cooldown_minutes=60):
                last_sent = notified_events.get(event_key)
                if last_sent is None:
                    return True
                return (now - last_sent) > timedelta(minutes=cooldown_minutes)

            # Controllo crescita > +4%
            if price_change >= GROWTH_THRESHOLD_UP:
                event_key = (symbol, 'price_up')
                if can_notify(event_key):
                    tempo_slancio = TIMEFRAME  # 5 minuti (puoi personalizzare)
                    msg = (
                        f"*{symbol}* è cresciuta del *{price_change*100:.2f}%* negli ultimi {tempo_slancio}\n"
                        f"Prezzo prima: {prev_close:.4f} USD\n"
                        f"Prezzo attuale: {last_close:.4f} USD\n"
                        f"Orario UTC: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    send_telegram_message(msg)
                    notified_events[event_key] = now

            # Controllo calo < -2%
            elif price_change <= GROWTH_THRESHOLD_DOWN:
                event_key = (symbol, 'price_down')
                if can_notify(event_key):
                    tempo_slancio = TIMEFRAME
                    msg = (
                        f"*{symbol}* è scesa del *{abs(price_change)*100:.2f}%* negli ultimi {tempo_slancio}\n"
                        f"Prezzo prima: {prev_close:.4f} USD\n"
                        f"Prezzo attuale: {last_close:.4f} USD\n"
                        f"Orario UTC: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    send_telegram_message(msg)
                    notified_events[event_key] = now

            # Controllo aumento volume > +25% (anche se prezzo non sale del 4%)
            elif volume_change >= VOLUME_INCREASE_THRESHOLD:
                event_key = (symbol, 'volume_up')
                if can_notify(event_key):
                    msg = (
                        f"*{symbol}* volume aumentato del *{volume_change*100:.2f}%* negli ultimi {TIMEFRAME}\n"
                        f"Prezzo cambio: {price_change*100:.2f}%\n"
                        f"Prezzo attuale: {last_close:.4f} USD\n"
                        f"Orario UTC: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    send_telegram_message(msg)
                    notified_events[event_key] = now

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
        print(f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] Controllo variazioni...")
        check_and_notify()
        clean_memory()
        time.sleep(300)  # 5 minuti
