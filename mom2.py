#!/usr/bin/env python3
"""
Motivational Moms Post Generator:
Generate parenting/mom motivational posts using Gemini,
create images with random color text boxes, and post to Facebook.
"""

import os
import random
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import hashlib
from datetime import datetime
import json

# ================================
# CONFIGURATION
# ================================

FB_PAGE_TOKEN = os.environ.get("FB_PAGE_TOKEN")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
POST_HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "posted_parenting.json")

HASHTAGS = [
    "#MomLife", "#ParentingMotivation", "#MomStrong", "#ParentingJourney",
    "#FamilyFirst", "#MomPower", "#ParentingWisdom", "#MomGoals"
]

# ================================
# HELPER FUNCTIONS
# ================================

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def load_posted_posts():
    try:
        if os.path.exists(POST_HISTORY_FILE):
            with open(POST_HISTORY_FILE, "r") as f:
                content = f.read().strip()
                return json.loads(content) if content else []
        return []
    except Exception as e:
        log(f"Error loading post history: {e}")
        return []

def save_post(post_text):
    posted_posts = load_posted_posts()
    post_hash = hashlib.md5(post_text.encode()).hexdigest()
    if post_hash not in posted_posts:
        posted_posts.append(post_hash)
        os.makedirs(os.path.dirname(POST_HISTORY_FILE), exist_ok=True)
        with open(POST_HISTORY_FILE, "w") as f:
            json.dump(posted_posts, f)
        return True
    return False

def is_duplicate(post_text):
    posted_posts = load_posted_posts()
    post_hash = hashlib.md5(post_text.encode()).hexdigest()
    return post_hash in posted_posts

def generate_post_text():
    prompt = """
Generate a motivational, uplifting, and inspiring post for moms.
Rules:
- No personal pronouns (I, me, my, we, our)
- Include 2-3 relevant emojis
- Max 250 characters
- Make it positive, encouraging, and relatable
Return only the post text.
"""
    try:
        log("Generating post text via Gemini...")
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent",
            params={"key": GEMINI_API_KEY},
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            if "candidates" in data and data["candidates"]:
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                log("Post generated successfully")
                return text
    except Exception as e:
        log(f"Gemini generation error: {e}")
    return "Moms are superheroes 💪❤️ Keep shining every day! #MomLife #ParentingMotivation"

def create_image(post_text):
    log("Creating image for post...")
    width, height = 1200, 1200
    bg_color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
    background = Image.new('RGB', (width, height), (255, 255, 255))

    draw = ImageDraw.Draw(background)
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        font = ImageFont.truetype(font_path, 60)
    except Exception:
        font = ImageFont.load_default()

    # Wrap text
    import textwrap
    wrapped_text = textwrap.fill(post_text, width=25)
    bbox = draw.textbbox((0, 0), wrapped_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2

    # Random color box behind text
    box_color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
    draw.rectangle([x-30, y-30, x+text_width+30, y+text_height+30], fill=box_color)
    draw.text((x, y), wrapped_text, fill=(0,0,0), font=font, align='center')

    output = BytesIO()
    background.save(output, format="JPEG", quality=95)
    log("Image created successfully")
    return output.getvalue()

def create_caption(post_text):
    hashtags = " ".join(random.sample(HASHTAGS, 4))
    return f"{post_text}\n\n{hashtags}"

def post_to_facebook(image_data, caption):
    log("Posting to Facebook...")
    if not FB_PAGE_TOKEN or not FB_PAGE_ID:
        log("Facebook credentials not set")
        return False

    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
    files = {'source': ('mom_post.jpg', image_data, 'image/jpeg')}
    data = {'message': caption, 'access_token': FB_PAGE_TOKEN}

    try:
        response = requests.post(url, files=files, data=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            save_post(caption)
            log(f"Post successfully published: {result.get('id')}")
            return True
        else:
            log(f"Facebook API error {response.status_code}: {response.text}")
            return False
    except Exception as e:
        log(f"Error posting to Facebook: {e}")
        return False

# ================================
# MAIN EXECUTION
# ================================

def main():
    log("Motivational Moms Bot Starting...")
    if not FB_PAGE_TOKEN or not FB_PAGE_ID or not GEMINI_API_KEY:
        log("❌ Missing required secrets")
        return

    post_text = generate_post_text()
    if is_duplicate(post_text):
        log("Generated post is a duplicate, skipping...")
        return

    image = create_image(post_text)
    caption = create_caption(post_text)
    post_to_facebook(image, caption)

if __name__ == "__main__":
    main()