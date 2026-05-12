import pytz
import pandas as pd
import numpy as np
import yfinance as yf
import ccxt
from datetime import datetime, timedelta

# ===========================================================
#  KONFIGURASI & UTURITAS
# ===========================================================
HARI_ID = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']

def format_ribuan(angka, desimal=2):
    """Memformat angka menjadi string dengan pemisah ribuan."""
    if angka is None: return "N/A"
    if desimal == 0:
        return "{:,.0f}".format(angka)
    return "{:,.2f}".format(angka)

def _format_timestamp(ts):
    """Format timestamp ke string WIB yang mudah dibaca."""
    if ts is None:
        return "N/A"
    try:
        wib = pytz.timezone('Asia/Jakarta')
        # Jika ts sudah punya timezone, konversi ke WIB
        if hasattr(ts, 'tzinfo') and ts.tzinfo is not None:
            ts = ts.astimezone(wib)
        return ts.strftime('%d-%b-%Y %H:%M WIB')
    except Exception:
        return str(ts)

# ===========================================================
#  CEK JAM PASAR
# ===========================================================
def check_market_hours(market_type):
    if market_type == 'crypto':
        return True, None

    wib  = pytz.timezone('Asia/Jakarta')
    now  = datetime.now(wib)
    wd   = now.weekday()               
    cur  = now.hour * 60 + now.minute  

    if market_type == 'IDX':
        open_m  = 9 * 60          
        close_m = 15 * 60 + 30    
        if wd < 5 and open_m <= cur < close_m:
            return True, None
        if wd < 5 and cur < open_m:
            next_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
        else:
            days_add = 3 if wd == 4 else (2 if wd == 5 else 1)
            next_open = (now + timedelta(days=days_add)).replace(hour=9, minute=0, second=0, microsecond=0)
        return False, f"{HARI_ID[next_open.weekday()]}, {next_open.strftime('%d %b %Y')} pukul 09:00 WIB"

    if market_type == 'US':
        open_m  = 21 * 60 + 30   
        close_m = 4  * 60        
        evening = (wd <= 4) and (cur >= open_m)
        morning = (1 <= wd <= 5) and (cur < close_m)
        if evening or morning:
            return True, None
        if wd <= 4 and cur < open_m:
            next_open = now.replace(hour=21, minute=30, second=0, microsecond=0)
        else:
            days_add = 3 if wd == 4 else (2 if wd == 5 else 1)
            next_open = (now + timedelta(days=days_add)).replace(hour=21, minute=30, second=0, microsecond=0)
        return False, f"{HARI_ID[next_open.weekday()]}, {next_open.strftime('%d %b %Y')} pukul 21:30 WIB"

    return True, None

# ===========================================================
#  RESOLUSI SIMBOL
# ===========================================================
def resolve_stock_symbol(symbol):
    if symbol.endswith('.JK'):
        try:
            if not yf.Ticker(symbol).history(period='1d', interval='5m').empty:
                return symbol, 'IDX'
        except: pass
        return None, None  
    try:
        if not yf.Ticker(symbol).history(period='1d', interval='5m').empty:
            return symbol, 'US'
    except: pass
    try:
        symbol_jk = f"{symbol}.JK"
        if not yf.Ticker(symbol_jk).history(period='1d', interval='5m').empty:
            return symbol_jk, 'IDX'
    except: pass
    return None, None

# ===========================================================
#  PENGAMBILAN DATA
# ===========================================================
def get_data(symbol, is_crypto, timeframe='5m', limit=150):
    try:
        if is_crypto:
            exchange = ccxt.binance()
            bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms').dt.tz_localize('UTC').dt.tz_convert('Asia/Jakarta')
            return df
        else:
            df = yf.Ticker(symbol).history(period='3d', interval=timeframe)
            if df.empty: return None
            df.columns = [c.lower() for c in df.columns]
            df['timestamp'] = df.index
            return df.reset_index(drop=True).tail(limit)
    except Exception:
        return None

