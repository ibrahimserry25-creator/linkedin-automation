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
from src.database import save_post, init_db, get_kv, set_kv

# Post hours (Cairo time): 9 AM and 2 PM
POST_HOURS = [9, 14]

def generate_and_publish_now(target_hour=None):
    """Generates a single post with AI and publishes it directly to LinkedIn.
    If target_hour is provided, it waits until exactly that hour before publishing.
    """
    from src.content_generator import generate_recommendations, generate_post, generate_image_prompt, ANGLES
    from src.image_generator import generate_image
    
    NICHES = [
      "أخبار وتقنيات الذكاء الاصطناعي الجديدة والتريند",
      "نصائح احترافية لاجتياز مقابلات العمل (Interviews)",
      "أهمية تطوير المهارات الناعمة (Soft Skills) للموظفين",
      "أدوات ذكاء اصطناعي تزيد من الإنتاجية في العمل",
      "قصص نجاح ملهمة في ريادة الأعمال والعمل الحر",
      "أخطاء شائعة في البرمجة وكيفية تجنبها",
      "مستقبل الوظائف في عصر الأتمتة والذكاء الاصطناعي",
      "استراتيجيات التسويق الرقمي (Digital Marketing) الحديثة",
      "قصص نجاح ملهمة لشركات عالمية بدأت من الصفر",
      "نصائح للصحة النفسية وتجنب الإرهاق (Burnout) أثناء العمل",
      "أفضل وأحدث البرامج التي يجب استخدامها لتسهيل وتسريع الشغل",
      "الأتمتة (Automation): كيف تجعل البرامج تنجز المهام بدلاً منك في العمل",
      "بيئة العمل: كيف تتعامل مع الإيجابيات والسلبيات في الشركات",
      "مواقف مضحكة وخفيفة نتعرض لها يومياً في بيئة الشغل والمكاتب"
    ]
    niche = random.choice(NICHES)
    
    print(f"[*] Generating a new post with AI about niche: {niche.encode('ascii', 'ignore').decode()}...")
    
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
    
    # 50% No-Image Mode
    mode_50 = get_kv("image_mode")
    image_path, source = None, "بدون صورة"
    
    if mode_50 == "50" and random.random() < 0.5:
        print("[*] 50% No-Image mode activated for this post! Skipping image.")
    else:
        image_path, source = generate_image(img_prompt, safe_filename)
        
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
    
    # Precise Timing Logic
    if target_hour is not None:
        now = datetime.now()
        target_time = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
        
        # If target_hour is for tomorrow (e.g. we started at 23:50 for a 0:00 post), handle it
        if target_time < now:
            from datetime import timedelta
            target_time += timedelta(days=1)
            
        wait_seconds = (target_time - now).total_seconds()
        if wait_seconds > 0:
            print(f"[*] Post prepared successfully! Waiting {wait_seconds:.0f} seconds until exactly {target_hour}:00 to publish...")
            time.sleep(wait_seconds)
    
    print(f"[*] Publishing to LinkedIn NOW at {datetime.now().strftime('%H:%M:%S')}...")
    success, message = publish_to_linkedin(post_id)
    
    if success:
        print(f"[+] Published successfully!")
        
        mode_status = "مفعل" if mode_50 == "50" else "ملغى"
        send_telegram_alert(
            f"✅ <b>تم نشر بوست جديد تلقائياً!</b>\n"
            f"📌 {topic_title}\n"
            f"📷 مصدر الصورة: {source}\n"
            f"⚙️ وضع 50% (نص فقط): {mode_status}\n"
            f"⏰ {datetime.now().strftime('%H:%M')}"
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
    
    # Calculate target hour for precision
    target_hour = None
    if current_hour in POST_HOURS:
        target_hour = current_hour
    elif (current_hour + 1) in POST_HOURS and current_minute >= 45:
        target_hour = current_hour + 1
        
    if target_hour is not None and not is_dispatch:
        print(f"[*] It's scheduled posting time! Preparing post for {target_hour}:00...")
        generate_and_publish_now(target_hour=target_hour)
    elif is_dispatch:
        print("[*] Received Google Apps Script Dispatch!")
        topic = os.getenv("POST_TOPIC", "")
        angle = os.getenv("POST_ANGLE", "أسلوب احترافي")
        
        # Handle Mode 50 Toggles
        if "شغل وضع 50" in topic:
            set_kv("image_mode", "50")
            send_telegram_alert("✅ <b>تم تفعيل وضع 50% للصور!</b>\n50% من البوستات القادمة ستكون نصية فقط.")
            return
        elif "وقف وضع 50" in topic:
            set_kv("image_mode", "off")
            send_telegram_alert("❌ <b>تم إيقاف وضع 50% للصور.</b>\nالآن جميع البوستات ستكون مرفقة بصور.")
            return
            
        from src.telegram_bot import _execute_publish
        _execute_publish(topic, angle)
    else:
        print(f"[*] Skipping scheduled post (current: {current_hour}:{current_minute:02d}).")

    print(f"\n[*] Run complete at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    init_db()
    run_scheduler()
