import pytz
import pandas as pd
import yfinance as yf
import ccxt
import ta
from datetime import datetime, timedelta

# Nama hari dalam Bahasa Indonesia
HARI_ID = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']

def format_ribuan(angka, desimal=2):
    """Memformat angka menjadi string dengan pemisah ribuan."""
    if desimal == 0:
        return "{:,.0f}".format(angka)
    return "{:,.2f}".format(angka)

def _format_timestamp(ts):
    """Format timestamp ke string WIB yang mudah dibaca."""
    if ts is None:
        return "N/A"
    try:
        wib = pytz.timezone('Asia/Jakarta')
        if hasattr(ts, 'tzinfo') and ts.tzinfo is not None:
            ts = ts.astimezone(wib)
        return ts.strftime('%d-%b-%Y %H:%M WIB')
    except Exception:
        return str(ts)

# ===========================================================
#  CEK JAM PASAR
# ===========================================================
def check_market_hours(market_type):
    """
    Memeriksa apakah pasar sedang buka atau tutup.
    Returns:
        (is_open: bool, next_open_str: str | None)
        next_open_str hanya berisi nilai jika pasar sedang tutup.
    """
    if market_type == 'crypto':
        return True, None

    wib  = pytz.timezone('Asia/Jakarta')
    now  = datetime.now(wib)
    wd   = now.weekday()               # 0=Senin … 6=Minggu
    cur  = now.hour * 60 + now.minute  # menit sejak tengah malam

    if market_type == 'IDX':
        # IDX: Senin–Jumat, 09:00–15:30 WIB
        open_m  = 9 * 60          # 540
        close_m = 15 * 60 + 30    # 930

        if wd < 5 and open_m <= cur < close_m:
            return True, None

        # Tentukan kapan pasar buka berikutnya
        if wd < 5 and cur < open_m:
            # Hari kerja, tapi belum buka hari ini
            next_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
        else:
            # Sudah tutup atau hari libur/akhir pekan
            if wd == 4:   days_add = 3  # Jumat   -> Senin
            elif wd == 5: days_add = 2  # Sabtu   -> Senin
            elif wd == 6: days_add = 1  # Minggu  -> Senin
            else:         days_add = 1  # Sen–Kam -> hari berikutnya
            next_open = (now + timedelta(days=days_add)).replace(
                hour=9, minute=0, second=0, microsecond=0)

        label = HARI_ID[next_open.weekday()]
        return False, f"{label}, {next_open.strftime('%d %b %Y')} pukul 09:00 WIB"

    if market_type == 'US':
        # Nasdaq/NYSE: Senin–Jumat, 09:30–16:00 ET  =  21:30–04:00 WIB (hari berikutnya)
        open_m  = 21 * 60 + 30   # 1290
        close_m = 4  * 60        # 240

        # Sesi sore (21:30 ke atas): Senin–Jumat (wd 0–4)
        evening = (wd <= 4) and (cur >= open_m)
        # Sesi dini hari (sebelum 04:00): Selasa–Sabtu (wd 1–5)
        morning = (1 <= wd <= 5) and (cur < close_m)

        if evening or morning:
            return True, None

        # Tentukan kapan pasar buka berikutnya (21:30 WIB)
        if wd <= 4 and cur < open_m:
            # Hari kerja, sesi belum dimulai hari ini
            next_open = now.replace(hour=21, minute=30, second=0, microsecond=0)
        else:
            if wd == 4:   days_add = 3  # Jumat siang/malam  -> Senin
            elif wd == 5: days_add = 2  # Sabtu (setelah 04) -> Senin
            elif wd == 6: days_add = 1  # Minggu             -> Senin
            else:         days_add = 1  # Sen–Kam siang      -> hari berikutnya
            next_open = (now + timedelta(days=days_add)).replace(
                hour=21, minute=30, second=0, microsecond=0)

        label = HARI_ID[next_open.weekday()]
        return False, f"{label}, {next_open.strftime('%d %b %Y')} pukul 21:30 WIB"

    # Pasar tidak dikenali → biarkan lanjut
    return True, None

# ===========================================================
#  RESOLUSI SIMBOL & DETEKSI PASAR
# ===========================================================
def resolve_stock_symbol(symbol):
    """
    Menentukan simbol yang valid dan jenis pasarnya.
    Prioritas deteksi:
      0. Jika ticker sudah berakhiran '.JK'  -> langsung pasar IDX (tidak dicoba US)
      1. Coba simbol apa adanya              -> pasar US/asing (NVDA, QQQ, SPY, WDC, TSM …)
      2. Coba simbol + '.JK'                 -> pasar IDX       (BBCA, BMRI, TLKM …)
    Returns: (resolved_symbol, market_type) atau (None, None) jika tidak ditemukan.
    """
    # Prioritas 0: ticker sudah mengandung '.JK' -> langsung IDX
    if symbol.endswith('.JK'):
        try:
            df = yf.Ticker(symbol).history(period='5d', interval='1h')
            if not df.empty:
                return symbol, 'IDX'
        except Exception:
            pass
        return None, None  # .JK tapi tidak ditemukan, jangan fallback ke US

    # Prioritas 1: coba sebagai saham US/asing
    try:
        df = yf.Ticker(symbol).history(period='5d', interval='1h')
        if not df.empty:
            return symbol, 'US'
    except Exception:
        pass

    # Prioritas 2: fallback ke IDX dengan tambahan '.JK'
    try:
        symbol_jk = f"{symbol}.JK"
        df = yf.Ticker(symbol_jk).history(period='5d', interval='1h')
        if not df.empty:
            return symbol_jk, 'IDX'
    except Exception:
        pass

    return None, None

