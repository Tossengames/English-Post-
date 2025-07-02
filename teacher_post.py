import os
import random
from common import read_json, write_json, ask_ai, post_to_facebook, clean_ai_output
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
    posting_style = teacher_info.get("posting_style", "friendly")

    prompt = f"""
    أنت معلم لغة إنجليزية موجه للطلاب العرب. اسمك هو {teacher_name}، وشخصيتك هي {posting_style}.
    مهمتك هي شرح الدرس التالي بأسلوب تعليمي، مكتوب بواسطة إنسان، ومناسب لفيسبوك.
    
    **قواعد التنسيق الهامة واللغة:**
    1.  **اللغة الأساسية هي العربية:** يجب أن يكون المحتوى الرئيسي للمنشور باللغة العربية الفصحى.
    2.  **الفصل بين اللغتين:** يتم استخدام الكلمات أو الجمل الإنجليزية للمصطلحات، الأمثلة، أو الأسئلة، ويجب أن يتبعها دائمًا ترجمتها العربية مباشرةً على سطر جديد منفصل. لا تخلط الإنجليزية والعربية في نفس السطر.
        مثال:
        Hello everyone!
        مرحباً بالجميع!
        
        This is an important lesson.
        هذا درس مهم.
    3.  **لا تستخدم تنسيق الماركداون (Markdown):** لا تستخدم علامات مثل ** للنصوص الغامقة، * للمائلة، أو ## للعناوين. اكتب نصاً عادياً فقط.
    4.  استخدم فقرات واضحة مع مسافات مزدوجة بينها (سطرين فارغين).
    5.  أضف من 3 إلى 5 هاشتاغات ذات صلة باللغتين العربية والإنجليزية في نهاية المنشور، كل هاشتاغ على سطر جديد بعد المحتوى الرئيسي.
    6.  **تجنب تمامًا أي عبارات تشير إلى أنك ذكاء اصطناعي** (مثل: "بوصفي نموذج ذكاء اصطناعي..."، "هذا هو منشورك!"، "يمكنني المساعدة في ذلك").

    الدرس المراد شرحه:
    {lesson_content}

    منشور الفيسبوك:
    """
    print(f"Generating post for {teacher_name} with lesson: {lesson_content[:50]}...")
    ai_generated_content = ask_ai(prompt)

    if not ai_generated_content:
        print("AI failed to generate teacher post. Falling back to simple message.")
        return f"مرحباً بكم! اليوم لدينا درس جديد عن {lesson_content[:50]}... ترقبوا المزيد!\n#تعلم_الإنجليزي\n#EnglishLesson"

    final_post_content = clean_ai_output(ai_generated_content)

    if "#" not in final_post_content[-50:]:
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
        for post in teacher_posts[-5:]:
            preview = post.get("content_preview", "").replace("...", "").strip()
            if "Present Simple" in preview: recent_lesson_topics.append("المضارع البسيط")
            elif "Present Continuous" in preview: recent_lesson_topics.append("المضارع المستمر")
            elif "Past Simple" in preview: recent_lesson_topics.append("الماضي البسيط")
            elif "Verbs" in preview: recent_lesson_topics.append("الأفعال")
            elif "Nouns" in preview: recent_lesson_topics.append("الأسماء")
            elif "Adjectives" in preview: recent_lesson_topics.append("الصفات")
            else: recent_lesson_topics.append(preview.split('عن')[-1].strip() if 'عن' in preview else preview)
    
    lessons_summary = ", ".join(list(set(recent_lesson_topics))) if recent_lesson_topics else "مفاهيم اللغة الإنجليزية الأساسية"

    prompt = f"""
    لقد مر أسبوع من الدروس الشيقة في اللغة الإنجليزية! حان وقت الاختبار لتقييم فهم الطلاب.
    أنت معلم لغة إنجليزية موجه للطلاب العرب. مهمتك هي إنشاء اختبار قصير وممتع لفيسبوك، يغطي مواضيع مثل: {lessons_summary}.
    
    **قواعد التنسيق الهامة واللغة:**
    1.  **اللغة الأساسية هي العربية:** يجب أن يكون المحتوى الرئيسي للمنشور باللغة العربية الفصحى.
    2.  **الفصل بين اللغتين:** يجب أن تكون الأسئلة أو الخيارات الإنجليزية متبوعة مباشرة بترجمتها العربية على سطر جديد منفصل. لا تخلط الإنجليزية والعربية في نفس السطر.
        مثال:
        Question 1: What is...?
        السؤال الأول: ما هو...؟
        
        (A) Option A
        (أ) الخيار أ
    3.  **لا تستخدم تنسيق الماركداون (Markdown):** لا تستخدم علامات مثل ** للنصوص الغامقة، * للمائلة، أو ## للعناوين. اكتب نصاً عادياً فقط.
    4.  استخدم فقرات واضحة مع مسافات مزدوجة بينها (سطرين فارغين).
    5.  أضف من 3 إلى 5 هاشتاغات ذات صلة باللغتين العربية والإنجليزية في نهاية المنشور، كل هاشتاغ على سطر جديد بعد المحتوى الرئيسي.
    6.  لا تذكر أنك ذكاء اصطناعي. اجعلها تبدو وكأنها معدة من قبل معلم.

    منشور الفيسبوك:
    """
    print("Generating exam post...")
    ai_generated_content = ask_ai(prompt)

    if not ai_generated_content:
        print("AI failed to generate exam post. Falling back to simple exam message.")
        return "حان وقت مراجعة ما تعلمناه هذا الأسبوع! استعدوا لاختبار قصير وممتع!\n#اختبار_انجليزي\n#EnglishQuiz"

    final_post_content = clean_ai_output(ai_generated_content)

    if "#" not in final_post_content[-50:]:
        if not final_post_content.strip().endswith('\n\n'):
            final_post_content += '\n\n'
        final_post_content += "#اختبارات_لغة_انجليزية\n#مراجعة_انجليزي\n#تقييم_اللغة\n#EnglishExam\n#LanguageAssessment"

    return final_post_content

