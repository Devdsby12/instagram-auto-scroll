import instaloader
import os
import json
import time
import requests
import datetime

# --- Configuration ---
# Your Instagram session ID. Store this as a GitHub Secret INSTAGRAM_SESSION_ID.
# Instructions on how to get it are provided in the README.
INSTAGRAM_SESSION_ID = os.getenv('INSTAGRAM_SESSION_ID')
# Your Gemini API Key. Store this as a GitHub Secret GEMINI_API_KEY.
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Hashtags to search for reels
HASHTAGS = ["funny", "indiancomedy", "memesdaily", "desicomedy", "relatable"]

# Maximum number of reels to download per hashtag
MAX_REELS_PER_HASHTAG = 5

# Directory to save reels
REELS_DIR = "reels"

# File to keep track of downloaded reel IDs to avoid duplicates
DOWNLOADED_REELS_LOG = os.path.join(REELS_DIR, "downloaded_reels.json")

# --- Gemini API Configuration ---
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# --- Helper Functions ---

def load_downloaded_reels_log():
    """Loads the log of previously downloaded reel IDs."""
    if os.path.exists(DOWNLOADED_REELS_LOG):
        with open(DOWNLOADED_REELS_LOG, 'r') as f:
            return set(json.load(f))
    return set()

def save_downloaded_reels_log(downloaded_reels):
    """Saves the log of downloaded reel IDs."""
    os.makedirs(REELS_DIR, exist_ok=True)
    with open(DOWNLOADED_REELS_LOG, 'w') as f:
        json.dump(list(downloaded_reels), f)

def generate_hinglish_caption(prompt_text):
    """Generates a Hinglish caption using the Gemini API."""
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY is not set. Cannot generate captions.")
        return "No caption generated (API key missing)."

    headers = {
        'Content-Type': 'application/json'
    }
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text}
                ]
            }
        ]
    }
    params = {'key': GEMINI_API_KEY}

    try:
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload, params=params)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        result = response.json()
        if result.get("candidates") and len(result["candidates"]) > 0 and \
           result["candidates"][0].get("content") and \
           result["candidates"][0]["content"].get("parts") and \
           len(result["candidates"][0]["content"]["parts"]) > 0:
            caption = result["candidates"][0]["content"]["parts"][0]["text"]
            return caption.strip()
        else:
            print(f"Gemini API did not return expected content. Response: {result}")
            return "No caption generated (API response error)."
    except requests.exceptions.RequestException as e:
        print(f"Error calling Gemini API: {e}")
        return "No caption generated (API connection error)."
    except json.JSONDecodeError:
        print(f"Error decoding JSON response from Gemini API: {response.text}")
        return "No caption generated (API JSON error)."


