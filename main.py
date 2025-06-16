import os
import time
import random
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# Load from .env
load_dotenv()
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
SESSIONID = os.getenv("SESSIONID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

HASHTAGS = ["funny", "darkhumor", "meme", "dank", "comedy"]
DOWNLOAD_LIMIT = 15

def human_delay(min_sec=2, max_sec=5):
    time.sleep(random.uniform(min_sec, max_sec))

def scroll_like_comment(page):
    for _ in range(10):
        human_delay()
        page.keyboard.press("PageDown")
        human_delay()
        page.click('xpath=//section//button//*[contains(text(), "Like")]', timeout=5000)
        human_delay(2, 3)
        comment = random.choice(["🔥", "😂😂", "This is gold", "Relatable 😭"])
        page.click('textarea', timeout=5000)
        page.fill('textarea', comment)
        page.keyboard.press('Enter')
        human_delay()

def login_with_sessionid(context):
    context.add_cookies([{
        'name': 'sessionid',
        'value': SESSIONID,
        'domain': '.instagram.com',
        'path': '/',
        'httpOnly': True,
        'secure': True,
        'sameSite': 'Lax'
    }])

def run_bot():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        login_with_sessionid(context)
        page = context.new_page()
        page.goto("https://www.instagram.com")

        print("[✓] Logged in using session ID")

        for tag in HASHTAGS:
            page.goto(f"https://www.instagram.com/explore/tags/{tag}/")
            print(f"[↓] Scrolling tag: #{tag}")
            human_delay(3, 5)
            scroll_like_comment(page)
            # TO-DO: Add reel download/edit/upload functions

        print("[✓] All done")
        context.close()
        browser.close()

if __name__ == "__main__":
    run_bot()
