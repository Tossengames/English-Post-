#!/usr/bin/env python3
"""
Tech Tips Generator: Generate VARIED content for tech enthusiasts on PC, mobile, gadgets, and technology trends.
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
    print("✅ Using new Google GenAI SDK")
    SDK_TYPE = "new"
except ImportError:
    try:
        # Fallback to old import style
        import google.generativeai as genai
        print("✅ Using old Google Generative AI SDK")
        SDK_TYPE = "old"
    except ImportError as e:
        print(f"❌ Failed to import Google AI libraries: {e}")
        print("💡 Please install the required package:")
        print("   pip install google-genai  # For new SDK")
        print("   or")
        print("   pip install google-generativeai  # For old SDK")
        exit(1)

# Try to import googlesearch for real web searches
try:
    from googlesearch import search as google_search
    GOOGLE_SEARCH_AVAILABLE = True
    print("✅ Using googlesearch-python for web searches")
except ImportError:
    GOOGLE_SEARCH_AVAILABLE = False
    print("❌ googlesearch-python not available")

# File to store posted tips for duplication check - using absolute path
POST_HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "posted_quotes.json")

def load_posted_tips():
    """Load history of posted tips to avoid duplicates"""
    try:
        print(f"Looking for history file at: {POST_HISTORY_FILE}")
        if os.path.exists(POST_HISTORY_FILE):
            with open(POST_HISTORY_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
                else:
                    return []
        return []
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error loading history file: {e}")
        return []

def save_posted_tip(tip_text):
    """Save a posted tip to history using its main text"""
    try:
        posted_tips = load_posted_tips()
        
        # Create a unique hash of the main tip text to identify duplicates
        tip_hash = hashlib.md5(tip_text.encode()).hexdigest()
        
        # Add to history if not already there
        if tip_hash not in posted_tips:
            posted_tips.append(tip_hash)
            # Ensure directory exists
            os.makedirs(os.path.dirname(POST_HISTORY_FILE), exist_ok=True)
            with open(POST_HISTORY_FILE, 'w') as f:
                json.dump(posted_tips, f)
            print(f"✅ Saved tip to history: {tip_text[:50]}...")
            return True
        else:
            print(f"❌ Tip already exists in history: {tip_text[:50]}...")
            return False
    except Exception as e:
        print(f"❌ Error saving to history: {e}")
        return False

def is_duplicate_tip(tip_text):
    """Check if a tip has already been posted"""
    try:
        posted_tips = load_posted_tips()
        tip_hash = hashlib.md5(tip_text.encode()).hexdigest()
        is_dup = tip_hash in posted_tips
        if is_dup:
            print(f"❌ Duplicate detected: {tip_text[:50]}...")
        else:
            print(f"✅ New tip: {tip_text[:50]}...")
        return is_dup
    except Exception as e:
        print(f"❌ Error checking duplicate: {e}")
        return False

def get_google_trends():
    """Get trending topics using reliable fallback method - TECH FOCUSED"""
    try:
        # Use a more reliable approach for trend discovery - TECH FOCUSED
        trending_keywords = [
            "smartphone", "PC gaming", "laptop reviews", "tech gadgets", 
            "AI technology", "mobile apps", "wireless earbuds", "smart home",
            "gaming PC", "tech news", "Android tips", "iOS features",
            "computer hardware", "software updates", "cybersecurity tips",
            "productivity apps", "tech reviews", "wearable technology"
        ]
        
        all_trends = []
        for keyword in trending_keywords:
            try:
                print(f"🔍 Searching for trends: {keyword}")
                
                # Perform Google search with correct parameters
                results = list(google_search(
                    keyword, 
                    num_results=5,
                    pause=2.0,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                ))
                
                # Extract potential trends from URLs
                for url in results:
                    if any(x in url for x in ['trend', 'news', 'blog', 'article', 'report', 'review']):
                        # Extract meaningful words from URL
                        url_parts = url.split('/')
                        for part in url_parts:
                            if len(part) > 3 and '-' in part and any(c.isalpha() for c in part):
                                words = part.split('-')
                                for word in words:
                                    if (len(word) > 4 and word.isalpha() and 
                                        word.lower() not in ['https', 'www', 'com', 'org', 'net', 'html', 'php']):
                                        all_trends.append(word)
                
                time.sleep(1)  # Be polite with requests
                
            except Exception as e:
                print(f"❌ Error searching for {keyword}: {e}")
                continue
        
        # Filter and return unique trends
        unique_trends = list(set([t for t in all_trends if 3 < len(t) < 20]))
        if unique_trends:
            print(f"✅ Found {len(unique_trends)} potential trends")
            return unique_trends[:10]
        
        return get_fallback_trends()
            
    except Exception as e:
        print(f"❌ Error fetching trends: {e}")
        return get_fallback_trends()

def get_fallback_trends():
    """Get reliable fallback trending topics - TECH FOCUSED"""
    fallback_trends = [
        # PC & Hardware
        "gaming PC", "processor comparison", "graphics cards", "RAM upgrade",
        "SSD vs HDD", "PC building", "laptop specs", "motherboard",
        "cooling systems", "PC performance", "overclocking", "PC accessories",
        # Mobile & Apps
        "smartphone camera", "battery life", "mobile gaming", "app recommendations",
        "iOS vs Android", "phone security", "mobile photography", "app development",
        "wearable tech", "smartwatch features", "mobile accessories", "phone reviews",
        # General Tech
        "AI technology", "smart home", "wireless charging", "tech gadgets",
        "cybersecurity", "data privacy", "cloud storage", "tech innovations",
        "productivity tools", "software updates", "tech tips", "digital lifestyle"
    ]
    selected = random.sample(fallback_trends, min(8, len(fallback_trends)))
    print(f"✅ Using fallback trends: {selected}")
    return selected

def search_web_content(topic):
    """Perform real web search for the topic using Google Search"""
    try:
        if not GOOGLE_SEARCH_AVAILABLE:
            print("❌ Google search not available, using fallback content")
            return f"Tech experts are discussing {topic} as an important topic for technology enthusiasts."
        
        print(f"🔍 Performing real web search for: {topic}")
        
        # Perform Google search with correct parameters
        search_query = f"{topic} technology tips gadgets 2024"
        results = list(google_search(
            search_query, 
            num_results=3,
            pause=2.0,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ))
        
        # Create meaningful content from search results
        content_parts = []
        content_parts.append(f"Recent tech discussions show that {topic} is a relevant topic right now.")
        
        if results:
            content_parts.append("Tech sources indicate several important points:")
            content_parts.append(f"- {topic} is gaining attention among tech professionals")
            content_parts.append(f"- This topic connects to broader technology trends and innovation")
            
            # Mention that we found relevant sources
            domain_count = len(set(url.split('/')[2] for url in results if len(url.split('/')) > 2))
            content_parts.append(f"Based on analysis of {domain_count} sources, this is a valuable area for tech education.")
        else:
            content_parts.append("This tech concept is gaining attention across technology communities and discussions.")
        
        content_parts.append("Tech experts and reviewers are discussing the importance of this topic.")
        
        return " ".join(content_parts)
        
    except Exception as e:
        print(f"❌ Error in web search: {e}")
        return f"Recent discussions about {topic} indicate it's a significant technology topic. Experts are highlighting its importance for tech enthusiasts and digital lifestyle."

def generate_tech_post():
    """Generate a VARIED tech post using Gemini. No rigid templates."""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Get real trending topics
            trends = get_google_trends()
            selected_trend = random.choice(trends) if trends else "technology innovation"
            
            # Perform real web search about this trend
            web_content = search_web_content(selected_trend)
            print(f"🎯 Selected trend: {selected_trend}")
            print(f"🔍 Web context: {web_content[:100]}...")
            
            # Initialize client based on available SDK
            if SDK_TYPE == "new":
                client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
            else:
                genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            
            # REVISED PROMPT: Enforces formatting, variety, and hashtags - IN ARABIC
            prompt = f"""
            ACT AS: A knowledgeable and engaging tech expert. You are creating a social media post for your Arabic-speaking followers.

            TOPIC/TREND: "{selected_trend}"
            CONTEXT: "{web_content}"

            TASK: Create a social media post in ARABIC without any greeting with TWO distinct parts:

            PART 1: IMAGE_HOOK
            - This is a SHORT, punchy, and compelling one-line statement in ARABIC.
            - It must be under 10 words.
            - It must be strong enough to stand alone on an image.
            - **NO EMOJIS.** Just plain text.
            - Examples: "الهاتف الذكي هو امتداد لإبداعك" | "البطارية تدوم طويلاً بالإعدادات الصحيحة"

            PART 2: FULL_CAPTION
            - This is the full social media caption in ARABIC that expands on the hook.
            - **VARY YOUR OPENING:** Use different openings in Arabic.
            - **USE LINE BREAKS:** Make it easy to read. Use empty lines to separate ideas.
            - Include a natural Call-To-Action in Arabic (e.g., ask for a like, share, or follow).
            - Include a specific question in Arabic to prompt comments.
            - **MUST INCLUDE 5-7 RELEVANT ARABIC HASHTAGS at the end.**
            - **WRITE ENTIRELY IN ARABIC.**

            FORMAT YOUR RESPONSE EXACTLY LIKE THIS:

            IMAGE_HOOK: [Your short, emoji-free hook in Arabic here]
            FULL_CAPTION: [Your engaging full caption in Arabic here]

            Now create a post in Arabic about {selected_trend}:
            """
            
            # Generate content based on available SDK
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
            print(f"Gemini response:\n{response_text}")
            
            # Parse the response
            post_data = {}
            lines = response_text.split('\n')
            
            image_hook_found = False
            full_caption_lines = []
            
            for line in lines:
                if line.startswith('IMAGE_HOOK:'):
                    post_data['image_text'] = line.replace('IMAGE_HOOK:', '').strip()
                    image_hook_found = True
                elif line.startswith('FULL_CAPTION:'):
                    # Start collecting the caption after this line
                    caption_start = line.replace('FULL_CAPTION:', '').strip()
                    if caption_start:  # If there's text on the same line
                        full_caption_lines.append(caption_start)
                elif image_hook_found and 'full_post' not in post_data:
                    # Check if we are in the caption section
                    if line.strip() == '' and not full_caption_lines:
                        continue  # Skip empty lines before caption starts
                    full_caption_lines.append(line)
            
            # Join the caption lines to form the full post
            if full_caption_lines:
                post_data['full_post'] = '\n'.join(full_caption_lines).strip()
            
            # Check if we have both parts and if the hook is a duplicate
            if 'image_text' in post_data and 'full_post' in post_data:
                if is_duplicate_tip(post_data['image_text']):
                    print(f"🔄 Generated hook is a duplicate, trying again... (Attempt {retry_count + 1}/{max_retries})")
                    retry_count += 1
                    continue
                
                # Final check: Ensure hashtags are present
                if '#' not in post_data['full_post']:
                    print("🔄 Generated caption lacks hashtags, trying again...")
                    retry_count += 1
                    continue
                
                return post_data
            else:
                raise Exception("Invalid response format from Gemini. Missing IMAGE_HOOK or FULL_CAPTION.")
            
        except Exception as e:
            print(f"❌ Error generating tech post: {e}")
            retry_count += 1
            if retry_count >= max_retries:
                break
            time.sleep(2)  # Wait before retrying
    
    # Fallback if all retries fail - IN ARABIC
    print("🔄 Using Arabic fallback after Gemini failures...")
    fallback_posts = [
        {
            'image_text': "اختر المعالج المناسب لاحتياجاتك.",
            'full_post': "إليك دليل سريع لاختيار المعالج المثالي: المعالجات متعددة الأنوية أفضل للألعاب والمهام المتعددة، بينما سرعة الساعة الأعلى أفضل للمهام الفردية.\n\nلا تنخدع بعدد الأنوية فقط - انظر إلى الأداء الفعلي في التطبيقات التي تستخدمها.\n\nما نوع المعالج الذي تستخدمه حالياً؟ شارك تجربتك في التعليقات! 💻\n\nاتبع للمزيد من النصائح التقنية والحيل الذكية. #تقنية #معالجات #أجهزة_كمبيوتر #نصائح_تقنية #تكنولوجيا"
        },
        {
            'image_text': "بطارية هاتفك تدوم طويلاً بهذه الحيلة.",
            'full_post': "خفض سطوع الشاشة بنسبة 20% فقط يمكن أن يضيف ساعات إضافية لعمر البطارية. أغلق التطبيقات التي تعمل في الخلفية وقلل من إشعارات الدفع.\n\nالشحن من 20% إلى 80% هو الأمثل لصحة البطارية على المدى الطويل.\n\nما هي أفضل طريقة وجدتها لإطالة عمر بطارية هاتفك؟ شارك نصائحك! 🔋\n\nاحفظ هذا المنشور للرجوع إليه لاحقاً! #بطارية #هواتف #نصائح_تقنية #حيل_ذكية #تقنية"
        },
        {
            'image_text': "الأمان الرقمي يبدأ بكلمة مرور قوية.",
            'full_post': "استخدم مزيجاً من الأحرف الكبيرة والصغيرة، الأرقام، والرموز الخاصة. تجنب استخدام المعلومات الشخصية أو الكلمات الشائعة.\n\nميزة المصادقة الثنائية (2FA) تضيف طبقة حماية إضافية مهمة جداً.\n\nما هي أفضل ممارسات الأمان التي تتبعها لحماية حساباتك؟ شارك تجربتك! 🔒\n\nانشر المعرفة - شارك هذا المنشور مع أصدقائك! #أمان_رقمي #حماية #كلمات_مرور #تقنية #نصائح"
        }
    ]
    
    # Filter out duplicates from fallback posts
    non_duplicate_posts = [
        p for p in fallback_posts 
        if not is_duplicate_tip(p['image_text'])
    ]
    
    if non_duplicate_posts:
        return random.choice(non_duplicate_posts)
    else:
        # If all fallbacks are duplicates, return a random one anyway
        print("⚠️ All fallback posts are duplicates, using random one")
        return random.choice(fallback_posts)

def get_pixabay_image():
    """Get a random image from Pixabay API - TECH FOCUSED CATEGORIES"""
    try:
        api_key = os.environ.get("PIXABAY_KEY")
        if not api_key:
            print("❌ PIXABAY_KEY not found in environment variables")
            return None
            
        # TECH FOCUSED CATEGORIES
        categories = ["technology", "computer", "laptop", "smartphone", "gadgets",
                     "electronics", "pc gaming", "mobile", "tech", "innovation",
                     "coding", "programming", "digital", "cyber", "network",
                     "software", "hardware", "ai", "robot", "future"]
        category = random.choice(categories)
        
        print(f"🌄 Searching Pixabay for: {category}")
        
        url = "https://pixabay.com/api/"
        params = {
            "key": api_key,
            "q": category,
            "image_type": "photo",
            "orientation": "horizontal",
            "per_page": 20,
            "safesearch": "true",
            "editors_choice": "true"
        }
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data['hits']:
                # Select a random image from the results
                image_data = random.choice(data['hits'])
                image_url = image_data["largeImageURL"]
                
                print(f"✅ Found Pixabay image: {image_url}")
                
                # Download the image
                img_response = requests.get(image_url, timeout=15)
                return BytesIO(img_response.content)
            else:
                print(f"❌ No images found for category: {category}")
                return None
        else:
            print(f"❌ Pixabay API error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error fetching image from Pixabay: {e}")
        return None

def create_tech_image(image_text):
    """Create tech-themed image with Pixabay background and text overlay"""
    width, height = 1200, 1200
    
    # Try to get a Pixabay image first
    image_bytes = get_pixabay_image()
    
    if image_bytes:
        try:
            # Open and process the Pixabay image
            background = Image.open(image_bytes)
            background = background.resize((width, height), Image.LANCZOS)
            
            # Apply a slight darkening filter for better text readability
            enhancer = ImageEnhance.Brightness(background)
            background = enhancer.enhance(0.7)  # Darken slightly
            
            print("✅ Using Pixabay background image")
            
        except Exception as e:
            print(f"❌ Error processing Pixabay image: {e}")
            # Fallback to solid color background
            tech_colors = [
                '#0066cc', '#0077dd', '#0088ee', '#0099ff', '#00aaff',
                '#3366cc', '#4477dd', '#5588ee', '#6699ff', '#77aaff',
                '#003366', '#004477', '#005588', '#006699', '#0077aa',
                '#6600cc', '#7700dd', '#8800ee', '#9900ff', '#aa00ff'
            ]
            bg_color = random.choice(tech_colors)
            background = Image.new('RGB', (width, height), color=bg_color)
            print("✅ Using fallback solid color background")
    else:
        # Fallback to solid color background
        tech_colors = [
            '#0066cc', '#0077dd', '#0088ee', '#0099ff', '#00aaff',
            '#3366cc', '#4477dd', '#5588ee', '#6699ff', '#77aaff',
            '#003366', '#004477', '#005588', '#006699', '#0077aa',
            '#6600cc', '#7700dd', '#8800ee', '#9900ff', '#aa00ff'
        ]
        bg_color = random.choice(tech_colors)
        background = Image.new('RGB', (width, height), color=bg_color)
        print("✅ Using fallback solid color background")
    
    # Create drawing context
    draw = ImageDraw.Draw(background)
    
    # Try to load font
    try:
        # Try to find a font that supports Arabic characters
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/System/Library/Fonts/Arial.ttf",
            "C:/Windows/Fonts/arial.ttf"
        ]
        
        tip_font = None
        for font_path in font_paths:
            try:
                tip_font = ImageFont.truetype(font_path, 62)
                print(f"✅ Using font: {font_path}")
                break
            except (IOError, OSError):
                continue
        
        if tip_font is None:
            tip_font = ImageFont.load_default()
            print("⚠️ Using default font (may not support Arabic well)")
            
    except Exception as e:
        print(f"❌ Error loading font: {e}")
        tip_font = ImageFont.load_default()
    
    # Wrap the main tip text
    max_chars_per_line = 22
    wrapped_tip = textwrap.fill(image_text, width=max_chars_per_line)
    
    # Calculate text position
    bbox = draw.textbbox((0, 0), wrapped_tip, font=tip_font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Generate random background color for text box 
    random_bg_color = (
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        180  # Alpha value for transparency
    )
    
    # Add semi-transparent background with random color for better readability
    padding = 40
    draw.rectangle([
        x - padding, y - padding,
        x + text_width + padding, y + text_height + padding
    ], fill=random_bg_color)
    
    # Draw main tip text
    draw.text((x, y), wrapped_tip, fill=(255, 255, 255), font=tip_font, align='center')
    
    # Convert to bytes
    output_buffer = BytesIO()
    background.save(output_buffer, format="JPEG", quality=95)
    return output_buffer.getvalue()

def post_to_facebook(image_data, post_data):
    """Post the image to Facebook Page with the AI-generated caption"""
    try:
        page_id = os.environ.get("FB_PAGE_ID")
        access_token = os.environ.get("FB_PAGE_TOKEN")
        
        if not page_id or not access_token:
            print("❌ Facebook credentials not found in environment variables")
            return False
        
        # Upload image to Facebook
        url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
        
        # Use the AI-generated full post as the caption
        caption = post_data['full_post']
        
        files = {'source': ('tech_tip.jpg', image_data, 'image/jpeg')}
        data = {'message': caption, 'access_token': access_token}
        
        response = requests.post(url, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            # Save to posted tips history to prevent duplicates (using the image hook)
            if save_posted_tip(post_data['image_text']):
                print(f"✅ Successfully posted to Facebook! Post ID: {result.get('id')}")
            else:
                print(f"⚠️ Posted to Facebook but failed to save to history: {result.get('id')}")
            return True
        else:
            print(f"❌ Facebook API error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error posting to Facebook: {e}")
        return False

def main():
    """Main function to run the entire process"""
    print("🚀 Starting tech tips content generation and posting process...")
    print(f"📁 History file location: {POST_HISTORY_FILE}")
    
    # Check environment variables
    required_env_vars = ["GEMINI_API_KEY", "PIXABAY_KEY", "FB_PAGE_ID", "FB_PAGE_TOKEN"]
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("💡 Please add missing variables to your GitHub Secrets")
        return
    
    # Load existing history to check functionality
    posted_tips = load_posted_tips()
    print(f"📊 Existing tips in history: {len(posted_tips)}")
    
    # Generate a varied tech post
    post_data = generate_tech_post()
    print("🎯 Generated tech post")
    print(f"🖼️  Image Hook: {post_data['image_text']}")
    print(f"📝 Full Caption: {post_data['full_post']}")
    
    # Create image with the short, clean hook
    final_image = create_tech_image(post_data['image_text'])
    print("🎨 Tech image created")
    
    # Post to Facebook
    success = post_to_facebook(final_image, post_data)
    
    if success:
        print("✅ Process completed successfully! The tech post has been shared.")
    else:
        print("❌ Process completed with errors")

if __name__ == "__main__":
    main()