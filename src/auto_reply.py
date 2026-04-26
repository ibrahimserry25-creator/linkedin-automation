import re
import time
import sqlite3
import os
import asyncio
from src.scraper import scrape_linkedin_comments
from src.content_generator import generate_smart_replies
from src.linkedin_publisher import post_comment_on_linkedin
from src.telegram_notifier import send_telegram_alert

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "social_posts.db")

def _ensure_comments_table(cursor):
    """Creates the comments table if it doesn't exist."""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            comment_text TEXT,
            author TEXT,
            auto_reply TEXT,
            replied INTEGER DEFAULT 0,
            replied_at DATETIME,
            reply_published INTEGER DEFAULT 0
        )
    ''')

def _extract_urn_from_url(post_url: str) -> str | None:
    """
    Extracts the LinkedIn URN from a post URL.
    e.g. https://www.linkedin.com/feed/update/urn:li:ugcPost:1234567890/ -> urn:li:ugcPost:1234567890
    """
    match = re.search(r'(urn:li:[a-zA-Z:]+\d+)', post_url)
    return match.group(1) if match else None

async def run_auto_replies():
    print("[*] Starting Auto-Reply Job...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    _ensure_comments_table(cursor)
    conn.commit()

    # Fetch posts that are published and have a URL (only check last 7 days)
    cursor.execute("""
        SELECT id, content, post_url FROM posts 
        WHERE status = 'Published' 
          AND post_url IS NOT NULL 
          AND post_url != ''
          AND created_at >= datetime('now', '-7 days', 'localtime')
    """)
    published_posts = cursor.fetchall()

    if not published_posts:
        print("[*] No published posts to check for comments.")
        conn.close()
        return

    replied_count = 0
    failed_count = 0

    for post in published_posts:
        post_id, post_content, post_url = post
        if not post_url or not post_url.startswith("http"):
            continue

        print(f"[*] Checking comments for post ID {post_id}: {post_url}")
        try:
            result = await scrape_linkedin_comments(post_url)

            # If cookies are expired, notify via Telegram and stop
            if "error" in result:
                err_msg = result["error"]
                print(f"[!] Scraper error: {err_msg}")
                if "انتهت صلاحية" in err_msg or "تسجيل الدخول" in err_msg:
                    send_telegram_alert(
                        "🚨 <b>تنبيه: جلسة لينكدإن منتهية!</b>\n\n"
                        "انتهت صلاحية ملف الجلسة (linkedin_state.json).\n"
                        "يرجى فتح لوحة التحكم والنقر على 'سحب التعليقات' مرة واحدة لتسجيل الدخول من جديد.\n\n"
                        f"⏰ الوقت: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                continue

            comments = result.get("comments", [])
            for c in comments:
                # Handle both dict format and plain string format
                if isinstance(c, dict):
                    text = c.get("text", "")
                    author = c.get("author", "Unknown")
                else:
                    text = str(c)
                    author = "Unknown"

                if not text.strip():
                    continue

                # Skip if already replied
                cursor.execute(
                    "SELECT id FROM comments WHERE post_id = ? AND comment_text = ? AND author = ?",
                    (post_id, text, author)
                )
                if cursor.fetchone():
                    continue

                print(f"[+] New comment by '{author}': {text[:80]}...")

                # Generate smart reply
                try:
                    replies = generate_smart_replies(text, context="reply")
                    best_reply = replies[0]["text"] if replies else "شكراً لتعليقك الرائع! 🙏"
                except Exception as e:
                    print(f"[!] Failed to generate reply: {e}")
                    best_reply = "شكراً لمرورك الكريم! 🙏"

                # Extract URN from URL and post the reply on LinkedIn
                post_urn = _extract_urn_from_url(post_url)
                reply_published = 0

                if post_urn:
                    success, msg = post_comment_on_linkedin(post_urn, best_reply)
                    if success:
                        reply_published = 1
                        replied_count += 1
                        print(f"   [+] Reply published on LinkedIn: {best_reply[:60]}...")
                    else:
                        failed_count += 1
                        print(f"   [!] Failed to publish reply: {msg}")
                else:
                    print(f"   [!] Could not extract URN from URL: {post_url}")

                # Save comment + reply to DB
                cursor.execute(
                    """INSERT INTO comments 
                       (post_id, comment_text, author, auto_reply, replied, replied_at, reply_published) 
                       VALUES (?, ?, ?, ?, 1, datetime('now','localtime'), ?)""",
                    (post_id, text, author, best_reply, reply_published)
                )
                conn.commit()

        except Exception as e:
            print(f"[!] Error processing post {post_id}: {e}")

    conn.close()

    # Send Telegram summary if anything happened
    if replied_count > 0 or failed_count > 0:
        send_telegram_alert(
            f"💬 <b>تقرير الردود التلقائية</b>\n\n"
            f"✅ تم الرد على: {replied_count} تعليق\n"
            f"❌ فشل النشر: {failed_count} تعليق\n"
            f"⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    print(f"[*] Auto-Reply Job Complete. Replied: {replied_count}, Failed: {failed_count}")


def run_auto_replies_sync():
    asyncio.run(run_auto_replies())


if __name__ == "__main__":
    run_auto_replies_sync()
