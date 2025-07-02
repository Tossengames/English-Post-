# teacher_post.py
import os
import json
import random
from common import ask_ai, post_to_facebook
from datetime import datetime

TEACHER_META_PATH = "teachers.json"

def load_teachers():
    with open(TEACHER_META_PATH, encoding="utf-8") as f:
        return json.load(f)

def save_teachers(data):
    with open(TEACHER_META_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def pick_teacher(teachers):
    today = datetime.now().date().isoformat()
    order = list(teachers.keys())
    index = hash(today) % len(order)
    return order[index], teachers[order[index]]

def generate_teacher_prompt(teacher, topic):
    return f"""اكتبي درسًا قصيرًا عن "{topic}" بأسلوب {teacher['style']}، مع أمثلة مبسطة وترجمة عربية. لا تذكري الطلب أو الذكاء الاصطناعي."""

def get_random_image(folder):
    images = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.png'))]
    if not images:
        return None
    return os.path.join(folder, random.choice(images))

def main():
    teachers = load_teachers()
    teacher_id, teacher = pick_teacher(teachers)
    index = teacher["current_index"]
    lesson = teacher["lesson_queue"][index]

    prompt = generate_teacher_prompt(teacher, lesson)
    post_text = ask_ai(prompt)

    if not post_text:
        print("⚠️ AI failed to generate post.")
        return

    post_text = f"📘 من كتاب: {lesson}\n\n{post_text}"
    image = get_random_image(teacher["folder"])
    post_to_facebook(post_text, image)

    teacher["history"].append(lesson)
    teacher["current_index"] = (index + 1) % len(teacher["lesson_queue"])
    save_teachers(teachers)

if __name__ == "__main__":
    main()
