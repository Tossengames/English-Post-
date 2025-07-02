import os
import random
from common import read_json, write_json, ask_ai, post_to_facebook
import datetime

CHARACTER_DIR = "characters"
LEARNING_MATERIALS_DIR = "learning_materials" # Not directly used in current script, but kept for structure

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

    # This prompt is crucial. Refine it for your desired output.
    prompt = f"""
    You are an English language teacher for Arabic-speaking students. Your name is {teacher_name}, and your personality is {posting_style}.
    Your task is to explain the following lesson in a human-written, educational, and Facebook-friendly style.
    **Absolutely avoid any phrases that suggest you are an AI** (e.g., "As an AI model...", "Here's your post!", "I can help with that").
    Use a clean format with line breaks. The content should be in formal Arabic, with English words or phrases integrated contextually.
    Include relevant Arabic and English hashtags at the end of the post (e.g., #تعليم_إنجليزي #LearnEnglish).
    
    The lesson to explain:
    {lesson_content}

    The Facebook Post:
    """
    print(f"Generating post for {teacher_name} with lesson: {lesson_content[:50]}...")
    ai_generated_content = ask_ai(prompt)

    if not ai_generated_content:
        print("AI failed to generate teacher post. Falling back to simple message.")
        return f"مرحباً بكم! اليوم لدينا درس جديد عن {lesson_content[:50]}... ترقبوا المزيد! #تعلم_الإنجليزي #EnglishLesson"

    # Add general hashtags if AI didn't include them, or ensure they are present
    if "#" not in ai_generated_content:
        ai_generated_content += "\n\n#تعلم_اللغة_الإنجليزية #لغة_انجليزية #دروس_انجليزي #EnglishLearning #LearnEnglish"

    return ai_generated_content

def generate_exam_post(teacher_meta: dict, post_log: dict) -> str:
    """
    Generates an exam post based on recent lessons.
    This needs sophisticated logic to actually track and summarize lessons.
    For now, it will attempt to summarize recent topics from the post_log.
    """
    # Collect recent lesson topics from post_log (last 5 teacher posts)
    recent_lesson_topics = []
    if "posts" in post_log:
        teacher_posts = [p for p in post_log["posts"] if p.get("type") == "teacher_lesson"]
        # Get content_preview from last few teacher lessons
        for post in teacher_posts[-5:]: # Look at the last 5 teacher lessons in the log
            # Extract lesson title from content_preview if possible, or use the whole preview
            preview = post.get("content_preview", "").replace("...", "").strip()
            # Simple heuristic: try to find common English grammar terms or just use the preview
            if "Present Simple" in preview: recent_lesson_topics.append("المضارع البسيط")
            elif "Present Continuous" in preview: recent_lesson_topics.append("المضارع المستمر")
            elif "Past Simple" in preview: recent_lesson_topics.append("الماضي البسيط")
            elif "Verbs" in preview: recent_lesson_topics.append("الأفعال")
            elif "Nouns" in preview: recent_lesson_topics.append("الأسماء")
            elif "Adjectives" in preview: recent_lesson_topics.append("الصفات")
            else: recent_lesson_topics.append(preview.split('عن')[-1].strip() if 'عن' in preview else preview) # Basic attempt to get topic
    
    lessons_summary = ", ".join(list(set(recent_lesson_topics))) if recent_lesson_topics else "مفاهيم اللغة الإنجليزية الأساسية"

    prompt = f"""
    لقد مر أسبوع من الدروس الشيقة في اللغة الإنجليزية! حان وقت الاختبار لتقييم فهم الطلاب.
    أنت معلم لغة إنجليزية موجه للطلاب العرب. مهمتك هي إنشاء اختبار قصير وممتع لفيسبوك، يغطي مواضيع مثل: {lessons_summary}.
    يجب أن يكون الاختبار بتنسيق سؤال وجواب، مع خيارات متعددة إذا أمكن، أو أسئلة تتطلب إجابة قصيرة.
    لا تذكر أنك ذكاء اصطناعي. اجعلها تبدو وكأنها معدة من قبل معلم.
    أضف 3-5 هاشتاغات ذات صلة باللغتين العربية والإنجليزية في نهاية المنشور.
    المنشور:
    """
    print("Generating exam post...")
    ai_generated_content = ask_ai(prompt)

    if not ai_generated_content:
        print("AI failed to generate exam post. Falling back to simple exam message.")
        return "حان وقت مراجعة ما تعلمناه هذا الأسبوع! استعدوا لاختبار قصير وممتع! #اختبار_انجليزي #EnglishQuiz"

    # Add general hashtags if AI didn't include them, or ensure they are present
    if "#" not in ai_generated_content:
        ai_generated_content += "\n\n#اختبارات_لغة_انجليزية #مراجعة_انجليزي #تقييم_اللغة #EnglishExam #LanguageAssessment"


    return ai_generated_content

