import os
import json
import requests
import re
from pathlib import Path

# === CONFIG ===
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

# === TRACK POST TYPE ===
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

# === PROMPT BUILDER (ENGLISH PROMPT / ARABIC MSA OUTPUT) ===
def build_prompt(post_type):
    common_suffix = " Respond only in Modern Standard Arabic (الفصحى). Do not use dialect or spoken Arabic. Do not explain. Just return the final post."

    prompts = {
        "grammar_tip": "Act like an Arabic English teacher. Write a short Facebook post explaining one English grammar rule with an English example and Arabic translation." + common_suffix,
        "vocabulary_word": "You are an Arabic English teacher. Write a Facebook post showing a useful English word, its Arabic meaning, an example sentence in English, and its Arabic translation. Do NOT explain what you're doing." + common_suffix,
        "common_phrase": "Write a Facebook post sharing one common English phrase, its Arabic meaning, an English sentence using it, and Arabic translation." + common_suffix,
        "common_mistake": "Write a Facebook post that highlights a common mistake Arabic speakers make in English. Show the wrong and correct sentence, and explain the mistake. Just return the Arabic post." + common_suffix,
        "quiz": "Write a multiple-choice quiz about English with 4 options (A-D). The whole quiz must be in Arabic. Do not give the answer. Format it clearly like a teacher wrote it." + common_suffix,
        "short_story": "Write a short dialogue between two people in English. Under each line, write its Arabic translation in Modern Standard Arabic. No intro or explanation." + common_suffix
    }

    return prompts.get(post_type, "Write a helpful educational post. " + common_suffix)

# === FORMAT CLEANUP ===
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

# === GENERATE POST CONTENT USING GEMINI API ===
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

        # Clean AI/assistant phrases
        for bad_phrase in [
            "بالتأكيد", "بالطبع", "حسنًا", "إليك", "ها هو", "ها هي", 
            "Sure", "Of course", "Okay", "Here is", "Here’s", "Let me"
        ]:
            text = text.replace(bad_phrase, "")

        # Clean formatting
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

# === POST TO FACEBOOK ===
def post_text_to_facebook(page_id, token, message):
    url = f"https://graph.facebook.com/{page_id}/feed"
    payload = {"message": message, "access_token": token}
    r = requests.post(url, data=payload)
    print(f"[{page_id}] → {r.status_code}: {r.text[:200]}")

# === MAIN ===
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
