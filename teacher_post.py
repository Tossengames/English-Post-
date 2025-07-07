import os
import random
import datetime
import sys
from common import ask_ai, post_to_facebook, clean_ai_output, read_json, get_pixabay_image_url

# Centralized Pixabay Keywords
# These keywords will be used randomly when fetching an image for any teacher post.
# You can expand this list with more relevant terms.
PIXABAY_GLOBAL_KEYWORDS = [
    "education", "learning", "classroom", "study", "student", "teacher",
    "books", "knowledge", "ideas", "inspire", "communication",
    "reading", "writing", "dictionary", "language", "school supplies",
    "graduation", "achievement", "success", "teaching"
]

def get_teacher_image_from_pixabay() -> str:
    """
    Selects a random keyword from the global list and fetches a Pixabay image.
    """
    selected_keyword = random.choice(PIXABAY_GLOBAL_KEYWORDS)
    print(f"Searching Pixabay for image with keyword: '{selected_keyword}'")
    return get_pixabay_image_url(selected_keyword)

def generate_teacher_lesson_post(teacher_meta: dict) -> tuple[str, str, str, str]:
    """
    Randomly selects a teacher and a random lesson from their queue,
    then generates a post with a Pixabay image using global keywords.
    Returns (post_content, image_url, teacher_name, lesson_topic) or None if failed.
    """
    teacher_ids = list(teacher_meta.keys())
    if not teacher_ids:
        print("No teachers found in teacher_meta.json. Cannot generate teacher post.")
        return None, None, None, None

    # Pick a random teacher
    random_teacher_id = random.choice(teacher_ids)
    teacher = teacher_meta[random_teacher_id]

    # Pick a random lesson from their queue
    lesson_queue = teacher.get("lesson_queue", [])
    if not lesson_queue:
        print(f"Teacher {teacher['name']} has no lessons in their queue. Cannot generate post for this teacher.")
        return None, None, None, None
    
    lesson_topic = random.choice(lesson_queue) # Randomly pick a lesson

    teacher_name = teacher.get("name", "المعلم")
    posting_style = teacher.get("posting_style", "ودود")
    
    # Get image URL from Pixabay using global keywords
    image_to_post_url = get_teacher_image_from_pixabay()

    # Extract level if it's in the lesson_topic (e.g., "مستوى مبتدئ: Present Simple")
    lesson_level = "درس جديد"
    if ":" in lesson_topic:
        level_part = lesson_topic.split(":", 1)[0].strip()
        if "مستوى" in level_part:
            lesson_level = level_part
        lesson_display = lesson_topic.split(":", 1)[1].strip()
    else:
        lesson_display = lesson_topic # If no level is specified

    prompt = f"""
    أنت معلم لغة إنجليزية موجه للطلاب العرب. اسمك هو {teacher_name}، وشخصيتك هي {posting_style}.
    مهمتك هي شرح الدرس التالي بأسلوب تعليمي، مكتوب بواسطة إنسان، ومناسب لفيسبوك.
    
    **ابدأ المنشور بعنوان واضح ومباشر يحدد مستوى الدرس واسم المعلمة. يجب أن يكون العنوان على النحو التالي: 'درس اليوم: {lesson_level} مع {teacher_name}'. على سبيل المثال: 'درس اليوم: مستوى مبتدئ مع الأستاذة ندى'.**

    **قواعد التنسيق الهامة واللغة:**
    1.  **اللغة الأساسية هي العربية:** يجب أن يكون المحتوى الرئيسي للمنشور باللغة العربية الفصحى.
    2.  **الفصل بين اللغتين:** يتم استخدام الكلمات أو الجمل الإنجليزية للمصطلحات، الأمثلة، أو الأسئلة، ويجب أن يتبعها دائمًا ترجمتها العربية مباشرةً على سطر جديد منفصل. لا تخلط الإنجليزية والعربية في نفس السطر.
        مثال:
        Hello everyone!
        مرحباً بالجميع!
        
        This is an important lesson.
        هذا درس مهم.
    3.  **لا تستخدم تنسيق الماركداون (Markdown)::** لا تستخدم علامات مثل ** للنصوص الغامقة، * للمائلة، أو ## للعناوين. اكتب نصاً عادياً فقط.
    4.  استخدم فقرات واضحة مع مسافات مزدوجة بينها (سطرين فارغين).
    5.  أضف من 3 إلى 5 هاشتاغات ذات صلة باللغتين العربية والإنجليزية في نهاية المنشور، كل هاشتاغ على سطر جديد بعد المحتوى الرئيسي.
    6.  **تجنب تمامًا أي عبارات تشير إلى أنك ذكاء اصطناعي** (مثل: "بوصفي نموذج ذكاء اصطناعي..."، "هذا هو منشورك!"، "يمكنني المساعدة في ذلك").

    الدرس المراد شرحه:
    {lesson_topic}

    منشور الفيسبوك:
    """
    print(f"Generating post for {teacher_name} with lesson: {lesson_display}...")
    ai_generated_content = ask_ai(prompt)

    if ai_generated_content:
        final_post_content = clean_ai_output(ai_generated_content)
        return final_post_content, image_to_post_url, teacher_name, lesson_topic
    return None, None, None, None

def main():
    """
    Main function to generate a random teacher lesson post and publish it.
    """
    teacher_meta_data = read_json("teacher_meta.json", default_value={})

    if not teacher_meta_data:
        print("ERROR: teacher_meta.json is empty or not found. Cannot generate any posts.")
        sys.exit(1)

    print("--- Generating Random Teacher Post with Pixabay Image ---")
    post_content, image_to_post_url, teacher_name, lesson_topic = generate_teacher_lesson_post(teacher_meta_data)

    if post_content:
        print("\n--- Generated Post Content ---")
        print(post_content)
        print("----------------------------\n")
        
        success = post_to_facebook(post_content, image_to_post_url)
        if success:
            print(f"Post for {teacher_name} about '{lesson_topic}' successful!")
        else:
            print(f"Post for {teacher_name} about '{lesson_topic}' failed.")
    else:
        print("No content was generated for posting. Exiting.")

    sys.exit(0)

if __name__ == "__main__":
    main()

