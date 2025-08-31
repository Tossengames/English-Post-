#!/usr/bin/env python3
"""
Simple script to generate English quizzes with Gemini AI, create image with Pollinations,
overlay properly formatted text, and post to Facebook Page.
"""

import os
import requests
import random
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from google import genai
from io import BytesIO

# Your Facebook page link
FB_PAGE_LINK = "https://www.facebook.com/engleasyapp"

def generate_grammar_challenge():
    """Generate an English quiz with missing word and 3 options using Gemini 2.0 Flash"""
    try:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        
        prompt = """
        Create a SHORT English quiz exercise with one word missing, replaced by a blank (____).
        Focus on: verb tenses, prepositions, articles, adjectives. Keep the sentence UNDER 8 WORDS total.
        Provide 3 multiple-choice options: one correct answer and two incorrect options.
        
        Rules:
        1. Maximum 8 words total in the sentence
        2. Must have exactly one blank (____)
        3. Provide ONLY 3 options: A, B, C
        4. Make options short (1-2 words each)
        5. Start the challenge with phrases like: "Fill in the blank:", "Select the correct option:", "Can you complete:", "Choose the right word:"
        6. Format the response exactly like this:
        
        CHALLENGE: [Fill in the blank/Select the correct option/Can you complete: Short sentence with ____]
        OPTIONS:
        A) [Option 1]
        B) [Option 2]
        C) [Option 3]
        ANSWER: [Letter of correct option]
        
        Examples:
        
        CHALLENGE: Fill in the blank: She ____ to school.
        OPTIONS:
        A) walked
        B) walking
        C) walks
        ANSWER: A
        
        CHALLENGE: Select the correct option: I'm good ____ math.
        OPTIONS:
        A) at
        B) in
        C) on
        ANSWER: A
        
        CHALLENGE: Can you complete: This is ____ book.
        OPTIONS:
        A) a
        B) an
        C) the
        ANSWER: A
        """
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        
        response_text = response.text.strip()
        print(f"Gemini response:\n{response_text}")
        
        # Parse the response
        lines = response_text.split('\n')
        challenge = ""
        options = []
        correct_answer = ""
        
        for line in lines:
            if line.startswith('CHALLENGE:'):
                challenge = line.replace('CHALLENGE:', '').strip()
            elif line.startswith('A)') or line.startswith('B)') or line.startswith('C)'):
                options.append(line.strip())
            elif line.startswith('ANSWER:'):
                correct_answer = line.replace('ANSWER:', '').strip()
        
        # Validate we got all components
        if not challenge or len(options) != 3 or not correct_answer:
            raise Exception("Invalid response format from Gemini")
        
        return {
            'challenge': challenge,
            'options': options,
            'correct_answer': correct_answer
        }
        
    except Exception as e:
        print(f"Error generating grammar challenge: {e}")
        # Fallback challenges with better phrasing
        fallback_challenges = [
            {
                'challenge': 'Fill in the blank: She ____ home.',
                'options': ['A) ran', 'B) run', 'C) running'],
                'correct_answer': 'A'
            },
            {
                'challenge': 'Select the correct option: I like ____.',
                'options': ['A) pizza', 'B) run', 'C) blue'],
                'correct_answer': 'A'
            },
            {
                'challenge': 'Can you complete: He ____ fast.',
                'options': ['A) runs', 'B) running', 'C) ran'],
                'correct_answer': 'A'
            },
            {
                'challenge': 'Choose the right word: We ____ there.',
                'options': ['A) went', 'B) go', 'C) going'],
                'correct_answer': 'A'
            },
            {
                'challenge': 'Fill in the blank: It is ____.',
                'options': ['A) cold', 'B) colder', 'C) coldest'],
                'correct_answer': 'A'
            }
        ]
        return random.choice(fallback_challenges)

