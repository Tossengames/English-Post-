import os
import random
from common import read_json, write_json, ask_ai, post_to_facebook, get_current_day_of_week_arabic, clean_ai_output
import datetime

RANDOM_POST_TYPES_FILE = "random_types.json"

def get_random_post_type(random_types_config: dict) -> str:
    """Selects a random post type from the configuration based on weights."""
    if not random_types_config or not random_types_config.get("types"):
        print("No random post types configured in random_types.json.")
        return None

    types = random_types_config["types"]
    if not types:
        print("Random types list is empty.")
        return None

    weights = [item.get("weight", 1) for item in types]
    choices = [item["name"] for item in types]

    try:
        return random.choices(choices, weights=weights, k=1)[0]
    except Exception as e:
        print(f"Error selecting random post type: {e}. Falling back to first type if available.")
        return choices[0] if choices else None


def generate_random_post(post_type: str) -> str:
    """Generates a random educational post using AI."""
    day_of_week = datetime.datetime.now().strftime("%A")

    # --- UPDATED PROMPT FOR LANGUAGE PRIORITY AND CLARITY ---
    base_prompt = f"""
    أنت معلم لغة إنجليزية موجه للطلاب العرب. مهمتك هي إنشاء منشور فيسبوك موجز، مفيد، وتعليمي.
    
    **قواعد التنسيق الهامة واللغة:**
    1.  **اللغة الأساسية هي العربية:** يجب أن يكون المحتوى الرئيسي للمنشور باللغة العربية الفصحى.
    2.  **الفصل بين اللغتين:** يتم استخدام الكلمات أو الجمل الإنجليزية للمصطلحات، الأمثلة، أو الأسئلة، ويجب أن يتبعها دائمًا ترجمتها العربية مباشرةً على سطر جديد منفصل. لا تخلط الإنجليزية والعربية في نفس السطر.
        مثال:
        Word: Hello
        الكلمة: مرحباً
        
        Example sentence: Hello, how are you?
        مثال الجملة: مرحباً، كيف حالك؟
    3.  **لا تستخدم تنسيق الماركداون (Markdown):** لا تستخدم علامات مثل ** للنصوص الغامقة، * للمائلة، أو ## للعناوين. اكتب نصاً عادياً فقط.
    4.  استخدم فقرات واضحة مع مسافات مزدوجة بينها (سطرين فارغين).
    5.  أضف من 3 إلى 5 هاشتاغات ذات صلة باللغتين العربية والإنجليزية في نهاية المنشور، كل هاشتاغ على سطر جديد بعد المحتوى الرئيسي.
    6.  **تجنب تمامًا أي عبارات تشير إلى أنك ذكاء اصطناعي** (مثل: "بوصفي نموذج ذكاء اصطناعي..."، "هذا هو منشورك!"، "يمكنني المساعدة في ذلك").
    """

    if post_type == "Word of the Day":
        prompt = base_prompt + """
        Requirement: "Word of the Day". Choose a common English word, explain its meaning in Arabic, and provide an example of its use in an English sentence with an Arabic translation.
        """
    elif post_type == "Grammar Tip":
        prompt = base_prompt + """
        Requirement: "Grammar Tip". Choose a simple English grammar point (e.g., use of 'a'/'an', 'there/their/they're', common tenses), explain it concisely in Arabic, and provide one or two examples.
        """
    elif post_type == "Quiz":
        prompt = base_prompt + """
        Requirement: "Short Quiz". Create one or two short English questions (multiple choice or fill-in-the-blank) and provide the correct answer(s) at the end of the post (after some space or a new line to avoid immediate reveal). Remember to separate English question/options from Arabic translations.
        """
    elif post_type == "Dialogue":
        prompt = base_prompt + """
        Requirement: "Short Dialogue". Create a short, simple dialogue between two people in an everyday situation (e.g., ordering coffee, greetings, asking for directions). Provide the dialogue in English, each line followed by its Arabic translation on a new line.
        """
    elif post_type == "Exercise":
        prompt = base_prompt + """
        Requirement: "Exercise". Provide a simple exercise for students (e.g., rearrange words to form a sentence, match words with meanings, correct mistakes). Provide the instructions/questions in English followed by Arabic, and include an answer key at the end (after some space).
        """
    else:
        prompt = base_prompt + """
        Requirement: A general educational post about English learning tips or a short cultural fact related to the English language.
        """

    print(f"Generating random post of type: {post_type} for {day_of_week} (local time).")
    ai_generated_content = ask_ai(prompt)

    if not ai_generated_content:
        print("AI failed to generate random post. Falling back to simple message.")
        return f"مرحباً بكم! نتمنى لكم يوماً تعليمياً سعيداً في {get_current_day_of_week_arabic()}!\n#تعلم_الإنجليزي\n#لغة_انجليزية"

    final_post_content = clean_ai_output(ai_generated_content)

    if "#" not in final_post_content[-50:]:
        if not final_post_content.strip().endswith('\n\n'):
            final_post_content += '\n\n'
        final_post_content += "#تعلم_اللغة_الإنجليزية\n#لغة_انجليزية\n#دروس_انجليزي\n#EnglishLearning\n#LearnEnglish"

    return final_post_content

def main():
    random_types_config = read_json(RANDOM_POST_TYPES_FILE)
    post_type = get_random_post_type(random_types_config)

    if not post_type:
        print("Failed to determine a random post type. Exiting random post process.")
        return

    post_content = generate_random_post(post_type)

    if post_to_facebook(post_content):
        post_log = read_json("post_log.json")
        post_log.setdefault("posts", []).append({
            "timestamp": datetime.datetime.now().isoformat(),
            "type": post_type,
            "content_preview": post_content[:200] + "..."
        })
        write_json("post_log.json", post_log)
        print("Post logged successfully.")
    else:
        print("Failed to post random content to Facebook.")

if __name__ == "__main__":
    main()
