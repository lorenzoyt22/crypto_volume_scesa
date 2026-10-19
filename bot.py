import ccxt.async_support as ccxt_async  # Versione asincrona
import os
import time
import requests
import asyncio
import gc  # Garbage Collector per mantenere la RAM a zero su Railway
from datetime import datetime, timezone, timedelta
from threading import Thread

# ===== CONFIGURAZIONE SOGLIE =====
LARGE_CAPS = {'BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD', 'DOGE-USD'}

MID_CAPS   = {'AVAX-USD', 'LINK-USD', 'DOT-USD', 'NEAR-USD', 'APT-USD', 'ARB-USD', 'OP-USD', 'IMX-USD', 'INJ-USD', 'SUI-USD',
              'ATOM-USD', 'HBAR-USD', 'LTC-USD', 'BCH-USD', 'AAVE-USD', 'UNI-USD', 'CRV-USD', 'LDO-USD', 'GRT-USD',
              'FIL-USD', 'ICP-USD', 'QNT-USD', 'STX-USD', 'FLR-USD', 'RENDER-USD', 'FET-USD', 'WLD-USD', 'TIA-USD', 'SEI-USD',
              'ETC-USD', 'ONDO-USD', 'ALGO-USD', 'ENA-USD', 'VET-USD', 'POL-USD', 'BONK-USD', 'PEPE-USD', 'SHIB-USD',
              'FLOKI-USD', 'WIF-USD', 'JASMY-USD', 'XLM-USD', 'TON-USD'}

def get_threshold(symbol):
    if symbol in LARGE_CAPS: return 0.01  # 1%
    elif symbol in MID_CAPS: return 0.03  # 3%
    else: return 0.04                     # 4%

DUMP_THRESHOLD = 0.05       # Paracadute: -5% dal picco
MIN_PEAK_FOR_DUMP = 0.20    # Il paracadute si attiva solo se il pump supera il +20%

EXCHANGE = ccxt_async.coinbase({'enableRateLimit': True})

