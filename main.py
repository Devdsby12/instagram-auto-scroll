import asyncio
from playwright.async_api import async_playwright

# Your sessionid, decoded (no %3A, only :)
INSTAGRAM_SESSION_ID = "73278141431:qCOvHoH8s2EZYt:28:AYeej0GNsgLxMwtp8XeecwndJ-75UG27VJZQeSIzfQ"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        print("Visiting Instagram home page...")
        await page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
        print("Setting sessionid cookie...")
        await context.add_cookies([{
            'name': 'sessionid',
            'value': INSTAGRAM_SESSION_ID.strip(),
            'domain': '.instagram.com',
            'path': '/',
            'httpOnly': True,
            'secure': True
        }])
        print("Cookie set! Now you can access Instagram as logged-in user.")
        # Test: open the Reels page
        await page.goto("https://www.instagram.com/reels/", wait_until="domcontentloaded")
        await asyncio.sleep(5)
        await page.screenshot(path="reels_test.png")
        print("Screenshot saved as reels_test.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
