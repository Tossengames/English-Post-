#!/usr/bin/env python3
"""
English Coach: Generate practical English learning tips and lessons with Gemini AI,
create images with text overlay in both English and Arabic, and post to Facebook Page.
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

# Try to import Arabic text processing libraries
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_SUPPORT = True
    print("✅ Arabic text support enabled")
except ImportError:
    ARABIC_SUPPORT = False
    print("⚠️ Arabic text support disabled - install arabic-reshaper and python-bidi")

# File to store posted tips for duplication check - using absolute path
POST_HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "posted_english_tips.json")

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

def save_posted_tip(tip_data):
    """Save a posted tip to history"""
    try:
        posted_tips = load_posted_tips()
        
        # Create a unique hash of the main tip to identify duplicates
        tip_hash = hashlib.md5(tip_data['main_tip'].encode()).hexdigest()
        
        # Add to history if not already there
        if tip_hash not in posted_tips:
            posted_tips.append(tip_hash)
            # Ensure directory exists
            os.makedirs(os.path.dirname(POST_HISTORY_FILE), exist_ok=True)
            with open(POST_HISTORY_FILE, 'w') as f:
                json.dump(posted_tips, f)
            print(f"✅ Saved tip to history: {tip_data['main_tip'][:50]}...")
            return True
        else:
            print(f"❌ Tip already exists in history: {tip_data['main_tip'][:50]}...")
            return False
    except Exception as e:
        print(f"❌ Error saving to history: {e}")
        return False

def is_duplicate_tip(tip_data):
    """Check if a tip has already been posted"""
    try:
        posted_tips = load_posted_tips()
        tip_hash = hashlib.md5(tip_data['main_tip'].encode()).hexdigest()
        is_dup = tip_hash in posted_tips
        if is_dup:
            print(f"❌ Duplicate detected: {tip_data['main_tip'][:50]}...")
        else:
            print(f"✅ New tip: {tip_data['main_tip'][:50]}...")
        return is_dup
    except Exception as e:
        print(f"❌ Error checking duplicate: {e}")
        return False

def generate_english_tip():
    """Generate a practical English learning tip using Gemini with Arabic translation"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Initialize client based on available SDK
            if SDK_TYPE == "new":
                client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
            else:
                genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            
            prompt = """
            Create ONE comprehensive English learning post with these components:

            MAIN_TIP: [A short, practical, actionable English learning tip - under 15 words]
            EXPLANATION: [1-2 sentences explaining why this tip works or how to implement it]
            EXAMPLE: [A clear example showing the tip in action]
            ARABIC_TIP: [Arabic translation of the main tip - نص عربي]
            ARABIC_EXPLANATION: [Arabic translation of the explanation - شرح عربي]
            HASHTAGS: [3-4 relevant hashtags in English]

            Focus on practical advice for:
            - Grammar rules and common mistakes
            - Vocabulary building techniques
            - Pronunciation tips
            - Speaking confidence
            - Listening comprehension
            - Writing skills
            - Reading strategies
            - Idioms and expressions
            - Business English
            - Conversation skills

            IMPORTANT: Provide accurate Arabic translations that are natural and educational.

            Format the response exactly like this:

            MAIN_TIP: Learn collocations - words that naturally go together.
            EXPLANATION: This makes your English sound more natural and fluent instead of translated.
            EXAMPLE: Instead of "make a photo", say "take a photo". Instead of "strong rain", say "heavy rain".
            ARABIC_TIP: تعلم المتلازمات اللفظية - الكلمات التي تترافق معًا بشكل طبيعي
            ARABIC_EXPLANATION: هذا يجعل لغتك الإنجليزية تبدو أكثر طلاقة وطبيعية بدلاً من أن تبدو مترجمة
            HASHTAGS: #EnglishTips #Vocabulary #LearnEnglish #ESL

            Return only ONE post in this exact format.
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
            tip_data = {}
            lines = response_text.split('\n')
            
            for line in lines:
                if line.startswith('MAIN_TIP:'):
                    tip_data['main_tip'] = line.replace('MAIN_TIP:', '').strip()
                elif line.startswith('EXPLANATION:'):
                    tip_data['explanation'] = line.replace('EXPLANATION:', '').strip()
                elif line.startswith('EXAMPLE:'):
                    tip_data['example'] = line.replace('EXAMPLE:', '').strip()
                elif line.startswith('ARABIC_TIP:'):
                    tip_data['arabic_tip'] = line.replace('ARABIC_TIP:', '').strip()
                elif line.startswith('ARABIC_EXPLANATION:'):
                    tip_data['arabic_explanation'] = line.replace('ARABIC_EXPLANATION:', '').strip()
                elif line.startswith('HASHTAGS:'):
                    tip_data['hashtags'] = line.replace('HASHTAGS:', '').strip()
            
            if 'main_tip' in tip_data and 'arabic_tip' in tip_data:
                # Check if this is a duplicate before returning
                if is_duplicate_tip(tip_data):
                    print(f"🔄 Generated tip is a duplicate, trying again... (Attempt {retry_count + 1}/{max_retries})")
                    retry_count += 1
                    continue
                
                return tip_data
            else:
                raise Exception("Invalid response format from Gemini - missing required fields")
            
        except Exception as e:
            print(f"❌ Error generating English tip: {e}")
            retry_count += 1
            if retry_count >= max_retries:
                break
            time.sleep(2)  # Wait before retrying
    
    # Fallback practical English tips with Arabic translations
    print("🔄 Using fallback tips after Gemini failures...")
    fallback_tips = [
        {
            'main_tip': 'Learn collocations - words that naturally go together.',
            'explanation': 'This makes your English sound more natural and fluent instead of translated.',
            'example': 'Instead of "make a photo", say "take a photo". Instead of "strong rain", say "heavy rain".',
            'arabic_tip': 'تعلم المتلازمات اللفظية - الكلمات التي تترافق معًا بشكل طبيعي',
            'arabic_explanation': 'هذا يجعل لغتك الإنجليزية تبدو أكثر طلاقة وطبيعية بدلاً من أن تبدو مترجمة',
            'hashtags': '#EnglishTips #Vocabulary #LearnEnglish #ESL'
        },
        {
            'main_tip': 'Use the present perfect for experiences and recent actions.',
            'explanation': 'This tense connects past actions to the present moment, which is common in English.',
            'example': '"I have visited Paris" (experience), "She has just finished her work" (recent action).',
            'arabic_tip': 'استخدم المضارع التام للتجارب والأحداث الحديثة',
            'arabic_explanation': 'هذا الزمن يربط بين الأفعال الماضية واللحظة الحالية، وهو شائع في اللغة الإنجليزية',
            'hashtags': '#Grammar #EnglishTenses #LearnEnglish #ESL'
        },
        {
            'main_tip': 'Practice sentence stress to sound more natural.',
            'explanation': 'English is a stress-timed language, so emphasizing key words improves rhythm and clarity.',
            'example': 'In "I WANT to GO to the STORE", stress the capitalized words for natural rhythm.',
            'arabic_tip': 'تدرب على نبرة الجملة لتظهر أكثر طلاقة',
            'arabic_explanation': 'اللغة الإنجليزية تعتمد على النبرة، لذا فإن التركيز على الكلمات المهمة يحسن الإيقاع والوضوح',
            'hashtags': '#Pronunciation #Speaking #EnglishRhythm #LearnEnglish'
        },
        {
            'main_tip': 'Learn phrasal verbs in context, not just memorizing lists.',
            'explanation': 'Understanding how they work in sentences helps you use them correctly in conversation.',
            'example': '"Look up" means search for information: "I need to look up that word in the dictionary."',
            'arabic_tip': 'تعلم الأفعال المركبة في السياق وليس فقط حفظ القوائم',
            'arabic_explanation': 'فهم كيفية عملها في الجمل يساعدك على استخدامها بشكل صحيح في المحادثة',
            'hashtags': '#PhrasalVerbs #Vocabulary #EnglishGrammar #LearnEnglish'
        }
    ]
    
    # Filter out duplicates from fallback tips
    non_duplicate_tips = [
        t for t in fallback_tips 
        if not is_duplicate_tip(t)
    ]
    
    if non_duplicate_tips:
        return random.choice(non_duplicate_tips)
    else:
        # If all fallbacks are duplicates, return a random one anyway
        print("⚠️ All fallback tips are duplicates, using random one")
        return random.choice(fallback_tips)

def get_pixabay_image():
    """Get a random educational or inspiring image from Pixabay API"""
    try:
        api_key = os.environ.get("PIXABAY_KEY")
        if not api_key:
            print("❌ PIXABAY_KEY not found in environment variables")
            return None
            
        categories = ["education", "books", "library", "writing", "nature", "sky", "flowers", "sunset", "office", "coffee"]
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

def get_arabic_font():
    """Try to load an Arabic-compatible font"""
    font_paths = [
        # Common Arabic fonts on Linux
        "/usr/share/fonts/truetype/arabic/arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        # Windows fonts (if running on Windows)
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/tahoma.ttf",
        # macOS fonts
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf"
    ]
    
    for font_path in font_paths:
        try:
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, 42)
        except Exception:
            continue
    
    # Fallback to default font
    print("⚠️ No Arabic font found, using default")
    return ImageFont.load_default()

def create_english_image(tip_data):
    """Create English learning themed image with dual language text overlay"""
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
            educational_colors = [
                '#1a4b8c', '#2c5aa0', '#3d69b4', '#4f78c8', '#6187dc',
                '#2d6a4f', '#3e7c61', '#4f8e73', '#60a085', '#71b297',
                '#8B4513', '#A0522D', '#B5651D', '#CD853F', '#D2691E'
            ]
            bg_color = random.choice(educational_colors)
            background = Image.new('RGB', (width, height), color=bg_color)
            print("✅ Using fallback solid color background")
    else:
        # Fallback to solid color background
        educational_colors = [
            '#1a4b8c', '#2c5aa0', '#3d69b4', '#4f78c8', '#6187dc',
            '#2d6a4f', '#3e7c61', '#4f8e73', '#60a085', '#71b297',
            '#8B4513', '#A0522D', '#B5651D', '#CD853F', '#D2691E'
        ]
        bg_color = random.choice(educational_colors)
        background = Image.new('RGB', (width, height), color=bg_color)
        print("✅ Using fallback solid color background")
    
    # Create drawing context
    draw = ImageDraw.Draw(background)
    
    # Load fonts
    try:
        english_font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        english_font = ImageFont.truetype(english_font_path, 48)
    except (IOError, OSError):
        try:
            english_font = ImageFont.truetype("arial.ttf", 48)
        except (IOError, OSError):
            english_font = ImageFont.load_default()
    
    # Load Arabic font
    arabic_font = get_arabic_font()
    
    # Prepare Arabic text with reshaping and bidirectional algorithm
    if ARABIC_SUPPORT:
        try:
            arabic_tip_reshaped = arabic_reshaper.reshape(tip_data['arabic_tip'])
            arabic_tip_display = get_display(arabic_tip_reshaped)
        except Exception as e:
            print(f"❌ Error processing Arabic text: {e}")
            arabic_tip_display = tip_data['arabic_tip']  # Fallback to original text
    else:
        arabic_tip_display = tip_data['arabic_tip']
        print("⚠️ Arabic text processing disabled - text may not display correctly")
    
    # Wrap the main tip text (English)
    max_chars_per_line = 25
    wrapped_english_tip = textwrap.fill(tip_data['main_tip'], width=max_chars_per_line)
    
    # Wrap Arabic text (approximate)
    arabic_lines = []
    current_line = ""
    for word in tip_data['arabic_tip'].split():
        if len(current_line + word) <= 15:  # Arabic characters are wider
            current_line += " " + word
        else:
            arabic_lines.append(current_line.strip())
            current_line = word
    if current_line:
        arabic_lines.append(current_line.strip())
    
    wrapped_arabic_tip = "\n".join(arabic_lines)
    
    # Prepare Arabic lines for display
    if ARABIC_SUPPORT:
        try:
            arabic_lines_reshaped = []
            for line in wrapped_arabic_tip.split('\n'):
                reshaped_line = arabic_reshaper.reshape(line)
                displayed_line = get_display(reshaped_line)
                arabic_lines_reshaped.append(displayed_line)
            wrapped_arabic_tip_display = "\n".join(arabic_lines_reshaped)
        except Exception as e:
            print(f"❌ Error processing wrapped Arabic text: {e}")
            wrapped_arabic_tip_display = wrapped_arabic_tip
    else:
        wrapped_arabic_tip_display = wrapped_arabic_tip
    
    # Calculate text positions
    # English text at top
    english_bbox = draw.textbbox((0, 0), wrapped_english_tip, font=english_font)
    english_width = english_bbox[2] - english_bbox[0]
    english_height = english_bbox[3] - english_bbox[1]
    english_x = (width - english_width) // 2
    english_y = height // 4 - english_height // 2
    
    # Arabic text at bottom
    arabic_bbox = draw.textbbox((0, 0), wrapped_arabic_tip_display, font=arabic_font)
    arabic_width = arabic_bbox[2] - arabic_bbox[0]
    arabic_height = arabic_bbox[3] - arabic_bbox[1]
    arabic_x = (width - arabic_width) // 2
    arabic_y = 3 * height // 4 - arabic_height // 2
    
    # Generate background color for text boxes
    text_bg_color = (0, 0, 0, 160)  # Semi-transparent black
    
    # Add semi-transparent background for English text
    english_padding = 30
    draw.rectangle([
        english_x - english_padding, english_y - english_padding,
        english_x + english_width + english_padding, english_y + english_height + english_padding
    ], fill=text_bg_color)
    
    # Add semi-transparent background for Arabic text
    arabic_padding = 30
    draw.rectangle([
        arabic_x - arabic_padding, arabic_y - arabic_padding,
        arabic_x + arabic_width + arabic_padding, arabic_y + arabic_height + arabic_padding
    ], fill=text_bg_color)
    
    # Draw English text
    draw.text((english_x, english_y), wrapped_english_tip, fill=(255, 255, 255), font=english_font, align='center')
    
    # Draw Arabic text
    draw.text((arabic_x, arabic_y), wrapped_arabic_tip_display, fill=(255, 255, 255), font=arabic_font, align='center')
    
    # Convert to bytes
    output_buffer = BytesIO()
    background.save(output_buffer, format="JPEG", quality=95)
    return output_buffer.getvalue()

def create_facebook_caption(tip_data):
    """Create Facebook caption with dual language English learning advice"""
    # Random header options
    headers = [
        "English Learning Tip 📚",
        "Grammar Quick Tip ✨",
        "Vocabulary Builder 🗣️",
        "Pronunciation Help 🎯",
        "English Speaking Tip 💬"
    ]
    
    header = random.choice(headers)
    
    # Random CTA options
    cta_options = [
        "👍 Like and share if you found this helpful! Follow for daily English tips!",
        "💬 Want to improve your English? Follow for daily learning strategies!",
        "🚀 Share this with someone learning English! Follow for more language insights!",
        "📚 Found this useful? Share and follow for daily English learning tips!",
        "👥 Tag a friend who's learning English! Follow for more language tips!"
    ]
    
    cta = random.choice(cta_options)
    
    caption = f"""{header}

