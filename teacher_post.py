import os
import random
from common import read_json, write_json, ask_ai, post_to_facebook
import datetime

CHARACTER_DIR = "characters"
LEARNING_MATERIALS_DIR = "learning_materials"

def get_next_teacher(teacher_meta: dict, post_state: dict) -> str:
    """Determines the next teacher based on rotation."""
    teacher_ids = sorted(teacher_meta.keys())
    current_teacher_index = post_state.get("current_teacher_index", 0)
    
    if not teacher_ids:
        return None

    next_teacher_id = teacher_ids[current_teacher_index % len(teacher_ids)]
    post_state["current_teacher_index"] = (current_teacher_index + 1) % len(teacher_ids)
    
    # Reset exam counter if a new teacher cycle starts
    if post_state["current_teacher_index"] == 0:
        post_state["days_since_last_exam"] = 0
    else:
        post_state["days_since_last_exam"] = post_state.get("days_since_last_exam", 0) + 1

    return next_teacher_id

def get_next_lesson(teacher_id: str, teacher_meta: dict, post_state: dict) -> str:
    """Gets the next lesson from the teacher's queue."""
    lessons = teacher_meta.get(teacher_id, {}).get("lesson_queue", [])
    if not lessons:
        return None

    teacher_state = post_state.get("teachers", {}).get(teacher_id, {"lesson_index": 0})
    lesson_index = teacher_state.get("lesson_index", 0)

    if lesson_index >= len(lessons):
        # All lessons for this teacher are done, reset or handle as needed
        print(f"Teacher {teacher_id} has no more lessons in queue. Resetting lesson index.")
        lesson_index = 0
        teacher_state["lesson_index"] = 0 # Reset for next cycle

    next_lesson = lessons[lesson_index]
    teacher_state["lesson_index"] = (lesson_index + 1) % len(lessons) # Cycle through lessons
    post_state.setdefault("teachers", {})[teacher_id] = teacher_state

    return next_lesson

