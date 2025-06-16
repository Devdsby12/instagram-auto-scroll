import os
import time
import random
import requests
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()
SESSION_ID = os.getenv("SESSION_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ✅ Safety check for environment variables
if not SESSION_ID or not GEMINI_API_KEY:
    raise Exception("Error: SESSION_ID or GEMINI_API_KEY not found in environment.")

TAGS = ["reelsinstagram", "indianfunny", "hindimemes", "comedy"]
DOWNLOAD_DIR = "reels"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def delay(min_sec=2, max_sec=5):
    time.sleep(random.uniform(min_sec, max_sec))

def generate_caption():
    prompt = "Write a funny caption for an Instagram meme reel in Hinglish with an Indian city name."
    try:
        res = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]}
        )
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "#funny #reels"

def download_reel(video_url, filename):
    r = requests.get(video_url, stream=True)
    with open(filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            f.write(chunk)

def run_bot():
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
        page.wait_for_timeout(5000)
        print("[✅] Logged in and homepage loaded")

        for tag in TAGS:
            print(f"[🔥] Visiting #{tag}")
            try:
                page.goto(f"https://www.instagram.com/explore/tags/{tag}/", timeout=60000)
                delay(5, 8)

                # 🔁 Scroll to load more reels
                for _ in range(5):
                    page.mouse.wheel(0, 1500)
                    delay(2, 3)

                page.wait_for_selector("video", timeout=30000)
                videos = page.locator("video").all()

                print(f"[🎥] Found {len(videos)} videos")
                count = 0
                for video in videos:
                    if count >= 5:
                        break
                    video_url = video.get_attribute("src")
                    if video_url and ".mp4" in video_url:
                        filename = f"{DOWNLOAD_DIR}/reel_{random.randint(1000,9999)}.mp4"
                        download_reel(video_url, filename)
                        caption = generate_caption()
                        print(f"[✅] Saved: {filename}")
                        print(f"[📝] Caption: {caption}")
                        count += 1
                        delay(2, 5)
            except Exception as e:
                print(f"[❌] Error with #{tag}: {e}")
                delay(2, 4)

        context.close()
        browser.close()

if __name__ == "__main__":
    run_bot()
