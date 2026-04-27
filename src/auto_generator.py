import time
import os
from datetime import datetime, timedelta
import random

from src.content_generator import generate_recommendations, generate_post, generate_image_prompt, ANGLES
from src.image_generator import generate_image
from src.database import save_post

def run_daily_generation(niche="الوظائف، مقابلات العمل، التكنولوجيا، الذكاء الاصطناعي، مشاكل العمل، تطوير الذات، وكيفية الحصول على ترقية"):
    print(f"[*] Starting Daily Auto-Generation for niche: {niche}")
    
    # 1. Get 3 ideas from Gemini
    try:
        recommendations = generate_recommendations(niche)
    except Exception as e:
        print(f"[!] Failed to get recommendations: {e}")
        return False
        
    if not recommendations or len(recommendations) == 0:
        print("[!] No recommendations generated.")
        return False
        
    # We want exactly 3 posts
    topics_to_generate = recommendations[:3]
    
    # Schedule times for today: 09:00, 14:00, 19:00
    now = datetime.now()
    schedule_times = [
        now.replace(hour=9, minute=0, second=0, microsecond=0),
        now.replace(hour=14, minute=0, second=0, microsecond=0),
        now.replace(hour=19, minute=0, second=0, microsecond=0)
    ]
    
    # If we are already past 9 AM, we should schedule for tomorrow, or just next available slots today.
    # To keep it simple, if the scheduled time is in the past, add 1 day to it.
    for i in range(len(schedule_times)):
        if schedule_times[i] < now:
            schedule_times[i] = schedule_times[i] + timedelta(days=1)
    
    # Sort them just in case
    schedule_times.sort()

    for idx, item in enumerate(topics_to_generate):
        topic_title = item.get("title", "موضوع عام")
        angle = item.get("angle", random.choice(ANGLES))
        
        print(f"[*] Generating content for: {topic_title}")
        
        # 2. Generate text
        content = generate_post(topic_title, "LinkedIn")
        if not content:
            print(f"[!] Failed to generate content for {topic_title}. Skipping.")
            continue
            
        # 3. Generate image
        print(f"[*] Generating image for: {topic_title}")
        img_prompt = generate_image_prompt(topic_title, content)
        safe_filename = f"auto_{int(time.time())}_{idx}"
        image_path = generate_image(img_prompt, safe_filename)
        
        image_url = f"/outputs/{os.path.basename(image_path)}" if image_path else ""
        
        # 4. Schedule and Save
        scheduled_at_str = schedule_times[idx].strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            post_id = save_post(
                topic=topic_title,
                angle=angle,
                content=content,
                image_url=image_url,
                image_path=image_path,
                platform="LinkedIn",
                status="Scheduled",
                scheduled_at=scheduled_at_str
            )
            print(f"[+] Successfully scheduled auto-post '{topic_title}' for {scheduled_at_str} (ID: {post_id})")
        except Exception as e:
            print(f"[!] DB Error while saving auto-post: {e}")

    print("[*] Daily Auto-Generation Complete.")
    return True

if __name__ == "__main__":
    # For testing manually
    run_daily_generation()
