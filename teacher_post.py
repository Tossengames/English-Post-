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
    # College Academic English (30 topics)
    "🎓 Academic Essay Structure - Introduction/Body/Conclusion",
    "📚 Research Paper Vocabulary - Key Terms for University",
    "💡 Thesis Statement Development - Master Your Argument",
    "🔍 Critical Analysis Phrases - Academic Discussion",
    "📝 Literature Review Language - Synthesizing Sources",
    "⚡ Avoiding Plagiarism - Paraphrasing Techniques",
    "📊 Data Analysis Terms - Presenting Research Findings",
    "🎯 Academic Presentations - Language for Public Speaking",
    "🤔 Debate and Discussion Phrases - Classroom Participation",
    "📖 Scholarly Article Comprehension - Reading Strategies",
    "✍️ Academic Email Writing - Professional Communication",
    "🔬 STEM Vocabulary - Science and Technology Terms",
    "📈 Business Case Study Language - Analysis Frameworks",
    "🌍 Global Issues Terminology - Current Events Vocabulary",
    "⚖️ Legal Studies Vocabulary - Law and Justice Terms",
    "🏛️ Political Science Terms - Government and Policy",
    "💼 Internship Application Language - Professional Requests",
    "📋 Lab Report Writing - Scientific Method Documentation",
    "🎨 Arts and Humanities Vocabulary - Critical Theory Terms",
    "💰 Economics Terminology - Market and Financial Language",
    "👥 Group Project Communication - Collaborative Language",
    "📆 Time Management Vocabulary - Academic Planning",
    "🎤 Conference Presentation Skills - Academic Events",
    "📝 Note-taking Strategies - Lecture Comprehension",
    "🔎 Source Evaluation Language - Credibility Assessment",
    "📚 Textbook Reading Techniques - Efficient Study Methods",
    "💬 Classroom Interaction Phrases - Active Participation",
    "📋 Exam Preparation Vocabulary - Test Strategies",
    "🎯 Peer Review Language - Constructive Feedback",
    "📖 Academic Reading Speed - Comprehension Techniques",

    # High School English Essentials (30 topics)
    "📖 Book Report Language - Analyzing Literature",
    "✏️ Essay Writing Basics - High School Structure",
    "🔤 Vocabulary Building - Word Roots and Prefixes",
    "📝 Creative Writing Prompts - Story Development",
    "🎭 Shakespearean Language - Modern Translations",
    "📚 Novel Analysis Terms - Character and Plot",
    "⚡ Poetry Analysis - Figurative Language",
    "📋 Study Skills Vocabulary - Effective Learning",
    "🎯 Grammar for Essays - Common Mistakes to Avoid",
    "💬 Classroom Presentation Skills - Confidence Building",
    "📊 Compare and Contrast Language - Analytical Writing",
    "🔍 Reading Comprehension Strategies - Test Taking",
    "📝 Persuasive Writing Techniques - Argument Development",
    "🎓 College Application Essays - Personal Statements",
    "📖 Literary Devices - Metaphor, Simile, Symbolism",
    "⚡ Sentence Variety - Improving Writing Style",
    "📚 Short Story Analysis - Elements of Fiction",
    "💡 Critical Thinking Vocabulary - Analysis Terms",
    "🎤 Speech and Debate Terms - Formal Speaking",
    "📝 Research Project Basics - Source Integration",
    "🔤 Spelling Rules - Common Patterns and Exceptions",
    "📖 Reading Fluency - Pace and Expression",
    "🎯 Test-taking Strategies - Multiple Choice Skills",
    "📝 Paragraph Development - Topic Sentences",
    "💬 Discussion Leadership - Facilitating Conversations",
    "📚 Genre Study Vocabulary - Fiction vs Nonfiction",
    "⚡ Vocabulary in Context - Guessing Meaning",
    "🎓 Scholarship Essay Writing - Winning Applications",
    "📝 Editing and Proofreading - Error Detection",
    "🔍 Text Evidence - Supporting Arguments",

    # University Survival English (25 topics)
    "🏠 Dorm Life Vocabulary - Campus Living Terms",
    "🍔 Dining Hall Conversations - Food and Socializing",
    "📚 Library Research - Academic Resource Language",
    "💻 Online Learning Terms - Digital Classroom",
    "👥 Professor Communication - Office Hours Etiquette",
    "🎯 Major Declaration Language - Academic Planning",
    "📆 Syllabus Comprehension - Course Requirements",
    "💼 Career Center Vocabulary - Job Preparation",
    "🎓 Graduation Requirements - Academic Progress",
    "📝 Capstone Project Language - Final Year Work",
    "🔬 Research Assistant Terms - Academic Employment",
    "🌍 Study Abroad Vocabulary - International Education",
    "💬 Campus Club Language - Extracurricular Activities",
    "🏥 Health Center Terms - Medical Campus Services",
    "💰 Financial Aid Vocabulary - Tuition and Funding",
    "📚 Textbook Buying/Selling - Campus Commerce",
    "🎯 Academic Advising Terms - Guidance Meetings",
    "📝 Internship Interview Language - Professional Skills",
    "🔍 Lab Safety Vocabulary - Science Classroom Terms",
    "📊 Statistics Terminology - Data Interpretation",
    "🎤 Student Government Language - Campus Leadership",
    "📚 Peer Tutoring Terms - Academic Support",
    "💻 Technology Troubleshooting - Campus IT Issues",
    "🏛️ Administrative Office Vocabulary - University Services",
    "🎯 Time Management for Students - Balancing Workload",

    # Modern Communication Skills (20 topics)
    "💼 Professional Email Writing - Formal Communication",
    "📱 Social Media English - Digital Communication",
    "👥 Networking Language - Making Professional Connections",
    "💬 Interview English - Job and Internship Questions",
    "📝 Cover Letter Vocabulary - Employment Applications",
    "🤝 Team Meeting Phrases - Collaborative Language",
    "🎯 Project Proposal Language - Idea Presentation",
    "📊 Data Presentation Terms - Visualizing Information",
    "💡 Brainstorming Vocabulary - Creative Sessions",
    "⚡ Conflict Resolution Phrases - Professional Disagreements",
    "📋 Feedback Language - Giving and Receiving Criticism",
    "🎤 Public Speaking Skills - Audience Engagement",
    "📝 Business Report Writing - Formal Documentation",
    "🔍 Problem-solving Vocabulary - Analytical Language",
    "💬 Small Talk Skills - Social Situations",
    "📱 Digital Etiquette - Online Communication Rules",
    "👥 Cross-cultural Communication - Global Context",
    "🎯 Negotiation Language - Compromise and Agreement",
    "📝 Professional Summary Writing - Career Documents",
    "💼 Workplace Terminology - Office Environment",

    # Test Preparation Vocabulary (15 topics)
    "🎯 TOEFL Essential Vocabulary - Academic Test Terms",
    "📚 IELTS Writing Task Language - Exam Structure",
    "💡 SAT Critical Reading - Test-specific Vocabulary",
    "⚡ ACT English Section - Grammar and Usage",
    "📝 GRE Analytical Writing - Advanced Vocabulary",
    "🔍 GMAT Sentence Correction - Business Terms",
    "📊 Test-taking Strategies - Time Management",
    "🎯 Vocabulary in Context - Reading Comprehension",
    "📝 Essay Exam Phrases - Timed Writing",
    "🔤 Word Association - Memory Techniques",
    "📚 Practice Test Language - Simulation Vocabulary",
    "💡 Test Anxiety Terms - Performance Psychology",
    "⚡ Multiple Choice Strategies - Elimination Techniques",
    "📝 Short Answer Language - Concise Responses",
    "🎯 Standardized Test Format - Structure Understanding"
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
        response = requests.post(url, headers=headers, json=data, timeout=90)
        response.raise_for_status()
        result = response.json()
        
        # Improved error handling for Gemini API response
        if 'candidates' in result and len(result['candidates']) > 0:
            candidate = result['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content']:
                if len(candidate['content']['parts']) > 0:
                    return candidate['content']['parts'][0]['text']
        
        print(f"⚠️ Gemini API response structure unexpected: {result}")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Gemini API Request Error: {e}")
        return None
    except Exception as e:
        print(f"⚠️ Gemini Unexpected Error: {e}")
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
    if not text:
        return ""
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
    Create a short English learning post in Arabic about: {topic}
    
    Requirements:
    - No greetings or opening phrases
    - Content in Arabic explaining English concepts
    - Structure: {style['structure']}
    - Keep it concise and practical
    - For pronunciation posts: show English words with Arabic pronunciation guides
    - Include engagement CTA within the content naturally
    - Add group invitation: "انضم لمجتمعنا التعليمي: https://facebook.com/groups/202055694371791/"
    - Use 2-3 emojis maximum
    - End with hashtags: {style['hashtags']}
    
    Important:
    - Never provide pronunciation guides for Arabic words
    - Focus only on English pronunciation
    - Make CTA part of the content flow
    - Keep it short and direct
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
    Create a short English-to-Arabic translation challenge post for Arabic learners.
    
    Requirements:
    - No greetings or opening phrases
    - Write a short English paragraph (2-3 sentences)
    - Challenge users to translate it to Arabic
    - Write the entire post in Arabic
    - Structure: {style['structure']}
    - Include engagement CTA within the content naturally
    - Add group invitation: "انضم لمجتمعنا التعليمي: https://facebook.com/groups/202055694371791/"
    - Use 2-3 emojis maximum
    - End with hashtags: {style['hashtags']}
    
    Important:
    - Make it short and engaging
    - All instructions must be in Arabic
    - Make CTA part of the content flow
    - Keep it concise
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
    Create a short reading comprehension post for Arabic learners of English.
    
    Requirements:
    - No greetings or opening phrases
    - Write a short English story or text (3-4 sentences)
    - Create 2 comprehension questions about the text
    - Write the entire post in Arabic
    - Structure: {style['structure']}
    - Include engagement CTA within the content naturally
    - Add group invitation: "انضم لمجتمعنا التعليمي: https://facebook.com/groups/202055694371791/"
    - Use 2-3 emojis maximum
    - End with hashtags: {style['hashtags']}
    
    Important:
    - Make it short and educational
    - Questions should be directly related to the text
    - Make CTA part of the content flow
    - Keep it concise
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
    
    # Return to original weights
    weights = [0.10, 0.0, 0.0]  # 60% regular, 20% translation, 20% comprehension
    
    selected_generator = random.choices(post_types, weights=weights, k=1)[0]
    return selected_generator()

# ===== MAIN EXECUTION =====
def main():
    print(f"\n=== English Post Generator [{datetime.now().strftime('%Y-%m-%d %H:%M')}] ===")
    
    # Test API keys first
    if not all([FB_PAGE_TOKEN, FB_PAGE_ID, GEMINI_API_KEY, PIXABAY_KEY]):
        print("❌ Missing environment variables. Please check your API keys.")
        return
    
    print("✅ All environment variables loaded")
    
    post, image, topic = generate_english_post()
    
    if post:
        print(f"\n=== Generated {topic} Content ===")
        print(post[:200] + "..." if len(post) > 200 else post)
        
        if post_to_facebook(post, image):
            print(f"\n✅ Posted successfully: {topic}")
        else:
            print("\n❌ Facebook posting failed")
    else:
        print("\n⚠️ Failed to generate content")

if __name__ == "__main__":
    main()