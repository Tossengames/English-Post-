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
    "learning", "education", "books", "study", "classroom",
    "language", "writing", "reading", "students", "teacher",
    "notebook", "pen", "laptop", "online", "school",
    "university", "college", "library", "campus", "graduation"
]

# ===== ENGLISH TEACHING TOPICS FOR SCHOOL & COLLEGE STUDENTS =====
LESSON_TOPICS = [
    # 📚 GRAMMAR ESSENTIALS (20 topics)
    "📝 Present Perfect vs Past Simple",
    "🔍 All English Tenses Overview",
    "🎯 Modal Verbs: Can, Could, Should, Must",
    "📖 Passive Voice in Academic Writing",
    "⚠️ Common Article Mistakes (a/an/the)",
    "🔄 Reported Speech for School Essays",
    "💬 Phrasal Verbs for Daily Conversation",
    "⏳ Future Forms: Will vs Going to",
    "🔤 Countable & Uncountable Nouns",
    "❓ Question Formation Techniques",
    "📌 Relative Clauses: Who, Which, That",
    "✨ Gerunds and Infinitives",
    "🧩 Prepositions of Time and Place",
    "📊 Comparative & Superlative Forms",
    "🔗 Linking Words for Better Writing",
    "📈 Subject-Verb Agreement Rules",
    "🎓 Conditional Sentences",
    "📋 Word Order in English Sentences",
    "🔍 Direct vs Indirect Questions",
    "📖 Adjective Word Order",

    # 🗣️ SPEAKING & PRONUNCIATION (15 topics)
    "🎤 English Pronunciation Basics",
    "🔊 TH Sound Practice",
    "🗣️ Intonation Patterns",
    "💬 Common Speaking Mistakes",
    "🎯 Fluency Building Exercises",
    "📢 Public Speaking Tips",
    "👂 Listening Comprehension",
    "🔈 Word Stress Rules",
    "🎙️ Connected Speech",
    "📝 Tongue Twisters Practice",
    "💡 Conversation Starters",
    "🎭 Role-Play Scenarios",
    "📞 Telephone English",
    "🤝 Social English Phrases",
    "🎓 Academic Presentations",

    # 📖 WRITING SKILLS (15 topics)
    "✍️ Paragraph Structure",
    "📝 Essay Writing Basics",
    "🎯 Thesis Statement Writing",
    "📋 Formal vs Informal Writing",
    "🔍 Punctuation Rules",
    "📖 Sentence Variety",
    "💡 Writing Strong Conclusions",
    "📊 Descriptive Writing",
    "🎯 Argumentative Essays",
    "📝 Letter Writing Format",
    "🔍 Proofreading Techniques",
    "📖 Summary Writing",
    "🎓 Research Paper Basics",
    "📋 Note-Taking Methods",
    "✍️ Creative Writing Tips",

    # 📚 ACADEMIC ENGLISH (15 topics)
    "🎓 University Lecture Comprehension",
    "📖 Academic Vocabulary Building",
    "📝 Exam Writing Strategies",
    "⏰ Time Management for Exams",
    "🔍 Reading Comprehension Tips",
    "📋 Note-Making in Lectures",
    "🎯 Seminar Participation",
    "📖 Textbook Study Methods",
    "📝 Assignment Writing",
    "🔍 Critical Reading Skills",
    "📊 Graph Description Language",
    "🎓 Group Discussion English",
    "📖 Literature Analysis Terms",
    "📝 Research Methodology Language",
    "🎯 Academic Presentations",

    # 💼 PRACTICAL ENGLISH (15 topics)
    "📧 Email Writing Etiquette",
    "💼 Job Interview English",
    "📋 CV and Resume Writing",
    "🤝 Business Meeting Phrases",
    "📞 Customer Service English",
    "🎯 Small Talk Strategies",
    "📝 Formal Letter Writing",
    "💬 Social Situations Vocabulary",
    "📋 Application Forms",
    "🎓 College Application Essays",
    "📖 Understanding Instructions",
    "🔍 Following Directions",
    "📝 Note-Taking in Meetings",
    "💡 Problem-Solving Language",
    "🎯 Giving Opinions Politely"
]

