import os
import json
import random
import datetime
import requests
import google.generativeai as genai
from docx import Document
from PyPDF2 import PdfReader

# ENV VARS
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
POST_TYPE_OVERRIDE = os.getenv("POST_TYPE_OVERRIDE", "auto")

# INIT GEMINI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.0-pro")

# FILES
CONFIG_FILE = "characters/character_config.json"
STATE_FILE = "post_state.json"
LOG_FILE = "post_log.json"

# UTILS
def load_json(path, fallback):
    return json.load(open(path)) if os.path.exists(path) else fallback

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def folder_has_valid_files(folder, extensions):
    return any(file.lower().endswith(tuple(extensions)) for file in os.listdir(folder))

def read_random_file(folder):
    files = [f for f in os.listdir(folder) if f.endswith((".txt", ".pdf", ".docx"))]
    if not files:
        return None, None
    file_path = os.path.join(folder, random.choice(files))
    content = ""
    try:
        if file_path.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        elif file_path.endswith(".docx"):
            doc = Document(file_path)
            content = "\n".join([p.text for p in doc.paragraphs])
        elif file_path.endswith(".pdf"):
            reader = PdfReader(file_path)
            content = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        return None, None
    return os.path.basename(file_path), content.strip()

def select_teacher():
    state = load_json(STATE_FILE, {"last_teacher": -1})
    teachers = list(load_json(CONFIG_FILE, {}).keys())
    index = (state["last_teacher"] + 1) % len(teachers)
    state["last_teacher"] = index
    save_json(STATE_FILE, state)
    return teachers[index]

def generate_teacher_post(name, image_folder, book_folder, style, material, book_name):
    prompt = (
        f"You are a female Arabic teacher. Here is your personality: {style}. "
        f"Use the following learning material from the book '{book_name}' to create a helpful post "
        f"for Arabic-speaking English learners. Make it informative, well-formatted, and clearly human-written. "
        f"Respond only with the final post text in Arabic (no intro or system text). "
        f"Content:\n\n{material[:3000]}"
    )
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return None

def generate_random_post():
    prompt = (
        "Create a helpful short English learning post for Arabic speakers. Include vocabulary or a quiz. "
        "Respond in Arabic only. Format cleanly, no markdown or bold symbols like '**'. Avoid AI phrases."
    )
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return None

def post_to_facebook(message, image_path=None):
    url = f"https://graph.facebook.com/{FB_PAGE_ID}/photos"
    data = {
        "caption": message,
        "access_token": FB_PAGE_TOKEN
    }
    files = {"source": open(image_path, "rb")} if image_path else None
    response = requests.post(url, data=data, files=files)
    if response.status_code == 200:
        print("✅ Post published successfully.")
        return True
    print("❌ Post failed:", response.text)
    return False

def main():
    config = load_json(CONFIG_FILE, {})
    post_log = load_json(LOG_FILE, {})

    today = datetime.date.today()
    today_str = today.isoformat()
    current_hour = datetime.datetime.now().hour

    # Determine post type
    if POST_TYPE_OVERRIDE == "random" or current_hour == 14:
        print("📌 Generating RANDOM midday post...")
        post = generate_random_post()
        if post:
            post_to_facebook(post)
        return

    teacher_id = select_teacher()
    teacher = config.get(teacher_id)
    if not teacher:
        print("🚫 No teacher config found.")
        return

    book_folder = teacher["book_folder"]
    image_folder = teacher["folder"]
    style = teacher["style"]
    teacher_name = teacher["name"]

    # Check for book
    if not folder_has_valid_files(book_folder, [".pdf", ".docx", ".txt"]):
        print(f"📂 No valid book for {teacher_name}, skipping...")
        return

    # Read material
    book_name, material = read_random_file(book_folder)
    if not material:
        print("⚠️ Could not read book content.")
        return

    # Generate post
    print(f"✏️ Generating post from {teacher_name} based on '{book_name}'...")
    post = generate_teacher_post(teacher_name, image_folder, book_folder, style, material, book_name)
    if not post:
        print("⚠️ AI could not generate teacher post.")
        return

    # Pick random image
    images = [f for f in os.listdir(image_folder) if f.lower().endswith((".jpg", ".png"))]
    image_path = os.path.join(image_folder, random.choice(images)) if images else None

    # Add heading
    message = f"📚 من كتاب: {book_name}\n\n{post}"

    # Post to Facebook
    success = post_to_facebook(message, image_path)

    if success:
        post_log.setdefault(today_str, []).append({
            "teacher": teacher_name,
            "book": book_name,
            "type": "teacher",
            "hour": current_hour
        })
        save_json(LOG_FILE, post_log)

if __name__ == "__main__":
    main()