# Modified main function to accept specific_teacher_id
def main(specific_teacher_id: str = None):
    teacher_meta = read_json("teacher_meta.json")
    # Load post_state and post_log, but only modify if it's a non-specific run
    post_state = read_json("post_state.json")
    post_log = read_json("post_log.json")

    # If a specific teacher is requested, bypass regular rotation and exam logic
    if specific_teacher_id:
        print(f"Manual run for specific teacher: {specific_teacher_id}")
        if specific_teacher_id not in teacher_meta:
            print(f"Error: Teacher ID '{specific_teacher_id}' not found in teacher_meta.json. Please check the ID.")
            return

        selected_teacher_id = specific_teacher_id
        teacher_info = teacher_meta.get(selected_teacher_id, {})

        # To ensure we get *a* lesson for a specific teacher, we might need to adjust this.
        # For testing, let's just get the "next" one based on its current state,
        # but without altering that state for the next *scheduled* run.
        # Create a temporary post_state for this specific teacher run so it doesn't affect the real one
        temp_post_state = {"teachers": post_state.setdefault("teachers", {}).get(selected_teacher_id, {"lesson_index": 0})}
        lesson_content = get_next_lesson(selected_teacher_id, teacher_meta, temp_post_state)
        # Note: We are not writing temp_post_state back, so the lesson_index isn't persisted for this test.

        image_to_post = get_random_teacher_image(selected_teacher_id)

        if not lesson_content:
            print(f"No lessons found for specific teacher {selected_teacher_id}. Cannot generate post.")
            return

        post_content = generate_teacher_post(selected_teacher_id, lesson_content, teacher_info)
        post_type_log = f"teacher_lesson_test_{selected_teacher_id}" # Indicate this is a test post

        print(f"Generated test post for {teacher_info.get('name', selected_teacher_id)}")
        
        # Post to Facebook and log it, but don't update main post_state for scheduling
        if post_to_facebook(post_content, image_to_post):
            post_log.setdefault("posts", []).append({
                "timestamp": datetime.datetime.now().isoformat(),
                "type": post_type_log,
                "content_preview": post_content[:200] + "...",
                "image_used": image_to_post if image_to_post else "none",
                "is_test": True # Mark as test post
            })
            write_json("post_log.json", post_log)
            print("Test post logged successfully (without affecting main schedule).")
        else:
            print("Failed to post test content to Facebook.")
        return # Exit after specific teacher run

    # --- Regular Scheduled or General Manual Run Logic (if specific_teacher_id is None) ---
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

    write_json("post_state.json", post_state) # Always save post_state for scheduled/general manual runs

