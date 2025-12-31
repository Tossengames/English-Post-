import os
import requests
import random
import textwrap
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime

# ================================
# CONFIGURATION
# ================================
PIXABAY_KEY = os.environ.get('PIXABAY_KEY')
FACEBOOK_PAGE_TOKEN = os.environ.get('FB_PAGE_TOKEN')
FACEBOOK_PAGE_ID = os.environ.get('FB_PAGE_ID')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Pixabay queries for images
PIXABAY_QUERIES = ["parents", "nature", "flowers", "mother child", "family outdoors"]

# Motivational topics parameters
POST_TOPICS = [
    "parenting struggles",
    "self-care for moms",
    "family bonding",
    "life lessons for kids",
    "overcoming challenges",
    "finding balance"
]

# Hashtags to choose from
HASHTAGS = ["#MomLife", "#Parenting", "#Motivation", "#Family", "#Inspiration", "#SelfCare"]

# ================================
# FUNCTIONS
# ================================

def get_random_pixabay_image():
    query = random.choice(PIXABAY_QUERIES)
    url = f"https://pixabay.com/api/?key={PIXABAY_KEY}&q={query}&image_type=photo&orientation=horizontal&safesearch=true&per_page=50"
    response = requests.get(url, timeout=30)
    data = response.json()
    if data.get("hits"):
        image_url = random.choice(data["hits"])["largeImageURL"]
        print(f"[INFO] Selected Pixabay image: {image_url}")
        return image_url
    print("[WARN] No image found, using fallback")
    return None

def generate_motivational_text():
    topic = random.choice(POST_TOPICS)
    prompt = f"""
Generate a motivational, uplifting post for moms. Topic: {topic}.
Rules:
- Keep it encouraging and positive
- No first-person pronouns
- Max 200 characters
Return only the post text.
"""
    try:
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent",
            params={"key": GEMINI_API_KEY},
            headers={"Content-Type": "application/json"},
            json={"contents":[{"parts":[{"text": prompt}]}]},
            timeout=30
        )
        data = response.json()
        if "candidates" in data and data["candidates"]:
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            print(f"[INFO] Generated post text: {text}")
            return text
    except Exception as e:
        print(f"[ERROR] AI generation failed: {e}")
    fallback_text = "Every mom is doing their best, and that’s enough. 💖"
    print(f"[INFO] Using fallback text: {fallback_text}")
    return fallback_text

def add_text_to_image(image_url, text):
    try:
        response = requests.get(image_url, timeout=30)
        image = Image.open(io.BytesIO(response.content)).convert("RGB")
    except Exception as e:
        print(f"[ERROR] Failed to download image: {e}")
        image = Image.new("RGB", (1080, 1080), (255, 255, 255))

    draw = ImageDraw.Draw(image)
    width, height = image.size

    # Random background box color
    box_color = tuple(random.randint(200, 255) for _ in range(3))
    font_size = max(30, width // 25)
    font = ImageFont.truetype("arial.ttf", font_size)

    # Wrap text
    wrapped_text = textwrap.fill(text, width=25)
    text_width, text_height = draw.multiline_textsize(wrapped_text, font=font)

    # Random position
    x = random.randint(20, max(20, width - text_width - 20))
    y = random.randint(20, max(20, height - text_height - 20))

    # Draw background box
    draw.rectangle(
        [x-10, y-10, x + text_width + 10, y + text_height + 10],
        fill=box_color
    )
    # Draw text
    draw.multiline_text((x, y), wrapped_text, fill=(0,0,0), font=font)

    final_path = "post_final.jpg"
    image.save(final_path)
    print(f"[INFO] Image saved with text: {final_path}")
    return final_path

def generate_caption():
    hashtags = random.sample(HASHTAGS, 4)
    emojis = random.sample(["💖","🌸","✨","🌼","😊","🌿"], 3)
    caption = " ".join(emojis) + " " + " ".join(hashtags)
    print(f"[INFO] Generated caption: {caption}")
    return caption

def post_to_facebook(image_path, caption):
    try:
        with open(image_path, "rb") as img_file:
            files = {"source": img_file}
            data = {"caption": caption, "access_token": FACEBOOK_PAGE_TOKEN}
            response = requests.post(f"https://graph.facebook.com/{FACEBOOK_PAGE_ID}/photos", files=files, data=data)
            if response.status_code == 200:
                print("[INFO] Successfully posted to Facebook!")
            else:
                print(f"[ERROR] Facebook post failed: {response.text}")
    except Exception as e:
        print(f"[ERROR] Posting to Facebook failed: {e}")

# ================================
# MAIN EXECUTION
# ================================

def main():
    print(f"[INFO] Script started at {datetime.now()}")
    post_text = generate_motivational_text()
    image_url = get_random_pixabay_image()
    image_path = add_text_to_image(image_url, post_text)
    caption = generate_caption()
    post_to_facebook(image_path, caption)
    print(f"[INFO] Script finished at {datetime.now()}")

if __name__ == "__main__":
    main()