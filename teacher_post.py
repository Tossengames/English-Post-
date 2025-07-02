import os
import random
from common import read_json, write_json, ask_ai, post_to_facebook, clean_ai_output # Added clean_ai_output
import datetime

CHARACTER_DIR = "characters"
LEARNING_MATERIALS_DIR = "learning_materials"

def get_next_teacher(teacher_meta: dict, post_state: dict) -> str:
    """Determines the next teacher based on rotation."""
    teacher_ids = sorted(teacher_meta.keys())
    current_teacher_index = post_state.get("current_teacher_index", 0)

    if not teacher_ids:
        print("No teachers configured in teacher_meta.json.")
        return None

    next_teacher_id = teacher_ids[current_teacher_index % len(teacher_ids)]

    # Update index for next run
    post_state["current_teacher_index"] = (current_teacher_index + 1) % len(teacher_ids)

    # Manage exam counter. This logic determines if an exam should be generated next.
    # The exam is generated after N teacher-led posts, effectively.
    # Reset days_since_last_exam when a new teacher cycle starts (or after an exam)
    if current_teacher_index % len(teacher_ids) == 0 and current_teacher_index != 0: # New cycle starts, but not the very first run
         post_state["days_since_last_exam"] = 0
    else:
        post_state["days_since_last_exam"] = post_state.get("days_since_last_exam", 0) + 1

    return next_teacher_id

def get_next_lesson(teacher_id: str, teacher_meta: dict, post_state: dict) -> str:
    """Gets the next lesson from the teacher's queue."""
    lessons = teacher_meta.get(teacher_id, {}).get("lesson_queue", [])
    if not lessons:
        print(f"No lesson queue found for teacher {teacher_id}.")
        return None

    # Get teacher-specific state or initialize it
    teacher_state = post_state.setdefault("teachers", {}).setdefault(teacher_id, {"lesson_index": 0})
    lesson_index = teacher_state.get("lesson_index", 0)

    if lesson_index >= len(lessons):
        # All lessons for this teacher are done, reset index for next cycle
        print(f"Teacher {teacher_id} has completed all lessons in queue. Resetting lesson index.")
        lesson_index = 0
        teacher_state["lesson_index"] = 0 # Reset for next cycle

    next_lesson = lessons[lesson_index]
    teacher_state["lesson_index"] = (lesson_index + 1) % len(lessons) # Advance lesson index

    return next_lesson

