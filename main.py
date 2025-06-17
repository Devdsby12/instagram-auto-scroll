import os
import asyncio
import json
import time
from pathlib import Path

from playwright.async_api import async_playwright
import requests

INSTAGRAM_SESSION_ID = os.environ['INSTAGRAM_SESSION_ID']
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']

REELS_DIR = Path('reels')
REELS_DIR.mkdir(exist_ok=True)

MAX_REELS_TO_DOWNLOAD = 5  # Number of reels to download per run

def generate_caption(api_key, video_name):
    prompt = f"Write a funny Hinglish caption for this Instagram Reel video named {video_name}."
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": api_key}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        response = requests.post(url, headers=headers, params=params, json=data)
        response.raise_for_status()
        text = response.json()['candidates'][0]['content']['parts'][0]['text']
        return text.strip()
    except Exception as e:
        print(f"Gemini API error: {e}")
        return "Funny Hinglish caption!"

async def scroll_and_collect_video_links(page, max_videos):
    video_links = set()
    last_height = await page.evaluate("() => document.body.scrollHeight")
    scroll_attempts = 0

    while len(video_links) < max_videos and scroll_attempts < 10:
        # Collect video src URLs on page
        videos = await page.query_selector_all("video")
        for video in videos:
            src = await video.get_attribute("src")
            if src and src not in video_links:
                video_links.add(src)
                if len(video_links) >= max_videos:
                    break

        # Scroll down to load more reels
        await page.evaluate("window.scrollBy(0, window.innerHeight);")
        await asyncio.sleep(3)  # wait for new content to load

        new_height = await page.evaluate("() => document.body.scrollHeight")
        if new_height == last_height:
            scroll_attempts += 1
        else:
            scroll_attempts = 0
            last_height = new_height

    return list(video_links)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        # Set Instagram sessionid cookie for login
        await context.add_cookies([{
            'name': 'sessionid',
            'value': INSTAGRAM_SESSION_ID,
            'domain': '.instagram.com',
            'path': '/',
            'httpOnly': True,
            'secure': True,
            'sameSite': 'Lax'
        }])

        page = await context.new_page()
        print("Opening Instagram Reels feed...")
        await page.goto("https://www.instagram.com/reels/", wait_until="networkidle")

        # Wait for reels videos to load
        try:
            await page.wait_for_selector("video", timeout=15000)
        except Exception:
            print("No videos found on page. Check if sessionid is valid or Instagram layout changed.")
            await browser.close()
            return

        print("Scrolling and collecting video URLs...")
        video_urls = await scroll_and_collect_video_links(page, MAX_REELS_TO_DOWNLOAD)
        print(f"Found {len(video_urls)} videos. Downloading...")

        for idx, video_url in enumerate(video_urls, start=1):
            try:
                filename = REELS_DIR / f"reel_{idx}.mp4"
                print(f"Downloading video {idx}: {video_url}")
                resp = requests.get(video_url, stream=True)
                resp.raise_for_status()
                with open(filename, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)

                caption = generate_caption(GEMINI_API_KEY, filename.name)
                print(f"Caption for {filename.name}: {caption}\n")

            except Exception as e:
                print(f"Failed to download or generate caption for video {idx}: {e}")

        await browser.close()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(main())


