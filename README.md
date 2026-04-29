# 📊 XAUUSD Scalping Bot — Twelve Data Edition

Bot otomatis untuk memantau **XAUUSD (Gold/USD)** setiap **1 jam** dan mengirimkan **Technical Outlook** langsung ke **Telegram** menggunakan strategi scalping M15.

Menggunakan **Twelve Data API** — 800 request gratis/hari, data real-time, tidak perlu kartu kredit.

---

## ⚙️ Strategi Trading

| Parameter       | Detail                                    |
|----------------|-------------------------------------------|
| Timeframe       | M15 (15 menit)                            |
| Indikator       | RSI(14) + EMA 9/21/50 Crossover + ATR(14) |
| Target TP1      | +$0.50 atau 0.8× ATR (mana yang lebih besar) |
| Target TP2      | +$1.00 atau 1.5× ATR                      |
| Stop Loss       | −$0.60 atau 1.0× ATR                      |
| Support/Resist  | Swing high/low 20 candle terakhir         |
| Session Filter  | Deteksi otomatis sesi Tokyo/London/NY     |
| Jadwal          | Setiap 1 jam otomatis via GitHub Actions  |

---

## 🚀 Setup Deploy (10 Menit)

### Step 1 — Fork repo ini ke akun GitHub kamu

Klik **Fork** di pojok kanan atas halaman ini.

---

### Step 2 — Dapatkan Twelve Data API Key (gratis)

1. Buka [twelvedata.com](https://twelvedata.com) → **Get free API key**
2. Daftar dengan email (tidak perlu kartu kredit)
3. Salin API Key dari dashboard kamu

**Free plan:**
- ✅ 800 API credits/hari
- ✅ Setiap request `/time_series` = 8 credits
- ✅ 800 ÷ 8 = **100 request/hari** — lebih dari cukup untuk 24 alert/hari

---

### Step 3 — Buat Telegram Bot

1. Buka Telegram → cari `@BotFather`
2. Kirim: `/newbot`
3. Ikuti instruksi → beri nama bot (contoh: `XAUUSDScalpingBot`)
4. **Salin Bot Token** yang diberikan (format: `123456:ABC-DEF...`)

**Dapatkan Chat ID:**
1. Kirim pesan apa saja ke bot yang baru kamu buat
2. Buka browser, kunjungi:
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
3. Cari nilai `"id"` di dalam `"chat"` → itu **Chat ID** kamu
4. Bisa juga menggunakan `@userinfobot` untuk mendapatkan Chat ID

---

### Step 4 — Tambahkan Secrets ke GitHub

Buka repo hasil fork → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Tambahkan **3 secret** berikut:

| Secret Name           | Nilai                              |
|----------------------|------------------------------------|
| `TWELVE_DATA_API_KEY` | API Key dari Twelve Data           |
| `TELEGRAM_BOT_TOKEN`  | Token dari @BotFather              |
| `TELEGRAM_CHAT_ID`    | Chat ID Telegram kamu              |

---

### Step 5 — Aktifkan GitHub Actions

1. Buka tab **Actions** di repo kamu
2. Klik **"I understand my workflows, go ahead and enable them"**
3. ✅ Selesai! Bot akan berjalan otomatis setiap jam

---

## 🧪 Test Manual

**Via GitHub Actions:**
1. Buka tab **Actions**
2. Klik **"📊 XAUUSD Scalping Bot — Hourly Alert"**
3. Klik **"Run workflow"** → **"Run workflow"**

**Via terminal lokal:**
```bash
git clone https://github.com/USERNAME/xauusd-scalping-bot.git
cd xauusd-scalping-bot
pip install -r requirements.txt

export TWELVE_DATA_API_KEY="api_key_kamu"
export TELEGRAM_BOT_TOKEN="token_kamu"
export TELEGRAM_CHAT_ID="chat_id_kamu"

python src/analyzer.py
```

---

## 📱 Contoh Pesan Telegram

```
╔══════════════════════════════╗
║   📊 XAUUSD SCALPING ALERT   ║
╚══════════════════════════════╝

🕐 Waktu   : 29 Apr 2026 21:00 WIB
💰 Harga   : $3320.50
⏱ TF      : M15
🌍 Sesi    : 🇺🇸 NEW YORK
           Sesi New York aktif — volatilitas TERTINGGI ⭐

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚦 SIGNAL  : BUY 🟢
🏷 Setup   : STRONG SETUP ⭐
💪 Strength: ⭐⭐⭐⭐⭐
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📐 INDIKATOR:
  • RSI(14)  : 48.3 [████░░░░░░]
             ⚪ NEUTRAL
  • EMA9     : 3318.75
  • EMA21    : 3317.20
  • EMA50    : 3312.40
  • ATR(14)  : 1.85 (volatilitas)
  • Trend    : 📈 BULLISH

📊 SUPPORT & RESISTANCE (20 candle):
  🔴 Resistance : $3328.00
  🟢 Support    : $3310.50

📝 ANALISIS:
✅ EMA9 cross ATAS EMA21 — bullish crossover terkonfirmasi
✅ RSI 48.3 — ruang naik tersedia (belum overbought)
✅ Harga DI ATAS EMA50 — trend makro bullish

💹 LEVEL TRADING:
📌 Entry    : $3320.50
🎯 TP1      : $3321.98  (+$1.48)
🎯 TP2      : $3323.28  (+$2.78)
🛑 SL       : $3318.65  (-$1.85)
📐 R:R      : 1:0.8

⚠️ Selalu gunakan manajemen risiko. DYOR.
#XAUUSD #Gold #Scalping #M15 #TechnicalAnalysis
```

---

## ⏰ Jadwal Otomatis

GitHub Actions berjalan tiap jam (menit ke-0 UTC). **Sesi terpenting:**

| Sesi              | Jam UTC    | Jam WIB       | Keterangan          |
|------------------|------------|---------------|---------------------|
| 🇯🇵 Tokyo/Asia    | 00–08      | 07–15 WIB     | Volatilitas rendah  |
| 🇬🇧 London Open   | 07–09      | 14–16 WIB     | Mulai aktif         |
| 🇺🇸 NY + London   | 13–16      | 20–23 WIB     | ⭐ Terbaik untuk scalping |
| 🇺🇸 New York      | 13–22      | 20–05 WIB     | Volatilitas tertinggi |

---

## 📁 Struktur Repo

```
xauusd-scalping-bot/
├── .github/
│   └── workflows/
│       └── scalping-bot.yml   # Jadwal otomatis GitHub Actions
├── src/
│   └── analyzer.py            # Logic utama: fetch, indikator, signal, Telegram
├── requirements.txt           # Dependensi Python
├── .gitignore
└── README.md
```

---

## 🔧 Konfigurasi Lanjutan

Edit `src/analyzer.py` untuk menyesuaikan:

```python
SYMBOL     = "XAU/USD"   # Bisa diganti pair lain: EUR/USD, BTC/USD, dll.
INTERVAL   = "15min"     # Opsi: 1min, 5min, 15min, 30min, 1h, 4h, 1day
OUTPUTSIZE = 100         # Jumlah candle yang diambil
```

---

## ⚠️ Disclaimer

> Bot ini hanya alat bantu analisis teknikal otomatis.
> **Bukan rekomendasi investasi atau ajakan trading.**
> Selalu gunakan manajemen risiko, position sizing yang tepat, dan lakukan analisis sendiri (DYOR).
> Trading emas/forex mengandung risiko tinggi dan dapat mengakibatkan kerugian.
