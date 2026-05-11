# 📈 Crypto & Stock Signal Analyzer
**Aplikasi Analisis Sinyal Trading Otomatis berbasis Python.**

Aplikasi ini dirancang untuk memberikan sinyal cepat (**BELI**, **JUAL**, atau **WAIT**) bagi instrumen Saham maupun Kripto. Menggunakan kombinasi indikator teknikal populer yang telah disempurnakan untuk akurasi yang lebih baik dalam timeframe 1 jam.

Dibuat dengan 💖 oleh **Oki Dwi Yulianto**.

---

## 🚀 Fitur Utama
- **Multi-Asset Support:** Mendukung pengecekan ticker Saham (via Yahoo Finance) dan Kripto (via Binance/CCXT).
- **Logika Terkalibrasi:** Menggunakan parameter indikator yang dioptimalkan:
  - **Bollinger Bands:** Periode 21, Std Dev 2.
  - **RSI:** Periode 6 (Sensitif terhadap momentum pendek).
  - **Volume Validation:** Menggunakan Moving Average (MA5) untuk memastikan lonjakan harga didukung partisipasi pasar.
- **Output Informatif:** Menampilkan data real-time yang mudah dibaca dengan format ribuan (`1,250.00`).
- **Antarmuka Interaktif:** Konsol yang mudah digunakan dan mendukung perintah keluar cepat.

---

## 🛠️ Logika Strategi
Aplikasi ini bekerja dengan memindai kondisi market terkini:
1. **Sinyal BELI:** Muncul saat harga berada di area *oversold* (Lower Band) atau mulai memantul dari Middle Band dengan dukungan volume tinggi.
2. **Sinyal JUAL:** Muncul saat harga mencapai area *overbought* (Upper Band) atau menembus ke bawah Middle Band dengan validasi volume.
3. **Sinyal WAIT:** Diberikan saat market tidak memenuhi kriteria teknikal untuk meminimalisir risiko *false signal*.

---

## 📦 Instalasi

1. **Clone Repositori ini:**
   ```bash
   git clone [https://github.com/username-anda/nama-repo.git](https://github.com/okidwiyulianto/aplikasi-trading.git)
   cd nama-repo

2. **Install Library yang Dibutuhkan**
   ```bash
   pip install -r requirements.txt

## 🖥️ Cara Penggunaan
Jalankan aplikasi dengan perintah:
1. **Cara eksekusi:**
   ```bash
   python main.py

## 📊 Contoh Tampilan Output
1. **Tampilan:**
   ```bash
   --- HASIL ANALISA BTC/USDT ---
   BB (21,2)      : UP = 65,420.50; MB = 64,200.00; DN = 62,979.50
   VOL            : 12,450; MA(5) = 8,200
   RSI(6)         : 72.45
   Harga Terakhir : 65,500.00
   Sinyal         : JUAL (Harga >= UP & RSI Overbought)