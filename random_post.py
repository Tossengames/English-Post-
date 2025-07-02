import os
import random
from common import read_json, write_json, ask_ai, post_to_facebook, clean_ai_output
import datetime

# --- General Utility Functions (from common.py, for clarity if this script runs standalone) ---
# Assuming read_json, write_json, ask_ai, clean_ai_output, post_to_facebook are accessible.
# If this file runs completely standalone, you'd copy them here or import specifically.

# --- New Post Generation Functions ---

def generate_did_you_know_post():
    """Generates an engaging 'Did You Know?' fact post."""
    prompt = """
    أنت حساب تعليمي للغة الإنجليزية على فيسبوك. مهمتك هي نشر حقيقة شيقة أو معلومة ثقافية قصيرة وممتعة عن اللغة الإنجليزية أو الدول الناطقة بها.
    يجب أن تكون الحقيقة سهلة الفهم، مكتوبة بأسلوب ودي وجذاب.

    **قواعد التنسيق الهامة واللغة:**
    1.  **ابدأ المنشور بـ "هل تعلم؟" (Did You Know?).**
    2.  **اللغة الأساسية هي العربية:** يجب أن يكون المحتوى الرئيسي للمنشور باللغة العربية الفصحى.
    3.  **الفصل بين اللغتين:** إذا استخدمت كلمة أو جملة إنجليزية، يجب أن يتبعها ترجمتها العربية مباشرةً على سطر جديد منفصل. لا تخلط الإنجليزية والعربية في نفس السطر.
    4.  **لا تستخدم تنسيق الماركداون (Markdown):** اكتب نصاً عادياً فقط.
    5.  استخدم فقرات واضحة مع مسافات مزدوجة بينها (سطرين فارغين).
    6.  أضف 3-5 هاشتاغات ذات صلة باللغتين العربية والإنجليزية في نهاية المنشور.
    7.  **تجنب تمامًا أي عبارات تشير إلى أنك ذكاء اصطناعي.**
    8.  **أضف عبارة تحث المستخدمين على التفاعل، مثل الإعجاب أو المشاركة أو التعليق على الحقيقة.**

    مثال على حقيقة:
    الإنجليزية هي اللغة الرسمية لأكثر من 50 دولة حول العالم.

    منشور الفيسبوك:
    """
    print("Generating 'Did You Know?' post...")
    ai_generated_content = ask_ai(prompt)
    final_content = clean_ai_output(ai_generated_content)

    if not final_content.strip().endswith('\n\n'):
        final_content += '\n\n'
    final_content += "#هل_تعلم_الإنجليزية\n#حقائق_اللغة\n#معلومات_مفيدة\n#EnglishFacts\n#DidYouKnow"

    return final_content

def generate_vocabulary_challenge_post():
    """Generates a vocabulary challenge post."""
    prompt = """
    أنت حساب تعليمي للغة الإنجليزية على فيسبوك. مهمتك هي نشر تحدي مفردات قصير وممتع.
    يجب أن تقدم كلمة إنجليزية واحدة (ربما كلمة متوسطة أو متقدمة قليلاً)، وتطلب من المستخدمين تعريفها أو استخدامها في جملة.

    **قواعد التنسيق الهامة واللغة:**
    1.  **ابدأ المنشور بـ "تحدي المفردات!" (Vocabulary Challenge!).**
    2.  **اذكر الكلمة الإنجليزية بوضوح في بداية التحدي.**
    3.  **اللغة الأساسية هي العربية:** يجب أن يكون المحتوى الرئيسي للمنشور باللغة العربية الفصحى.
    4.  **الفصل بين اللغتين:** إذا استخدمت كلمة أو جملة إنجليزية، يجب أن يتبعها ترجمتها العربية مباشرةً على سطر جديد منفصل. لا تخلط الإنجليزية والعربية في نفس السطر.
    5.  **لا تستخدم تنسيق الماركداون (Markdown):** اكتب نصاً عادياً فقط.
    6.  استخدم فقرات واضحة مع مسافات مزدوجة بينها (سطرين فارغين).
    7.  أضف 3-5 هاشتاغات ذات صلة باللغتين العربية والإنجليزية في نهاية المنشور.
    8.  **تجنب تمامًا أي عبارات تشير إلى أنك ذكاء اصطناعي.**
    9.  **أضف عبارة تحث المستخدمين على التفاعل في التعليقات.**

    مثال على تحدي:
    كلمة اليوم: 'Ubiquitous'
    تحدي المفردات!
    من يستطيع تعريف كلمة 'Ubiquitous' أو استخدامها في جملة؟
    نحن نرى الهواتف الذكية في كل مكان هذه الأيام، أليس كذلك؟

    منشور الفيسبوك:
    """
    print("Generating 'Vocabulary Challenge' post...")
    ai_generated_content = ask_ai(prompt)
    final_content = clean_ai_output(ai_generated_content)

    if not final_content.strip().endswith('\n\n'):
        final_content += '\n\n'
    final_content += "#تحدي_مفردات\n#كلمات_انجليزية\n#تعلم_اللغة_الإنجليزية\n#VocabularyChallenge\n#EnglishWords"

    return final_content

