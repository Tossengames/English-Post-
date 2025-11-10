#!/usr/bin/env python3
"""
English Learning Generator: Generate informative Arabic content about English learning, tips, and resources.
Creates images with text overlay and posts to Facebook Page.
"""

import os
import requests
import random
import textwrap
import json
import hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps
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

def load_arabic_font(font_size=56):
    """Try to load an Arabic-supported font with fallbacks"""
    arabic_font_paths = [
        # Common Arabic font paths on different systems
        "/usr/share/fonts/truetype/arabic_fonts/NotoNaskhArabic-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
        "/usr/share/fonts/truetype/fonts-arabeyes/ae_AlMateen.ttf",
        "C:/Windows/Fonts/arabtype.ttf",  # Windows Arabic font
        "C:/Windows/Fonts/trado.ttf",     # Windows Traditional Arabic
        "C:/Windows/Fonts/simplarab.ttf", # Windows Simplified Arabic
        "/System/Library/Fonts/GeezaPro.ttc",  # macOS Arabic font
        "/Library/Fonts/Arial Unicode MS.ttf", # macOS - has Arabic support
        "/Library/Fonts/Times New Roman.ttf",  # macOS - sometimes has Arabic
    ]
    
    for font_path in arabic_font_paths:
        try:
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, font_size)
        except (IOError, OSError):
            continue
    
    # Try to download a fallback Arabic font if none are available locally
    try:
        # Download Noto Sans Arabic font as fallback
        font_url = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansArabic/NotoSansArabic-Regular.ttf"
        response = requests.get(font_url, timeout=10)
        if response.status_code == 200:
            font_file = BytesIO(response.content)
            return ImageFont.truetype(font_file, font_size)
    except:
        pass
    
    # Ultimate fallback - try default fonts that might support Arabic
    try:
        return ImageFont.truetype("arial.ttf", font_size)
    except:
        try:
            return ImageFont.truetype("arialuni.ttf", font_size)  # Arial Unicode
        except:
            return ImageFont.load_default()

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