🇬🇧 English:
{tip_data['main_tip']}

💡 {tip_data['explanation']}

📝 Example: {tip_data.get('example', 'Practice makes perfect!')}

🇸🇦 العربية:
{tip_data['arabic_tip']}

💡 {tip_data['arabic_explanation']}

💬 What's your biggest English challenge? Share in the comments!

{cta}

{tip_data['hashtags']}
#EnglishLearning #تعلم_الإنجليزية #LanguageTips #ESL #EnglishGrammar #SpeakEnglish"""

    return caption

def post_to_facebook(image_data, tip_data):
    """Post the image to Facebook Page with dual language caption"""
    try:
        page_id = os.environ.get("FB_PAGE_ID")
        access_token = os.environ.get("FB_PAGE_TOKEN")
        
        if not page_id or not access_token:
            print("❌ Facebook credentials not found in environment variables")
            return False
        
        # Upload image to Facebook
        url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
        
        # Create caption
        caption = create_facebook_caption(tip_data)
        
        files = {'source': ('english_tip.jpg', image_data, 'image/jpeg')}
        data = {'message': caption, 'access_token': access_token}
        
        response = requests.post(url, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            # Save to posted tips history to prevent duplicates
            if save_posted_tip(tip_data):
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
    print("🚀 Starting English coach tip generation and posting process...")
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
    
    # Generate practical English learning tip with Arabic translation
    tip_data = generate_english_tip()
    print(f"💡 English Tip: {tip_data['main_tip']}")
    print(f"💡 Arabic Tip: {tip_data['arabic_tip']}")
    print(f"📝 Explanation: {tip_data['explanation']}")
    print(f"📝 Arabic Explanation: {tip_data['arabic_explanation']}")
    if 'example' in tip_data:
        print(f"📚 Example: {tip_data['example']}")
    print(f"🏷️ Hashtags: {tip_data['hashtags']}")
    
    # Create image with dual language text
    final_image = create_english_image(tip_data)
    print("🎨 Dual language English learning image created")
    
    # Post to Facebook
    success = post_to_facebook(final_image, tip_data)
    
    if success:
        print("✅ Process completed successfully! The dual language English tip has been shared.")
    else:
        print("❌ Process completed with errors")

if __name__ == "__main__":
    main()