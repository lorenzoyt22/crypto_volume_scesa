import ccxt.async_support as ccxt_async  # Importante: usiamo la versione asincrona!
import os
import time
import requests
import asyncio
from datetime import datetime, timezone, timedelta
from threading import Thread

# ===== CONFIG =====
# Rimosso TIMEFRAME='5m' perché calcoliamo le candele internamente in modo ultra-veloce.

LARGE_CAPS = {'BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD', 'DOGE-USD', 'TRX-USD', 'USDC-USD'}

MID_CAPS   = {'AVAX-USD', 'LINK-USD', 'DOT-USD', 'NEAR-USD', 'APT-USD', 'ARB-USD', 'OP-USD', 'IMX-USD', 'INJ-USD', 'SUI-USD',
              'ATOM-USD', 'HBAR-USD', 'LTC-USD', 'BCH-USD', 'AAVE-USD', 'UNI-USD', 'CRV-USD', 'LDO-USD', 'GRT-USD',
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
    '1INCH-USD', '2Z-USD', 'A8-USD', 'ABT-USD', 'ACH-USD', 'ACS-USD', 'AERO-USD', 'AERGO-USD', 'AGLD-USD', 'AI-USD', 
    'AIOZ-USD', 'AKT-USD', 'ALCX-USD', 'ALEO-USD', 'ALEPH-USD', 'ALICE-USD', 'AMP-USD', 'ANKR-USD', 'APE-USD', 'API3-USD', 
    'ARKM-USD', 'ARPA-USD', 'ASM-USD', 'AST-USD', 'ATH-USD', 'AUCTION-USD', 'AUDIO-USD', 'AURORA-USD', 'AVNT-USD', 'AVT-USD', 
    'AWE-USD', 'AXS-USD', 'B3-USD', 'BADGER-USD', 'BAL-USD', 'BAND-USD', 'BAT-USD', 'BEAM-USD', 'BERA-USD', 
    'BICO-USD', 'BIGTIME-USD', 'BLUR-USD', 'BLZ-USD', 'BNT-USD', 'BOBA-USD', 'BTRST-USD', 'C98-USD', 
    'CELR-USD', 'CHZ-USD', 'CLANKER-USD', 'COMP-USD', 'COOKIE-USD', 'COTI-USD', 'COW-USD', 'CRO-USD', 'CTSI-USD', 'CVC-USD', 
    'CVX-USD', 'DASH-USD', 'DEGEN-USD', 'DIA-USD', 'DIMO-USD', 'DOGINME-USD', 'DOLO-USD', 'DRIFT-USD', 
    'EDGE-USD', 'EGLD-USD', 'EIGEN-USD', 'ELA-USD', 'ENS-USD', 'EUL-USD', 'FAI-USD', 'FARM-USD', 'FIDA-USD', 'FLOW-USD', 
    'FLUID-USD', 'FORT-USD', 'FORTH-USD', 'GFI-USD', 'GHST-USD', 'GIGA-USD', 'GLM-USD', 'GMT-USD', 'GODS-USD', 
    'GRASS-USD', 'GST-USD', 'GTC-USD', 'HFT-USD', 'HIGH-USD', 'HNT-USD', 'HONEY-USD', 'HOPR-USD', 'HYPE-USD', 'IDEX-USD', 
    'IDOS-USD', 'ILV-USD', 'IMU-USD', 'IO-USD', 'IOTX-USD', 'IP-USD', 'JTO-USD', 'KAITO-USD', 'KARRAT-USD', 'KAVA-USD', 
    'KERNEL-USD', 'KNC-USD', 'KRL-USD', 'KSM-USD', 'KTA-USD', 'L3-USD', 'LA-USD', 'LAYER-USD', 'LCX-USD', 'LMWR-USD', 
    'LPT-USD', 'LQTY-USD', 'LRC-USD', 'LRDS-USD', 'MAGIC-USD', 'MANA-USD', 'MASK-USD', 'MATH-USD', 'MDT-USD', 'ME-USD', 
    'MELANIA-USD', 'METIS-USD', 'MEW-USD', 'MINA-USD', 'MLN-USD', 'MNDE-USD', 'MOG-USD', 'MON-USD', 'MOODENG-USD', 'MORPHO-USD', 
    'MSOL-USD', 'NCT-USD', 'NEIRO-USD', 'NEON-USD', 'NKN-USD', 'NMR-USD', 'NOT-USD', 'OCEAN-USD', 'OFC-USD', 'OGN-USD', 
    'ORCA-USD', 'OSMO-USD', 'OXT-USD', 'PARTI-USD', 'PENDLE-USD', 'PENGU-USD', 'PERP-USD', 'PLUME-USD', 'PNG-USD', 'PNUT-USD', 
    'POLS-USD', 'POND-USD', 'PONKE-USD', 'POPCAT-USD', 'POWR-USD', 'PRCL-USD', 'PRIME-USD', 'PRO-USD', 'PROMPT-USD', 'PROVE-USD', 
    'PUMP-USD', 'PUNDIX-USD', 'PYR-USD', 'PYTH-USD', 'QI-USD', 'RAD-USD', 'RARE-USD', 'RARI-USD', 'RAY-USD', 'RED-USD', 
    'REQ-USD', 'REZ-USD', 'RLC-USD', 'RLS-USD', 'ROSE-USD', 'RPL-USD', 'RSC-USD', 'RSR-USD', 'SAFE-USD', 'SAND-USD', 
    'SD-USD', 'SENT-USD', 'SHDW-USD', 'SHPING-USD', 'SKL-USD', 'SKY-USD', 'SNX-USD', 'SOMI-USD', 'SPA-USD', 'SPELL-USD', 
    'SPK-USD', 'SPX-USD', 'SQD-USD', 'STG-USD', 'STORJ-USD', 'STRK-USD', 'SUKU-USD', 'SUPER-USD', 'SUSHI-USD', 'SWELL-USD', 
    'SWFTC-USD', 'SXT-USD', 'SYRUP-USD', 'T-USD', 'TAIKO-USD', 'TNSR-USD', 'TOKEN-USD', 'TOSHI-USD', 'TRAC-USD', 'TRB-USD', 
    'TREE-USD', 'TRU-USD', 'TRUMP-USD', 'TURBO-USD', 'UMA-USD', 'VELO-USD', 'VOXEL-USD', 'VTHO-USD', 'VVV-USD', 'W-USD', 
    'WAL-USD', 'WLFI-USD', 'WOO-USD', 'XAN-USD', 'XCN-USD', 'XDC-USD', 'XPL-USD', 'XTZ-USD', 'XYO-USD', 'YFI-USD', 
    'ZAMA-USD', 'ZEN-USD', 'ZK-USD', 'ZKC-USD', 'ZKJ-USD', 'ZORA-USD', 'ZRO-USD', 'ZRX-USD',
    
    # --- Mid cap (soglia 3%) ---
    'AVAX-USD', 'LINK-USD', 'DOT-USD', 'NEAR-USD', 'APT-USD', 'ARB-USD', 'OP-USD', 'IMX-USD', 'INJ-USD', 'SUI-USD',
    'ATOM-USD', 'HBAR-USD', 'LTC-USD', 'BCH-USD', 'AAVE-USD', 'UNI-USD', 'CRV-USD', 'LDO-USD', 'GRT-USD', 'FIL-USD', 
    'ICP-USD', 'QNT-USD', 'STX-USD', 'FLR-USD', 'RENDER-USD', 'FET-USD', 'WLD-USD', 'TIA-USD', 'SEI-USD', 'ETC-USD', 
    'ONDO-USD', 'ALGO-USD', 'ENA-USD', 'VET-USD', 'POL-USD', 'JUP-USD', 'BONK-USD', 'PEPE-USD', 'SHIB-USD', 'FLOKI-USD', 
    'WIF-USD', 'JASMY-USD', 'XLM-USD', 'TON-USD',
    
    # --- Large cap (soglia 1%) ---
    'BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD', 'DOGE-USD', 'TRX-USD', 'USDC-USD'
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
    global last_prices, SYMBOLS
    
    tickers = None
    while True:
        try:
            # OTTIMIZZAZIONE MASSIMA: Un'unica richiesta API per ottenere TUTTI i prezzi correnti
            tickers = await EXCHANGE.fetch_tickers(SYMBOLS)
            break
        except Exception as e:
            error_str = str(e)
            if "does not have market symbol" in error_str:
                bad_symbol = error_str.split("symbol ")[-1].strip()
                if bad_symbol in SYMBOLS:
                    SYMBOLS.remove(bad_symbol)
                    print(f"🗑️ Trovato intruso ({bad_symbol}), scartato. Riprovo subito a scaricare il resto...")
                    continue
            print("Errore fetch_tickers:", error_str)
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
    global SYMBOLS
    print("Bot avviato. Monitoraggio ottimizzato a singola chiamata con pulizia automatica.")
    
    # Primo caricamento per riempire la memoria dei prezzi senza inviare notifiche
    try:
        print("Pre-caricamento prezzi in corso...")
        tickers = None
        while True:
            try:
                tickers = await EXCHANGE.fetch_tickers(SYMBOLS)
                break
            except Exception as e:
                error_str = str(e)
                if "does not have market symbol" in error_str:
                    bad_symbol = error_str.split("symbol ")[-1].strip()
                    if bad_symbol in SYMBOLS:
                        SYMBOLS.remove(bad_symbol)
                        print(f"🗑️ Simbolo non valido saltato al pre-caricamento: {bad_symbol}")
                        continue
                print("Errore imprevisto nel pre-caricamento:", error_str)
                break
                
        if tickers:
            for sym in SYMBOLS:
                if sym in tickers and tickers[sym].get('last'):
                    last_prices[sym] = tickers[sym]['last']
            print(f"Pre-caricamento completato. {len(last_prices)} crypto monitorate attivamente.")
    except Exception as e:
        print("Errore fatale nel pre-caricamento:", e)

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
