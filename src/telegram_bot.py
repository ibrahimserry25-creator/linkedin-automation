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
        try:
            print(f"[*] Generating post about: {topic}")
            content = generate_post(topic, "LinkedIn")
            if content:
                print(f"[+] Post generated successfully")
            else:
                print(f"[!] Failed to generate post")
                send_telegram_alert(f"❌ <b>فشل الذكاء الاصطناعي في كتابة البوست.</b>\nحاول مرة أخرى.")
                return
        except Exception as e:
            print(f"[!] Error generating post: {e}")
            send_telegram_alert(f"❌ <b>حدث خطأ أثناء كتابة البوست:</b>\n{str(e)}")
            return
        
        if content:
            try:
                print(f"[*] Generating image prompt...")
                img_prompt = generate_image_prompt(topic, content)
                print(f"[*] Generating image...")
                safe_filename = f"telegram_{int(time.time())}"
                image_path = generate_image(img_prompt, safe_filename)
                image_url = f"/outputs/{os.path.basename(image_path)}" if image_path else ""
                print(f"[*] Image generated: {image_path}")
                
                print(f"[*] Saving post to database...")
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
                print(f"[*] Post saved with ID: {post_id}")
                
                # Publish immediately
                print(f"[*] Publishing to LinkedIn...")
                send_telegram_alert(f"🚀 <b>جاري النشر على LinkedIn...</b>")
                
                success, msg = publish_to_linkedin(post_id)
                if success:
                    mark_post_as_published(post_id)
                    send_telegram_alert(f"✅ <b>تم النشر بنجاح على LinkedIn!</b> 🚀\n\n<b>موضوع البوست:</b> {topic}")
                    print(f"[+] Published successfully!")
                else:
                    send_telegram_alert(f"❌ <b>حدث خطأ أثناء النشر:</b>\n{msg}")
                    print(f"[!] Failed to publish: {msg}")
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"[!] Error during post creation: {e}\n{error_details}")
                send_telegram_alert(f"❌ <b>حدث خطأ تقني أثناء إنشاء البوست:</b>\n{str(e)}")
        else:
            send_telegram_alert(f"❌ <b>فشل الذكاء الاصطناعي في كتابة البوست.</b> حاول مرة أخرى.")
            print(f"[!] Failed to generate content")

def process_webhook_message():
    import os
    message_text = os.getenv("TELEGRAM_MESSAGE", "")
    if message_text:
        print(f"[*] Processing webhook message: {message_text}")
        update = {
            "message": {
                "text": message_text
            }
        }
        process_telegram_update(update)
    else:
        print("[*] No webhook message found.")
        
if __name__ == "__main__":
    process_webhook_message()
