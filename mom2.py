import os
import requests
import random
import time
import json
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# ================================
# CONFIGURATION
# ================================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PIXABAY_KEY = os.environ.get("PIXABAY_KEY")
FB_PAGE_TOKEN = os.environ.get("FB_PAGE_TOKEN")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")

# Pixabay queries
PIXABAY_QUERIES = ["parents", "nature", "flowers", "mom", "family"]

# Motivational post topics
POST_TOPICS = [
    "parenting struggle",
    "self-care for moms",
    "encouragement after tough days",
    "balancing work and family",
    "finding small joys",
    "overcoming mom guilt",
    "celebrating small wins",
    "perseverance and patience"
]

# Hashtags pool
HASHTAGS_POOL = ["#MomLife", "#Parenting", "#Motivation", "#Family", "#SelfCare", "#Love", "#DailyInspiration"]

# Font path
FONT_PATH = "fonts/OpenSans-Bold.ttf"

# ================================
# UTILITY FUNCTIONS
# ================================

def pick_random_pixabay_image():
    query = random.choice(PIXABAY_QUERIES)
    url = f"https://pixabay.com/api/?key={PIXABAY_KEY}&q={query}&image_type=photo&orientation=horizontal&per_page=50"
    response = requests.get(url, timeout=15)
    data = response.json()
    hits = data.get("hits", [])
    if not hits:
        print("[WARN] No images found, using fallback image")
        return None
    image_url = random.choice(hits)["largeImageURL"]
    print(f"[INFO] Selected Pixabay image: {image_url}")
    return image_url

def generate_gemini_post(topic):
    prompt = f"""
Create a short motivational post for moms (150-200 chars). Topic: {topic}.
- Do not use first-person (I, me, we, my, our)
- Keep it encouraging and positive
- Include 1-2 emojis at the end
- Return only the post text
"""
    try:
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent",
            params={"key": GEMINI_API_KEY},
            headers={"Content-Type": "application/json"},
            json={"contents":[{"parts":[{"text": prompt}]}]},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            return text
        else:
            print("[WARN] Gemini API failed, using fallback text")
    except Exception as e:
        print("[ERROR] Gemini request failed:", e)
    # fallback
    return "Every mom is doing their best, and that’s enough 💖"

def add_text_to_image(image_url, post_text):
    response = requests.get(image_url, timeout=15)
    img = Image.open(BytesIO(response.content)).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Random text box background color
    bg_color = tuple(random.choices(range(100, 256), k=3))  # pastel color
    font_size = max(20, img.width // 25)
    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except OSError:
        print("[WARN] Font not found, using default")
        font = ImageFont.load_default()

    # Wrap text
    lines = []
    words = post_text.split()
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        w, h = draw.textsize(test_line, font=font)
        if w > img.width * 0.8:
            lines.append(line)
            line = word
        else:
            line = test_line
    lines.append(line)

    # Calculate box size
    line_height = font.getsize("A")[1] + 10
    box_height = line_height * len(lines) + 20
    box_width = int(img.width * 0.85)
    box_x = int(img.width * 0.075)
    box_y = int(img.height * 0.75 - box_height / 2)

    # Draw rectangle
    draw.rectangle([box_x, box_y, box_x + box_width, box_y + box_height], fill=bg_color + (200,), outline=None)

    # Draw text
    y_text = box_y + 10
    for line in lines:
        w, h = draw.textsize(line, font=font)
        x_text = box_x + (box_width - w)/2
        draw.text((x_text, y_text), line, font=font, fill="black")
        y_text += line_height

    # Save image
    filename = f"post_{int(time.time())}.jpg"
    img.save(filename)
    print(f"[INFO] Image saved: {filename}")
    return filename

def generate_caption(post_text):
    hashtags = random.sample(HASHTAGS_POOL, 4)
    emojis = random.sample(["💖","🌸","✨","🌼","🌷","🌞","🌟"], 2)
    caption = f"{post_text} {' '.join(emojis)} {' '.join(hashtags)}"
    return caption

def post_to_facebook(image_path, caption):
    print("[INFO] Posting to Facebook...")
    url = f"https://graph.facebook.com/v17.0/{FB_PAGE_ID}/photos"
    files = {"source": open(image_path, "rb")}
    data = {"caption": caption, "access_token": FB_PAGE_TOKEN}
    response = requests.post(url, files=files, data=data, timeout=30)
    if response.status_code == 200:
        print("[INFO] Successfully posted to Facebook!")
    else:
        print("[ERROR] Facebook post failed:", response.text)

# ================================
# MAIN EXECUTION
# ================================

def main():
    print("[INFO] Mom Motivational Bot Starting...")
    topic = random.choice(POST_TOPICS)
    post_text = generate_gemini_post(topic)
    print("[INFO] Generated Post:", post_text)

    image_url = pick_random_pixabay_image()
    if not image_url:
        print("[ERROR] No image available, exiting.")
        return

    image_path = add_text_to_image(image_url, post_text)
    caption = generate_caption(post_text)
    print("[INFO] Generated Caption:", caption)

    post_to_facebook(image_path, caption)

if __name__ == "__main__":
    main()