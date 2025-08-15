import random
from common import ask_ai, post_to_facebook, clean_ai_output, get_pixabay_image_url

# Image Keywords - Nature themes
PIXABAY_KEYWORDS = [
    "flowers", "landscape", "mountains", "forest", "ocean",
    "sunset", "animals", "wildlife", "butterfly", "waterfall",
    "garden", "spring", "autumn", "winter", "summer"
]

# Lesson Topics - Focused on Vocabulary, Grammar, and Pronunciation
LESSON_TOPICS = [
    # Grammar Tips with Pronunciation
    "🔍 الفرق بين المضارع التام والماضي البسيط مع النطق",
    "💡 الجمل الشرطية بأنواعها مع النطق الصحيح",
    "🛠️ استخدامات الأفعال الناقصة مع الأمثلة المنطوقة",
    "🎭 المبني للمجهول وكيفية نطقه",
    "⚠️ أخطاء شائعة في أدوات التعريف والنكرة مع التصحيح",

    # Vocabulary Tips with Pronunciation
    "📚 مفردات أكاديمية مهمة مع النطق العربي",
    "💼 عبارات إنجليزية للأعمال مع طريقة اللفظ",
    "✍️ كلمات الآيلتس الأساسية مع النطق",
    "🔤 مرادفات متقدمة مع اللفظ الصحيح",
    "🤝 متلازمات لفظية شائعة مع النطق",

    # Pronunciation Focus
    "🔊 أصعب الأصوات الإنجليزية للناطقين بالعربية",
    "🗣️ نطق حرف الـ TH بثلاث طرق مختلفة",
    "🎙️ الفرق بين R و L في النطق الإنجليزي",
    "👄 كلمات ينطقها العرب خطأً بشكل شائع",
    "🔈 نطق الحروف الصامتة في الإنجليزية"
]

# Posting Styles
POST_STYLES = {
    "Grammar Tips": {
        "hashtags": "#نصائح_قواعدية #تعلم_الإنجليزية #النطق_الصحيح 🧠",
        "structure": "🎯 تقديم قاعدة مع شرح مختصر\n💡 مثال إنجليزي مع:\n- الترجمة العربية\n- النطق بالحروف العربية\n🔑 لماذا هذه القاعدة مهمة؟"
    },
    "Vocabulary Tips": {
        "hashtags": "#مفردات_إنجليزية #كلمة_اليوم #النطق_الصحيح 📖",
        "structure": "🚀 تقديم 3 كلمات/عبارات مع:\n- المعنى\n- مثال\n- النطق بالحروف العربية\n💎 كيف تستخدمها في المحادثة؟"
    },
    "Pronunciation Guide": {
        "hashtags": "#النطق_الصحيح #إنجليزية #تعلم_اللغة 🗣️",
        "structure": "🔊 تقديم صوت/قاعدة نطق\n💡 كلمات توضيحية مع:\n- النطق بالحروف العربية\n- الفرق بين النطق الصحيح والخاطئ\n🎯 تمارين تطبيقية"
    }
}

# Dynamic CTAs in Arabic
CTAS = [
    "💬 جرب نطق الكلمات في التعليقات وسنساعدك في التصحيح!",
    "🌟 هل استفدت من درس النطق اليوم؟ لا تنسى الإعجاب والمشاركة",
    "🗣️ شاركنا الكلمات التي تجد صعوبة في نطقها",
    "🔔 تابعنا لمزيد من دروس النطق اليومية",
    "🎧 استمع للفظ الصحيح على قناتنا في التلغرام"
]

def get_nature_image():
    """Get a random nature image"""
    return get_pixabay_image_url(random.choice(PIXABAY_KEYWORDS))

def generate_pronunciation_post():
    """Generate a post with Arabic pronunciation guides"""
    topic = random.choice(LESSON_TOPICS)
    
    # Choose style based on topic
    if "نطق" in topic or "لفظ" in topic:
        style_name, style = "Pronunciation Guide", POST_STYLES["Pronunciation Guide"]
    elif any(word in topic for word in ["مفردات", "كلمة", "عبارة"]):
        style_name, style = "Vocabulary Tips", POST_STYLES["Vocabulary Tips"]
    else:
        style_name, style = "Grammar Tips", POST_STYLES["Grammar Tips"]
    
    prompt = f"""
    أنشئ منشورًا تعليميًا باللغة العربية حول:
    {topic}
    
    المتطلبات:
    1. العنوان في السطر الأول مع إيموجي
    2. المحتوى بالعربية مع إيموجي
    3. الهيكل: {style['structure']}
    4. لكل مثال إنجليزي:
       - اكتبه بالإنجليزية
       - اكتب ترجمته العربية
       - اكتب نطقه بالحروف العربية بين قوسين
    5. أكتب في نهاية المنشور:
       - "{random.choice(CTAS)}"
       - "🔔 تابعنا لمزيد من الدروس"
       - "🎧 استمع للنطق الصحيح على تلغرام: https://t.me/englishpronunciation"
    6. الهاشتاقات: {style['hashtags']}
    
    مثال:
    كلمة: Schedule
    الترجمة: جدول
    النطق: (سكِدْيُول) للهجة البريطانية / (سكِدْوَل) للأمريكية
    """
    
    response = ask_ai(prompt)
    if response:
        content = clean_ai_output(response)
        
        # Format hashtags properly
        lines = content.split('\n')
        main_content = []
        final_hashtags = style['hashtags']
        
        for line in lines:
            if not line.startswith('#'):
                main_content.append(line)
        
        formatted_content = '\n'.join(main_content).strip()
        formatted_content += '\n\n' + final_hashtags
        
        return formatted_content, get_nature_image(), topic
    
    return None, None, None

def main():
    print("--- Generating English Pronunciation Post ---")
    post, image, topic = generate_pronunciation_post()
    
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