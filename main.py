import asyncio
from playwright.async_api import async_playwright

INSTAGRAM_SESSION_ID = "73278141431:qCOvHoH8s2EZYt:28:AYeej0GNsgLxMwtp8XeecwndJ-75UG27VJZQeSIzfQ"

async def main():
    async with async_playwright() as p:
        # 1. Launch the browser
        browser = await p.chromium.launch(headless=True)
        # 2. Create a browser context with a real user-agent
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        # 3. Open a new page
        page = await context.new_page()
        print("Navigating to Instagram...")
        # 4. Visit Instagram first (this is REQUIRED before setting cookies)
        await page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
        print("Setting sessionid cookie...")
        # 5. Now set the sessionid cookie
        await context.add_cookies([{
            'name': 'sessionid',
            'value': INSTAGRAM_SESSION_ID.strip(),  # removes any spaces
            'domain': '.instagram.com',
            'path': '/',
            'httpOnly': True,
            'secure': True
        }])
        print("Cookie set. Navigating to Reels...")
        # 6. Now you are logged in, you can go to Reels or any other page
        await page.goto("https://www.instagram.com/reels/", wait_until="domcontentloaded")
        await page.screenshot(path="reels_test.png")
        print("Screenshot saved as reels_test.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
