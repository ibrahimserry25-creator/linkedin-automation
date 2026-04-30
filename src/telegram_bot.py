import os
import time
from datetime import datetime
from dotenv import load_dotenv
import threading

load_dotenv()

from src.database import save_post, mark_post_as_published, get_chat_history, add_chat_message, get_all_posts
from src.content_generator import generate_post, generate_image_prompt
from src.image_generator import generate_image
from src.linkedin_publisher import publish_to_linkedin
from src.telegram_notifier import send_telegram_alert

import google.generativeai as genai

def publish_new_post_tool(topic: str, angle: str = "طلب مباشر من تليجرام"):
    """
    استخدم هذه الأداة فقط عندما يطلب المستخدم صراحة نشر بوست جديد، 
    وبعد التأكد من عدم تكرار الموضوع (أو في حال موافقته على التكرار).
    """
    # Run publishing synchronously because GitHub Actions will kill background threads when main script exits
    _execute_publish(topic, angle)
    return f"نجاح: تم نشر البوست بنجاح لموضوع '{topic}'."

def _execute_publish(topic, angle):
    print(f"[*] Executing background publish for topic: {topic}")
    send_telegram_alert(f"⏳ <b>تم بدء عملية النشر!</b>\nجاري كتابة المنشور وتوليد الصورة عن: <i>{topic}</i>...\nبرجاء الانتظار قليلاً.")
    
    try:
        content = generate_post(topic, "LinkedIn")
        if not content:
            send_telegram_alert(f"❌ <b>فشل الذكاء الاصطناعي في كتابة البوست عن {topic}.</b>\nحاول مرة أخرى.")
            return
            
        img_prompt = generate_image_prompt(topic, content)
        safe_filename = f"telegram_{int(time.time())}"
        image_path = generate_image(img_prompt, safe_filename)
        image_url = f"/outputs/{os.path.basename(image_path)}" if image_path else ""
        
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
        
        send_telegram_alert(f"🚀 <b>تم حفظ البوست وتوليد الصورة بنجاح. جاري النشر على LinkedIn...</b>")
        
        success, msg = publish_to_linkedin(post_id)
        if success:
            mark_post_as_published(post_id)
            send_telegram_alert(f"✅ <b>تم النشر بنجاح على LinkedIn!</b> 🚀\n\n<b>موضوع البوست:</b> {topic}")
        else:
            send_telegram_alert(f"❌ <b>حدث خطأ أثناء النشر على لينكد إن:</b>\n{msg}")
            
    except Exception as e:
        print(f"[!] Error in background publish: {e}")
        send_telegram_alert(f"❌ <b>حدث خطأ تقني أثناء النشر:</b>\n{str(e)}")

def process_telegram_update(update):
    message = update.get("message", {})
    text = message.get("text", "")
    
    if not text:
        return
        
    print(f"[*] Received Telegram message: {text}")
    
    # 1. Save user message to history
    add_chat_message("user", text)
    
    # 2. Prepare Context (Recent Posts)
    recent_posts = get_all_posts()[:15] # Top 15 recent posts
    if recent_posts:
        posts_context = "\n".join([f"- Topic: {p['topic']} | Status: {p['status']} | Date: {p['created_at']}" for p in recent_posts])
    else:
        posts_context = "لا يوجد أي بوستات منشورة حتى الآن."
        
    system_instruction = f"""
أنت مساعد ذكي ومتحدث طبيعي لإدارة حساب لينكد إن الخاص بي.

هذه قائمة بأحدث البوستات الموجودة في قاعدة البيانات الخاصة بي:
{posts_context}

تعليمات هامة:
1. تحدث معي باللغة العربية بأسلوب ودود واحترافي وكأنك مساعدي الشخصي. لا تتحدث بأسلوب آلي.
2. إذا سألتك عن البوستات المنشورة، أجبني من القائمة أعلاه بوضوح وإيجاز.
3. إذا طلبت منك كتابة أو نشر بوست عن موضوع معين:
   - ابحث أولاً في القائمة أعلاه.
   - إذا وجدت أننا نشرنا بوست عن هذا الموضوع (أو موضوع مشابه جداً)، أخبرني بذلك واسألني: "لقد نشرنا بالفعل عن [الموضوع] مؤخراً، هل تحب أن أنشر واحداً جديداً بزاوية أو صيغة مختلفة؟"
   - إذا لم تجد الموضوع في القائمة، أو إذا أكدت لك أنني أريد النشر رغم التكرار، قم باستدعاء الدالة publish_new_post_tool(topic, angle) لبدء النشر، ورد علي بـ "جاري العمل على نشر البوست...".
4. إذا سألتك أسئلة عامة أو ألقيت التحية، رد علي بشكل طبيعي.
    """
    
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("[!] GEMINI_API_KEY not found!")
            send_telegram_alert("❌ لم يتم العثور على مفتاح API لـ Gemini.")
            return
            
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            system_instruction=system_instruction,
            tools=[publish_new_post_tool]
        )
        
        # 3. Load Chat History for Context
        db_history = get_chat_history(limit=10)
        formatted_history = []
        
        # We need to format for Gemini: role must be 'user' or 'model'
        # Exclude the very last one which is the user's current message (we will send it directly)
        for msg in db_history[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            formatted_history.append({"role": role, "parts": [msg["content"]]})
            
        # Start chat with automatic function calling enabled
        chat = model.start_chat(
            history=formatted_history,
            enable_automatic_function_calling=True
        )
        
        # 4. Get Response from Gemini
        response = chat.send_message(text)
        
        bot_reply = response.text
        if not bot_reply and response.parts:
            bot_reply = "تم استلام الطلب وجاري التنفيذ..."
            
        if bot_reply:
            print(f"[+] Bot Reply: {bot_reply}")
            send_telegram_alert(bot_reply)
            add_chat_message("bot", bot_reply)
            
    except Exception as e:
        print(f"[!] Error in AI agent: {e}")
        send_telegram_alert(f"❌ <b>حدث خطأ في المساعد الذكي:</b>\n{str(e)}")

def process_webhook_message():
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
