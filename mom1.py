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
    "Effective homework strategies for children with ADHD",
    "Developing executive function skills through daily routines",
    "Managing distractions in a world of constant stimulation",
    "Positive behavioral support systems that build confidence",
    "Creating sensory-friendly home environments",
    "Sleep hygiene practices for neurodiverse children",
    "Nutritional approaches to support focus and regulation",
    "Teaching emotional regulation skills",
    "Social skill development for children with ADHD",
    "Time management tools for neurodiverse learners",
    "Channeling high energy into productive activities",
    "Movement-based learning strategies",
    "Understanding and implementing school accommodations",
    "Mindfulness techniques suitable for children with ADHD",
    "Balancing technology use for optimal development",
    
    # Autism & Sensory Support
    "Communication strategies for children on the spectrum",
    "Creating sensory-safe spaces at home",
    "The importance of predictable routines for autistic children",
    "Supporting language development in nonverbal children",
    "Teaching emotion recognition and expression",
    "Using visual supports effectively in daily life",
    "Implementing sensory diets for regulation",
    "Addressing selective eating in autistic children",
    "Establishing healthy sleep patterns",
    "Toilet training approaches for children with sensory differences",
    "Developing play skills and social engagement",
    "Preventing and managing sensory overload",
    "Transition strategies for school and activities",
    "Building empathy and social understanding",
    "Incorporating rhythm and music for regulation",
    
    # Parenting Strategies
    "Connection-based discipline approaches",
    "Meeting individual needs in sibling relationships",
    "Active listening techniques for parent-child communication",
    "Fostering growth mindset and resilience",
    "Establishing healthy digital boundaries",
    "Sustainable self-care practices for parents",
    "Supporting positive sibling dynamics",
    "Age-appropriate responsibility and independence",
    "Shared reading as relationship building",
    "The developmental benefits of outdoor play",
    "Creative expression for emotional processing",
    "Cooking together as learning and bonding",
    "Teaching financial literacy through daily life",
    "Adapting parenting approaches across developmental stages",
    "Recognizing and celebrating developmental progress",
    
    # Parent Support
    "Building supportive parenting communities",
    "Managing parenting expectations and perfectionism",
    "Advocacy skills for educational and healthcare settings",
    "Reflective practices for parenting growth",
    "Maintaining presence amidst parenting demands",
    "Balancing career and parenting responsibilities",
    "Nurturing partner relationships through parenting challenges",
    "Establishing healthy boundaries with extended family",
    "Integrating complementary approaches to support",
    "Developing confidence in parenting decisions"
]

# ===== IMAGE KEYWORDS =====
PIXABAY_KEYWORDS = [
    "parent child learning", "family support", "organized home", 
    "calm parenting", "educational play", "therapy session", 
    "structured routine", "patient teaching", "development support",
    "special needs education", "positive parenting", "family bonding",
    "child focus", "learning environment", "supportive family",
    "developmental activities", "educational materials", "family organization"
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
    """Clean AI-generated text"""
    if not text:
        return ""
    
    # Remove markdown and formatting
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'[\*\_]{2,}', '', text)
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    
    # Ensure proper paragraph spacing
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    return text.strip()

# ===== PARENTING POST GENERATOR =====
def generate_parenting_post():
    """Generate authoritative yet warm parenting content"""
    topic = random.choice(EVERGREEN_TOPICS)
    
    prompt = f"""
    Create a professional yet compassionate parenting guidance post about: {topic}
    
    TONE AND VOICE REQUIREMENTS:
    - Authoritative: Based on established parenting principles and child development research
    - Professional: Sound like an experienced educator or child development specialist
    - Warm but not casual: Maintain professional boundaries while showing empathy
    - Evidence-informed: Reference established approaches (OT, ABA, developmental psychology) when relevant
    - Clear and structured: Present information in logical, digestible sections
    - Supportive: Acknowledge challenges while providing practical solutions
    
    ABSOLUTELY AVOID:
    - Personal anecdotes ("In my experience...", "What worked for me...")
    - Overly casual language ("You know?", "Honestly...", coffee chat style)
    - First-person framing that makes it about the writer
    - Any "friend chatting" tone
    
    STRUCTURE:
    1. Opening: State the parenting challenge clearly and professionally
    2. Core Content: Present 3-4 key strategies or insights
    3. Implementation: How to apply these in daily parenting
    4. Closing: Summary and encouragement
    
    ESSENTIAL ELEMENTS:
    1. Three CTAs (must be organically integrated):
       - Opening CTA: Early invitation to engage or learn more
       - Mid-post CTA: Natural transition inviting reflection or action
       - Closing CTA: Clear next steps and resource mention
    
    2. Natural website integration:
       - Mention "www.google.com" as a resource naturally
       - Position it as additional reading, not a sales pitch
       - Example: "For more detailed strategies on this topic, visit www.google.com"
    
    3. Fresh engagement elements:
       - Generate 5-7 relevant hashtags based on the specific content
       - Create 1-2 engagement prompts specific to the topic
       - NO preset or generic engagement elements
    
    4. Authoritative framing:
       - Use "research shows", "developmental experts suggest", "established practice indicates"
       - Cite approaches by their proper names when relevant
       - Maintain professional credibility throughout
    
    WRITING STYLE:
    - Clear, professional sentences
    - Varied paragraph lengths for readability
    - Subheadings or bold text for key points (using **)
    - Actionable, practical language
    - Empathetic but not emotionally overstated
    
    LENGTH: 300-500 words, well-structured
    
    IMPORTANT: The tone should be like a knowledgeable professional guiding parents, not a peer sharing personal experiences.
    """
    
    response = ask_ai(prompt)
    
    if response:
        content = clean_ai_output(response)
        
        # Add subtle human touches to professional content
        lines = content.split('\n')
        enhanced_content = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line:
                # Occasionally add emphasis to key points
                if i > 0 and i % 3 == 0 and len(line) > 40:
                    if not any(marker in line for marker in ['**', '*', '_']):
                        key_phrase = line.split('.')[0] if '.' in line else line[:50]
                        if len(key_phrase) > 20:
                            line = f"**{key_phrase}** - {line[len(key_phrase):]}" if line.startswith(key_phrase) else line
                
                enhanced_content.append(line)
        
        final_content = '\n\n'.join(enhanced_content)
        
        # Get appropriate image
        if any(word in topic.lower() for word in ['adhd', 'focus', 'executive']):
            image_keyword = "child focus learning"
        elif any(word in topic.lower() for word in ['autism', 'sensory', 'spectrum']):
            image_keyword = "therapy sensory support"
        elif any(word in topic.lower() for word in ['routine', 'structure', 'organization']):
            image_keyword = "organized home family"
        else:
            image_keyword = "parent child learning"
        
        image_url = get_pixabay_image_url(image_keyword)
        
        return final_content, image_url, topic
    
    return None, None, None

# ===== MAIN EXECUTION =====
def main():
    """Main execution function - silent operation"""
    # Quietly check for essential configurations
    essential_vars = [FB_PAGE_TOKEN, FB_PAGE_ID, GEMINI_API_KEY]
    
    if not all(essential_vars):
        return
    
    # Generate and post content
    post, image, topic = generate_parenting_post()
    
    if post:
        # Post without error display
        post_to_facebook(post, image)

if __name__ == "__main__":
    main()