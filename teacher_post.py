import random
import requests
import json
import re
import os
from datetime import datetime

# ===== CONFIGURATION =====
FB_PAGE_TOKEN = os.getenv('FB_PAGE_TOKEN')       # Your Facebook Page Token
FB_PAGE_ID = os.getenv('FB_PAGE_ID')             # Your Facebook Page ID
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')     # Your Gemini API Key
PIXABAY_KEY = os.getenv('PIXABAY_KEY')           # Your Pixabay API Key

# ===== IMAGE KEYWORDS =====
PIXABAY_KEYWORDS = [
    "flowers", "landscape", "mountains", "forest", "ocean",
    "sunset", "animals", "wildlife", "butterfly", "waterfall",
    "garden", "spring", "autumn", "winter", "summer"
]

# ===== LESSON TOPICS =====
LESSON_TOPICS = [
    # Grammar Tips (25 topics)
    "🔍 Present Perfect vs Past Simple - Key Differences",
    "💡 All Conditional Types Explained Simply",
    "🛠️ How to Use Modal Verbs Correctly",
    "🎭 Passive Voice Made Easy",
    "⚠️ Common Article Mistakes and Fixes",
    "📝 Reported Speech - Rules and Examples",
    "🔄 Essential Phrasal Verbs You Need",
    "⏳ Future Tenses Comparison (Will/Going to/Present Continuous)",
    "🔤 Countable vs Uncountable Nouns",
    "🤔 Question Tags - How to Form Them Correctly",
    "📌 Relative Clauses (Who/Which/That/Where)",
    "✨ Gerunds vs Infinitives - Common Verbs",
    "🧩 Prepositions of Time and Place",
    "🆚 Comparative and Superlative Adjectives",
    "🔗 Linking Words for Better Writing",
    "📊 Quantifiers (Some/Any/Much/Many)",
    "🔄 Subject-Verb Agreement Rules",
    "🎯 Demonstratives (This/That/These/Those)",
    "📌 Possessive Forms ('s vs of)",
    "🔄 Word Order in English Questions",
    "⏰ Time Expressions with Different Tenses",
    "🔤 Irregular Plural Nouns",
    "🔄 So vs Such - When to Use Each",
    "🎯 Either/Neither - Correct Usage",
    "📌 Adverbs of Frequency Placement",

    # Vocabulary Tips (25 topics)
    "📚 5 Advanced Academic Words You Need",
    "💼 Essential Business English Phrases",
    "✍️ Must-Know IELTS Vocabulary",
    "🔤 Alternatives to Overused Words",
    "🤝 Common Verb Collocations",
    "🏥 Medical and Health Vocabulary",
    "💻 Technology Terms Everyone Should Know",
    "✈️ Travel and Airport Vocabulary",
    "🍳 Cooking and Kitchen Terms",
    "🛒 Shopping and Money Expressions",
    "🎓 University and Education Terms",
    "⚽ Sports and Fitness Vocabulary",
    "🎨 Art and Culture Related Words",
    "🌳 Environment and Ecology Terms",
    "👔 Job Interview Vocabulary",
    "📱 Social Media and Internet Slang",
    "🏠 House and Furniture Vocabulary",
    "🚗 Car and Driving Terms",
    "👗 Clothing and Fashion Words",
    "🐾 Animal Related Vocabulary",
    "🌦️ Weather Expressions",
    "💑 Relationship and Dating Terms",
    "🎭 Theater and Performance Words",
    "📉 Business and Finance Vocabulary",
    "👶 Baby and Parenting Terms",
    "⚖️ Law and Legal Vocabulary",

    # Pronunciation Focus (15 topics)
    "🗣️ Mastering the TH Sound",
    "🎙️ R vs L Pronunciation Guide",
    "👄 Commonly Mispronounced Words",
    "🔈 Silent Letters in English",
    "📢 Sentence Intonation Rules",
    "👂 Homophones (Same Sound, Different Meaning)",
    "💬 Linking Sounds in Natural Speech",
    "📖 -ED Ending Pronunciation Rules",
    "🔊 V vs W Sound Difference",
    "🗣️ P vs B Pronunciation Tips",
    "🎙️ Schwa Sound - The Most Common Vowel",
    "🔈 Difficult Consonant Clusters"
]

