#!/usr/bin/env python3
"""
Daily English Quiz Generator and Facebook Poster
Generates English quiz questions with images and posts to Facebook
"""

import os
import random
import textwrap
import requests
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai
from datetime import datetime

def create_quiz_image(question, options, correct_answer):
    """
    Create an engaging quiz image with proper text backgrounds
    """
    # Image dimensions (optimized for Facebook)
    width, height = 1200, 800
    
    # Create background image with a gradient
    image = Image.new('RGB', (width, height), color=(240, 245, 255))
    draw = ImageDraw.Draw(image)
    
    # Add a subtle gradient background
    for y in range(height):
        r = int(240 - (y / height * 20))
        g = int(245 - (y / height * 25))
        b = int(255 - (y / height * 15))
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Try to load installed fonts, fallback to default if not found
    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 48)
        font_question = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
        font_options = ImageFont.truetype("DejaVuSans.ttf", 32)
        font_footer = ImageFont.truetype("DejaVuSans.ttf", 24)
    except IOError:
        print("Using default fonts - DejaVu fonts not found")
        font_title = ImageFont.load_default()
        font_question = ImageFont.load_default()
        font_options = ImageFont.load_default()
        font_footer = ImageFont.load_default()
    
    # Add header decoration
    draw.rectangle([(0, 0), (width, 80)], fill=(59, 89, 152))
    draw.text((width//2, 40), "🇬🇧 English Quiz Time! 🇺🇸", 
              font=font_title, fill=(255, 255, 255), anchor="mm")
    
    y_position = 120
    
    # Draw question with improved background
    question_lines = textwrap.wrap(question, width=35)
    for line in question_lines:
        bbox = draw.textbbox((0, 0), line, font=font_question)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Draw semi-transparent background behind text (full width)
        background_rect = [
            (width - text_width - 100) // 2 - 20, 
            y_position - 10,
            (width + text_width + 100) // 2 + 20, 
            y_position + text_height + 10
        ]
        draw.rectangle(background_rect, fill=(255, 255, 255, 200), outline=(200, 200, 200), width=2)
        
        # Draw text centered
        draw.text((width//2, y_position), line, font=font_question, 
                 fill=(50, 50, 50), anchor="mm")
        y_position += text_height + 20
    
    y_position += 40
    
    # Draw options with nice backgrounds
    for i, option in enumerate(options):
        option_text = f"{chr(65+i)}) {option}"
        bbox = draw.textbbox((0, 0), option_text, font=font_options)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Draw option background (full width)
        option_rect = [
            (width - text_width - 80) // 2 - 25, 
            y_position - 8,
            (width + text_width + 80) // 2 + 25, 
            y_position + text_height + 8
        ]
        
        # Different colors for options
        option_colors = [(230, 240, 255), (240, 255, 240), (255, 240, 240), (255, 255, 230)]
        draw.rounded_rectangle(option_rect, radius=15, fill=option_colors[i], 
                              outline=(180, 180, 180), width=1)
        
        # Draw option text
        draw.text((width//2, y_position), option_text, font=font_options, 
                 fill=(40, 40, 40), anchor="mm")
        y_position += text_height + 25
    
    # Add footer with instructions
    footer_text = "💡 Comment your answer below! The correct answer will be revealed tomorrow."
    draw.text((width//2, height - 50), footer_text, font=font_footer, 
             fill=(100, 100, 100), anchor="mm")
    
    # Add decorative elements
    draw.rectangle([(0, height-80), (width, height)], fill=(245, 245, 245))
    draw.text((width//2, height-30), "📚 Daily English Learning • Follow for more! 📚", 
              font=font_footer, fill=(100, 100, 100), anchor="mm")
    
    return image

def generate_english_question():
    """
    Generate an English quiz question with options
    """
    question_templates = [
        {
            "question": "Fill in the blank: 'She _____ to the store yesterday.'",
            "options": ["goed", "went", "gone", "go"],
            "correct": "went"
        },
        {
            "question": "Select the correct option: 'Which verb completes this sentence: He _____ very fast.'",
            "options": ["runned", "ran", "run", "running"],
            "correct": "ran"
        },
        {
            "question": "Can you complete this: 'If I had known, I _____ differently.'",
            "options": ["would have acted", "would acted", "will act", "acted"],
            "correct": "would have acted"
        },
        {
            "question": "Choose the right word: 'The weather is _____ today than yesterday.'",
            "options": ["more better", "better", "gooder", "best"],
            "correct": "better"
        },
        {
            "question": "Which is correct: 'There are too _____ people in the room.'",
            "options": ["much", "many", "lot", "few"],
            "correct": "many"
        },
        {
            "question": "Fill the blank: 'I _____ my homework every day.'",
            "options": ["do", "does", "did", "done"],
            "correct": "do"
        }
    ]
    
    return random.choice(question_templates)

def generate_with_gemini(api_key):
    """
    Generate a question using Gemini AI (fallback if available)
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = """Generate one English grammar quiz question in JSON format with:
        - question: engaging question starting with "Fill in the blank", "Select the correct option", or "Can you complete this"
        - options: 4 plausible options where one is correct
        - correct: the correct option text
        
        Example: {
            "question": "Fill in the blank: 'She _____ to the store yesterday.'",
            "options": ["goed", "went", "gone", "go"],
            "correct": "went"
        }"""
        
        response = model.generate_content(prompt)
        # Parse response (this is simplified - you might need more robust parsing)
        return response.text
    except Exception as e:
        print(f"Gemini API error: {e}")
        return None

def post_to_facebook(image_path, message, page_id, access_token):
    """
    Post the quiz image to Facebook page
    """
    try:
        # Upload image
        post_url = f"https://graph.facebook.com/v23.0/{page_id}/photos"
        payload = {
            'message': message,
            'access_token': access_token
        }
        
        with open(image_path, 'rb') as image_file:
            files = {'source': image_file}
            response = requests.post(post_url, data=payload, files=files)
        
        if response.status_code == 200:
            post_data = response.json()
            print("✅ Successfully posted to Facebook!")
            return post_data.get('post_id', post_data.get('id'))
        else:
            print(f"❌ Error posting to Facebook: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Facebook posting error: {e}")
        return None

def main():
    """
    Main function to generate and post the daily quiz
    """
    print("🚀 Starting daily English quiz generation...")
    
    # Get environment variables
    gemini_api_key = os.environ.get('GEMINI_API_KEY')
    fb_page_token = os.environ.get('FB_PAGE_TOKEN')
    fb_page_id = os.environ.get('FB_PAGE_ID')
    
    # Generate question (try Gemini first, then fallback)
    question_data = None
    if gemini_api_key:
        question_data = generate_with_gemini(gemini_api_key)
    
    if not question_data:
        question_data = generate_english_question()
        print("Using predefined question (Gemini not available)")
    
    question = question_data["question"]
    options = question_data["options"]
    correct_answer = question_data["correct"]
    
    print(f"📝 Question: {question}")
    print(f"📋 Options: {options}")
    print(f"✅ Correct: {correct_answer}")
    
    # Create engaging image
    image = create_quiz_image(question, options, correct_answer)
    image_path = "daily_english_quiz.png"
    image.save(image_path, quality=95)
    print("🖼️ Image created successfully!")
    
    # Create Facebook message
    message = f"""🤔 ENGLISH QUIZ TIME! 🤔

{question}

Options:
{' • '.join([f'{chr(65+i)}) {opt}' for i, opt in enumerate(options)])}

💭 Think you know the answer? Drop your guess in the comments! 
We'll reveal the correct answer tomorrow! ⏳

✨ Follow for daily English lessons and tips! ✨

#EnglishQuiz #LearnEnglish #Grammar #EnglishGrammar #FillInTheBlank 
#LanguageLearning #ESL #EnglishTeacher #DailyEnglish"""
    
    # Post to Facebook if credentials available
    if fb_page_token and fb_page_id:
        post_id = post_to_facebook(image_path, message, fb_page_id, fb_page_token)
        if post_id:
            print(f"🔗 View your post at: https://www.facebook.com/{post_id}")
        else:
            print("💾 Image saved locally (facebook.com/{post_id})")
    else:
        print("ℹ️ Facebook credentials not found. Image saved locally.")
        print("💾 Image saved as:", image_path)
    
    print("🎉 Daily quiz process completed!")

if __name__ == "__main__":
    main()