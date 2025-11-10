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

# File to store posted content for duplication check - Use current working directory
POST_HISTORY_FILE = os.path.join(os.getcwd(), "posted_content.json")

# Content parameters for variety
TOPICS = [
    "grammar rules",
    "vocabulary building", 
    "speaking practice",
    "listening skills",
    "pronunciation tips"
]

ISSUES = [
    "common mistakes",
    "learning challenges",
    "practice problems",
    "understanding difficulties",
    "communication barriers"
]

METHODS = [
    "daily practice",
    "immersive learning",
    "structured study",
    "conversation practice",
    "multimedia resources"
]

BENEFITS = [
    "improved fluency",
    "better communication",
    "career opportunities",
    "cultural understanding",
    "academic success"
]

TIPS = [
    "quick tips",
    "effective strategies",
    "simple techniques",
    "proven methods",
    "easy approaches"
]

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
        print(f"Looking for history file at: {POST_HISTORY_FILE}")
        if os.path.exists(POST_HISTORY_FILE):
            with open(POST_HISTORY_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
                    print(f"Loaded {len(data)} items from history")
                    return data
                else:
                    print("History file is empty")
                    return []
        else:
            print("History file does not exist, starting fresh")
            return []
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error loading history file: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error loading history: {e}")
        return []

def save_posted_content(content_text):
    """Save posted content to history"""
    try:
        posted_content = load_posted_content()
        
        # Create a unique hash of the content text
        content_hash = hashlib.md5(content_text.encode()).hexdigest()
        
        if content_hash not in posted_content:
            posted_content.append(content_hash)
            # Ensure directory exists
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
        is_duplicate = content_hash in posted_content
        if is_duplicate:
            print(f"Duplicate content detected: {content_text[:30]}...")
        return is_duplicate
    except Exception as e:
        print(f"Error checking duplicate: {e}")
        return False

def generate_content_combination():
    """Generate a unique content combination from parameters"""
    max_attempts = 10
    
    for attempt in range(max_attempts):
        # Randomly select parameters
        topic = random.choice(TOPICS)
        issue = random.choice(ISSUES)
        method = random.choice(METHODS)
        benefit = random.choice(BENEFITS)
        tip_type = random.choice(TIPS)
        
        # Create unique content identifier
        content_id = f"{topic}_{issue}_{method}_{benefit}_{tip_type}"
        content_hash = hashlib.md5(content_id.encode()).hexdigest()
        
        # Check if this combination was used before
        posted_content = load_posted_content()
        if content_hash not in posted_content:
            print(f"Generated new content combination: {content_id}")
            return {
                'topic': topic,
                'issue': issue,
                'method': method,
                'benefit': benefit,
                'tip_type': tip_type,
                'content_id': content_id
            }
        else:
            print(f"Combination already used, trying again... (attempt {attempt + 1})")
    
    # If all combinations are exhausted, return a random one
    print("All combinations exhausted, using fallback")
    return {
        'topic': random.choice(TOPICS),
        'issue': random.choice(ISSUES),
        'method': random.choice(METHODS),
        'benefit': random.choice(BENEFITS),
        'tip_type': random.choice(TIPS),
        'content_id': 'fallback_' + str(random.randint(1000, 9999))
    }

def generate_english_content():
    """Generate informative English learning content using Gemini"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Get unique content combination
            content_combo = generate_content_combination()
            
            print(f"Generating content with Gemini API...")
            
            if SDK_TYPE == "new":
                client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
            else:
                genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            
            prompt = f"""
            ACT AS: An expert English teacher creating short, valuable content for Arabic-speaking learners.

            CONTEXT PARAMETERS:
            - Topic: {content_combo['topic']}
            - Focus: {content_combo['issue']} 
            - Method: {content_combo['method']}
            - Benefit: {content_combo['benefit']}
            - Style: {content_combo['tip_type']}

            TASK: Create SHORT, informative English learning content in ARABIC with TWO parts:

            PART 1: IMAGE_TEXT (8-12 words max)
            - A concise, factual statement in Arabic
            - Focus on practical English learning insight
            - No emojis, just clear factual text

            PART 2: DETAILED_CONTENT (2-3 short paragraphs max)
            - Brief, direct explanation in Arabic
            - Focus on practical value
            - Include 3-5 relevant Arabic hashtags at the end
            - Keep it concise and actionable

            FORMAT YOUR RESPONSE EXACTLY LIKE THIS:

            IMAGE_TEXT: [Your short factual statement in Arabic here]
            DETAILED_CONTENT: [Your brief informative content in Arabic here]

            Make it SHORT and VALUABLE:
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
            print("Received response from Gemini")
            
            post_data = {}
            lines = response_text.split('\n')
            
            image_text_found = False
            detailed_content_lines = []
            
            for line in lines:
                if line.startswith('IMAGE_TEXT:'):
                    post_data['image_text'] = line.replace('IMAGE_TEXT:', '').strip()
                    image_text_found = True
                    print(f"Found image text: {post_data['image_text']}")
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
                # Check for duplicates
                if is_duplicate_content(post_data['image_text']):
                    print("Duplicate content detected, generating new combination...")
                    retry_count += 1
                    continue
                
                # Save the content combination to avoid reuse
                save_posted_content(content_combo['content_id'])
                save_posted_content(post_data['image_text'])
                
                return post_data
            else:
                print("Invalid response format from Gemini")
                raise Exception("Invalid response format from Gemini")
            
        except Exception as e:
            print(f"Error generating content (attempt {retry_count + 1}): {e}")
            retry_count += 1
            if retry_count >= max_retries:
                break
            time.sleep(2)
    
    # Fallback content with parameter combinations
    print("Using fallback content")
    fallback_combinations = [
        {
            'image_text': "الممارسة اليومية تحسن الطلاقة بشكل ملحوظ",
            'detailed_content': "خصص 15 دقيقة يومياً للتحدث باللغة الإنجليزية. الاستمرارية أهم من المدة.\n\nحاول استخدام جمل جديدة كل يوم لبناء ثقتك.\n\n#تعلم_الإنجليزية #طلاقة #ممارسة"
        },
        {
            'image_text': "تعلم 5 كلمات يومياً يوسع مفرداتك بفعالية",
            'detailed_content': "ركز على الكلمات الشائعة واستخدمها في جمل عملية. التكرار يساعد على التذكر.\n\nاكتب الجمل في دفتر للمراجعة لاحقاً.\n\n#مفردات #كلمات #إنجليزية"
        },
        {
            'image_text': "الاستماع اليومي يحسن الفهم والنطق معاً",
            'detailed_content': "استمع إلى محتوى إنجليزي أثناء التنقل أو العمل. التعرض المستمر أساسي.\n\nابدأ بمحتوى بطيء ثم تدرج إلى السرعة الطبيعية.\n\n#استماع #نطق #فهم"
        },
        {
            'image_text': "الأخطاء جزء من عملية التعلم الناجح",
            'detailed_content': "لا تخشى الأخطاء عند التحدث. كل متعلم يمر بهذه المرحلة.\n\nالتصحيح الذاتي يحسن الدقة مع الوقت.\n\n#تعلم #أخطاء #تقدم"
        },
        {
            'image_text': "التكرار المتباعد يعزز حفظ المفردات",
            'detailed_content': "راجع الكلمات الجديدة بعد يوم، ثم أسبوع، ثم شهر. هذه الطريقة علمياً الأفضل.\n\nاستخدم تطبيقات التكرار المتباعد لتنظيم المراجعات.\n\n#ذاكرة #مراجعة #مفردات"
        }
    ]
    
    # Find non-duplicate fallback
    non_duplicate_posts = [
        p for p in fallback_combinations 
        if not is_duplicate_content(p['image_text'])
    ]
    
    if non_duplicate_posts:
        selected_post = random.choice(non_duplicate_posts)
        # Mark as used
        save_posted_content(selected_post['image_text'])
        print("Using non-duplicate fallback content")
        return selected_post
    else:
        # If all fallbacks are used, use one but mark it
        selected_post = random.choice(fallback_combinations)
        save_posted_content(selected_post['image_text'])
        print("Using duplicate fallback content (all options exhausted)")
        return selected_post

def get_pixabay_image():
    """Get a random education/learning-related image from Pixabay"""
    try:
        api_key = os.environ.get("PIXABAY_KEY")
        if not api_key:
            print("Pixabay API key not found")
            return None
            
        categories = ["education", "learning", "study", "books", "school",
                     "university", "reading", "writing", "language", "english",
                     "classroom", "student", "teacher", "notebook", "knowledge"]
        category = random.choice(categories)
        
        print(f"Searching Pixabay for: {category}")
        
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
                print(f"Downloading image from: {image_url}")
                img_response = requests.get(image_url, timeout=15)
                print("Successfully downloaded Pixabay image")
                return BytesIO(img_response.content)
            else:
                print("No images found on Pixabay")
        else:
            print(f"Pixabay API error: {response.status_code}")
        return None
            
    except Exception as e:
        print(f"Error getting Pixabay image: {e}")
        return None

def get_random_box_color():
    """Generate random semi-transparent background colors"""
    colors = [
        (30, 144, 255, 180),   # Dodger Blue
        (46, 139, 87, 180),    # Sea Green
        (147, 112, 219, 180),  # Medium Purple
        (220, 20, 60, 180),    # Crimson
        (255, 140, 0, 180),    # Dark Orange
        (32, 178, 170, 180),   # Light Sea Green
        (199, 21, 133, 180),   # Medium Violet Red
        (25, 25, 112, 180),    # Midnight Blue
        (139, 69, 19, 180),    # Saddle Brown
        (47, 79, 79, 180),     # Dark Slate Gray
    ]
    color = random.choice(colors)
    print(f"Using box color: {color}")
    return color

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
            print("Using Pixabay background image")
        except Exception as e:
            # Fallback to solid color background
            education_colors = ['#2E8B57', '#4682B4', '#5F9EA0', '#DA70D6', '#20B2AA']
            bg_color = random.choice(education_colors)
            background = Image.new('RGB', (width, height), color=bg_color)
            print(f"Using solid color background: {bg_color}")
    else:
        # Fallback to solid color background
        education_colors = ['#2E8B57', '#4682B4', '#5F9EA0', '#DA70D6', '#20B2AA']
        bg_color = random.choice(education_colors)
        background = Image.new('RGB', (width, height), color=bg_color)
        print(f"Using solid color background: {bg_color}")
    
    # Convert to RGBA for transparency support
    background = background.convert('RGBA')
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
    
    # Add semi-transparent background with random color
    padding = 40
    box_color = get_random_box_color()
    
    # Create a separate image for the box to handle transparency properly
    box_image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    box_draw = ImageDraw.Draw(box_image)
    box_draw.rectangle([
        x - padding, y - padding,
        x + text_width + padding, y + text_height + padding
    ], fill=box_color)
    
    # Composite the box onto the background
    background = Image.alpha_composite(background, box_image)
    
    # Redraw the text
    draw = ImageDraw.Draw(background)
    draw.text((x, y), wrapped_text, fill=(255, 255, 255), font=font, align='center')
    
    # Convert back to RGB for JPEG saving
    background = background.convert('RGB')
    
    # Convert to bytes
    output_buffer = BytesIO()
    background.save(output_buffer, format="JPEG", quality=95)
    print("Image created successfully")
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
        
        print("Posting to Facebook...")
        response = requests.post(url, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
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
    print("Starting English Learning Content Generator...")
    print(f"Current working directory: {os.getcwd()}")
    
    # Check environment variables
    required_env_vars = ["GEMINI_API_KEY", "PIXABAY_KEY", "FB_PAGE_ID", "FB_PAGE_TOKEN"]
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"Missing environment variables: {', '.join(missing_vars)}")
        return
    
    print("All environment variables are set")
    
    # Generate English learning content
    print("Generating English learning content...")
    post_data = generate_english_content()
    print("Generated English learning content")
    print(f"Image text: {post_data['image_text']}")
    print(f"Content preview: {post_data['detailed_content'][:100]}...")
    
    # Create image
    print("Creating image...")
    final_image = create_english_learning_image(post_data['image_text'])
    print("Created English learning image")
    
    # Post to Facebook
    print("Posting to Facebook...")
    success = post_to_facebook(final_image, post_data)
    
    if success:
        print("Process completed successfully")
    else:
        print("Process completed with errors")

if __name__ == "__main__":
    main()