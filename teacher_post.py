import random
from common import ask_ai, post_to_facebook, clean_ai_output, get_pixabay_image_url

# Image Keywords by Level
PIXABAY_KEYWORDS = {
    "مبتدئ": ["alphabet", "numbers", "school", "family", "colors"],
    "متوسط": ["grammar", "writing", "teaching", "college", "teacher"],
    "متقدم": ["literature", "science", "students", "college", "academic"]
}

# Lesson Topics (75 topics - 25 per level)
LESSON_TOPICS = {
    "مبتدئ": [
        "الأبجدية الإنجليزية",
        "الأرقام من 1 إلى 100",
        "أيام الأسبوع والشهور",
        "أفراد العائلة",
        "المهن الأساسية",
        "أجزاء الجسم",
        "الألوان الأساسية",
        "الأطعمة والمشروبات",
        "أدوات المدرسة",
        "الحيوانات الشائعة",
        "المفرد والمجموع",
        "أدوات التعريف (a, an, the)",
        "ضمائر الملكية",
        "أفعال الحركة الأساسية",
        "الصفات الوصفية البسيطة",
        "أدوات الاستفهام الأساسية",
        "التعابير اليومية البسيطة",
        "أسماء الدول والجنسيات",
        "أوقات اليوم والفصول",
        "المباني والأماكن العامة",
        "الملابس والأزياء",
        "الأمر والنهي البسيط",
        "حالات الطقس",
        "الأدوات المنزلية",
        "الهوايات والأنشطة"
    ],
    "متوسط": [
        "زمن المضارع المستمر",
        "زمن الماضي البسيط",
        "المقارنة والتفضيل",
        "الأفعال الناقصة (can, should, must)",
        "حروف الجر المكانية",
        "أدوات الربط الأساسية",
        "السؤال باستخدام wh-",
        "الأفعال الشاذة في الماضي",
        "صيغة الأمر",
        "المستقبل (will/going to)",
        "المعدود وغير المعدود",
        "أدوات النفي",
        "مفردات السفر",
        "التعبير عن الوقت والتاريخ",
        "الصفات المقارنة",
        "المفعول به المباشر وغير المباشر",
        "أفعال الكينونة (be, have, do)",
        "الجملة الشرطية الأولى",
        "الضمائر الانعكاسية",
        "المصدر واستخداماته",
        "الظروف الزمانية والمكانية",
        "صيغ التفضيل",
        "التعبير عن الأسباب والنتائج",
        "المفردات الإدارية",
        "الاختصارات الشائعة"
    ],
    "متقدم": [
        "زمن المضارع التام",
        "المبني للمجهول",
        "الجمل الشرطية بأنواعها",
        "الأسلوب غير المباشر",
        "أزمنة المضارع التام المستمر",
        "الصفات المشتقة",
        "التعبيرات الاصطلاحية",
        "الاختلافات بين الإنجليزية البريطانية والأمريكية",
        "لغة الأعمال الرسمية",
        "كتابة الرسائل الإلكترونية",
        "المجاز والكناية",
        "تحليل النصوص الأدبية",
        "الانزياحات الدلالية",
        "حذف حروف الجر في السياقات المختلفة",
        "الجمل المعقدة والتركيب النحوي",
        "الترادف والتضاد",
        "الانزياحات النحوية",
        "الانزياحات الصوتية",
        "اللغة الإعلامية",
        "اللغة العلمية",
        "اللغة التقنية",
        "اللغة القانونية",
        "اللغة الطبية",
        "اللغة الأكاديمية",
        "الترجمة الفورية"
    ]
}

# Posting Styles
POST_STYLES = {
    "أكاديمي": {
        "hashtags": "#قواعد_الإنجليزية #تعلم_اللغة #دروس",
        "structure": "3 نقاط رئيسية مع شرح لكل نقطة"
    },
    "عملي": {
        "hashtags": "#الإنجليزية_العملية #ممارسة #تطبيق",
        "structure": "نقطتان رئيسيتان مع أمثلة تطبيقية" 
    },
    "تفاعلي": {
        "hashtags": "#اسأل_ونجاوب #تفاعل #تعلم_اللغة",
        "structure": "شرح موجز مع أسئلة تفاعلية"
    }
}

def get_educational_image(level):
    """Get a random educational image for the specified level"""
    return get_pixabay_image_url(random.choice(PIXABAY_KEYWORDS[level]))

def generate_lesson_post():
    """Generate a formatted lesson post"""
    level = random.choice(list(LESSON_TOPICS.keys()))
    topic = random.choice(LESSON_TOPICS[level])
    style_name, style = random.choice(list(POST_STYLES.items()))
    
    prompt = f"""
    اكتب منشورًا تعليميًا عن:
    {topic}
    
    المتطلبات:
    1. ابدأ بالعنوان فقط في السطر الأول
    2. المحتوى بالعربية الفصحى الرسمية
    3. الهيكل: {style['structure']}
    4. استخدم ترقيمًا واضحًا للفقرات
    5. أضف أمثلة عملية عند الحاجة
    6. اختم بـ 3 هاشتاقات فقط: {style['hashtags']}
    7. لا تترك أسطرًا فارغة بين الهاشتاقات
    
    ملاحظات:
    - استخدم لغة واضحة وسهلة
    - تجنب العبارات الطويلة المعقدة
    - تأكد من صحة المعلومات
    """
    
    response = ask_ai(prompt)
    if response:
        # Clean and format the content
        content = clean_ai_output(response)
        
        # Ensure exactly 3 hashtags
        lines = content.split('\n')
        main_content = []
        hashtags = []
        
        for line in lines:
            if line.startswith('#'):
                hashtags.extend(line.split())
            else:
                main_content.append(line)
        
        # Use the first 3 hashtags found or default to style's hashtags
        final_hashtags = ' '.join(hashtags[:3]) if hashtags else style['hashtags']
        
        # Rebuild content with proper spacing
        formatted_content = '\n'.join(main_content).strip()
        formatted_content += '\n\n' + final_hashtags
        
        return formatted_content, get_educational_image(level), topic
    
    return None, None, None

def main():
    print("--- بدء إنشاء المنشور التعليمي ---")
    post, image, topic = generate_lesson_post()
    
    if post:
        print("\n--- المحتوى النهائي ---")
        print(post)
        
        if post_to_facebook(post, image):
            print(f"\nتم النشر بنجاح: {topic}")
        else:
            print("\nفشل في النشر")
    else:
        print("فشل في إنشاء المحتوى")

if __name__ == "__main__":
    main()