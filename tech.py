#!/usr/bin/env python3
"""
Tech Information Generator: Generate informative Arabic content about technology, PCs, mobile, and gadgets.
Creates images with text overlay and posts to Facebook Page.
"""

import os
import requests
import random
import textwrap
import json
import hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from io import BytesIO
import time
from urllib.parse import quote_plus

# Try the new Google GenAI SDK import first
try:
    from google import genai
    print("Using new Google GenAI SDK")
    SDK_TYPE = "new"
except ImportError:
    try:
        # Fallback to old import style
        import google.generativeai as genai
        print("Using old Google Generative AI SDK")
        SDK_TYPE = "old"
    except ImportError as e:
        print(f"Failed to import Google AI libraries: {e}")
        print("Please install the required package:")
        print("   pip install google-genai  # For new SDK")
        print("   or")
        print("   pip install google-generativeai  # For old SDK")
        exit(1)

# Try to import googlesearch for real web searches
try:
    from googlesearch import search as google_search
    GOOGLE_SEARCH_AVAILABLE = True
    print("Using googlesearch-python for web searches")
except ImportError:
    GOOGLE_SEARCH_AVAILABLE = False
    print("googlesearch-python not available")

# File to store posted content for duplication check
POST_HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "posted_content.json")

def load_posted_content():
    """Load history of posted content to avoid duplicates"""
    try:
        if os.path.exists(POST_HISTORY_FILE):
            with open(POST_HISTORY_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
                else:
                    return []
        return []
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error loading history file: {e}")
        return []

def save_posted_content(content_text):
    """Save posted content to history"""
    try:
        posted_content = load_posted_content()
        
        # Create a unique hash of the content text
        content_hash = hashlib.md5(content_text.encode()).hexdigest()
        
        if content_hash not in posted_content:
            posted_content.append(content_hash)
            os.makedirs(os.path.dirname(POST_HISTORY_FILE), exist_ok=True)
            with open(POST_HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(posted_content, f)
            print(f"Saved content to history: {content_text[:50]}...")
            return True
        else:
            print(f"Content already exists in history: {content_text[:50]}...")
            return False
    except Exception as e:
        print(f"Error saving to history: {e}")
        return False

def is_duplicate_content(content_text):
    """Check if content has already been posted"""
    try:
        posted_content = load_posted_content()
        content_hash = hashlib.md5(content_text.encode()).hexdigest()
        return content_hash in posted_content
    except Exception as e:
        print(f"Error checking duplicate: {e}")
        return False

def get_google_trends():
    """Get trending tech topics"""
    try:
        trending_keywords = [
            "smartphone", "PC gaming", "laptop reviews", "tech gadgets", 
            "AI technology", "mobile apps", "wireless earbuds", "smart home",
            "gaming PC", "tech news", "Android tips", "iOS features",
            "computer hardware", "software updates", "cybersecurity",
            "productivity apps", "tech reviews", "wearable technology"
        ]
        
        all_trends = []
        for keyword in trending_keywords:
            try:
                results = list(google_search(
                    keyword, 
                    num_results=5,
                    pause=2.0,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                ))
                
                for url in results:
                    if any(x in url for x in ['trend', 'news', 'blog', 'article', 'report', 'review']):
                        url_parts = url.split('/')
                        for part in url_parts:
                            if len(part) > 3 and '-' in part and any(c.isalpha() for c in part):
                                words = part.split('-')
                                for word in words:
                                    if (len(word) > 4 and word.isalpha() and 
                                        word.lower() not in ['https', 'www', 'com', 'org', 'net', 'html', 'php']):
                                        all_trends.append(word)
                
                time.sleep(1)
                
            except Exception as e:
                continue
        
        unique_trends = list(set([t for t in all_trends if 3 < len(t) < 20]))
        if unique_trends:
            return unique_trends[:10]
        
        return get_fallback_trends()
            
    except Exception as e:
        return get_fallback_trends()

def get_fallback_trends():
    """Get reliable fallback trending topics"""
    fallback_trends = [
        "gaming PC", "processor comparison", "graphics cards", "RAM upgrade",
        "SSD vs HDD", "PC building", "laptop specs", "motherboard",
        "cooling systems", "PC performance", "smartphone camera", "battery life",
        "mobile gaming", "app recommendations", "iOS vs Android", "phone security",
        "mobile photography", "AI technology", "smart home", "wireless charging",
        "tech gadgets", "cybersecurity", "data privacy", "cloud storage"
    ]
    return random.sample(fallback_trends, min(8, len(fallback_trends)))

def search_web_content(topic):
    """Perform web search for the topic"""
    try:
        if not GOOGLE_SEARCH_AVAILABLE:
            return f"Technology experts are discussing {topic} as an important development in the tech industry."
        
        search_query = f"{topic} technology innovation 2024"
        results = list(google_search(
            search_query, 
            num_results=3,
            pause=2.0,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ))
        
        content_parts = []
        content_parts.append(f"Recent technology discussions indicate that {topic} is currently a significant focus area.")
        
        if results:
            content_parts.append("Industry analysis shows several key developments:")
            content_parts.append(f"- {topic} represents important technological advancement")
            content_parts.append(f"- This area connects to broader innovation trends in the tech sector")
            
            domain_count = len(set(url.split('/')[2] for url in results if len(url.split('/')) > 2))
            content_parts.append(f"Based on review of {domain_count} sources, this represents valuable technological insight.")
        else:
            content_parts.append("This technology area is receiving significant attention across industry discussions.")
        
        content_parts.append("Technology analysts and experts are highlighting the importance of these developments.")
        
        return " ".join(content_parts)
        
    except Exception as e:
        return f"Current discussions about {topic} indicate it represents significant technological progress. Experts are emphasizing its relevance for the technology landscape."

def generate_tech_content():
    """Generate informative tech content using Gemini"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            trends = get_google_trends()
            selected_trend = random.choice(trends) if trends else "technology innovation"
            
            web_content = search_web_content(selected_trend)
            
            if SDK_TYPE == "new":
                client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
            else:
                genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            
            prompt = f"""
            ACT AS: An expert technology analyst creating informative content for Arabic-speaking audience.

            TOPIC: "{selected_trend}"
            CONTEXT: "{web_content}"

            TASK: Create informative technology content in ARABIC with TWO parts:

            PART 1: IMAGE_TEXT
            - A concise, factual statement in Arabic (under 12 words)
            - Should present valuable information, not advice
            - No emojis, just clear factual text
            - Examples: "معالجات الجيل الجديد تستهلك طاقة أقل بنسبة 40%" | "شاشات OLED توفر تبايناً أفضل من LCD"

            PART 2: DETAILED_CONTENT
            - Direct, informative explanation in Arabic (no greetings)
            - Present facts, specifications, or technical information
            - Use clear paragraph breaks for readability
            - Include 5-7 relevant Arabic hashtags at the end
            - Entirely in Arabic, professional tone

            FORMAT YOUR RESPONSE EXACTLY LIKE THIS:

            IMAGE_TEXT: [Your factual statement in Arabic here]
            DETAILED_CONTENT: [Your detailed informative content in Arabic here]

            Create content about {selected_trend}:
            """
            
            if SDK_TYPE == "new":
                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=prompt,
                )
                response_text = response.text
            else:
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(prompt)
                response_text = response.text
            
            response_text = response_text.strip()
            
            post_data = {}
            lines = response_text.split('\n')
            
            image_text_found = False
            detailed_content_lines = []
            
            for line in lines:
                if line.startswith('IMAGE_TEXT:'):
                    post_data['image_text'] = line.replace('IMAGE_TEXT:', '').strip()
                    image_text_found = True
                elif line.startswith('DETAILED_CONTENT:'):
                    content_start = line.replace('DETAILED_CONTENT:', '').strip()
                    if content_start:
                        detailed_content_lines.append(content_start)
                elif image_text_found and 'detailed_content' not in post_data:
                    if line.strip() == '' and not detailed_content_lines:
                        continue
                    detailed_content_lines.append(line)
            
            if detailed_content_lines:
                post_data['detailed_content'] = '\n'.join(detailed_content_lines).strip()
            
            if 'image_text' in post_data and 'detailed_content' in post_data:
                if is_duplicate_content(post_data['image_text']):
                    retry_count += 1
                    continue
                
                if '#' not in post_data['detailed_content']:
                    retry_count += 1
                    continue
                
                return post_data
            else:
                raise Exception("Invalid response format from Gemini")
            
        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                break
            time.sleep(2)
    
    fallback_posts = [
        {
            'image_text': "معالجات الجيل الخامس توفر أداءً أفضل باستهلاك طاقة أقل",
            'detailed_content': "معالجات الجيل الخامس من Intel و AMD تقدم تحسينات كبيرة في الأداء مع تقليل استهلاك الطاقة بنسبة تصل إلى 40% مقارنة بالجيل السابق.\n\nهذه المعالجات تدعم تقنيات الذكاء الاصطناعي المتقدمة وتوفر أداءً ممتازاً في الألعاب والمهام الإنتاجية.\n\nالتطور المستمر في هندسة المعالجات يمثل قفزة تقنية مهمة في عالم الحواسيب.\n\n#تقنية #معالجات #حواسيب #تكنولوجيا #أداء"
        },
        {
            'image_text': "شاشات OLED تتفوق على LCD في التباين ودقة الألوان",
            'detailed_content': "شاشات OLED توفر تبايناً لا نهائياً ودقة ألوان ممتازة نظراً لقدرة كل بكسل على الإنارة بشكل مستقل.\n\nهذه التقنية تستهلك طاقة أقل عندما تعرض محتوى داكن، وتوفر زوايا مشاهدة أوسع من شاشات LCD التقليدية.\n\nالتطور في تقنيات العرض continues to provide better viewing experiences for users.\n\n#شاشات #OLED #تكنولوجيا #عرض #ألوان"
        },
        {
            'image_text': "التخزين SSD أسرع 10 مرات من الأقراص الصلبة التقليدية",
            'detailed_content': "وحدات التخزين SSD توفر سرعات قراءة وكتابة تصل إلى 10 أضعاف速度 الأقراص الصلبة التقليدية، مما يقلل أوقات التحميل بشكل كبير.\n\nهذه التقنية لا تحتوي على أجزاء متحركة، مما يجعلها أكثر موثوقية واستهلاكاً أقل للطاقة.\n\nالتحول إلى التخزين SSD يمثل واحدة من أهم ترقيات الأداء لأي حاسوب.\n\n#تخزين #SSD #أداء #تقنية #ترقيات"
        }
    ]
    
    non_duplicate_posts = [
        p for p in fallback_posts 
        if not is_duplicate_content(p['image_text'])
    ]
    
    if non_duplicate_posts:
        return random.choice(non_duplicate_posts)
    else:
        return random.choice(fallback_posts)

def get_pixabay_image():
    """Get a random tech-related image from Pixabay"""
    try:
        api_key = os.environ.get("PIXABAY_KEY")
        if not api_key:
            return None
            
        categories = ["technology", "computer", "laptop", "smartphone", "gadgets",
                     "electronics", "pc gaming", "mobile", "tech", "innovation",
                     "coding", "programming", "digital", "cyber", "network"]
        category = random.choice(categories)
        
        url = "https://pixabay.com/api/"
        params = {
            "key": api_key,
            "q": category,
            "image_type": "photo",
            "orientation": "horizontal",
            "per_page": 20,
            "safesearch": "true"
        }
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data['hits']:
                image_data = random.choice(data['hits'])
                image_url = image_data["largeImageURL"]
                img_response = requests.get(image_url, timeout=15)
                return BytesIO(img_response.content)
        return None
            
    except Exception as e:
        return None

def create_tech_image(image_text):
    """Create tech-themed image with custom Arabic font"""
    width, height = 1200, 1200
    
    image_bytes = get_pixabay_image()
    
    if image_bytes:
        try:
            background = Image.open(image_bytes)
            background = background.resize((width, height), Image.LANCZOS)
            enhancer = ImageEnhance.Brightness(background)
            background = enhancer.enhance(0.7)
        except Exception as e:
            tech_colors = ['#0066cc', '#0077dd', '#0088ee', '#0099ff', '#00aaff']
            bg_color = random.choice(tech_colors)
            background = Image.new('RGB', (width, height), color=bg_color)
    else:
        tech_colors = ['#0066cc', '#0077dd', '#0088ee', '#0099ff', '#00aaff']
        bg_color = random.choice(tech_colors)
        background = Image.new('RGB', (width, height), color=bg_color)
    
    draw = ImageDraw.Draw(background)
    
    # Try to load Arabic-friendly fonts
    font_paths = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]
    
    font_size = 56
    tip_font = None
    
    for font_path in font_paths:
        try:
            tip_font = ImageFont.truetype(font_path, font_size)
            break
        except (IOError, OSError):
            continue
    
    if tip_font is None:
        tip_font = ImageFont.load_default()
    
    # Adjust text wrapping for Arabic
    max_chars_per_line = 20
    wrapped_text = textwrap.fill(image_text, width=max_chars_per_line)
    
    # Calculate text position
    bbox = draw.textbbox((0, 0), wrapped_text, font=tip_font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Semi-transparent background
    padding = 40
    draw.rectangle([
        x - padding, y - padding,
        x + text_width + padding, y + text_height + padding
    ], fill=(0, 0, 0, 180))
    
    # Draw text
    draw.text((x, y), wrapped_text, fill=(255, 255, 255), font=tip_font, align='center')
    
    output_buffer = BytesIO()
    background.save(output_buffer, format="JPEG", quality=95)
    return output_buffer.getvalue()

def post_to_facebook(image_data, post_data):
    """Post the image to Facebook Page"""
    try:
        page_id = os.environ.get("FB_PAGE_ID")
        access_token = os.environ.get("FB_PAGE_TOKEN")
        
        if not page_id or not access_token:
            return False
        
        url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
        
        caption = post_data['detailed_content']
        
        files = {'source': ('tech_info.jpg', image_data, 'image/jpeg')}
        data = {'message': caption, 'access_token': access_token}
        
        response = requests.post(url, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            save_posted_content(post_data['image_text'])
            return True
        else:
            return False
            
    except Exception as e:
        return False

def main():
    """Main function to run the entire process"""
    # Check environment variables
    required_env_vars = ["GEMINI_API_KEY", "PIXABAY_KEY", "FB_PAGE_ID", "FB_PAGE_TOKEN"]
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    
    if missing_vars:
        return
    
    # Generate tech content
    post_data = generate_tech_content()
    
    # Create image
    final_image = create_tech_image(post_data['image_text'])
    
    # Post to Facebook
    success = post_to_facebook(final_image, post_data)

if __name__ == "__main__":
    main()