SYMBOLS = [
    # --- Small / micro cap (soglia 4%) ---
    '1INCH-USD', '2Z-USD', 'A8-USD', 'ABT-USD', 'ACH-USD', 'ACS-USD', 'AERO-USD', 'AERGO-USD', 'AGLD-USD', 'AI-USD', 
    'AIOZ-USD', 'AKT-USD', 'ALCX-USD', 'ALEO-USD', 'ALEPH-USD', 'ALICE-USD', 'AMP-USD', 'ANKR-USD', 'APE-USD', 'API3-USD', 
    'ARKM-USD', 'ARPA-USD', 'ASM-USD', 'AST-USD', 'ATH-USD', 'AUCTION-USD', 'AUDIO-USD', 'AURORA-USD', 'AVNT-USD', 'AVT-USD', 
    'AWE-USD', 'AXS-USD', 'B3-USD', 'BADGER-USD', 'BAL-USD', 'BAND-USD', 'BAT-USD', 'BEAM-USD', 'BERA-USD', 
    'BICO-USD', 'BIGTIME-USD', 'BLUR-USD', 'BLZ-USD', 'BNT-USD', 'BOBA-USD', 'BTRST-USD', 'C98-USD', 
    'CELR-USD', 'CHZ-USD', 'CLANKER-USD', 'COMP-USD', 'COOKIE-USD', 'COTI-USD', 'COW-USD', 'CRO-USD', 'CTSI-USD', 'CVC-USD', 
    'CVX-USD', 'DASH-USD', 'DEGEN-USD', 'DIA-USD', 'DIMO-USD', 'DOGINME-USD', 'DOLO-USD', 'DRIFT-USD', 
    'EDGE-USD', 'EGLD-USD', 'EIGEN-USD', 'ELA-USD', 'ENS-USD', 'EUL-USD', 'FAI-USD', 'FARM-USD', 'FIDA-USD', 'FLOW-USD', 
    'FLUID-USD', 'FORT-USD', 'FORTH-USD', 'GFI-USD', 'GHST-USD', 'GIGA-USD', 'GLM-USD', 'GMT-USD', 'GODS-USD', 
    'GRASS-USD', 'GST-USD', 'GTC-USD', 'HFT-USD', 'HIGH-USD', 'HNT-USD', 'HONEY-USD', 'HOPR-USD', 'HYPE-USD', 
    'ILV-USD', 'IMU-USD', 'IO-USD', 'IP-USD', 'JTO-USD', 'KAITO-USD', 'KARRAT-USD', 'KAVA-USD', 
    'KERNEL-USD', 'KNC-USD', 'KRL-USD', 'KSM-USD', 'KTA-USD', 'L3-USD', 'LA-USD', 'LAYER-USD', 'LCX-USD', 
    'LPT-USD', 'LQTY-USD', 'LRDS-USD', 'MAGIC-USD', 'MANA-USD', 'MASK-USD', 'MATH-USD', 'MDT-USD', 
    'METIS-USD', 'MINA-USD', 'MLN-USD', 'MNDE-USD', 'MOG-USD', 'MON-USD', 'MOODENG-USD', 'MORPHO-USD', 
    'MSOL-USD', 'NCT-USD', 'NEON-USD', 'NKN-USD', 'NMR-USD', 'OCEAN-USD', 'OGN-USD', 
    'ORCA-USD', 'OSMO-USD', 'OXT-USD', 'PENDLE-USD', 'PENGU-USD', 'PERP-USD', 'PLUME-USD', 'PNG-USD', 'PNUT-USD', 
    'POLS-USD', 'POND-USD', 'POPCAT-USD', 'POWR-USD', 'PRCL-USD', 'PRIME-USD', 'PRO-USD', 'PROMPT-USD', 'PROVE-USD', 
    'PUMP-USD', 'PUNDIX-USD', 'PYR-USD', 'PYTH-USD', 'QI-USD', 'RAD-USD', 'RARE-USD', 'RARI-USD', 'RAY-USD', 'RED-USD', 
    'REQ-USD', 'REZ-USD', 'RLC-USD', 'RLS-USD', 'ROSE-USD', 'RPL-USD', 'RSC-USD', 'RSR-USD', 'SAFE-USD', 'SAND-USD', 
    'SD-USD', 'SENT-USD', 'SHDW-USD', 'SHPING-USD', 'SKL-USD', 'SKY-USD', 'SNX-USD', 'SPA-USD', 'SPELL-USD', 
    'SPK-USD', 'SPX-USD', 'SQD-USD', 'STG-USD', 'STORJ-USD', 'STRK-USD', 'SUKU-USD', 'SUPER-USD', 'SUSHI-USD', 'SWELL-USD', 
    'SWFTC-USD', 'SXT-USD', 'SYRUP-USD', 'T-USD', 'TNSR-USD', 'TOSHI-USD', 'TRAC-USD', 'TRB-USD', 
    'TREE-USD', 'TRUMP-USD', 'TURBO-USD', 'UMA-USD', 'VELO-USD', 'VOXEL-USD', 'VTHO-USD', 'VVV-USD', 'W-USD', 
    'WAL-USD', 'WLFI-USD', 'XAN-USD', 'XCN-USD', 'XPL-USD', 'XTZ-USD', 'XYO-USD', 'YFI-USD', 
    'ZAMA-USD', 'ZEN-USD', 'ZK-USD', 'ZKC-USD', 'ZORA-USD', 'ZRO-USD', 'ZRX-USD',
    
    # --- Mid cap (soglia 3%) ---
    'AVAX-USD', 'LINK-USD', 'DOT-USD', 'NEAR-USD', 'APT-USD', 'ARB-USD', 'OP-USD', 'IMX-USD', 'INJ-USD', 'SUI-USD',
    'ATOM-USD', 'HBAR-USD', 'LTC-USD', 'BCH-USD', 'AAVE-USD', 'UNI-USD', 'CRV-USD', 'LDO-USD', 'GRT-USD', 'FIL-USD', 
    'ICP-USD', 'QNT-USD', 'STX-USD', 'FLR-USD', 'RENDER-USD', 'FET-USD', 'WLD-USD', 'TIA-USD', 'SEI-USD', 'ETC-USD', 
    'ONDO-USD', 'ALGO-USD', 'ENA-USD', 'VET-USD', 'POL-USD', 'BONK-USD', 'PEPE-USD', 'SHIB-USD', 'FLOKI-USD', 
    'WIF-USD', 'JASMY-USD', 'XLM-USD', 'TON-USD',
    
    # --- Large cap (soglia 1%) ---
    'BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD', 'DOGE-USD'
]

# ===== TELEGRAM =====
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ===== STATO DEL BOT (In RAM) =====
bot_active = True
limit_mode = False          # False = FOMO illimitata, True = Max 2 alert ogni 4 ore
parachute_active = True     # True = Paracadute attivo (sopra il 20%), False = Spento via comando

alert_history = {}          # Storico orari alert 24h
last_prices = {}            # Prezzo di riferimento per lo scatto successivo
last_volumes = {}           # Volume precedente per calcolare i dollari nei 5 min
pump_start_prices = {}      # Prezzo di partenza del pump (1° alert)
fomo_peaks = {}             # Picchi massimi per il paracadute

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

