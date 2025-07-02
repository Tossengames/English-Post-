# post_random.py
import random
from common import ask_ai, post_to_facebook

def get_random_prompt():
    prompts = [
        # Vocabulary post
        "اكتبي كلمة إنجليزية مفيدة، معناها، مثال بجملة، والترجمة. بدون ذكر الطلب أو الذكاء الاصطناعي.",
        
        # Grammar tip
        "اكتبي قاعدة نحوية إنجليزية مفيدة مع مثال بسيط وترجمتها إلى العربية. لا تذكري أنني طلبت أو أن المحتوى من AI.",
        
        # English quiz
        "اكتبي سؤالًا بسيطًا باللغة الإنجليزية مع 4 اختيارات، حددي الإجابة الصحيحة، وترجمي السؤال والإجابة للعربية. لا تذكري أنها طلبية أو AI.",
        
        # Short dialogue/story
        "اكتبي حوارًا قصيرًا بين شخصين بالإنجليزية مع الترجمة العربية لكل جملة. لا تكتبي مقدمات أو أي ذكر للذكاء الاصطناعي.",
        
        # Idiom
        "اكتبي تعبيرًا اصطلاحيًا (idiom) إنجليزيًا، معناه، مثال بجملة، وترجمته إلى العربية. بدون أي مقدمات أو ذكر للذكاء الاصطناعي.",
        
        # Common expression
        "اكتبي عبارة إنجليزية شائعة الاستخدام، معناها بالعربية، واستخدامها بجملة وترجمتها.",
        
        # Synonym challenge
        "اكتبي كلمة إنجليزية ثم اعطي 4 كلمات أخرى، من ضمنها مرادف للكلمة الأصلية، واذكري الإجابة الصحيحة، مع الترجمة.",
        
        # Cultural fact
        "اكتبي معلومة ثقافية صغيرة أو ممتعة عن دولة ناطقة بالإنجليزية، بالإنجليزية ثم ترجمتها للعربية. لا تذكري مصدرها أو أنها طلبية."
    ]
    return random.choice(prompts)

def main():
    prompt = get_random_prompt()
    result = ask_ai(prompt)

    if result:
        # Remove any leading AI-like statements if any slipped through
        for bad in ["Here's", "Sure", "Of course"]:
            if result.lower().startswith(bad.lower()):
                result = result[len(bad):].lstrip(":،-– ")
        post_to_facebook(result.strip())
    else:
        print("⚠️ Could not generate random post.")

if __name__ == "__main__":
    main()
