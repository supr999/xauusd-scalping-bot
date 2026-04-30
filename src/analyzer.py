import os
import sys
from telegram import Bot
import requests

def main():
    try:
        # Cek environment variables
        required_env = ['TWELVE_DATA_API_KEY', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']
        for env in required_env:
            if not os.getenv(env):
                raise ValueError(f"Missing env: {env}")
        
        # Analisis XAUUSD...
        message = "🚀 XAUUSD Analysis Complete!"
        send_telegram(message)
        
    except Exception as e:
        send_telegram(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
