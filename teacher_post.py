# teacher_post.py (Modified)
import os
import random
from common import read_json, write_json, ask_ai, post_to_facebook, clean_ai_output
import datetime
import sys # Import sys to read command line arguments

# --- Import random_post functions ---
# These functions should be defined in your separate random_post.py file
# Note: These are not used directly in this modified teacher_post.py, as random_post.py now handles its own generation.
# from random_post import generate_did_you_know_post, generate_vocabulary_challenge_post, generate_grammar_tip_post

CHARACTER_DIR = "characters"
LEARNING_MATERIALS_DIR = "learning_materials"

def get_next_teacher_for_slot(slot_index: int, teacher_meta: dict) -> str:
    """
    Determines the teacher ID based on the slot index.
    Slot 0: Teacher 1
    Slot 2: Teacher 2
    Slot 4: Teacher 3
    """
    if slot_index == 0:
        return "1"
    elif slot_index == 2:
        return "2"
    elif slot_index == 4:
        return "3"
    return None # Should not happen if slots are managed correctly

def advance_teacher_lesson_index(teacher_id: str, teacher_meta: dict, post_state: dict):
    """
    Advances the lesson index for a specific teacher.
    This function is called by main, not directly.
    """
    lessons = teacher_meta.get(teacher_id, {}).get("lesson_queue", [])
    if not lessons:
        print(f"No lesson queue found for teacher {teacher_id}. Cannot advance lesson index.")
        return

    teacher_state = post_state.setdefault("teachers", {}).setdefault(teacher_id, {"lesson_index": 0})
    current_lesson_index = teacher_state.get("lesson_index", 0)

    next_lesson_index = (current_lesson_index + 1) % len(lessons)
    teacher_state["lesson_index"] = next_lesson_index
    print(f"Advanced teacher {teacher_id} lesson index from {current_lesson_index} to {next_lesson_index}.")


def get_current_lesson_content(teacher_id: str, teacher_meta: dict, post_state: dict) -> str:
    """
    Gets the current lesson from the teacher's queue without advancing the index.
    The advancement is handled by advance_teacher_lesson_index after a successful post.
    """
    lessons = teacher_meta.get(teacher_id, {}).get("lesson_queue", [])
    if not lessons:
        print(f"No lesson queue found for teacher {teacher_id}.")
        return None

    teacher_state = post_state.setdefault("teachers", {}).setdefault(teacher_id, {"lesson_index": 0})
    lesson_index = teacher_state.get("lesson_index", 0)

    if lesson_index >= len(lessons):
        # This case should ideally be caught and handled by advance_teacher_lesson_index
        # if the lesson_index was not reset properly in a previous run.
        # For safety, reset here if somehow out of bounds.
        print(f"Warning: Teacher {teacher_id} lesson index {lesson_index} out of bounds ({len(lessons)}). Resetting to 0.")
        lesson_index = 0
        teacher_state["lesson_index"] = 0

    return lessons[lesson_index]


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

