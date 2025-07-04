import os
import json
import datetime
import sys
import requests
import google.generativeai as genai
import random 

# --- Configuration (from environment variables) ---
FB_PAGE_ID = os.getenv('FB_PAGE_ID')
FB_PAGE_TOKEN = os.getenv('FB_PAGE_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# --- Gemini API Configuration ---
genai.configure(api_key=GEMINI_API_KEY)
GEMINI_MODEL = genai.GenerativeModel('gemini-1.5-flash') 

# --- File Operations ---
def read_json(filename, default_value=None):
    """
    Reads a JSON file, returns its content, or a default value if file doesn't exist or is corrupted.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Warning: {filename} not found or corrupted. Initializing with default value.")
        if default_value is not None:
            return default_value
        return {}

def write_json(filename, data):
    """Writes data to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# --- Post to Facebook Function (UPDATED for images) ---
def post_to_facebook(message, image_url=None):
    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
    params = {
        'message': message,
        'access_token': FB_PAGE_TOKEN
    }
    if image_url:
        params['picture'] = image_url # Use 'picture' for link preview or attached image
        # For actual photo upload, it's more complex (requires /photos endpoint)
        # For simplicity, we'll use 'picture' which often works for linking images.
        # If you need direct photo upload, we'd adjust this.
        print(f"Attempting to attach image from: {image_url}")

    response = requests.post(url, params=params)
    if response.status_code == 200:
        print("Successfully posted to Facebook!")
        print(response.json())
        return True
    else:
        print(f"Error posting to Facebook: {response.status_code}")
        print(response.json())
        return False

# --- AI Content Generation ---
def generate_ai_post(prompt_text):
    response = None
    try:
        response = GEMINI_MODEL.generate_content(prompt_text)
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

# --- Post Type Generators (Simplified) ---

# Teacher Post Generator
def generate_teacher_post_content(teacher_meta_data):
    # Randomly select a teacher
    teacher_ids = list(teacher_meta_data.keys())
    if not teacher_ids:
        print("No teachers found in teacher_meta.json.")
        return None, None, None # content, type, image_url

    random_teacher_id = random.choice(teacher_ids)
    teacher = teacher_meta_data[random_teacher_id]

    # Randomly select a lesson from the teacher's queue
    if not teacher.get("lesson_queue"):
        print(f"Teacher {teacher['name']} has no lessons in their queue.")
        return None, None, None
    
    lesson_topic = random.choice(teacher["lesson_queue"])
    posting_style = teacher["posting_style"]
    teacher_image_url = teacher.get("profile_image_url") # Get image URL

    prompt = (
        f"You are an English teacher named {teacher['name']}. Your persona and teaching style are: '{posting_style}'. "
        f"Your current lesson topic is: '{lesson_topic}'. "
        f"Explain this topic clearly and concisely, including key points. "
        f"Your post should be engaging and encourage interaction, always including a call to action to like, share, and comment. "
        f"Keep it within 150-200 words, using the specified Arabic dialect if mentioned in the posting style.\n\n"
    )
    
    ai_post_content = generate_ai_post(prompt)

    if ai_post_content:
        return ai_post_content, "teacher", teacher_image_url, teacher['name'], lesson_topic
    return None, None, None, None, None

# Random Post Generator
def generate_random_post_content(random_topics_data):
    if not random_topics_data:
        print("No random topics found in random_topics.json.")
        return None, None # content, type

    topic_data = random.choice(random_topics_data)
    
    prompt = (
        f"Create an engaging Facebook post about: {topic_data['topic']}. "
        f"Include interesting facts or a brief explanation from this content: {topic_data['content']}. "
        f"The post should be positive, concise (150-200 words), and encourage interaction "
        f"(e.g., ask a question related to the topic for comments). "
        f"Always include a call to action to like, share, and comment."
    )

    ai_post_content = generate_ai_post(prompt)
    if ai_post_content:
        return ai_post_content, "random", topic_data["topic"]
    return None, None, None

# --- Main Orchestration Logic (Simplified) ---
def main():
    # We still keep post_log.json for recording purposes
    post_log = read_json("post_log.json", default_value=[])

    teacher_meta_data = read_json("teacher_meta.json", default_value={})
    random_topics_data = read_json("random_topics.json", default_value=[])

    if not teacher_meta_data and not random_topics_data:
        print("ERROR: Both teacher_meta.json and random_topics.json are empty or missing. Cannot generate any posts.")
        sys.exit(1)

    # --- Decide Post Type Randomly ---
    # Give higher chance to teacher posts if both exist
    post_type_options = []
    if teacher_meta_data:
        post_type_options.extend(["teacher"] * 2) # e.g., 66% chance for teacher
    if random_topics_data:
        post_type_options.append("random") # e.g., 33% chance for random

    if not post_type_options:
        print("No content sources available (teachers or random topics). Exiting.")
        sys.exit(0)

    chosen_post_type = random.choice(post_type_options)
    print(f"Randomly chosen post type for this run: {chosen_post_type}")

    generated_content = None
    post_image_url = None
    log_data_extra = {}

    if chosen_post_type == "teacher":
        generated_content, post_category, post_image_url, teacher_name, lesson_topic = generate_teacher_post_content(teacher_meta_data)
        if generated_content:
            log_data_extra = {
                "teacher_name": teacher_name,
                "lesson_topic": lesson_topic
            }
        else:
            print("Failed to generate content for a teacher post. Trying random post instead if available.")
            if "random" in post_type_options:
                chosen_post_type = "random" # Fallback
            else:
                print("No fallback to random post. Exiting.")
                sys.exit(1)

    if chosen_post_type == "random": # This branch can be reached directly or as a fallback
        generated_content, post_category, topic_name = generate_random_post_content(random_topics_data)
        if generated_content:
            log_data_extra = {
                "topic_name": topic_name
            }
        else:
            print("Failed to generate content for a random post. Exiting.")
            sys.exit(1) # No more fallbacks

    if generated_content:
        print("\n--- Generated Post ---")
        print(generated_content)
        print("----------------------\n")

        success = post_to_facebook(generated_content, post_image_url)
        if success:
            post_log.append({
                "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                "type": post_category,
                "content_summary": generated_content[:200] + "..." if len(generated_content) > 200 else generated_content,
                "image_posted": bool(post_image_url),
                **log_data_extra # Add teacher_name/lesson_topic or topic_name
            })
            write_json("post_log.json", post_log)
            print("Post successful and log updated.")
        else:
            print("Post failed. Log not updated for this entry.")
    else:
        print("No content was generated for posting. Exiting.")

    sys.exit(0) # Ensure script always exits gracefully


if __name__ == "__main__":
    main()