# ===== POSTING STYLES =====
POST_STYLES = {
    "Grammar Tips": {
        "hashtags": "#English_Grammar #Learn_English #English_Tips 🧠",
        "structure": "🎯 Rule Explanation\n💡 Example Sentences\n🔑 Why This Matters\n✨ Practical Tip"
    },
    "Vocabulary Tips": {
        "hashtags": "#English_Vocab #Word_of_the_Day #Learn_English 📖",
        "structure": "🚀 3 Words/Phrases\n📌 Meaning\n💡 Example\n💎 Usage Tip"
    },
    "Pronunciation Guide": {
        "hashtags": "#English_Pronunciation #Speak_English #Learn_English 🗣️",
        "structure": "🔊 Sound/Rule Focus\n💡 Example Words\n🎯 Practice Exercise\n🔈 Pronunciation Tip"
    },
    "Translation Challenge": {
        "hashtags": "#Translation_Challenge #English_Practice #Learn_English 🌟",
        "structure": "📝 نص إنجليزي قصير\n🎯 التحدي: الترجمة إلى العربية\n💡 ممنوع استخدام برامج الترجمة!\n🏆 شارك ترجمتك في التعليقات"
    },
    "Reading Comprehension": {
        "hashtags": "#Reading_Practice #English_Comprehension #Learn_English 📚",
        "structure": "📖 قصة/نص إنجليزي قصير\n❓ 2-3 أسئلة فهم\n💭 اجب في التعليقات"
    }
}

# ===== ENGAGEMENT MESSAGES =====
ENGAGEMENT_MSGS = [
    "💬 شاركنا رأيك في التعليقات!",
    "🌟 اضغط على زر الإعجاب إذا وجدت هذا مفيدًا!",
    "📌 شارك هذا المنشور لمساعدة الآخرين في تعلم الإنجليزية!",
    "🔔 تابع صفحتنا لدروس يومية!"
]

