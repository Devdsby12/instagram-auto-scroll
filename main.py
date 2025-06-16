import os
import time
import random
import requests
from dotenv import load_dotenv
from google import genai
from playwright.sync_api import sync_playwright

def main():
    # Load environment variables from .env file if present
    load_dotenv()
    
    # Retrieve Instagram session ID and Gemini API key from environment
    sessionid = os.getenv("INSTAGRAM_SESSION_ID")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not sessionid or not gemini_api_key:
        print("Error: INSTAGRAM_SESSION_ID or GEMINI_API_KEY not found in environment.")
        return

    # Initialize Gemini (Google GenAI SDK) client
    try:
        client = genai.Client(api_key=gemini_api_key)
    except Exception as e:
        print(f"Error initializing Gemini client: {e}")
        return
    
    # Ensure 'reels' folder exists
    os.makedirs("reels", exist_ok=True)

    # Launch Playwright browser
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            # Set Instagram session cookie for login
            context.add_cookies([{
                "name": "sessionid",
                "value": sessionid,
                "domain": ".instagram.com",
                "path": "/",
                "httpOnly": True,
                "secure": True,
                "sameSite": "Lax"
            }])
            page = context.new_page()

            # Navigate to Instagram homepage
            page.goto("https://www.instagram.com/", timeout=60000)
            page.reload()
            page.wait_for_load_state("networkidle")
            
            # Navigate to Explore page for Reels
            page.goto("https://www.instagram.com/explore/", timeout=60000)
            page.wait_for_selector("video")

            # Collect unique video sources
            video_urls = set()
            scroll_attempts = 0
            while len(video_urls) < 5 and scroll_attempts < 5:
                videos = page.query_selector_all("video")
                for video in videos:
                    src = video.get_attribute("src")
                    if src and src not in video_urls:
                        video_urls.add(src)
                    if len(video_urls) >= 5:
                        break
                if len(video_urls) >= 5:
                    break
                # Scroll down to load more content
                page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                time.sleep(2)
                scroll_attempts += 1

            # Download each video and generate caption
            for idx, video_url in enumerate(list(video_urls)[:5], start=1):
                try:
                    # Download video content
                    headers = {"User-Agent": "Mozilla/5.0"}
                    response = requests.get(video_url, headers=headers, timeout=60)
                    response.raise_for_status()
                    video_path = os.path.join("reels", f"video_{idx}.mp4")
                    with open(video_path, "wb") as f:
                        f.write(response.content)
                    
                    # Generate random city name for caption
                    cities = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Ahmedabad", 
                              "Chennai", "Kolkata", "Pune", "Jaipur", "Lucknow"]
                    city = random.choice(cities)
                    prompt = f"Write a funny Hinglish Instagram caption that includes the name of the city {city}."

                    # Generate caption using Gemini API
                    response = client.models.generate_content(model="gemini-2.0-flash-001", contents=prompt)
                    caption = response.text.strip()

                    print(f"Downloaded Video {idx}: {video_path}")
                    print(f"Generated Caption: {caption}\n")
                except Exception as e:
                    print(f"Error processing video {idx}: {e}")
        except Exception as e:
            print(f"Error during Playwright execution: {e}")

if __name__ == "__main__":
    main()
