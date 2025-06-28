import os
import json
import random
import datetime
import requests
import google.generativeai as genai
from docx import Document
from PyPDF2 import PdfReader

# ENV VARIABLES
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
POST_TYPE_OVERRIDE = os.getenv("POST_TYPE_OVERRIDE", "auto")

# INIT MODEL
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.0-pro")

# CONFIG FILES
CONFIG_FILE = "characters/character_config.json"
STATE_FILE = "post_state.json"
LOG_FILE = "post_log.json"

# HELPERS
def load_json(path, fallback):
    return json.load(open(path)) if os.path.exists(path) else fallback

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
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
    state = load_json(STATE_FILE, {})
    teachers = list(load_json(CONFIG_FILE, {}).keys())
    last_index = state.get("last_teacher", -1)
    index = (last_index + 1) % len(teachers)
    state["last_teacher"] = index
    save_json(STATE_FILE, state)
    return teachers[index]

def generate_teacher_post(name, image_folder, book_folder, style, material, book_name):
    prompt = (
        f"You are an Arabic female English teacher. Your personality: {style}.\n"
        f"Using the book titled '{book_name}', generate a helpful, natural-sounding educational post "
        f"to help Arabic-speaking English learners.\n"
        f"Use Modern Standard Arabic only, no dialects unless specified, and remove any AI phrases.\n"
        f"Do not use ** formatting. Only return the final formatted Arabic post.\n\n"
        f"Text to learn from:\n{material[:3000]}"
    )
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return None

def generate_random_post():
    prompt = (
        "Create a helpful short English learning post for Arabic speakers. "
        "It should include vocabulary, grammar tips, or a quiz. "
        "Avoid any AI phrases like 'Sure' or 'Here is'. Do not use ** formatting. "
        "Respond only in Modern Standard Arabic."
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

    # Decide post type
    if POST_TYPE_OVERRIDE == "random" or current_hour == 14:
        print("🔁 Generating random midday post...")
        post = generate_random_post()
        if post:
            post_to_facebook(post)
        return

    # TEACHER POST FLOW
    teacher_id = select_teacher()
    teacher = config.get(teacher_id)
    if not teacher:
        print("🚫 No teacher config found.")
        return

    teacher_name = teacher["name"]
    image_folder = teacher["folder"]
    book_folder = teacher["book_folder"]
    style = teacher["style"]

    if not folder_has_valid_files(book_folder, [".pdf", ".docx", ".txt"]):
        print("📂 No valid learning files found.")
        return

    book_name, material = read_random_file(book_folder)
    if not material:
        print("⚠️ Couldn't read learning material.")
        return

    print(f"📘 Generating post for: {teacher_name} using book: {book_name}")
    post = generate_teacher_post(teacher_name, image_folder, book_folder, style, material, book_name)
    if not post:
        print("⚠️ AI failed to generate post.")
        return

    # Select image
    image_files = [f for f in os.listdir(image_folder) if f.lower().endswith((".jpg", ".png"))]
    image_path = os.path.join(image_folder, random.choice(image_files)) if image_files else None

    # Final message
    message = f"📖 من كتاب: {book_name}\n\n{post}"

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
