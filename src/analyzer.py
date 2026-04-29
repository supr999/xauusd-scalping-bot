"""
XAUUSD Scalping Bot — Twelve Data Edition
Strategi : RSI(14) + EMA 9/21/50 Crossover, Timeframe M15
Data     : Twelve Data API (800 req/day gratis, real-time)
Output   : Telegram Alert setiap 1 jam via GitHub Actions
"""

import os
import sys
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

# ──────────────────────────────────────────────────────────────────────────────
# CONFIG  (semua dari GitHub Secrets / env variable)
# ──────────────────────────────────────────────────────────────────────────────
TWELVE_DATA_API_KEY = os.environ.get("TWELVE_DATA_API_KEY", "")
TELEGRAM_BOT_TOKEN  = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID    = os.environ.get("TELEGRAM_CHAT_ID", "")

SYMBOL     = "XAU/USD"
INTERVAL   = "15min"
OUTPUTSIZE = 100          # candle terakhir (cukup untuk EMA50 + buffer)
WIB        = pytz.timezone("Asia/Jakarta")


# ──────────────────────────────────────────────────────────────────────────────
# 1. FETCH DATA — Twelve Data
# ──────────────────────────────────────────────────────────────────────────────
def fetch_xauusd() -> pd.DataFrame:
    """
    Ambil OHLCV XAUUSD dari Twelve Data endpoint /time_series.
    Docs: https://twelvedata.com/docs#time-series
    Free plan: 800 API credits/day, 8 credits per request (sudah cukup untuk 24x/hari).
    """
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol":     SYMBOL,
        "interval":   INTERVAL,
        "outputsize": OUTPUTSIZE,
        "apikey":     TWELVE_DATA_API_KEY,
        "format":     "JSON",
        "order":      "ASC",   # oldest first -> pandas-friendly
    }

    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    # Twelve Data mengembalikan {"status": "error"} untuk API key invalid dll.
    if data.get("status") == "error":
        raise ValueError(f"Twelve Data API error: {data.get('message', data)}")

    values = data.get("values")
    if not values:
        raise ValueError(f"Tidak ada data 'values'. Response: {data}")

    df = pd.DataFrame(values)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.set_index("datetime").sort_index()

    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # volume tidak selalu ada untuk XAU/USD
    if "volume" in df.columns:
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
    else:
        df["volume"] = 0.0

    return df[["open", "high", "low", "close", "volume"]]


