import os
import random
from common import read_json, write_json, ask_ai, post_to_facebook
import datetime

RANDOM_POST_TYPES_FILE = "random_types.json"

def get_random_post_type(random_types_config: dict) -> str:
    """Selects a random post type from the configuration."""
    if not random_types_config or not random_types_config.get("types"):
        return None
    
    weights = [item.get("weight", 1) for item in random_types_config["types"]]
    choices = [item["name"] for item in random_types_config["types"]]
    
    return random.choices(choices, weights=weights, k=1)[0]

def generate_random_post(post_type: str) -> str:
    """Generates a random educational post using AI."""
    day_of_week = datetime.datetime.now().strftime("%A") # Get day name for context
    
    base_prompt = f"""
    أنت متخصص في تعليم اللغة الإنجليزية لمتحدثي اللغة العربية.
    مهمتك هي إنشاء منشور تعليمي قصير ومفيد لفيسبوك.
    المنشور يجب أن يكون باللغة العربية الفصحى مع إدراج الكلمات أو العبارات الإنجليزية في سياقها.
    تجنب تمامًا أي عبارات تشير إلى أنك ذكاء اصطناعي (مثل "بالتأكيد!", "إليك منشورك", "كمساعد ذكاء اصطناعي").
    المنشور يجب أن يكون بتنسيق نظيف، مع فواصل أسطر وعلامات ترقيم عربية صحيحة.
    أضف 3-5 هاشتاغات ذات صلة باللغتين العربية والإنجليزية في نهاية المنشور.
    """

    if post_type == "Word of the Day":
        prompt = base_prompt + """
        المطلوب: "كلمة اليوم". اختر كلمة إنجليزية شائعة، اشرح معناها باللغة العربية، قدم مثالاً على استخدامها في جملة إنجليزية مع ترجمتها للعربية.
        """
    elif post_type == "Grammar Tip":
        prompt = base_prompt + """
        المطلوب: "نصيحة نحوية". اختر نقطة نحوية إنجليزية بسيطة (مثل استخدام 'a'/'an', 'there/their/they're', الأزمنة الشائعة)، اشرحها باختصار باللغة العربية، وقدم مثالاً أو مثالين.
        """
    elif post_type == "Quiz":
        prompt = base_prompt + """
        المطلوب: "اختبار قصير". ضع سؤالاً واحداً أو سؤالين قصيرين في اللغة الإنجليزية (اختيار من متعدد أو أكمل الفراغ) مع تقديم الإجابة الصحيحة في نهاية المنشور (بعد مسافة أو سطر جديد لعدم الكشف عنها فوراً).
        """
    elif post_type == "Dialogue":
        prompt = base_prompt + """
        المطلوب: "حوار قصير". أنشئ حوارًا قصيرًا وبسيطًا بين شخصين في موقف يومي (مثل طلب قهوة، التحية، سؤال عن الاتجاهات). قدم الحوار باللغة الإنجليزية مع ترجمته الموجزة للعربية.
        """
    elif post_type == "Exercise":
        prompt = base_prompt + """
        المطلوب: "تمرين". قدم تمرينًا بسيطًا للطلاب (مثل ترتيب كلمات لتكوين جملة، مطابقة كلمات بمعانيها، تصحيح أخطاء). اترك مجالاً للإجابة أو قدم الإجابات في النهاية.
        """
    else:
        # Fallback for unknown types or general random content
        prompt = base_prompt + """
        المطلوب: منشور تعليمي عام حول نصائح لتعلم اللغة الإنجليزية أو معلومة ثقافية قصيرة متعلقة باللغة الإنجليزية.
        """

    print(f"Generating random post of type: {post_type}...")
    ai_generated_content = ask_ai(prompt)

    if not ai_generated_content:
        print("AI failed to generate random post. Falling back to simple message.")
        return f"مرحباً بكم! نتمنى لكم يوماً تعليمياً سعيداً في {get_current_day_of_week_arabic()}! #تعلم_الإنجليزي #لغة_انجليزية"

    # Add general hashtags if AI didn't include them, or ensure they are present
    if "#" not in ai_generated_content:
        ai_generated_content += "\n\n#تعلم_اللغة_الإنجليزية #لغة_انجليزية #دروس_انجليزي #EnglishLearning #LearnEnglish"

    return ai_generated_content

def main():
    random_types_config = read_json(RANDOM_POST_TYPES_FILE)
    post_type = get_random_post_type(random_types_config)

    if not post_type:
        print("No random post types configured. Skipping random post.")
        return

    post_content = generate_random_post(post_type)
    
    if post_to_facebook(post_content):
        post_log = read_json("post_log.json")
        post_log.setdefault("posts", []).append({
            "timestamp": datetime.datetime.now().isoformat(),
            "type": post_type,
            "content_preview": post_content[:100] + "..."
        })
        write_json("post_log.json", post_log)
    else:
        print("Failed to post random content to Facebook.")

if __name__ == "__main__":
    main()
