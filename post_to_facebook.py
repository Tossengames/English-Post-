import os
import json
import random
import datetime
import requests
import mimetypes

import google.generativeai as genai
from docx import Document
from PyPDF2 import PdfReader

# ENV VARS
FB_PAGE_TOKEN = os.environ.get("FB_PAGE_TOKEN")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
POST_TYPE_OVERRIDE = os.environ.get("POST_TYPE_OVERRIDE", "auto")  # auto, teacher, or random

# Gemini setup
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-2.0-flash")

# File paths
CHARACTER_CONFIG_PATH = "characters/character_config.json"
POST_STATE_PATH = "post_state.json"
POST_LOG_PATH = "post_log.json"

# Types of posts
POST_TYPES = ["شرح", "تلخيص", "أسئلة", "حل", "تدريب", "أمثلة", "معلومة"]

# Utility Functions
def folder_has_valid_files(folder, valid_extensions):
    if not os.path.exists(folder):
        return False
    return any(
        any(file.lower().endswith(ext) for ext in valid_extensions)
        for file in os.listdir(folder)
    )

def read_file_content(filepath):
    if filepath.endswith(".txt"):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    elif filepath.endswith(".docx"):
        doc = Document(filepath)
        return "\n".join(p.text for p in doc.paragraphs)
    elif filepath.endswith(".pdf"):
        reader = PdfReader(filepath)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return ""

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def choose_next_character(characters, post_state):
    index = post_state.get("character_index", 0)
    character = list(characters.keys())[index % len(characters)]
    post_state["character_index"] = index + 1
    return character

def pick_random_file(folder, extensions):
    files = [f for f in os.listdir(folder) if any(f.lower().endswith(ext) for ext in extensions)]
    return os.path.join(folder, random.choice(files)) if files else None

def clean_gemini_response(text):
    lines = text.strip().splitlines()
    return "\n".join(line.strip("* ").strip() for line in lines if line.strip())

def generate_post_content(text, style, post_type):
    prompt = (
        f"You are an Arabic English teacher. Use the following material:\n\n"
        f"{text}\n\n"
        f"Write a Facebook post in Arabic to do a '{post_type}' of this content. Use this style:\n\n{style}\n\n"
        f"Do NOT introduce yourself or mention AI. Just return final post content."
    )
    try:
        response = model.generate_content(prompt)
        return clean_gemini_response(response.text)
    except Exception as e:
        print(f"⚠️ AI generation failed: {e}")
        return None

def post_to_facebook(message, image_path=None):
    url = f"https://graph.facebook.com/{FB_PAGE_ID}/photos" if image_path else f"https://graph.facebook.com/{FB_PAGE_ID}/feed"
    payload = {"caption" if image_path else "message": message, "access_token": FB_PAGE_TOKEN}
    files = None

    if image_path:
        mime = mimetypes.guess_type(image_path)[0]
        files = {"source": (os.path.basename(image_path), open(image_path, "rb"), mime)}

    response = requests.post(url, data=payload, files=files)
    if response.status_code != 200:
        print(f"❌ Facebook post failed: {response.text}")
    else:
        print("✅ Post published successfully.")

def post_random_fallback():
    try:
        print("📌 Posting fallback random post...")
        fallback = model.generate_content(
            "Give an English tip, quiz, or word with Arabic explanation. Don’t introduce yourself. Just return the post."
        )
        message = clean_gemini_response(fallback.text)
        post_to_facebook(message)
        return True
    except Exception as e:
        print(f"❌ Fallback post failed: {e}")
        return False

# Main Logic
def main():
    post_state = load_json(POST_STATE_PATH, {})
    characters = load_json(CHARACTER_CONFIG_PATH, {})
    post_log = load_json(POST_LOG_PATH, {})

    current_hour = datetime.datetime.utcnow().hour + 2  # Cairo Time (UTC+2)
    today_str = datetime.date.today().isoformat()

    # Determine post type
    if POST_TYPE_OVERRIDE == "random":
        post_type = "🌀 عشوائي"
    elif POST_TYPE_OVERRIDE == "teacher":
        post_type = "📘 من الكتاب"
    elif current_hour < 12:
        post_type = "📘 من الكتاب"
    elif current_hour < 18:
        post_type = "🌀 عشوائي"
    else:
        post_type = "📘 من الكتاب"

    # RANDOM POST SLOT
    if post_type == "🌀 عشوائي":
        if not post_random_fallback():
            print("🛑 Could not generate midday fallback.")
        return

    # TEACHER POST SLOT
    character_name = post_state.get("current_character")
    if not character_name or today_str != post_state.get("last_used_date"):
        character_name = choose_next_character(characters, post_state)
        post_state["current_character"] = character_name
        post_state["last_used_date"] = today_str

    char_info = characters.get(character_name)
    if not char_info:
        print("⚠️ No character config found.")
        return

    book_folder = char_info["book_folder"]
    image_folder = char_info["folder"]

    has_books = folder_has_valid_files(book_folder, [".txt", ".pdf", ".docx"])
    has_images = folder_has_valid_files(image_folder, [".jpg", ".png", ".jpeg"])

    if not has_books or not has_images:
        print(f"⚠️ Missing files for {character_name}.")
        if POST_TYPE_OVERRIDE == "teacher":
            print("🛑 Manual override forbids fallback. Skipping.")
            return
        print("📌 Fallback to random post...")
        if not post_random_fallback():
            print("🛑 Fallback also failed.")
        return

    file_path = pick_random_file(book_folder, [".txt", ".pdf", ".docx"])
    text = read_file_content(file_path)
    style = char_info.get("style", "")
    task_type = random.choice(POST_TYPES)

    message = generate_post_content(text, style, task_type)
    if not message:
        print("⚠️ Generation failed.")
        if POST_TYPE_OVERRIDE == "teacher":
            print("🛑 Manual override forbids fallback. Skipping.")
            return
        if not post_random_fallback():
            print("🛑 Fallback also failed.")
        return

    image_path = pick_random_file(image_folder, [".jpg", ".png", ".jpeg"])
    final_message = f"👩‍🏫 {character_name}:\n\n{message}"
    post_to_facebook(final_message, image_path)

    # Save logs
    log_entry = {
        "date": today_str,
        "character": character_name,
        "type": task_type,
        "file": os.path.basename(file_path)
    }
    post_log.setdefault(today_str, []).append(log_entry)
    save_json(POST_LOG_PATH, post_log)
    save_json(POST_STATE_PATH, post_state)

if __name__ == "__main__":
    main()
