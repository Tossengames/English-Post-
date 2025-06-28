# ✅ post_to_facebook.py

import os, random, json
from pathlib import Path
from datetime import datetime
import requests
import fitz  # PyMuPDF
import docx

FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

CHARACTER_CONFIG_FILE = "characters/character_config.json"
POST_TYPES_FILE = "post_types_config.json"
POST_STATE_FILE = "post_state.json"
POST_LOG_FILE = "post_log.json"

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_text_from_file(file_path):
    if file_path.endswith(".pdf"):
        doc = fitz.open(file_path)
        return "\n".join(page.get_text() for page in doc)
    elif file_path.endswith(".docx"):
        doc = docx.Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs)
    elif file_path.endswith(".txt"):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

def get_random_image_from(folder):
    images = list(Path(folder).glob("*.jpg")) + list(Path(folder).glob("*.png"))
    return str(random.choice(images)) if images else None

def build_prompt(text, post_type_prompt, style):
    return (
        f"اكتب المنشور بصيغة المعلم بدون ذكر الذكاء الاصطناعي وبدون جمل تمهيدية. "
        f"استخدم العربية الفصحى فقط.\n\n"
        f"النص:\n{text[:3000]}\n\n"
        f"نوع المنشور: {post_type_prompt}. {style}"
    )

def generate_gemini_content(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    r = requests.post(url, headers=headers, json=payload)
    try:
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return None

def post_to_facebook(message, image_path=None):
    if image_path:
        files = {'source': open(image_path, 'rb')}
        data = {'caption': message, 'access_token': FB_PAGE_TOKEN}
        url = f'https://graph.facebook.com/{FB_PAGE_ID}/photos'
    else:
        files = None
        data = {'message': message, 'access_token': FB_PAGE_TOKEN}
        url = f'https://graph.facebook.com/{FB_PAGE_ID}/feed'
    return requests.post(url, data=data, files=files).json()

def clean_filename(name):
    return name.replace(".pdf", "").replace(".docx", "").replace(".txt", "").replace("_", " ")

def log_post(entry):
    log = []
    if Path(POST_LOG_FILE).exists():
        log = load_json(POST_LOG_FILE)
    log.append(entry)
    save_json(POST_LOG_FILE, log)

def load_state():
    return load_json(POST_STATE_FILE) if Path(POST_STATE_FILE).exists() else {"day_index": 0}

def save_state(state):
    save_json(POST_STATE_FILE, state)

def create_post(post_index=0):
    state = load_state()
    characters = load_json(CHARACTER_CONFIG_FILE)
    post_types = load_json(POST_TYPES_FILE)

    teacher_keys = list(characters.keys())
    teacher_index = state["day_index"] % len(teacher_keys)
    teacher_key = teacher_keys[teacher_index]
    teacher = characters[teacher_key]

    book_folder = Path(teacher["book_folder"])
    book_files = list(book_folder.glob("*.*"))
    if not book_files:
        print("❌ لا توجد ملفات تعليمية.")
        return

    file = book_files[0]
    text = extract_text_from_file(str(file))
    post_type = random.choice(list(post_types.keys()))
    prompt = build_prompt(text, post_types[post_type], teacher["style"])
    content = generate_gemini_content(prompt)

    if not content:
        print("⚠️ فشل التوليد.")
        return

    title = f"📘 {clean_filename(file.name)}:\n"
    image = get_random_image_from(teacher["folder"])
    message = f"{title}\n{content.strip()}"
    post_to_facebook(message, image)

    log_post({
        "date": datetime.now().isoformat(),
        "teacher": teacher_key,
        "file": file.name,
        "type": post_type,
        "summary": content[:60].replace('\n', ' ')
    })

    if post_index == 2:
        state["day_index"] += 1
        save_state(state)

    print(f"✅ Posted by {teacher_key} ({post_type})")

if __name__ == '__main__':
    import sys
    index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    create_post(index)
