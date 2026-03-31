import ccxt
import os
import time
import json
import requests
from datetime import datetime, timezone, timedelta
from threading import Thread

# ===== CONFIG =====
TIMEFRAME = '5m'
CHECK_INTERVAL = 300  # secondi (5 minuti, allineato con la candela 5m)

# Soglie dinamiche per categoria
LARGE_CAPS = {'BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD', 'DOGE-USD', 'TRX-USD', 'USDT-USD', 'USDC-USD'}
MID_CAPS   = {'AVAX-USD', 'LINK-USD', 'DOT-USD', 'NEAR-USD', 'APT-USD', 'ARB-USD', 'OP-USD', 'IMX-USD', 'INJ-USD', 'SUI-USD',
              'ATOM-USD', 'HBAR-USD', 'LTC-USD', 'BCH-USD', 'AAVE-USD', 'UNI-USD', 'MKR-USD', 'CRV-USD', 'LDO-USD', 'GRT-USD',
              'FIL-USD', 'ICP-USD', 'QNT-USD', 'STX-USD', 'FLR-USD', 'RENDER-USD', 'FET-USD', 'WLD-USD', 'TIA-USD', 'SEI-USD',
              'ETC-USD', 'ONDO-USD', 'ALGO-USD', 'ENA-USD', 'VET-USD', 'POL-USD', 'JUP-USD', 'BONK-USD', 'PEPE-USD', 'SHIB-USD',
              'FLOKI-USD', 'WIF-USD', 'JASMY-USD', 'XLM-USD', 'TON-USD'}

def get_threshold(symbol):
    """Soglia di rialzo dinamica per dimensione della cripto."""
    if symbol in LARGE_CAPS:
        return 0.01   # 1% — BTC, ETH e major: anche +1% è un segnale forte
    elif symbol in MID_CAPS:
        return 0.03   # 3% — mid cap
    else:
        return 0.04   # 4% — small/micro cap

