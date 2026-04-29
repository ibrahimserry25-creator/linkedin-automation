import sqlite3
import os
import time
import re
from src.scraper import scrape_linkedin_comments
from src.content_generator import generate_smart_replies
from src.linkedin_publisher import post_comment_on_linkedin
from src.telegram_notifier import send_telegram_alert

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "social_posts.db")

def _ensure_comments_table(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            comment_text TEXT,
            author TEXT,
            reply_text TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

def _extract_urn_from_url(post_url):
    """
    Extracts the LinkedIn URN from a post URL.
    """
    match = re.search(r'(urn:li:[a-zA-Z:]+\d+)', post_url)
    if not match:
        # Try to find numeric ID for activity links
        match = re.search(r'activity-(\d+)', post_url)
        if match:
            return f"urn:li:activity:{match.group(1)}"
    return match.group(1) if match else None

async def process_post_comments(post_url, post_id, post_content=""):
    """Scrapes, generates replies and posts them for a single URL."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    _ensure_comments_table(cursor)
    
    print(f"[*] Navigating to {post_url}")
    result = await scrape_linkedin_comments(post_url)

    if "error" in result:
        print(f"[!] Error: {result['error']}")
        conn.close()
        return 0

    comments = result.get("comments_data", [])
    if not comments:
        # Fallback to plain comments list
        comments = [{"author": "Unknown", "text": c} for c in result.get("comments", [])]
        
    replied_count = 0
    
    for c in comments:
        text = c.get("text", "").strip()
        author = c.get("author", "Unknown")

        if not text: continue

        cursor.execute("SELECT id FROM comments WHERE post_id = ? AND comment_text = ? AND author = ?", 
                       (post_id, text, author))
        if cursor.fetchone(): continue

        print(f"  [+] New comment found: \"{text[:50]}...\"")
        send_telegram_alert(
            f"📩 <b>تعليق جديد على بوست!</b>\n\n"
            f"👤 <b>الشخص:</b> {author}\n"
            f"📝 <b>التعليق:</b> {text}\n\n"
            f"⏳ جاري كتابة الرد..."
        )
        replies = generate_smart_replies(text, "reply")
        if replies:
            reply_text = replies[0]["text"]
            post_urn = _extract_urn_from_url(post_url)
            if post_urn:
                success, msg = post_comment_on_linkedin(post_urn, reply_text)
                if success:
                    cursor.execute("INSERT INTO comments (post_id, comment_text, author, reply_text) VALUES (?, ?, ?, ?)",
                                   (post_id, text, author, reply_text))
                    conn.commit()
                    replied_count += 1
                    print(f"  [✓] Replied successfully!")
                    send_telegram_alert(
                        f"💬 <b>رد تلقائي جديد!</b>\n\n"
                        f"👤 <b>الشخص:</b> {author}\n"
                        f"📝 <b>تعليقه:</b> {text}\n\n"
                        f"🤖 <b>الرد:</b> {reply_text}"
                    )
                else:
                    print(f"  [!] Failed to post reply: {msg}")
                    send_telegram_alert(
                        f"❌ <b>فشل الرد التلقائي على تعليق</b>\n\n"
                        f"👤 {author}\n"
                        f"📝 {text[:100]}...\n"
                        f"⚠️ السبب: {msg}"
                    )

    conn.close()
    return replied_count

async def run_auto_replies():
    print("[*] Starting Auto-Reply Job...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    _ensure_comments_table(cursor)
    conn.commit()

    cursor.execute("""
        SELECT id, content, post_url FROM posts 
        WHERE status = 'Published' 
          AND post_url IS NOT NULL 
          AND post_url != ''
          AND created_at >= datetime('now', '-7 days', 'localtime')
        ORDER BY created_at DESC
        LIMIT 3
    """)
    published_posts = cursor.fetchall()
    conn.close()

    if not published_posts:
        print("[*] No published posts to check.")
        return

    replied_count = 0
    for post_id, post_content, post_url in published_posts:
        replied_count += await process_post_comments(post_url, post_id, post_content)

    print(f"[*] Auto-Reply Job Complete. Replied: {replied_count}")

def run_auto_replies_sync():
    import asyncio
    asyncio.run(run_auto_replies())