# ===========================================================
#  AMBIL DATA
# ===========================================================
def get_crypto_data(symbol, timeframe='15m', limit=300):
    try:
        exchange = ccxt.binance()
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return df
    except Exception:
        return None

def _fetch_yf(symbol, timeframe):
    """
    Mengambil data yfinance untuk simbol dan timeframe yang sudah diketahui.
    Timestamp index disimpan sebagai kolom.
    """
    try:
        ticker = yf.Ticker(symbol)

        if timeframe == '4h':
            df = ticker.history(period='3mo', interval='1h')
            if df.empty:
                return None
            df.columns = [c.lower() for c in df.columns]
            df = df.resample('4h').agg({
                'open': 'first', 'high': 'max',
                'low': 'min',   'close': 'last',
                'volume': 'sum'
            }).dropna()
        else:
            tf_cfg = {'15m': ('5d', '15m'), '1h': ('1mo', '1h')}
            period, interval = tf_cfg.get(timeframe, ('1mo', '1h'))
            df = ticker.history(period=period, interval=interval)
            if df.empty:
                return None
            df.columns = [c.lower() for c in df.columns]

        if df.empty:
            return None

        df = df.copy()
        df['timestamp'] = df.index
        df = df.reset_index(drop=True)
        return df
    except Exception:
        return None

def get_stock_data(resolved_symbol, timeframe='15m'):
    """Mengambil data saham untuk simbol yang sudah di-resolve."""
    return _fetch_yf(resolved_symbol, timeframe)

# ===========================================================
#  ANALISA SINYAL (multi-timeframe)
#  TF 4H  → Filter Trend  : EMA(200)
#  TF 15M → Filter Volume : VOL > MA(5)
#  TF 15M → Sinyal Akhir  : RSI(6)
# ===========================================================
def analyze_signal(df_4h, df_15m):
    # -- LANGKAH 1: EMA 200 pada TF 4 Jam --
    df_4h = df_4h.copy()
    df_4h['EMA200'] = ta.trend.EMAIndicator(
        close=df_4h['close'], window=200
    ).ema_indicator()

    last_4h  = df_4h.iloc[-1]
    ema200   = last_4h['EMA200']
    close_4h = last_4h['close']
    ts_4h    = last_4h.get('timestamp', None)

    if pd.isna(ema200):
        return "WAIT (Data 4H tidak cukup untuk EMA 200)", None

    if close_4h <= ema200:
        return "WAIT (Harga di Bawah EMA 200 - Tren Turun)", {
            'ema200': ema200, 'close_4h': close_4h, 'ts_4h': ts_4h,
            'vol': None, 'vol_ma5': None,
            'rsi': None, 'close_15m': None, 'ts_15m': None,
        }

    # -- LANGKAH 2: Volume MA(5) pada TF 15 Menit --
    df_15m = df_15m.copy()
    df_15m['VOL_MA5'] = df_15m['volume'].rolling(window=5).mean()

    last_15m = df_15m.iloc[-1]
    vol      = last_15m['volume']
    vol_ma5  = last_15m['VOL_MA5']
    ts_15m   = last_15m.get('timestamp', None)

    if pd.isna(vol_ma5):
        return "WAIT (Data 15M tidak cukup untuk VOL MA(5))", None

    if vol <= vol_ma5:
        return "WAIT (Volume Lemah - Volume <= MA(5))", {
            'ema200': ema200, 'close_4h': close_4h, 'ts_4h': ts_4h,
            'vol': vol, 'vol_ma5': vol_ma5,
            'rsi': None, 'close_15m': last_15m['close'], 'ts_15m': ts_15m,
        }

    # -- LANGKAH 3: RSI(6) pada TF 15 Menit --
    df_15m['RSI'] = ta.momentum.RSIIndicator(
        close=df_15m['close'], window=6
    ).rsi()

    last_15m  = df_15m.iloc[-1]
    rsi       = last_15m['RSI']
    close_15m = last_15m['close']
    ts_15m    = last_15m.get('timestamp', None)

    params = {
        'ema200': ema200, 'close_4h': close_4h, 'ts_4h': ts_4h,
        'vol': vol, 'vol_ma5': vol_ma5,
        'rsi': rsi, 'close_15m': close_15m, 'ts_15m': ts_15m,
    }

    if rsi > 70:
        signal = "JUAL (RSI Overbought > 70)"
    elif rsi < 30:
        signal = "BELI (RSI Oversold < 30)"
    else:
        signal = "WAIT (RSI Netral - Tidak Ada Sinyal)"

    return signal, params

