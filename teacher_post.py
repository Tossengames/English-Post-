import random
from common import ask_ai, post_to_facebook, clean_ai_output, get_pixabay_image_url

# Centralized Pixabay Keywords
PIXABAY_GLOBAL_KEYWORDS = [
    "education", "learning", "classroom", "study", 
    "books", "knowledge", "language", "school"
]

# Built-in lesson topics categorized by level
LESSON_TOPICS = {
    "beginner": [
        "زمن المضارع البسيط (Present Simple)",
        "أدوات التعريف (a, an, the)",
        "المفردات الأساسية (الألوان، الأرقام، العائلة)",
        "حروف الجر الأساسية (in, on, at)"
    ],
    "intermediate": [
        "زمن الماضي البسيط (Past Simple)",
        "المقارنة والتفضيل (Comparatives/Superlatives)",
        "الأفعال الناقصة (Modal Verbs: can, should, must)",
        "الجمل الشرطية (Conditionals)"
    ],
    "advanced": [
        "زمن المضارع التام (Present Perfect)",
        "المبني للمجهول (Passive Voice)",
        "الأساليب البلاغية في الإنجليزية",
        "كتابة التقارير الرسمية"
    ]
}

# Posting tones with Arabic descriptions
POST_TONES = {
    "serious": "أسلوب أكاديمي رسمي مع شرح مفصل",
    "humorous": "أسلوب تعليمي ممزوج بلمسات من الدعابة المناسبة",
    "motivational": "أسلوب تحفيزي يشجع على التعلم",
    "interactive": "أسلوب تفاعلي مع طرح الأسئلة"
}

# Common CTAs (Call to Action)
CTAS = [
    "ما هي الجمل التي يمكنك تكوينها باستخدام هذه القاعدة؟ شاركها في التعليقات!",
    "هل لديك أسئلة عن هذا الدرس؟ اكتبها في التعليقات وسنجيب عليها!",
    "جرب تطبيق هذه القاعدة في جملة من إنشائك!",
    "ما أصعب جزء في هذا الدرس برأيك؟"
]

def get_teacher_image_from_pixabay():
    """Fetches a random educational image from Pixabay"""
    keyword = random.choice(PIXABAY_GLOBAL_KEYWORDS)
    print(f"Fetching image with keyword: {keyword}")
    return get_pixabay_image_url(keyword)

def generate_lesson_post():
    """Generates a formal Arabic lesson post with random tone"""
    # Random selections
    level = random.choice(list(LESSON_TOPICS.keys()))
    topic = random.choice(LESSON_TOPICS[level])
    tone = random.choice(list(POST_TONES.keys()))
    cta = random.choice(CTAS)
    
    # Arabic level names
    level_arabic = {
        "beginner": "للمبتدئين",
        "intermediate": "للمتوسطين",
        "advanced": "للمتقدمين"
    }[level]

    prompt = f"""
    أنت خبير في تعليم اللغة الإنجليزية للعرب. مهمتك كتابة منشور تعليمي باللغة العربية الفصحى الرسمية.
    
    **المتطلبات:**
    1. العنوان: "درس اليوم: {topic} {level_arabic}"
    2. الأسلوب: {POST_TONES[tone]}
    3. المحتوى:
       - شرح واضح للقاعدة/الموضوع
       - أمثلة بالإنجليزية مع ترجمة عربية فورية أسفل كل مثال
       - تجنب تمامًا أي إشارة للذكاء الاصطناعي
    4. التنسيق:
       - فقرات قصيرة مع سطر فارغ بينها
       - لا تستخدم أي تنسيق ماركداون
    5. الهاشتاقات: 3-4 هاشتاجات فقط ذات صلة
    6. ختام المنشور: دعوة للتفاعل ({cta})

    اكتب المنشور الآن:
    """
    
    print(f"Generating {tone} post about: {topic} ({level} level)")
    response = ask_ai(prompt)
    
    if response:
        content = clean_ai_output(response)
        image_url = get_teacher_image_from_pixabay()
        return content, image_url, topic
    return None, None, None

def main():
    print("--- Generating English Lesson Post ---")
    post, image, topic = generate_lesson_post()

    if post:
        print("\n--- Generated Post ---")
        print(post)
        print("\n---")
        
        if post_to_facebook(post, image):
            print(f"Posted successfully about: {topic}")
        else:
            print("Posting failed")
    else:
        print("Content generation failed")

if __name__ == "__main__":
    main()