def generate_grammar_tip_post():
    """Generates a quick grammar tip post."""
    prompt = """
    أنت حساب تعليمي للغة الإنجليزية على فيسبوك. مهمتك هي نشر نصيحة نحوية سريعة ومفيدة أو تصحيح لخطأ شائع.
    يجب أن تكون النصيحة واضحة ومباشرة، مع أمثلة باللغتين الإنجليزية والعربية.

    **قواعد التنسيق الهامة واللغة:**
    1.  **ابدأ المنشور بـ "نصيحة نحوية سريعة!" (Quick Grammar Tip!).**
    2.  **اللغة الأساسية هي العربية:** يجب أن يكون المحتوى الرئيسي للمنشور باللغة العربية الفصحى.
    3.  **الفصل بين اللغتين:** الأمثلة الإنجليزية يجب أن يتبعها ترجمتها العربية مباشرةً على سطر جديد منفصل. لا تخلط الإنجليزية والعربية في نفس السطر.
    4.  **لا تستخدم تنسيق الماركداون (Markdown):** اكتب نصاً عادياً فقط.
    5.  استخدم فقرات واضحة مع مسافات مزدوجة بينها (سطرين فارغين).
    6.  أضف 3-5 هاشتاغات ذات صلة باللغتين العربية والإنجليزية في نهاية المنشور.
    7.  **تجنب تمامًا أي عبارات تشير إلى أنك ذكاء اصطناعي.**
    8.  **أضف عبارة تحث المستخدمين على التفاعل أو طرح الأسئلة.**

    مثال على نصيحة:
    نصيحة نحوية سريعة!
    الفرق بين 'Affect' و 'Effect':
    'Affect' فعل، ويعني 'يؤثر على'.
    'Effect' اسم، ويعني 'تأثير'.

    The rain affected the game.
    المطر أثر على المباراة.
    The effect of the rain was a delayed game.
    كان تأثير المطر هو تأجيل المباراة.

    منشور الفيسبوك:
    """
    print("Generating 'Grammar Tip' post...")
    ai_generated_content = ask_ai(prompt)
    final_content = clean_ai_output(ai_generated_content)

    if not final_content.strip().endswith('\n\n'):
        final_content += '\n\n'
    final_content += "#نصائح_نحوية\n#قواعد_الإنجليزية\n#تعلم_الإنجليزية\n#GrammarTips\n#EnglishGrammar"

    return final_content

# --- Main Function to Select and Post ---

def main():
    # List of available random post types
    post_types = [
        generate_did_you_know_post,
        generate_vocabulary_challenge_post,
        generate_grammar_tip_post
    ]

    # Randomly select a post type
    selected_generator = random.choice(post_types)
    post_content = selected_generator() # Generate the post content

    # Post to Facebook (assuming post_to_facebook is accessible globally or imported)
    # random_post types currently don't use images
    if post_to_facebook(post_content, image_path=None):
        print("Successfully posted a random content type to Facebook.")
        # You might want to log these random posts too, similar to teacher_post.py
        # You'd need a post_log.json here or pass it around.
        # For simplicity of just getting the types working, we'll omit explicit logging here for now.
    else:
        print("Failed to post random content type to Facebook.")

if __name__ == "__main__":
    main()
