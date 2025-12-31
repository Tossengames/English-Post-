#!/usr/bin/env python3
"""
Mom Motivation Bot: Generate motivational posts for moms with Gemini AI,
create images with text overlay using Pixabay backgrounds, and post to Facebook Page.
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
        import google.generativeai as genai
        print("✅ Using old Google Generative AI SDK")
        SDK_TYPE = "old"
    except ImportError as e:
        print(f"❌ Failed to import Google AI libraries: {e}")
        exit(1)

POST_HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "posted_mom_quotes.json")

def load_posted_quotes():
    try:
        if os.path.exists(POST_HISTORY_FILE):
            with open(POST_HISTORY_FILE, 'r') as f:
                content = f.read().strip()
                return json.loads(content) if content else []
        return []
    except Exception as e:
        print(f"❌ Error loading history: {e}")
        return []

def save_posted_quote(quote_data):
    try:
        posted_quotes = load_posted_quotes()
        quote_hash = hashlib.md5(quote_data['main_quote'].encode()).hexdigest()
        if quote_hash not in posted_quotes:
            posted_quotes.append(quote_hash)
            os.makedirs(os.path.dirname(POST_HISTORY_FILE), exist_ok=True)
            with open(POST_HISTORY_FILE, 'w') as f:
                json.dump(posted_quotes, f)
            print(f"✅ Saved quote: {quote_data['main_quote'][:50]}...")
            return True
        else:
            print(f"❌ Quote already posted: {quote_data['main_quote'][:50]}...")
            return False
    except Exception as e:
        print(f"❌ Error saving quote: {e}")
        return False

def is_duplicate_quote(quote_data):
    try:
        posted_quotes = load_posted_quotes()
        quote_hash = hashlib.md5(quote_data['main_quote'].encode()).hexdigest()
        is_dup = quote_hash in posted_quotes
        print("❌ Duplicate" if is_dup else "✅ New quote", f": {quote_data['main_quote'][:50]}...")
        return is_dup
    except Exception as e:
        print(f"❌ Error checking duplicate: {e}")
        return False

def generate_mom_motivation():
    """Generate motivational posts for moms"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            if SDK_TYPE == "new":
                client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
            else:
                genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            
            prompt = """
            Create ONE short, uplifting, and motivational post for moms with these components:

            MAIN_QUOTE: [A short, powerful, and encouraging quote for moms - under 20 words]
            EXPLANATION: [1-2 sentences explaining why this quote is inspiring or how it can empower moms]
            HASHTAGS: [3-4 relevant hashtags]

            Avoid clichés and generic phrases. Focus on real-life mom challenges, empowerment, self-love, patience, and resilience.

            Format exactly like:

            MAIN_QUOTE: You are stronger than you think, mom.
            EXPLANATION: Even on tough days, your love and perseverance make a difference. Keep going!
            HASHTAGS: #MomLife #MotivationForMoms #StrongMom #SelfCare
            """
            
            if SDK_TYPE == "new":
                response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
                response_text = response.text
            else:
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(prompt)
                response_text = response.text
            
            response_text = response_text.strip()
            
            quote_data = {}
            for line in response_text.split('\n'):
                if line.startswith('MAIN_QUOTE:'):
                    quote_data['main_quote'] = line.replace('MAIN_QUOTE:', '').strip()
                elif line.startswith('EXPLANATION:'):
                    quote_data['explanation'] = line.replace('EXPLANATION:', '').strip()
                elif line.startswith('HASHTAGS:'):
                    quote_data['hashtags'] = line.replace('HASHTAGS:', '').strip()
            
            if 'main_quote' in quote_data:
                if is_duplicate_quote(quote_data):
                    retry_count += 1
                    continue
                return quote_data
            else:
                raise Exception("Invalid Gemini response")
        except Exception as e:
            print(f"❌ Error generating quote: {e}")
            retry_count += 1
            time.sleep(2)
    
    # Fallback quotes
    fallback_quotes = [
        {
            'main_quote': 'You are enough, just as you are.',
            'explanation': 'Your love, patience, and effort matter every day, even when it feels invisible.',
            'hashtags': '#MomLife #SelfLove #StrongMom'
        },
        {
            'main_quote': 'Small steps today create big changes tomorrow.',
            'explanation': 'Every little effort counts, and you are shaping the future with love and care.',
            'hashtags': '#MomMotivation #Persistence #DailyWins'
        },
        {
            'main_quote': 'Breathe. You are doing amazing.',
            'explanation': 'Even when overwhelmed, pausing to breathe reminds you of your strength.',
            'hashtags': '#MomLife #SelfCare #MotivationForMoms'
        }
    ]
    
    non_duplicate = [q for q in fallback_quotes if not is_duplicate_quote(q)]
    return random.choice(non_duplicate) if non_duplicate else random.choice(fallback_quotes)

