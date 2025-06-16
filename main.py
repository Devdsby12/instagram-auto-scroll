import os
import time
import random
import requests
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
SESSION_ID = os.getenv("SESSION_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

TAGS = ["funny", "reels", "reelitfeelit", "indiancomedy"]
DOWNLOAD_DIR = "reels"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def delay(min_sec=2, max_sec=5):
    time.sleep(random.uniform(min_sec, max_sec))

def generate_caption():
    prompt = "Write a funny Instagram caption in Hinglish with Indian city names for a viral meme reel."
    res = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}",
        headers={"Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}]}
    )
    return res.json()['candidates'][0]['content']['parts'][0]['text']

def download_reel(video_url, filename):
    r = requests.get(video_url, stream=True)
    with open(filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

def run_bot():
    print("🚀 Starting Instagram bot...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        context.add_cookies([{
            "name": "sessionid",
            "value": SESSION_ID,
            "domain": ".instagram.com",
            "path": "/",
            "httpOnly": True,
            "secure": True,
            "sameSite": "Lax"
        }])
        page = context.new_page()

        page.goto("https://www.instagram.com/", timeout=60000)
        delay(5, 8)
        print("[✅] Logged in and homepage loaded")

        for tag in TAGS:
            try:
                print(f"[🔥] Visiting #{tag}")
                page.goto(f"https://www.instagram.com/explore/tags/{tag}/", timeout=60000)
                delay(5, 8)

                # Scroll to load reels
                for _ in range(6):
                    page.mouse.wheel(0, 4000)
                    delay(3, 5)

                page.wait_for_selector("a[href*='/reel/']", timeout=30000)
                links = page.locator("a[href*='/reel/']").all()
                print(f"[📽️] Found {len(links)} links")

                downloaded = 0
                for post in links:
                    if downloaded >= 10:
                        break
                    href = post.get_attribute("href")
                    if not href or "/reel/" not in href:
                        continue

                    reel_url = f"https://www.instagram.com{href}"
                    print(f"[🔗] Opening reel: {reel_url}")
                    page.goto(reel_url, timeout=30000)
                    delay(4, 6)

                    video = page.locator("video")
                    video_url = video.get_attribute("src")
                    if not video_url:
                        continue

                    filename = f"{DOWNLOAD_DIR}/reel_{random.randint(1000,9999)}.mp4"
                    download_reel(video_url, filename)
                    caption = generate_caption()
                    print(f"[✅] Downloaded: {filename}")
                    print(f"[📝] Caption: {caption}")
                    downloaded += 1
                    delay(5, 8)

            except Exception as e:
                print(f"[❌] Error with #{tag}: {str(e)}")

        browser.close()

if __name__ == "__main__":
    run_bot()
