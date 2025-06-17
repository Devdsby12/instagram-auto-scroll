import asyncio
from pathlib import Path
import os
import requests
from playwright.async_api import async_playwright

# Get secrets from environment variables (set in GitHub Actions)
INSTAGRAM_SESSION_ID = os.environ.get("INSTAGRAM_SESSION_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

REELS_DIR = Path('reels')
REELS_DIR.mkdir(exist_ok=True)
MAX_REELS_TO_DOWNLOAD = 5

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
    for _ in range(12):  # Scroll up to 12 times
        videos = await page.query_selector_all("video")
        for video in videos:
            src = await video.get_attribute("src")
            if src and src not in video_links:
                video_links.add(src)
                if len(video_links) >= max_videos:
                    return list(video_links)
        await page.evaluate("window.scrollBy(0, window.innerHeight);")
        await asyncio.sleep(2)
    return list(video_links)

async def main():
    if not INSTAGRAM_SESSION_ID or not GEMINI_API_KEY:
        print("❌ Missing secrets! Please set INSTAGRAM_SESSION_ID and GEMINI_API_KEY as environment variables.")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        print("Visiting Instagram home page...")
        await page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
        print("Setting sessionid cookie...")
        await context.add_cookies([{
            'name': 'sessionid',
            'value': INSTAGRAM_SESSION_ID.strip(),
            'domain': '.instagram.com',
            'path': '/',
            'httpOnly': True,
            'secure': True
        }])
        print("Opening Instagram Reels feed...")
        await page.goto("https://www.instagram.com/reels/", wait_until="domcontentloaded", timeout=40000)
        await asyncio.sleep(5)  # Let the page render

        # Check if login worked
        html = await page.content()
        if "Log in" in html or "login" in html.lower():
            print("❌ Not logged in! Check your session id.")
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

