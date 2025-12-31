import os
import requests
import random
import textwrap
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# ================================
# CONFIGURATION
# ================================
FB_PAGE_TOKEN = os.environ.get('FB_PAGE_TOKEN')
FB_PAGE_ID = os.environ.get('FB_PAGE_ID')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
PIXABAY_KEY = os.environ.get('PIXABAY_KEY')

# Pixabay image query options
PIXABAY_QUERIES = ["parents", "mother child", "nature", "flowers"]

# Random post parameters
TONES = ["encouraging", "uplifting", "motivational", "inspirational", "hopeful"]
TOPICS = ["parenting", "self-care", "bonding", "resilience", "overcoming challenges"]
HOOKS = ["Remember:", "Never forget:", "Keep in mind:", "Always remember:", "A gentle reminder:"]
ENDINGS = ["You’ve got this!", "Keep shining!", "Stay strong!", "Every day counts.", "Your effort matters."]
SUBJECTS = [
    "encouragement on tough parenting days",
    "celebrating small wins as a mom",
    "finding peace amidst chaos",
    "bonding with children in meaningful ways",
    "self-care for busy parents",
    "overcoming guilt and perfectionism",
    "finding joy in simple moments",
    "resilience and perseverance for moms"
]

# Hashtags for captions
HASHTAGS = ["#Parenting", "#MomLife", "#Motivation", "#SelfCare", "#Inspiration", "#Family"]

# Font path (adjust if needed)
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# ================================
# UTILITY FUNCTIONS
# ================================
def call_gemini(prompt):
    try:
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
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        print(f"Gemini error: {response.status_code} {response.text}")
    except Exception as e:
        print("Gemini API call failed:", e)
    return None

def generate_random_post_text():
    tone = random.choice(TONES)
    topic = random.choice(TOPICS)
    hook = random.choice(HOOKS)
    ending = random.choice(ENDINGS)
    subject = random.choice(SUBJECTS)
    seed = random.randint(1000, 9999)

    prompt = f"""
Generate a motivational post for moms.
Tone: {tone}
Focus: {topic}
Subject: {subject}
Hook: {hook}
Ending: {ending}
Rules:
- No personal pronouns (I, me, my, we, our)
- Max 250 characters
- Use different wording each time
- Random seed: {seed}
Return only the post text.
"""
    post_text = call_gemini(prompt)
    if not post_text:
        post_text = f"{hook} {subject.capitalize()}. {ending}"
    print("Generated post text:", post_text)
    return post_text

def pick_pixabay_image():
    query = random.choice(PIXABAY_QUERIES)
    url = f"https://pixabay.com/api/?key={PIXABAY_KEY}&q={query}&image_type=photo&orientation=horizontal&per_page=50"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if data["hits"]:
            image_url = random.choice(data["hits"])["largeImageURL"]
            print(f"Picked Pixabay image for '{query}': {image_url}")
            return image_url
    except Exception as e:
        print("Pixabay API error:", e)
    return None

def download_image(url, path="post_image.jpg"):
    try:
        r = requests.get(url, stream=True, timeout=15)
        if r.status_code == 200:
            with open(path, 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            print("Image downloaded:", path)
            return path
    except Exception as e:
        print("Failed to download image:", e)
    return None

def add_text_to_image(image_path, text):
    try:
        img = Image.open(image_path).convert("RGB")
        draw = ImageDraw.Draw(img)
        font_size = 40
        font = ImageFont.truetype(FONT_PATH, font_size)

        img_width, img_height = img.size
        margin = 50
        text_wrapped = textwrap.fill(text, width=30)
        text_width, text_height = draw.multiline_textsize(text_wrapped, font=font)
        x0 = random.randint(margin, img_width - text_width - margin)
        y0 = random.randint(margin, img_height - text_height - margin)
        x1, y1 = x0 + text_width + 20, y0 + text_height + 20
        bg_color = tuple(random.randint(200, 255) for _ in range(3))
        draw.rectangle([x0, y0, x1, y1], fill=bg_color)
        draw.multiline_text((x0 + 10, y0 + 10), text_wrapped, fill="black", font=font)
        img.save("post_final.jpg")
        print("Text added to image: post_final.jpg")
        return "post_final.jpg"
    except Exception as e:
        print("Failed to add text to image:", e)
        return image_path

def generate_caption(post_text):
    hashtags = " ".join(random.sample(HASHTAGS, 4))
    emojis = "".join(random.choices(["🌸", "💪", "🌞", "🌈", "👩‍👧‍👦"], k=3))
    caption = f"{post_text}\n\n{emojis} {hashtags}"
    print("Generated caption:", caption)
    return caption

def post_to_facebook(image_path, caption):
    try:
        print("Posting to Facebook...")
        files = {"source": open(image_path, "rb")}
        data = {"caption": caption, "access_token": FB_PAGE_TOKEN}
        url = f"https://graph.facebook.com/v17.0/{FB_PAGE_ID}/photos"
        r = requests.post(url, files=files, data=data, timeout=30)
        if r.status_code == 200:
            print("✅ Successfully posted to Facebook")
            return True
        else:
            print("❌ Facebook post failed:", r.status_code, r.text)
    except Exception as e:
        print("Facebook posting error:", e)
    return False

# ================================
# MAIN EXECUTION
# ================================
def main():
    print("Motivational Moms Bot Starting...")

    if not FB_PAGE_TOKEN or not FB_PAGE_ID or not GEMINI_API_KEY or not PIXABAY_KEY:
        print("❌ Missing environment variables")
        return

    post_text = generate_random_post_text()
    image_url = pick_pixabay_image()
    if not image_url:
        print("❌ No image found, exiting")
        return
    image_path = download_image(image_url)
    if not image_path:
        print("❌ Image download failed, exiting")
        return
    final_image = add_text_to_image(image_path, post_text)
    caption = generate_caption(post_text)
    post_to_facebook(final_image, caption)

if __name__ == "__main__":
    main()