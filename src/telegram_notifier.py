import os
import requests
from dotenv import load_dotenv

load_dotenv()

def send_telegram_alert(message: str):
    """
    Sends a message to a Telegram bot.
    Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("[!] Telegram credentials not set. Cannot send alert:")
        print(f"    Message: {message}")
        return False
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return True
        else:
            print(f"[!] Telegram API error: {response.text}")
            return False
    except Exception as e:
        print(f"[!] Failed to send Telegram alert: {e}")
        return False
