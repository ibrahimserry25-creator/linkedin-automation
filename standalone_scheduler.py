"""
standalone_scheduler.py
-----------------------
One-shot script designed to run on GitHub Actions.
At 9:00 AM, 3:00 PM Cairo -> generates a post and publishes it DIRECTLY.
Telegram webhook commands are processed via workflow_dispatch.
"""
import os
import sys
import time
import random
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Make sure src/ is importable
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
from src.linkedin_publisher import publish_to_linkedin, check_linkedin_token_health
from src.telegram_notifier import send_telegram_alert
from src.database import save_post, init_db

# Post hours (Cairo time): 9 AM and 2 PM
POST_HOURS = [9, 14]

def generate_and_publish_now():
    """Generates a single post with AI and publishes it directly to LinkedIn."""
    from src.content_generator import generate_recommendations, generate_post, generate_image_prompt, ANGLES
    from src.image_generator import generate_image
    
    niche = "الوظائف، مقابلات العمل، التكنولوجيا، الذكاء الاصطناعي، تطوير الذات، وكيفية الحصول على ترقية"
    
    print("[*] Generating a new post with AI...")
    
    try:
        recommendations = generate_recommendations(niche)
    except Exception as e:
        print(f"[!] Failed to get recommendations: {e}")
        return False
    
    if not recommendations:
        print("[!] No recommendations generated.")
        return False
    
    item = recommendations[0]
    topic_title = item.get("title", "موضوع عام")
    angle = item.get("angle", random.choice(ANGLES))
    
    print(f"[*] Writing post about: {topic_title.encode('ascii', 'ignore').decode()}")
    content = generate_post(topic_title, "LinkedIn")
    if not content:
        print("[!] Failed to generate content.")
        return False
    
    print(f"[*] Generating image...")
    img_prompt = generate_image_prompt(topic_title, content)
    safe_filename = f"auto_{int(time.time())}"
    image_path = generate_image(img_prompt, safe_filename)
    image_url = f"/outputs/{os.path.basename(image_path)}" if image_path else ""
    
    post_id = save_post(
        topic=topic_title,
        angle=angle,
        content=content,
        image_url=image_url,
        image_path=image_path,
        platform="LinkedIn",
        status="Scheduled",
        scheduled_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    print(f"[+] Saved post ID: {post_id}")
    
    print("[*] Publishing to LinkedIn NOW...")
    success, message = publish_to_linkedin(post_id)
    
    if success:
        print(f"[+] Published successfully!")
        send_telegram_alert(
            f"✅ <b>تم نشر بوست جديد تلقائياً!</b>\n📌 {topic_title}\n⏰ {datetime.now().strftime('%H:%M')}"
        )
        return True
    else:
        print(f"[!] Failed to publish: {message.encode('ascii', 'ignore').decode()}")
        send_telegram_alert(
            f"❌ <b>فشل نشر البوست التلقائي</b>\n📌 {topic_title}\n⚠️ {message}"
        )
        return False

def run_scheduler():
    print(f"\n{'='*50}")
    print(f"[*] GitHub Actions Scheduler Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")

    is_healthy, health_msg = check_linkedin_token_health()
    print(f"[Health] {health_msg.encode('ascii', 'ignore').decode()}")
    if not is_healthy:
        send_telegram_alert(
            f"🔑 <b>تنبيه: مشكلة في التوكن!</b>\n\n{health_msg}\n\n"
            f"يرجى تحديث LINKEDIN_ACCESS_TOKEN في GitHub Secrets."
        )
        print("[!] Token unhealthy. Exiting.")
        return

    current_hour = datetime.now().hour
    current_minute = datetime.now().minute
    
    print(f"[*] Time check: {current_hour}:{current_minute:02d} (Target Hours: {POST_HOURS})")

    is_dispatch = bool(os.getenv("POST_TOPIC", "").strip())
    
    # Check if we are within the first 45 minutes of the target hour
    if current_hour in POST_HOURS and current_minute < 45 and not is_dispatch:
        print(f"[*] It's scheduled posting time! Hour: {current_hour}:00")
        generate_and_publish_now()
    elif is_dispatch:
        print("[*] Received Google Apps Script Dispatch!")
        topic = os.getenv("POST_TOPIC")
        angle = os.getenv("POST_ANGLE", "أسلوب احترافي")
        from src.telegram_bot import _execute_publish
        _execute_publish(topic, angle)
    else:
        print(f"[*] Skipping scheduled post (current: {current_hour}:{current_minute:02d}).")

    print(f"\n[*] Run complete at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    init_db()
    run_scheduler()