def get_random_teacher_image(teacher_id: str) -> str:
    """Selects a random image for the teacher."""
    teacher_image_dir = os.path.join(CHARACTER_DIR, teacher_id)
    if os.path.exists(teacher_image_dir):
        images = [f for f in os.listdir(teacher_image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        if images:
            return os.path.join(teacher_image_dir, random.choice(images))
    print(f"No images found for teacher {teacher_id} in {teacher_image_dir}.")
    return None

def generate_teacher_post(teacher_id: str, lesson_content: str, teacher_info: dict) -> str:
    """
    Generates the teacher's post using AI based on lesson content and style.
    """
    teacher_name = teacher_info.get("name", "The Teacher")
    posting_style = teacher_info.get("posting_style", "friendly") # Default to friendly

    # **IMPORTANT: Updated Prompt for better formatting**
    prompt = f"""
    You are an English language teacher for Arabic-speaking students. Your name is {teacher_name}, and your personality is {posting_style}.
    Your task is to explain the following lesson in a human-written, educational, and Facebook-friendly style.
    
    **CRITICAL FORMATTING RULES:**
    1.  **NO MARKDOWN:** Do NOT use markdown characters for bolding, italics, or headings (e.g., **, *, ##). Write plain text.
    2.  **SEPARATE ENGLISH & ARABIC:** Always put English text on its own line(s), and its Arabic translation directly below it on new line(s). Do NOT mix English and Arabic on the same line.
        Example:
        Hello everyone!
        مرحباً بالجميع!
        
        This is an important lesson.
        هذا درس مهم.
    3.  Use clear paragraphs with double newlines between them.
    4.  Include 3-5 relevant hashtags in both Arabic and English at the very end of the post, each on a new line after the main content.
    5.  **Absolutely avoid any phrases that suggest you are an AI** (e.g., "As an AI model...", "Here's your post!", "I can help with that").
    6.  The content should be in formal Arabic, with English words or phrases integrated contextually.

    The lesson to explain:
    {lesson_content}

    The Facebook Post:
    """
    print(f"Generating post for {teacher_name} with lesson: {lesson_content[:50]}...")
    ai_generated_content = ask_ai(prompt)

    if not ai_generated_content:
        print("AI failed to generate teacher post. Falling back to simple message.")
        return f"مرحباً بكم! اليوم لدينا درس جديد عن {lesson_content[:50]}... ترقبوا المزيد!\n#تعلم_الإنجليزي\n#EnglishLesson"

    # Apply cleanup after AI generation
    final_post_content = clean_ai_output(ai_generated_content)

    # Ensure hashtags are present and on separate lines at the end
    if "#" not in final_post_content[-50:]: # Check last 50 chars for hashtags
        if not final_post_content.strip().endswith('\n\n'):
            final_post_content += '\n\n'
        final_post_content += "#تعلم_اللغة_الإنجليزية\n#لغة_انجليزية\n#دروس_انجليزي\n#EnglishLearning\n#LearnEnglish"

    return final_post_content

def generate_exam_post(teacher_meta: dict, post_log: dict) -> str:
    """
    Generates an exam post based on recent lessons.
    """
    recent_lesson_topics = []
    if "posts" in post_log:
        teacher_posts = [p for p in post_log["posts"] if p.get("type") == "teacher_lesson"]
        for post in teacher_posts[-5:]: # Look at the last 5 teacher lessons in the log
            preview = post.get("content_preview", "").replace("...", "").strip()
            if "Present Simple" in preview: recent_lesson_topics.append("المضارع البسيط")
            elif "Present Continuous" in preview: recent_lesson_topics.append("المضارع المستمر")
            elif "Past Simple" in preview: recent_lesson_topics.append("الماضي البسيط")
            elif "Verbs" in preview: recent_lesson_topics.append("الأفعال")
            elif "Nouns" in preview: recent_lesson_topics.append("الأسماء")
            elif "Adjectives" in preview: recent_lesson_topics.append("الصفات")
            else: recent_lesson_topics.append(preview.split('عن')[-1].strip() if 'عن' in preview else preview)
    
    lessons_summary = ", ".join(list(set(recent_lesson_topics))) if recent_lesson_topics else "مفاهيم اللغة الإنجليزية الأساسية"

    # **IMPORTANT: Updated Prompt for better formatting**
    prompt = f"""
    لقد مر أسبوع من الدروس الشيقة في اللغة الإنجليزية! حان وقت الاختبار لتقييم فهم الطلاب.
    أنت معلم لغة إنجليزية موجه للطلاب العرب. مهمتك هي إنشاء اختبار قصير وممتع لفيسبوك، يغطي مواضيع مثل: {lessons_summary}.
    
    **CRITICAL FORMATTING RULES:**
    1.  **NO MARKDOWN:** Do NOT use markdown characters for bolding, italics, or headings (e.g., **, *, ##). Write plain text.
    2.  **SEPARATE ENGLISH & ARABIC:** Always put English text on its own line(s), and its Arabic translation directly below it on new line(s). Do NOT mix English and Arabic on the same line.
        Example:
        Question 1: What is...?
        السؤال الأول: ما هو...؟
        
        (A) Option A
        (أ) الخيار أ
    3.  Use clear paragraphs with double newlines between them.
    4.  Add 3-5 relevant hashtags in both Arabic and English at the very end of the post, each on a new line after the main content.
    5.  Do not mention that you are an AI. Make it seem like it's prepared by a teacher.

    The Facebook Post:
    """
    print("Generating exam post...")
    ai_generated_content = ask_ai(prompt)

    if not ai_generated_content:
        print("AI failed to generate exam post. Falling back to simple exam message.")
        return "حان وقت مراجعة ما تعلمناه هذا الأسبوع! استعدوا لاختبار قصير وممتع!\n#اختبار_انجليزي\n#EnglishQuiz"

    # Apply cleanup after AI generation
    final_post_content = clean_ai_output(ai_generated_content)

    # Ensure hashtags are present and on separate lines at the end
    if "#" not in final_post_content[-50:]: # Check last 50 chars for hashtags
        if not final_post_content.strip().endswith('\n\n'):
            final_post_content += '\n\n'
        final_post_content += "#اختبارات_لغة_انجليزية\n#مراجعة_انجليزي\n#تقييم_اللغة\n#EnglishExam\n#LanguageAssessment"

    return final_post_content

def main():
    teacher_meta = read_json("teacher_meta.json")
    post_state = read_json("post_state.json")
    post_log = read_json("post_log.json")

    post_state.setdefault("current_teacher_index", 0)
    post_state.setdefault("days_since_last_exam", 0)
    post_state.setdefault("teachers", {})

    EXAM_INTERVAL_DAYS = 5 

    if post_state["days_since_last_exam"] >= EXAM_INTERVAL_DAYS:
        print(f"It's exam day! (Days since last exam: {post_state['days_since_last_exam']})")
        post_content = generate_exam_post(teacher_meta, post_log)
        image_to_post = None
        post_type_log = "exam"
        post_state["days_since_last_exam"] = 0
    else:
        selected_teacher_id = get_next_teacher(teacher_meta, post_state)
        
        if not selected_teacher_id:
            print("No teachers defined. Cannot generate teacher post. Falling back to random post if possible.")
            import random_post
            random_post.main()
            write_json("post_state.json", post_state)
            return

        teacher_info = teacher_meta.get(selected_teacher_id, {})
        lesson_content = get_next_lesson(selected_teacher_id, teacher_meta, post_state)
        image_to_post = get_random_teacher_image(selected_teacher_id)

        if not lesson_content:
            print(f"No lessons found for teacher {selected_teacher_id} after getting next. Skipping teacher post and falling back to random.")
            import random_post
            random_post.main()
            write_json("post_state.json", post_state)
            return

        post_content = generate_teacher_post(selected_teacher_id, lesson_content, teacher_info)
        post_type_log = "teacher_lesson"
        print(f"Generated teacher post for {teacher_info.get('name', selected_teacher_id)}")
    
    if post_to_facebook(post_content, image_to_post):
        post_log.setdefault("posts", []).append({
            "timestamp": datetime.datetime.now().isoformat(),
            "type": post_type_log,
            "content_preview": post_content[:200] + "...",
            "image_used": image_to_post if image_to_post else "none"
        })
        write_json("post_log.json", post_log)
        print("Post logged successfully.")
    else:
        print("Failed to post content to Facebook. Post state not updated for failed post.")

    write_json("post_state.json", post_state)

if __name__ == "__main__":
    main()
