import os
import time
import threading
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from src.content_generator import generate_post, generate_image_prompt, ANGLES
from src.image_generator import generate_image
from src.database import save_post, get_all_posts, delete_post, update_post_content, get_scheduled_posts, mark_post_as_published, DB_PATH
from src.linkedin_publisher import publish_to_linkedin, check_linkedin_token_health
from src.telegram_notifier import send_telegram_alert
import sqlite3

from fastapi.responses import RedirectResponse

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return RedirectResponse(url="/dashboard/index.html")

# Create outputs directory if not exists
if not os.path.exists("outputs"):
    os.makedirs("outputs")

# Mount static files
app.mount("/dashboard", StaticFiles(directory="dashboard"), name="dashboard")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# ─── Scheduler Logic ─────────────────────────────────────────
def run_scheduler():
    print("[*] Scheduler started...")
    while True:
        post_id = None
        try:
            scheduled_posts = get_scheduled_posts()
            for post in scheduled_posts:
                post_id, topic, content, image_path, platform = post
                print(f"[*] Publishing scheduled post ID: {post_id}")

                success, message = publish_to_linkedin(post_id)
                if success:
                    mark_post_as_published(post_id)
                    print(f"[+] Successfully published post ID {post_id}")
                    send_telegram_alert(
                        f"✅ <b>تم نشر بوست بنجاح!</b>\n\n"
                        f"📌 الموضوع: {topic}\n"
                        f"🆔 Post ID: {post_id}\n"
                        f"⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                else:
                    print(f"[!] Failed to publish scheduled post ID {post_id}: {message}")
                    send_telegram_alert(
                        f"❌ <b>فشل نشر البوست!</b>\n\n"
                        f"📌 الموضوع: {topic}\n"
                        f"🆔 Post ID: {post_id}\n"
                        f"⚠️ السبب: {message}\n"
                        f"⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}"
                    )

            time.sleep(60)  # Check every minute
        except Exception as e:
            print(f"[!] Scheduler Error on post ID {post_id or 'unknown'}: {e}")
            time.sleep(60)

threading.Thread(target=run_scheduler, daemon=True).start()

from src.auto_generator import run_daily_generation
from src.auto_reply import run_auto_replies_sync

def run_daily_loop():
    print("[*] Daily Auto-Generator loop started...")
    while True:
        try:
            # Check if we generated today
            from src.database import DB_PATH
            import sqlite3
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM posts WHERE date(created_at) = date('now', 'localtime')")
            count = cursor.fetchone()[0]
            conn.close()
            
            if count < 3:
                run_daily_generation()
        except Exception as e:
            print(f"[!] Daily loop error: {e}")
        time.sleep(3600) # Check every hour

def run_reply_loop():
    print("[*] Auto-Reply loop started...")
    # Wait 2 minutes on startup before first run
    time.sleep(120)
    while True:
        try:
            run_auto_replies_sync()
        except Exception as e:
            print(f"[!] Reply loop error: {e}")
        time.sleep(3600 * 4)  # Run every 4 hours

def run_token_health_loop():
    """Checks LinkedIn token health every 6 hours and alerts on Telegram if expired."""
    print("[*] Token Health Monitor started...")
    last_alert_sent = False
    while True:
        try:
            is_healthy, message = check_linkedin_token_health()
            if not is_healthy:
                if not last_alert_sent:
                    send_telegram_alert(
                        f"🔑 <b>تنبيه: مشكلة في التوكن!</b>\n\n"
                        f"{message}\n\n"
                        f"يرجى تحديث LINKEDIN_ACCESS_TOKEN في ملف .env وإعادة تشغيل الخادم.\n"
                        f"⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    last_alert_sent = True
                    print(f"[!] Token Health Alert Sent: {message}")
            else:
                last_alert_sent = False
                print(f"[+] Token OK: {message}")
        except Exception as e:
            print(f"[!] Token health check error: {e}")
        time.sleep(3600 * 6)  # Check every 6 hours

threading.Thread(target=run_daily_loop, daemon=True).start()
threading.Thread(target=run_reply_loop, daemon=True).start()
threading.Thread(target=run_token_health_loop, daemon=True).start()

# ─── Models ────────────────────────────────────────────────
class GenerateRequest(BaseModel):
    topic: str
    platform: str
    scheduled_at: Optional[str] = None # Format: YYYY-MM-DD HH:MM

class PublishRequest(BaseModel):
    content: str

class UpdateContentRequest(BaseModel):
    content: str

# ─── Endpoints ─────────────────────────────────────────────
@app.get("/api/recommendations")
def recommendations_api(niche: str = "ريادة الأعمال والتكنولوجيا"):
    from src.content_generator import generate_recommendations
    try:
        recommendations = generate_recommendations(niche)
        return {"recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trends")
def trends_api(keyword: str):
    from src.content_generator import analyze_trend
    if not keyword.strip():
        raise HTTPException(status_code=400, detail="يجب إدخال كلمة بحث.")
    try:
        trend_data = analyze_trend(keyword)
        return trend_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SmartReplyRequest(BaseModel):
    post_text: str
    context: str = "engagement"  # 'engagement' or 'reply'

@app.post("/api/smart-reply")
def smart_reply_api(req: SmartReplyRequest):
    from src.content_generator import generate_smart_replies
    if not req.post_text.strip():
        raise HTTPException(status_code=400, detail="يجب إدخال نص المنشور أو التعليق.")
    try:
        replies = generate_smart_replies(req.post_text, req.context)
        return {"replies": replies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ScrapeRequest(BaseModel):
    url: str

@app.post("/api/scrape-comments")
async def scrape_comments_api(req: ScrapeRequest):
    from src.scraper import scrape_linkedin_comments
    if not req.url.startswith("http"):
        raise HTTPException(status_code=400, detail="رابط غير صالح.")
    try:
        result = await scrape_linkedin_comments(req.url)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return {"comments": result["comments"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate")
def generate_api(req: GenerateRequest):
    print(f"[*] Received Generate Request: {req.topic} | Platform: {req.platform} | Scheduled: {req.scheduled_at}")
    
    if not req.topic.strip():
        raise HTTPException(status_code=400, detail="الموضوع لا يمكن أن يكون فارغاً.")

    try:
        import random
        angle = random.choice(ANGLES)

        content = generate_post(req.topic, req.platform)
        if not content:
            raise HTTPException(status_code=500, detail="فشل توليد النص. جميع محاولات النماذج فشلت (قد تكون مشكلة في الكوتا أو الاتصال).")

        img_prompt = generate_image_prompt(req.topic, content)
        safe_filename = f"post_{int(time.time())}"
        image_path = generate_image(img_prompt, safe_filename)

        image_url = ""
        if image_path:
            image_url = f"/outputs/{os.path.basename(image_path)}"

        status = "Scheduled" if req.scheduled_at and req.scheduled_at.strip() else "Generated"
        
        post_id = save_post(
            topic=req.topic,
            angle=angle,
            content=content,
            image_url=image_url,
            image_path=image_path,
            platform=req.platform,
            status=status,
            scheduled_at=req.scheduled_at if status == "Scheduled" else None
        )
        
        return {"content": content, "image_url": image_url, "post_id": post_id, "status": status}
    except Exception as e:
        print(f"[!] Error in generate_api: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/publish/{post_id}")
def publish_api(post_id: int, req: PublishRequest):
    try:
        from src.database import get_post_by_id
        post = get_post_by_id(post_id)
        if not post:
            raise HTTPException(status_code=404, detail="المنشور غير موجود.")
        
        image_path = post[4] # image_path is at index 4
        
        # Save the edited content first
        update_post_content(post_id, req.content)
        
        success, message = publish_to_linkedin(post_id)
        
        if success:
            mark_post_as_published(post_id)
            return {"message": "✅ تم النشر بنجاح على لينكد إن!"}
        else:
            raise HTTPException(status_code=500, detail=f"فشل النشر: {message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/posts")
def get_posts_api():
    return get_all_posts()

@app.delete("/api/posts/{post_id}")
def delete_post_api(post_id: int):
    from src.linkedin_publisher import delete_linkedin_post
    
    # Attempt to delete from LinkedIn if published
    success, msg = delete_linkedin_post(post_id)
    if not success:
        print(f"[!] Warning: Failed to delete from LinkedIn: {msg}")
    
    delete_post(post_id)
    return {"message": "Post deleted locally and on LinkedIn if applicable", "linkedin_msg": msg}

@app.put("/api/posts/{post_id}")
def update_post_api(post_id: int, req: UpdateContentRequest):
    update_post_content(post_id, req.content)
    return {"message": "Post updated"}

from fastapi import Request, BackgroundTasks

# ─── New Automation Endpoints ──────────────────────────────────

@app.post("/api/webhook/telegram")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    from src.telegram_bot import process_telegram_update
    background_tasks.add_task(process_telegram_update, data)
    return {"status": "ok"}


@app.get("/api/health")
def health_check_api():
    """Check if LinkedIn token is still valid."""
    is_healthy, message = check_linkedin_token_health()
    return {"healthy": is_healthy, "message": message}

@app.get("/api/comments")
def get_comments_api():
    """Returns all auto-saved comments and their replies from the DB."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT c.*, p.topic, p.post_url 
            FROM comments c
            LEFT JOIN posts p ON c.post_id = p.id
            ORDER BY c.id DESC
        """)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/api/trigger/generate")
def trigger_daily_generation():
    """Manually triggers the daily post generation (for testing or force-run)."""
    def _run():
        try:
            run_daily_generation()
            send_telegram_alert("🚀 <b>تشغيل يدوي لمولد المحتوى</b>\nتم توليد وجدولة 3 بوستات جديدة بنجاح!")
        except Exception as e:
            print(f"[!] Manual generation error: {e}")
    threading.Thread(target=_run, daemon=True).start()
    return {"message": "✅ تم تشغيل مولد المحتوى في الخلفية. تحقق من قائمة البوستات بعد قليل."}

@app.post("/api/trigger/replies")
def trigger_auto_replies():
    """Manually triggers the auto-reply job."""
    def _run():
        try:
            run_auto_replies_sync()
        except Exception as e:
            print(f"[!] Manual reply trigger error: {e}")
    threading.Thread(target=_run, daemon=True).start()
    return {"message": "✅ تم تشغيل فحص التعليقات في الخلفية."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
