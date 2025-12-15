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
    "Creating homework routines that actually work for ADHD brains",
    "Helping your child develop executive function skills naturally",
    "Managing distractions without constant nagging",
    "Positive reinforcement systems that don't feel like bribes",
    "Organizing your home to reduce sensory overload",
    "Bedtime routines for kids who just won't settle",
    "Nutrition that supports focus and calm (beyond eliminating sugar)",
    "Teaching emotional regulation when emotions feel overwhelming",
    "Navigating friendship challenges with social differences",
    "Time management tools that work for neurodiverse minds",
    "Channeling hyperfocus into creative outlets",
    "Movement breaks that actually help with focus",
    "Understanding school accommodations and how to advocate for them",
    "Simple mindfulness techniques for busy families",
    "Finding the right balance with screen time",
    
    # Autism Parenting (15 topics)
    "Building connection with a child who communicates differently",
    "Creating calm spaces in a sensory-overwhelming world",
    "Why predictability matters and how to create flexible routines",
    "Supporting speech development when words don't come easily",
    "Teaching emotion recognition in a way that makes sense",
    "Using social stories for real-life situations",
    "Daily sensory activities that actually help with regulation",
    "Expanding food acceptance without mealtime battles",
    "Sleep solutions for children who struggle to wind down",
    "Toilet training approaches that respect sensory needs",
    "Joining your child's play world to build connection",
    "Recognizing meltdown triggers before they escalate",
    "Visual schedules that actually get used",
    "Developing empathy and perspective-taking skills",
    "Using music and rhythm for emotional regulation",
    
    # General Parenting Wisdom (15 topics)
    "Discipline that strengthens connection rather than breaking it",
    "Finding one-on-one time with multiple children",
    "Listening to understand, not just to respond",
    "Praising effort in a way that builds resilience",
    "Setting tech boundaries that feel reasonable to everyone",
    "Finding moments of self-care in a packed schedule",
    "Helping siblings understand and support each other",
    "Age-appropriate responsibilities that build confidence",
    "Making reading together a special connection time",
    "The mental health benefits of outdoor play",
    "Using creativity to work through big feelings",
    "Cooking together as relationship-building time",
    "Teaching money concepts in practical, age-appropriate ways",
    "Adapting your parenting as your child grows",
    "Noticing and celebrating the tiny, beautiful moments",
    
    # Mom Support & Community (10 topics)
    "Building your village when you feel isolated",
    "Letting go of perfect and embracing 'good enough'",
    "Speaking up for your child without burning bridges",
    "Using journaling to process the parenting journey",
    "Staying present when you're pulled in a million directions",
    "Finding work-life balance that works for your family",
    "Nurturing your relationship amid parenting demands",
    "Setting boundaries with well-meaning relatives",
    "Natural approaches that complement traditional methods",
    "Trusting your instincts amid conflicting advice"
]

# ===== IMAGE KEYWORDS =====
PIXABAY_KEYWORDS = [
    "mother child", "family love", "parenting", "kids playing",
    "calm home", "organized space", "outdoor family", "learning toys",
    "sensory play", "happy children", "mom reading", "family nature",
    "creative kids", "peaceful home", "parenting joy", "mother daughter",
    "father child", "family kitchen", "bedtime story", "playground fun",
    "special needs", "inclusive play", "therapy session", "learning time"
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
            "temperature": 0.8,
            "topP": 0.95,
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
        
        return None
        
    except Exception:
        return None

def post_to_facebook(message, image_url=None):
    """Post to Facebook Page"""
    try:
        if image_url:
            upload_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
            upload_params = {
                'access_token': FB_PAGE_TOKEN,
                'url': image_url,
                'published': 'false'
            }
            
            upload_resp = requests.post(upload_url, params=upload_params, timeout=30)
            upload_resp.raise_for_status()
            photo_id = upload_resp.json().get('id')
            
            if photo_id:
                post_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
                post_params = {
                    'access_token': FB_PAGE_TOKEN,
                    'message': message,
                    'attached_media': json.dumps([{'media_fbid': photo_id}])
                }
                post_resp = requests.post(post_url, params=post_params, timeout=30)
                return post_resp.status_code == 200
        else:
            post_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
            post_params = {
                'access_token': FB_PAGE_TOKEN,
                'message': message
            }
            post_resp = requests.post(post_url, params=post_params, timeout=30)
            return post_resp.status_code == 200
            
    except Exception:
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
        if data['totalHits'] > 0:
            return random.choice(data['hits'])['webformatURL']
        return None
    except Exception:
        return None

def clean_ai_output(text):
    """Clean AI-generated text to feel more human"""
    if not text:
        return ""
    
    # Remove markdown formatting
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'[\*\_]{2,}', '', text)
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    
    # Add human-like imperfections
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line:
            # Occasionally add ellipsis or conversational punctuation
            if random.random() > 0.7 and len(line) > 40:
                if not line.endswith(('?', '!', '...')):
                    if random.random() > 0.5:
                        line = line + "..."
            
            # Sometimes add conversational phrases
            if random.random() > 0.8 and len(cleaned_lines) > 2:
                connectors = ["You know?", "Right?", "Honestly...", "I've found that..."]
                if line.endswith('.'):
                    line = line[:-1] + f" {random.choice(connectors)}"
            
            cleaned_lines.append(line)
    
    return '\n\n'.join(cleaned_lines)

