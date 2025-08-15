import random
from common import ask_ai, post_to_facebook, clean_ai_output, get_pixabay_image_url

# Image Keywords - Changed to nature themes
PIXABAY_KEYWORDS = [
    "flowers", "landscape", "mountains", "forest", "ocean",
    "sunset", "animals", "wildlife", "butterfly", "waterfall",
    "garden", "spring", "autumn", "winter", "summer"
]

# Lesson Topics - Focused on Vocabulary and Grammar tips/tricks
LESSON_TOPICS = [
    # Grammar Tips/Tricks
    "🔍 حيل ذكية لفهم الفرق بين المضارع التام والماضي البسيط",
    "💡 خدعة سريعة لتذكر الجمل الشرطية بأنواعها",
    "🛠️ طريقة سهلة لاستخدام الأفعال الناقصة بشكل صحيح",
    "🎭 كيف تتعرف على المبني للمجهول بسرعة؟",
    "⚠️ تخلص من أخطاء أدوات التعريف والنكرة بهذه الطريقة",

    # Vocabulary Tips/Tricks
    "📚 5 حيل لتذكر المفردات الأكاديمية للأبد",
    "💼 خدعة ذكية لتعلم مفردات الأعمال بسرعة",
    "✍️ طريقة مبتكرة لحفظ مفردات الآيلتس",
    "🔤 كيف تتجنب تكرار الكلمات المستهلكة؟",
    "🤝 خدعة بسيطة لتذكر المتلازمات اللفظية",

    # Memory Techniques
    "🧠 كيف تحفظ القواعد الإنجليزية باستخدام تقنيات الذاكرة",
    "🎯 طريقة الربط لتعلم المفردات بسرعة",
    "🔗 خدعة ربط الكلمات لتذكر المفردات الصعبة",
    "📝 كيف تخلق قصصًا لتذكر القواعد النحوية",
    "💎 تقنية التكرار المتباعد لحفظ المفردات",

    # Practical Application
    "🏆 كيف تطبق القواعد النحوية في الحديث اليومي؟",
    "🚀 طريقة استخدام المفردات الجديدة فور تعلمها",
    "💬 كيف تتحدث بثقة باستخدام القواعد الصحيحة",
    "📖 خدعة قراءة الكتب لتحسين المفردات",
    "🎧 كيف تستخدم الموسيقى لتعلم القواعد والمفردات"
]

# Posting Styles - Updated for tips/tricks format
POST_STYLES = {
    "Grammar Tips": {
        "hashtags": "#نصائح_قواعدية #تعلم_الإنجليزية #قواعد_الإنجليزية 🧠",
        "structure": "🎯 تقديم حيلة/خدعة واحدة\n💡 شرح مبسط مع أمثلة\n🔑 لماذا هذه الطريقة فعالة؟\n✨ نصائح إضافية للتطبيق"
    },
    "Vocabulary Tricks": {
        "hashtags": "#حيل_المفردات #كلمة_اليوم #تعلم_اللغة 🧠",
        "structure": "🚀 تقديم طريقة/خدعة لحفظ المفردات\n📌 3 أمثلة تطبيقية\n💎 كيف تستخدم هذه الطريقة يومياً؟\n🌟 نصائح لتعزيز المفردات"
    },
    "Memory Techniques": {
        "hashtags": "#تقنيات_الحفظ #تعلم_سريع #اللغة_الإنجليزية 🧠",
        "structure": "🧠 تقديم تقنية ذاكرة واحدة\n📝 شرح خطوات التطبيق\n💡 أمثلة واقعية\n🔑 كيف تطبقها في حياتك اليومية؟"
    },
    "Practical Application": {
        "hashtags": "#تطبيق_عملي #الإنجليزية_اليومية #تعلم_لغوي 🛠️",
        "structure": "🏆 تقديم طريقة تطبيقية واحدة\n💬 أمثلة من الحياة الواقعية\n🎯 كيف تدمجها في روتينك؟\n✨ فوائد هذه الطريقة"
    }
}

# Dynamic CTAs in Arabic
CTAS = [
    "💬 شاركنا في التعليقات: ما هي الطريقة التي تستخدمها أنت؟",
    "🌟 هل وجدت هذه الخدعة مفيدة؟ اضغط زر الإعجاب وشاركها مع أصدقائك",
    "🤝 ساعد غيرك في التعلم بمشاركة هذا المنشور",
    "🎯 تابعنا للمزيد من الحيل والنصائح يومياً",
    "📌 جربت هذه الطريقة من قبل؟ أخبرنا عن تجربتك في التعليقات",
    "🔔 متابعينا الأعزاء، لايك للمنشور إذا استفدتم",
    "💡 أعجبك المحتوى؟ شاركه في ستوريزك ليستفيد الجميع"
]

def get_nature_image():
    """Get a random nature image"""
    return get_pixabay_image_url(random.choice(PIXABAY_KEYWORDS))

def generate_tips_post():
    """Generate a formatted tips/tricks post"""
    topic = random.choice(LESSON_TOPICS)
    
    # Choose style based on topic type
    if any(word in topic for word in ["قواعد", "نحوية", "أخطاء"]):
        style_name, style = "Grammar Tips", POST_STYLES["Grammar Tips"]
    elif any(word in topic for word in ["مفردات", "كلمة", "عبارة", "مرادفات"]):
        style_name, style = "Vocabulary Tricks", POST_STYLES["Vocabulary Tricks"]
    elif any(word in topic for word in ["ذاكرة", "حفظ", "تقنية", "ربط"]):
        style_name, style = "Memory Techniques", POST_STYLES["Memory Techniques"]
    else:
        style_name, style = "Practical Application", POST_STYLES["Practical Application"]
    
    prompt = f"""
    أنشئ منشورًا تعليميًا باللغة العربية الفصحى حول:
    {topic}
    
    المتطلبات:
    1. العنوان في السطر الأول مع إيموجي مناسب (بالعربية) دون تحيات أو مقدمات
    2. المحتوى بالعربية الفصحى مع استخدام إيموجي
    3. الهيكل: {style['structure']}
    4. أمثلة تطبيقية (الإنجليزية مع الترجمة والنطق المكتوب بالحروف العربية)
    5. أضف في نهاية المنشور:
       - "{random.choice(CTAS)}"
       - "🔔 تابع الصفحة لتصلك جميع النصائح الجديدة"
       - "📢 انضم لقناتنا على تلغرام لمزيد من الحيل: https://t.me/alleliteenglish"
    6. أنهِ المنشور بهذه الهاشتاقات بالضبط: {style['hashtags']}
    
    ملاحظات:
    - المحتوى مفصل ويمكن أن يكون طويلاً حسب الحاجة
    - ركز على تقديم قيمة حقيقية ونصائح عملية
    - استخدم لغة تشجيعية تحفز التفاعل
    - أضف سؤالاً تشويقياً في النهاية
    - استخدم 3-5 إيموجي في المنشور
    - قدم أمثلة واقعية وتطبيقات عملية
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
        
        return formatted_content, get_nature_image(), topic
    
    return None, None, None

def main():
    print("--- Generating English Learning Tips Post ---")
    post, image, topic = generate_tips_post()
    
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