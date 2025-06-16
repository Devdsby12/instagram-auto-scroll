import os
import time
import random
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# Load .env values
load_dotenv()
SESSION_ID = os.getenv("SESSION_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

TAGS = ["funny", "meme", "darkhumor", "comedy"]
DOWNLOAD_DIR = "reels"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def delay(min_sec=2, max_sec=5):
    time.sleep(random.uniform(min_sec, max_sec))

def generate_caption():
    prompt = "Write a funny Hinglish caption for Instagram meme/dark humor reel. Add random Indian city."
    try:
        res = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]}
        )
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "😂 Made in India 🇮🇳 #funny"

def download_reel(video_url, filename):
    r = requests.get(video_url, stream=True)
    with open(filename, 'wb') as f:
        for chunk in r.iter_content(1024):
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
            try:
                print(f"[🔥] Visiting #{tag}")
                page.goto(f"https://www.instagram.com/explore/tags/{tag}/", timeout=60000)
                delay(8, 12)

                page.wait_for_selector("a[href*='/reel/']", timeout=20000)
                links = page.locator("a[href*='/reel/']").all()

                if len(links) == 0:
                    print(f"[⚠️] No reels in #{tag}")
                    continue

                downloaded = 0
                for post in links:
                    if downloaded >= 10:
                        break
                    href = post.get_attribute("href")
                    if not href or "/reel/" not in href:
                        continue

                    page.goto(f"https://www.instagram.com{href}", timeout=30000)
                    delay(4, 7)
                    video = page.locator("video")
                    video_url = video.get_attribute("src")
                    if video_url:
                        filename = f"{DOWNLOAD_DIR}/reel_{random.randint(1000,9999)}.mp4"
                        download_reel(video_url, filename)
                        caption = generate_caption()
                        print(f"[✅] Saved {filename}")
                        print(f"[📝] Caption: {caption}")
                        downloaded += 1
                    delay(4, 6)

            except Exception as e:
                print(f"[❌] Error with #{tag}: {str(e)}")
                continue

        browser.close()

# 🔌 Dummy HTTP server to keep Render happy
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is running.\n')

def start_server():
    server = HTTPServer(('0.0.0.0', 10000), Handler)
    print("✅ Server running on port 10000 to keep Render alive.")
    server.serve_forever()

if __name__ == "__main__":
    thread = threading.Thread(target=start_server)
    thread.start()

    print("🚀 Starting Instagram bot...")
    run_bot()
