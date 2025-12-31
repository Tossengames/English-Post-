#!/usr/bin/env python3
"""
Parenting Humor Post Generator:
Fetch Reddit/Parenting RSS, generate humorous posts using Gemini,
create images using Pixabay backgrounds, and post to Facebook.
Detailed logging included.
"""

import os
import requests
import random
import time
import json
import feedparser
from datetime import datetime
import re
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import hashlib

# ================================
# CONFIGURATION
# ================================

FB_PAGE_TOKEN = os.environ.get("FB_PAGE_TOKEN")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
POST_HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "posted_parenting.json")

RSS_FEEDS = [
    "https://www.reddit.com/r/ParentingHumor/.rss",
    "https://www.reddit.com/r/funny/.rss",
    "https://www.reddit.com/r/MomForAMinute/.rss",
]

HASHTAGS = [
    "#ParentingHumor", "#MomLife", "#DadLife", "#FunnyKids",
    "#ParentingStruggles", "#Humor", "#Toddlers", "#LifeWithKids"
]

PIXABAY_CATEGORIES = ["funny", "parenting", "kids", "home", "family"]

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

def fetch_rss_posts():
    log("Fetching RSS posts...")
    all_posts = []
    headers = {"User-Agent": "ParentHumorBot/1.0"}
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                title = entry.title
                # Exclude first-person references
                if any(word in title.lower() for word in ["i ", "my ", "me "]):
                    continue
                all_posts.append(title)
        except Exception as e:
            log(f"Error parsing {feed_url}: {e}")
    random.shuffle(all_posts)
    log(f"Fetched {len(all_posts)} valid posts")
    return all_posts

def get_pixabay_image():
    api_key = os.environ.get("PIXABAY_KEY")
    if not api_key:
        log("PIXABAY_KEY not set")
        return None

    category = random.choice(PIXABAY_CATEGORIES)
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
    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        if data.get("hits"):
            image_url = random.choice(data["hits"])["largeImageURL"]
            img_response = requests.get(image_url, timeout=15)
            return BytesIO(img_response.content)
    except Exception as e:
        log(f"Error fetching Pixabay image: {e}")
    return None

def create_image(post_text):
    log("Creating image for post...")
    width, height = 1200, 1200
    image_bytes = get_pixabay_image()
    if image_bytes:
        background = Image.open(image_bytes).resize((width, height), Image.LANCZOS)
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.7)
    else:
        bg_color = random.choice(['#FFB6C1', '#FFD700', '#87CEFA', '#98FB98', '#FFA07A'])
        background = Image.new('RGB', (width, height), bg_color)

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

    # Semi-transparent box behind text
    draw.rectangle([x-30, y-30, x+text_width+30, y+text_height+30], fill=(0,0,0,150))
    draw.text((x, y), wrapped_text, fill=(255,255,255), font=font, align='center')

    output = BytesIO()
    background.save(output, format="JPEG", quality=95)
    log("Image created successfully")
    return output.getvalue()

def generate_post_text(posts):
    if not posts:
        return "Nothing funny trending in parenting right now… stay tuned! 😅"

    article = random.choice(posts)
    summary = re.sub(r"<[^>]+>", "", article)[:200]

    prompt = f"""
Generate a funny, witty, parenting humor post.

Topic: {article}
Details: {summary}

Rules:
- Keep it funny, no personal pronouns
- Include 3-5 emojis
- Include 3-5 relevant hashtags at the end
- Max 250 characters
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
    return f"{article} 🤣 #ParentingHumor"

def create_caption(post_text):
    hashtags = " ".join(random.sample(HASHTAGS, 4))
    return f"{post_text}\n\n{hashtags}"

def post_to_facebook(image_data, caption):
    log("Posting to Facebook...")
    if not FB_PAGE_TOKEN or not FB_PAGE_ID:
        log("Facebook credentials not set")
        return False

    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
    files = {'source': ('parenting.jpg', image_data, 'image/jpeg')}
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
    log("Parenting Humor Bot Starting...")
    if not FB_PAGE_TOKEN or not FB_PAGE_ID or not GEMINI_API_KEY:
        log("❌ Missing required secrets")
        return

    posts = fetch_rss_posts()
    if not posts:
        log("No posts fetched from RSS feeds")
        return

    for post_text in posts:
        if not is_duplicate(post_text):
            text = generate_post_text([post_text])
            image = create_image(text)
            caption = create_caption(text)
            post_to_facebook(image, caption)
            break
    else:
        log("All posts are duplicates")

if __name__ == "__main__":
    main()