if __name__ == "__main__":
    main()

import os
import random
from common import read_json, write_json, ask_ai, post_to_facebook, clean_ai_output
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
    posting_style = teacher_info.get("posting_style", "friendly")

    prompt = f"""
    أنت معلم لغة إنجليزية موجه للطلاب العرب. اسمك هو {teacher_name}، وشخصيتك هي {posting_style}.
    مهمتك هي شرح الدرس التالي بأسلوب تعليمي، مكتوب بواسطة إنسان، ومناسب لفيسبوك.
    
    **قواعد التنسيق الهامة واللغة:**
    1.  **اللغة الأساسية هي العربية:** يجب أن يكون المحتوى الرئيسي للمنشور باللغة العربية الفصحى.
    2.  **الفصل بين اللغتين:** يتم استخدام الكلمات أو الجمل الإنجليزية للمصطلحات، الأمثلة، أو الأسئلة، ويجب أن يتبعها دائمًا ترجمتها العربية مباشرةً على سطر جديد منفصل. لا تخلط الإنجليزية والعربية في نفس السطر.
        مثال:
        Hello everyone!
        مرحباً بالجميع!
        
        This is an important lesson.
        هذا درس مهم.
    3.  **لا تستخدم تنسيق الماركداون (Markdown):** لا تستخدم علامات مثل ** للنصوص الغامقة، * للمائلة، أو ## للعناوين. اكتب نصاً عادياً فقط.
    4.  استخدم فقرات واضحة مع مسافات مزدوجة بينها (سطرين فارغين).
    5.  أضف من 3 إلى 5 هاشتاغات ذات صلة باللغتين العربية والإنجليزية في نهاية المنشور، كل هاشتاغ على سطر جديد بعد المحتوى الرئيسي.
    6.  **تجنب تمامًا أي عبارات تشير إلى أنك ذكاء اصطناعي** (مثل: "بوصفي نموذج ذكاء اصطناعي..."، "هذا هو منشورك!"، "يمكنني المساعدة في ذلك").

    الدرس المراد شرحه:
    {lesson_content}

    منشور الفيسبوك:
    """
    print(f"Generating post for {teacher_name} with lesson: {lesson_content[:50]}...")
    ai_generated_content = ask_ai(prompt)

    if not ai_generated_content:
        print("AI failed to generate teacher post. Falling back to simple message.")
        return f"مرحباً بكم! اليوم لدينا درس جديد عن {lesson_content[:50]}... ترقبوا المزيد!\n#تعلم_الإنجليزي\n#EnglishLesson"

    final_post_content = clean_ai_output(ai_generated_content)

    if "#" not in final_post_content[-50:]:
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
        for post in teacher_posts[-5:]:
            preview = post.get("content_preview", "").replace("...", "").strip()
            if "Present Simple" in preview: recent_lesson_topics.append("المضارع البسيط")
            elif "Present Continuous" in preview: recent_lesson_topics.append("المضارع المستمر")
            elif "Past Simple" in preview: recent_lesson_topics.append("الماضي البسيط")
            elif "Verbs" in preview: recent_lesson_topics.append("الأفعال")
            elif "Nouns" in preview: recent_lesson_topics.append("الأسماء")
            elif "Adjectives" in preview: recent_lesson_topics.append("الصفات")
            else: recent_lesson_topics.append(preview.split('عن')[-1].strip() if 'عن' in preview else preview)
    
    lessons_summary = ", ".join(list(set(recent_lesson_topics))) if recent_lesson_topics else "مفاهيم اللغة الإنجليزية الأساسية"

    prompt = f"""
    لقد مر أسبوع من الدروس الشيقة في اللغة الإنجليزية! حان وقت الاختبار لتقييم فهم الطلاب.
    أنت معلم لغة إنجليزية موجه للطلاب العرب. مهمتك هي إنشاء اختبار قصير وممتع لفيسبوك، يغطي مواضيع مثل: {lessons_summary}.
    
    **قواعد التنسيق الهامة واللغة:**
    1.  **اللغة الأساسية هي العربية:** يجب أن يكون المحتوى الرئيسي للمنشور باللغة العربية الفصحى.
    2.  **الفصل بين اللغتين:** يجب أن تكون الأسئلة أو الخيارات الإنجليزية متبوعة مباشرة بترجمتها العربية على سطر جديد منفصل. لا تخلط الإنجليزية والعربية في نفس السطر.
        مثال:
        Question 1: What is...?
        السؤال الأول: ما هو...؟
        
        (A) Option A
        (أ) الخيار أ
    3.  **لا تستخدم تنسيق الماركداون (Markdown):** لا تستخدم علامات مثل ** للنصوص الغامقة، * للمائلة، أو ## للعناوين. اكتب نصاً عادياً فقط.
    4.  استخدم فقرات واضحة مع مسافات مزدوجة بينها (سطرين فارغين).
    5.  أضف من 3 إلى 5 هاشتاغات ذات صلة باللغتين العربية والإنجليزية في نهاية المنشور، كل هاشتاغ على سطر جديد بعد المحتوى الرئيسي.
    6.  لا تذكر أنك ذكاء اصطناعي. اجعلها تبدو وكأنها معدة من قبل معلم.

    منشور الفيسبوك:
    """
    print("Generating exam post...")
    ai_generated_content = ask_ai(prompt)

    if not ai_generated_content:
        print("AI failed to generate exam post. Falling back to simple exam message.")
        return "حان وقت مراجعة ما تعلمناه هذا الأسبوع! استعدوا لاختبار قصير وممتع!\n#اختبار_انجليزي\n#EnglishQuiz"

    final_post_content = clean_ai_output(ai_generated_content)

    if "#" not in final_post_content[-50:]:
        if not final_post_content.strip().endswith('\n\n'):
            final_post_content += '\n\n'
        final_post_content += "#اختبارات_لغة_انجليزية\n#مراجعة_انجليزي\n#تقييم_اللغة\n#EnglishExam\n#LanguageAssessment"

    return final_post_content

