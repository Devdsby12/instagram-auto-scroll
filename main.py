import os
import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright
import requests

INSTAGRAM_SESSION_ID = os.environ['INSTAGRAM_SESSION_ID']
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
HASHTAGS = ['funny', 'comedy', 'reelsinstagram']
DOWNLOADS_PER_HASHTAG = 5
REELS_DIR = Path('reels')
REELS_DIR.mkdir(exist_ok=True)

def get_gemini_caption(api_key, video_path):
    # For demo: send video filename to Gemini, real implementation may need video transcription
    prompt = f"Write a funny Hinglish caption for this Instagram Reel: {video_path.name}"
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    params = {"key": api_key}
    resp = requests.post(url, headers=headers, params=params, data=json.dumps(data))
    try:
        return resp.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception:
        return "Funny Hinglish caption!"

async def download_reels_for_hashtag(playwright, hashtag):
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()
    # Set sessionid cookie for Instagram
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
    url = f'https://www.instagram.com/explore/tags/{hashtag}/'
    await page.goto(url)
    await page.wait_for_selector('article a', timeout=20000)
    reel_links = await page.eval_on_selector_all(
        'article a',
        'els => els.map(e => e.href).filter(h => h.includes("/reel/"))'
    )
    reel_links = list(dict.fromkeys(reel_links))[:DOWNLOADS_PER_HASHTAG]  # Deduplicate and limit

    for link in reel_links:
        await page.goto(link)
        try:
            await page.wait_for_selector('video', timeout=15000)
            video_url = await page.eval_on_selector('video', 'el => el.src')
            if not video_url:
                continue
            video_resp = requests.get(video_url, stream=True)
            file_name = f"{hashtag}_{link.rstrip('/').split('/')[-1]}.mp4"
            file_path = REELS_DIR / file_name
            with open(file_path, 'wb') as f:
                for chunk in video_resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            caption = get_gemini_caption(GEMINI_API_KEY, file_path)
            print(f"Downloaded: {file_name}")
            print(f"Caption: {caption}\n")
        except Exception as e:
            print(f"Failed for {link}: {e}")
    await browser.close()

async def main():
    async with async_playwright() as playwright:
        for hashtag in HASHTAGS:
            print(f"Processing #{hashtag}")
            await download_reels_for_hashtag(playwright, hashtag)

if __name__ == "__main__":
    asyncio.run(main())
