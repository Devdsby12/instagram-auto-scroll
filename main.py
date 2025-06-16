import os
import random
import time
from playwright.sync_api import sync_playwright
import requests
from dotenv import load_dotenv

# Load secrets
load_dotenv()
SESSION_ID = os.getenv("SESSION_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Hashtags to search
HASHTAGS = ["funny", "darkhumor", "meme", "comedy"]
MIN_LIKES = 10000

# Download folder
DOWNLOAD_DIR = "reels"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def generate_caption(prompt="Write a funny caption for Instagram reel"):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        res = requests.post(url, headers=headers, params=params, json=data)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "🔥 Must watch! #funny #memes"

def download_reel(video_url, output_path):
    r = requests.get(video_url, stream=True)
    with open(output_path, 'wb') as f:
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

        # Go to hashtag explore page
        hashtag = random.choice(HASHTAGS)
        page.goto(f"https://www.instagram.com/explore/tags/{hashtag}/")
        page.wait_for_timeout(5000)
        
        # Click first reel
        page.locator("article a").first.click()
        time.sleep(2)

        # Extract video URL
        try:
            video_url = page.locator("video").get_attribute("src")
            if video_url:
                filename = f"{DOWNLOAD_DIR}/{hashtag}_{random.randint(1000,9999)}.mp4"
                download_reel(video_url, filename)

                caption = generate_caption()
                print("Downloaded:", filename)
                print("Generated Caption:", caption)

                # TODO: Upload step here (separate function)

        except Exception as e:
            print("Failed:", e)

        browser.close()

if __name__ == "__main__":
    run_bot()
