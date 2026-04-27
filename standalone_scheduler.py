"""
standalone_scheduler.py
-----------------------
One-shot script designed to run on GitHub Actions every 5 minutes.
Does NOT need a long-running FastAPI server.
It checks for:
  1. Scheduled posts ready to be published -> publishes them
  2. Daily post generation (if < 3 posts today)
  3. Auto-reply to comments (runs every ~4 hours based on minute)
"""
import os
import sys
import time
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Make sure src/ is importable
sys.path.insert(0, os.path.dirname(__file__))

from src.database import get_scheduled_posts, mark_post_as_published, DB_PATH
from src.linkedin_publisher import publish_to_linkedin, check_linkedin_token_health
from src.auto_generator import run_daily_generation
from src.telegram_notifier import send_telegram_alert

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

    # ── Step 2: Publish scheduled posts ───────────────────
    scheduled = get_scheduled_posts()
    if scheduled:
        print(f"[*] Found {len(scheduled)} post(s) ready to publish...")
        for post in scheduled:
            post_id, topic, content, image_path, platform = post
            print(f"  -> Publishing post ID {post_id}: {topic[:50]}")
            success, message = publish_to_linkedin(post_id)
            if success:
                mark_post_as_published(post_id)
                print(f"  [+] Published successfully!")
                send_telegram_alert(
                    f"✅ <b>تم نشر بوست!</b>\n📌 {topic}\n⏰ {datetime.now().strftime('%H:%M')}"
                )
            else:
                print(f"  [!] Failed: {message}")
                send_telegram_alert(
                    f"❌ <b>فشل نشر البوست</b>\n📌 {topic}\n⚠️ {message}"
                )
    else:
        print("[*] No scheduled posts ready to publish.")

    # ── Step 3: Daily generation (if < 3 posts today) ─────
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM posts WHERE date(created_at) = date('now', 'localtime')")
    count_today = cursor.fetchone()[0]
    conn.close()

    print(f"[*] Posts created today: {count_today}")
    if count_today < 3:
        print("[*] Running daily generation...")
        run_daily_generation()
    else:
        print("[*] Already have 3+ posts today. Skipping generation.")

    # ── Step 4: Check Telegram for direct commands ────────
    print("[*] Checking Telegram for direct webhook commands...")
    from src.telegram_bot import process_webhook_message
    process_webhook_message()

    # ── Step 5: Auto-reply (only runs at specific times) ───
    # Run auto-reply every 4 hours: at minute 0 of hours 0,4,8,12,16,20
    current_hour = datetime.now().hour
    current_minute = datetime.now().minute
    if current_hour % 4 == 0 and current_minute < 10:
        print("[*] Running auto-reply check...")
        import asyncio
        from src.auto_reply import run_auto_replies
        asyncio.run(run_auto_replies())
    else:
        print(f"[*] Skipping auto-reply (next run at hour divisible by 4).")

    print(f"\n[*] Run complete at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    run_scheduler()