def main():
    teacher_meta = read_json("teacher_meta.json")
    post_state = read_json("post_state.json")
    post_log = read_json("post_log.json") # Read post_log for exam generation

    post_state.setdefault("current_teacher_index", 0)
    post_state.setdefault("days_since_last_exam", 0) # Track days since last exam (teacher posts count)
    post_state.setdefault("teachers", {}) # Ensure teachers dictionary exists

    # Check if it's exam day (after 5 teacher posts)
    # The 'days_since_last_exam' increments only when a teacher lesson is posted.
    # An exam counts as a separate "post event", not advancing the teacher sequence.
    EXAM_INTERVAL_DAYS = 5 # Post an exam after 5 teacher lesson posts

    if post_state["days_since_last_exam"] >= EXAM_INTERVAL_DAYS:
        print(f"It's exam day! (Days since last exam: {post_state['days_since_last_exam']})")
        post_content = generate_exam_post(teacher_meta, post_log) # Pass post_log for recent topics
        image_to_post = None # Exams might not have specific teacher images
        post_type_log = "exam"
        post_state["days_since_last_exam"] = 0 # Reset counter after exam
    else:
        # It's a regular teacher lesson day
        selected_teacher_id = get_next_teacher(teacher_meta, post_state)
        
        if not selected_teacher_id:
            print("No teachers defined. Cannot generate teacher post. Falling back to random post if possible.")
            # Fallback to random post by calling its main function
            import random_post
            random_post.main()
            write_json("post_state.json", post_state) # Save state even if no teacher post
            return

        teacher_info = teacher_meta.get(selected_teacher_id, {})
        lesson_content = get_next_lesson(selected_teacher_id, teacher_meta, post_state)
        image_to_post = get_random_teacher_image(selected_teacher_id) # Image is selected for the teacher

        if not lesson_content:
            print(f"No lessons found for teacher {selected_teacher_id} after getting next. Skipping teacher post and falling back to random.")
            # Fallback to random post if no lessons
            import random_post
            random_post.main()
            write_json("post_state.json", post_state) # Save state even if no teacher post
            return

        post_content = generate_teacher_post(selected_teacher_id, lesson_content, teacher_info)
        post_type_log = "teacher_lesson"
        print(f"Generated teacher post for {teacher_info.get('name', selected_teacher_id)}")
    
    # Attempt to post to Facebook
    if post_to_facebook(post_content, image_to_post):
        # Update post_log only if posting was successful
        post_log.setdefault("posts", []).append({
            "timestamp": datetime.datetime.now().isoformat(),
            "type": post_type_log,
            "content_preview": post_content[:200] + "...", # Log more preview text
            "image_used": image_to_post if image_to_post else "none"
        })
        write_json("post_log.json", post_log)
        print("Post logged successfully.")
    else:
        print("Failed to post content to Facebook. Post state not updated for failed post.")
        # If posting fails, consider if you want to revert post_state changes
        # For simplicity, we are allowing the state to advance for now,
        # but in a production system, you might want a retry mechanism or a revert.

    write_json("post_state.json", post_state) # Always save post_state regardless of FB post success for progress tracking

if __name__ == "__main__":
    main()
