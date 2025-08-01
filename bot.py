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
    'NMR-USD', 'OCEAN-USD', 'CTSI-USD', 'AERGO-USD', 'MAGIC-USD', 'PRO-USD', 'DIA-USD', 'C98-USD', 'ACS-USD',
    'CAT-USD', 'TAI-USD', 'CELR-USD', 'HFT-USD', 'TNSR-USD', 'GODS-USD', 'RARE-USD', 'FORT-USD', 'BOBA-USD',
    'FWOG-USD', 'TOKEN-USD', 'STORJ-USD', 'TRU-USD', 'NCT-USD', 'OGN-USD', 'OXT-USD', 'MIGGLES-USD',
    'RAD-USD', 'LOKA-USD', 'REZ-USD', 'PNG-USD', 'LMWR-USD', 'GTC-USD', 'CLV-USD', 'SD-USD', 'SWELL-USD',
    'DYDX-USD', 'PYR-USD', 'WEN-USD', 'GME-USD', 'MLN-USD', 'GHST-USD', 'ARPA-USD', 'NKN-USD', 'BADGER-USD',
    'ALCX-USD', 'IDEX-USD', 'ASM-USD', 'HOPR-USD', 'FARM-USD', 'MATH-USD', 'POLS-USD', 'BENJI-USD', 'RARI-USD',
    'BLZ-USD', 'FIS-USD', 'SUKU-USD', 'VINU-USD', 'AVT-USD', 'VOXEL-USD', 'MDT-USD', 'AST-USD', 'FX-USD',
    'GST-USD', 'BTRST-USD', 'HIGH-USD', 'PLA-USD', 'SHPING-USD', 'MKR-USD', 'BTC-USD', 'ETH-USD', 'XRP-USD',
    'USDT-USD', 'BNB-USD', 'SOL-USD', 'USDC-USD', 'DOGE-USD', 'TRX-USD', 'ADA-USD', 'XLM-USD', 'SUI-USD',
    'LINK-USD', 'HBAR-USD', 'BCH-USD', 'AVAX-USD', 'SHIB-USD', 'TON-USD', 'LTC-USD', 'DOT-USD', 'UNI-USD',
    'PEPE-USD', 'AAVE-USD', 'CRO-USD', 'APT-USD', 'NEAR-USD', 'ICP-USD', 'ONDO-USD', 'ETC-USD', 'ALGO-USD',
    'ENA-USD', 'ATOM-USD', 'VET-USD', 'POL-USD', 'ARB-USD', 'BONK-USD', 'RENDER-USD', 'TRUMP-USD', 'PENGU-USD',
    'FET-USD', 'WLD-USD', 'SEI-USD', 'FIL-USD', 'QNT-USD', 'JUP-USD', 'SPX-USD', 'TIA-USD', 'INJ-USD',
    'STX-USD', 'FLR-USD', 'OP-USD', 'IMX-USD', 'WIF-USD', 'GRT-USD', 'FLOKI-USD', 'CRV-USD', 'MSOL-USD',
    'GALA-USD', 'JASMY-USD', 'MOG-USD', 'LDO-USD', 'ENS-USD', 'AERO-USD', 'PYTH-USD', 'XTZ-USD', 'JTO-USD',
    'FLOW-USD', 'MANA-USD', 'MORPHO-USD', 'XCN-USD', 'HNT-USD', 'APE-USD', 'RLUSD-USD', 'STRK-USD', 'RSR-USD',
    'KAVA-USD', 'EGLD-USD', '1INCH-USD', 'COMP-USD', 'AIOZ-USD', 'EIGEN-USD', 'AXS-USD', 'CHZ-USD', 'EOS-USD',
    'WUSD-USD', 'KAITO-USD', 'AKT-USD', 'POPCAT-USD', 'WAXL-USD', 'SUPER-USD', 'MATIC-USD', 'CTC-USD', 'AMP-USD',
    'ATH-USD', 'TURBO-USD', 'SAFE-USD', 'MEW-USD', 'LPT-USD', 'CVX-USD', 'DASH-USD', 'PNUT-USD', 'GLM-USD',
    'MINA-USD', 'KSM-USD', 'ARKM-USD', 'ZRO-USD', 'BERA-USD', 'TOSHI-USD', 'SNX-USD', 'BAT-USD', 'ZRX-USD'
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
            # price_change_15 = (last_close - old_close) / old_close if old_close > 0 else 0  # Non usato ora
            volume_change = (last_vol - prev_vol) / prev_vol if prev_vol > 0 else 0

            def can_notify(key, cooldown=60):
                last = notified_events.get(key)
                return last is None or (now - last) > timedelta(minutes=cooldown)

            # Alert per crescita prezzo
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

            # Alert per calo prezzo
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

            # Alert per volume solo se aumenta almeno del 7000% E prezzo cambia almeno del ±2%
            if volume_change >= VOLUME_INCREASE_THRESHOLD:
                price_diff_pct = (last_close - prev_close) / prev_close * 100 if prev_close > 0 else 0
                if abs(price_diff_pct) >= 2.0:
                    key = (symbol, 'volume_up')
                    if can_notify(key):
                        color = "🟢" if price_diff_pct > 0 else "🔴"
                        direction = "📈" if price_diff_pct > 0 else "📉"
                        msg = (
                            f"{color}🔊 *{symbol} volume ↑ +{volume_change*100:.2f}% in 5 minuti*\n"
                            f"{direction} *Prezzo prima aumento volume:* {prev_close:.4f} USD\n"
                            f"{direction} *Prezzo attuale:* {last_close:.4f} USD\n"
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
