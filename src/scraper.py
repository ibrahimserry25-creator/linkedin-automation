import os
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
STATE_FILE = os.path.join(os.path.dirname(__file__), "linkedin_state.json")

async def scrape_linkedin_comments(url: str):
    """
    Scrapes comments from a LinkedIn post URL using Playwright.
    If not logged in, opens a visible browser to allow the user to login once.
    """
    async with async_playwright() as p:
        # Launch real Google Chrome to bypass Google SSO "Insecure Browser" blocks
        needs_login = not os.path.exists(STATE_FILE)
        try:
            browser = await p.chromium.launch(headless=not needs_login)
        except Exception:
            # Fallback to default chromium if Chrome is not installed
            browser = await p.chromium.launch(headless=not needs_login)
        
        needs_login = not os.path.exists(STATE_FILE)
        
        if needs_login:
            context = await browser.new_context()
            page = await context.new_page()
            await stealth_async(page)
            print("[!] No saved state found. Forcing login...")
            await page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
            try:
                # Wait for user to login and reach the feed
                await page.wait_for_url("**/feed/**", timeout=120000)
                await context.storage_state(path=STATE_FILE)
                print("[*] Login successful and state saved!")
            except Exception as e:
                await browser.close()
                return {"error": "انتهى وقت الانتظار لتسجيل الدخول (دقيقتين). يرجى المحاولة مرة أخرى."}
        else:
            context = await browser.new_context(storage_state=STATE_FILE)
            page = await context.new_page()
            await stealth_async(page)

        try:
            print(f"Navigating to {url}")
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
            except Exception:
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(5000)

            # Save screenshot for debugging
            try:
                import time as _time
                screenshot_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", f"screenshot_{_time.time():.0f}.png")
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                await page.screenshot(path=screenshot_path, full_page=False)
                print(f"[*] Screenshot saved: {screenshot_path}")
            except Exception as e:
                print(f"[!] Screenshot failed: {e}")

            # Check if login is still required (cookie expired)
            current_url = page.url
            if "login" in current_url or "authwall" in current_url:
                if os.path.exists(STATE_FILE):
                    os.remove(STATE_FILE)
                await browser.close()
                # Send Telegram alert about expired session
                try:
                    from src.telegram_notifier import send_telegram_alert
                    send_telegram_alert(
                        "🚨 تنبيه: جلسة لينكدإن منتهية!\n\n"
                        "انتهت صلاحية ملف الجلسة (linkedin_state.json).\n"
                        "يرجى فتح لوحة التحكم والنقر على 'سحب التعليقات' مرة واحدة لتسجيل الدخول من جديد.\n\n"
                        f"⏰ الوقت: {__import__('time').strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                except Exception:
                    pass
                return {"error": "انتهت صلاحية تسجيل الدخول. يرجى الضغط على الزر مرة أخرى لتسجيل الدخول من جديد."}

            # Click "show comments" button if it exists
            try:
                show_comments_btn = await page.query_selector("button[aria-label*='comment'], button[aria-label*='Comment'], button[aria-label*='تعليق']")
                if show_comments_btn:
                    await show_comments_btn.click()
                    await page.wait_for_timeout(3000)
            except Exception:
                pass

            # Scroll to load comments
            for _ in range(6):
                await page.evaluate("window.scrollBy(0, 600)")
                await page.wait_for_timeout(1500)

            comments_data = []
            
            # Strategy 1: comments-comment-item (current LinkedIn structure)
            comment_nodes = await page.query_selector_all("[class*='comments-comment-item']")
            print(f"  Strategy 1: Found {len(comment_nodes)} comment nodes")
            
            for node in comment_nodes:
                author = "Unknown"
                text = ""
                # Get author name
                author_el = await node.query_selector("[class*='comment-item__inline-show-more-text'], a[class*='hoverable-link-text'] span[dir='ltr'], span[class*='comment-item__author']")
                if not author_el:
                    author_el = await node.query_selector("a span span")
                if author_el:
                    author = (await author_el.inner_text()).strip()
                
                # Get comment text
                text_el = await node.query_selector("[class*='comment-item__main-content'], span[class*='comment-item__inline-show-more-text'], [dir='ltr']")
                if not text_el:
                    text_el = await node.query_selector("span.break-words")
                if text_el:
                    text = (await text_el.inner_text()).strip()
                
                if text and len(text) > 1:
                    comments_data.append({"author": author, "text": text})
            
            # Strategy 2: article-based comments
            if not comments_data:
                comment_nodes = await page.query_selector_all("article[class*='comment']")
                print(f"  Strategy 2: Found {len(comment_nodes)} article comment nodes")
                for node in comment_nodes:
                    text_el = await node.query_selector("span[dir='ltr'], div[dir='ltr'], span.break-words")
                    if text_el:
                        text = (await text_el.inner_text()).strip()
                        if text and len(text) > 1:
                            comments_data.append({"author": "Unknown", "text": text})
            
            # Strategy 3: Generic text blocks (skip the post itself)
            if not comments_data:
                all_text_blocks = await page.query_selector_all("span.break-words, .update-components-text span[dir='ltr']")
                print(f"  Strategy 3: Found {len(all_text_blocks)} text blocks")
                if len(all_text_blocks) > 1:
                    for el in all_text_blocks[1:]:
                        text = (await el.inner_text()).strip()
                        if text and len(text) > 1 and text not in [c["text"] for c in comments_data]:
                            comments_data.append({"author": "Unknown", "text": text})

            # Strategy 4: Last resort - use page.evaluate to extract from DOM
            if not comments_data:
                print("  Strategy 4: Using JS extraction...")
                js_comments = await page.evaluate("""() => {
                    const results = [];
                    // Try to find comment containers
                    const els = document.querySelectorAll('[class*="comment"] span[dir], [class*="comment"] .break-words');
                    els.forEach(el => {
                        const text = el.innerText.trim();
                        if (text.length > 1) results.push({author: 'Unknown', text: text});
                    });
                    return results;
                }""")
                if js_comments:
                    comments_data = js_comments
                    print(f"  Strategy 4: Found {len(comments_data)} comments via JS")

            await browser.close()
            
            if not comments_data:
                return {"error": "لم نتمكن من قراءة التعليقات. تأكد من أن المنشور يحتوي على تعليقات ومرئي للعامة."}
            
            # Return in both formats for compatibility
            comments_text = [c["text"] for c in comments_data[:10]]
            return {"comments": comments_text, "comments_data": comments_data[:10]}
            
        except Exception as e:
            await browser.close()
            return {"error": f"حدث خطأ أثناء السحب: {str(e)}"}
