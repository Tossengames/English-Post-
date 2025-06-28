import os
import json
import requests
import re
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

TYPE_HASHTAGS = {
    "grammar_tip": "#EnglishGrammar #LearnEnglish #قواعد_اللغة_الإنجليزية",
    "vocabulary_word": "#EnglishVocabulary #WordOfTheDay #كلمات_إنجليزية",
    "common_phrase": "#EnglishPhrases #عبارات_إنجليزية #LearnEnglish",
    "common_mistake": "#EnglishMistakes #LearnFromMistakes #تعلم_الإنجليزية",
    "quiz": "#EnglishQuiz #اختبار_إنجليزي #EnglishChallenge",
    "short_story": "#EnglishStory #قصص_إنجليزية #ReadingPractice"
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
        "grammar_tip": "اكتب منشورًا جاهزًا للنشر على فيسبوك لمتعلمي اللغة الإنجليزية العرب، بدون مقدمات عامة. اشرح قاعدة نحوية بسيطة مع مثال إنجليزي وترجمه.",
        "vocabulary_word": "اكتب منشورًا جاهزًا للنشر على فيسبوك، بدون مقدمات عامة. اختر كلمة إنجليزية مفيدة، اكتب معناها بالعربية، وضعها في جملة إنجليزية مع الترجمة.",
        "common_phrase": "اكتب منشورًا عن عبارة إنجليزية شائعة. اذكر العبارة، معناها بالعربية، وجملة إنجليزية تحتويها مع الترجمة. بدون مقدمات.",
        "common_mistake": "اشرح خطأ شائعًا يرتكبه العرب في اللغة الإنجليزية. اذكر المثال الخاطئ، الصحيح، والشرح، بدون مقدمات.",
        "quiz": "أنشئ سؤالًا بسيطًا باللغة الإنجليزية مع 4 اختيارات A, B, C, D. لا تستخدم جمل تمهيدية ولا تذكر الإجابة الصحيحة. التنسيق يجب أن يكون:\n\nالسؤال\n\nA) ...\nB) ...\nC) ...\nD) ...",
        "short_story": "اكتب قصة قصيرة أو حوارًا بسيطًا بين شخصين باللغة الإنجليزية، مع الترجمة العربية لكل سطر. بدون مقدمات."
    }
    return prompts.get(post_type, "اكتب شيئًا مفيدًا لتعلم اللغة الإنجليزية، بدون مقدمات.")

# == Spacing & Formatting ==
def fix_spacing_and_formatting(text, post_type):
    lines = text.splitlines()
    english_lines = []
    arabic_lines = []
    other_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r'^[A-Da-d]\)', stripped):
            # Quiz option like A) ...
            other_lines.append(stripped)
        elif re.search(r'[A-Za-z]', stripped) and not re.search(r'[\u0600-\u06FF]', stripped):
            english_lines.append(stripped)
        elif re.search(r'[\u0600-\u06FF]', stripped):
            arabic_lines.append(stripped)
        else:
            other_lines.append(stripped)

    result_lines = []

    if post_type == "short_story":
        result_lines += english_lines + ["", "---", ""] + arabic_lines
    elif post_type == "quiz":
        result_lines += english_lines + other_lines
    else:
        result_lines += lines

    return "\n".join(result_lines)

# == Gemini 2.0 Flash Call ==
def generate_post_content(post_type):
    prompt = build_prompt(post_type)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={os.getenv('GEMINI_API_KEY')}"
    headers = {"Content-Type": "application/json"}
    body = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(url, headers=headers, json=body)
        data = response.json()

        if "error" in data:
            print("⚠️ Gemini API error:", data["error"]["message"])
            return None

        text = data["candidates"][0]["content"]["parts"][0]["text"]

        # Remove AI filler phrases
        for bad_phrase in [
            "بالتأكيد،", "بالطبع،", "إليك ", "ها هو ", "ها هي ",
            "Sure! ", "Of course, ", "Here is ", "Here's ", "Let me show you"
        ]:
            text = text.replace(bad_phrase, "")

        # Remove markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        text = re.sub(r'^\s*[\*\-]\s*', '', text, flags=re.MULTILINE)

        clean_text = fix_spacing_and_formatting(text.strip(), post_type)
        hashtags = TYPE_HASHTAGS.get(post_type, "")
        return f"{TYPE_HEADERS[post_type]}\n\n{clean_text}\n\n{hashtags}"

    except Exception as e:
        print("⚠️ Exception:", str(e))
        return None

# == Facebook Posting ==
def post_text_to_facebook(page_id, token, message):
    url = f"https://graph.facebook.com/{page_id}/feed"
    payload = {"message": message, "access_token": token}
    r = requests.post(url, data=payload)
    print(f"[{page_id}] → {r.status_code}: {r.text[:200]}")

# == Main Runner ==
if __name__ == "__main__":
    post_type = get_next_post_type()
    print(f"📢 Generating post type: {post_type}")
    message = generate_post_content(post_type)

    if message:
        post_text_to_facebook(
            os.getenv("FB_PAGE_ID"),
            os.getenv("FB_PAGE_TOKEN"),
            message
        )
    else:
        print("🚫 Skipping post due to content generation failure.")
