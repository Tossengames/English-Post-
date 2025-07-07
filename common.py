import json
import os
import datetime
import requests
import google.generativeai as genai
import re
import random

# Configure Google Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    MODEL = genai.GenerativeModel('gemini-1.5-flash')
else:
    print("Warning: GEMINI_API_KEY not set. AI functions will not work.")
    MODEL = None

# Configure Pixabay API Key
PIXABAY_API_KEY = os.getenv('PIXABAY_KEY')
if not PIXABAY_API_KEY:
    print("Warning: PIXABAY_KEY not set. Pixabay image fetching will not work.")

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
        if hasattr(response, 'text') and response.text.strip():
            return response.text.strip()
        else:
            print("Gemini API primary response was empty or did not contain text.")
            if response and response.candidates:
                for candidate in response.candidates:
                    if candidate.content and hasattr(candidate.content, 'parts') and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text.strip():
                                print("Using text from candidate due to primary response issue.")
                                return part.text.strip()
            return None
    except Exception as e:
        print(f"Error generating AI content: {e}")
        return None

# --- File I/O ---
def read_json(filepath: str, default_value=None) -> dict:
    """Reads a JSON file and returns its content, or a default value if file doesn't exist or is corrupted."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Warning: {filepath} not found or corrupted. Initializing with default value.")
        return default_value if default_value is not None else {}
    except Exception as e:
        print(f"An error occurred reading JSON from {filepath}: {e}")
        return default_value if default_value is not None else {}


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
    Removes common AI output artifacts, markdown formatting, and ensures hashtags.
    """
    text = text.strip()
    
    # Remove AI introductory phrases (more comprehensive list)
    text = text.replace("Here's your Facebook post:", "").strip()
    text = text.replace("Here is the Facebook post:", "").strip()
    text = text.replace("تفضل منشورك على فيسبوك:", "").strip()
    text = text.replace("بالتأكيد، إليك منشور الفيسبوك:", "").strip()
    text = text.replace("إليك منشور الفيسبوك:", "").strip()
    text = text.replace("هذا هو منشورك!", "").strip()
    text = text.replace("يمكنني المساعدة في ذلك.", "").strip()
    text = text.replace("بصفتي نموذجًا لغويا", "").strip()
    text = text.replace("بصفتي نموذج ذكاء اصطناعي", "").strip()
    text = text.replace("Sure, here is your post:", "").strip()
    text = text.replace("Of course, here is your post:", "").strip()
    text = text.replace("I can help with that.", "").strip()
    text = text.replace("I am an AI language model and cannot...", "").strip()
    text = text.replace("As an AI language model, I cannot...", "").strip()
    text = text.replace("بالتأكيد، إليك ما طلبته:", "").strip()
    text = text.replace("ها هو:", "").strip()
    
    # Remove markdown bold/italic/header formatting
    text = re.sub(r'\*\*([^\*]+?)\*\*', r'\1', text)
    text = re.sub(r'\*([^\*]+?)\*', r'\1', text)
    text = re.sub(r'^\s*#+\s*', '', text, flags=re.MULTILINE)
    
    # Remove code blocks (```)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = text.replace('```', '')

    # Normalize multiple newlines to max two (for paragraphs)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove leading/trailing whitespace from lines
    cleaned_lines = [line.strip() for line in text.splitlines()]
    text = '\n'.join(cleaned_lines)

    # Separate hashtags from content and ensure standard hashtags are present
    lines = text.split('\n')
    extracted_hashtags = [line for line in lines if line.strip().startswith('#')]
    content_lines = [line for line in lines if not line.strip().startswith('#')]
    
    cleaned_content = '\n'.join(content_lines).strip()

    # Default hashtags if none or too few are generated
    default_hashtags = [
        "#تعلم_اللغة_الإنجليزية",
        "#لغة_انجليزية",
        "#دروس_انجليزي",
        "#EnglishLearning",
        "#LearnEnglish"
    ]

    if len(extracted_hashtags) < 3:
        hashtags_to_add = default_hashtags
    else:
        hashtags_to_add = extracted_hashtags

    if not cleaned_content.endswith('\n\n'):
        cleaned_content += '\n\n'
    
    cleaned_content += '\n'.join([h.strip() for h in hashtags_to_add])

    return cleaned_content.strip()

# --- Pixabay Image Interaction ---
def get_pixabay_image_url(query: str, orientation: str = 'horizontal', safesearch: bool = True) -> str:
    """
    Searches Pixabay for an image based on the query and returns a direct image URL.
    Returns None if no image is found or an error occurs.
    """
    if not PIXABAY_API_KEY:
        print("Pixabay API Key not set. Cannot fetch images.")
        return None

    url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={query}&image_type=photo&orientation={orientation}&safesearch={safesearch}&per_page=20"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if data['hits']:
            random_hit = random.choice(data['hits'])
            print(f"Found Pixabay image for '{query}': {random_hit['webformatURL']}")
            return random_hit['webformatURL']
        else:
            print(f"No Pixabay images found for query: '{query}'.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching image from Pixabay for query '{query}': {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred with Pixabay API for query '{query}': {e}")
        return None

# --- Facebook API Interaction ---
def post_to_facebook(message: str, image_url: str = None) -> bool:
    """
    Posts content to Facebook using the Graph API.
    Accepts a direct image URL for sharing.
    """
    PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_TOKEN")
    PAGE_ID = os.getenv("FB_PAGE_ID")

    if not PAGE_ACCESS_TOKEN or not PAGE_ID:
        print("Facebook credentials (FB_PAGE_TOKEN or FB_PAGE_ID) not set in environment variables. Cannot post.")
        return False

    GRAPH_API_VERSION = "v20.0"
    GRAPH_API_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

    try:
        if image_url:
            photo_upload_endpoint = f"{GRAPH_API_URL}/{PAGE_ID}/photos"
            photo_payload = {
                'access_token': PAGE_ACCESS_TOKEN,
                'caption': message,
                'url': image_url
            }
            print(f"Attempting to upload image from URL: {image_url} with caption to {photo_upload_endpoint}")
            response = requests.post(photo_upload_endpoint, data=photo_payload)
        else:
            feed_post_endpoint = f"{GRAPH_API_URL}/{PAGE_ID}/feed"
            post_payload = {
                'message': message,
                'access_token': PAGE_ACCESS_TOKEN
            }
            print(f"Attempting to post text message to Facebook feed at {feed_post_endpoint}")
            response = requests.post(feed_post_endpoint, data=post_payload)

        response.raise_for_status()
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
