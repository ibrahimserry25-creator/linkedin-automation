import os
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from src.database import save_post, mark_post_as_published
from src.content_generator import generate_post, generate_image_prompt
from src.image_generator import generate_image
from src.linkedin_publisher import publish_to_linkedin
from src.telegram_notifier import send_telegram_alert

def update_gas_status(topic, status):
    """Update post status in Google Sheets via Google Apps Script Webhook."""
    gas_url = os.getenv("GAS_WEBHOOK_URL")
    if not gas_url:
        print("[!] GAS_WEBHOOK_URL not set. Skipping sheet update.")
        return
        
    try:
        response = requests.post(
            gas_url,
            json={"action": "update_post_status", "topic": topic, "status": status},
            timeout=10
        )
        print(f"[*] GAS Sheet Update Response: {response.status_code}")
    except Exception as e:
        print(f"[!] Failed to update GAS Sheet: {e}")

def _execute_publish(topic, angle):
    print(f"[*] Executing background publish for topic: {topic}")
    
    try:
        content = generate_post(topic, "LinkedIn")
        if not content:
            send_telegram_alert(f"❌ <b>فشل في كتابة البوست عن {topic}.</b>\nالذكاء الاصطناعي لم يعد بمحتوى.")
            update_gas_status(topic, "Failed (Content)")
            return
            
        img_prompt = generate_image_prompt(topic, content)
        safe_filename = f"telegram_{int(time.time())}"
        image_path = generate_image(img_prompt, safe_filename)
        image_url = f"/outputs/{os.path.basename(image_path)}" if image_path else ""
        
        # Save to local SQLite (for caching/logging purposes)
        post_id = save_post(
            topic=topic,
            angle=angle,
            content=content,
            image_url=image_url,
            image_path=image_path,
            platform="LinkedIn",
            status="Scheduled",
            scheduled_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        send_telegram_alert(f"🚀 <b>تم إنشاء المحتوى لـ:</b> {topic}\nجاري النشر على LinkedIn...")
        
        success, msg = publish_to_linkedin(post_id)
        if success:
            mark_post_as_published(post_id)
            update_gas_status(topic, "Published")
            send_telegram_alert(f"✅ <b>تم النشر بنجاح!</b> 🚀\n\n<b>الموضوع:</b> {topic}")
        else:
            update_gas_status(topic, "Failed (Publish)")
            send_telegram_alert(f"❌ <b>حدث خطأ أثناء النشر على لينكد إن:</b>\n{msg}")
            
    except Exception as e:
        print(f"[!] Error in background publish: {e}")
        update_gas_status(topic, f"Error: {str(e)[:50]}")
        send_telegram_alert(f"❌ <b>حدث خطأ تقني أثناء تحضير البوست:</b>\n{str(e)}")

# This block is used if the script is run directly for some testing
if __name__ == "__main__":
    test_topic = os.getenv("POST_TOPIC")
    test_angle = os.getenv("POST_ANGLE", "احترافي")
    if test_topic:
        _execute_publish(test_topic, test_angle)
    else:
        print("No POST_TOPIC found.")
