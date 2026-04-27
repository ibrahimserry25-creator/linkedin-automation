import os
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from src.database import get_kv, set_kv, save_post, mark_post_as_published, init_db
from src.content_generator import generate_post, generate_image_prompt
from src.image_generator import generate_image
from src.linkedin_publisher import publish_to_linkedin
from src.telegram_notifier import send_telegram_alert

def process_telegram_update(update):
    message = update.get("message", {})
    text = message.get("text", "")
    
    if text and any(word in text for word in ["انشر عن", "اكتب عن", "بوست عن", "اتكلم عن"]):
        print(f"[*] Received Telegram command: {text}")
        
        # Extract topic
        topic = text.replace("انشر عن", "").replace("اكتب عن", "").replace("بوست عن", "").replace("اتكلم عن", "").strip()
        if not topic:
            topic = "موضوع عشوائي في مجال التكنولوجيا"
        
        # Notify user that we started
        send_telegram_alert(f"⏳ <b>تم استلام طلبك!</b>\nجاري كتابة المنشور وتوليد الصورة عن: <i>{topic}</i>...\nبرجاء الانتظار قليلاً.")
        
        # Generate post
        content = generate_post(topic, "LinkedIn")
        if content:
            img_prompt = generate_image_prompt(topic, content)
            safe_filename = f"telegram_{int(time.time())}"
            image_path = generate_image(img_prompt, safe_filename)
            image_url = f"/outputs/{os.path.basename(image_path)}" if image_path else ""
            
            post_id = save_post(
                topic=topic,
                angle="طلب مباشر من تليجرام",
                content=content,
                image_url=image_url,
                image_path=image_path,
                platform="LinkedIn",
                status="Scheduled",
                scheduled_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            
            # Publish immediately
            success, msg = publish_to_linkedin(post_id)
            if success:
                mark_post_as_published(post_id)
                send_telegram_alert(f"✅ <b>تم النشر بنجاح على LinkedIn!</b> 🚀\n\n<b>موضوع البوست:</b> {topic}")
            else:
                send_telegram_alert(f"❌ <b>حدث خطأ أثناء النشر:</b>\n{msg}")
        else:
            send_telegram_alert(f"❌ <b>فشل الذكاء الاصطناعي في كتابة البوست.</b> حاول مرة أخرى.")

def check_telegram_commands():
    """
    Checks Telegram for new messages and triggers post generation if requested.
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("[*] No Telegram Bot Token found. Skipping bot check.")
        return

    from src.database import init_db, get_kv, set_kv
    # Ensure KV table exists
    init_db()

    offset = get_kv("telegram_offset", 0)
    if offset:
        offset = int(offset)

    url = f"https://api.telegram.org/bot{bot_token}/getUpdates?offset={offset}&timeout=5"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if not data.get("ok"):
            print(f"[!] Error fetching Telegram updates: {data}")
            return
            
        results = data.get("result", [])
        if not results:
            print("[*] No new Telegram commands.")
            return
            
        for update in results:
            update_id = update["update_id"]
            process_telegram_update(update)
            # Update offset to mark as read
            set_kv("telegram_offset", update_id + 1)
            
    except Exception as e:
        print(f"[!] Error in Telegram bot loop: {e}")
        
if __name__ == "__main__":
    check_telegram_commands()
