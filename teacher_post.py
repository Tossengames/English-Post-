import random
from common import ask_ai, post_to_facebook, clean_ai_output, get_pixabay_image_url

# Image Keywords
PIXABAY_KEYWORDS = ["email", "writing", "office", "communication", "business"]

# Lesson Topics
LESSON_TOPICS = [
    "كتابة الرسائل الإلكترونية الرسمية",
    "فن كتابة الرسائل التجارية",
    "إتيكيت المراسلات الإلكترونية",
    "الفرق بين الرسائل الرسمية وغير الرسمية",
    "كيف تكتب رسالة احترافية",
    "الأخطاء الشائعة في كتابة الرسائل"
]

# Posting Styles
POST_STYLES = {
    "detailed": {
        "hashtags": "#كتابة_رسائل #البريد_الإلكتروني #مهارات_التواصل",
        "structure": "3 نقاط رئيسية مع شرح لكل نقطة"
    },
    "examples": {
        "hashtags": "#أمثلة_عملية #تعلم_المراسلة #نموذج_رسالة", 
        "structure": "نقطتان رئيسيتان مع أمثلة تطبيقية"
    }
}

def generate_email_writing_post():
    """Generate a formatted post about email writing"""
    topic = random.choice(LESSON_TOPICS)
    style = random.choice(list(POST_STYLES.values()))
    
    prompt = f"""
    اكتب منشورًا تعليميًا عن:
    {topic}
    
    المتطلبات:
    1. ابدأ بعنوان واضح في الأعلى
    2. المحتوى باللغة العربية الفصحى فقط
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
        # Ensure clean formatting
        content = clean_ai_output(response)
        lines = content.split('\n')
        
        # Remove any extra hashtags beyond the 3 specified
        main_content = []
        hashtags = []
        for line in lines:
            if line.startswith('#'):
                hashtags.extend(line.split())
            else:
                main_content.append(line)
        
        # Use only the first 3 hashtags
        final_hashtags = ' '.join(hashtags[:3]) if hashtags else style['hashtags']
        
        # Rebuild content with proper spacing
        formatted_content = '\n'.join(main_content).strip()
        formatted_content += '\n\n' + final_hashtags
        
        return formatted_content, get_pixabay_image_url(random.choice(PIXABAY_KEYWORDS))
    
    return None, None

def main():
    print("--- Generating Email Writing Post ---")
    post, image = generate_email_writing_post()
    
    if post:
        print("\n--- Formatted Post ---")
        print(post)
        
        if post_to_facebook(post, image):
            print("\nPost published successfully!")
        else:
            print("\nFailed to publish post")
    else:
        print("Failed to generate content")

if __name__ == "__main__":
    main()