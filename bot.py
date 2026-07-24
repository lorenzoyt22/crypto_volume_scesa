import ccxt.async_support as ccxt_async  # Importante: usiamo la versione asincrona!
import os
import time
import requests
import asyncio
from datetime import datetime, timezone, timedelta
from threading import Thread

# ===== CONFIG =====
# Rimosso TIMEFRAME='5m' perché calcoliamo le candele internamente in modo ultra-veloce.

LARGE_CAPS = {'BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD', 'DOGE-USD', 'TRX-USD', 'USDT-USD', 'USDC-USD'}
MID_CAPS   = {'AVAX-USD', 'LINK-USD', 'DOT-USD', 'NEAR-USD', 'APT-USD', 'ARB-USD', 'OP-USD', 'IMX-USD', 'INJ-USD', 'SUI-USD',
              'ATOM-USD', 'HBAR-USD', 'LTC-USD', 'BCH-USD', 'AAVE-USD', 'UNI-USD', 'MKR-USD', 'CRV-USD', 'LDO-USD', 'GRT-USD',
              'FIL-USD', 'ICP-USD', 'QNT-USD', 'STX-USD', 'FLR-USD', 'RENDER-USD', 'FET-USD', 'WLD-USD', 'TIA-USD', 'SEI-USD',
              'ETC-USD', 'ONDO-USD', 'ALGO-USD', 'ENA-USD', 'VET-USD', 'POL-USD', 'JUP-USD', 'BONK-USD', 'PEPE-USD', 'SHIB-USD',
              'FLOKI-USD', 'WIF-USD', 'JASMY-USD', 'XLM-USD', 'TON-USD'}

def get_threshold(symbol):
    if symbol in LARGE_CAPS: return 0.01
    elif symbol in MID_CAPS: return 0.03
    else: return 0.04

EXCHANGE = ccxt_async.coinbase({'enableRateLimit': True})

