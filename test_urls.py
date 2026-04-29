import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state='src/linkedin_state.json')
        page = await context.new_page()
        await page.goto('https://www.linkedin.com/feed/update/urn:li:share:7455031316032462848/', wait_until='networkidle')
        print('URL2:', page.url)
        await page.screenshot(path='test_screenshot2.png')
        
        await page.goto('https://www.linkedin.com/posts/ibrahim-ismail01_%D8%A7%D9%86%D8%B4%D8%B1-%D8%A3%D9%87%D9%85%D9%8A%D8%A9-%D8%A7%D9%84%D8%B9%D9%85%D9%84-%D8%A7%D9%84%D8%AC%D9%85%D8%A7%D8%B9%D9%8A-share-7454701727682895873-oZtf', wait_until='networkidle')
        print('URL1:', page.url)
        await page.screenshot(path='test_screenshot1.png')
        
        await browser.close()

asyncio.run(test())