EXCHANGE = ccxt.coinbase()
SYMBOLS = ['AUCTION-USD', 'RLC-USD', 'TAIKO-USD', 'BAL-USD', 'POND-USD', 'CHILLGUY-USD', 'ABT-USD', 'AGLD-USD', 'NMR-USD', 'OCEAN-USD', 'CTSI-USD', 'AERGO-USD', 'MAGIC-USD',
           'PRO-USD', 'DIA-USD', 'C98-USD', 'ACS-USD', 'CAT-USD', 'TAI-USD', 'CELR-USD', 'HFT-USD', 'TNSR-USD', 'GODS-USD', 'RARE-USD', 'FORT-USD', 'BOBA-USD', 'FWOG-USD', 'TOKEN-USD',
           'STORJ-USD', 'TRU-USD', 'NCT-USD', 'OGN-USD', 'OXT-USD', 'MIGGLES-USD', 'RAD-USD', 'LOKA-USD', 'REZ-USD', 'PNG-USD', 'LMWR-USD', 'GTC-USD', 'CLV-USD', 'SD-USD', 'SWELL-USD',
           'DYDX-USD', 'PYR-USD', 'WEN-USD', 'GME-USD', 'MLN-USD', 'GHST-USD', 'ARPA-USD', 'NKN-USD', 'BADGER-USD', 'ALCX-USD', 'IDEX-USD', 'ASM-USD', 'HOPR-USD', 'FARM-USD', 'MATH-USD',
           'POLS-USD', 'BENJI-USD', 'RARI-USD', 'BLZ-USD', 'FIS-USD', 'SUKU-USD', 'VINU-USD', 'AVT-USD', 'VOXEL-USD', 'MDT-USD', 'AST-USD', 'FX-USD', 'GST-USD', 'BTRST-USD', 'HIGH-USD',
           'PLA-USD', 'SHPING-USD', 'MKR-USD', 'BTC-USD', 'ETH-USD', 'XRP-USD', 'BNB-USD', 'SOL-USD', 'DOGE-USD', 'TRX-USD', 'ADA-USD', 'XLM-USD', 'SUI-USD', 'LINK-USD',
           'HBAR-USD', 'BCH-USD', 'AVAX-USD', 'SHIB-USD', 'TON-USD', 'LTC-USD', 'DOT-USD', 'UNI-USD', 'PEPE-USD', 'AAVE-USD', 'CRO-USD', 'APT-USD', 'NEAR-USD', 'ICP-USD', 'ONDO-USD', 'ETC-USD',
           'ALGO-USD', 'ENA-USD', 'ATOM-USD', 'VET-USD', 'POL-USD', 'ARB-USD', 'BONK-USD', 'RENDER-USD', 'TRUMP-USD', 'PENGU-USD', 'FET-USD', 'WLD-USD', 'SEI-USD', 'FIL-USD', 'QNT-USD', 'JUP-USD',
           'SPX-USD', 'TIA-USD', 'INJ-USD', 'STX-USD', 'FLR-USD', 'OP-USD', 'IMX-USD', 'WIF-USD', 'GRT-USD', 'FLOKI-USD', 'CRV-USD', 'MSOL-USD', 'GALA-USD', 'JASMY-USD', 'MOG-USD', 'LDO-USD', 'ENS-USD',
           'AERO-USD', 'PYTH-USD', 'XTZ-USD', 'JTO-USD', 'FLOW-USD', 'MANA-USD', 'MORPHO-USD', 'XCN-USD', 'HNT-USD', 'APE-USD', 'RLUSD-USD', 'STRK-USD', 'RSR-USD', 'KAVA-USD', 'EGLD-USD', '1INCH-USD',
           'COMP-USD', 'AIOZ-USD', 'EIGEN-USD', 'AXS-USD', 'CHZ-USD', 'EOS-USD', 'KAITO-USD', 'AKT-USD', 'POPCAT-USD', 'WAXL-USD', 'SUPER-USD', 'MATIC-USD', 'CTC-USD', 'AMP-USD', 'ATH-USD',
           'TURBO-USD', 'SAFE-USD', 'MEW-USD', 'LPT-USD', 'CVX-USD', 'DASH-USD', 'PNUT-USD', 'GLM-USD', 'MINA-USD', 'KSM-USD', 'ARKM-USD', 'ZRO-USD', 'BERA-USD', 'TOSHI-USD', 'SNX-USD', 'BAT-USD', 'ZRX-USD',
           'BLUR-USD', 'ROSE-USD', 'IOTX-USD', 'NEIRO-USD', 'VTHO-USD', 'YFI-USD', 'CELO-USD', 'GIGA-USD', 'MOODENG-USD', 'COW-USD', 'TRAC-USD', 'ANKR-USD', 'WOO-USD', 'GMT-USD', 'IO-USD',
           'SUSHI-USD', 'MASK-USD', 'PRIME-USD', 'XYO-USD', 'ZEN-USD', 'OSMO-USD', 'MELANIA-USD', 'RPL-USD', 'ME-USD', 'COTI-USD', 'SKL-USD', 'ILV-USD', 'BIGTIME-USD', 'METIS-USD', 'SWFTC-USD', 'REQ-USD',
           'OMNI-USD', 'BAND-USD', 'ACH-USD', 'LQTY-USD', 'UMA-USD', 'BICO-USD', 'COOKIE-USD', 'LRC-USD', 'DEGEN-USD', 'POWR-USD', 'API3-USD', 'KNC-USD', 'AUDIO-USD', 'SPELL-USD',
           'ACX-USD', 'CVC-USD', 'FIDA-USD', 'PONKE-USD', 'BNT-USD']

# ===== TELEGRAM =====
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ===== STATO BOT =====
bot_active = True          # True = attivo, False = in pausa
notified_events = {}       # (symbol, "up") -> datetime ultimo alert (cooldown 12h)

# ===== UTILS =====
def fmt_price(p):
    p = float(p)
    if p >= 1:
        s = f"{p:.2f}"
    elif p >= 0.0001:
        s = f"{p:.6f}"
    else:
        s = f"{p:.8f}"
    return s.rstrip('0').rstrip('.') if '.' in s else s

def normalize_symbol(s):
    s = s.upper().strip().replace('/', '-')
    if '-' not in s:
        s += '-USD'
    return s

def send_telegram(text, chat_id=None):
    if chat_id is None:
        chat_id = TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print("Errore Telegram:", e)

