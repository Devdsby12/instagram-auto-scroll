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

TAGS = ["funny", "meme", "darkhumor", "comedy"]
DOWNLOAD_DIR = "reels"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def delay(min_sec=2, max_sec=5):
    time.sleep(random.uniform(min_sec, max_sec))

def generate_caption():
    prompt = "Write a funny, Instagram-style caption for a reel with dark humor or meme vibes in Hinglish. Include Indian city name."
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
        tag = random.choice(TAGS)
        print(f"[🔥] Visiting #{tag}")
        page.goto(f"https://www.instagram.com/explore/tags/{tag}/", timeout=60000)
        delay(5, 10)

        links = page.locator("article a").all()
        print(f"[📽️] Found {len(links)} posts")

        downloaded = 0
        for post in links:
            if downloaded >= 15:
                break
            try:
                href = post.get_attribute("href")
                if not href or "/reel/" not in href:
                    continue

                page.goto(f"https://www.instagram.com{href}", timeout=30000)
                delay(5, 8)

                video = page.locator("video")
                video_url = video.get_attribute("src")

                if video_url:
                    filename = f"{DOWNLOAD_DIR}/reel_{random.randint(1000,9999)}.mp4"
                    download_reel(video_url, filename)
                    caption = generate_caption()
                    print(f"[✅] Downloaded: {filename}")
                    print(f"[📝] Caption: {caption}")
                    downloaded += 1

                delay(4, 7)

            except Exception as e:
                print(f"[❌] Error: {str(e)}")
                delay(3, 6)

        context.close()
        browser.close()

if __name__ == "__main__":
    run_bot()