# ===== POSTING STYLES =====
POST_STYLES = {
    "Grammar Tips": {
        "hashtags": "#EnglishGrammar #LearnEnglish #GrammarTips",
        "structure": "🎯 Rule Explanation\n💡 Example Sentences\n🔑 Quick Tip"
    },
    "Speaking Practice": {
        "hashtags": "#SpeakingEnglish #EnglishPractice #Pronunciation",
        "structure": "🗣️ Practice Point\n💬 Example Dialogue\n🎯 Your Turn"
    },
    "Writing Skills": {
        "hashtags": "#WritingSkills #EnglishWriting #AcademicEnglish",
        "structure": "✍️ Writing Tip\n📝 Example\n🔍 Key Point"
    },
    "Vocabulary Building": {
        "hashtags": "#EnglishVocabulary #WordPower #LearnWords",
        "structure": "📚 3 Useful Words\n📖 Meaning & Examples\n💡 Practice Tip"
    },
    "Study Tips": {
        "hashtags": "#StudyTips #EnglishLearning #StudentLife",
        "structure": "🎓 Study Strategy\n💡 How to Use It\n📚 Practice Idea"
    }
}

# ===== ENGAGEMENT MESSAGES =====
ENGAGEMENT_MSGS = [
    "💬 Practice this in the comments below!",
    "📝 Write your own example sentence!",
    "🎯 Try using this in your next conversation!",
    "📚 Share your study tips with us!"
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
            "maxOutputTokens": 1024  # Shorter posts
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=90)
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
def get_education_image():
    """Get a random education-related image"""
    return get_pixabay_image_url(random.choice(PIXABAY_KEYWORDS))

def generate_english_lesson_post():
    """Generate a short English lesson post"""
    topic = random.choice(LESSON_TOPICS)
    
    # Determine post style based on topic
    if any(word in topic for word in ["Grammar", "Tense", "Verb", "Sentence"]):
        style_name, style = "Grammar Tips", POST_STYLES["Grammar Tips"]
    elif any(word in topic for word in ["Speaking", "Pronunciation", "Conversation"]):
        style_name, style = "Speaking Practice", POST_STYLES["Speaking Practice"]
    elif any(word in topic for word in ["Writing", "Essay", "Paragraph"]):
        style_name, style = "Writing Skills", POST_STYLES["Writing Skills"]
    elif any(word in topic for word in ["Vocabulary", "Words", "Terms"]):
        style_name, style = "Vocabulary Building", POST_STYLES["Vocabulary Building"]
    else:
        style_name, style = "Study Tips", POST_STYLES["Study Tips"]
    
    prompt = f"""
    Create a SHORT English teaching post for school and college students about:
    {topic}
    
    Requirements:
    1. Keep it very brief and practical (3-4 lines maximum)
    2. Structure: {style['structure']}
    3. Include ONE call-to-action within the content (not at the end)
    4. Use simple, clear English
    5. Add 1-2 relevant emojis
    6. Make it feel like a teacher sharing a quick tip
    
    Example format:
    🎯 Present Perfect for recent experiences
    💡 "I have just finished my homework"
    🔑 Use with 'just', 'already', 'yet'
    💬 Try: Write about something you've done today!
    
    Important:
    - Maximum 4 lines total
    - Include engagement within the content
    - No long explanations
    - Focus on one specific point
    - Use student-friendly language
    """
    
    response = ask_ai(prompt)
    if response:
        content = clean_ai_output(response)
        
        # Format the post
        lines = content.split('\n')
        main_content = [line for line in lines if not line.startswith('#')]
        formatted_content = '\n'.join(main_content).strip()
        
        # Add hashtags
        formatted_content += '\n\n' + style['hashtags']
        
        return formatted_content, get_education_image(), topic
    
    return None, None, None

# ===== MAIN EXECUTION =====
def main():
    print(f"\n=== English Lesson Post Generator [{datetime.now().strftime('%Y-%m-%d %H:%M')}] ===")
    post, image, topic = generate_english_lesson_post()
    
    if post:
        print(f"\n=== Generated Lesson: {topic} ===")
        print(post)
        
        if post_to_facebook(post, image):
            print(f"\n✅ Posted successfully: {topic}")
        else:
            print("\n❌ Facebook posting failed")
    else:
        print("\n⚠️ Failed to generate content")

if __name__ == "__main__":
    main()