def generate_image_with_pollinations(challenge):
    """Generate image based on challenge text using Pollinations.AI"""
    try:
        # Remove the blank for image generation but keep the context
        clean_prompt = challenge.replace('____', 'something').replace('"', '').replace("'", "")
        # Remove the instruction prefix for better image generation
        clean_prompt = clean_prompt.replace('Fill in the blank:', '').replace('Select the correct option:', '').replace('Can you complete:', '').replace('Choose the right word:', '').strip()
        pollinations_url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1200&height=1200&nologo=true&quality=0.9"
        
        response = requests.get(pollinations_url, timeout=30)
        if response.status_code == 200:
            print("Image successfully generated with Pollinations")
            return response.content
        else:
            raise Exception(f"Pollinations API returned status {response.status_code}")
            
    except Exception as e:
        print(f"Error generating image with Pollinations: {e}")
        return None

def create_fallback_image():
    """Create a simple fallback image with random color background"""
    width, height = 1200, 1200
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3C91E6', '#342E37']
    bg_color = random.choice(colors)
    
    image = Image.new('RGB', (width, height), color=bg_color)
    return image

def add_challenge_to_image(image_data, challenge_data):
    """Add challenge content to the image with proper formatting - normal width backgrounds"""
    try:
        # Open image
        if isinstance(image_data, bytes):
            image = Image.open(BytesIO(image_data))
        else:
            image = image_data
        
        # Enhance image brightness/contrast if needed
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(0.9)
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.1)
        
        draw = ImageDraw.Draw(image)
        width, height = image.size
        
        # Extract just the sentence part (remove "Fill in the blank:" etc.)
        full_challenge = challenge_data['challenge']
        if ": " in full_challenge:
            # Remove the instruction part, keep only the sentence
            sentence = full_challenge.split(": ", 1)[1]
        else:
            sentence = full_challenge
        
        options = challenge_data['options']
        
        # Use large fonts
        try:
            sentence_font = ImageFont.truetype("arial.ttf", 70)
            options_font = ImageFont.truetype("arial.ttf", 55)
            inst_font = ImageFont.truetype("arial.ttf", 40)
        except:
            try:
                sentence_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 70)
                options_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 55)
                inst_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 40)
            except:
                sentence_font = ImageFont.load_default()
                options_font = ImageFont.load_default()
                inst_font = ImageFont.load_default()
        
        # Draw sentence (centered at top) with normal width background
        s_bbox = draw.textbbox((0, 0), sentence, font=sentence_font)
        s_width = s_bbox[2] - s_bbox[0]
        s_height = s_bbox[3] - s_bbox[1]
        s_x = (width - s_width) // 2
        s_y = 100
        
        # Add normal width background for sentence (like original script)
        draw.rectangle([
            s_x - 20, s_y - 20,
            s_x + s_width + 20, s_y + s_height + 20
        ], fill=(0, 0, 0, 180))
        
        draw.text((s_x, s_y), sentence, fill=(255, 255, 255), font=sentence_font)
        
        # Draw options (centered) with normal width backgrounds
        option_y = 400
        
        for i, option in enumerate(options):
            o_bbox = draw.textbbox((0, 0), option, font=options_font)
            o_width = o_bbox[2] - o_bbox[0]
            o_height = o_bbox[3] - o_bbox[1]
            o_x = (width - o_width) // 2
            
            # Add normal width background for each option (like original script)
            draw.rectangle([
                o_x - 20, option_y - 15,
                o_x + o_width + 20, option_y + o_height + 15
            ], fill=(0, 0, 0, 160))
            
            draw.text((o_x, option_y), option, fill=(255, 255, 255), font=options_font)
            option_y += 100  # Space between options
        
        # Add instruction at bottom with normal width background
        instruction = "💡 Comment A, B, or C with your answer! 👇"
        i_bbox = draw.textbbox((0, 0), instruction, font=inst_font)
        i_width = i_bbox[2] - i_bbox[0]
        i_height = i_bbox[3] - i_bbox[1]
        i_x = (width - i_width) // 2
        i_y = height - 120
        
        # Normal width background for instruction
        draw.rectangle([
            i_x - 20, i_y - 15,
            i_x + i_width + 20, i_y + i_height + 15
        ], fill=(0, 0, 0, 200))
        
        draw.text((i_x, i_y), instruction, fill=(255, 255, 255), font=inst_font)
        
        # Save to bytes
        output_buffer = BytesIO()
        image.save(output_buffer, format="JPEG", quality=95)
        return output_buffer.getvalue()
        
    except Exception as e:
        print(f"Error adding challenge to image: {e}")
        output_buffer = BytesIO()
        image.save(output_buffer, format="JPEG", quality=95)
        return output_buffer.getvalue()