def can_notify(key):
    """Evita notifiche duplicate per la stessa cripto entro 12 ore."""
    now = datetime.now(timezone.utc)
    last = notified_events.get(key)
    if last and (now - last) < timedelta(hours=12):
        return False
    return True

# ===== CICLO CONTROLLO =====
def check_and_notify():
    now = datetime.now(timezone.utc)
    for symbol in SYMBOLS:
        try:
            ohlcv = EXCHANGE.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=2)
            if len(ohlcv) < 2:
                continue
            prev_close = float(ohlcv[-2][4])
            last_close = float(ohlcv[-1][4])
            if prev_close == 0:
                continue
            change = (last_close - prev_close) / prev_close
            threshold = get_threshold(symbol)

            # Solo RIALZI — nessuna notifica per i ribassi
            if change >= threshold:
                key = (symbol, "up")
                if can_notify(key):
                    label = "large cap" if symbol in LARGE_CAPS else ("mid cap" if symbol in MID_CAPS else "small cap")
                    msg = (f"🟢 *{symbol}* +{change*100:.2f}% in 5 min [{label}]\n"
                           f"💵 {fmt_price(prev_close)} → {fmt_price(last_close)} USD\n"
                           f"🕒 {now.strftime('%H:%M')} UTC")
                    send_telegram(msg)
                    notified_events[key] = now
        except Exception as e:
            print(f"Errore {symbol}: {e}")

# ===== COMANDI TELEGRAM =====
def handle_command(chat_id, text):
    global bot_active
    parts = text.strip().lower().split()
    if not parts:
        return
    cmd = parts[0]

    if cmd in ("/fine", "/stop", "/pausa"):
        bot_active = False
        send_telegram(
            "⏸ *Bot in pausa.*\n"
            "Non riceverai più notifiche finché non scrivi /inizia o /ricomincia.",
            chat_id
        )

    elif cmd in ("/inizia", "/ricomincia", "/start"):
        bot_active = True
        send_telegram("▶️ *Bot riattivato!* Riprendo il monitoraggio crypto.", chat_id)

    elif cmd == "/status":
        stato = "▶️ *Attivo* — sto monitorando tutte le crypto" if bot_active else "⏸ *In pausa* — scrivi /inizia per riattivarlo"
        send_telegram(f"Stato bot: {stato}", chat_id)

    elif cmd == "/price" and len(parts) >= 2:
        sym = normalize_symbol(parts[1])
        try:
            ticker = EXCHANGE.fetch_ticker(sym)
            send_telegram(f"💰 *{sym}* → {fmt_price(ticker['last'])} USD", chat_id)
        except Exception as e:
            send_telegram(f"Errore prezzo {sym}: {e}", chat_id)

    elif cmd == "/help":
        send_telegram(
            "📖 *Comandi disponibili:*\n"
            "/fine — metti il bot in pausa (nessuna notifica)\n"
            "/inizia — riattiva il bot\n"
            "/status — vedi stato attuale del bot\n"
            "/price BTC — prezzo attuale di una cripto\n"
            "/help — questo messaggio",
            chat_id
        )

# ===== POLLING TELEGRAM =====
def telegram_polling():
    update_id = None
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
            params = {"timeout": 30}
            if update_id:
                params["offset"] = update_id
            res = requests.get(url, params=params, timeout=35)
            if res.status_code == 200:
                for item in res.json().get("result", []):
                    update_id = item["update_id"] + 1
                    msg = item.get("message", {})
                    text = msg.get("text", "")
                    chat_id = msg.get("chat", {}).get("id")
                    if text and chat_id:
                        handle_command(chat_id, text)
        except Exception as e:
            print("Polling error:", e)
        time.sleep(1)

# ===== MAIN LOOP =====
def main_loop():
    print("Bot avviato. Monitoraggio solo rialzi con soglie dinamiche per market cap.")
    while True:
        if bot_active:
            try:
                check_and_notify()
            except Exception as e:
                print("Errore main loop:", e)
        # Quando in pausa: sleep senza fare nulla — consumo CPU quasi zero
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    Thread(target=telegram_polling, daemon=True).start()
    main_loop()
