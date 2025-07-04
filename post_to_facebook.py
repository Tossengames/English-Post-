import os
import json
import datetime
import sys
import requests
import google.generativeai as genai
import random 

# --- Configuration (from environment variables) ---
FB_PAGE_ID = os.getenv('FB_PAGE_ID')
FB_PAGE_TOKEN = os.getenv('FB_PAGE_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# --- Directory for Character Images ---
CHARACTER_DIR = "characters" # This should be at the root of your repository

# --- Gemini API Configuration ---
genai.configure(api_key=GEMINI_API_KEY)
GEMINI_MODEL = genai.GenerativeModel('gemini-1.5-flash') 

# --- Helper Functions ---
def read_json(filename, default_value=None):
    """
    Reads a JSON file, returns its content, or a default value if file doesn't exist or is corrupted.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Warning: {filename} not found or corrupted. Initializing with default value.")
        if default_value is not None:
            return default_value
        return {}

def write_json(filename, data):
    """Writes data to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def ask_ai(prompt_text):
    """Sends a prompt to the Gemini AI model and returns the response text."""
    response = None
    try:
        response = GEMINI_MODEL.generate_content(prompt_text)
        if hasattr(response, 'text') and response.text.strip():
            return response.text.strip()
        else:
            print("Gemini API primary response was empty or did not contain text.")
            if response and response.candidates:
                for candidate in response.candidates:
                    if candidate.content and hasattr(candidate.content, 'parts') and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text.strip():
                                print("Using text from candidate due to primary response issue.")
                                return part.text.strip()
            return None
    except Exception as e:
        print(f"Error generating AI content: {e}")
        return None

def clean_ai_output(text):
    """Cleans up common AI output artifacts."""
    text = text.strip()
    text = text.replace("Here's your Facebook post:", "").strip()
    text = text.replace("Here is the Facebook post:", "").strip()
    text = text.replace("تفضل منشورك على فيسبوك:", "").strip()
    text = text.replace("بالتأكيد، إليك منشور الفيسبوك:", "").strip()
    text = text.replace("إليك منشور الفيسبوك:", "").strip()
    text = text.replace("هذا هو منشورك!", "").strip()
    text = text.replace("يمكنني المساعدة في ذلك.", "").strip()
    text = text.replace("بصفتي نموذجًا لغويًا، لا يمكنني...", "").strip()
    text = text.replace("بصفتي نموذج ذكاء اصطناعي...", "").strip()
    text = text.replace("Sure, here is your post:", "").strip()
    text = text.replace("Of course, here is your post:", "").strip()
    text = text.replace("I can help with that.", "").strip()
    text = text.replace("I am an AI language model and cannot...", "").strip()
    
    # Remove markdown bold/italic/header formatting if any slipped through
    text = text.replace('**', '').replace('*', '').replace('##', '').replace('#', '')

    lines = text.split('\n')
    hashtags = [line for line in lines if line.strip().startswith('#')]
    content_lines = [line for line in lines if not line.strip().startswith('#')]
    
    cleaned_content = '\n'.join(content_lines).strip()

    if not hashtags:
        hashtags_to_add = [
            "#تعلم_اللغة_الإنجليزية",
            "#لغة_انجليزية",
            "#دروس_انجليزي",
            "#EnglishLearning",
            "#LearnEnglish"
        ]
        if not cleaned_content.endswith('\n\n'):
            cleaned_content += '\n\n'
        cleaned_content += '\n'.join(hashtags_to_add)
    else:
        if not cleaned_content.endswith('\n\n'):
            cleaned_content += '\n\n'
        cleaned_content += '\n'.join(hashtags)

    return cleaned_content

# --- Post to Facebook Function (UPDATED for local images) ---
def post_to_facebook(message, image_path=None):
    """
    Posts a message to Facebook, optionally with a local image file.
    This uses the /photos endpoint for direct image upload.
    """
    if not FB_PAGE_ID or not FB_PAGE_TOKEN:
        print("Facebook Page ID or Token is not set. Cannot post to Facebook.")
        return False

    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
    
    files = {}
    data = {
        'message': message,
        'access_token': FB_PAGE_TOKEN
    }

    if image_path:
        if os.path.exists(image_path):
            try:
                # Open image in binary read mode
                files = {'source': open(image_path, 'rb')}
                print(f"Attempting to upload image from: {image_path}")
            except Exception as e:
                print(f"Error opening image file {image_path}: {e}")
                image_path = None # Don't try to send a broken file
        else:
            print(f"Image file not found at: {image_path}. Posting message only.")
            image_path = None # Don't try to send a non-existent file

    response = requests.post(url, data=data, files=files)
    
    # Close the file if it was opened
    if image_path and 'source' in files:
        files['source'].close()

    if response.status_code == 200:
        print("Successfully posted to Facebook!")
        print(response.json())
        return True
    else:
        print(f"Error posting to Facebook: {response.status_code}")
        print(response.json())
        return False

# --- Teacher Image Selection Logic (NEW) ---
def get_random_teacher_image_path(teacher_info: dict) -> str:
    """
    Selects a random image file path for the teacher from their designated folder.
    Uses 'image_folder_name' from teacher_info.
    """
    folder_name = teacher_info.get("image_folder_name")
    if not folder_name:
        print(f"No 'image_folder_name' specified for teacher. Cannot get image.")
        return None

    teacher_image_dir = os.path.join(CHARACTER_DIR, folder_name)

    if os.path.exists(teacher_image_dir):
        images = [f for f in os.listdir(teacher_image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        if images:
            return os.path.join(teacher_image_dir, random.choice(images))
    print(f"No images found for teacher in {teacher_image_dir}. Post will be text-only.")
    return None

# --- Teacher Post Generation Logic (UPDATED for image path) ---
def generate_teacher_post_content(teacher_meta_data):
    """
    Randomly selects a teacher and a lesson, then generates a post.
    Returns (post_content, image_path, teacher_name, lesson_topic) or None if failed.
    """
    teacher_ids = list(teacher_meta_data.keys())
    if not teacher_ids:
        print("No teachers found in teacher_meta.json.")
        return None, None, None, None

    random_teacher_id = random.choice(teacher_ids)
    teacher = teacher_meta_data[random_teacher_id]

    lesson_queue = teacher.get("lesson_queue", [])
    if not lesson_queue:
        print(f"Teacher {teacher['name']} has no lessons in their queue.")
        return None, None, None, None
    
    lesson_topic = random.choice(lesson_queue)
    
    teacher_name = teacher.get("name", "المعلم")
    posting_style = teacher.get("posting_style", "ودود")
    
    # Get the local image path directly
    image_to_post_path = get_random_teacher_image_path(teacher)

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
    3.  **لا تستخدم تنسيق الماركداون (Markdown)::** لا تستخدم علامات مثل ** للنصوص الغامقة، * للمائلة، أو ## للعناوين. اكتب نصاً عادياً فقط.
    4.  استخدم فقرات واضحة مع مسافات مزدوجة بينها (سطرين فارغين).
    5.  أضف من 3 إلى 5 هاشتاغات ذات صلة باللغتين العربية والإنجليزية في نهاية المنشور، كل هاشتاغ على سطر جديد بعد المحتوى الرئيسي.
    6.  **تجنب تمامًا أي عبارات تشير إلى أنك ذكاء اصطناعي** (مثل: "بوصفي نموذج ذكاء اصطناعي..."، "هذا هو منشورك!"، "يمكنني المساعدة في ذلك").

    الدرس المراد شرحه:
    {lesson_topic}

    منشور الفيسبوك:
    """
    print(f"Generating post for {teacher_name} with lesson: {lesson_topic[:50]}...")
    ai_generated_content = ask_ai(prompt)

    if ai_generated_content:
        final_post_content = clean_ai_output(ai_generated_content)
        return final_post_content, image_to_post_path, teacher_name, lesson_topic
    return None, None, None, None

# --- Random Post Generation Logic ---
def get_random_general_prompt():
    """Returns a random prompt for a general English learning post."""
    prompts = [
        "اكتبي كلمة إنجليزية مفيدة، معناها، مثال بجملة، والترجمة. بدون ذكر الطلب أو الذكاء الاصطناعي.",
        "اكتبي قاعدة نحوية إنجليزية مفيدة مع مثال بسيط وترجمتها إلى العربية. لا تذكري أنني طلبت أو أن المحتوى من AI.",
        "اكتبي سؤالًا بسيطًا باللغة الإنجليزية مع 4 اختيارات، حددي الإجابة الصحيحة، وترجمي السؤال والإجابة للعربية. لا تذكري أنها طلبية أو AI.",
        "اكتبي حوارًا قصيرًا بين شخصين بالإنجليزية مع الترجمة العربية لكل جملة. لا تكتبي مقدمات أو أي ذكر للذكاء الاصطناعي.",
        "اكتبي تعبيرًا اصطلاحيًا (idiom) إنجليزيًا، معناه، مثال بجملة، وترجمته إلى العربية. بدون أي مقدمات أو ذكر للذكاء الاصطناعي.",
        "اكتبي عبارة إنجليزية شائعة الاستخدام، معناها بالعربية، واستخدامها بجملة وترجمتها.",
        "اكتبي كلمة إنجليزية ثم اعطي 4 كلمات أخرى، من ضمنها مرادف للكلمة الأصلية، واذكري الإجابة الصحيحة، مع الترجمة.",
        "اكتبي معلومة ثقافية صغيرة أو ممتعة عن دولة ناطقة بالإنجليزية، بالإنجليزية ثم ترجمتها للعربية. لا تذكري مصدرها أو أنها طلبية."
    ]
    return random.choice(prompts)

def generate_random_general_post_content():
    """Generates a random general English learning post using AI."""
    prompt = get_random_general_prompt()
    print(f"Generating random general post with prompt: {prompt[:50]}...")
    ai_generated_content = ask_ai(prompt)

    if ai_generated_content:
        final_post_content = clean_ai_output(ai_generated_content)
        return final_post_content
    return None

# --- Main Orchestration Logic ---
def main():
    # Load necessary data
    teacher_meta_data = read_json("teacher_meta.json", default_value={})
    post_log = read_json("post_log.json", default_value={"posts": []})
    post_log.setdefault("posts", []) 

    if not teacher_meta_data and not get_random_general_prompt(): 
        print("ERROR: Both teacher_meta.json is empty and no general random prompts are defined. Cannot generate any posts.")
        sys.exit(1)

    # --- Randomly Decide Post Type (Teacher vs. Random General) ---
    post_type_options = []
    if teacher_meta_data:
        # Give teacher posts a higher probability (2/3 chance)
        post_type_options.extend(["teacher"] * 2) 
    # General random posts (1/3 chance)
    post_type_options.append("random_general") 

    if not post_type_options:
        print("No content sources available (teachers or random general posts). Exiting.")
        sys.exit(0)

    chosen_post_type = random.choice(post_type_options)
    print(f"Randomly chosen post type for this run: {chosen_post_type}")

    post_content = None
    image_to_post = None # This will now store the local image path
    log_entry_details = {} 

    if chosen_post_type == "teacher":
        post_content, image_to_post, teacher_name, lesson_topic = generate_teacher_post_content(teacher_meta_data)
        if post_content:
            log_entry_details = {
                "post_category": "teacher_lesson",
                "teacher_name": teacher_name,
                "lesson_topic": lesson_topic
            }
        else:
            print("Failed to generate content for a teacher post. Attempting a random general post instead if possible.")
            if "random_general" in post_type_options:
                chosen_post_type = "random_general" 
            else:
                print("No fallback to random general post. Exiting.")
                sys.exit(1)

    if chosen_post_type == "random_general": 
        post_content = generate_random_general_post_content()
        if post_content:
            log_entry_details = {
                "post_category": "random_general",
                "topic_type": "AI_Generated_Random_Prompt" 
            }
        else:
            print("Failed to generate content for a random general post. Exiting.")
            sys.exit(1) 

    # --- Attempt to Post to Facebook ---
    if post_content:
        print("\n--- Generated Post Content ---")
        print(post_content)
        print("----------------------------\n")

        # Pass the local image path to the post_to_facebook function
        success = post_to_facebook(post_content, image_to_post)
        if success:
            post_log["posts"].append({
                "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                "type": log_entry_details.get("post_category", "unknown"),
                "content_preview": post_content[:200] + "..." if len(post_content) > 200 else post_content,
                "image_posted": bool(image_to_post), # Log whether an image was attempted
                **{k: v for k, v in log_entry_details.items() if k != "post_category"} 
            })
            write_json("post_log.json", post_log)
            print("Post successful and log updated.")
        else:
            print("Post failed. Log not updated for this entry.")
    else:
        print("No content was generated for posting. Exiting.")

    sys.exit(0) 

if __name__ == "__main__":
    main()
