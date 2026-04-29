"""
test_connection.py — Verifikasi semua API sebelum deploy ke GitHub Actions.

Jalankan lokal:
    export TWELVE_DATA_API_KEY="..."
    export TELEGRAM_BOT_TOKEN="..."
    export TELEGRAM_CHAT_ID="..."
    python test_connection.py
"""

import os
import sys
import requests

TWELVE_DATA_API_KEY = os.environ.get("TWELVE_DATA_API_KEY", "")
TELEGRAM_BOT_TOKEN  = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID    = os.environ.get("TELEGRAM_CHAT_ID", "")


def test_twelve_data():
    print("🔍 Test 1: Twelve Data API...")
    if not TWELVE_DATA_API_KEY:
        print("   ❌ TWELVE_DATA_API_KEY tidak diset")
        return False

    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol":     "XAU/USD",
        "interval":   "15min",
        "outputsize": 5,
        "apikey":     TWELVE_DATA_API_KEY,
        "format":     "JSON",
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") == "error":
            print(f"   ❌ API Error: {data.get('message')}")
            return False

        values = data.get("values", [])
        if not values:
            print(f"   ❌ Tidak ada data. Response: {data}")
            return False

        last_price = values[0]["close"]
        print(f"   ✅ Twelve Data OK — Harga terakhir XAU/USD: ${float(last_price):.2f}")
        print(f"   ✅ {len(values)} candle diterima")
        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_telegram():
    print("\n🔍 Test 2: Telegram Bot API...")
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("   ❌ TELEGRAM_BOT_TOKEN atau TELEGRAM_CHAT_ID tidak diset")
        return False

    # Cek bot info
    url  = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            print(f"   ❌ Token tidak valid: {data}")
            return False
        bot_name = data["result"].get("username", "unknown")
        print(f"   ✅ Bot valid: @{bot_name}")
    except Exception as e:
        print(f"   ❌ Error cek bot: {e}")
        return False

    # Kirim pesan test
    url     = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id":    TELEGRAM_CHAT_ID,
        "text":       "✅ *XAUUSD Bot — Tes Koneksi Berhasil!*\n\nBot siap mengirimkan analisis scalping setiap 1 jam.\n\n#XAUUSD #Test",
        "parse_mode": "Markdown",
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        if not result.get("ok"):
            print(f"   ❌ Gagal kirim: {result}")
            return False
        print(f"   ✅ Pesan test terkirim ke chat_id: {TELEGRAM_CHAT_ID}")
        return True
    except Exception as e:
        print(f"   ❌ Error kirim pesan: {e}")
        return False


def main():
    print("=" * 50)
    print("  XAUUSD Bot — Connection Test")
    print("=" * 50)

    ok1 = test_twelve_data()
    ok2 = test_telegram()

    print("\n" + "=" * 50)
    if ok1 and ok2:
        print("✅ Semua koneksi OK! Bot siap deploy ke GitHub Actions.")
        print("\n📋 Langkah selanjutnya:")
        print("   1. Push repo ini ke GitHub")
        print("   2. Tambahkan 3 secrets di Settings → Secrets")
        print("   3. Enable GitHub Actions")
        print("   4. Coba Run workflow manual untuk verifikasi")
    else:
        print("❌ Ada koneksi yang gagal. Periksa API key dan token di atas.")
        sys.exit(1)
    print("=" * 50)


if __name__ == "__main__":
    main()