def extract_usd_volume(ticker, current_price):
    q_vol = ticker.get('quoteVolume')
    if q_vol is not None and q_vol > 0:
        return float(q_vol)
    b_vol = ticker.get('baseVolume')
    if b_vol is not None and b_vol > 0 and current_price:
        return float(b_vol) * float(current_price)
    return None

def get_btc_change(tickers):
    """Calcola la variazione di BTC nelle 24h per fare il confronto con il mercato."""
    btc_ticker = tickers.get('BTC/USD')
    if btc_ticker and btc_ticker.get('percentage') is not None:
        return float(btc_ticker['percentage'])
    return None

def analyze_liquidity_and_volume(symbol, ticker, current_vol_24h, prev_vol_24h, current_price):
    """Analisi non invasiva della liquidità (Spread + Dollari nei 5 min) per le Small Cap."""
    if symbol in LARGE_CAPS or symbol in MID_CAPS:
        return ""
    
    notes = []
    
    # 1. Controllo Spread Bid/Ask
    bid = ticker.get('bid')
    ask = ticker.get('ask')
    if bid and ask and bid > 0:
        spread_pct = ((ask - bid) / bid) * 100
        if spread_pct >= 1.5:
            notes.append(f"🚨 *Spread alto ({spread_pct:.1f}%)* - Rischio illiquidità")
        elif spread_pct >= 0.8:
            notes.append(f"⚠️ Spread: {spread_pct:.1f}%")

    # 2. Dollari reali entrati negli ultimi 5 minuti
    if current_vol_24h is not None and prev_vol_24h is not None and current_vol_24h > prev_vol_24h:
        vol_5m = current_vol_24h - prev_vol_24h
        if vol_5m < 1000:
            notes.append(f"⚠️ Movimento leggero (soli *{fmt_price(vol_5m)}$* in 5m)")
        elif vol_5m >= 15000:
            notes.append(f"🐳 *Forte pressione d'acquisto* (*+{fmt_price(vol_5m)}$* in 5m)")
            
    return ("\n" + " | ".join(notes)) if notes else ""

def check_and_record_alert(symbol, now, prev_price):
    history = alert_history.get(symbol, [])
    cutoff_24h = now - timedelta(hours=24)
    history = [t for t in history if t > cutoff_24h]
    
    if len(history) == 0:
        pump_start_prices[symbol] = prev_price
        fomo_peaks.pop(symbol, None)
    
    if limit_mode:
        cutoff_4h = now - timedelta(hours=4)
        alerts_last_4h = sum(1 for t in history if t > cutoff_4h)
        if alerts_last_4h >= 2:
            alert_history[symbol] = history
            return False, len(history)
            
    history.append(now)
    alert_history[symbol] = history
    return True, len(history)

def get_active_24h_count(symbol, now):
    cutoff_24h = now - timedelta(hours=24)
    history = [t for t in alert_history.get(symbol, []) if t > cutoff_24h]
    if history:
        alert_history[symbol] = history
    else:
        alert_history.pop(symbol, None)
        pump_start_prices.pop(symbol, None)
        fomo_peaks.pop(symbol, None)
    return len(history)

