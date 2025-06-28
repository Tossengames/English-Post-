import os
import json
import requests
from pathlib import Path

# == Constants ==
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
                return json.load(f).get("last_index", -1)
        except:
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
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={os.getenv('GEMINI_API_KEY')}"
    
    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=body)
        data = response.json()
        if "error" in data:
            raise Exception(data["error"]["message"])
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return f"{TYPE_HEADERS[post_type]}\n\n{text.strip()}"
    except Exception as e:
        return f"{TYPE_HEADERS[post_type]}\n\n⚠️ تعذر توليد المحتوى تلقائيًا: {str(e)}"

def post_text_to_facebook(page_id, token, message):
    url = f"https://graph.facebook.com/{page_id}/feed"
    payload = {
        "message": message,
        "access_token": token
    }
    r = requests.post(url, data=payload)
    print(f"[{page_id}] → {r.status_code}: {r.text[:200]}")

if __name__ == "__main__":
    post_type = get_next_post_type()
    print(f"📢 Generating post type: {post_type}")
    message = generate_post_content(post_type)
    post_text_to_facebook(
        os.getenv("FB_PAGE_ID"),
        os.getenv("FB_PAGE_TOKEN"),
        message
    )
