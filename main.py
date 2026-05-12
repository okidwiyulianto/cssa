import pandas as pd
import yfinance as yf # type: ignore
import ccxt # type: ignore
import ta # type: ignore
import sys

def format_ribuan(angka, desimal=2):
    """Memformat angka menjadi string dengan pemisah koma untuk ribuan dan titik untuk desimal"""
    if desimal == 0:
        return "{:,.0f}".format(angka)
    return "{:,.2f}".format(angka)

def get_crypto_data(symbol, timeframe='15m', limit=300):
    try:
        exchange = ccxt.binance()
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return df
    except:
        return None

def _fetch_yf(symbol, timeframe):
    """Helper: ambil data yfinance untuk satu simbol dan timeframe tertentu."""
    ticker = yf.Ticker(symbol)
    if timeframe == '4h':
        # yfinance tidak mendukung 4h langsung, ambil 1h lalu resample ke 4h
        df = ticker.history(period="3mo", interval="1h")
        if df.empty:
            return None
        df.columns = [c.lower() for c in df.columns]
        df = df.resample('4h').agg({
            'open': 'first', 'high': 'max',
            'low': 'min',   'close': 'last',
            'volume': 'sum'
        }).dropna()
    else:
        tf_config = {
            '15m': ('5d',  '15m'),
            '1h':  ('1mo', '1h'),
        }
        period, interval = tf_config.get(timeframe, ('1mo', '1h'))
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            return None
        df.columns = [c.lower() for c in df.columns]
    return df if not df.empty else None

def get_stock_data(symbol, timeframe='15m'):
    """
    Deteksi pasar otomatis:
      1. Coba simbol apa adanya → cocok untuk saham AS/asing (NVDA, QQQ, SPY, TSM, dll.)
         dan simbol IDX yang sudah mengandung '.JK' (BMRI.JK).
      2. Jika kosong/gagal, coba tambahkan '.JK' → fallback untuk saham IDX
         dengan ticker 4 huruf (BBCA, BMRI, TLKM, dll.).
    """
    try:
        # ── Percobaan 1: Simbol apa adanya (US / asing / sudah lengkap) ──
        df = _fetch_yf(symbol, timeframe)
        if df is not None:
            return df

        # ── Percobaan 2: Fallback ke IDX (.JK) ──────────────────────────
        symbol_jk = f"{symbol}.JK"
        df = _fetch_yf(symbol_jk, timeframe)
        return df  # None jika keduanya gagal
    except:
        return None

# ===========================================================
#  FUNGSI UTAMA YANG DIUBAH: analyze_signal
#  Strategi multi-timeframe:
#    TF 4H  → Filter Trend  : EMA(200)
#    TF 15M → Filter Volume : VOL > MA(5)
#    TF 15M → Sinyal Akhir  : RSI(6)
# ===========================================================
def analyze_signal(df_4h, df_15m):
    """
    LANGKAH 1 — Trend Filter (TF 4 Jam, EMA 200)
      - Harga < EMA200  → WAIT, berhenti
      - Harga > EMA200  → lanjut ke Langkah 2

    LANGKAH 2 — Volume Filter (TF 15 Menit, Volume MA 5)
      - Volume < MA(5)  → WAIT, berhenti
      - Volume > MA(5)  → lanjut ke Langkah 3

    LANGKAH 3 — Sinyal Akhir (TF 15 Menit, RSI 6)
      - RSI > 70        → JUAL
      - RSI < 30        → BELI
      - Selain itu      → WAIT
    """

    # ── LANGKAH 1: EMA 200 pada TF 4 Jam ──────────────────
    df_4h = df_4h.copy()
    df_4h['EMA200'] = ta.trend.EMAIndicator(
        close=df_4h['close'], window=200
    ).ema_indicator()

    last_4h = df_4h.iloc[-1]
    ema200  = last_4h['EMA200']
    close_4h = last_4h['close']

    if pd.isna(ema200):
        return "WAIT (Data 4H tidak cukup untuk EMA 200)", None

    if close_4h <= ema200:
        params = {
            'ema200':   ema200,
            'close_4h': close_4h,
            'vol':      None,
            'vol_ma5':  None,
            'rsi':      None,
            'close_15m': None,
        }
        return "WAIT (Harga di Bawah EMA 200 — Tren Turun)", params

    # ── LANGKAH 2: Volume MA(5) pada TF 15 Menit ──────────
    df_15m = df_15m.copy()
    df_15m['VOL_MA5'] = df_15m['volume'].rolling(window=5).mean()

    last_15m  = df_15m.iloc[-1]
    vol       = last_15m['volume']
    vol_ma5   = last_15m['VOL_MA5']

    if pd.isna(vol_ma5):
        return "WAIT (Data 15M tidak cukup untuk VOL MA(5))", None

    if vol <= vol_ma5:
        params = {
            'ema200':    ema200,
            'close_4h':  close_4h,
            'vol':       vol,
            'vol_ma5':   vol_ma5,
            'rsi':       None,
            'close_15m': last_15m['close'],
        }
        return "WAIT (Volume Lemah — Volume < MA(5))", params

    # ── LANGKAH 3: RSI(6) pada TF 15 Menit ───────────────
    df_15m['RSI'] = ta.momentum.RSIIndicator(
        close=df_15m['close'], window=6
    ).rsi()

    last_15m  = df_15m.iloc[-1]   # refresh setelah kolom baru ditambah
    rsi       = last_15m['RSI']
    close_15m = last_15m['close']

    params = {
        'ema200':    ema200,
        'close_4h':  close_4h,
        'vol':       vol,
        'vol_ma5':   vol_ma5,
        'rsi':       rsi,
        'close_15m': close_15m,
    }

    if rsi > 70:
        signal = "JUAL (RSI Overbought > 70)"
    elif rsi < 30:
        signal = "BELI (RSI Oversold < 30)"
    else:
        signal = "WAIT (RSI Netral — Tidak Ada Sinyal)"

    return signal, params