# ===========================================================
#  MAIN
# ===========================================================
def main():
    print("=" * 60)
    print("Aplikasi Trading Saham dan Kripto")
    print("Dibuat oleh: Oki Dwi Yulianto")
    print("Disclaimer: Aplikasi ini hanya mempermudah trader dalam")
    print("menganalisa, bukan jaminan 100% profit.")
    print("=" * 60)
    print("Strategi  : EMA(200)/4H -> VOL MA(5)/15M -> RSI(6)/15M")
    print("Data delay: +-15 menit (yfinance free tier)")
    print()
    print("JAM PASAR (WIB):")
    print("  IDX    : Senin-Jumat  09:00 - 15:30")
    print("  Nasdaq : Senin-Jumat  21:30 - 04:00 (hari berikutnya)")
    print("  NYSE   : Senin-Jumat  21:30 - 04:00 (hari berikutnya)")
    print("  Crypto : 24 jam / 7 hari")
    print()
    print("(Ketik 'exit' atau '0' untuk keluar)")

    while True:
        try:
            print("-" * 60)
            print("\nKetikan ticker atau simbolnya.")
            print("Khusus untuk pasar IDX, tambahkan sufiks .JK setelah ticker")
            print("Contoh ticker: BTC/USDT, NVDA, QQQ, BMRI.JK, BBRI.JK")
            user_input = input("\nMasukan ticker : ")
            ticker = user_input.upper().strip()

            if ticker in ['EXIT', '0']:
                print("Program ditutup. Terima kasih!")
                break

            is_crypto = "/" in ticker

            # ── Deteksi pasar & cek jam buka ─────────────────────────────
            if is_crypto:
                market_type     = 'crypto'
                resolved_symbol = ticker
            else:
                print(f"Mendeteksi pasar untuk {ticker}...")
                resolved_symbol, market_type = resolve_stock_symbol(ticker)

                if resolved_symbol is None:
                    print(f"Ticker '{ticker}' tidak ditemukan. "
                          f"Gunakan '/' untuk Kripto (Contoh: ETH/USDT).")
                    continue

            is_open, next_open_str = check_market_hours(market_type)

            if not is_open:
                nama_pasar = "IDX" if market_type == "IDX" else "Nasdaq/NYSE"
                print(f"\nSaat ini pasar {nama_pasar} sedang tutup.")
                print(f"Buka kembali: {next_open_str}")
                continue

            # ── Ambil data & analisa ──────────────────────────────────────
            print(f"Mengambil data 4H untuk {ticker}...")
            df_4h = (get_crypto_data(ticker, timeframe='4h', limit=300)
                     if is_crypto else get_stock_data(resolved_symbol, timeframe='4h'))

            print(f"Mengambil data 15M untuk {ticker}...")
            df_15m = (get_crypto_data(ticker, timeframe='15m', limit=300)
                      if is_crypto else get_stock_data(resolved_symbol, timeframe='15m'))

            if df_4h is None or df_4h.empty:
                print(f"Data 4H '{ticker}' tidak berhasil diambil.")
                continue
            if df_15m is None or df_15m.empty:
                print(f"Data 15M '{ticker}' tidak berhasil diambil.")
                continue

            signal, p = analyze_signal(df_4h, df_15m)

            # ── Tampilkan hasil ───────────────────────────────────────────
            print(f"\n------------------ HASIL ANALISA {ticker} ------------------")

            if p is not None:
                print(f"[4H] Candle    : {_format_timestamp(p.get('ts_4h'))}")
                print(f"[4H] EMA(200)  : {format_ribuan(p['ema200'])}")
                print(f"[4H] Harga     : {format_ribuan(p['close_4h'])}")

                if p['vol'] is not None:
                    print(f"[15M] Candle   : {_format_timestamp(p.get('ts_15m'))}")
                    print(f"[15M] Harga    : {format_ribuan(p['close_15m'])}")
                    print(f"[15M] VOL      : {format_ribuan(p['vol'], 0)}"
                          f"  | MA(5) = {format_ribuan(p['vol_ma5'], 0)}")

                if p['rsi'] is not None:
                    print(f"[15M] RSI(6)   : {format_ribuan(p['rsi'])}")

            print(f"Sinyal         : {signal}")
            print("-" * 60)

        except (EOFError, KeyboardInterrupt):
            print("\nProgram ditutup. Terima kasih!")
            break

if __name__ == "__main__":
    main()
