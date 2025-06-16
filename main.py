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

TAGS = ["reelsinstagram", "indianreels", "reelitfeelit", "trendingreels"]
DOWNLOAD_DIR = "reels"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def delay(min_sec=2, max_sec=5):
    time.sleep(random.uniform(min_sec, max_sec))

def generate_caption():
    prompt = "Write a funny, Instagram-style caption for a reel with meme or dark humor in Hinglish. Include a random Indian city."
    res = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}",
        headers={"Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}]}
    )
    try:
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "#funny #reels"

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

        for tag in TAGS:
            print(f"[🔥] Visiting #{tag}")
            page.goto(f"https://www.instagram.com/explore/tags/{tag}/", timeout=60000)
            delay(8, 12)

            try:
                page.wait_for_selector("video", timeout=20000)
                videos = page.locator("video").all()

                if len(videos) == 0:
                    print(f"[⚠️] No videos found for #{tag}, skipping...")
                    continue

                print(f"[🎥] Found {len(videos)} videos")
                downloaded = 0

                for video in videos:
                    if downloaded >= 10:
                        break
                    try:
                        video_url = video.get_attribute("src")
                        if video_url and ".mp4" in video_url:
                            filename = f"{DOWNLOAD_DIR}/reel_{random.randint(1000,9999)}.mp4"
                            download_reel(video_url, filename)
                            caption = generate_caption()
                            print(f"[✅] Downloaded: {filename}")
                            print(f"[📝] Caption: {caption}")
                            downloaded += 1
                            delay(4, 7)
                    except Exception as e:
                        print(f"[❌] Failed to download a video: {str(e)}")
                        delay(2, 4)

            except Exception as e:
                print(f"[❌] Error with #{tag}: {str(e)}")
                continue

        context.close()
        browser.close()

if __name__ == "__main__":
    run_bot()
