import random
import requests
import json
import re
import os
from datetime import datetime

# ===== CONFIGURATION =====
FB_PAGE_TOKEN = os.getenv('FB_PAGE_TOKEN')
FB_PAGE_ID = os.getenv('FB_PAGE_ID')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
PIXABAY_KEY = os.getenv('PIXABAY_KEY')

# ===== EVERGREEN PARENTING TOPICS =====
EVERGREEN_TOPICS = [
    # ADHD Strategies (15 topics)
    "📚 ADHD Homework Strategies - Creating Effective Routines",
    "🧠 Executive Function Development - Building Planning Skills",
    "⚡ ADHD Focus Techniques - Managing Distractions",
    "🎯 Behavior Management for ADHD - Positive Reinforcement Systems",
    "🏠 ADHD-Friendly Home Organization - Reducing Overstimulation",
    "💤 Sleep Strategies for ADHD Children - Establishing Routines",
    "🍎 Nutrition Tips for ADHD - Brain-Boosting Foods",
    "😤 Emotional Regulation for ADHD Kids - Managing Frustration",
    "🤝 Social Skills Building - ADHD Friendship Challenges",
    "⏰ Time Management for ADHD - Visual Schedules & Timers",
    "🎨 Creative Outlets for ADHD Energy - Channeling Hyperfocus",
    "🏃 Movement Breaks - Why Fidgeting Helps Focus",
    "🎓 School Accommodations - IEP/504 Plan Essentials",
    "🧘 Mindfulness for ADHD - Calming Techniques",
    "📱 Technology Balance - Screen Time Management",

    # Autism Parenting (15 topics)
    "🤝 Autism Communication Strategies - Building Connection",
    "🌀 Sensory Processing Support - Creating Calm Environments",
    "📅 Predictability & Routines - Why Structure Matters",
    "🗣️ Speech & Language Development - Alternative Communication",
    "😊 Emotion Recognition - Teaching Facial Expressions",
    "👥 Social Story Creation - Preparing for New Situations",
    "👐 Sensory Diet Implementation - Daily Regulation Activities",
    "🍽️ Picky Eating Solutions - Expanding Food Acceptance",
    "💤 Autism Sleep Solutions - Bedtime Routines",
    "🚽 Toilet Training Strategies - Autism-Specific Approaches",
    "🎭 Play Skills Development - Joining Their World",
    "🚨 Meltdown Prevention - Recognizing Triggers",
    "🏫 School Transition Support - Visual Schedules",
    "🤗 Building Empathy Skills - Perspective-Taking Activities",
    "🎶 Music & Rhythm Therapy - Calming Benefits",

    # General Parenting Wisdom (15 topics)
    "❤️ Positive Discipline - Connection Before Correction",
    "🎪 Balancing Multiple Children - Individual Attention",
    "👂 Active Listening Skills - Understanding Your Child",
    "🌱 Growth Mindset Parenting - Praising Effort vs Results",
    "📱 Digital Parenting - Healthy Tech Boundaries",
    "💖 Self-Care for Moms - Avoiding Burnout",
    "👨‍👩‍👧‍👦 Sibling Dynamics - Managing Rivalry",
    "🎯 Age-Appropriate Chores - Building Responsibility",
    "📖 Reading Together - Bonding Through Books",
    "🌳 Nature Connection - Outdoor Play Benefits",
    "🎨 Creative Parenting - Art & Expression",
    "🍳 Cooking With Kids - Life Skills Development",
    "💰 Teaching Financial Literacy - Age-Appropriate Lessons",
    "🔄 Parenting Transitions - Adapting as Kids Grow",
    "🎉 Celebrating Small Wins - Joy in Daily Moments",

    # Mom Support & Community (10 topics)
    "🤝 Mom Friendships - Building Your Support Village",
    "💪 Mom Guilt Management - Letting Go of Perfect",
    "🗣️ Advocating for Your Child - School & Healthcare",
    "📝 Journaling for Moms - Processing the Journey",
    "🧘 Mindfulness for Moms - Staying Present",
    "👩‍💼 Work-Life Balance - Realistic Expectations",
    "💝 Marriage Maintenance - Nurturing Your Relationship",
    "👵 Grandparent Relationships - Setting Boundaries",
    "🌿 Holistic Wellness - Natural Parenting Approaches",
    "🎯 Finding Your Parenting Style - Trusting Your Instincts"
]