# ===== CORE FUNCTIONS =====
def ask_ai(prompt):
    """Generate content using Gemini 2.5 Flash"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.9,
            "maxOutputTokens": 2048
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"⚠️ Gemini Error: {e}")
        return None

def post_to_facebook(message, image_url=None):
    """Post to Facebook Page"""
    if image_url:
        # Upload image first
        upload_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
        upload_params = {
            'access_token': FB_PAGE_TOKEN,
            'url': image_url,
            'published': 'false'
        }
        try:
            upload_resp = requests.post(upload_url, params=upload_params)
            upload_resp.raise_for_status()
            photo_id = upload_resp.json()['id']
            
            # Create post with image
            post_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
            post_params = {
                'access_token': FB_PAGE_TOKEN,
                'message': message,
                'attached_media': json.dumps([{'media_fbid': photo_id}])
            }
            post_resp = requests.post(post_url, params=post_params)
            post_resp.raise_for_status()
            return True
        except Exception as e:
            print(f"⚠️ Facebook Post Error: {e}")
            return False
    else:
        # Text-only post
        try:
            post_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
            post_params = {
                'access_token': FB_PAGE_TOKEN,
                'message': message
            }
            post_resp = requests.post(post_url, params=post_params)
            post_resp.raise_for_status()
            return True
        except Exception as e:
            print(f"⚠️ Facebook Post Error: {e}")
            return False

def get_pixabay_image_url(keyword):
    """Get random image from Pixabay"""
    try:
        response = requests.get(
            "https://pixabay.com/api/",
            params={
                'key': PIXABAY_KEY,
                'q': keyword,
                'image_type': 'photo',
                'orientation': 'horizontal',
                'per_page': 50,
                'safesearch': 'true'
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return random.choice(data['hits'])['webformatURL'] if data['totalHits'] > 0 else None
    except Exception as e:
        print(f"⚠️ Pixabay Error: {e}")
        return None

def clean_ai_output(text):
    """Clean AI-generated text"""
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'[\*\_]{2,}', '', text)
    return text.strip()

# ===== POST GENERATION FUNCTIONS =====
def get_nature_image():
    """Get a random nature image"""
    return get_pixabay_image_url(random.choice(PIXABAY_KEYWORDS))

def generate_regular_english_post():
    """Generate a regular English learning post"""
    topic = random.choice(LESSON_TOPICS)
    
    # Determine post style
    if any(word in topic for word in ["Grammar", "Verb", "Tense", "Article"]):
        style_name, style = "Grammar Tips", POST_STYLES["Grammar Tips"]
    elif any(word in topic for word in ["Vocab", "Word", "Phrase", "Collocation"]):
        style_name, style = "Vocabulary Tips", POST_STYLES["Vocabulary Tips"]
    else:
        style_name, style = "Pronunciation Guide", POST_STYLES["Pronunciation Guide"]
    
    prompt = f"""
    Create an English learning post in Arabic about:
    {topic}
    
    Requirements:
    1. Arabic title with emoji
    2. Content in Arabic explaining English concepts
    3. Structure: {style['structure']}
    4. For pronunciation posts:
       - Show English words only
       - Add Arabic pronunciation guides in parentheses
    5. Include at the end:
       - "{random.choice(ENGAGEMENT_MSGS)}"
       - "👍 أعجبني وتابعنا لدروس إنجليزية يومية"
       - "🎓 دروس متقدمة على التليجرام: https://t.me/alleliteenglish"
    6. Hashtags: {style['hashtags']}
    
    Important:
    - Never provide pronunciation guides for Arabic words
    - Focus only on English pronunciation
    - Keep explanations simple and practical
    - Use 3-5 emojis per post
    """
    
    response = ask_ai(prompt)
    if response:
        content = clean_ai_output(response)
        
        # Format hashtags properly
        lines = content.split('\n')
        main_content = [line for line in lines if not line.startswith('#')]
        formatted_content = '\n'.join(main_content).strip()
        formatted_content += '\n\n' + style['hashtags']
        
        return formatted_content, get_nature_image(), topic
    
    return None, None, None

def generate_translation_challenge():
    """Generate a translation challenge post"""
    style = POST_STYLES["Translation Challenge"]
    
    prompt = f"""
    Create an English-to-Arabic translation challenge post for Arabic learners of English.
    
    Requirements:
    1. Write a short English paragraph (3-5 sentences) with intermediate-level vocabulary
    2. The paragraph should be interesting and engaging
    3. Challenge users to translate it to Arabic in the comments
    4. Encourage them not to use translator apps
    5. Write the entire post in Arabic with an engaging introduction
    6. Structure: {style['structure']}
    7. Include at the end:
       - "اكتب ترجمتك في التعليقات"
       - "ممنوع استخدام برامج الترجمة الآلية"
       - "👍 أعجبني وتابعنا لتحديات إنجليزية يومية"
    8. Hashtags: {style['hashtags']}
    
    Important:
    - The English text should be clear and well-written
    - Use 3-5 emojis in the post
    - Make it engaging and fun
    - All instructions must be in Arabic
    - Don't promise to feature any translations
    """
    
    response = ask_ai(prompt)
    if response:
        content = clean_ai_output(response)
        
        # Format hashtags properly
        lines = content.split('\n')
        main_content = [line for line in lines if not line.startswith('#')]
        formatted_content = '\n'.join(main_content).strip()
        formatted_content += '\n\n' + style['hashtags']
        
        return formatted_content, get_nature_image(), "Translation Challenge"
    
    return None, None, None

def generate_reading_comprehension():
    """Generate a reading comprehension post"""
    style = POST_STYLES["Reading Comprehension"]
    
    prompt = f"""
    Create a reading comprehension post for Arabic learners of English.
    
    Requirements:
    1. Write a short English story or text (4-6 sentences) with intermediate-level vocabulary
    2. Create 2-3 comprehension questions about the text
    3. Write the entire post in Arabic with an engaging introduction
    4. Structure: {style['structure']}
    5. Include at the end:
       - "💭 اجب عن الأسئلة في التعليقات"
       - "📚 تابعنا لممارسة اللغة الإنجليزية يومياً"
    6. Hashtags: {style['hashtags']}
    
    Important:
    - The English text should be clear and interesting
    - Questions should be directly related to the text
    - Use 3-5 emojis in the post
    - Make it engaging and educational
    - All instructions must be in Arabic
    """
    
    response = ask_ai(prompt)
    if response:
        content = clean_ai_output(response)
        
        # Format hashtags properly
        lines = content.split('\n')
        main_content = [line for line in lines if not line.startswith('#')]
        formatted_content = '\n'.join(main_content).strip()
        formatted_content += '\n\n' + style['hashtags']
        
        return formatted_content, get_nature_image(), "Reading Comprehension"
    
    return None, None, None

def generate_english_post():
    """Randomly select and generate a post type"""
    post_types = [
        generate_regular_english_post,
        generate_translation_challenge,
        generate_reading_comprehension
    ]
    
    # Adjust weights if you want some types to appear more frequently
    weights = [0.10, 0.0, 0.0]  # 60% regular, 20% translation, 20% comprehension
    
    selected_generator = random.choices(post_types, weights=weights, k=1)[0]
    return selected_generator()

# ===== MAIN EXECUTION =====
def main():
    print(f"\n=== English Post Generator [{datetime.now().strftime('%Y-%m-%d %H:%M')}] ===")
    post, image, topic = generate_english_post()
    
    if post:
        print(f"\n=== Generated {topic} Content ===")
        print(post)
        
        if post_to_facebook(post, image):
            print(f"\n✅ Posted successfully: {topic}")
        else:
            print("\n❌ Facebook posting failed")
    else:
        print("\n⚠️ Failed to generate content")

if __name__ == "__main__":
    main()