SYMBOLS = [
    # --- Small/micro cap (soglia 4%) ---
    'AUCTION-USD', 'RLC-USD', 'TAIKO-USD', 'BAL-USD', 'POND-USD', 'CHILLGUY-USD', 'ABT-USD', 'AGLD-USD', 'NMR-USD', 'OCEAN-USD',
    'CTSI-USD', 'AERGO-USD', 'MAGIC-USD', 'PRO-USD', 'DIA-USD', 'C98-USD', 'ACS-USD', 'CAT-USD', 'TAI-USD', 'CELR-USD',
    'HFT-USD', 'TNSR-USD', 'GODS-USD', 'RARE-USD', 'FORT-USD', 'BOBA-USD', 'FWOG-USD', 'TOKEN-USD',
    'STORJ-USD', 'TRU-USD', 'NCT-USD', 'OGN-USD', 'OXT-USD', 'MIGGLES-USD', 'RAD-USD', 'LOKA-USD', 'REZ-USD', 'PNG-USD',
    'LMWR-USD', 'GTC-USD', 'CLV-USD', 'SD-USD', 'SWELL-USD', 'DYDX-USD', 'PYR-USD', 'WEN-USD', 'GME-USD', 'MLN-USD',
    'GHST-USD', 'ARPA-USD', 'NKN-USD', 'BADGER-USD', 'ALCX-USD', 'IDEX-USD', 'ASM-USD', 'HOPR-USD', 'FARM-USD', 'MATH-USD',
    'POLS-USD', 'BENJI-USD', 'RARI-USD', 'BLZ-USD', 'FIS-USD', 'SUKU-USD', 'VINU-USD', 'AVT-USD', 'VOXEL-USD', 'MDT-USD',
    'AST-USD', 'FX-USD', 'GST-USD', 'BTRST-USD', 'HIGH-USD', 'PLA-USD', 'SHPING-USD', 'SAND-USD', 'ENJ-USD',
    # --- Mid cap (soglia 3%) ---
    'MKR-USD', 'AVAX-USD', 'LINK-USD', 'DOT-USD', 'UNI-USD', 'PEPE-USD', 'AAVE-USD', 'CRO-USD', 'APT-USD', 'NEAR-USD',
    'ICP-USD', 'ONDO-USD', 'ETC-USD', 'ALGO-USD', 'ENA-USD', 'ATOM-USD', 'VET-USD', 'POL-USD', 'ARB-USD', 'BONK-USD',
    'RENDER-USD', 'TRUMP-USD', 'PENGU-USD', 'FET-USD', 'WLD-USD', 'SEI-USD', 'FIL-USD', 'QNT-USD', 'JUP-USD',
    'SPX-USD', 'TIA-USD', 'INJ-USD', 'STX-USD', 'FLR-USD', 'OP-USD', 'IMX-USD', 'WIF-USD', 'GRT-USD', 'FLOKI-USD',
    'CRV-USD', 'MSOL-USD', 'GALA-USD', 'JASMY-USD', 'MOG-USD', 'LDO-USD', 'ENS-USD',
    'AERO-USD', 'PYTH-USD', 'XTZ-USD', 'JTO-USD', 'FLOW-USD', 'MANA-USD', 'MORPHO-USD', 'XCN-USD', 'HNT-USD', 'APE-USD',
    'RLUSD-USD', 'STRK-USD', 'RSR-USD', 'KAVA-USD', 'EGLD-USD', '1INCH-USD',
    'COMP-USD', 'AIOZ-USD', 'EIGEN-USD', 'AXS-USD', 'CHZ-USD', 'EOS-USD', 'KAITO-USD', 'AKT-USD', 'POPCAT-USD',
    'WAXL-USD', 'SUPER-USD', 'MATIC-USD', 'CTC-USD', 'AMP-USD', 'ATH-USD',
    'TURBO-USD', 'SAFE-USD', 'MEW-USD', 'LPT-USD', 'CVX-USD', 'DASH-USD', 'PNUT-USD', 'GLM-USD', 'MINA-USD', 'KSM-USD',
    'ARKM-USD', 'ZRO-USD', 'BERA-USD', 'TOSHI-USD', 'SNX-USD', 'BAT-USD', 'ZRX-USD',
    'BLUR-USD', 'ROSE-USD', 'IOTX-USD', 'NEIRO-USD', 'VTHO-USD', 'YFI-USD', 'CELO-USD', 'GIGA-USD', 'MOODENG-USD',
    'COW-USD', 'TRAC-USD', 'ANKR-USD', 'WOO-USD', 'GMT-USD', 'IO-USD',
    'SUSHI-USD', 'MASK-USD', 'PRIME-USD', 'XYO-USD', 'ZEN-USD', 'OSMO-USD', 'MELANIA-USD', 'RPL-USD', 'ME-USD',
    'COTI-USD', 'SKL-USD', 'ILV-USD', 'BIGTIME-USD', 'METIS-USD', 'SWFTC-USD', 'REQ-USD',
    'OMNI-USD', 'BAND-USD', 'ACH-USD', 'LQTY-USD', 'UMA-USD', 'BICO-USD', 'COOKIE-USD', 'LRC-USD', 'DEGEN-USD',
    'POWR-USD', 'API3-USD', 'KNC-USD', 'AUDIO-USD', 'SPELL-USD',
    'ACX-USD', 'CVC-USD', 'FIDA-USD', 'PONKE-USD', 'BNT-USD',
    # --- Large cap (soglia 1%) ---
    'BTC-USD', 'ETH-USD', 'XRP-USD', 'BNB-USD', 'SOL-USD', 'DOGE-USD', 'TRX-USD', 'ADA-USD',
    'XLM-USD', 'SUI-USD', 'HBAR-USD', 'BCH-USD', 'SHIB-USD', 'TON-USD', 'LTC-USD',
]

# ===== TELEGRAM =====
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ===== STATO BOT =====
bot_active = True
notified_events = {}
last_prices = {} # Memoria centralizzata dei prezzi

# ===== UTILS =====
def fmt_price(p):
    p = float(p)
    if p >= 1: s = f"{p:.2f}"
    elif p >= 0.0001: s = f"{p:.6f}"
    else: s = f"{p:.8f}"
    return s.rstrip('0').rstrip('.') if '.' in s else s

def normalize_symbol(s):
    s = s.upper().strip().replace('/', '-')
    if '-' not in s: s += '-USD'
    return s

def send_telegram(text, chat_id=None):
    if chat_id is None: chat_id = TELEGRAM_CHAT_ID
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print("Errore Telegram:", e)

def can_notify(key):
    now = datetime.now(timezone.utc)
    last = notified_events.get(key)
    # MODIFICA QUI: Se vuoi avvisi più frequenti, abbassa 'hours=12' (es. hours=2)
    if last and (now - last) < timedelta(hours=12): 
        return False
    return True