# Modified main function to accept specific_teacher_id
def main(specific_teacher_id: str = None):
    teacher_meta = read_json("teacher_meta.json")
    # Load post_state and post_log, but only modify if it's a non-specific run
    post_state = read_json("post_state.json")
    post_log = read_json("post_log.json")

    # If a specific teacher is requested, bypass regular rotation and exam logic
    if specific_teacher_id:
        print(f"Manual run for specific teacher: {specific_teacher_id}")
        if specific_teacher_id not in teacher_meta:
            print(f"Error: Teacher ID '{specific_teacher_id}' not found in teacher_meta.json. Please check the ID.")
            return

        selected_teacher_id = specific_teacher_id
        teacher_info = teacher_meta.get(selected_teacher_id, {})

        # To ensure we get *a* lesson for a specific teacher, we might need to adjust this.
        # For testing, let's just get the "next" one based on its current state,
        # but without altering that state for the next *scheduled* run.
        # Create a temporary post_state for this specific teacher run so it doesn't affect the real one
        temp_post_state = {"teachers": post_state.setdefault("teachers", {}).get(selected_teacher_id, {"lesson_index": 0})}
        lesson_content = get_next_lesson(selected_teacher_id, teacher_meta, temp_post_state)
        # Note: We are not writing temp_post_state back, so the lesson_index isn't persisted for this test.

        image_to_post = get_random_teacher_image(selected_teacher_id)

        if not lesson_content:
            print(f"No lessons found for specific teacher {selected_teacher_id}. Cannot generate post.")
            return

        post_content = generate_teacher_post(selected_teacher_id, lesson_content, teacher_info)
        post_type_log = f"teacher_lesson_test_{selected_teacher_id}" # Indicate this is a test post

        print(f"Generated test post for {teacher_info.get('name', selected_teacher_id)}")
        
        # Post to Facebook and log it, but don't update main post_state for scheduling
        if post_to_facebook(post_content, image_to_post):
            post_log.setdefault("posts", []).append({
                "timestamp": datetime.datetime.now().isoformat(),
                "type": post_type_log,
                "content_preview": post_content[:200] + "...",
                "image_used": image_to_post if image_to_post else "none",
                "is_test": True # Mark as test post
            })
            write_json("post_log.json", post_log)
            print("Test post logged successfully (without affecting main schedule).")
        else:
            print("Failed to post test content to Facebook.")
        return # Exit after specific teacher run

    # --- Regular Scheduled or General Manual Run Logic (if specific_teacher_id is None) ---
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

    write_json("post_state.json", post_state) # Always save post_state for scheduled/general manual runs

if __name__ == "__main__":
    main()

