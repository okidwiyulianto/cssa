# 📈 Crypto & Stock Signal Analyzer
**Aplikasi Analisis Sinyal Trading Otomatis berbasis Python.**

Aplikasi ini dirancang untuk mempermudah pemula seperti saya, yang belum memiliki pengetahuan analisa teknik atau yang ingin investasi atau mulai trading, aplikasi ini membantu memberikan sinyal cepat (**BELI**, **JUAL**, atau **WAIT**) bagi instrumen Saham maupun Kripto. Menggunakan kombinasi indikator teknikal populer yang telah disempurnakan untuk akurasi yang lebih baik dalam analisa teknikal multi timeframe 4 jam dan 15 menit.

Aplikasi ini sangat sederhana sekali dan membutuhkan pengembangan lebih lanjut.

Aplikasi ini cocok digunakan untuk Day Trading atau Swing Trading, tidak untuk Scalping.

Saya buat dua strategi analisis yang diambil dari berbagai video di YouTube kemudian saya campurkan hasilnya adalah:
1. Multi Timeframe Analysis
2. Vacuum Model Analysis

Dibuat dengan 💖 oleh **Oki Dwi Yulianto** untuk kalian yang pengen memulai investasi atau trading. Jangan digunakan untuk komersil ya?

---

## 🚀 Fitur Utama
1. Multi Timeframe Analysis
- **Multi-Asset Support:** Mendukung pengecekan ticker Saham (via Yahoo Finance) dan Kripto (via Binance/CCXT).
- **Multi-Timeframe Analysis:** Mendukung analisa candlestick di posisi 4 jam (untuk analisa) dan 15 menit (untuk eksekusi)
- **Logika Terkalibrasi:** Menggunakan parameter indikator yang dioptimalkan:
  - **EMA:** 200.
  - **VOL:** 5.
  - **RSI:** 6 (Sensitif terhadap momentum pendek).
  - **Volume Validation:** Menggunakan Moving Average (MA5) untuk memastikan lonjakan harga didukung partisipasi pasar.
  - **Volume Profile**
- **Output Informatif:** Menampilkan data real-time yang mudah dibaca dengan format ribuan (`1,250.00`).
- **Antarmuka Interaktif:** Konsol yang mudah digunakan dan mendukung perintah keluar cepat.

2. Vacuum Model Analysis
* **Multi-Market Support**: Analisis real-time untuk Binance (Kripto), yfinance (Saham US & IDX).
* **Volume Profile Analysis**: Deteksi otomatis bentuk profil harga (P-Shape, B-Shape, dan D-Shape).
* **The Vacuum Model Strategy**: Mengidentifikasi *Bullish/Bearish Traps* berdasarkan posisi *Point of Control* (POC).
* **Dual-Time Monitoring**: Menampilkan Waktu Sistem (Real-time) dan Waktu Data (Candle Terakhir) dalam format WIB untuk akurasi tinggi.
* **Manajemen Risiko Otomatis**: Kalkulasi otomatis level *Stop Loss* (SL) dan *Take Profit* (TP) berbasis struktur pasar.
* **Market Hours Check**: Fitur deteksi otomatis apakah pasar tujuan sedang buka atau tutup.

---

## 🛠️ Logika Strategi Multi Timeframe Analysis
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

## 🛠️ Logika Strategi Vacum Model Analysis
Strategi ini berfokus pada psikologi trader yang terjebak di area harga tertentu:
```
   1.  Buy (Long Setup):
      * Kondisi: Terbentuk profil B-Shape (akumulasi volume di bawah), menandakan adanya Bearish Trap.
      * Konfirmas: Harga berhasil menembus dan ditutup di atas level Point of Control (POC).
      * Target: Menuju area Low Volume Node (ujung atas range).

   2.  Sell (Short Setup):
      * Kondisi: Terbentuk profil P-Shape (akumulasi volume di atas), menandakan adanya Bullish Trap.
      * Konfirmasi: Harga gagal bertahan dan ditutup di bawah level **Point of Control (POC).
      * Target: Menuju area Low Volume Node (ujung bawah range).

   3.  Wait (Netral):
      * Harga masih berada di area keseimbangan (Balance) atau belum ada penembusan POC yang valid.
```

---

## 📦 Instalasi & Cara Penggunaan

1. **Install Python 3.11.0**
   [Klik di sini](https://www.python.org/downloads/release/python-3110/)

2. **Install Git**
   [Klik di sini](https://git-scm.com/install/windows)

3. **Install Library yang Dibutuhkan**
   ```bash
   pip install -r requirements.txt

4. **Clone Repositori ini:**
   ```bash
   git clone https://github.com/okidwiyulianto/cssa.git
   cd cssa

5. **Jalankan Programnya dengan klik 2x pada file Python atau ketikan perintah:**
   ```bash
   python multi-timeframe-analysis.py
   python vacuum-model-analysis.py

---

## 📊 Contoh Tampilan Output Strategi Multi Timeframe Analysis
   ```bash
   ============================================================
   Aplikasi Trading Saham dan Kripto
   Dibuat oleh: Oki Dwi Yulianto
   Disclaimer: Aplikasi ini hanya mempermudah trader dalam
   menganalisa, bukan jaminan 100% profit.
   ============================================================
   Strategi  : EMA(200)/4H -> VOL MA(5)/15M -> RSI(6)/15M
   Data delay: +-15 menit (yfinance free tier)

   JAM PASAR (WIB):
   IDX    : Senin-Jumat  09:00 - 15:30
   Nasdaq : Senin-Jumat  21:30 - 04:00 (hari berikutnya)
   NYSE   : Senin-Jumat  21:30 - 04:00 (hari berikutnya)
   Crypto : 24 jam / 7 hari

   (Ketik 'exit' atau '0' untuk keluar)
   ------------------------------------------------------------

   Ketikan ticker atau simbolnya.
   Khusus untuk pasar IDX, tambahkan sufiks .JK setelah ticker
   Contoh ticker: BTC/USDT, NVDA, QQQ, BMRI.JK, BBRI.JK

   Masukan ticker :
   ```

## 📊 Contoh Tampilan Output Strategi Vacum Model Analysis
   ```bash
   ============================================================
   CRYPTO & STOCK SIGNAL ANALYZER
   Dibuat oleh: Oki Dwi Yulianto | Strategi: Volume Profile
   ============================================================
   Timeframe : 5 Menit (Ideal untuk Scalping/Day Trade)
   Data      : yfinance (Delay 15m) / Binance (Real-time)
   ------------------------------------------------------------

   Masukan ticker (Contoh: BTC/USDT, NVDA, BBCA.JK) :
   ```

## ⚠️ Disclaimer
Aplikasi ini dibuat hanya untuk tujuan edukasi dan alat bantu analisis teknikal. Keputusan investasi sepenuhnya berada di tangan pengguna. Perlu diingat bahwa trading memiliki risiko finansial.