def get_random_teacher_image(teacher_id: str) -> str:
    """Selects a random image for the teacher."""
    teacher_image_dir = os.path.join(CHARACTER_DIR, teacher_id)
    if os.path.exists(teacher_image_dir):
        images = [f for f in os.listdir(teacher_image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        if images:
            return os.path.join(teacher_image_dir, random.choice(images))
    return None

def generate_teacher_post(teacher_id: str, lesson_content: str, teacher_info: dict) -> str:
    """
    Generates the teacher's post using AI based on lesson content and style.
    """
    teacher_name = teacher_info.get("name", "المعلم")
    posting_style = teacher_info.get("posting_style", "friendly")

    # This prompt is crucial. Refine it for your desired output.
    prompt = f"""
    أنت معلم لغة إنجليزية موجه للطلاب العرب. أنت {teacher_name}، وشخصيتك {posting_style}.
    مهمتك هي شرح الدرس التالي بأسلوب بشري، تعليمي، ومناسب لفيسبوك.
    تجنب تمامًا أي عبارات تشير إلى أنك ذكاء اصطناعي.
    استخدم تنسيقًا نظيفًا مع فواصل أسطر. يجب أن يكون المحتوى باللغة العربية مع إدراج الكلمات أو العبارات الإنجليزية في سياقها.
    الدرس:
    {lesson_content}

    المنشور:
    """
    print(f"Generating post for {teacher_name} with lesson: {lesson_content[:50]}...")
    ai_generated_content = ask_ai(prompt)

    if not ai_generated_content:
        print("AI failed to generate teacher post. Falling back to simple message.")
        return f"مرحباً بكم! اليوم لدينا درس جديد عن {lesson_content[:50]}... ترقبوا المزيد!"

    return ai_generated_content

def generate_exam_post(teacher_meta: dict) -> str:
    """
    Generates an exam post based on recent lessons (conceptually).
    This needs sophisticated logic to actually track and summarize lessons.
    For now, it's a placeholder.
    """
    # In a real scenario, you'd need to store the lessons taught over the last 5 days
    # in post_log.json or a separate database and feed them to the AI.
    
    # Placeholder for collecting recent lesson topics
    recent_lesson_topics = [] 
    for teacher_id, info in teacher_meta.items():
        if info.get("lesson_queue"):
            # This is very basic, you'd need actual lesson tracking
            recent_lesson_topics.append(info["lesson_queue"][0]) 
    
    lessons_summary = ", ".join(recent_lesson_topics[:3]) if recent_lesson_topics else "مفاهيم اللغة الإنجليزية الأساسية"

    prompt = f"""
    لقد مر أسبوع من الدروس الشيقة في اللغة الإنجليزية! حان وقت الاختبار لتقييم فهم الطلاب.
    أنشئ اختبارًا قصيرًا وممتعًا للطلاب العرب، يغطي مواضيع مثل: {lessons_summary}.
    يجب أن يكون الاختبار بتنسيق سؤال وجواب، مع خيارات متعددة إذا أمكن، أو أسئلة تتطلب إجابة قصيرة.
    لا تذكر أنك ذكاء اصطناعي. اجعلها تبدو وكأنها معدة من قبل معلم.
    المنشور:
    """
    print("Generating exam post...")
    ai_generated_content = ask_ai(prompt)
    
    if not ai_generated_content:
        print("AI failed to generate exam post. Falling back to simple exam message.")
        return "حان وقت مراجعة ما تعلمناه هذا الأسبوع! استعدوا لاختبار قصير وممتع!"

    return ai_generated_content

def main():
    teacher_meta = read_json("teacher_meta.json")
    post_state = read_json("post_state.json")
    
    post_state.setdefault("current_teacher_index", 0)
    post_state.setdefault("days_since_last_exam", 0) # Track days since last exam

    # Check if it's exam day (after 5 teacher posts)
    if post_state["days_since_last_exam"] >= 5:
        post_content = generate_exam_post(teacher_meta)
        image_to_post = None # Exams might not have specific teacher images
        post_state["days_since_last_exam"] = 0 # Reset counter after exam
        print("Generated an exam post.")
    else:
        # It's a regular teacher lesson day
        selected_teacher_id = get_next_teacher(teacher_meta, post_state)
        if not selected_teacher_id:
            print("No teachers defined. Skipping teacher post.")
            # Fallback to random post if no teachers
            import random_post
            random_post.main()
            return

        teacher_info = teacher_meta.get(selected_teacher_id, {})
        lesson_content = get_next_lesson(selected_teacher_id, teacher_meta, post_state)
        image_to_post = get_random_teacher_image(selected_teacher_id)

        if not lesson_content:
            print(f"No lessons found for teacher {selected_teacher_id}. Skipping teacher post and falling back to random.")
            # Fallback to random post if no lessons
            import random_post
            random_post.main()
            return

        post_content = generate_teacher_post(selected_teacher_id, lesson_content, teacher_info)
        print(f"Generated teacher post for {teacher_info.get('name', selected_teacher_id)}")

    if post_to_facebook(post_content, image_to_post):
        # Update post_log only if posting was (simulated) successful
        post_log = read_json("post_log.json")
        post_log.setdefault("posts", []).append({
            "timestamp": datetime.datetime.now().isoformat(),
            "type": "teacher_lesson" if post_state["days_since_last_exam"] != 0 else "exam",
            "content_preview": post_content[:100] + "...",
            "image_used": image_to_post
        })
        write_json("post_log.json", post_log)
    else:
        print("Failed to post teacher/exam content to Facebook.")
        # If posting fails, you might want to revert post_state changes for the lesson/teacher
        # or log the failure to retry later. For simplicity, we'll let it advance for now.

    write_json("post_state.json", post_state)

if __name__ == "__main__":
    main()
