#!/usr/bin/env python3
"""
Audience Engagement: Generate thought-provoking questions for audience engagement
using Gemini AI, create images with text overlay using Pixabay backgrounds, 
and post to Facebook Page.
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

# File to store posted questions for duplication check - using absolute path
POST_HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "posted_questions.json")

def load_posted_questions():
    """Load history of posted questions to avoid duplicates"""
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

def save_posted_question(question_data):
    """Save a posted question to history"""
    try:
        posted_questions = load_posted_questions()
        
        # Create a unique hash of the main question to identify duplicates
        question_hash = hashlib.md5(question_data['main_question'].encode()).hexdigest()
        
        # Add to history if not already there
        if question_hash not in posted_questions:
            posted_questions.append(question_hash)
            # Ensure directory exists
            os.makedirs(os.path.dirname(POST_HISTORY_FILE), exist_ok=True)
            with open(POST_HISTORY_FILE, 'w') as f:
                json.dump(posted_questions, f)
            print(f"✅ Saved question to history: {question_data['main_question'][:50]}...")
            return True
        else:
            print(f"❌ Question already exists in history: {question_data['main_question'][:50]}...")
            return False
    except Exception as e:
        print(f"❌ Error saving to history: {e}")
        return False

def is_duplicate_question(question_data):
    """Check if a question has already been posted"""
    try:
        posted_questions = load_posted_questions()
        question_hash = hashlib.md5(question_data['main_question'].encode()).hexdigest()
        is_dup = question_hash in posted_questions
        if is_dup:
            print(f"❌ Duplicate detected: {question_data['main_question'][:50]}...")
        else:
            print(f"✅ New question: {question_data['main_question'][:50]}...")
        return is_dup
    except Exception as e:
        print(f"❌ Error checking duplicate: {e}")
        return False

def generate_engagement_question():
    """Generate thought-provoking questions for audience engagement using Gemini"""
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
            Create ONE engaging question post with these components:

            MAIN_QUESTION: [A thought-provoking, open-ended question that encourages discussion and comments - under 15 words]
            CONTEXT: [1-2 sentences that provide context or explain why this question is interesting to think about]
            HASHTAGS: [4-5 relevant hashtags for social media engagement]

            Question topics should include:
            - Life and personal growth
            - Work and career
            - Relationships and social dynamics
            - Technology and modern life
            - Philosophy and deep thinking
            - Happiness and fulfillment
            - Future and aspirations
            - Challenges and overcoming obstacles
            - Personal preferences and opinions

            IMPORTANT: The question should be open-ended, thought-provoking, and encourage people to share their personal experiences and opinions in the comments.

            Format the response exactly like this:

            MAIN_QUESTION: What's one skill you believe everyone should learn and why?
            CONTEXT: In today's rapidly changing world, certain skills can make a big difference in both personal and professional life.
            HASHTAGS: #Discussion #LifeSkills #PersonalGrowth #CommunityChat

            Return only ONE question post in this exact format.
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
            question_data = {}
            lines = response_text.split('\n')
            
            for line in lines:
                if line.startswith('MAIN_QUESTION:'):
                    question_data['main_question'] = line.replace('MAIN_QUESTION:', '').strip()
                elif line.startswith('CONTEXT:'):
                    question_data['context'] = line.replace('CONTEXT:', '').strip()
                elif line.startswith('HASHTAGS:'):
                    question_data['hashtags'] = line.replace('HASHTAGS:', '').strip()
            
            if 'main_question' in question_data:
                # Check if this is a duplicate before returning
                if is_duplicate_question(question_data):
                    print(f"🔄 Generated question is a duplicate, trying again... (Attempt {retry_count + 1}/{max_retries})")
                    retry_count += 1
                    continue
                
                return question_data
            else:
                raise Exception("Invalid response format from Gemini")
            
        except Exception as e:
            print(f"❌ Error generating engagement question: {e}")
            retry_count += 1
            if retry_count >= max_retries:
                break
            time.sleep(2)  # Wait before retrying
    
    # Fallback engagement questions
    print("🔄 Using fallback questions after Gemini failures...")
    fallback_questions = [
        {
            'main_question': "What's one skill you believe everyone should learn and why?",
            'context': "In today's rapidly changing world, certain skills can make a big difference in both personal and professional life.",
            'hashtags': '#Discussion #LifeSkills #PersonalGrowth #CommunityChat'
        },
        {
            'main_question': "What's the best piece of advice you've ever received?",
            'context': "Great advice can come from unexpected places and often stays with us for life.",
            'hashtags': '#Wisdom #LifeAdvice #ShareYourStory #Community'
        },
        {
            'main_question': "If you could have dinner with anyone from history, who would it be?",
            'context': "Imagine the conversations and insights you could gain from spending time with historical figures.",
            'hashtags': '#Discussion #History #WhatIf #CommunityChat'
        },
        {
            'main_question': "What's something you believed as a child that you now think differently about?",
            'context': "Our perspectives evolve as we grow and gain new experiences.",
            'hashtags': '#Growth #Perspective #LifeLessons #ShareYourThoughts'
        },
        {
            'main_question': "What does 'success' mean to you personally?",
            'context': "Success means different things to different people - it's not always about money or status.",
            'hashtags': '#Success #PersonalGrowth #LifeGoals #Discussion'
        },
        {
            'main_question': "What's one small change that significantly improved your daily life?",
            'context': "Sometimes the smallest adjustments can have the biggest impact on our happiness and productivity.",
            'hashtags': '#LifeHacks #Productivity #Wellness #ShareYourTips'
        },
        {
            'main_question': "What book has had the biggest impact on your thinking?",
            'context': "Great books can change our perspectives and stay with us long after we've finished reading.",
            'hashtags': '#Books #Reading #PersonalDevelopment #CommunityRecommendations'
        },
        {
            'main_question': "What's the most important lesson you've learned from a failure?",
            'context': "Some of our most valuable growth comes from challenges and setbacks.",
            'hashtags': '#GrowthMindset #LifeLessons #Resilience #ShareYourStory'
        },
        {
            'main_question': "If you could give your younger self one piece of advice, what would it be?",
            'context': "Looking back, we often see things more clearly and wish we could share that wisdom.",
            'hashtags': '#Wisdom #LifeAdvice #PersonalGrowth #Reflection'
        },
        {
            'main_question': "What's something you're currently curious about or want to learn?",
            'context': "Curiosity keeps our minds active and helps us continue growing throughout life.",
            'hashtags': '#Curiosity #LifelongLearning #PersonalDevelopment #CommunityChat'
        }
    ]
    
    # Filter out duplicates from fallback questions
    non_duplicate_questions = [
        q for q in fallback_questions 
        if not is_duplicate_question(q)
    ]
    
    if non_duplicate_questions:
        return random.choice(non_duplicate_questions)
    else:
        # If all fallbacks are duplicates, return a random one anyway
        print("⚠️ All fallback questions are duplicates, using random one")
        return random.choice(fallback_questions)

def get_pixabay_image():
    """Get a random image from Pixabay API"""
    try:
        api_key = os.environ.get("PIXABAY_KEY")
        if not api_key:
            print("❌ PIXABAY_KEY not found in environment variables")
            return None
            
        categories = ["nature", "landscape", "sky", "mountains", "flowers", "sunset", "forest", "ocean", "people", "business", "technology", "abstract"]
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

def create_engagement_image(question_data):
    """Create engagement-themed image with Pixabay background and question text overlay"""
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
            engaging_colors = [
                '#1a4b8c', '#2c5aa0', '#3d69b4', '#4f78c8', '#6187dc',
                '#2d6a4f', '#3e7c61', '#4f8e73', '#60a085', '#71b297',
                '#495057', '#5c636a', '#6f777e', '#828a91', '#959da4',
                '#8c1a4b', '#a02c5a', '#b43d69', '#c84f78', '#dc6187'
            ]
            bg_color = random.choice(engaging_colors)
            background = Image.new('RGB', (width, height), color=bg_color)
            print("✅ Using fallback solid color background")
    else:
        # Fallback to solid color background
        engaging_colors = [
            '#1a4b8c', '#2c5aa0', '#3d69b4', '#4f78c8', '#6187dc',
            '#2d6a4f', '#3e7c61', '#4f8e73', '#60a085', '#71b297',
            '#495057', '#5c636a', '#6f777e', '#828a91', '#959da4',
            '#8c1a4b', '#a02c5a', '#b43d69', '#c84f78', '#dc6187'
        ]
        bg_color = random.choice(engaging_colors)
        background = Image.new('RGB', (width, height), color=bg_color)
        print("✅ Using fallback solid color background")
    
    # Create drawing context
    draw = ImageDraw.Draw(background)
    
    # Try to load font
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        question_font = ImageFont.truetype(font_path, 58)
    except (IOError, OSError):
        try:
            question_font = ImageFont.truetype("arial.ttf", 58)
        except (IOError, OSError):
            question_font = ImageFont.load_default()
    
    # Wrap the main question text
    max_chars_per_line = 24
    wrapped_question = textwrap.fill(question_data['main_question'], width=max_chars_per_line)
    
    # Calculate text position
    bbox = draw.textbbox((0, 0), wrapped_question, font=question_font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Add question mark or engagement indicator
    engagement_indicators = ["💭", "🤔", "💬", "🗨️", "❓"]
    indicator = random.choice(engagement_indicators)
    
    # Add semi-transparent background for better readability
    padding = 50
    draw.rectangle([
        x - padding, y - padding,
        x + text_width + padding, y + text_height + padding
    ], fill=(0, 0, 0, 150))  # Semi-transparent black
    
    # Draw main question text
    draw.text((x, y), wrapped_question, fill=(255, 255, 255), font=question_font, align='center')
    
    # Draw engagement indicator above the text
    indicator_font_size = 80
    try:
        indicator_font = ImageFont.truetype(font_path, indicator_font_size)
    except:
        indicator_font = ImageFont.load_default()
    
    indicator_bbox = draw.textbbox((0, 0), indicator, font=indicator_font)
    indicator_width = indicator_bbox[2] - indicator_bbox[0]
    indicator_x = (width - indicator_width) // 2
    indicator_y = y - indicator_font_size - 20
    
    draw.text((indicator_x, indicator_y), indicator, fill=(255, 255, 255), font=indicator_font)
    
    # Convert to bytes
    output_buffer = BytesIO()
    background.save(output_buffer, format="JPEG", quality=95)
    return output_buffer.getvalue()

def create_facebook_caption(question_data):
    """Create Facebook caption with engagement question and CTA"""
    # Random header options
    headers = [
        "Let's Chat!",
        "Daily Discussion",
        "Question of the Day",
        "Community Conversation",
        "Your Thoughts?",
        "Let's Talk About It",
        "Share Your Perspective",
        "What Do You Think?"
    ]
    
    header = random.choice(headers)
    
    # Random CTA options focused on engagement
    cta_options = [
        "💬 Share your answer in the comments! Let's get a great discussion going!",
        "👇 Drop your thoughts below! I read every comment and love hearing from you!",
        "🗨️ Let's chat! Comment your answer and reply to others to keep the conversation going!",
        "💭 What's your take? Share below and let's learn from each other's perspectives!",
        "👥 Tag a friend who would have an interesting answer to this question!",
        "📢 Your voice matters! Share your thoughts in the comments and join the discussion!"
    ]
    
    cta = random.choice(cta_options)
    
    caption = f"""{header}

