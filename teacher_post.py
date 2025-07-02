import os
import random
from common import read_json, write_json, ask_ai, post_to_facebook, clean_ai_output
import datetime

# --- Import random_post functions ---
# Assuming these functions are available, either directly in random_post.py
# or copied/integrated into this file for simplicity if random_post.py is small.
# For this example, let's assume you'll import them from random_post.py.
from random_post import generate_did_you_know_post, generate_vocabulary_challenge_post, generate_grammar_tip_post

CHARACTER_DIR = "characters"
LEARNING_MATERIALS_DIR = "learning_materials"

def get_next_teacher(teacher_meta: dict, post_state: dict) -> str:
    """Determines the next teacher based on rotation."""
    teacher_ids = sorted(teacher_meta.keys(), key=int)
    current_teacher_index = post_state.get("current_teacher_index", 0)

    if not teacher_ids:
        print("No teachers configured in teacher_meta.json.")
        return None

    next_teacher_id = teacher_ids[current_teacher_index % len(teacher_ids)]
    
    # Only advance the current_teacher_index if it's the first teacher post of the day's cycle
    # This ensures the same teacher is selected for both teacher slots in a day's cycle if needed.
    # The actual advancement will happen at the end of the 3-post cycle.
    
    return next_teacher_id

def advance_teacher_index(post_state: dict, teacher_meta: dict):
    """Advances the main teacher index for the next cycle."""
    teacher_ids = sorted(teacher_meta.keys(), key=int)
    post_state["current_teacher_index"] = (post_state.get("current_teacher_index", 0) + 1) % len(teacher_ids)


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
    # Advance lesson index only if this is a 'real' teacher post, not a test.
    # The main loop will handle saving post_state.
    teacher_state["lesson_index"] = (lesson_index + 1) % len(lessons)

    return next_lesson

