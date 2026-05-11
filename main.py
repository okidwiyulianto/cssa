import pandas as pd
import yfinance as yf
import ccxt
import ta
import sys

def format_ribuan(angka, desimal=2):
    """Memformat angka menjadi string dengan pemisah koma untuk ribuan dan titik untuk desimal"""
    if desimal == 0:
        return "{:,.0f}".format(angka)
    return "{:,.2f}".format(angka)

def get_crypto_data(symbol):
    try:
        exchange = ccxt.binance()
        # Menggunakan timeframe '1h' (1 jam)
        bars = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=100)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return df
    except:
        return None

def get_stock_data(symbol):
    try:
        if len(symbol) == 4 and symbol.isalpha():
            symbol = f"{symbol}.JK"
        ticker = yf.Ticker(symbol)
        # Menggunakan interval="1h" (1 jam)
        df = ticker.history(period="1mo", interval="1h")
        if df.empty: return None
        df.columns = [c.lower() for c in df.columns]
        return df
    except:
        return None

def analyze_signal(df):
    # 1. Hitung Bollinger Bands (BB = 21, 2)
    indicator_bb = ta.volatility.BollingerBands(close=df["close"], window=21, window_dev=2)
    df['UP'] = indicator_bb.bollinger_hband()
    df['MB'] = indicator_bb.bollinger_mavg()
    df['DN'] = indicator_bb.bollinger_lband()
    
    # 2. Hitung RSI(6)
    df['RSI'] = ta.momentum.RSIIndicator(close=df["close"], window=6).rsi()
    
    # 3. Hitung Volume MA(5)
    df['VOL_MA5'] = df['volume'].rolling(window=5).mean()

    # Ambil baris terakhir
    last = df.iloc[-1]
    
    params = {
        'up': last['UP'],
        'mb': last['MB'],
        'dn': last['DN'],
        'vol': last['volume'],
        'vol_ma5': last['VOL_MA5'],
        'rsi': last['RSI'],
        'close': last['close']
    }
    
    # Logika Final
    if (last['close'] >= last['UP']) and (last['volume'] > last['VOL_MA5']) and (last['RSI'] >= 70):
        signal = "JUAL (Harga >= UP & RSI Overbought)"
    elif (last['close'] < last['MB']) and (last['volume'] > last['VOL_MA5']) and (last['RSI'] >= 65):
        signal = "JUAL (Harga < MB & RSI Tinggi)"
    elif (last['close'] <= last['DN']) and (last['volume'] > last['VOL_MA5']) and (last['RSI'] <= 30):
        signal = "BELI (Harga <= DN & RSI Oversold)"
    elif (last['close'] > last['MB']) and (last['volume'] > last['VOL_MA5']) and (last['RSI'] <= 35):
        signal = "BELI (Harga > MB & RSI Rendah)"
    else:
        signal = "WAIT"
        
    return signal, params

def main():
    print("="*60)
    print("Aplikasi Trading Saham dan Kripto")
    print("Dibuat oleh: Oki Dwi Yulianto")
    print("Disclaimer: Aplikasi ini hanya mempermudah trader dalam menganalisa, bukan jaminan 100% profit.")
    print("="*60)
    print("(Ketik 'exit', atau '0' untuk keluar)")

    while True:
        try:
            user_input = input("\nMasukan ticker (Contoh: BTC/USDT atau BMRI): ")
            ticker = user_input.upper().strip()
            
            if ticker in ['EXIT', '0']:
                print("Program ditutup. Terima kasih!")
                break

            print(f"Sedang menganalisa {ticker} (Timeframe: 1 Jam)...")
            df = get_crypto_data(ticker) if "/" in ticker else get_stock_data(ticker)

            if df is not None and not df.empty:
                signal, p = analyze_signal(df)
                
                print(f"\n-------------------- HASIL ANALISA {ticker} --------------------")
                print(f"BB (21,2)     : UP = {format_ribuan(p['up'])}; MB = {format_ribuan(p['mb'])}; DN = {format_ribuan(p['dn'])}")
                print(f"VOL           : {format_ribuan(p['vol'], 0)}; MA(5) = {format_ribuan(p['vol_ma5'], 0)}")
                print(f"RSI(6)        : {format_ribuan(p['rsi'])}")
                print(f"Harga Terakhir: {format_ribuan(p['close'])}")
                print(f"Sinyal        : {signal}")
                print("-" * 60)
            else:
                print(f"Data '{ticker}' tidak ditemukan. Gunakan '/' untuk Kripto (Contoh: ETH/USDT).")

        except (EOFError, KeyboardInterrupt):
            print("\nProgram ditutup. Terima kasih!")
            break

if __name__ == "__main__":
    main()