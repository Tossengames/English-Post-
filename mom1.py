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
    # ADHD & Executive Function
    "Homework strategies for children with ADHD",
    "Executive function skills development",
    "Managing distractions for better focus",
    "Positive behavioral support systems",
    "Sensory-friendly home environments",
    "Sleep routines for neurodiverse children",
    "Nutrition for focus and emotional regulation",
    "Teaching emotional regulation skills",
    "Social skill development for ADHD",
    "Time management for neurodiverse learners",
    "Productive energy channeling",
    "Movement-based learning approaches",
    "School accommodations implementation",
    "Mindfulness for children with ADHD",
    "Balancing technology use",
    
    # Autism & Sensory Support
    "Communication strategies for autistic children",
    "Creating sensory-safe spaces",
    "Predictable routines for autistic children",
    "Language development support",
    "Teaching emotion recognition",
    "Visual supports in daily life",
    "Sensory diet implementation",
    "Addressing selective eating",
    "Establishing sleep patterns",
    "Toilet training with sensory differences",
    "Play skills development",
    "Managing sensory overload",
    "School transition strategies",
    "Building empathy skills",
    "Music for emotional regulation",
    
    # Parenting Strategies
    "Connection-based discipline",
    "Individual attention in sibling relationships",
    "Active listening techniques",
    "Fostering growth mindset",
    "Establishing digital boundaries",
    "Sustainable self-care for parents",
    "Positive sibling dynamics",
    "Age-appropriate responsibilities",
    "Shared reading for bonding",
    "Outdoor play benefits",
    "Creative expression for emotions",
    "Cooking as learning time",
    "Teaching financial literacy",
    "Parenting across developmental stages",
    "Celebrating developmental progress",
    
    # Parent Support
    "Building parenting communities",
    "Managing parenting expectations",
    "Advocacy in educational settings",
    "Reflective parenting practices",
    "Maintaining presence as a parent",
    "Career and parenting balance",
    "Nurturing partner relationships",
    "Boundaries with extended family",
    "Complementary support approaches",
    "Confidence in parenting decisions"
]

# ===== IMAGE KEYWORDS =====
PIXABAY_KEYWORDS = [
    "parent child learning", "family support", "organized home", 
    "calm parenting", "educational play", "therapy session", 
    "structured routine", "patient teaching", "development support",
    "special needs education", "positive parenting", "family bonding",
    "child focus", "learning environment", "supportive family",
    "developmental activities", "educational materials", "family organization",
    "parent child reading", "outdoor learning", "creative play"
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
    """Clean AI-generated text to remove markdown and AI clichés"""
    if not text:
        return ""
    
    # Remove all markdown formatting
    text = re.sub(r'\*\*|\*|__|_|`', '', text)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    
    # Remove common AI clichés and phrases
    ai_cliches = [
        r'\bnavigating\b.*?\bcomplexity\b',
        r'\bdiscover\b.*?\bpotential\b',
        r'\bunlock\b.*?\bsecrets?\b',
        r'\bjourney\b.*?\btoward\b',
        r'\bunleash\b.*?\bpotential\b',
        r'\btransform\b.*?\bexperience\b',
        r'\bembark\b.*?\badventure\b',
        r'\bharness\b.*?\bpower\b',
        r'\btap into\b.*?\bpotential\b',
        r'\belevate\b.*?\bexperience\b',
        r'\bmaster\b.*?\bart\b',
        r'\brevolutionize\b.*?\bapproach\b',
        r'\bpave.*?way\b',
        r'\bunveil.*?mysteries?\b',
        r'\bchart.*?course\b'
    ]
    
    for cliche in ai_cliches:
        text = re.sub(cliche, '', text, flags=re.IGNORECASE)
    
    # Clean up extra spaces and line breaks
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    # Ensure clear paragraph structure
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    return '\n\n'.join(paragraphs)

# ===== PARENTING POST GENERATOR =====
def generate_parenting_post():
    """Generate professional parenting content with clear headline"""
    topic = random.choice(EVERGREEN_TOPICS)
    
    prompt = f"""
    Create a parenting guidance post with a clear headline about: {topic}
    
    FORMAT REQUIREMENTS:
    1. Start with a SHORT, CLEAR HEADLINE in all caps, followed by a blank line
    2. No markdown of any kind (no **bold**, no *italics*, no bullet points)
    3. Use plain text with clear paragraphs
    
    TONE REQUIREMENTS:
    - Authoritative and professional
    - Warm but not casual
    - Direct and clear
    - Based on established parenting principles
    
    ABSOLUTELY AVOID:
    - Any AI cliché phrases like "navigating the complexity", "discover your", "unlock the", "journey toward", "unleash potential"
    - Markdown formatting
    - Personal anecdotes
    - Overly casual language
    - Vague or flowery language
    
    STRUCTURE:
    1. HEADLINE: Clear, specific, in all caps
    2. Opening paragraph: State the issue clearly
    3. Main content: 3-4 specific strategies or points
    4. Practical application: How to implement
    5. Closing: Summary and encouragement
    
    ESSENTIAL ELEMENTS:
    1. Three natural CTAs integrated:
       - Early in the post (first paragraph)
       - Middle of the post (after main strategies)
       - End of the post (final paragraph)
    
    2. Website mention: Include "www.google.com" naturally once
    
    3. Engagement elements:
       - Generate 3-5 relevant hashtags at the end
       - Include one question for engagement
    
    WRITING STYLE:
    - Use clear, direct sentences
    - Focus on practical, actionable advice
    - Avoid jargon unless clearly explained
    - Paragraphs should be 2-4 sentences each
    
    LENGTH: 250-400 words total
    
    EXAMPLE HEADLINE: MANAGING HOMEWORK STRUGGLES WITH ADHD
    
    Begin with the headline immediately.
    """
    
    response = ask_ai(prompt)
    
    if response:
        content = clean_ai_output(response)
        
        # Ensure it starts with a clear headline
        lines = content.split('\n')
        if len(lines) > 0 and not lines[0].isupper() and len(lines[0]) < 50:
            # Add a headline if missing
            headline = topic.upper()
            content = f"{headline}\n\n{content}"
        
        # Get appropriate image
        if any(word in topic.lower() for word in ['adhd', 'focus', 'homework', 'executive']):
            image_keyword = "child focus learning"
        elif any(word in topic.lower() for word in ['autism', 'sensory']):
            image_keyword = "therapy sensory support"
        elif any(word in topic.lower() for word in ['routine', 'structure']):
            image_keyword = "organized home family"
        elif any(word in topic.lower() for word in ['sleep', 'bedtime']):
            image_keyword = "calm bedroom child"
        elif any(word in topic.lower() for word in ['nutrition', 'food', 'eating']):
            image_keyword = "healthy food family"
        elif any(word in topic.lower() for word in ['social', 'friends', 'play']):
            image_keyword = "children playing together"
        else:
            image_keyword = "parent child learning"
        
        image_url = get_pixabay_image_url(image_keyword)
        
        return content, image_url, topic
    
    return None, None, None

# ===== MAIN EXECUTION =====
def main():
    """Main execution function - silent operation"""
    essential_vars = [FB_PAGE_TOKEN, FB_PAGE_ID, GEMINI_API_KEY]
    
    if not all(essential_vars):
        return
    
    post, image, topic = generate_parenting_post()
    
    if post:
        post_to_facebook(post, image)

if __name__ == "__main__":
    main()