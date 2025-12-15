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
    "parent child reading", "outdoor learning", "creative play",
    "mother child homework", "sensory activities", "family meal time"
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

def format_with_proper_spacing(text):
    """Format text with proper spacing for readability"""
    if not text:
        return ""
    
    # Clean all markdown
    text = re.sub(r'\*\*|\*|__|_|`', '', text)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    
    # Remove AI clichés
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
    
    # Normalize spacing
    text = re.sub(r'\s+', ' ', text)
    
    # Split into paragraphs and clean
    paragraphs = []
    for p in text.split('\n\n'):
        p = p.strip()
        if p:
            # Ensure each paragraph has proper line breaks
            sentences = re.split(r'(?<=[.!?])\s+', p)
            formatted_paragraph = '\n'.join(sentences)
            paragraphs.append(formatted_paragraph)
    
    # Join with double line breaks for clear separation
    return '\n\n'.join(paragraphs)

# ===== PARENTING POST GENERATOR =====
def generate_parenting_post():
    """Generate professional parenting content with proper spacing"""
    topic = random.choice(EVERGREEN_TOPICS)
    website_url = "https://elitemomshq.blogspot.com/"
    
    prompt = f"""
    Create a natural, readable parenting guidance post about: {topic}
    
    FORMAT REQUIREMENTS:
    1. Start with a SHORT, CLEAR HEADLINE in all caps
    2. Leave a blank line after the headline
    3. Use proper spacing between paragraphs
    4. Keep paragraphs short (2-3 sentences each)
    5. Add line breaks between sentences for better readability
    
    TONE REQUIREMENTS:
    - Natural and conversational
    - Authoritative but warm
    - Like a trusted expert sharing practical advice
    - Direct and clear without being robotic
    
    ESSENTIAL ELEMENTS:
    1. Three natural CTAs integrated organically:
       - Early in the post (within first paragraph)
       - Middle of the post (after key points)
       - End of the post (as a natural conclusion)
    
    2. Website mention: Include {website_url} naturally once
    
    3. Natural engagement:
       - Include 4-5 relevant hashtags at the end
       - Add one open-ended question for engagement
    
    CONTENT STRUCTURE:
    HEADLINE IN ALL CAPS
    
    [Opening paragraph with first CTA]
    
    [Key strategies or insights - 2-3 paragraphs]
    
    [Practical application with second CTA]
    
    [Closing thoughts with third CTA and website mention]
    
    [Question for engagement]
    
    [Hashtags]
    
    WRITING STYLE:
    - Use natural line breaks
    - Keep sentences varied in length
    - Make it feel like a human wrote it
    - Avoid robotic or formulaic patterns
    
    LENGTH: 250-350 words total
    
    Focus on creating content that flows naturally and is easy to read with proper spacing.
    """
    
    response = ask_ai(prompt)
    
    if response:
        # First, clean the content
        content = format_with_proper_spacing(response)
        
        # Ensure headline formatting
        lines = content.split('\n')
        if len(lines) > 0:
            # Check if first line looks like a headline
            first_line = lines[0].strip()
            if len(first_line) < 60 and not first_line.endswith('.') and not first_line.endswith('?'):
                # It's likely a headline, ensure proper spacing
                if len(lines) > 1 and lines[1].strip():
                    content = f"{first_line}\n\n{'\n'.join(lines[1:])}"
            else:
                # Add a headline
                headline = topic.upper()
                content = f"{headline}\n\n{content}"
        
        # Ensure website URL is included naturally
        if website_url not in content:
            # Add it organically at the end
            closing_phrases = [
                f"For more parenting resources, visit {website_url}",
                f"Find additional strategies at {website_url}",
                f"Explore more content at {website_url}"
            ]
            content += f"\n\n{random.choice(closing_phrases)}"
        
        # Get appropriate image
        if any(word in topic.lower() for word in ['adhd', 'homework', 'focus']):
            image_keyword = "child homework help"
        elif any(word in topic.lower() for word in ['autism', 'sensory']):
            image_keyword = "sensory play therapy"
        elif any(word in topic.lower() for word in ['sleep', 'bedtime', 'routine']):
            image_keyword = "bedtime routine child"
        elif any(word in topic.lower() for word in ['nutrition', 'food', 'eating']):
            image_keyword = "healthy family meal"
        elif any(word in topic.lower() for word in ['social', 'friends', 'play']):
            image_keyword = "children playing together"
        elif any(word in topic.lower() for word in ['self-care', 'parent', 'balance']):
            image_keyword = "mom self care"
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
        # Add visual separators for readability
        post = post.replace('\n\n', '\n\n')
        
        post_to_facebook(post, image)

if __name__ == "__main__":
    main()