# ===== POSTING STYLES =====
POST_STYLES = {
    "Practical Tips": {
        "hashtags": "#ParentingTips #ADHDMom #AutismParenting #MomLife",
        "structure": "🎯 The Challenge\n💡 Evidence-Based Strategy\n✨ Real-Life Application\n✅ Quick Implementation Tip"
    },
    "Science Explained": {
        "hashtags": "#ChildDevelopment #Neurodiversity #ParentingScience #MomAdvice",
        "structure": "🧠 The Science Behind It\n👶 How It Manifests in Kids\n🛠️ Practical Parenting Adaptation\n🌟 Why This Matters Long-Term"
    },
    "Quick Wins": {
        "hashtags": "#MomHacks #ParentingWin #ADHDLife #AutismSupport",
        "structure": "⚡ The Problem You're Facing\n🎯 One Simple Adjustment\n💖 Expected Outcome\n📝 Try This Today"
    },
    "Story Format": {
        "hashtags": "#MomStory #RealParenting #SpecialNeedsMom #ParentingJourney",
        "structure": "📖 A Common Mom Struggle\n💡 The Turning Point\n✨ What Actually Worked\n❤️ What I Learned"
    },
    "Q&A Style": {
        "hashtags": "#MomQuestions #ParentingAdvice #ADHDHelp #AutismCommunity",
        "structure": "❓ Question From a Mom\n🎯 Expert-Informed Answer\n✨ Step-by-Step Guidance\n💝 Encouragement for You"
    }
}

# ===== IMAGE KEYWORDS =====
PIXABAY_KEYWORDS = [
    "mother child", "family love", "parenting", "kids playing",
    "calm home", "organized space", "outdoor family", "learning toys",
    "sensory play", "happy children", "mom reading", "family nature",
    "creative kids", "peaceful home", "parenting joy"
]

# ===== ENGAGEMENT MESSAGES =====
ENGAGEMENT_MSGS = [
    "💬 Which of these strategies have you tried? Share your experience below!",
    "👥 Tag a mom friend who needs to see this!",
    "❤️ Save this post for when you need it most!",
    "👇 What's YOUR biggest parenting challenge right now? Comment below!"
]