# ===== CICLO CONTROLLO ASINCRONO =====
async def check_all_symbols():
    global SYMBOLS
    
    ccxt_symbols = [s.replace('-', '/') for s in SYMBOLS]
    tickers = None
    
    try:
        tickers = await EXCHANGE.fetch_tickers(ccxt_symbols)
    except Exception as e:
        error_str = str(e)
        if "does not have market symbol" in error_str:
            bad_ccxt_sym = error_str.split("symbol ")[-1].strip()
            bad_sym = bad_ccxt_sym.replace('/', '-')
            if bad_sym in SYMBOLS:
                SYMBOLS.remove(bad_sym)
                ccxt_symbols.remove(bad_ccxt_sym)
                print(f"🗑️ Trovato intruso ({bad_sym}), scartato.")
        return

    if not tickers: return

    now = datetime.now(timezone.utc)
    btc_change = get_btc_change(tickers)

    for symbol in SYMBOLS:
        ticker = tickers.get(symbol.replace('-', '/'))
        if not ticker: continue
        
        current_price = ticker.get('last')
        if current_price is None: continue

        current_vol = extract_usd_volume(ticker, current_price)
        prev_vol = last_volumes.get(symbol)
        if current_vol is not None:
            last_volumes[symbol] = current_vol

        active_alerts = get_active_24h_count(symbol, now)

        # --- PARACADUTE ANTI-DUMP (Solo se attivo, pump > 20% e >= 2 alert) ---
        if parachute_active and active_alerts >= 2 and symbol in fomo_peaks:
            peak_data = fomo_peaks[symbol]
            start_p = pump_start_prices.get(symbol, peak_data['peak'])
            total_gain_from_start = (peak_data['peak'] - start_p) / start_p if start_p > 0 else 0
            
            # Si attiva solo se il picco ha superato il +20% dall'inizio
            if total_gain_from_start >= MIN_PEAK_FOR_DUMP:
                if current_price > peak_data['peak']:
                    peak_data['peak'] = current_price
                elif not peak_data['notified']:
                    drop = (peak_data['peak'] - current_price) / peak_data['peak']
                    if drop >= DUMP_THRESHOLD:
                        peak_data['notified'] = True
                        dump_msg = (f"🪂 *PARACADUTE {symbol}*: -{drop*100:.2f}% dal picco!\n"
                                    f"📉 Massimo: {fmt_price(peak_data['peak'])} ➔ Ora: {fmt_price(current_price)} USD\n"
                                    f"ℹ️ Aveva fatto *{active_alerts} alert* (Pump totale superava il +{total_gain_from_start*100:.1f}%).\n"
                                    f"🕒 {now.strftime('%H:%M')} UTC")
                        asyncio.create_task(asyncio.to_thread(send_telegram, dump_msg))

        # --- LOGICA DI SALITA A GRADINI ---
        if symbol in last_prices:
            prev_price = last_prices[symbol]
            if prev_price > 0:
                change = (current_price - prev_price) / prev_price
                threshold = get_threshold(symbol)

                if change >= threshold:
                    allowed, count_24h = check_and_record_alert(symbol, now, prev_price)
                    
                    prev_peak = fomo_peaks.get(symbol, {}).get('peak', 0)
                    fomo_peaks[symbol] = {'peak': max(current_price, prev_peak), 'notified': False}
                    
                    if allowed:
                        label = "large cap" if symbol in LARGE_CAPS else ("mid cap" if symbol in MID_CAPS else "small cap")
                        mode_tag = " [Max 2/4h]" if limit_mode else ""
                        
                        start_p = pump_start_prices.get(symbol, prev_price)
                        tot_change = ((current_price - start_p) / start_p) * 100 if start_p > 0 else change * 100
                        tot_str = f"\n🚀 *Totale da inizio FOMO:* +{tot_change:.2f}%" if count_24h > 1 else ""
                        
                        # Confronto Bitcoin
                        btc_note = ""
                        if symbol != 'BTC-USD' and btc_change is not None:
                            if btc_change < 0.5:
                                btc_note = f" (BTC: {btc_change:+.1f}% ➔ 🔥 *Vera FOMO isolata!*)"
                            else:
                                btc_note = f" (BTC: {btc_change:+.1f}%)"

                        liquidity_str = analyze_liquidity_and_volume(symbol, ticker, current_vol, prev_vol, current_price)

                        msg = (f"🟢 *{symbol}* +{change*100:.2f}% [{label}]{mode_tag}{btc_note}\n"
                               f"💵 {fmt_price(prev_price)} ➔ {fmt_price(current_price)} USD"
                               f"{tot_str}"
                               f"{liquidity_str}\n"
                               f"🔥 Alert 24h: *#{count_24h}*\n"
                               f"🕒 {now.strftime('%H:%M')} UTC")
                        asyncio.create_task(asyncio.to_thread(send_telegram, msg))
                    
                    last_prices[symbol] = current_price
                elif current_price < prev_price:
                    last_prices[symbol] = current_price
        else:
            last_prices[symbol] = current_price

    # Pulizia RAM aggressiva per Railway a fine ciclo
    gc.collect()

async def main_loop_async():
    global SYMBOLS
    print("Bot avviato con tutte le ottimizzazioni FOMO, Paracadute e Liquidità.")
    
    try:
        ccxt_symbols = [s.replace('-', '/') for s in SYMBOLS]
        tickers = await EXCHANGE.fetch_tickers(ccxt_symbols)
        if tickers:
            for sym in SYMBOLS:
                ticker = tickers.get(sym.replace('/', '-'))
                if ticker and ticker.get('last'):
                    p = ticker['last']
                    last_prices[sym] = p
                    v = extract_usd_volume(ticker, p)
                    if v is not None:
                        last_volumes[sym] = v
            print(f"✅ Pre-caricamento completato. {len(last_prices)} crypto monitorate.")
    except Exception as e:
        print("Errore nel pre-caricamento:", e)

    while True:
        now = datetime.now()
        minutes_to_next = 5 - (now.minute % 5)
        seconds_to_sleep = (minutes_to_next * 60) - now.second
        
        await asyncio.sleep(seconds_to_sleep + 2)
        
        if bot_active:
            try:
                await check_all_symbols()
            except Exception as e:
                print("Errore nel ciclo principale:", e)

