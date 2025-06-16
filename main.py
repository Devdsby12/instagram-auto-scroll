import time
from playwright.sync_api import sync_playwright
import random

def run_bot():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Go to Instagram login page
        page.goto("https://www.instagram.com/accounts/login/")
        time.sleep(5)

        # You must manually log in here or save cookies
        print("Please log in manually within the browser window...")
        time.sleep(60)  # wait 60 seconds for manual login

        # Go to Reels
        page.goto("https://www.instagram.com/reels/")
        time.sleep(5)

        for _ in range(10):
            # Simulate watching a reel
            time.sleep(random.randint(4, 8))
            if random.choice([True, False]):
                try:
                    like_button = page.locator('svg[aria-label="Like"]')
                    like_button.click()
                except:
                    pass
            # Press arrow down (or swipe) to next reel
            page.keyboard.press("ArrowDown")
        
        browser.close()

if __name__ == "__main__":
    run_bot()