# ===========================================================

def main():
    print("="*60)
    print("Aplikasi Trading Saham dan Kripto")
    print("Dibuat oleh: Oki Dwi Yulianto")
    print("Disclaimer: Aplikasi ini hanya mempermudah trader dalam")
    print("menganalisa, bukan jaminan 100% profit.")
    print("="*60)
    print("Strategi  : EMA(200)/4H → VOL MA(5)/15M → RSI(6)/15M")
    print("(Ketik 'exit' atau '0' untuk keluar)")

    while True:
        try:
            user_input = input("\nMasukan ticker (Contoh: BTC/USDT atau BMRI): ")
            ticker = user_input.upper().strip()

            if ticker in ['EXIT', '0']:
                print("Program ditutup. Terima kasih!")
                break

            is_crypto = "/" in ticker

            print(f"Mengambil data 4H untuk {ticker}...")
            df_4h = get_crypto_data(ticker, timeframe='4h', limit=300) if is_crypto else get_stock_data(ticker, timeframe='4h')

            print(f"Mengambil data 15M untuk {ticker}...")
            df_15m = get_crypto_data(ticker, timeframe='15m', limit=300) if is_crypto else get_stock_data(ticker, timeframe='15m')

            if df_4h is None or df_4h.empty:
                print(f"Data 4H '{ticker}' tidak ditemukan.")
                continue
            if df_15m is None or df_15m.empty:
                print(f"Data 15M '{ticker}' tidak ditemukan.")
                continue

            signal, p = analyze_signal(df_4h, df_15m)

            print(f"\n------------------ HASIL ANALISA {ticker} ------------------")

            if p is not None:
                tf_label = "4H " if p['close_15m'] is None else "4H "
                print(f"EMA(200)/4H   : {format_ribuan(p['ema200'])}")
                print(f"Harga/4H      : {format_ribuan(p['close_4h'])}")

                if p['vol'] is not None:
                    print(f"VOL/15M       : {format_ribuan(p['vol'], 0)}; MA(5) = {format_ribuan(p['vol_ma5'], 0)}")

                if p['rsi'] is not None:
                    print(f"RSI(6)/15M    : {format_ribuan(p['rsi'])}")
                    print(f"Harga/15M     : {format_ribuan(p['close_15m'])}")

            print(f"Sinyal        : {signal}")
            print("-" * 60)

        except (EOFError, KeyboardInterrupt):
            print("\nProgram ditutup. Terima kasih!")
            break

if __name__ == "__main__":
    main()
