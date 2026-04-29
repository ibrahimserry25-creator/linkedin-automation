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
from src.auto_reply import run_auto_replies, process_post_comments

# Post hours (Cairo time): 9 AM and 2 PM
POST_HOURS = [9, 14]

def generate_and_publish_now():
    """Generates a single post with AI and publishes it directly to LinkedIn."""
    from src.content_generator import generate_recommendations, generate_post, generate_image_prompt, ANGLES
    from src.image_generator import generate_image
    
    niche = "الوظائف، مقابلات العمل، التكنولوجيا، الذكاء الاصطناعي، تطوير الذات، وكيفية الحصول على ترقية"
    
    print("[*] Generating a new post with AI...")
    
    # 1. Get topic
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
    
    # 2. Generate content
    print(f"[*] Writing post about: {topic_title}")
    content = generate_post(topic_title, "LinkedIn")
    if not content:
        print("[!] Failed to generate content.")
        return False
    
    # 3. Generate image
    print(f"[*] Generating image...")
    img_prompt = generate_image_prompt(topic_title, content)
    safe_filename = f"auto_{int(time.time())}"
    image_path = generate_image(img_prompt, safe_filename)
    image_url = f"/outputs/{os.path.basename(image_path)}" if image_path else ""
    
    # 4. Save to DB
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
    
    # 5. Publish immediately
    print("[*] Publishing to LinkedIn NOW...")
    success, message = publish_to_linkedin(post_id)
    
    if success:
        print(f"[+] Published successfully!")
        send_telegram_alert(
            f"✅ <b>تم نشر بوست جديد تلقائياً!</b>\n📌 {topic_title}\n⏰ {datetime.now().strftime('%H:%M')}"
        )
        return True
    else:
        print(f"[!] Failed to publish: {message}")
        send_telegram_alert(
            f"❌ <b>فشل نشر البوست التلقائي</b>\n📌 {topic_title}\n⚠️ {message}"
        )
        return False

def run_scheduler():
    print(f"\n{'='*50}")
    print(f"[*] GitHub Actions Scheduler Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")

    # ── Step 1: Check token health ─────────────────────────
    is_healthy, health_msg = check_linkedin_token_health()
    print(f"[Health] {health_msg}")
    if not is_healthy:
        send_telegram_alert(
            f"🔑 <b>تنبيه: مشكلة في التوكن!</b>\n\n{health_msg}\n\n"
            f"يرجى تحديث LINKEDIN_ACCESS_TOKEN في GitHub Secrets."
        )
        print("[!] Token unhealthy. Exiting.")
        return

    # ── Step 2: Check if it's posting time (9, 14) ────
    current_hour = datetime.now().hour
    current_minute = datetime.now().minute
    
    # If triggered via Telegram webhook, skip auto-post
    is_webhook = bool(os.getenv("TELEGRAM_MESSAGE", "").strip())
    
    if current_hour in POST_HOURS and current_minute < 15 and not is_webhook:
        print(f"[*] It's scheduled posting time! Hour: {current_hour}:00")
        generate_and_publish_now()
    else:
        print(f"[*] Skipping scheduled post (current: {current_hour}:{current_minute:02d}).")

    # ── Step 3: Check Telegram for direct commands ────────
    print("[*] Checking for Telegram direct commands...")
    from src.telegram_bot import process_webhook_message
    process_webhook_message()

    # ── Step 4: Auto-reply (DISABLED as requested) ────────
    print("[*] Auto-reply is disabled as per user request.")mport
    #         asyncio.run(process_post_comments(test_url, 999))
    #     else:
    #         asyncio.run(run_auto_replies())
    # except Exception as e:
    #     print(f"[!] Auto-reply error: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n[*] Run complete at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    init_db()
    run_scheduler()