def get_parenting_image():
    """Get a random parenting/family image"""
    return get_pixabay_image_url(random.choice(PIXABAY_KEYWORDS))

# ===== NEW PARENTING POST GENERATOR =====
def generate_parenting_post():
    """Generate a single, well-crafted parenting post"""
    topic = random.choice(EVERGREEN_TOPICS)
    image_keyword = random.choice(PIXABAY_KEYWORDS)
    
    prompt = f"""
    Create a warm, conversational parenting post about: {topic}
    
    TONE AND VOICE:
    - Write like a wise, compassionate friend who's been there
    - Use natural, conversational language with occasional imperfections
    - Include personal anecdotes or "I've noticed..." observations
    - Sound like a real human parent sharing experience, not an expert lecturing
    - Warm, companionable, reassuring - like chatting over coffee
    
    STRUCTURE:
    Start with: An opening that grabs attention with understanding
    Middle: Share insights, strategies, or perspectives
    End: Wrap up with encouragement and next steps
    
    CONTENT REQUIREMENTS:
    1. Must include CTA at THREE points:
       - Early in the post (first few sentences)
       - Middle of the post (natural transition point)
       - End of the post (final thought)
    
    2. CTAs should encourage engagement naturally:
       - Ask questions that invite sharing
       - Suggest sharing with specific people
       - Invite to read more on our website
       - Use phrases like "I'd love to know..." or "Tell me..."
    
    3. Engagement elements must be GENERATED for this specific topic:
       - Create relevant hashtags (5-7) based on the content
       - Create engagement tags (like "Tag a friend who...")
       - Make them feel organic to the conversation
    
    4. Include mention of our website naturally:
       - www.google.com (placeholder)
       - Work it into the conversation naturally
       - Example: "We've got more on this at www.google.com if you're curious"
    
    5. Human-like touches:
       - Occasional parentheses with asides
       - Natural sentence fragments for emphasis
       - Varied sentence lengths
       - Conversational questions
    
    6. Content must feel evergreen - relevant anytime
    
    LENGTH: 250-400 words, broken into short paragraphs
    
    IMPORTANT: Don't use any preset hashtags, tags, or CTAs. Generate them fresh for this topic.
    The writing should flow naturally like a real social media post from a friend.
    """
    
    response = ask_ai(prompt)
    
    if response:
        # Clean and format the response
        content = clean_ai_output(response)
        
        # Ensure we have engagement elements
        if '#parenting' not in content.lower():
            # Add a line about engagement if missing
            engagement_lines = [
                "\n\nI'd love to hear your thoughts on this...",
                "\n\nWhat's been your experience with this?",
                "\n\nThis stuff is always better when we share ideas..."
            ]
            content += random.choice(engagement_lines)
        
        # Get image (silently fail if no image)
        image_url = get_pixabay_image_url(image_keyword)
        
        return content, image_url, topic
    
    return None, None, None

# ===== MAIN EXECUTION =====
def main():
    """Main execution function - silent on errors"""
    # Test API keys quietly
    if not all([FB_PAGE_TOKEN, FB_PAGE_ID, GEMINI_API_KEY]):
        return
    
    # Generate post
    post, image, topic = generate_parenting_post()
    
    if post:
        # Try to post, but don't show errors
        success = post_to_facebook(post, image)
        if success:
            # Optional: Log success quietly if needed
            pass

if __name__ == "__main__":
    main()