def generate_teacher_post(teacher_id: str, lesson_content: str, teacher_info: dict, post_number_of_day: int) -> str:
    """
    Generates the teacher's post using AI based on lesson content and style.
    Includes the post number of the day in the title and a shorter greeting.
    """
    teacher_name = teacher_info.get("name", "The Teacher")
    posting_style = teacher_info.get("posting_style", "friendly") # Default to 'friendly' if not specified

    # Adjusting the title creation to include the post number of the day
    # Assuming post_number_of_day is 0-indexed, display it as 1-6.
    display_post_number_for_title = (post_number_of_day // 2) + 1 # Converts 0,1->1; 2,3->2; 4,5->3 for teacher index
    
    # Decide which teacher is speaking for the title
    if post_number_of_day == 0:
        teacher_in_title = "الأستاذة ندى"
    elif post_number_of_day == 2:
        teacher_in_title = "الأستاذة ريتا"
    elif post_number_of_day == 4:
        teacher_in_title = "الأستاذة سارة"
    else:
        teacher_in_title = teacher_name # Fallback, though controlled by main

    prompt = f"""
    أنت معلم لغة إنجليزية موجه للطلاب العرب. اسمك هو {teacher_name}، وشخصيتك هي {posting_style}.
    مهمتك هي شرح الدرس التالي بأسلوب تعليمي، مكتوب بواسطة إنسان، ومناسب لفيسبوك.
    
    **في بداية المنشور، ابدأ بتحية قصيرة جداً (مثل "أهلاً!" أو "مرحباً!"). ثم قم بإنشاء عنوان واضح ومباشر يحدد مستوى الدرس واسم المعلمة ورقم المنشور لهذا اليوم. يجب أن يكون العنوان على النحو التالي: 'درس اليوم: [مستوى الدرس باللغة العربية] - المنشور رقم {display_post_number_for_title} مع {teacher_in_title}'. على سبيل المثال: 'درس اليوم: مستوى مبتدئ - المنشور رقم 1 مع الأستاذة ندى'.**

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
        teacher_posts = [p for p in post_log["posts"] if p.get("type") and "teacher_lesson" in p.get("type")]
        for post in teacher_posts[-5:]: # Look at the last 5 teacher lessons
            preview = post.get("content_preview", "").replace("...", "").strip()
            # Simple keyword extraction for exam topics - can be improved if needed
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
    3.  **لا تستخدم تنسيق الماركداون (Markdown)::** لا تستخدم علامات مثل ** للنصوص الغامقة، * للمائلة، أو ## للعناوين. اكتب نصاً عادياً فقط.
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

def main(current_post_slot: int = None, specific_teacher_id: str = None):
    """
    Main function to generate and post content based on the current slot or manual override.
    current_post_slot: 0-5 for scheduled slots, None for specific_teacher_id test.
    specific_teacher_id: Used for manual testing of a single teacher post.
    """
    teacher_meta = read_json("teacher_meta.json")
    post_state = read_json("post_state.json")
    post_log = read_json("post_log.json")

    # Initialize state variables if they don't exist
    post_state.setdefault("days_since_last_exam", 0)
    post_state.setdefault("teachers", {})
    # current_post_cycle_index is now managed by post_to_facebook.py and passed in
    # This script will only advance global state if it's the last post of a full cycle.

    EXAM_INTERVAL_DAYS = 5 # An exam every 5 days of posting cycles (which is 30 individual posts in total, 6 posts/day * 5 days)

    post_content = ""
    image_to_post = None
    post_type_log = ""

    # --- Manual trigger logic for specific teacher testing (from workflow_dispatch) ---
    if specific_teacher_id:
        print(f"Manual test run for specific teacher: {specific_teacher_id}")
        if specific_teacher_id not in teacher_meta:
            print(f"Error: Teacher ID '{specific_teacher_id}' not in teacher_meta.json. Please check.")
            return

        teacher_info = teacher_meta.get(specific_teacher_id, {})
        lesson_content = get_current_lesson_content(specific_teacher_id, teacher_meta, post_state)
        image_to_post = get_random_teacher_image(specific_teacher_id, teacher_info)

        if not lesson_content:
            print(f"No lessons found for specific teacher {specific_teacher_id}. Cannot generate post.")
            return

        # For specific teacher tests, we can use slot 0 (or any) for title formatting,
        # but it doesn't affect the actual sequence.
        # We also don't advance the lesson index for test posts.
        post_content = generate_teacher_post(specific_teacher_id, lesson_content, teacher_info, 0)
        post_type_log = f"teacher_lesson_test_{specific_teacher_id}"

        print(f"Generated test post for {teacher_info.get('name', specific_teacher_id)}")
        
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

    # --- Regular Scheduled Posting Logic (managed by current_post_slot) ---
    # Determine if it's an exam slot (always slot 0, replacing Teacher 1)
    # The decision to post an exam is only made if it's slot 0 of the day.
    if current_post_slot == 0 and post_state["days_since_last_exam"] >= EXAM_INTERVAL_DAYS:
        print(f"It's exam day! Generating Exam Post for slot {current_post_slot}.")
        post_content = generate_exam_post(teacher_meta, post_log)
        post_type_log = "exam"
        post_state["days_since_last_exam"] = 0 # Reset exam counter after posting
    
    # Otherwise, proceed with teacher or random posts based on slot
    elif current_post_slot % 2 == 0: # Slots 0, 2, 4 are teacher posts
        # Determine the teacher based on the slot
        teacher_id_for_slot = get_next_teacher_for_slot(current_post_slot, teacher_meta)
        if not teacher_id_for_slot:
            print(f"Error: No teacher mapped for slot {current_post_slot}. Skipping post.")
            return

        teacher_info = teacher_meta.get(teacher_id_for_slot, {})
        print(f"Generating Teacher Post for slot {current_post_slot} ({teacher_info.get('name', teacher_id_for_slot)})")
        
        lesson_content = get_current_lesson_content(teacher_id_for_slot, teacher_meta, post_state)
        image_to_post = get_random_teacher_image(teacher_id_for_slot, teacher_info)
        post_content = generate_teacher_post(teacher_id_for_slot, lesson_content, teacher_info, current_post_slot)
        post_type_log = f"teacher_lesson_{teacher_id_for_slot}"
        
        # Advance the lesson for this specific teacher only after generating the post
        advance_teacher_lesson_index(teacher_id_for_slot, teacher_meta, post_state)
            
    elif current_post_slot % 2 == 1: # Slots 1, 3, 5 are random posts
        print(f"Generating Random Post for slot {current_post_slot}")
        # Call the random_post.main() function (if it returns content, otherwise generate directly here)
        # Assuming random_post.main() generates and posts itself,
        # or we need to import its generation functions.
        # For simplicity, let's assume random_post.py contains functions to generate, not post.
        # This will be handled by the call from post_to_facebook.py
        # THIS PART OF THE LOGIC SHOULD NOT BE IN teacher_post.py anymore for random posts.
        # The calling script (post_to_facebook.py) will decide what to call.
        pass # This branch will now be handled by post_to_facebook.py calling random_post.main()


    # Attempt to post to Facebook IF content was generated here (i.e., not a random post slot)
    if post_content: # Only if a teacher or exam post was generated
        if post_to_facebook(post_content, image_to_post):
            post_log.setdefault("posts", []).append({
                "timestamp": datetime.datetime.now().isoformat(),
                "type": post_type_log,
                "content_preview": post_content[:200] + "...",
                "image_used": image_to_post if image_to_post else "none",
                "slot_index": current_post_slot # Log the slot index
            })
            write_json("post_log.json", post_log)
            print("Post logged successfully.")
        else:
            print("Failed to post content to Facebook. Post state not updated for failed post.")
    else:
        # This branch will be hit if it was a random post slot (1, 3, 5)
        # as post_content is not generated in this script for those slots.
        # The calling script (post_to_facebook.py) will handle random_post.main()
        print(f"No teacher/exam content generated in teacher_post.py for slot {current_post_slot}.")

    # Increment days_since_last_exam ONLY if the full 6-post cycle is completed (slot 5 has been processed)
    # This logic is best handled in post_to_facebook.py as it orchestrates the full cycle.
    # We will remove this responsibility from teacher_post.py
    
    write_json("post_state.json", post_state) # Always save post_state at the end

if __name__ == "__main__":
    # For direct testing, you might run: python teacher_post.py --slot 0
    # Or: python teacher_post.py --teacher 1
    # This is mainly for scheduled/orchestrated runs now.
    
    # Parse command line arguments for manual testing
    # Expecting: python teacher_post.py [specific_teacher_id] [current_post_slot]
    
    _specific_teacher_id = None
    _current_post_slot = None

    if len(sys.argv) > 1 and sys.argv[1] not in ('None', ''):
        _specific_teacher_id = sys.argv[1]

    if len(sys.argv) > 2 and sys.argv[2] not in ('None', ''):
        try:
            _current_post_slot = int(sys.argv[2])
        except ValueError:
            print(f"Warning: Invalid current_post_slot value '{sys.argv[2]}'. Ignoring.")

    # If a specific teacher ID is provided, it's a test run for that teacher
    if _specific_teacher_id:
        main(specific_teacher_id=_specific_teacher_id)
    # Otherwise, assume it's a scheduled run and current_post_slot must be provided
    elif _current_post_slot is not None:
        main(current_post_slot=_current_post_slot)
    else:
        print("Usage: python teacher_post.py [specific_teacher_id] [current_post_slot]")
        print("  or:  python teacher_post.py --slot <0-5> (for scheduled run simulation)")
        print("  or:  python teacher_post.py --teacher <ID> (for specific teacher test)")
        print("No arguments provided, exiting.")
        sys.exit(1)

