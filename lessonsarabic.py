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
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps
from io import BytesIO
import time
from urllib.parse import quote_plus

# Try to import Arabic text libraries
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_SUPPORT = True
    print("✓ Arabic text support enabled")
except ImportError:
    ARABIC_SUPPORT = False
    print("⚠ Arabic text libraries not available")

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

# File to store posted content for duplication check
POST_HISTORY_FILE = os.path.join(os.getcwd(), "posted_content.json")

def load_arabic_font(font_size=56):
    """Load Arabic font"""
    arabic_font_paths = [
        "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
        "/usr/share/fonts/truetype/fonts-arabeyes/ae_AlMateen.ttf",
    ]
    
    for font_path in arabic_font_paths:
        try:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
                print(f"✓ Loaded Arabic font: {os.path.basename(font_path)}")
                return font
        except (IOError, OSError):
            continue
    
    # Download Arabic font as fallback
    try:
        font_url = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansArabic/NotoSansArabic-Regular.ttf"
        response = requests.get(font_url, timeout=15)
        if response.status_code == 200:
            font_file = BytesIO(response.content)
            print("✓ Downloaded Arabic font")
            return ImageFont.truetype(font_file, font_size)
    except Exception as e:
        print(f"⚠ Error downloading Arabic font: {e}")
    
    return None

def load_english_font(font_size=56):
    """Load English font"""
    english_font_paths = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/System/Library/Fonts/Arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    
    for font_path in english_font_paths:
        try:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
                print(f"✓ Loaded English font: {os.path.basename(font_path)}")
                return font
        except (IOError, OSError):
            continue
    
    # Download English font as fallback
    try:
        font_url = "https://github.com/liberationfonts/liberation-fonts/files/2926169/LiberationSans-Regular.tar.gz"
        response = requests.get(font_url, timeout=15)
        if response.status_code == 200:
            font_file = BytesIO(response.content)
            print("✓ Downloaded English font")
            return ImageFont.truetype(font_file, font_size)
    except Exception as e:
        print(f"⚠ Error downloading English font: {e}")
    
    # Ultimate fallback
    print("⚠ Using default font for English")
    return ImageFont.load_default()

def split_mixed_text(text):
    """Split text into Arabic and English segments"""
    # Pattern to match Arabic text (Arabic Unicode range)
    arabic_pattern = r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+'
    # Pattern to match English text (Latin characters)
    english_pattern = r'[a-zA-Z]+'
    
    segments = []
    current_pos = 0
    
    while current_pos < len(text):
        # Look for Arabic text
        arabic_match = re.search(arabic_pattern, text[current_pos:])
        # Look for English text
        english_match = re.search(english_pattern, text[current_pos:])
        
        # Find which comes first
        arabic_start = arabic_match.start() if arabic_match else float('inf')
        english_start = english_match.start() if english_match else float('inf')
        
        if arabic_start < english_start and arabic_match:
            # Arabic text found first
            if arabic_start > 0:
                # There's some non-Arabic text before the Arabic
                segments.append(('other', text[current_pos:current_pos + arabic_start]))
            segments.append(('arabic', arabic_match.group()))
            current_pos += arabic_start + len(arabic_match.group())
        elif english_start < arabic_start and english_match:
            # English text found first
            if english_start > 0:
                # There's some non-English text before the English
                segments.append(('other', text[current_pos:current_pos + english_start]))
            segments.append(('english', english_match.group()))
            current_pos += english_start + len(english_match.group())
        else:
            # No more Arabic or English text, add the rest as other
            if current_pos < len(text):
                segments.append(('other', text[current_pos:]))
            break
    
    return segments