def get_english_learning_trends():
    """Get trending English learning topics"""
    try:
        trending_keywords = [
            "English grammar", "vocabulary building", "speaking practice", 
            "listening skills", "English pronunciation", "writing skills",
            "IELTS preparation", "TOEFL tips", "business English", 
            "conversational English", "English idioms", "phrasal verbs",
            "English for beginners", "advanced English", "daily English",
            "English fluency", "learning methods", "study techniques"
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
                    if any(x in url for x in ['learn', 'study', 'english', 'language', 'tips', 'method', 'technique']):
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
        
        return get_fallback_english_trends()
            
    except Exception as e:
        return get_fallback_english_trends()

def get_fallback_english_trends():
    """Get reliable fallback English learning topics"""
    fallback_trends = [
        "grammar rules", "vocabulary expansion", "speaking confidence",
        "listening comprehension", "pronunciation practice", "writing improvement",
        "IELTS strategies", "TOEFL preparation", "business communication",
        "daily conversation", "common idioms", "phrasal verbs usage",
        "beginner English", "advanced vocabulary", "fluency development",
        "study planning", "learning resources", "practice techniques"
    ]
    return random.sample(fallback_trends, min(8, len(fallback_trends)))

def search_english_content(topic):
    """Perform web search for English learning topic"""
    try:
        if not GOOGLE_SEARCH_AVAILABLE:
            return f"Language experts are discussing {topic} as an important aspect of English learning."
        
        search_query = f"{topic} English learning tips methods 2024"
        results = list(google_search(
            search_query, 
            num_results=3,
            pause=2.0,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ))
        
        content_parts = []
        content_parts.append(f"Recent discussions in English learning indicate that {topic} is currently a significant focus area.")
        
        if results:
            content_parts.append("Language learning research shows several key insights:")
            content_parts.append(f"- {topic} represents important language acquisition strategy")
            content_parts.append(f"- This area connects to broader effective learning methods")
            
            domain_count = len(set(url.split('/')[2] for url in results if len(url.split('/')) > 2))
            content_parts.append(f"Based on review of {domain_count} educational sources, this represents valuable learning insight.")
        else:
            content_parts.append("This learning area is receiving significant attention across educational discussions.")
        
        content_parts.append("Language teachers and learning experts are highlighting the importance of these methods.")
        
        return " ".join(content_parts)
        
    except Exception as e:
        return f"Current discussions about {topic} indicate it represents effective English learning approach. Experts are emphasizing its relevance for language acquisition."

def generate_english_content():
    """Generate informative English learning content using Gemini"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            trends = get_english_learning_trends()
            selected_trend = random.choice(trends) if trends else "English learning methods"
            
            web_content = search_english_content(selected_trend)
            
            if SDK_TYPE == "new":
                client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
            else:
                genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            
            prompt = f"""
            ACT AS: An expert English teacher and language learning specialist creating informative content for Arabic-speaking audience.

            TOPIC: "{selected_trend}"
            CONTEXT: "{web_content}"

            TASK: Create informative English learning content in ARABIC with TWO parts:

            PART 1: IMAGE_TEXT
            - A concise, factual statement in Arabic about English learning (under 12 words)
            - Should present valuable learning information, not advice
            - No emojis, just clear factual text
            - Examples: "الممارسة اليومية تحسن الطلاقة بنسبة 70%" | "تعلم 10 كلمات يومياً يوسع المفردات بشكل فعال"

            PART 2: DETAILED_CONTENT
            - Direct, informative explanation in Arabic about English learning
            - Present facts, learning strategies, or educational information
            - Use clear paragraph breaks for readability
            - Include 5-7 relevant Arabic hashtags about English learning at the end
            - Entirely in Arabic, professional educational tone

            FORMAT YOUR RESPONSE EXACTLY LIKE THIS:

            IMAGE_TEXT: [Your factual statement about English learning in Arabic here]
            DETAILED_CONTENT: [Your detailed informative content about English learning in Arabic here]

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
            'image_text': "الممارسة اليومية تحسن الطلاقة اللغوية بشكل ملحوظ",
            'detailed_content': "الدراسات تظهر أن الممارسة اليومية للغة الإنجليزية لمدة 30 دقيقة تحسن الطلاقة بنسبة تصل إلى 70% خلال 3 أشهر.\n\nالتكرار المنتظم يساعد في ترسيخ المفردات والقواعد في الذاكرة طويلة المدى، مما يسهل عملية التحدث التلقائي.\n\nالاستماع والمحادثة اليومية أكثر فعالية من الدراسة المكثفة غير المنتظمة.\n\n#تعلم_الإنجليزية #طلاقة #ممارسة #لغة #إنجليزية"
        },
        {
            'image_text': "تعلم 10 كلمات يومياً يوسع المفردات بشكل فعال",
            'detailed_content': "تعلم 10 كلمات إنجليزية جديدة يومياً يمكن أن يضيف أكثر من 3000 كلمة إلى مفرداتك خلال سنة واحدة.\n\nاستخدام الكلمات في جمل عملية ومراجعتها بشكل منتظم يساعد على تذكرها بشكل أفضل.\n\nتنوع المفردات يحسن الفهم والكتابة والتحدث باللغة الإنجليزية.\n\n#مفردات #كلمات #إنجليزية #تعلم #لغة"
        },
        {
            'image_text': "الاستماع اليومي يحسن الفهم والنطق معاً",
            'detailed_content': "الاستماع اليومي للمحتوى الإنجليزي لمدة 20 دقيقة يحسن مهارات الفهم السمعي والنطق بشكل متوازي.\n\nالتعرض المستمر للهجات المختلفة يساعد الدماغ على التعرف على الأنماط الصوتية وتحسين النطق.\n\nالبودكاست والأفلام والبرامج وسائل فعالة للاستماع اليومي.\n\n#استماع #نطق #فهم #إنجليزية #لغة"
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
    """Get a random education/learning-related image from Pixabay"""
    try:
        api_key = os.environ.get("PIXABAY_KEY")
        if not api_key:
            return None
            
        categories = ["education", "learning", "study", "books", "school",
                     "university", "reading", "writing", "language", "english",
                     "classroom", "student", "teacher", "notebook", "knowledge",
                     "literature", "grammar", "vocabulary", "communication"]
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

def create_english_learning_image(image_text):
    """Create education-themed image with proper Arabic text rendering"""
    width, height = 1200, 1200
    
    # Get background image
    image_bytes = get_pixabay_image()
    
    if image_bytes:
        try:
            background = Image.open(image_bytes)
            background = background.resize((width, height), Image.LANCZOS)
            # Apply a slight darkening filter for better text readability
            enhancer = ImageEnhance.Brightness(background)
            background = enhancer.enhance(0.7)
        except Exception as e:
            # Fallback to solid color background
            education_colors = ['#2E8B57', '#4682B4', '#5F9EA0', '#DA70D6', '#20B2AA']
            bg_color = random.choice(education_colors)
            background = Image.new('RGB', (width, height), color=bg_color)
    else:
        # Fallback to solid color background
        education_colors = ['#2E8B57', '#4682B4', '#5F9EA0', '#DA70D6', '#20B2AA']
        bg_color = random.choice(education_colors)
        background = Image.new('RGB', (width, height), color=bg_color)
    
    draw = ImageDraw.Draw(background)
    
    # Load Arabic-supported font
    font = load_arabic_font(56)
    
    # Adjust text wrapping for Arabic - fewer characters per line
    max_chars_per_line = 18
    wrapped_text = textwrap.fill(image_text, width=max_chars_per_line)
    
    # Calculate text position
    try:
        # Use textbbox for newer Pillow versions
        bbox = draw.textbbox((0, 0), wrapped_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except:
        # Fallback for older Pillow versions
        try:
            text_width, text_height = draw.textsize(wrapped_text, font=font)
        except:
            # Ultimate fallback
            text_width, text_height = 800, 200
    
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Add semi-transparent background for better text readability
    padding = 40
    draw.rectangle([
        x - padding, y - padding,
        x + text_width + padding, y + text_height + padding
    ], fill=(0, 0, 0, 180))  # Semi-transparent black background
    
    # Draw Arabic text
    draw.text((x, y), wrapped_text, fill=(255, 255, 255), font=font, align='center')
    
    # Convert to bytes
    output_buffer = BytesIO()
    background.save(output_buffer, format="JPEG", quality=95)
    return output_buffer.getvalue()

def post_to_facebook(image_data, post_data):
    """Post the image to Facebook Page"""
    try:
        page_id = os.environ.get("FB_PAGE_ID")
        access_token = os.environ.get("FB_PAGE_TOKEN")
        
        if not page_id or not access_token:
            print("Missing Facebook credentials")
            return False
        
        url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
        
        caption = post_data['detailed_content']
        
        files = {'source': ('english_learning.jpg', image_data, 'image/jpeg')}
        data = {'message': caption, 'access_token': access_token}
        
        response = requests.post(url, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            save_posted_content(post_data['image_text'])
            print("Successfully posted to Facebook")
            return True
        else:
            print(f"Facebook API error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error posting to Facebook: {e}")
        return False

def main():
    """Main function to run the entire process"""
    # Check environment variables
    required_env_vars = ["GEMINI_API_KEY", "PIXABAY_KEY", "FB_PAGE_ID", "FB_PAGE_TOKEN"]
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"Missing environment variables: {', '.join(missing_vars)}")
        return
    
    # Generate English learning content
    post_data = generate_english_content()
    print("Generated English learning content")
    print(f"Image text: {post_data['image_text']}")
    
    # Create image
    final_image = create_english_learning_image(post_data['image_text'])
    print("Created English learning image")
    
    # Post to Facebook
    success = post_to_facebook(final_image, post_data)
    
    if success:
        print("Process completed successfully")
    else:
        print("Process completed with errors")

if __name__ == "__main__":
    main()