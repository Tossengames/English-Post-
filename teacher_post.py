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
    "🔗 حروف الجر في الأفعال المركبة - دليل شامل",
    "🔄 المصدر والتصريف الثالث - متى نستخدم كل منهما",
    "🗣️ الكلام المنقول مع أمثلة توضيحية",
    "✂️ تقليل الجمل الوصفية - تقنيات عملية",
    "📜 قلب ترتيب الجمل في الإنجليزية الرسمية",
    
    # Vocabulary Topics
    "📚 مفردات أكاديمية لكتابة مقالات عالية المستوى",
    "💼 عبارات إنجليزية الأعمال للمحترفين",
    "✍️ تعزيز مفردات كتابة الآيلتس",
    "🔤 مرادفات للكلمات المستهلكة - تطوير مفرداتك",
    "🤝 المتلازمات اللفظية مع الأفعال الشائعة",
    "🎩 المفردات الرسمية وغير الرسمية - حسب السياق",
    "🌐 التعابير الاصطلاحية للكتابة الأكاديمية",
    "💬 الأفعال المركبة في سياقات الأعمال",
    "🧩 البادئات واللواحق لتكوين الكلمات",
    "🚫 الكلمات الخادعة في الإنجليزية",
    
    # Pronunciation Topics
    "🔊 الكلمات التي تُنطق خطأً بشكل شائع",
    "🎙️ الحروف الصامتة في الإنجليزية - دليل شامل",
    "🗣️ الأصوات الصعبة للناطقين بغير الإنجليزية",
    "👄 تويستات اللسان لتحسين النطق",
    "🎵 أنماط التشديد في الكلمات الإنجليزية",
    "🇺🇸🇬🇧 الفروق بين النطق الأمريكي والبريطاني",
    "📢 الكلمات المتشابهة نطقاً المختلفة معنى",
    "🎤 النطق لاختبار الآيلتس الشفوي",
    "👂 تمارين الأزواج الصوتية لتدريب الأذن",
    "💬 الكلام المتصل في المحادثة الطبيعية",
    
    # Question/Quiz Topics
    "❓ أخطاء قواعدية شائعة - هل تستطيع تمييزها؟",
    "🔎 اكتشف الخطأ - نسخة متقدمة",
    "🔄 تحويل الجمل - تحدٍ لغوي",
    "📝 تمارين ترتيب الكلمات - رتبها بشكل صحيح",
    "⏳ اختبار زمن الفعل الصحيح - مسابقة زمنية",
    "📖 ملء الفراغات بمفردات أكاديمية",
    "✅ أي جملة صحيحة؟ اختبار قواعدي",
    "✏️ إعادة صياغة الجمل - مهارة أساسية",
    "✂️ تصحيح الأخطاء - اكتشف كل الأخطاء",
    "🏆 مسابقة القواعد - اختبر معلوماتك",
    
    # IELTS Practice
    "🎤 الجزء الأول من اختبار الآيلتس الشفوي - نماذج إجابات",
    "✍️ مهمة الكتابة الأولى في الآيلتس - هيكل الدرجة 9",
    "👂 قسم الاستماع في الآيلتس - استراتيجيات مجربة",
    "📚 قسم القراءة في الآيلتس - نصائح إدارة الوقت",
    "📊 معايير التقييم في اختبار الآيلتس الشفوي",
    "🖋️ مهمة الكتابة الثانية في الآيلتس - أنواع المقالات",
    "💯 تقنيات مقابلة الآيلتس لتحقيق درجات عالية",
    "📈 مفردات الآيلتس للوصول لدرجة 7+",
    "🗣️ نصائح نطق لخطاب واضح في الآيلتس",
    "⏱️ إدارة الوقت في يوم الاختبار"
]

# Posting Styles
POST_STYLES = {
    "Grammar Focus": {
        "hashtags": "#قواعد_الإنجليزية #تعلم_الإنجليزية #الإنجليزية 📚",
        "structure": "📝 شرح القاعدة مع 3 أمثلة\n💡 سؤال تطبيقي\n🔍 الإجابة مع الشرح"
    },
    "Vocabulary Builder": {
        "hashtags": "#مفردات_الإنجليزية #كلمة_اليوم #تعلم_اللغة 📖", 
        "structure": "✨ 5 كلمات/عبارات مفيدة\n📖 التعريفات والأمثلة\n💬 جمل تطبيقية"
    },
    "Quiz Time": {
        "hashtags": "#اختبار_الإنجليزية #تحدي_القواعد #مسابقة_لغوية ❓",
        "structure": "🧠 اختبار من 5 أسئلة\n⏳ 30 ثانية لكل سؤال\n✅ الإجابات مع الشرح"
    },
    "IELTS Prep": {
        "hashtags": "#تحضير_آيلتس #نصائح_آيلتس #اختبار_الإنجليزية 🎯",
        "structure": "📊 نصائح عملية\n✍️ نماذج أسئلة\n💡 نصائح خبراء"
    },
    "Pronunciation Guide": {
        "hashtags": "#نطق_الإنجليزية #تحدث_بوضوح #تعلم_الإنجليزية 🔈",
        "structure": "🔊 قائمة كلمات مع دليل نطق مبسط\n👄 أمثلة للتدريب\n🎙️ جمل للممارسة"
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
    أنشئ منشورًا تعليميًا باللغة العربية الفصحى حول:
    {topic}
    
    المتطلبات:
    1. العنوان في السطر الأول مع إيموجي مناسب (بالعربية) دون تحيات أو مقدمات
    2. المحتوى بالعربية الفصحى مع استخدام إيموجي
    3. الهيكل: {style['structure']}
    4. تضمين أمثلة عملية (باللغة الإنجليزية مع الترجمة العربية)
    5. بالنسبة للنطق:
       - استخدم دليل نطق مبسط بالعربية
       - أضف "تنطق مثل" عندما يكون ذلك مفيدًا
    6. أنهِ المنشور بهذه الهاشتاقات بالضبط: {style['hashtags']}
    
    ملاحظات:
    - اجعل الشروحات مختصرة ولكن شاملة (بالعربية)
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