def get_random_teacher_image(teacher_id: str, teacher_info: dict) -> str:
    """
    Selects a random image for the teacher.
    Uses 'image_folder_name' from teacher_info if specified,
    otherwise falls back to the teacher_id itself for the folder name.
    """
    folder_name = teacher_info.get("image_folder_name", teacher_id)
    teacher_image_dir = os.path.join(CHARACTER_DIR, folder_name)

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
    posting_style = teacher_info.get("posting_style", "friendly") # Default to 'friendly' if not specified

    prompt = f"""
    أنت معلم لغة إنجليزية موجه للطلاب العرب. اسمك هو {teacher_name}، وشخصيتك هي {posting_style}.
    مهمتك هي شرح الدرس التالي بأسلوب تعليمي، مكتوب بواسطة إنسان، ومناسب لفيسبوك.
    
    **في بداية المنشور، قم بإنشاء عنوان واضح ومباشر يحدد مستوى الدرس واسم المعلمة. يجب أن يكون العنوان على النحو التالي: 'درس اليوم: [مستوى الدرس باللغة العربية] مع {teacher_name}'. على سبيل المثال: 'درس اليوم: مستوى مبتدئ مع الأستاذة ندى'.**

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

    # Ensure hashtags are present and on new lines
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
        for post in teacher_posts[-5:]: # Look at the last 5 teacher lessons
            preview = post.get("content_preview", "").replace("...", "").strip()
            # Simple keyword extraction for exam topics - can be improved if needed
            # This logic might need refinement if content_preview doesn't reliably contain keywords
            if "المضارع البسيط" in preview or "Present Simple" in preview: recent_lesson_topics.append("المضارع البسيط")
            elif "المضارع المستمر" in preview or "Present Continuous" in preview: recent_lesson_topics.append("المضارع المستمر")
            elif "الماضي البسيط" in preview or "Past Simple" in preview: recent_lesson_topics.append("الماضي البسيط")
            elif "الأفعال" in preview or "Verbs" in preview: recent_lesson_topics.append("الأفعال")
            elif "الأسماء" in preview or "Nouns" in preview: recent_lesson_topics.append("الأسماء")
            elif "الصفات" in preview or "Adjectives" in preview: recent_lesson_topics.append("الصفات")
            else: 
                # Generic fallback to try and extract a topic from the content preview
                if 'درس اليوم' in preview:
                    topic_part = preview.split('درس اليوم', 1)[1]
                    if 'مع الأستاذة' in topic_part:
                        topic_part = topic_part.split('مع الأستاذة')[0]
                    if 'مع الأستاذ' in topic_part:
                        topic_part = topic_part.split('مع الأستاذ')[0]
                    recent_lesson_topics.append(topic_part.strip())
                elif 'عن' in preview: # previous generic fallback
                    recent_lesson_topics.append(preview.split('عن')[-1].strip())
                else: # take the whole preview as a topic if nothing specific found
                    recent_lesson_topics.append(preview)


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

    # Ensure hashtags are present and on new lines
    if "#" not in final_post_content[-50:]:
        if not final_post_content.strip().endswith('\n\n'):
            final_post_content += '\n\n'
        final_post_content += "#اختبارات_لغة_انجليزية\n#مراجعة_انجليزي\n#تقييم_اللغة\n#EnglishExam\n#LanguageAssessment"

    return final_post_content

def main(specific_teacher_id: str = None):
    teacher_meta = read_json("teacher_meta.json")
    post_state = read_json("post_state.json")
    post_log = read_json("post_log.json")

    # Initialize state variables if they don't exist
    post_state.setdefault("current_teacher_index", 0)
    post_state.setdefault("days_since_last_exam", 0)
    post_state.setdefault("post_slot_of_day", 0) # 0 = 1st post, 1 = 2nd, 2 = 3rd
    post_state.setdefault("teachers", {})

    EXAM_INTERVAL_DAYS = 5 # An exam every 5 days of posting cycles (which is 15 individual posts in total)

    # --- Manual trigger logic for specific teacher testing ---
    if specific_teacher_id:
        print(f"Manual test run for specific teacher: {specific_teacher_id}")
        if specific_teacher_id not in teacher_meta:
            print(f"Error: Teacher ID '{specific_teacher_id}' not found in teacher_meta.json. Please check the ID.")
            return

        selected_teacher_id = specific_teacher_id
        teacher_info = teacher_meta.get(selected_teacher_id, {})
        
        # For testing, we get the next lesson but don't persist index change in main post_state
        temp_teacher_state = post_state.setdefault("teachers", {}).get(selected_teacher_id, {"lesson_index": 0}).copy()
        temp_post_state_for_lesson_getter = {"teachers": {selected_teacher_id: temp_teacher_state}}
        lesson_content = get_next_lesson(selected_teacher_id, teacher_meta, temp_post_state_for_lesson_getter)
        # Revert lesson index change for testing purposes
        post_state["teachers"][selected_teacher_id]["lesson_index"] = temp_teacher_state["lesson_index"]

        image_to_post = get_random_teacher_image(selected_teacher_id, teacher_info)

        if not lesson_content:
            print(f"No lessons found for specific teacher {selected_teacher_id}. Cannot generate post.")
            return

        post_content = generate_teacher_post(selected_teacher_id, lesson_content, teacher_info)
        post_type_log = f"teacher_lesson_test_{selected_teacher_id}" # Indicate this is a test post

        print(f"Generated test post for {teacher_info.get('name', selected_teacher_id)}")
        
        if post_to_facebook(post_content, image_to_post):
            post_log.setdefault("posts", []).append({
                "timestamp": datetime.datetime.now().isoformat(),
                "type": post_type_log,
                "content_preview": post_content[:200] + "...",
                "image_used": image_to_post if image_to_post else "none",
                "is_test": True
            })
            write_json("post_log.json", post_log)
            print("Test post logged successfully (without affecting main schedule).")
        else:
            print("Failed to post test content to Facebook.")
        return # Exit after specific teacher run

    # --- Regular Scheduled Posting Logic (main daily cycle) ---
    post_content = ""
    image_to_post = None
    post_type_log = ""

    current_slot = post_state["post_slot_of_day"]
    selected_teacher_id = get_next_teacher(teacher_meta, post_state)
    teacher_info = teacher_meta.get(selected_teacher_id, {})

    # Random post types available
    random_post_generators = [
        generate_did_you_know_post,
        generate_vocabulary_challenge_post,
        generate_grammar_tip_post
    ]

    if post_state["days_since_last_exam"] >= EXAM_INTERVAL_DAYS and current_slot == 0:
        # If it's exam day AND the first post of the day, post the exam.
        print(f"It's exam day! (Days since last exam: {post_state['days_since_last_exam']})")
        post_content = generate_exam_post(teacher_meta, post_log)
        post_type_log = "exam"
        post_state["days_since_last_exam"] = 0 # Reset exam counter
        # Exam day replaces the first teacher post. The other 2 posts will proceed as normal.
        post_state["post_slot_of_day"] = (current_slot + 1) % 3 # Move to next slot for next run today
    else:
        if current_slot == 0 or current_slot == 2: # First and Third post are Teacher Posts
            print(f"Generating Teacher Post for slot {current_slot + 1}")
            lesson_content = get_next_lesson(selected_teacher_id, teacher_meta, post_state)
            image_to_post = get_random_teacher_image(selected_teacher_id, teacher_info)
            post_content = generate_teacher_post(selected_teacher_id, lesson_content, teacher_info)
            post_type_log = "teacher_lesson"
            
            # For the first teacher post of the day (slot 0), advance the teacher index and lesson index
            # This ensures the same teacher is used for both slots 0 and 2 on the same day if the index isn't advanced.
            # No, the get_next_lesson already advances the index. The teacher rotation happens at the end of the day's cycle.
            # So the current_teacher_index should only advance when all 3 posts for the day are done.
            
        elif current_slot == 1: # Second post is a Random Post
            print(f"Generating Random Post for slot {current_slot + 1}")
            selected_random_generator = random.choice(random_post_generators)
            post_content = selected_random_generator()
            post_type_log = "random_content"
            image_to_post = None # Random posts typically don't have images

        # Advance slot for next time this script runs today
        post_state["post_slot_of_day"] = (current_slot + 1) % 3

        # Advance exam counter and teacher_index only if it's the last post of the daily cycle
        if post_state["post_slot_of_day"] == 0: # It means all 3 posts for the day are done
            post_state["days_since_last_exam"] = post_state.get("days_since_last_exam", 0) + 1
            advance_teacher_index(post_state, teacher_meta) # Advance teacher for next day

    # Attempt to post to Facebook
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

    write_json("post_state.json", post_state) # Always save post_state

if __name__ == "__main__":
    main()
