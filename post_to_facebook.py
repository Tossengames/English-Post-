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

# == Post Type Tracking ==
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

# == Prompt Builder ==
def build_prompt(post_type):
    prompts = {
        "grammar_tip": "اكتب منشورًا جاهزًا للنشر على فيسبوك لمتعلمي اللغة الإنجليزية العرب، بدون مقدمات عامة مثل 'بالتأكيد' أو 'إليك'. اشرح قاعدة نحوية بسيطة مع مثال إنجليزي وترجمه.",
        "vocabulary_word": "اكتب منشورًا جاهزًا للنشر على فيسبوك، بدون مقدمات عامة مثل 'بالتأكيد' أو 'إليك'. اختر كلمة إنجليزية مفيدة، اكتب معناها بالعربية، وضعها في جملة إنجليزية مع الترجمة.",
        "common_phrase": "اكتب منشورًا عن عبارة إنجليزية شائعة. اذكر العبارة، معناها بالعربية، وجملة إنجليزية تحتويها مع الترجمة. بدون مقدمات عامة.",
        "common_mistake": "اشرح خطأ شائعًا يرتكبه العرب في اللغة الإنجليزية. اذكر المثال الخاطئ، الصحيح، والشرح، بدون استخدام مقدمات مثل 'بالطبع' أو 'إليك'.",
        "quiz": "أنشئ سؤالًا بسيطًا باللغة الإنجليزية مع 4 اختيارات (A, B, C, D) لفيسبوك. لا تذكر الإجابة الصحيحة في المنشور. لا تبدأ بجمل تمهيدية.",
        "short_story": "اكتب قصة قصيرة أو حوارًا بسيطًا بين شخصين باللغة الإنجليزية، مع الترجمة العربية لكل سطر. بدون مقدمات عامة."
    }
    return prompts.get(post_type, "اكتب شيئًا مفيدًا لتعلم اللغة الإنجليزية، بدون مقدمات عامة.")

# == Gemini 2.0 Flash Call ==
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

        # 🧹 Clean AI-style intros
        for bad_phrase in [
            "بالتأكيد،", "بالطبع،", "إليك ", "ها هو ", "ها هي ", 
            "Sure! ", "Of course, ", "Here is ", "Here's ", "Let me show you"
        ]:
            text = text.replace(bad_phrase, "")

        return f"{TYPE_HEADERS[post_type]}\n\n{text.strip()}"
    except Exception as e:
        return f"{TYPE_HEADERS[post_type]}\n\n⚠️ تعذر توليد المحتوى تلقائيًا: {str(e)}"

# == Facebook Post ==
def post_text_to_facebook(page_id, token, message):
    url = f"https://graph.facebook.com/{page_id}/feed"
    payload = {
        "message": message,
        "access_token": token
    }
    r = requests.post(url, data=payload)
    print(f"[{page_id}] → {r.status_code}: {r.text[:200]}")

# == Run ==
if __name__ == "__main__":
    post_type = get_next_post_type()
    print(f"📢 Generating post type: {post_type}")
    message = generate_post_content(post_type)
    post_text_to_facebook(
        os.getenv("FB_PAGE_ID"),
        os.getenv("FB_PAGE_TOKEN"),
        message
    )
