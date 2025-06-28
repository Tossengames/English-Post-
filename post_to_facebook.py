import os
import json
import requests
from pathlib import Path
import google.generativeai as genai

# ✅ Configure Gemini (MakerSuite)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("models/gemini-pro")  # Gemini 1.0

# ✅ Facebook config from GitHub Secrets
FB_PAGE_TOKENS = os.getenv("FB_PAGE_TOKENS").split(",")
FB_PAGE_IDS = os.getenv("FB_PAGE_IDS").split(",")

# ✅ Track which post type was used last
STATE_FILE = Path("post_state.json")
POST_TYPES = [
    "grammar_tip", "vocabulary_word", "common_phrase",
    "common_mistake", "quiz", "short_story"
]

TYPE_HEADERS = {
    "grammar_tip": "📘 قاعدة اليوم:",
    "vocabulary_word": "🧠 كلمة اليوم:",
    "common_phrase": "🗣️ عبارة اليوم:",
    "common_mistake": "⚠️ خطأ شائع:",
    "quiz": "❓ سؤال اليوم:",
    "short_story": "📖 قصة قصيرة:"
}

def load_last_type_index():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
                return data.get("last_index", -1)
        except json.JSONDecodeError:
            return -1
    return -1

def save_type_index(index):
    with open(STATE_FILE, "w") as f:
        json.dump({"last_index": index}, f)

def get_next_post_type():
    last_index = load_last_type_index()
    next_index = (last_index + 1) % len(POST_TYPES)
    save_type_index(next_index)
    return POST_TYPES[next_index]

def build_prompt(post_type):
    prompts = {
        "grammar_tip": "اكتب قاعدة نحوية مفيدة للمتعلمين العرب، واشرحها باللغة العربية مع مثال باللغة الإنجليزية.",
        "vocabulary_word": "اختر كلمة إنجليزية مفيدة، ثم أعطِ معناها بالعربية، واستخدمها في جملة إنجليزية.",
        "common_phrase": "اختر عبارة إنجليزية شائعة، ووضح معناها بالعربية، وأضف مثالًا إنجليزيًا.",
        "common_mistake": "اشرح خطأ شائعًا يرتكبه العرب في اللغة الإنجليزية، مع المثال الخاطئ والصحيح والشرح.",
        "quiz": "أنشئ سؤالًا بسيطًا باللغة الإنجليزية مع 4 اختيارات. لا تذكر الإجابة الصحيحة في النص.",
        "short_story": "اكتب حوارًا قصيرًا أو قصة قصيرة جدًا باللغة الإنجليزية مع ترجمتها للعربية."
    }
    return prompts.get(post_type, "اكتب شيئًا مفيدًا لتعلم اللغة الإنجليزية.")

def generate_post_content(post_type):
    prompt = build_prompt(post_type)
    try:
        response = model.generate_content(prompt)
        return f"{TYPE_HEADERS[post_type]}\n\n{response.text.strip()}"
    except Exception as e:
        return f"{TYPE_HEADERS[post_type]}\n\n⚠️ تعذر توليد المحتوى تلقائيًا. {str(e)}"

def get_pixabay_image(keyword):
    try:
        url = f"https://pixabay.com/api/?key={os.getenv('PIXABAY_API_KEY')}&q={keyword}&image_type=photo&per_page=3"
        r = requests.get(url)
        data = r.json()
        return data["hits"][0]["largeImageURL"] if data.get("hits") else None
    except:
        return None

def extract_keyword(text):
    # Pulls a likely image keyword from the generated message
    words = [word.strip(".,:;!?") for word in text.split() if word.isalpha() and word[0].isupper()]
    return words[0] if words else "language"

def post_to_facebook(page_id, token, message, image_url):
    url = f"https://graph.facebook.com/{page_id}/photos"
    payload = {
        "url": image_url,
        "caption": message,
        "access_token": token
    }
    r = requests.post(url, data=payload)
    print(f"[{page_id}] → {r.status_code}: {r.text[:200]}")

if __name__ == "__main__":
    post_type = get_next_post_type()
    print(f"📢 Generating post type: {post_type}")
    message = generate_post_content(post_type)
    keyword = extract_keyword(message)
    image_url = get_pixabay_image(keyword) or get_pixabay_image("education")

    for page_id, token in zip(FB_PAGE_IDS, FB_PAGE_TOKENS):
        post_to_facebook(page_id, token, message, image_url)
