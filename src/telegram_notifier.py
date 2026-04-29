import os
import requests
from dotenv import load_dotenv

load_dotenv()

def _clean_env(value: str | None) -> str:
    if not value:
        return ""
    return value.strip().strip('"').strip("'")

def _looks_placeholder(value: str) -> bool:
    return value.lower().startswith("your_")

def send_telegram_alert(message: str):
    """
    Sends a message to a Telegram bot.
    Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env
    """
    bot_token = _clean_env(os.getenv("TELEGRAM_BOT_TOKEN"))
    chat_id = _clean_env(os.getenv("TELEGRAM_CHAT_ID"))
    
    if not bot_token or not chat_id or _looks_placeholder(bot_token) or _looks_placeholder(chat_id):
        print("[!] Telegram credentials are missing/placeholder. Cannot send alert:")
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
            print(f"[!] Telegram API error ({response.status_code}): {response.text}")
            # Fallback without HTML parse mode in case message format is rejected.
            if response.status_code == 400:
                fallback_payload = {
                    "chat_id": chat_id,
                    "text": message
                }
                retry_response = requests.post(url, json=fallback_payload, timeout=10)
                if retry_response.status_code == 200:
                    return True
                print(f"[!] Telegram fallback error ({retry_response.status_code}): {retry_response.text}")
            return False
    except Exception as e:
        print(f"[!] Failed to send Telegram alert: {e}")
        return False
