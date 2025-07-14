import ccxt
import os
import time
import requests
from datetime import datetime, timedelta

# CONFIG
GROWTH_THRESHOLD_UP = 0.04    # +4%
GROWTH_THRESHOLD_DOWN = -0.02 # -2%
VOLUME_INCREASE_THRESHOLD = 50.0  # +5000%
TIMEFRAME = '5m'
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
'TURBO-USD', 'SAFE-USD', 'MEW-USD', 'LPT-USD', 'CVX-USD', 'DASH-USD', 'PNUT-USD', 'GLM-USD', 'MINA-USD', 'KSM-USD', 'ARKM-USD', 'ZRO-USD', 'BERA-USD', 'TOSHI-USD', 'SNX-USD', 'BAT-USD', 'ZRX-USD'
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
                print(f"[{symbol}] dati insufficienti")
                continue

            # Prelievo dati: ultime 4 candele da 5m (15 minuti)
            old_candle = ohlcv[-4]    # 15 minuti fa
            prev_candle = ohlcv[-2]   # 10 minuti fa (non usato direttamente)
            last_candle = ohlcv[-1]   # ultimo 5 minuti

            # Dati prezzi e volume
            old_close = old_candle[4]
            prev_close = prev_candle[4]
            last_close = last_candle[4]

            old_volume = old_candle[5]
            prev_volume = prev_candle[5]
            last_volume = last_candle[5]

            # Variazione prezzo a 5 minuti (ultima vs penultima candela)
            price_change = (last_close - prev_close) / prev_close
            # Variazione prezzo cumulativa a 15 minuti (ultima vs 4 candele fa)
            price_change_15m = (last_close - old_close) / old_close

            # Variazione volume a 5 minuti
            volume_change = (last_volume - prev_volume) / prev_volume if prev_volume > 0 else 0

            # Funzione per cooldown notifiche (evita spam)
            def can_notify(event_key, cooldown_minutes=60):
                last_sent = notified_events.get(event_key)
                if last_sent is None:
                    return True
                return (now - last_sent) > timedelta(minutes=cooldown_minutes)

            # Controllo crescita > +4% in 5 minuti
            if price_change >= GROWTH_THRESHOLD_UP:
                event_key = (symbol, 'price_up')
                if can_notify(event_key):
                    msg = (
                        f"📈 *{symbol} è salita del +{price_change*100:.2f}%* in 5 minuti\n"
                        f"💵 *Prezzo:* {prev_close:.4f} → {last_close:.4f} USD\n"
                        f"🕒 *Orario:* {now.strftime('%Y-%m-%d %H:%M:%S')} UTC"
                    )
                    send_telegram_message(msg)
                    notified_events[event_key] = now

            # Controllo crescita cumulativa > +4% in 15 minuti
            if price_change_15m >= GROWTH_THRESHOLD_UP:
                event_key = (symbol, 'price_up_15m')
                if can_notify(event_key):
                    msg = (
                        f"📈 *{symbol} è salita del +{price_change_15m*100:.2f}%* negli ultimi 15 minuti\n"
                        f"💵 *Prezzo:* {old_close:.4f} → {last_close:.4f} USD\n"
                        f"🕒 *Orario:* {now.strftime('%Y-%m-%d %H:%M:%S')} UTC"
                    )
                    send_telegram_message(msg)
                    notified_events[event_key] = now

            # Controllo calo < -2%
            elif price_change <= GROWTH_THRESHOLD_DOWN:
                event_key = (symbol, 'price_down')
                if can_notify(event_key):
                    msg = (
                        f"📉 *{symbol} è scesa del -{abs(price_change)*100:.2f}%* in 5 minuti\n"
                        f"💵 *Prezzo:* {prev_close:.4f} → {last_close:.4f} USD\n"
                        f"🕒 *Orario:* {now.strftime('%Y-%m-%d %H:%M:%S')} UTC"
                    )
                    send_telegram_message(msg)
                    notified_events[event_key] = now

            # Controllo aumento volume > +5000% (anche se prezzo non sale del 4%)
            elif volume_change >= VOLUME_INCREASE_THRESHOLD:
                event_key = (symbol, 'volume_up')
                if can_notify(event_key):
                    price_diff_pct = ((last_close - prev_close) / prev_close) * 100 if prev_close > 0 else 0
                    msg = (
                        f"🔊 *{symbol} volume ↑ +{volume_change*100:.2f}%* in 5 minuti\n"
                        f"📈 *Prezzo prima aumento volume:* {prev_close:.4f} USD\n"
                        f"📉 *Prezzo attuale:* {last_close:.4f} USD\n"
                        f"📊 *Differenza prezzo:* {price_diff_pct:+.2f}%\n"
                        f"🕒 *Orario:* {now.strftime('%Y-%m-%d %H:%M:%S')} UTC"
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
        check_and_notify()
        clean_memory()
        time.sleep(240)  # aspetta 4 minuti prima del prossimo ciclo