# ===========================================================
#  STRATEGI THE VACUUM MODEL (CASPER SMC)
# ===========================================================
def analyze_vacuum_model(df, bins=15):
    if df is None or len(df) < 50:
        return "WAIT", None

    recent_df = df.tail(100).copy()
    min_price = recent_df['low'].min()
    max_price = recent_df['high'].max()
    total_range = max_price - min_price
    
    if total_range == 0:
        return "WAIT", None

    # Kalkulasi Volume Profile
    price_bins = np.linspace(min_price, max_price, bins + 1)
    recent_df['price_bin'] = pd.cut(recent_df['close'], bins=price_bins, include_lowest=True)
    profile = recent_df.groupby('price_bin', observed=False)['volume'].sum()

    # Point of Control (POC)
    poc_bin = profile.idxmax()
    poc_price = poc_bin.mid

    # Shape Detection
    if poc_price > (max_price - 0.4 * total_range):
        shape = 'P'
    elif poc_price < (min_price + 0.4 * total_range):
        shape = 'B'
    else:
        shape = 'D'

    last_row = recent_df.iloc[-1]
    prev_row = recent_df.iloc[-2]
    current_close = last_row['close']
    prev_close = prev_row['close']
    ts_data = last_row.get('timestamp', None)

    action = "WAIT"
    sl, tp = None, None
    keterangan = "Menunggu konfirmasi harga menembus POC."

    # Logic: SELL pada P-Shape kegagalan
    if shape == 'P':
        if current_close < poc_price and prev_close >= poc_price:
            action = "SELL (SHORT)"
            keterangan = "P-Shape Breakout Down! Bulls Trapped."
            sl = poc_price * 1.001
            tp = min_price
        elif current_close < poc_price:
            keterangan = "Harga di bawah POC (Momentum sedang berjalan)."

    # Logic: BUY pada B-Shape kegagalan
    elif shape == 'B':
        if current_close > poc_price and prev_close <= poc_price:
            action = "BUY (LONG)"
            keterangan = "B-Shape Breakout Up! Bears Trapped."
            sl = poc_price * 0.999
            tp = max_price
        elif current_close > poc_price:
            keterangan = "Harga di atas POC (Momentum sedang berjalan)."

    params = {
        'ts': ts_data, 'current_price': current_close, 'poc': poc_price,
        'shape': shape, 'sl': sl, 'tp': tp, 'reason': keterangan
    }
    return action, params

# ===========================================================
#  MAIN LOOP
# ===========================================================
def main():
    wib = pytz.timezone('Asia/Jakarta')
    
    print("=" * 60)
    print("CRYPTO & STOCK SIGNAL ANALYZER")
    print("Dibuat oleh: Oki Dwi Yulianto | Strategi: Volume Profile")
    print("=" * 60)
    print("Timeframe : 5 Menit (Ideal untuk Scalping/Day Trade)")
    print("Data      : yfinance (Delay 15m) / Binance (Real-time)")
    print("-" * 60)

    while True:
        try:
            user_input = input("\nMasukan ticker (Contoh: BTC/USDT, NVDA, BBCA.JK) : ")
            ticker = user_input.upper().strip()

            if ticker in ['EXIT', '0']: break
            
            is_crypto = "/" in ticker
            if is_crypto:
                market_type, resolved_symbol = 'crypto', ticker
            else:
                print(f"Mencari pasar untuk {ticker}...")
                resolved_symbol, market_type = resolve_stock_symbol(ticker)
                if not resolved_symbol:
                    print(f"Ticker '{ticker}' tidak ditemukan.")
                    continue

            # Cek jam operasional
            is_open, next_open = check_market_hours(market_type)
            if not is_open:
                print(f"\nPASAR SEDANG TUTUP: {market_type}")
                print(f"Buka kembali: {next_open}")
                continue

            print(f"Mengambil data live...")
            df_5m = get_data(resolved_symbol, is_crypto, timeframe='5m')

            if df_5m is None or df_5m.empty:
                print("Gagal mengambil data. Periksa koneksi atau ticker.")
                continue

            # Analisa
            signal, p = analyze_vacuum_model(df_5m)
            
            # Waktu Sistem (Sekarang)
            waktu_sekarang = datetime.now(wib).strftime('%d-%b-%Y %H:%M:%S WIB')

            # Tampilkan Hasil
            print(f"\n" + "-"*20 + f" HASIL ANALISA {ticker} " + "-"*20)
            print(f"Waktu Sistem   : {waktu_sekarang} (Real-time)")
            
            if p:
                print(f"Waktu Data      : {_format_timestamp(p.get('ts'))} (Candle Terakhir)")
                print(f"Harga Terakhir  : {format_ribuan(p['current_price'])}")
                print(f"Point of Control: {format_ribuan(p['poc'])}")
                print(f"Bentuk Profil   : {p['shape']}-Shape")
                
                print(f"\n>>> SINYAL: {signal} <<<")
                print(f"Keterangan      : {p['reason']}")
                
                if signal in ["BUY (LONG)", "SELL (SHORT)"]:
                    print(f"Take Profit    : {format_ribuan(p['tp'])} (End of Vacuum)")
                    print(f"Stop Loss      : {format_ribuan(p['sl'])} (Tepat di POC)")
                    print("-" * 60)
                    print("SARAN: Gunakan trailing stop per candle untuk mengunci profit.")
            
            print("-" * 60)

        except (EOFError, KeyboardInterrupt):
            print("\nProgram dihentikan.")
            break
        except Exception as e:
            print(f"Terjadi kesalahan: {e}")

if __name__ == "__main__":
    main()