# ===== COMANDI TELEGRAM =====
def handle_command(chat_id, text):
    global bot_active, limit_mode, parachute_active, last_prices, alert_history, pump_start_prices, fomo_peaks
    parts = text.strip().lower().split()
    if not parts: return
    cmd = parts[0]

    if cmd in ("/fine", "/stop", "/pausa"):
        bot_active = False
        send_telegram("⏸️ *Bot in pausa a consumo zero.*", chat_id)
    
    elif cmd in ("/inizia", "/ricomincia", "/start"):
        bot_active = True
        last_prices.clear()
        send_telegram("▶️ *Bot riattivato!* Prezzi base azzerati.", chat_id)
    
    elif cmd == "/reset":
        alert_history.clear()
        pump_start_prices.clear()
        fomo_peaks.clear()
        last_prices.clear()
        send_telegram("🧹 *Memoria resettata con successo!* Tutti i conteggi 24h e i picchi sono stati azzerati.", chat_id)
    
    elif cmd == "/paracadute":
        parachute_active = True
        send_telegram("🪂 *Paracadute ATTIVO.*\nSe una crypto supera il +20% e poi crolla del -5%, riceverai l'avviso.", chat_id)

    elif cmd == "/noparacadute":
        parachute_active = False
        send_telegram("🛡️ *Paracadute DISATTIVATO.*\nNessun avviso di crollo dal picco.", chat_id)

    elif cmd in ("/limita", "/limit"):
        limit_mode = True
        send_telegram("🛡️ *Modalità Limitata ATTIVA* (Max 2 alert ogni 4 ore per crypto).", chat_id)
    
    elif cmd in ("/fomo", "/illimitato", "/unlimit"):
        limit_mode = False
        send_telegram("🚀 *Modalità FOMO ATTIVA* (Alert continui a ogni scatto).", chat_id)
    
    elif cmd == "/status":
        stato = "▶️ *Attivo*" if bot_active else "⏸️ *In pausa*"
        modo = "🛡️ *Limitata (2/4h)*" if limit_mode else "🚀 *FOMO illimitata*"
        para = "🪂 *Attivo (>20%)*" if parachute_active else "❌ *Spento*"
        send_telegram(f"Stato: {stato}\nMod.: {modo}\nParacadute: {para}", chat_id)
    
    elif cmd == "/price" and len(parts) >= 2:
        sym = normalize_symbol(parts[1])
        if sym in last_prices:
            now = datetime.now(timezone.utc)
            c24 = get_active_24h_count(sym, now)
            extra = f"\n🚀 Inizio FOMO da: {fmt_price(pump_start_prices[sym])} USD" if c24 > 0 and sym in pump_start_prices else ""
            send_telegram(f"💰 *{sym}* (Base: {fmt_price(last_prices[sym])} USD)\n🔥 Alert 24h: *{c24}*{extra}", chat_id)
        else:
            send_telegram(f"⚠️ Prezzo di {sym} non registrato.", chat_id)
    
    elif cmd == "/top":
        now = datetime.now(timezone.utc)
        classifica = []
        for sym in list(alert_history.keys()):
            cnt = get_active_24h_count(sym, now)
            if cnt > 0:
                classifica.append((sym, cnt))
        classifica.sort(key=lambda x: x[1], reverse=True)
        if not classifica:
            send_telegram("📊 Nessun alert nelle ultime 24 ore.", chat_id)
        else:
            top_list = "\n".join([f"• *{sym}*: {cnt} alert" for sym, cnt in classifica[:10]])
            send_telegram(f"🔥 *Top Crypto in FOMO (24h):*\n{top_list}", chat_id)

    elif cmd == "/help":
        send_telegram(
            "📖 *Comandi Bot:*\n"
            "/fomo o /limita - Cambia modalità alert\n"
            "/paracadute o /noparacadute - Gestisci paracadute crolli\n"
            "/reset - Pulizia totale memoria\n"
            "/top - Classifica FOMO 24h\n"
            "/price BTC - Info su una crypto\n"
            "/status - Stato del bot", chat_id
        )

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
