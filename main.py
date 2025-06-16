import os
import time
import random
import requests
from playwright.sync_api import sync_playwright, TimeoutError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
# Your Instagram session ID for authentication.
# Make sure this is kept secure and refreshed if it expires.
SESSION_ID = os.getenv("SESSION_ID")
# Your Gemini API Key for generating captions.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# List of hashtags to browse for reels
TAGS = ["reelsinstagram", "indianfunny", "hindimemes", "comedy"]
# Directory where downloaded reels will be saved
DOWNLOAD_DIR = "reels"

# Create the download directory if it doesn't exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# --- Utility Functions ---

def delay(min_sec=2, max_sec=5):
    """
    Introduces a random delay to mimic human behavior and avoid rate limiting.
    Args:
        min_sec (int): Minimum seconds for the delay.
        max_sec (int): Maximum seconds for the delay.
    """
    time.sleep(random.uniform(min_sec, max_sec))

def generate_caption():
    """
    Generates a funny Instagram caption using the Gemini API.
    Returns:
        str: A generated caption or a default hashtag string if an error occurs.
    """
    prompt = "Write a funny caption for an Instagram meme reel in Hinglish with an Indian city name."
    try:
        # Construct the API URL with the GEMINI_API_KEY
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
        
        # Prepare the payload for the API request
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7, # Adjust creativity
                "maxOutputTokens": 100 # Limit caption length
            }
        }
        
        # Make the POST request to the Gemini API
        res = requests.post(
            api_url,
            headers={"Content-Type": "application/json"},
            json=payload
        )
        res.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        
        # Parse the JSON response and extract the generated text
        json_response = res.json()
        return json_response['candidates'][0]['content']['parts'][0]['text']
    except requests.exceptions.RequestException as e:
        print(f"[❌] API Request Error: {e}")
        return "#funny #reels"
    except (KeyError, IndexError) as e:
        print(f"[❌] Error parsing Gemini API response: {e}")
        return "#funny #reels"
    except Exception as e:
        print(f"[❌] Unexpected error in caption generation: {e}")
        return "#funny #reels"

def download_reel(video_url, filename):
    """
    Downloads a video from a given URL and saves it to a file.
    Args:
        video_url (str): The URL of the video to download.
        filename (str): The path and name where the video will be saved.
    """
    try:
        r = requests.get(video_url, stream=True, timeout=30) # Add a timeout for the request
        r.raise_for_status() # Raise an HTTPError for bad responses
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)
    except requests.exceptions.RequestException as e:
        print(f"[❌] Error downloading reel from {video_url}: {e}")

# --- Main Bot Logic ---

def run_bot():
    """
    Main function to run the Instagram reel downloading bot.
    It browses Instagram tags, finds reels, downloads them, and generates captions.
    """
    print("[🚀] Starting Instagram bot...")

    with sync_playwright() as p:
        # Launch a Chromium browser in headless mode (no visible UI)
        # You can set headless=False for debugging to see the browser.
        browser = p.chromium.launch(headless=True)
        
        # Create a new browser context with a specific user agent to appear more like a real browser
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36")
        
        # Add the session ID cookie to the context for authentication
        if SESSION_ID:
            context.add_cookies([{
                "name": "sessionid",
                "value": SESSION_ID,
                "domain": ".instagram.com",
                "path": "/",
                "httpOnly": True,
                "secure": True,
                "sameSite": "Lax" # 'Lax' or 'None'
            }])
            print("[✔] Session ID added to context.")
        else:
            print("[❗] WARNING: SESSION_ID not found. Bot might not function correctly without login.")
            print("[❗] Please ensure you have set SESSION_ID in your .env file.")

        page = context.new_page()

        for tag in TAGS:
            print(f"\n[🔥] Visiting #{tag}")
            try:
                # Navigate to the tag page with a longer timeout
                page.goto(f"https://www.instagram.com/explore/tags/{tag}/", timeout=90000, wait_until='networkidle')
                delay(5, 10) # Give more time for content to load after navigation

                # Wait for any video element to be visible on the page with an extended timeout
                # This is more reliable than just waiting for existence, ensuring it's rendered.
                page.wait_for_selector("video:visible", timeout=60000)
                
                # Retrieve all visible video elements
                videos = page.locator("video:visible").all()

                print(f"[🎥] Found {len(videos)} potential video elements.")
                count = 0
                for video in videos:
                    if count >= 5: # Limit to 5 downloads per tag
                        break
                    
                    video_url = video.get_attribute("src")
                    
                    # Only proceed if a valid MP4 video URL is found
                    if video_url and ".mp4" in video_url:
                        filename = f"{DOWNLOAD_DIR}/reel_{random.randint(1000,9999)}.mp4"
                        print(f"[⬇️] Downloading: {video_url} to {filename}")
                        download_reel(video_url, filename)
                        
                        # Generate caption after successful download
                        caption = generate_caption()
                        print(f"[✅] Saved: {filename}")
                        print(f"[📝] Caption: {caption}")
                        count += 1
                        delay(3, 7) # Delay between downloads
                    else:
                        # print(f"[ℹ️] Skipped non-MP4 or missing src video: {video_url}") # Uncomment for more verbose logging
                        pass # Skip if video_url is None or not an MP4

            except TimeoutError as e:
                print(f"[❌] Timeout Error on #{tag}: {e}. This might mean the page took too long to load or no videos were found.")
                print(f"[ℹ️] Double-check your SESSION_ID and Instagram's page structure.")
                delay(5, 10) # Longer delay on error
            except Exception as e:
                print(f"[❌] General Error on #{tag}: {e}")
                delay(5, 10) # Longer delay on error

        # Close the browser context and browser
        context.close()
        browser.close()
        print("\n[🏁] Bot run finished.")

if __name__ == "__main__":
    run_bot()
