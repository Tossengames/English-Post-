import random
from common import ask_ai, post_to_facebook, clean_ai_output, get_pixabay_image_url

# Image Keywords
PIXABAY_KEYWORDS = ["grammar", "language", "education", "writing", "books"]

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

# Posting Styles with Fixed Hashtags
POST_STYLES = {
    "أكاديمي": "#قواعد_الإنجليزية #تعلم_اللغة #دروس",
    "عملي": "#الإنجليزية_العملية #ممارسة #تطبيق",
    "تفاعلي": "#اسأل_ونجاوب #تفاعل #تعلم_اللغة"
}

# Call-to-Action Phrases
CTAS = [
    "ما رأيك في هذه الأمثلة؟ هل لديك إضافات؟",
    "جرب تكوين جملة باستخدام هذه القاعدة!",
    "ما الجانب الذي تريد توضيحه أكثر؟"
]

def get_educational_image():
    """Get a random educational image from Pixabay"""
    return get_pixabay_image_url(random.choice(PIXABAY_KEYWORDS))

def clean_hashtags(content, default_hashtags):
    """Ensure exactly 3 hashtags at the end"""
    lines = content.split('\n')
    
    # Separate content lines from hashtag lines
    content_lines = []
    hashtag_lines = []
    
    for line in lines:
        if line.startswith('#'):
            hashtag_lines.extend(line.split())
        else:
            content_lines.append(line)
    
    # Use found hashtags or default ones
    final_hashtags = ' '.join(hashtag_lines[:3]) if hashtag_lines else default_hashtags
    
    # Rebuild content
    cleaned_content = '\n'.join(content_lines).strip()
    return f"{cleaned_content}\n{final_hashtags}"

def generate_post():
    """Generate a lesson post with fixed format"""
    level = random.choice(list(LESSON_TOPICS.keys()))
    topic = random.choice(LESSON_TOPICS[level])
    style_name, hashtags = random.choice(list(POST_STYLES.items()))
    cta = random.choice(CTAS)
    
    prompt = f"""
    اكتب شرحًا تعليميًا بالعربية الفصحى حسب المواصفات التالية:
    
    الموضوع: {topic}
    
    المتطلبات:
    1. ابدأ مباشرة بالشرح دون مقدمات أو عناوين فرعية
    2. قدم 3 نقاط رئيسية واضحة
    3. أضف مثالين تطبيقيين
    4. اختم بدعوة للتفاعل: {cta}
    5. أضف 3 هاشتاقات فقط في السطر الأخير
    
    ملاحظات:
    - استخدم لغة عربية فصحى واضحة
    - تجنب أي إشارة للذكاء الاصطناعي
    - لا تترك أسطرًا فارغة بين الهاشتاقات
    """
    
    response = ask_ai(prompt)
    if response:
        # Clean and standardize the output
        cleaned_content = clean_ai_output(response)
        standardized_content = clean_hashtags(cleaned_content, hashtags)
        return standardized_content, get_educational_image(), topic
    return None, None, None

def main():
    """Main execution function"""
    print("--- بدء إنشاء المنشور التعليمي ---")
    post_content, image_url, topic = generate_post()
    
    if post_content:
        print("\n--- المحتوى النهائي ---")
        print(post_content)
        print("\n---")
        
        if post_to_facebook(post_content, image_url):
            print(f"تم النشر بنجاح: {topic}")
        else:
            print("فشل في النشر")
    else:
        print("فشل في إنشاء المحتوى")

if __name__ == "__main__":
    main()