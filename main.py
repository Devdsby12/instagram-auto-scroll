import asyncio
from playwright.async_api import async_playwright

INSTAGRAM_SESSION_ID = "73278141431:iux9CyAUjxeFAF:11:AYe5AHWepVYTglTyroSRkyTajemGsvds3O6G8EecBg"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        print("Visiting Instagram home page...")
        await page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
        cookie = {
            'name': 'sessionid',
            'value': INSTAGRAM_SESSION_ID.strip(),
            'domain': '.instagram.com',
            'path': '/',
            'httpOnly': True,
            'secure': True
        }
        print("Cookie to add:", cookie)
        await context.add_cookies([cookie])
        print("Cookie set! Now you can access Instagram as logged-in user.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