def main():
    """Main function to run the bot."""
    print(f"Starting Instagram Reels Downloader Bot at {datetime.datetime.now()}")

    # Create reels directory if it doesn't exist
    os.makedirs(REELS_DIR, exist_ok=True)

    # Load previously downloaded reels
    downloaded_reels = load_downloaded_reels_log()
    print(f"Loaded {len(downloaded_reels)} previously downloaded reels.")

    L = instaloader.Instaloader()

    try:
        # Load session from file if it exists, otherwise use session ID from environment
        session_file = "instaloader.session"
        if os.path.exists(session_file):
            print(f"Loading session from {session_file}...")
            L.load_session_from_file(username=None, filename=session_file) # username=None loads any session
        elif INSTAGRAM_SESSION_ID:
            print("Logging in using session ID...")
            # instaloader expects a dictionary for cookies
            cookies = {"sessionid": INSTAGRAM_SESSION_ID}
            L.context.store_cookies(cookies)
            # Verify login by trying to retrieve current user's profile
            try:
                L.load_session_from_file(filename=session_file) # Try to save the session
            except Exception as e:
                print(f"Could not save session from provided session ID. Proceeding without saved session file. Error: {e}")
        else:
            print("Error: INSTAGRAM_SESSION_ID not provided and no session file found.")
            return

        # Save session for future runs
        L.save_session_to_file(session_file)
        print("Session loaded/saved successfully.")

    except Exception as e:
        print(f"Error during Instagram login/session handling: {e}")
        print("Please ensure your INSTAGRAM_SESSION_ID is valid and try again.")
        return

    total_reels_downloaded = 0
    for hashtag_name in HASHTAGS:
        print(f"\n--- Searching for reels under #{hashtag_name} ---")
        reels_downloaded_for_hashtag = 0

        try:
            # Iterate through top posts by hashtag
            # Instaloader.get_hashtag_posts supports 'top_posts' for popular posts
            for post in L.get_hashtag_posts(hashtag_name, shortcode_as_url=False):
                if reels_downloaded_for_hashtag >= MAX_REELS_PER_HASHTAG:
                    print(f"Reached limit of {MAX_REELS_PER_HASHTAG} reels for #{hashtag_name}.")
                    break

                if not post.is_video:
                    continue # Skip if not a video (reel)

                if post.shortcode in downloaded_reels:
                    # print(f"Skipping already downloaded reel: {post.shortcode}")
                    continue

                print(f"Found reel: {post.shortcode} by {post.owner_username}")

                # Download the reel
                try:
                    # Instaloader will download to the current directory unless specified
                    # We'll download it to the REELS_DIR
                    # Use post.shortcode for unique filename
                    filepath = os.path.join(REELS_DIR, f"{post.shortcode}.mp4")
                    if os.path.exists(filepath):
                        print(f"File {filepath} already exists, skipping download.")
                        downloaded_reels.add(post.shortcode)
                        continue

                    print(f"Downloading reel {post.shortcode}...")
                    L.download_post(post, REELS_DIR) # Downloads media to REELS_DIR
                    
                    # Instaloader names the file based on its internal naming convention.
                    # We need to find the downloaded file and rename it if necessary to .mp4
                    # Or verify it's the video we want.
                    # Instaloader usually creates files like "{owner_username}_{shortcode}.mp4"
                    downloaded_files = [f for f in os.listdir(REELS_DIR) if post.shortcode in f and f.endswith('.mp4')]
                    if not downloaded_files:
                        print(f"Could not find downloaded video file for {post.shortcode}. Skipping caption generation.")
                        continue
                    
                    # Assume the first found .mp4 file is our reel
                    downloaded_filename = os.path.join(REELS_DIR, downloaded_files[0])
                    target_filename = os.path.join(REELS_DIR, f"{post.shortcode}.mp4")
                    
                    if downloaded_filename != target_filename:
                        os.rename(downloaded_filename, target_filename)
                        print(f"Renamed {downloaded_filename} to {target_filename}")

                    # Generate Hinglish caption
                    prompt = f"Generate a funny Hinglish caption (mixture of Hindi and English) for a short comedy video. The video is related to the hashtag '{hashtag_name}'. Make it engaging, relatable, and suitable for Instagram Reels. Keep it concise, around 1-2 sentences."
                    caption = generate_hinglish_caption(prompt)
                    
                    # Save caption to a .txt file next to the video
                    caption_filepath = os.path.join(REELS_DIR, f"{post.shortcode}.txt")
                    with open(caption_filepath, 'w', encoding='utf-8') as f:
                        f.write(caption)
                    print(f"Caption generated and saved for {post.shortcode}: {caption}")

                    downloaded_reels.add(post.shortcode)
                    reels_downloaded_for_hashtag += 1
                    total_reels_downloaded += 1
                    save_downloaded_reels_log(downloaded_reels) # Save after each successful download

                except Exception as dl_e:
                    print(f"Error downloading or processing reel {post.shortcode}: {dl_e}")
                
                # Small delay to avoid hitting rate limits
                time.sleep(5) # Adjust as needed

        except instaloader.exceptions.QueryReturnedBadRequestException as qrb_e:
            print(f"Error fetching posts for #{hashtag_name} (QueryReturnedBadRequestException): {qrb_e}")
            print("This often means Instagram is blocking the request. Consider increasing delays or changing VPN/proxy if running locally.")
        except instaloader.exceptions.LoginRequiredException:
            print("Login required. Your session might have expired. Please update INSTAGRAM_SESSION_ID.")
            break # Exit loop if login is required
        except Exception as e:
            print(f"An unexpected error occurred for hashtag #{hashtag_name}: {e}")

    save_downloaded_reels_log(downloaded_reels) # Final save
    print(f"\nBot finished. Total reels downloaded: {total_reels_downloaded}")
    print(f"Updated downloaded reels log with {len(downloaded_reels)} entries.")

if __name__ == "__main__":
    main()

