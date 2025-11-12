#!/usr/bin/env python3
"""
English Coach: Generate practical English learning tips and lessons with Gemini AI,
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
    """Generate a practical English learning tip using Gemini"""
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
            HASHTAGS: [3-4 relevant hashtags]

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

            IMPORTANT: Avoid overused tips like "watch movies with subtitles" or "practice every day".
            Focus on fresh, specific, actionable English learning advice.

            Format the response exactly like this:

            MAIN_TIP: Learn collocations - words that naturally go together.
            EXPLANATION: This makes your English sound more natural and fluent instead of translated.
            EXAMPLE: Instead of "make a photo", say "take a photo". Instead of "strong rain", say "heavy rain".
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
                elif line.startswith('HASHTAGS:'):
                    tip_data['hashtags'] = line.replace('HASHTAGS:', '').strip()
            
            if 'main_tip' in tip_data:
                # Check if this is a duplicate before returning
                if is_duplicate_tip(tip_data):
                    print(f"🔄 Generated tip is a duplicate, trying again... (Attempt {retry_count + 1}/{max_retries})")
                    retry_count += 1
                    continue
                
                return tip_data
            else:
                raise Exception("Invalid response format from Gemini")
            
        except Exception as e:
            print(f"❌ Error generating English tip: {e}")
            retry_count += 1
            if retry_count >= max_retries:
                break
            time.sleep(2)  # Wait before retrying
    
    # Fallback practical English tips
    print("🔄 Using fallback tips after Gemini failures...")
    fallback_tips = [
        {
            'main_tip': 'Learn collocations - words that naturally go together.',
            'explanation': 'This makes your English sound more natural and fluent instead of translated.',
            'example': 'Instead of "make a photo", say "take a photo". Instead of "strong rain", say "heavy rain".',
            'hashtags': '#EnglishTips #Vocabulary #LearnEnglish #ESL'
        },
        {
            'main_tip': 'Use the present perfect for experiences and recent actions.',
            'explanation': 'This tense connects past actions to the present moment, which is common in English.',
            'example': '"I have visited Paris" (experience), "She has just finished her work" (recent action).',
            'hashtags': '#Grammar #EnglishTenses #LearnEnglish #ESL'
        },
        {
            'main_tip': 'Practice sentence stress to sound more natural.',
            'explanation': 'English is a stress-timed language, so emphasizing key words improves rhythm and clarity.',
            'example': 'In "I WANT to GO to the STORE", stress the capitalized words for natural rhythm.',
            'hashtags': '#Pronunciation #Speaking #EnglishRhythm #LearnEnglish'
        },
        {
            'main_tip': 'Learn phrasal verbs in context, not just memorizing lists.',
            'explanation': 'Understanding how they work in sentences helps you use them correctly in conversation.',
            'example': '"Look up" means search for information: "I need to look up that word in the dictionary."',
            'hashtags': '#PhrasalVerbs #Vocabulary #EnglishGrammar #LearnEnglish'
        },
        {
            'main_tip': 'Use linking words to connect your ideas smoothly.',
            'explanation': 'Transition words make your speech and writing flow better and sound more professional.',
            'example': 'Use "however" for contrast, "therefore" for results, "furthermore" for adding information.',
            'hashtags': '#WritingSkills #Speaking #EnglishFluency #LearnEnglish'
        },
        {
            'main_tip': 'Learn the difference between similar prepositions.',
            'explanation': 'Small preposition changes can completely alter meaning in English.',
            'example': '"Arrive in" a country/city, "arrive at" a building, "arrive on" a specific day.',
            'hashtags': '#Grammar #Prepositions #EnglishTips #LearnEnglish'
        },
        {
            'main_tip': 'Practice minimal pairs to improve pronunciation.',
            'explanation': 'Distinguishing similar sounds helps you speak more clearly and understand better.',
            'example': 'Practice: ship/sheep, live/leave, beach/bitch, work/walk.',
            'hashtags': '#Pronunciation #Speaking #EnglishSounds #LearnEnglish'
        },
        {
            'main_tip': 'Use the active voice more often than passive.',
            'explanation': 'Active voice is more direct, clear, and common in everyday English conversation.',
            'example': 'Active: "The team completed the project." Passive: "The project was completed by the team."',
            'hashtags': '#Grammar #WritingTips #Speaking #LearnEnglish'
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

def create_english_image(tip_data):
    """Create English learning themed image with Pixabay background and text overlay"""
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
    
    # Try to load font
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        tip_font = ImageFont.truetype(font_path, 62)
    except (IOError, OSError):
        try:
            tip_font = ImageFont.truetype("arial.ttf", 62)
        except (IOError, OSError):
            tip_font = ImageFont.load_default()
    
    # Wrap the main tip text
    max_chars_per_line = 22
    wrapped_tip = textwrap.fill(tip_data['main_tip'], width=max_chars_per_line)
    
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

def create_facebook_caption(tip_data):
    """Create Facebook caption with English learning advice and CTA"""
    # Random header options
    headers = [
        "English Learning Tip",
        "Grammar Quick Tip",
        "Vocabulary Builder",
        "Pronunciation Help",
        "English Speaking Tip",
        "Writing Skills",
        "English Fluency",
        "Language Learning"
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
    
    caption = f"""{header}:

{tip_data['main_tip']}

💡 {tip_data['explanation']}

📝 Example: {tip_data.get('example', 'Practice makes perfect!')}

💬 What's your biggest English challenge? Share in the comments!

{cta}

{tip_data['hashtags']}

#EnglishLearning #LanguageTips #ESL #EnglishGrammar #SpeakEnglish"""
    
    return caption

def post_to_facebook(image_data, tip_data):
    """Post the image to Facebook Page with English learning caption"""
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
    
    # Generate practical English learning tip
    tip_data = generate_english_tip()
    print(f"💡 Main Tip: {tip_data['main_tip']}")
    print(f"📝 Explanation: {tip_data['explanation']}")
    if 'example' in tip_data:
        print(f"📚 Example: {tip_data['example']}")
    print(f"🏷️ Hashtags: {tip_data['hashtags']}")
    
    # Create image with main tip text only
    final_image = create_english_image(tip_data)
    print("🎨 English learning image created")
    
    # Post to Facebook
    success = post_to_facebook(final_image, tip_data)
    
    if success:
        print("✅ Process completed successfully! The English learning tip has been shared.")
    else:
        print("❌ Process completed with errors")

if __name__ == "__main__":
    main()