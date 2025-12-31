#!/usr/bin/env python3
"""
Parent Humor Bot: Fetch funny parenting posts from Reddit RSS feeds,
generate humorous captions using Gemini AI, create images, and post to Facebook.
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
import feedparser
import time

# -------------------------------
# Environment / API Keys
# -------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PIXABAY_KEY = os.environ.get("PIXABAY_KEY")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_TOKEN = os.environ.get("FB_PAGE_TOKEN")

# -------------------------------
# Reddit RSS feeds (funny parenting)
# -------------------------------
PARENTING_RSS_FEEDS = [
    "https://www.reddit.com/r/ParentingHumor/.rss",
    "https://www.reddit.com/r/funnyparents/.rss",
    "https://www.reddit.com/r/Mommit/.rss"
]

# -------------------------------
# History file to avoid duplicates
# -------------------------------
POST_HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "posted_parenting.json")

def load_posted_posts():
    if os.path.exists(POST_HISTORY_FILE):
        with open(POST_HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_posted_post(post_hash):
    posted = load_posted_posts()
    posted.append(post_hash)
    with open(POST_HISTORY_FILE, "w") as f:
        json.dump(posted, f)

def is_duplicate_post(post_text):
    post_hash = hashlib.md5(post_text.encode()).hexdigest()
    return post_hash in load_posted_posts(), post_hash

# -------------------------------
# Fetch Reddit posts
# -------------------------------
def fetch_reddit_posts():
    all_posts = []
    for feed_url in PARENTING_RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:  # Limit to first 5 entries per feed
                all_posts.append({
                    "title": entry.title,
                    "link": entry.link
                })
            time.sleep(0.5)
        except Exception as e:
            print(f"Error fetching {feed_url}: {e}")
    random.shuffle(all_posts)
    return all_posts

# -------------------------------
# Generate funny caption using Gemini AI
# -------------------------------
def generate_funny_caption(text_prompt):
    try:
        payload = {
            "contents": [{"parts": [{"text": f"Create a funny parenting social media post based on this: {text_prompt}"}]}]
        }
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent",
            params={"key": GEMINI_API_KEY},
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            content = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            return content
    except Exception as e:
        print(f"Gemini AI error: {e}")
    # Fallback
    return text_prompt + " 😂 #ParentingHumor"

# -------------------------------
# Get Pixabay image
# -------------------------------
def get_pixabay_image():
    categories = ["funny", "kids", "family", "parenting", "home"]
    category = random.choice(categories)
    url = "https://pixabay.com/api/"
    params = {
        "key": PIXABAY_KEY,
        "q": category,
        "image_type": "photo",
        "orientation": "horizontal",
        "per_page": 20,
        "safesearch": "true"
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        if data['hits']:
            img_url = random.choice(data['hits'])["largeImageURL"]
            img_response = requests.get(img_url, timeout=15)
            return BytesIO(img_response.content)
    except Exception as e:
        print(f"Pixabay error: {e}")
    return None

# -------------------------------
# Create image with text overlay
# -------------------------------
def create_funny_image(post_text):
    width, height = 1200, 1200
    image_bytes = get_pixabay_image()
    if image_bytes:
        img = Image.open(image_bytes).resize((width, height), Image.LANCZOS)
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(0.7)
    else:
        img = Image.new("RGB", (width, height), color=random.choice(["#FFD700","#FF7F50","#87CEEB","#FFB6C1"]))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 62)
    except:
        font = ImageFont.load_default()
    wrapped_text = textwrap.fill(post_text, width=25)
    bbox = draw.textbbox((0,0), wrapped_text, font=font)
    x = (width - (bbox[2]-bbox[0])) // 2
    y = (height - (bbox[3]-bbox[1])) // 2
    draw.rectangle([x-20, y-20, x+(bbox[2]-bbox[0])+20, y+(bbox[3]-bbox[1])+20], fill=(0,0,0,150))
    draw.text((x, y), wrapped_text, fill=(255,255,255), font=font)
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=95)
    return buffer.getvalue()

# -------------------------------
# Post to Facebook
# -------------------------------
def post_to_facebook(image_data, caption):
    try:
        url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
        files = {"source": ("parenting.jpg", image_data, "image/jpeg")}
        data = {"message": caption, "access_token": FB_PAGE_TOKEN}
        response = requests.post(url, files=files, data=data, timeout=30)
        if response.status_code == 200:
            print("✅ Posted to Facebook!")
            return True
        else:
            print(f"Facebook error: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Facebook post error: {e}")
    return False

# -------------------------------
# Main process
# -------------------------------
def main():
    print("🚀 Starting Funny Parenting Post Bot")
    reddit_posts = fetch_reddit_posts()
    if not reddit_posts:
        print("No Reddit posts found. Exiting.")
        return
    for post in reddit_posts:
        caption = generate_funny_caption(post["title"])
        duplicate, post_hash = is_duplicate_post(caption)
        if duplicate:
            print("Duplicate detected. Skipping...")
            continue
        img = create_funny_image(caption)
        success = post_to_facebook(img, caption)
        if success:
            save_posted_post(post_hash)
            break  # Post only one per run
        time.sleep(2)

if __name__ == "__main__":
    main()