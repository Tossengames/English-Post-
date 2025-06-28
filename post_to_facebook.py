import os
import requests
import random
import google.generativeai as genai
import json
from pathlib import Path

# ENV VARS
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")
FB_PAGE_TOKENS = os.getenv("FB_PAGE_TOKENS").split(",")
FB_PAGE_IDS = os.getenv("FB_PAGE_IDS").split(",")

# File to track last used post type
STATE_FILE = Path("post_state.json")

# Post types
POST_TYPES = [
    "grammar_tip",
    "vocabulary_word",
    "common_phrase",
    "common_mistake",
    "quiz",
    "short_story"
]

# Arabic headers per type
TYPE_HEADERS = {
    "grammar_tip": "📘 قاعدة اليوم:",
    "vocabulary_word": "🧠 كلمة اليوم:",
    "common_phrase": "🗣️ عبارة اليوم:",
    "common_mistake": "⚠️ خطأ شائع:",
    "quiz": "❓ سؤال اليوم:",
    "short_story": "📖 قصة قصيرة:"
}

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro")

def load_last_type_index():
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
            return data.get("last_index", -1)
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
    if post_type == "grammar_tip":
        return (
            "اكتب قاعدة نحوية مفيدة، واشرحها باللغة العربية مع مثال واحد باللغة الإنجليزية."
        )
    elif post_type == "vocabulary_word":
        return (
            "اختر كلمة إنجليزية واحدة مفيدة، ثم أعطِ معناها بالعربية، واستخدمها في جملة إنجليزية كمثال."
        )
    elif post_type == "common_phrase":
        return (
            "اختر عبارة إنجليزية شائعة (idiom أو expression)، ووضح معناها بالعربية، وأضف مثالًا إنجليزيًا."
        )
    elif post_type == "common_mistake":
        return (
            "اشرح خطأ شائعًا يرتكبه المتعلمون في اللغة الإنجليزية، مع المثال الخاطئ والمثال الصحيح، وشرح السبب."
        )
    elif post_type == "quiz":
        return (
            "أنشئ سؤال اختيار من متعدد بسيط باللغة الإنجليزية لمتعلمي اللغة، وضع 4 اختيارات، وأشر للإجابة الصحيحة لاحقًا، لكن لا تذكر الإجابة في المنشور."
        )
    elif post_type == "short_story":
        return (
            "اكتب حوارًا قصيرًا (2-3 جمل) أو قصة قصيرة جدًا بين شخصين باللغة الإنجليزية، ثم ترجمها للعربية."
        )

def generate_post_content(post_type):
    prompt = build_prompt(post_type)
    response = model.generate_content(prompt)
    content = response.text.strip()
    return f"{TYPE_HEADERS[post_type]}\n\n{content}"

def get_pixabay_image(keyword):
    url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={keyword}&image_type=photo&per_page=3"
    r = requests.get(url)
    data = r.json()
    if data.get("hits"):
        return data["hits"][0]["largeImageURL"]
    return None

def post_to_facebook(page_id, token, message, image_url):
    url = f"https://graph.facebook.com/{page_id}/photos"
    payload = {
        "url": image_url,
        "caption": message,
        "access_token": token
    }
    r = requests.post(url, data=payload)
    print(f"[{page_id}] Status: {r.status_code} - {r.text[:200]}")

def extract_keyword(text):
    # Try to extract a word from English part
    words = [word.strip(".,:;!?") for word in text.split() if word.isalpha() and word[0].isupper()]
    return words[0] if words else "English"

# Main
if __name__ == "__main__":
    post_type = get_next_post_type()
    print(f"➡️ Generating post type: {post_type}")
    message = generate_post_content(post_type)
    keyword = extract_keyword(message)
    image_url = get_pixabay_image(keyword)

    if not image_url:
        image_url = get_pixabay_image("language")

    for page_id, token in zip(FB_PAGE_IDS, FB_PAGE_TOKENS):
        post_to_facebook(page_id, token, message, image_url)