# ===== CICLO CONTROLLO ASINCRONO =====
async def check_all_symbols():
    global last_prices
    try:
        # OTTIMIZZAZIONE MASSIMA: Un'unica richiesta API per ottenere TUTTI i prezzi correnti
        tickers = await EXCHANGE.fetch_tickers(SYMBOLS)
    except Exception as e:
        print("Errore fetch_tickers:", e)
        return

    now = datetime.now(timezone.utc)

    for symbol in SYMBOLS:
        ticker = tickers.get(symbol)
        if not ticker: continue
        
        current_price = ticker.get('last')
        if current_price is None: continue

        # Se abbiamo in memoria il prezzo dello step precedente (5 min fa), analizziamo
        if symbol in last_prices:
            prev_price = last_prices[symbol]
            
            if prev_price > 0:
                change = (current_price - prev_price) / prev_price
                threshold = get_threshold(symbol)

                if change >= threshold:
                    key = (symbol, "up")
                    if can_notify(key):
                        label = "large cap" if symbol in LARGE_CAPS else ("mid cap" if symbol in MID_CAPS else "small cap")
                        msg = (f"🟢 *{symbol}* +{change*100:.2f}% in 5 min [{label}]\n"
                               f"💵 {fmt_price(prev_price)} ➔ {fmt_price(current_price)} USD\n"
                               f"🕒 {now.strftime('%H:%M')} UTC")
                        # Scheduliamo l'invio su Telegram senza bloccare il ciclo
                        asyncio.create_task(asyncio.to_thread(send_telegram, msg))
                        notified_events[key] = now

        # Aggiorniamo il prezzo in memoria per la prossima "candela"
        last_prices[symbol] = current_price

async def main_loop_async():
    print("Bot avviato. Monitoraggio ottimizzato a singola chiamata.")
    
    # Primo caricamento per riempire la memoria dei prezzi senza inviare notifiche
    try:
        print("Pre-caricamento prezzi in corso...")
        tickers = await EXCHANGE.fetch_tickers(SYMBOLS)
        for sym in SYMBOLS:
            if sym in tickers and tickers[sym].get('last'):
                last_prices[sym] = tickers[sym]['last']
    except Exception as e:
        print("Errore nel pre-caricamento:", e)

    while True:
        # Calcoliamo prima quanto manca al prossimo multiplo di 5 minuti
        now = datetime.now()
        minutes_to_next = 5 - (now.minute % 5)
        seconds_to_sleep = (minutes_to_next * 60) - now.second
        
        # Dormiamo fino allo scoccare del 5° minuto
        await asyncio.sleep(seconds_to_sleep + 2) # +2 secondi di margine per aggiornamento dati
        
        if bot_active:
            await check_all_symbols()

# ===== COMANDI TELEGRAM =====
def handle_command(chat_id, text):
    global bot_active, last_prices
    parts = text.strip().lower().split()
    if not parts: return
    cmd = parts[0]

    if cmd in ("/fine", "/stop", "/pausa"):
        bot_active = False
        send_telegram("⏸️ *Bot in pausa.*\nNon riceverai più notifiche finché non scrivi /inizia.", chat_id)
    elif cmd in ("/inizia", "/ricomincia", "/start"):
        bot_active = True
        send_telegram("▶️ *Bot riattivato!* Riprendo il monitoraggio crypto.", chat_id)
    elif cmd == "/status":
        stato = "▶️ *Attivo*" if bot_active else "⏸️ *In pausa*"
        send_telegram(f"Stato bot: {stato}", chat_id)
    elif cmd == "/price" and len(parts) >= 2:
        sym = normalize_symbol(parts[1])
        # OTTIMIZZATO: Ora legge il prezzo dalla memoria in 0 millisecondi invece di interrogare l'Exchange
        if sym in last_prices:
            send_telegram(f"💰 *{sym}* ➔ {fmt_price(last_prices[sym])} USD", chat_id)
        else:
            send_telegram(f"⚠️ Prezzo di {sym} non ancora registrato in memoria. Attendi la chiusura della candela.", chat_id)
    elif cmd == "/help":
        send_telegram("📖 *Comandi:*\n/fine - pausa\n/inizia - riattiva\n/status - stato\n/price BTC - prezzo\n/help - info", chat_id)

def telegram_polling():
    update_id = None
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
            params = {"timeout": 30}
            if update_id: params["offset"] = update_id
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

if __name__ == "__main__":
    Thread(target=telegram_polling, daemon=True).start()
    asyncio.run(main_loop_async())
