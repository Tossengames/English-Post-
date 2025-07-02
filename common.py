import json
import os
import google.generativeai as genai

# Configure Google Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    MODEL = genai.GenerativeModel('gemini-1.5-flash')
else:
    print("Warning: GEMINI_API_KEY not set. AI functions will not work.")
    MODEL = None # Or handle this by raising an error

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
        return "" # Return empty string or specific error message

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

def write_json(filepath: str, data: dict):
    """Writes data to a JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# --- Facebook API Interaction ---
def post_to_facebook(message: str, image_path: str = None) -> bool:
    """
    Posts content to Facebook. This is a placeholder.
    You'll need to implement the actual Facebook Graph API calls here.
    Requires a Facebook Page Access Token with appropriate permissions.
    """
    # Placeholder for Facebook API integration
    # You'll typically use a library like 'facebook-sdk' or 'requests'
    # to make HTTP calls to the Graph API.
    #
    # Example (conceptual):
    # import requests
    #
    # PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
    # PAGE_ID = os.getenv("FB_PAGE_ID") # Or hardcode if it's constant and not sensitive
    #
    # if not PAGE_ACCESS_TOKEN or not PAGE_ID:
    #     print("Facebook credentials not set. Cannot post.")
    #     return False
    #
    # graph_url = f"https://graph.facebook.com/v19.0/{PAGE_ID}/feed"
    # payload = {
    #     'message': message,
    #     'access_token': PAGE_ACCESS_TOKEN
    # }
    #
    # if image_path:
    #     # For images, you might need to use the /photos endpoint
    #     # and then link the photo to a post, or include it directly
    #     # in the feed post. This is more complex and depends on FB API specifics.
    #     print(f"Note: Image posting to Facebook requires more complex setup.")
    #     # Example for just posting an image with a caption:
    #     # with open(image_path, 'rb') as img:
    #     #     files = {'source': img}
    #     #     response = requests.post(f"https://graph.facebook.com/v19.0/{PAGE_ID}/photos",
    #     #                              data={'caption': message, 'access_token': PAGE_ACCESS_TOKEN},
    #     #                              files=files)
    #     #     # Check response and handle success/failure
    # else:
    #     response = requests.post(graph_url, data=payload)
    #
    # if response.status_code == 200:
    #     print(f"Successfully posted to Facebook!")
    #     return True
    # else:
    #     print(f"Failed to post to Facebook: {response.status_code} - {response.text}")
    #     return False

    # For now, just simulate success:
    print(f"--- Simulating Facebook Post ---")
    print(f"Message:\n{message}")
    if image_path:
        print(f"Image: {image_path}")
    print(f"--------------------------------")
    return True # Always return True for simulation

# --- Other Utilities ---
def get_current_day_of_week_arabic() -> str:
    """Returns the current day of the week in Arabic."""
    import datetime
    days_of_week_arabic = ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]
    return days_of_week_arabic[datetime.datetime.now().weekday()]

