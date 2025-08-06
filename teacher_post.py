import random
from common import ask_ai, post_to_facebook, clean_ai_output, get_pixabay_image_url

# Image Keywords
PIXABAY_KEYWORDS = [
    "grammar", "dictionary", "education", "writing", "test", 
    "exam", "IELTS", "language", "vocabulary", "question", 
    "quiz", "interview", "speaking", "pronunciation", "phonetics"
]

# Lesson Topics
LESSON_TOPICS = [
    # Grammar Topics
    "🔍 الفرق بين المضارع التام والماضي البسيط",
    "💡 الجمل الشرطية بأنواعها مع أمثلة واقعية",
    "🛠️ استخدامات الأفعال الناقصة في السياقات المهنية",
    "🎭 صيغة المبني للمجهول في الكتابة الأكاديمية",
    "⚠️ أدوات التعريف والنكرة - الأخطاء الشائعة",
    
    # Vocabulary Topics
    "📚 5 مفردات أكاديمية لكتابة مقالات",
    "💼 3 عبارات إنجليزية الأعمال للمحترفين",
    "✍️ تعزيز مفردات كتابة الآيلتس",
    "🔤 مرادفات للكلمات المستهلكة",
    "🤝 المتلازمات اللفظية مع الأفعال الشائعة",
    
    # Pronunciation Topics
    "🔊 3 كلمات تُنطق خطأً بشكل شائع",
    "🎙️ الحروف الصامتة في الإنجليزية",
    "🗣️ الأصوات الصعبة للناطقين بالعربية",
    "👄 تويستات اللسان لتحسين النطق",
    "🎵 أنماط التشديد في الكلمات الإنجليزية",
    
    # Question/Quiz Topics
    "❓ أخطاء قواعدية شائعة - هل تعرفها؟",
    "🔎 اكتشف الخطأ في هذه الجملة",
    "🔄 تحويل الجمل - تحدٍ لغوي",
    "📝 اختر الإجابة الصحيحة",
    "✅ أي جملة صحيحة؟ اختبار سريع",
    
    # IELTS Practice
    "🎤 نصائح للجزء الأول من اختبار الآيلتس",
    "✍️ هيكل مقالة الآيلتس للدرجة 9",
    "👂 استراتيجيات قسم الاستماع في الآيلتس",
    "📚 نصائح إدارة الوقت في القراءة",
    "📊 معايير التقييم في اختبار الآيلتس"
]

# Posting Styles
POST_STYLES = {
    "Grammar Focus": {
        "hashtags": "#قواعد_الإنجليزية #تعلم_الإنجليزية #الإنجليزية 📚",
        "structure": "📝 شرح القاعدة في سطرين\n💡 مثال عملي (الإنجليزية + العربية)\n❓ سؤال سريع للتفاعل"
    },
    "Vocabulary Builder": {
        "hashtags": "#مفردات_الإنجليزية #كلمة_اليوم #تعلم_اللغة 📖", 
        "structure": "✨ 3 كلمات/عبارات مع:\n- المعنى\n- مثال\n- النطق المبسط"
    },
    "Quiz Time": {
        "hashtags": "#اختبار_الإنجليزية #تحدي_القواعد #مسابقة_لغوية ❓",
        "structure": "🧠 سؤال واحد مع خيارات\n💡 الجواب الصحيح في التعليقات"
    },
    "IELTS Prep": {
        "hashtags": "#تحضير_آيلتس #نصائح_آيلتس #اختبار_الإنجليزية 🎯",
        "structure": "🎯 نصيحة واحدة عملية\n✍️ مثال توضيحي\n⏱ تلميح لإدارة الوقت"
    },
    "Pronunciation Guide": {
        "hashtags": "#نطق_الإنجليزية #تحدث_بوضوح #تعلم_الإنجليزية 🔈",
        "structure": "🔊 كلمتان مع:\n- النطق العربي\n- مثال\n- تسجيل صوتي في القناة"
    }
}

def get_educational_image():
    """Get a random educational image"""
    return get_pixabay_image_url(random.choice(PIXABAY_KEYWORDS))

