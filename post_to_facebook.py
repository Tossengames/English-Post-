import os
import json
import datetime
import random
import requests
from google.generativeai import configure, GenerativeModel
from facebook import GraphAPI

# ENV VARS
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
configure(api_key=GEMINI_API_KEY)
model = GenerativeModel("models/gemini-1.0-pro")

STATE_FILE = "post_state.json"
RANDOM_TOPICS = ["word_of_the_day", "grammar_tip", "quiz", "short_story"]

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def select_image(images_folder):
    if not os.path.exists(images_folder):
        return None
    images = [f for f in os.listdir(images_folder) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
    if not images:
        return None
    return os.path.join(images_folder, random.choice(images))

def generate_lesson_post(teacher_name, topic, style):
    prompt = f"""أنتِ معلمة لغة إنجليزية تدعى {teacher_name}. درسك اليوم عن: {topic}.
اكتبي شرحاً واضحاً ومبسطاً للطلاب باللغة العربية الفصحى، متضمنًا أمثلة إنجليزية.
اجعلي الأسلوب {style}.
ابدئي المحتوى فورًا بدون مقدمات أو عبارات آلية."""

    try:
        response = model.generate_content(prompt)
        content = response.text.strip().replace("**", "")
        return f"📘 الدرس من {teacher_name} اليوم عن: {topic}\n\n{content}"
    except Exception as e:
        print(f"⚠️ AI failed to generate post: {e}")
        return None

def generate_exam(teacher_name, recent_topics, style):
    topics_text = "، ".join(recent_topics)
    prompt = f"""أنتِ معلمة لغة إنجليزية تدعى {teacher_name}.
خلال الأسبوع شرحت المواضيع التالية: {topics_text}.
اكتبي اختبارًا بسيطًا من 5 أسئلة متنوعة (اختيار من متعدد، صح أو خطأ، أكمل الفراغ).
اكتبيه بالفصحى، وابدئي مباشرة بالأسئلة."""

    try:
        response = model.generate_content(prompt)
        return f"📝 اختبار الأسبوع من {teacher_name}\n\n{response.text.strip()}"
    except Exception as e:
        print(f"⚠️ AI failed to generate exam: {e}")
        return None

def generate_random_post(post_type):
    prompts = {
        "word_of_the_day": "اكتب كلمة إنجليزية مع معناها بالعربية، واستخدمها في جملة، وترجم الجملة أيضاً.",
        "grammar_tip": "اشرح قاعدة نحوية إنجليزية بسيطة مع مثال وجملة وشرح بالعربية.",
        "quiz": "اكتب سؤال اختيار من متعدد بسيط في اللغة الإنجليزية، مع 4 اختيارات، ووضح الجواب الصحيح وترجم كل شيء للعربية.",
        "short_story": "اكتب محادثة قصيرة بين شخصين باللغة الإنجليزية، مع الترجمة الكاملة إلى العربية."
    }

    prompt = f"""{prompts[post_type]}
اكتب بصيغة مبسطة وبدون مقدمات آلية. لا تستخدم "**"، فقط النص العادي."""

    try:
        response = model.generate_content(prompt)
        content = response.text.strip().replace("**", "")
        titles = {
            "word_of_the_day": "🧠 كلمة اليوم:",
            "grammar_tip": "📘 قاعدة اليوم:",
            "quiz": "❓ سؤال اليوم:",
            "short_story": "📖 قصة قصيرة:"
        }
        return f"{titles[post_type]}\n\n{content}"
    except Exception as e:
        print(f"⚠️ Random post generation failed: {e}")
        return None

def post_to_facebook(message, image_path=None):
    try:
        graph = GraphAPI(access_token=FB_PAGE_TOKEN)
        if image_path:
            with open(image_path, "rb") as img:
                graph.put_photo(image=img, album_path=f"{FB_PAGE_ID}/photos", message=message)
        else:
            graph.put_object(parent_object=FB_PAGE_ID, connection_name="feed", message=message)
        print("✅ Post published successfully.")
        return True
    except Exception as e:
        print(f"❌ Facebook post failed: {e}")
        return False

def main():
    state = load_state()
    today = datetime.datetime.now()
    weekday = today.weekday()

    teacher_ids = list(state.keys())
    teacher_id = teacher_ids[weekday % len(teacher_ids)]
    teacher = state[teacher_id]

    queue = teacher.get("lesson_queue", [])
    index = teacher.get("current_index", 0)
    history = teacher.setdefault("history", [])
    name = teacher.get("name", teacher_id)
    style = teacher.get("style", "رسمية")
    folder = teacher.get("folder", f"characters/{teacher_id}")
    image = select_image(folder)

    # TEACHER POST (Morning)
    if index < len(queue):
        topic = queue[index]
        if index % 5 == 0 and index > 0:
            exam = generate_exam(name, queue[index-5:index], style)
            if exam:
                post_to_facebook(exam, image)
        lesson = generate_lesson_post(name, topic, style)
        if lesson:
            post_to_facebook(lesson, image)
            teacher["current_index"] += 1
            history.append(topic)

    # RANDOM POST (Midday)
    random_type = random.choice(RANDOM_TOPICS)
    random_post = generate_random_post(random_type)
    if random_post:
        post_to_facebook(random_post)

    # TEACHER POST 2 (Evening)
    index2 = teacher.get("current_index", 0)
    if index2 < len(queue):
        topic2 = queue[index2]
        lesson2 = generate_lesson_post(name, topic2, style)
        if lesson2:
            image2 = select_image(folder)
            post_to_facebook(lesson2, image2)
            teacher["current_index"] += 1
            history.append(topic2)

    save_state(state)

if __name__ == "__main__":
    main()