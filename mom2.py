#!/usr/bin/env python3
"""
Funny Parenting Post Generator: Fetch Reddit RSS, generate humorous parenting content,
create images using Pixabay backgrounds, and post to Facebook Page.
"""

import os
import requests
import random
import textwrap
import json
import hashlib
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import feedparser
import time

# File to store posted posts for duplication check
POST_HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "posted_parenting.json")

# Reddit RSS feeds for parenting humor
RSS_FEEDS = [
    "https://www.reddit.com/r/ParentingHumor/.rss",
    "https://www.reddit.com/r/funny/.rss",
    "https://www.reddit.com/r/MomForAMinute/.rss",
]

def load_posted_posts():
    try:
        if os.path.exists(POST_HISTORY_FILE):
            with open(POST_HISTORY_FILE, "r") as f:
                content = f.read().strip()
                return json.loads(content) if content else []
        return []
    except Exception:
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

def fetch_reddit_posts():
    all_posts = []
    headers = {"User-Agent": "FunnyParentBot/1.0"}
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                title = entry.title
                # Exclude posts with first-person references
                if any(word in title.lower() for word in ["i ", "my ", "me "]):
                    continue
                all_posts.append(title)
        except Exception as e:
            print(f"Error fetching {feed_url}: {e}")
    random.shuffle(all_posts)
    return all_posts

def get_pixabay_image():
    api_key = os.environ.get("PIXABAY_KEY")
    if not api_key:
        print("PIXABAY_KEY not set")
        return None

    categories = ["funny", "parenting", "kids", "home", "office"]
    category = random.choice(categories)
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
        if response.status_code == 200:
            data = response.json()
            if data['hits']:
                image_url = random.choice(data['hits'])["largeImageURL"]
                img_response = requests.get(image_url, timeout=15)
                return BytesIO(img_response.content)
    except Exception as e:
        print(f"Error fetching Pixabay image: {e}")
    return None

def create_image(post_text):
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
    return output.getvalue()

def create_caption(post_text):
    captions = [
        "😂 Parenting never comes with a manual.",
        "🤣 Because raising kids is basically stand-up comedy.",
        "👶 When tiny humans take over the house.",
        "💡 Share if you’ve survived the toddler negotiations!"
    ]
    caption = f"{post_text}\n\n{random.choice(captions)}"
    return caption

def post_to_facebook(image_data, caption):
    page_id = os.environ.get("FB_PAGE_ID")
    token = os.environ.get("FB_PAGE_TOKEN")
    if not page_id or not token:
        print("Facebook credentials not set")
        return False

    url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
    files = {'source': ('parenting.jpg', image_data, 'image/jpeg')}
    data = {'message': caption, 'access_token': token}

    try:
        response = requests.post(url, files=files, data=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            save_post(caption)
            print(f"Posted successfully: {result.get('id')}")
            return True
        else:
            print(f"Facebook API error: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"Error posting to Facebook: {e}")
        return False

def main():
    print("Fetching Reddit posts...")
    posts = fetch_reddit_posts()
    if not posts:
        print("No valid posts found.")
        return

    for post_text in posts:
        if not is_duplicate(post_text):
            image = create_image(post_text)
            caption = create_caption(post_text)
            post_to_facebook(image, caption)
            break
    else:
        print("All posts are duplicates.")

if __name__ == "__main__":
    main()