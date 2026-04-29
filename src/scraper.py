import os
import asyncio
from playwright.async_api import async_playwright

STATE_FILE = os.path.join(os.path.dirname(__file__), "linkedin_state.json")

# Detect if running in GitHub Actions (datacenter IP, usually blocked by LinkedIn)
IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"

async def scrape_linkedin_comments(url: str, post_id: int = None):
    """
    Scrapes comments from a LinkedIn post URL using Playwright.
    If not logged in, opens a visible browser to allow the user to login once.
    In GitHub Actions (datacenter IPs), scraping usually fails due to LinkedIn blocking.
    """
    # Temporarily removed GitHub Actions block to test US-based session
    # if IN_GITHUB_ACTIONS:
    #     print("[!] GitHub Actions detected: LinkedIn scraping likely blocked by datacenter IP. Skipping.")
    #     return {"error": "GitHub_Actions_Blocked", "message": "LinkedIn يحجب سحب التعليقات من سيرفرات GitHub (Datacenter IP). شغّل السحب من جهازك المحلي."}

    async with async_playwright() as p:
        # Launch real Google Chrome to bypass Google SSO "Insecure Browser" blocks
        try:
            browser = await p.chromium.launch(headless=False, channel="chrome")
        except Exception:
            # Fallback to default chromium if Chrome is not installed
            browser = await p.chromium.launch(headless=False)

        needs_login = not os.path.exists(STATE_FILE)

        if needs_login:
            context = await browser.new_context()
            page = await context.new_page()
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

        try:
            print(f"Navigating to {url}")
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_timeout(4000)

            # Check if login is still required (cookie expired)
            if await page.query_selector("input[id='session_key']") or await page.query_selector("input[id='username']"):
                os.remove(STATE_FILE)
                await browser.close()
                return {"error": "انتهت صلاحية تسجيل الدخول. يرجى الضغط على الزر مرة أخرى لتسجيل الدخول من جديد."}


            # Scroll to load comments
            for _ in range(4):
                await page.evaluate("window.scrollBy(0, 800)")
                await page.wait_for_timeout(1500)

            comments_text = []

            # Strategy 1: Look for common comment article or div tags
            comment_nodes = await page.query_selector_all("article[class*='comment']")
            if not comment_nodes:
                comment_nodes = await page.query_selector_all("div[class*='comment-item']")

            for node in comment_nodes:
                # Look for the text direction tag or component text
                text_el = await node.query_selector(".update-components-text, span[dir='ltr'], div[dir='ltr']")
                if text_el:
                    text = await text_el.inner_text()
                    text = text.strip()
                    if text and text not in comments_text:
                        comments_text.append(text)

            # Strategy 2: If strategy 1 fails, grab all update-components-text and skip the first one (the post itself)
            if not comments_text:
                all_text_blocks = await page.query_selector_all(".update-components-text, span.break-words")
                if len(all_text_blocks) > 1:
                    for el in all_text_blocks[1:]:
                        text = await el.inner_text()
                        text = text.strip()
                        if text and text not in comments_text:
                            comments_text.append(text)

            # Strategy 3: Last resort - use page.evaluate to extract from DOM
            if not comments_text:
                print("  Using JS extraction...")
                js_comments = await page.evaluate("""() => {
                    const results = [];
                    const els = document.querySelectorAll('[class*="comment"] span[dir], [class*="comment"] .break-words, .update-components-text span[dir]');
                    els.forEach(el => {
                        const text = el.innerText.trim();
                        if (text.length > 5) results.push(text);
                    });
                    return results;
                }""")
                if js_comments:
                    for t in js_comments:
                        if t not in comments_text:
                            comments_text.append(t)

            await browser.close()

            if not comments_text:
                return {"error": "لم نتمكن من قراءة التعليقات. تأكد من أن المنشور يحتوي على تعليقات ومرئي للعامة."}

            results = comments_text[:10]
            comments_data = [{"author": "Unknown", "text": t} for t in results]
            return {"comments": results, "comments_data": comments_data}

        except Exception as e:
            await browser.close()
            return {"error": f"حدث خطأ أثناء السحب: {str(e)}"}
