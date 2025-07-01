import os
import json
import random
import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

# Environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")

# Paths
TEACHERS_FILE = "teachers.json"
POST_STATE_FILE = "post_state.json"

def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def select_teacher(state, teachers):
    last_teacher = state.get("last_teacher", -1)
    ids = list(teachers.keys())
    if not ids:
        return None
    next_index = (last_teacher + 1) % len(ids)
    state["last_teacher"] = next_index
    return ids[next_index]

def select_image(folder):
    if not os.path.isdir(folder):
        return None
    images = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    return os.path.join(folder, random.choice(images)) if images else None

def generate_teacher_prompt(name, style, topic):
    return f"""You are {name}, a female Arabic English teacher. Your tone is {style}.
Generate an engaging educational post in Arabic for students on the topic: "{topic}".
Avoid saying you're an AI or introducing the task. Just write the post directly and clearly.
Include example sentences, explanation, translation, and a quick question if possible."""

def generate_random_prompt():
    return """Generate an educational English learning post in Arabic. It could be a word of the day, a grammar tip, a quiz, or a motivational tip.
Write the post clearly and naturally. Avoid saying “Sure!” or “Here's your post.” Just write the post as if it were written by a human teacher.
Use simple Modern Standard Arabic for Arabic parts, and format the content cleanly without asterisks or clutter."""

def call_gemini_api(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-pro:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.ok:
        try:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            return None
    return None

def post_to_facebook(message, image_path=None):
    url = f"https://graph.facebook.com/{FB_PAGE_ID}/photos"
    data = {
        "caption": message,
        "access_token": FB_PAGE_TOKEN
    }
    if image_path:
        with open(image_path, "rb") as img:
            files = {"source": img}
            response = requests.post(url, data=data, files=files)
    else:
        url = f"https://graph.facebook.com/{FB_PAGE_ID}/feed"
        data = {"message": message, "access_token": FB_PAGE_TOKEN}
        response = requests.post(url, data=data)
    return response.ok

def main():
    now = datetime.datetime.now()
    hour = now.hour
    today_str = now.strftime("%Y-%m-%d")

    # Load or initialize state
    state = load_json(POST_STATE_FILE)
    post_log = state.get("log", {})

    # Check time slot
    if hour < 10:
        time_slot = "morning"
    elif hour < 17:
        time_slot = "midday"
    else:
        time_slot = "evening"

    if today_str not in post_log:
        post_log[today_str] = []

    if time_slot in post_log[today_str]:
        print(f"✅ Already posted in {time_slot}. Skipping.")
        return

    teachers = load_json(TEACHERS_FILE)
    post_success = False

    if time_slot in ["morning", "evening"]:
        teacher_id = select_teacher(state, teachers)
        teacher = teachers.get(teacher_id)
        if teacher:
            name = teacher["name"]
            style = teacher["style"]
            lesson_queue = teacher["lesson_queue"]
            index = teacher.get("current_index", 0)

            if index < len(lesson_queue):
                topic = lesson_queue[index]
                prompt = generate_teacher_prompt(name, style, topic)
                result = call_gemini_api(prompt)

                if result:
                    teacher["current_index"] = index + 1
                    teacher["history"].append({
                        "date": today_str,
                        "topic": topic
                    })
                    image_path = select_image(teacher["folder"])
                    message = f"📘 الدرس اليوم من {name}:\n\n{result}"
                    post_success = post_to_facebook(message, image_path)
                else:
                    print("⚠️ AI failed to generate teacher post.")
            else:
                print(f"⚠️ No more lessons for {name}")
        else:
            print("⚠️ Teacher not found.")
    elif time_slot == "midday":
        prompt = generate_random_prompt()
        result = call_gemini_api(prompt)
        if result:
            post_success = post_to_facebook(result)

    if post_success:
        post_log[today_str].append(time_slot)
        state["log"] = post_log
        save_json(POST_STATE_FILE, state)
        save_json(TEACHERS_FILE, teachers)
        print("✅ Post published successfully.")
    else:
        print("❌ Failed to post.")

if __name__ == "__main__":
    main()