def reshape_arabic_text(text):
    """Reshape Arabic text for proper rendering"""
    if not ARABIC_SUPPORT:
        return text
        
    try:
        # Only reshape if there's Arabic text
        if re.search(r'[\u0600-\u06FF]', text):
            reshaped_text = arabic_reshaper.reshape(text)
            bidi_text = get_display(reshaped_text)
            return bidi_text
        else:
            return text
    except Exception as e:
        print(f"⚠ Error reshaping Arabic text: {e}")
        return text

def create_mixed_text_image(image_text, width=1200, height=1200):
    """Create image with mixed Arabic and English text using separate fonts"""
    # Get background image
    image_bytes = get_pixabay_image()
    
    if image_bytes:
        try:
            background = Image.open(image_bytes)
            background = background.resize((width, height), Image.LANCZOS)
            enhancer = ImageEnhance.Brightness(background)
            background = enhancer.enhance(0.7)
            print("✅ Using Pixabay background image")
        except Exception as e:
            education_colors = ['#2E8B57', '#4682B4', '#5F9EA0', '#20B2AA']
            bg_color = random.choice(education_colors)
            background = Image.new('RGB', (width, height), color=bg_color)
            print("🎨 Using solid color background")
    else:
        education_colors = ['#2E8B57', '#4682B4', '#5F9EA0', '#20B2AA']
        bg_color = random.choice(education_colors)
        background = Image.new('RGB', (width, height), color=bg_color)
        print("🎨 Using solid color background")
    
    # Convert to RGBA for transparency support
    background = background.convert('RGBA')
    draw = ImageDraw.Draw(background)
    
    # Load fonts
    arabic_font = load_arabic_font(56)
    english_font = load_english_font(56)
    
    # Split text into segments
    segments = split_mixed_text(image_text)
    print(f"📝 Text segments: {segments}")
    
    # Calculate total text dimensions
    total_width = 0
    max_height = 0
    
    for seg_type, seg_text in segments:
        if seg_type == 'arabic':
            font = arabic_font
            text_to_measure = reshape_arabic_text(seg_text)
        else:
            font = english_font
            text_to_measure = seg_text
        
        try:
            bbox = draw.textbbox((0, 0), text_to_measure, font=font)
            seg_width = bbox[2] - bbox[0]
            seg_height = bbox[3] - bbox[1]
        except:
            seg_width, seg_height = 100, 50
        
        total_width += seg_width
        max_height = max(max_height, seg_height)
    
    # Add spacing between segments
    total_width += (len(segments) - 1) * 10
    
    # Calculate starting position (centered)
    x = (width - total_width) // 2
    y = (height - max_height) // 2
    
    # Add semi-transparent background
    padding = 40
    box_color = get_random_box_color()
    
    box_image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    box_draw = ImageDraw.Draw(box_image)
    box_draw.rectangle([
        x - padding, y - padding,
        x + total_width + padding, y + max_height + padding
    ], fill=box_color)
    
    background = Image.alpha_composite(background, box_image)
    draw = ImageDraw.Draw(background)
    
    # Draw each segment with appropriate font
    current_x = x
    for seg_type, seg_text in segments:
        if seg_type == 'arabic':
            font = arabic_font
            text_to_draw = reshape_arabic_text(seg_text)
        else:
            font = english_font
            text_to_draw = seg_text
        
        # Calculate segment position
        try:
            bbox = draw.textbbox((0, 0), text_to_draw, font=font)
            seg_height = bbox[3] - bbox[1]
        except:
            seg_height = max_height
        
        text_y = y + (max_height - seg_height) // 2
        
        # Draw the text
        draw.text((current_x, text_y), text_to_draw, fill=(255, 255, 255), font=font)
        
        # Move to next position
        try:
            bbox = draw.textbbox((0, 0), text_to_draw, font=font)
            current_x += (bbox[2] - bbox[0]) + 10  # Add spacing
        except:
            current_x += 100  # Fallback width
    
    # Convert back to RGB for JPEG saving
    background = background.convert('RGB')
    
    # Convert to bytes
    output_buffer = BytesIO()
    background.save(output_buffer, format="JPEG", quality=95)
    print("✅ Mixed text image created successfully")
    return output_buffer.getvalue()