# ──────────────────────────────────────────────────────────────────────────────
# 2. INDIKATOR TEKNIKAL
# ──────────────────────────────────────────────────────────────────────────────
def calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta    = series.diff()
    gain     = delta.clip(lower=0)
    loss     = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs       = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calc_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def calc_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range — ukuran volatilitas per candle"""
    hl  = df["high"] - df["low"]
    hc  = (df["high"] - df["close"].shift()).abs()
    lc  = (df["low"]  - df["close"].shift()).abs()
    tr  = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()


def calc_support_resistance(df: pd.DataFrame, lookback: int = 20) -> tuple:
    """Support & Resistance sederhana dari swing high/low N candle terakhir"""
    recent     = df.tail(lookback)
    resistance = round(recent["high"].max(), 2)
    support    = round(recent["low"].min(),  2)
    return support, resistance


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["rsi"]       = calc_rsi(df["close"], 14)
    df["ema9"]      = calc_ema(df["close"], 9)
    df["ema21"]     = calc_ema(df["close"], 21)
    df["ema50"]     = calc_ema(df["close"], 50)
    df["atr"]       = calc_atr(df, 14)
    df["ema_cross"] = df["ema9"] - df["ema21"]
    return df


# ──────────────────────────────────────────────────────────────────────────────
# 3. SESSION DETECTOR
# ──────────────────────────────────────────────────────────────────────────────
def get_market_session() -> tuple:
    now_utc = datetime.now(pytz.utc).hour

    if 13 <= now_utc < 22:
        # London + New York overlap = jam terbaik
        return "🇺🇸 NEW YORK", "Sesi New York aktif — volatilitas TERTINGGI ⭐"
    elif 7 <= now_utc < 16:
        return "🇬🇧 LONDON", "Sesi London aktif — volatilitas tinggi"
    elif 0 <= now_utc < 9:
        return "🇯🇵 TOKYO / ASIA", "Sesi Asia — volatilitas rendah, hati-hati"
    else:
        return "🌙 AFTER HOURS", "Di luar sesi utama — spread lebih lebar"


# ──────────────────────────────────────────────────────────────────────────────
# 4. SIGNAL ENGINE
# ──────────────────────────────────────────────────────────────────────────────
def generate_signal(df: pd.DataFrame) -> dict:
    last  = df.iloc[-1]
    prev  = df.iloc[-2]

    price = last["close"]
    rsi   = last["rsi"]
    ema9  = last["ema9"]
    ema21 = last["ema21"]
    ema50 = last["ema50"]
    atr   = last["atr"]

    cross_now  = last["ema_cross"]
    cross_prev = prev["ema_cross"]
    bullish_cross = cross_prev <= 0 < cross_now
    bearish_cross = cross_prev >= 0 > cross_now

    trend = "BULLISH" if price > ema50 else "BEARISH"

    if rsi >= 70:
        rsi_zone = "🔴 OVERBOUGHT"
    elif rsi <= 30:
        rsi_zone = "🟢 OVERSOLD"
    elif rsi >= 60:
        rsi_zone = "🟡 BULLISH ZONE"
    elif rsi <= 40:
        rsi_zone = "🟡 BEARISH ZONE"
    else:
        rsi_zone = "⚪ NEUTRAL"

    signal   = "WAIT"
    strength = 0
    conf_tag = ""
    reason   = []

    # ── BUY ──
    if bullish_cross and trend == "BULLISH" and rsi < 65:
        signal, strength, conf_tag = "BUY 🟢", 5, "STRONG SETUP ⭐"
        reason = [
            "✅ EMA9 cross ATAS EMA21 — bullish crossover terkonfirmasi",
            f"✅ RSI {rsi:.1f} — ruang naik tersedia (belum overbought)",
            "✅ Harga DI ATAS EMA50 — trend makro bullish",
        ]
    elif bullish_cross and trend == "BULLISH" and 65 <= rsi < 70:
        signal, strength, conf_tag = "BUY 🟢", 3, "MODERATE SETUP ⚠️"
        reason = [
            "✅ EMA9 cross ATAS EMA21 — bullish crossover",
            f"⚠️ RSI {rsi:.1f} — mendekati overbought, ambil TP cepat",
            "✅ Harga DI ATAS EMA50 — trend masih bullish",
        ]
    elif rsi <= 25 and trend == "BULLISH":
        signal, strength, conf_tag = "BUY 🟢", 4, "REVERSAL SETUP 🔄"
        reason = [
            f"✅ RSI {rsi:.1f} — EXTREME OVERSOLD, potensi bounce",
            "✅ Trend makro BULLISH — koreksi mungkin berakhir",
            "⚠️ Tunggu konfirmasi candle hijau sebelum entry",
        ]

    # ── SELL ──
    elif bearish_cross and trend == "BEARISH" and rsi > 35:
        signal, strength, conf_tag = "SELL 🔴", 5, "STRONG SETUP ⭐"
        reason = [
            "✅ EMA9 cross BAWAH EMA21 — bearish crossover terkonfirmasi",
            f"✅ RSI {rsi:.1f} — ruang turun tersedia (belum oversold)",
            "✅ Harga DI BAWAH EMA50 — trend makro bearish",
        ]
    elif bearish_cross and trend == "BEARISH" and 30 < rsi <= 35:
        signal, strength, conf_tag = "SELL 🔴", 3, "MODERATE SETUP ⚠️"
        reason = [
            "✅ EMA9 cross BAWAH EMA21 — bearish crossover",
            f"⚠️ RSI {rsi:.1f} — mendekati oversold, ambil TP cepat",
            "✅ Harga DI BAWAH EMA50 — trend masih bearish",
        ]
    elif rsi >= 75 and trend == "BEARISH":
        signal, strength, conf_tag = "SELL 🔴", 4, "REVERSAL SETUP 🔄"
        reason = [
            f"✅ RSI {rsi:.1f} — EXTREME OVERBOUGHT, potensi reversal",
            "✅ Trend makro BEARISH — rally mungkin berakhir",
            "⚠️ Tunggu konfirmasi candle merah sebelum entry",
        ]

    # ── WAIT ──
    else:
        signal, strength, conf_tag = "WAIT ⏳", 0, "NO CLEAR SETUP"
        reason = [
            "⏳ Belum ada konfirmasi EMA crossover",
            f"⏳ RSI {rsi:.1f} — zona netral, tidak ada divergensi",
            "⏳ Tunggu setup yang lebih jelas sebelum entry",
        ]

    # TP / SL dinamis berdasarkan ATR
    if "BUY" in signal:
        entry = price
        tp1   = round(price + max(0.50, atr * 0.8), 2)
        tp2   = round(price + max(1.00, atr * 1.5), 2)
        sl    = round(price - max(0.60, atr * 1.0), 2)
    elif "SELL" in signal:
        entry = price
        tp1   = round(price - max(0.50, atr * 0.8), 2)
        tp2   = round(price - max(1.00, atr * 1.5), 2)
        sl    = round(price + max(0.60, atr * 1.0), 2)
    else:
        entry = tp1 = tp2 = sl = None

    support, resistance = calc_support_resistance(df, 20)
    session, session_desc = get_market_session()

    rr = None
    if entry and tp1 and sl and sl != entry:
        rr = round(abs(tp1 - entry) / abs(sl - entry), 2)

    return {
        "timestamp":    datetime.now(WIB).strftime("%d %b %Y %H:%M WIB"),
        "price":        price,
        "rsi":          rsi,
        "rsi_zone":     rsi_zone,
        "ema9":         ema9,
        "ema21":        ema21,
        "ema50":        ema50,
        "atr":          round(atr, 2),
        "trend":        trend,
        "signal":       signal,
        "strength":     strength,
        "conf_tag":     conf_tag,
        "reason":       reason,
        "entry":        entry,
        "tp1":          tp1,
        "tp2":          tp2,
        "sl":           sl,
        "rr":           rr,
        "support":      support,
        "resistance":   resistance,
        "session":      session,
        "session_desc": session_desc,
    }


# ──────────────────────────────────────────────────────────────────────────────
# 5. FORMAT PESAN TELEGRAM
# ──────────────────────────────────────────────────────────────────────────────
def format_message(s: dict) -> str:
    trend_emoji = "📈" if s["trend"] == "BULLISH" else "📉"
    rsi_val     = s["rsi"]
    rsi_filled  = min(10, int(rsi_val / 10))
    rsi_bar     = "█" * rsi_filled + "░" * (10 - rsi_filled)
    stars       = "⭐" * s["strength"] + "☆" * (5 - s["strength"]) if s["strength"] > 0 else "—"

    level_block = ""
    if s["entry"]:
        tp1_diff = abs(s["tp1"] - s["entry"])
        tp2_diff = abs(s["tp2"] - s["entry"])
        sl_diff  = abs(s["sl"]  - s["entry"])
        rr_str   = f"  R:R = 1:{s['rr']}" if s["rr"] else ""
        level_block = (
            f"\n\n💹 *LEVEL TRADING:*"
            f"\n📌 Entry    : `${s['entry']:.2f}`"
            f"\n🎯 TP1      : `${s['tp1']:.2f}`  (+${tp1_diff:.2f})"
            f"\n🎯 TP2      : `${s['tp2']:.2f}`  (+${tp2_diff:.2f})"
            f"\n🛑 SL       : `${s['sl']:.2f}`   (-${sl_diff:.2f})"
            + (f"\n📐 R:R      : `1:{s['rr']}`" if s["rr"] else "")
        )

    reasons_str = "\n".join(s["reason"])

    msg = (
        "╔══════════════════════════════╗\n"
        "║   📊 XAUUSD SCALPING ALERT   ║\n"
        "╚══════════════════════════════╝\n\n"
        f"🕐 *Waktu   :* `{s['timestamp']}`\n"
        f"💰 *Harga   :* `${s['price']:.2f}`\n"
        f"⏱ *TF      :* M15\n"
        f"🌍 *Sesi    :* {s['session']}\n"
        f"           _{s['session_desc']}_\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🚦 *SIGNAL  : {s['signal']}*\n"
        f"🏷 *Setup   :* {s['conf_tag']}\n"
        f"💪 *Strength:* {stars}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📐 *INDIKATOR:*\n"
        f"  • RSI(14)  : `{rsi_val:.1f}` `[{rsi_bar}]`\n"
        f"             {s['rsi_zone']}\n"
        f"  • EMA9     : `{s['ema9']:.2f}`\n"
        f"  • EMA21    : `{s['ema21']:.2f}`\n"
        f"  • EMA50    : `{s['ema50']:.2f}`\n"
        f"  • ATR(14)  : `{s['atr']:.2f}` _(volatilitas)_\n"
        f"  • Trend    : {trend_emoji} `{s['trend']}`\n\n"
        "📊 *SUPPORT & RESISTANCE (20 candle):*\n"
        f"  🔴 Resistance : `${s['resistance']:.2f}`\n"
        f"  🟢 Support    : `${s['support']:.2f}`\n\n"
        "📝 *ANALISIS:*\n"
        f"{reasons_str}"
        f"{level_block}\n\n"
        "⚠️ _Selalu gunakan manajemen risiko. DYOR._\n"
        "#XAUUSD #Gold #Scalping #M15 #TechnicalAnalysis"
    )
    return msg


# ──────────────────────────────────────────────────────────────────────────────
# 6. KIRIM TELEGRAM
# ──────────────────────────────────────────────────────────────────────────────
def send_telegram(text: str):
    url     = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id":    TELEGRAM_CHAT_ID,
        "text":       text,
        "parse_mode": "Markdown",
    }
    resp = requests.post(url, json=payload, timeout=10)
    resp.raise_for_status()
    result = resp.json()
    if not result.get("ok"):
        raise ValueError(f"Telegram error: {result}")
    print(f"✅ Alert terkirim [{datetime.now(WIB).strftime('%H:%M:%S WIB')}]")


# ──────────────────────────────────────────────────────────────────────────────
# 7. MAIN
# ──────────────────────────────────────────────────────────────────────────────
def main():
    ts = datetime.now(WIB).strftime("%d %b %Y %H:%M:%S WIB")
    print(f"[{ts}] 🚀 Menjalankan XAUUSD Scalping Bot (Twelve Data)...")

    # Validasi env
    missing = [k for k, v in {
        "TWELVE_DATA_API_KEY": TWELVE_DATA_API_KEY,
        "TELEGRAM_BOT_TOKEN":  TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHAT_ID":    TELEGRAM_CHAT_ID,
    }.items() if not v]

    if missing:
        print(f"❌ Environment variable tidak lengkap: {missing}")
        print("   Pastikan semua secret sudah diset di GitHub → Settings → Secrets")
        sys.exit(1)

    try:
        print("📡 Mengambil data XAUUSD dari Twelve Data API...")
        df = fetch_xauusd()
        print(f"✅ {len(df)} candle M15 diterima. Harga terakhir: ${df['close'].iloc[-1]:.2f}")

        df     = add_indicators(df)
        signal = generate_signal(df)
        msg    = format_message(signal)

        print("\n" + "─" * 56)
        print(msg)
        print("─" * 56 + "\n")

        send_telegram(msg)

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Data/API Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