{question_data['main_question']}

💡 {question_data['context']}

{cta}

{question_data['hashtags']}

#EngagementPost #CommunityDiscussion #AudienceEngagement #LetsTalk"""
    
    return caption

def post_to_facebook(image_data, question_data):
    """Post the image to Facebook Page with engagement question caption"""
    try:
        page_id = os.environ.get("FB_PAGE_ID")
        access_token = os.environ.get("FB_PAGE_TOKEN")
        
        if not page_id or not access_token:
            print("❌ Facebook credentials not found in environment variables")
            return False
        
        # Upload image to Facebook
        url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
        
        # Create caption
        caption = create_facebook_caption(question_data)
        
        files = {'source': ('engagement_question.jpg', image_data, 'image/jpeg')}
        data = {'message': caption, 'access_token': access_token}
        
        response = requests.post(url, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            # Save to posted questions history to prevent duplicates
            if save_posted_question(question_data):
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
    print("🚀 Starting audience engagement question generation and posting process...")
    print(f"📁 History file location: {POST_HISTORY_FILE}")
    
    # Check environment variables
    required_env_vars = ["GEMINI_API_KEY", "PIXABAY_KEY", "FB_PAGE_ID", "FB_PAGE_TOKEN"]
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("💡 Please add missing variables to your GitHub Secrets")
        return
    
    # Load existing history to check functionality
    posted_questions = load_posted_questions()
    print(f"📊 Existing questions in history: {len(posted_questions)}")
    
    # Generate engagement question
    question_data = generate_engagement_question()
    print(f"💭 Main Question: {question_data['main_question']}")
    print(f"📝 Context: {question_data['context']}")
    print(f"🏷️ Hashtags: {question_data['hashtags']}")
    
    # Create image with main question text
    final_image = create_engagement_image(question_data)
    print("🎨 Engagement image created")
    
    # Post to Facebook
    success = post_to_facebook(final_image, question_data)
    
    if success:
        print("✅ Process completed successfully! The engagement question has been shared.")
    else:
        print("❌ Process completed with errors")

if __name__ == "__main__":
    main()