# ===== CORE FUNCTIONS (UNCHANGED from your original script) =====
def ask_ai(prompt):
    """Generate content using Gemini 2.5 Flash"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.8,
            "topP": 0.9,
            "maxOutputTokens": 8192
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=90)
        response.raise_for_status()
        result = response.json()
        
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

# ===== NEW PARENTING POST GENERATORS =====
def get_parenting_image():
    """Get a random parenting/family image"""
    return get_pixabay_image_url(random.choice(PIXABAY_KEYWORDS))

def generate_evergreen_parenting_post():
    """Generate an evergreen parenting post"""
    topic = random.choice(EVERGREEN_TOPICS)
    
    # Determine post style based on topic
    if any(word in topic.lower() for word in ["strategy", "technique", "tip", "how to"]):
        style_name, style = "Practical Tips", POST_STYLES["Practical Tips"]
    elif any(word in topic.lower() for word in ["science", "development", "brain", "research"]):
        style_name, style = "Science Explained", POST_STYLES["Science Explained"]
    elif "story" in topic.lower() or "journey" in topic.lower():
        style_name, style = "Story Format", POST_STYLES["Story Format"]
    else:
        style_name, style = "Quick Wins", POST_STYLES["Quick Wins"]
    
    prompt = f"""
    Create an evergreen parenting post about: {topic}
    
    IMPORTANT REQUIREMENTS:
    1. Write in ENGLISH only (entire post)
    2. Target audience: Mothers of children with ADHD, Autism, or general parenting challenges
    3. Tone: Warm, encouraging, evidence-informed but not clinical
    4. Structure: {style['structure']}
    5. Content must remain relevant for years (evergreen) - no time-sensitive references
    
    CONTENT GUIDELINES:
    - Start directly with valuable content (no greetings)
    - Include practical, actionable advice
    - Reference established parenting approaches when applicable
    - Acknowledge that every child is different
    - Normalize parenting struggles
    - Focus on progress, not perfection
    
    ENGAGEMENT ELEMENTS:
    - Include ONE of these naturally in the content:
      * "{random.choice(ENGAGEMENT_MSGS)}"
    - Add these at the END of your post:
      * "👉 SAVE this post for when you need it!"
      * "🤝 Share your experience in the comments below"
      * "💌 Follow for daily parenting support"
      * "🌟 You're doing better than you think, mama"
    
    FORMATTING:
    - Use emojis sparingly for readability
    - End with hashtags: {style['hashtags']}
    
    LENGTH: Comprehensive but readable (aim for 300-500 words)
    """
    
    response = ask_ai(prompt)
    if response:
        content = clean_ai_output(response)
        
        # Format hashtags properly
        lines = content.split('\n')
        main_content = [line for line in lines if not line.startswith('#')]
        formatted_content = '\n'.join(main_content).strip()
        formatted_content += '\n\n' + style['hashtags']
        
        return formatted_content, get_parenting_image(), topic
    
    return None, None, None

def generate_mom_support_post():
    """Generate a mom-focused support post"""
    style = POST_STYLES["Q&A Style"]
    
    # Common mom struggles (evergreen)
    mom_questions = [
        "How do I balance my needs with my child's constant demands?",
        "I feel guilty when I lose patience with my neurodiverse child. Is this normal?",
        "How can I explain my child's ADHD/Autism to family members who don't understand?",
        "Where do I find the energy to advocate for my child day after day?",
        "How do other special needs moms manage self-care?"
    ]
    
    question = random.choice(mom_questions)
    
    prompt = f"""
    Create a supportive, encouraging post for mothers of children with ADHD, Autism, or special needs.
    
    QUESTION TO ADDRESS: "{question}"
    
    IMPORTANT REQUIREMENTS:
    1. Write in ENGLISH only
    2. Format as a warm, compassionate Q&A
    3. Structure: {style['structure']}
    4. Tone: Like a wise friend who's been there
    5. Make it evergreen - relevant anytime
    
    CONTENT GUIDELINES:
    - Start directly with the question
    - Provide validation and normalization first ("This is so common...")
    - Offer practical, gentle advice
    - Include specific, actionable steps
    - Emphasize self-compassion
    - Avoid clinical jargon
    
    MUST INCLUDE:
    - Validation of her feelings
    - 2-3 practical suggestions
    - Reminder that progress isn't linear
    - Encouragement to connect with other moms
    
    ENGAGEMENT:
    - End with: "💬 What advice would YOU give to a mom feeling this way? Comment below!"
    - Add: "❤️ Tag a mom friend who needs this reminder today"
    - Include: "📌 Save this for when you need a boost"
    
    HASHTAGS: {style['hashtags']}
    
    LENGTH: 250-400 words
    """
    
    response = ask_ai(prompt)
    if response:
        content = clean_ai_output(response)
        
        lines = content.split('\n')
        main_content = [line for line in lines if not line.startswith('#')]
        formatted_content = '\n'.join(main_content).strip()
        formatted_content += '\n\n' + style['hashtags']
        
        return formatted_content, get_parenting_image(), "Mom Support Q&A"
    
    return None, None, None

def generate_activity_idea_post():
    """Generate a post with practical activity ideas"""
    style = POST_STYLES["Practical Tips"]
    
    activity_types = [
        "Sensory-friendly activities for sensitive kids",
        "Quiet time ideas for overstimulated children",
        "Movement breaks that actually calm ADHD energy",
        "Social skills practice through play",
        "Emotional regulation tools you can make at home"
    ]
    
    activity = random.choice(activity_types)
    
    prompt = f"""
    Create a practical, activity-focused parenting post.
    
    ACTIVITY FOCUS: {activity}
    
    AUDIENCE: Parents of children with ADHD, Autism, or sensory processing differences
    
    REQUIREMENTS:
    1. Entire post in ENGLISH
    2. Structure: {style['structure']}
    3. Provide 3-5 specific activity ideas
    4. Include:
       - Age adaptations (toddlers, school-age, preteens)
       - Materials needed (simple, household items)
       - Expected benefits
       - Troubleshooting tips
    
    FORMAT:
    - List activities clearly
    - Explain WHY each activity helps
    - Include safety considerations if needed
    - Suggest modifications for different needs
    
    ENGAGEMENT:
    - Ask: "Which activity will you try first? Comment below! 📝"
    - Add: "👥 Share this with parents who need fresh ideas"
    
    HASHTAGS: {style['hashtags']} #SensoryPlay #ADHDActivities #AutismPlay #MomHacks
    
    LENGTH: 300-500 words
    """
    
    response = ask_ai(prompt)
    if response:
        content = clean_ai_output(response)
        
        lines = content.split('\n')
        main_content = [line for line in lines if not line.startswith('#')]
        formatted_content = '\n'.join(main_content).strip()
        formatted_content += '\n\n' + style['hashtags'] + " #SensoryPlay #ADHDActivities #AutismPlay #MomHacks"
        
        return formatted_content, get_parenting_image(), activity
    
    return None, None, None

def generate_parenting_post():
    """Randomly select and generate a post type"""
    post_types = [
        generate_evergreen_parenting_post,  # 50% chance
        generate_mom_support_post,          # 30% chance
        generate_activity_idea_post         # 20% chance
    ]
    
    weights = [0.5, 0.3, 0.2]
    selected_generator = random.choices(post_types, weights=weights, k=1)[0]
    return selected_generator()

# ===== MAIN EXECUTION =====
def main():
    print(f"\n=== Parenting Post Generator [{datetime.now().strftime('%Y-%m-%d %H:%M')}] ===")
    
    # Test API keys
    if not all([FB_PAGE_TOKEN, FB_PAGE_ID, GEMINI_API_KEY, PIXABAY_KEY]):
        print("❌ Missing environment variables. Please check your API keys.")
        return
    
    print("✅ All environment variables loaded")
    
    post, image, topic = generate_parenting_post()
    
    if post:
        print(f"\n=== Generated {topic} ===")
        print(post[:500] + "..." if len(post) > 500 else post)
        print(f"\nPost length: {len(post)} characters")
        
        if post_to_facebook(post, image):
            print(f"\n✅ Posted successfully: {topic}")
        else:
            print("\n❌ Facebook posting failed")
    else:
        print("\n⚠️ Failed to generate content")

if __name__ == "__main__":
    main()