def generate_lesson_post():
    """Generate a formatted lesson post"""
    topic = random.choice(LESSON_TOPICS)
    
    # Choose style based on topic type
    if "آيلتس" in topic:
        style_name, style = "IELTS Prep", POST_STYLES["IELTS Prep"]
    elif any(word in topic for word in ["اختبار", "مسابقة", "تحدي", "سؤال"]):
        style_name, style = "Quiz Time", POST_STYLES["Quiz Time"]
    elif any(word in topic for word in ["مفردات", "كلمة", "عبارة", "مرادفات"]):
        style_name, style = "Vocabulary Builder", POST_STYLES["Vocabulary Builder"]
    elif any(word in topic for word in ["نطق", "صوت", "لحن", "تحدث"]):
        style_name, style = "Pronunciation Guide", POST_STYLES["Pronunciation Guide"]
    else:
        style_name, style = "Grammar Focus", POST_STYLES["Grammar Focus"]
    
    prompt = f"""
    أنشئ منشورًا تعليميًا قصيرًا باللغة العربية الفصحى حول:
    {topic}
    
    المتطلبات:
    1. العنوان في السطر الأول مع إيموجي مناسب (بالعربية) دون تحيات أو مقدمات
    2. المحتوى بالعربية الفصحى مع استخدام إيموجي
    3. الهيكل: {style['structure']}
    4. أمثلة قصيرة (الإنجليزية مع الترجمة بالعربية والنطق الإنجليزيةبالعربية)
    5. أضف في نهاية المنشور:
       - "👍 أعجبك المنشور؟ لا تنسى الإعجاب والمشاركة!"
       - "🔔 تابع الصفحة للمزيد من الدروس اليومية"
       - "📢 للدروس المتقدمة، انضم لقناتنا على تلغرام: https://t.me/alleliteenglish"
    6. أنهِ المنشور بهذه الهاشتاقات بالضبط: {style['hashtags']}
    
    ملاحظات:
    - اجعل المحتوى قصيرًا وسهل القراءة (3-5 أسطر كحد أقصى)
    - استخدم لغة تشجيعية تحفز التفاعل
    - أضف سؤالًا تشويقيًا في النهاية لزيادة التفاعل
    - استخدم الإيموجي لجعل المنشور جذابًا
    - التركيز على فائدة واحدة رئيسية بدلاً من شرح مطول
    - اجعل أدلة النطق مناسبة للمبتدئين
    - بالنسبة للاختبارات، أدرج الإجابات مع الشروحات (بالعربية)
    - استخدم الإيموجي لجعل المنشور جذابًا بصريًا
    - اكتب بالعربية الفصحى فقط
    - الأمثلة يجب أن تكون باللغة الإنجليزية مع الترجمة العربية والنطق
    """
    
    response = ask_ai(prompt)
    if response:
        content = clean_ai_output(response)
        
        # Ensure proper hashtags
        lines = content.split('\n')
        main_content = []
        hashtags = []
        
        for line in lines:
            if line.startswith('#'):
                hashtags.extend(line.split())
            else:
                main_content.append(line)
        
        # Use specified hashtags
        final_hashtags = style['hashtags']
        
        # Rebuild content
        formatted_content = '\n'.join(main_content).strip()
        
        # Add engagement prompts if not already present
        engagement_texts = [
            "\n\n👍 أعجبك المنشور؟ لا تنسى الإعجاب والمشاركة!",
            "🔔 تابع الصفحة للمزيد من الدروس اليومية",
            "📢 للدروس المتقدمة، انضم لقناتنا على تلغرام: https://t.me/alleliteenglish"
        ]
        
        for text in engagement_texts:
            if text not in formatted_content:
                formatted_content += '\n' + text
                
        formatted_content += '\n\n' + final_hashtags
        
        return formatted_content, get_educational_image(), topic
    
    return None, None, None

def main():
    print("--- Generating English Learning Post ---")
    post, image, topic = generate_lesson_post()
    
    if post:
        print("\n--- Final Content ---")
        print(post)
        
        if post_to_facebook(post, image):
            print(f"\nPosted successfully: {topic}")
        else:
            print("\nPosting failed")
    else:
        print("Failed to generate content")

if __name__ == "__main__":
    main()