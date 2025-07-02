import json
import os
import datetime
import requests
import google.generativeai as genai
import re # Added for regular expressions to clean markdown

# Configure Google Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    MODEL = genai.GenerativeModel('gemini-1.5-flash')
else:
    print("Warning: GEMINI_API_KEY not set. AI functions will not work.")
    MODEL = None

# --- AI Interaction ---
def ask_ai(prompt: str) -> str:
    """
    Sends a prompt to the configured AI model and returns the response.
    Can be easily adapted for other AI platforms.
    """
    if MODEL is None:
        raise ValueError("AI model not initialized. GEMINI_API_KEY might be missing.")
    try:
        response = MODEL.generate_content(prompt)
        # You might need to adjust how to extract text based on the specific API response format
        return response.text.strip()
    except Exception as e:
        print(f"Error calling AI: {e}")
        return ""

# --- File I/O ---
def read_json(filepath: str) -> dict:
    """Reads a JSON file and returns its content."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return {}
    except json.JSONDecodeError:
        print(f"Error decoding JSON from: {filepath}")
        return {}
    except Exception as e:
        print(f"An error occurred reading JSON from {filepath}: {e}")
        return {}


def write_json(filepath: str, data: dict):
    """Writes data to a JSON file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"An error occurred writing JSON to {filepath}: {e}")

# --- Post Formatting and Cleanup ---
def clean_ai_output(text: str) -> str:
    """
    Removes common markdown formatting characters and cleans up extra spaces/newlines.
    """
    # Remove bold/italic markdown (** and *)
    text = re.sub(r'\*\*([^\*]+?)\*\*', r'\1', text) # Removes **text** -> text
    text = re.sub(r'\*([^\*]+?)\*', r'\1', text)    # Removes *text* -> text
    
    # Remove heading markdown (#, ## etc.)
    text = re.sub(r'^\s*#+\s*', '', text, flags=re.MULTILINE)

    # Remove code blocks (```) if they accidentally appear
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = text.replace('```', '')

    # Normalize multiple newlines to max two (for paragraphs)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove leading/trailing whitespace from lines
    cleaned_lines = [line.strip() for line in text.splitlines()]
    text = '\n'.join(cleaned_lines)
    
    return text.strip() # Final strip

# --- Facebook API Interaction ---
def post_to_facebook(message: str, image_path: str = None) -> bool:
    """
    Posts content to Facebook using the Graph API.
    """
    PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_TOKEN") # Using FB_PAGE_TOKEN as requested
    PAGE_ID = os.getenv("FB_PAGE_ID")

    if not PAGE_ACCESS_TOKEN or not PAGE_ID:
        print("Facebook credentials (FB_PAGE_TOKEN or FB_PAGE_ID) not set in environment variables. Cannot post.")
        return False

    # Base URL for the Facebook Graph API
    GRAPH_API_VERSION = "v20.0" # Using v20.0, released May 2024
    GRAPH_API_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

    try:
        if image_path and os.path.exists(image_path):
            # --- Scenario 1: Posting with an image ---
            photo_upload_endpoint = f"{GRAPH_API_URL}/{PAGE_ID}/photos"

            with open(image_path, 'rb') as img_file:
                files = {'source': img_file}
                photo_payload = {
                    'access_token': PAGE_ACCESS_TOKEN,
                    'caption': message # The text that goes with the image
                }
                print(f"Attempting to upload image from: {image_path} with caption to {photo_upload_endpoint}")
                response = requests.post(photo_upload_endpoint, data=photo_payload, files=files)
        else:
            # --- Scenario 2: Posting text-only ---
            feed_post_endpoint = f"{GRAPH_API_URL}/{PAGE_ID}/feed"
            post_payload = {
                'message': message,
                'access_token': PAGE_ACCESS_TOKEN
            }
            print(f"Attempting to post text message to Facebook feed at {feed_post_endpoint}")
            response = requests.post(feed_post_endpoint, data=post_payload)

        # Check the response from Facebook
        response.raise_for_status() # This will raise an HTTPError for bad responses (4xx or 5xx)
        response_data = response.json()

        if response.status_code == 200 and ('id' in response_data or 'post_id' in response_data):
            print(f"Successfully posted to Facebook! Post ID: {response_data.get('id') or response_data.get('post_id')}")
            return True
        else:
            print(f"Failed to post to Facebook. Status Code: {response.status_code}. Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Network or Facebook API error: {e}")
        if e.response is not None:
            print(f"Facebook detailed error: {e.response.text}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during Facebook posting: {e}")
        return False

# --- Other Utilities ---
def get_current_day_of_week_arabic() -> str:
    """Returns the current day of the week in Arabic."""
    days_of_week_arabic = ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]
    return days_of_week_arabic[datetime.datetime.now().weekday()]

