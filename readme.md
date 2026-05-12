# 📈 Crypto & Stock Signal Analyzer
**Aplikasi Analisis Sinyal Trading Otomatis berbasis Python.**

Aplikasi ini dirancang untuk memberikan sinyal cepat (**BELI**, **JUAL**, atau **WAIT**) bagi instrumen Saham maupun Kripto. Menggunakan kombinasi indikator teknikal populer yang telah disempurnakan untuk akurasi yang lebih baik dalam analisa teknikal multi timeframe 4 jam dan 15 menit.

Dibuat dengan 💖 oleh **Oki Dwi Yulianto**.

---

## 🚀 Fitur Utama
- **Multi-Asset Support:** Mendukung pengecekan ticker Saham (via Yahoo Finance) dan Kripto (via Binance/CCXT).
- **Multi-Timeframe Analysis:** Mendukung analisa candlestick di posisi 4 jam (untuk analisa) dan 15 menit (untuk eksekusi)
- **Logika Terkalibrasi:** Menggunakan parameter indikator yang dioptimalkan:
  - **EMA:** 200.
  - **VOL:** 5.
  - **RSI:** 6 (Sensitif terhadap momentum pendek).
  - **Volume Validation:** Menggunakan Moving Average (MA5) untuk memastikan lonjakan harga didukung partisipasi pasar.
- **Output Informatif:** Menampilkan data real-time yang mudah dibaca dengan format ribuan (`1,250.00`).
- **Antarmuka Interaktif:** Konsol yang mudah digunakan dan mendukung perintah keluar cepat.

---

## 🛠️ Logika Strategi
Aplikasi ini bekerja dengan memindai kondisi market terkini:
```
    LANGKAH 1 -- Trend Filter (TF 4 Jam, EMA 200)
      - Harga <= EMA200  -> WAIT, berhenti
      - Harga >  EMA200  -> lanjut ke Langkah 2

    LANGKAH 2 -- Volume Filter (TF 15 Menit, Volume MA 5)
      - Volume <= MA(5)  -> WAIT, berhenti
      - Volume >  MA(5)  -> lanjut ke Langkah 3

    LANGKAH 3 -- Sinyal Akhir (TF 15 Menit, RSI 6)
      - RSI > 70         -> JUAL
      - RSI < 30         -> BELI
      - Selain itu       -> WAIT
```

---

## 📦 Instalasi

1. **Clone Repositori ini:**
   ```bash
   git clone [https://github.com/username-anda/nama-repo.git](https://github.com/okidwiyulianto/aplikasi-trading-saham-dan-kripto.git)
   cd nama-repo

2. **Install Library yang Dibutuhkan**
   ```bash
   pip install -r requirements.txt

## 🖥️ Cara Penggunaan
Jalankan aplikasi dengan perintah:
**Cara eksekusi:**
   ```bash
   python main.py
   ```

## 📊 Contoh Tampilan Output
   ```bash
   ------------------ HASIL ANALISA BTC/USDT ------------------
   [4H] Candle    : 1778558400000.0
   [4H] EMA(200)  : 77,194.75
   [4H] Harga     : 81,255.33
   [15M] Candle   : 1778565600000.0
   [15M] Harga    : 81,258.48
   [15M] VOL      : 48  | MA(5) = 76
    Sinyal        : WAIT (Volume Lemah - Volume <= MA(5))
   ------------------------------------------------------------
   ```

## ⚠️ Disclaimer
Aplikasi ini dibuat hanya untuk tujuan edukasi dan alat bantu analisis teknikal. Keputusan investasi sepenuhnya berada di tangan pengguna. Perlu diingat bahwa trading memiliki risiko finansial.