def get_random_box_color():
    """Generate random semi-transparent background colors"""
    colors = [
        (30, 144, 255, 180), (46, 139, 87, 180), (147, 112, 219, 180),
        (220, 20, 60, 180), (255, 140, 0, 180), (32, 178, 170, 180),
    ]
    return random.choice(colors)

def get_pixabay_image():
    """Get a random education/learning-related image from Pixabay"""
    try:
        api_key = os.environ.get("PIXABAY_KEY")
        if not api_key:
            return None
            
        categories = ["education", "learning", "study", "books", "school"]
        category = random.choice(categories)
        
        url = "https://pixabay.com/api/"
        params = {
            "key": api_key,
            "q": category,
            "image_type": "photo",
            "per_page": 10,
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
    except:
        return None

# ... (keep the rest of your existing functions like load_posted_content, save_posted_content, 
# is_duplicate_content, generate_content_combination, generate_english_content, post_to_facebook, main)

def load_posted_content():
    """Load history of posted content to avoid duplicates"""
    try:
        if os.path.exists(POST_HISTORY_FILE):
            with open(POST_HISTORY_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        return []
    except:
        return []

def save_posted_content(content_text):
    """Save posted content to history"""
    try:
        posted_content = load_posted_content()
        content_hash = hashlib.md5(content_text.encode()).hexdigest()
        if content_hash not in posted_content:
            posted_content.append(content_hash)
            with open(POST_HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(posted_content, f)
            return True
        return False
    except:
        return False

def is_duplicate_content(content_text):
    """Check if content has already been posted"""
    try:
        posted_content = load_posted_content()
        content_hash = hashlib.md5(content_text.encode()).hexdigest()
        return content_hash in posted_content
    except:
        return False

def generate_english_content():
    """Generate informative English learning content"""
    # Your existing content generation logic here
    # Return post_data with 'image_text' and 'detailed_content'
    fallback_posts = [
        {
            'image_text': "تعلم 5 كلمات إنجليزية يومياً يحسن المفردات",
            'detailed_content': "تعلم كلمات جديدة كل يوم يساعد في بناء المفردات.\n\n#تعلم_الإنجليزية #مفردات"
        },
        {
            'image_text': "الممارسة اليومية essential للطلاقة",
            'detailed_content': "التكرار والممارسة أساسيات التعلم.\n\n#ممارسة #إنجليزية"
        }
    ]
    return random.choice(fallback_posts)

def post_to_facebook(image_data, post_data):
    """Post the image to Facebook Page"""
    try:
        page_id = os.environ.get("FB_PAGE_ID")
        access_token = os.environ.get("FB_PAGE_TOKEN")
        
        if not page_id or not access_token:
            return False
        
        url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
        files = {'source': ('english_learning.jpg', image_data, 'image/jpeg')}
        data = {'message': post_data['detailed_content'], 'access_token': access_token}
        
        response = requests.post(url, files=files, data=data, timeout=30)
        return response.status_code == 200
    except:
        return False

def main():
    """Main function"""
    print("🚀 Starting English Learning Content Generator...")
    
    # Check environment variables
    required_vars = ["GEMINI_API_KEY", "PIXABAY_KEY", "FB_PAGE_ID", "FB_PAGE_TOKEN"]
    for var in required_vars:
        if not os.environ.get(var):
            print(f"❌ Missing: {var}")
            return
    
    # Generate content
    post_data = generate_english_content()
    print(f"📝 Image text: {post_data['image_text']}")
    
    # Create image with mixed text support
    final_image = create_mixed_text_image(post_data['image_text'])
    
    # Post to Facebook
    success = post_to_facebook(final_image, post_data)
    print("✅ Posted successfully!" if success else "❌ Failed to post")

if __name__ == "__main__":
    main()