def process_image(challenge_data):
    """Process image - generate or create fallback, then add challenge content"""
    image_data = generate_image_with_pollinations(challenge_data['challenge'])
    
    if image_data:
        print("Using Pollinations generated image")
        return add_challenge_to_image(image_data, challenge_data)
    else:
        print("Using fallback image with colored background")
        fallback_image = create_fallback_image()
        return add_challenge_to_image(fallback_image, challenge_data)

def post_to_facebook(image_data, challenge_data):
    """Post the image to Facebook Page with improved caption including page links"""
    try:
        page_id = os.environ["FB_PAGE_ID"]
        access_token = os.environ["FB_PAGE_TOKEN"]
        
        url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
        
        # Create engaging caption without "Grammar Challenge"
        options_text = "\n".join(challenge_data['options'])
        
        # Use different engaging starters based on the challenge
        challenge_text = challenge_data['challenge']
        if "Fill in the blank" in challenge_text:
            starter = "🤔 Fill in the blank!"
        elif "Select the correct option" in challenge_text:
            starter = "🔍 Select the correct option!"
        elif "Can you complete" in challenge_text:
            starter = "💭 Can you complete this?"
        elif "Choose the right word" in challenge_text:
            starter = "🎯 Choose the right word!"
        else:
            starter = "🧠 English Quiz Time!"
        
        # Extract just the sentence for the caption
        if ": " in challenge_text:
            sentence_part = challenge_text.split(": ", 1)[1]
        else:
            sentence_part = challenge_text
        
        # Create caption with page links at beginning and end
        caption = f"""📚 Follow for daily English quizzes: {FB_PAGE_LINK}

{starter}

{sentence_part}

{options_text}

💬 Comment your answer below! We'll reveal the correct answer tomorrow! ⏳

✨ Follow for more English practice: {FB_PAGE_LINK} ✨

#EnglishQuiz #LearnEnglish #GrammarPractice #FillInTheBlank 
#LanguageLearning #ESL #EnglishPractice #DailyEnglish"""
        
        files = {'source': ('image.jpg', image_data, 'image/jpeg')}
        data = {'message': caption, 'access_token': access_token}
        
        response = requests.post(url, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Successfully posted to Facebook! Post ID: {result.get('id')}")
            print(f"Correct answer: {challenge_data['correct_answer']}")
            return True
        else:
            print(f"Facebook API error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error posting to Facebook: {e}")
        return False

def main():
    """Main function to run the entire process"""
    print("Starting English quiz generation and posting process...")
    
    # Generate challenge content
    challenge_data = generate_grammar_challenge()
    print(f"Full Challenge: {challenge_data['challenge']}")
    
    # Extract just the sentence part for display
    if ": " in challenge_data['challenge']:
        sentence_part = challenge_data['challenge'].split(": ", 1)[1]
        print(f"Sentence only: {sentence_part}")
    else:
        sentence_part = challenge_data['challenge']
        print(f"Sentence only: {sentence_part}")
    
    print(f"Options: {challenge_data['options']}")
    print(f"Correct answer: {challenge_data['correct_answer']}")
    
    # Process image with challenge content
    final_image = process_image(challenge_data)
    print("Image with challenge content created")
    
    # Post to Facebook
    success = post_to_facebook(final_image, challenge_data)
    
    if success:
        print("Process completed successfully!")
    else:
        print("Process completed with errors")

if __name__ == "__main__":
    main()