def get_pixabay_image():
    """Get a random background image"""
    try:
        api_key = os.environ.get("PIXABAY_KEY")
        if not api_key:
            return None
            
        categories = ["nature", "flowers", "sunset", "forest", "ocean", "home", "family", "relax", "sky"]
        category = random.choice(categories)
        url = "https://pixabay.com/api/"
        params = {"key": api_key, "q": category, "image_type": "photo",
                  "orientation": "horizontal", "per_page": 20, "safesearch": "true", "editors_choice": "true"}
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data['hits']:
                image_url = random.choice(data['hits'])["largeImageURL"]
                img_response = requests.get(image_url, timeout=15)
                return BytesIO(img_response.content)
        return None
    except Exception as e:
        print(f"❌ Error fetching Pixabay image: {e}")
        return None

def create_mom_image(quote_data):
    width, height = 1200, 1200
    image_bytes = get_pixabay_image()
    
    if image_bytes:
        try:
            background = Image.open(image_bytes).resize((width, height), Image.LANCZOS)
            background = ImageEnhance.Brightness(background).enhance(0.7)
        except:
            background = Image.new('RGB', (width, height), color=random.choice([
                '#f28b82','#fbbc04','#fff475','#ccff90','#a7ffeb','#cbf0f8','#aecbfa','#d7aefb'
            ]))
    else:
        background = Image.new('RGB', (width, height), color=random.choice([
            '#f28b82','#fbbc04','#fff475','#ccff90','#a7ffeb','#cbf0f8','#aecbfa','#d7aefb'
        ]))
    
    draw = ImageDraw.Draw(background)
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        tip_font = ImageFont.truetype(font_path, 62)
    except:
        try:
            tip_font = ImageFont.truetype("arial.ttf", 62)
        except:
            tip_font = ImageFont.load_default()
    
    wrapped_quote = textwrap.fill(quote_data['main_quote'], width=22)
    bbox = draw.textbbox((0,0), wrapped_quote, font=tip_font)
    text_width = bbox[2]-bbox[0]
    text_height = bbox[3]-bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Random semi-transparent text box color
    random_bg_color = (
        random.randint(0,255),
        random.randint(0,255),
        random.randint(0,255),
        180
    )
    
    padding = 40
    draw.rectangle([x-padding, y-padding, x+text_width+padding, y+text_height+padding], fill=random_bg_color)
    draw.text((x, y), wrapped_quote, fill=(255,255,255), font=tip_font, align='center')
    
    output_buffer = BytesIO()
    background.save(output_buffer, format="JPEG", quality=95)
    return output_buffer.getvalue()

def create_facebook_caption(quote_data):
    headers = ["Motivation for Moms","Momspiration","Daily Mom Boost","Positive Mom Energy"]
    cta_options = [
        "💖 Share this with a mom who needs encouragement today!",
        "🌸 Like and follow for more daily mom motivation!",
        "🌷 Tag a friend who would love this advice!"
    ]
    header = random.choice(headers)
    cta = random.choice(cta_options)
    
    caption = f"""{header}:

{quote_data['main_quote']}

💡 {quote_data['explanation']}

{cta}

{quote_data['hashtags']}
#MomLife #MotivationForMoms #SelfCare"""
    return caption

def post_to_facebook(image_data, quote_data):
    try:
        page_id = os.environ.get("FB_PAGE_ID")
        access_token = os.environ.get("FB_PAGE_TOKEN")
        if not page_id or not access_token:
            print("❌ Missing Facebook credentials")
            return False
        
        url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
        caption = create_facebook_caption(quote_data)
        files = {'source': ('mom_motivation.jpg', image_data, 'image/jpeg')}
        data = {'message': caption, 'access_token': access_token}
        response = requests.post(url, files=files, data=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            save_posted_quote(quote_data)
            print(f"✅ Posted to Facebook! Post ID: {result.get('id')}")
            return True
        else:
            print(f"❌ Facebook API error: {response.status_code}, {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error posting to Facebook: {e}")
        return False

def main():
    print("🚀 Starting Mom Motivation Post Process...")
    
    required_env_vars = ["GEMINI_API_KEY", "PIXABAY_KEY", "FB_PAGE_ID", "FB_PAGE_TOKEN"]
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    if missing_vars:
        print(f"❌ Missing env variables: {', '.join(missing_vars)}")
        return
    
    print(f"📊 Existing quotes in history: {len(load_posted_quotes())}")
    
    quote_data = generate_mom_motivation()
    print(f"💡 Quote: {quote_data['main_quote']}")
    print(f"📝 Explanation: {quote_data['explanation']}")
    
    image = create_mom_image(quote_data)
    print("🎨 Motivational image created")
    
    post_to_facebook(image, quote_data)

if __name__ == "__main__":
    main()