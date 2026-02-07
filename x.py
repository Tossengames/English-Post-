#!/usr/bin/env python3

import os
import requests
import json
import random
import time

USED_IMAGES_FILE = "posted_animals.json"

# Your keywords list
KEYWORDS = [
    "Moose", "Elephant", "Mountain Lion", "Hippopotamus", "Grizzly Bear",
    "Cape Buffalo", "Rattlesnake", "African Lion", "Alligator", "Wild Boar",
    "Tiger", "Komodo Dragon", "Polar Bear", "Kangaroo", "Gorilla",
    "Crocodile", "Wolf", "Black Bear", "Rhinoceros", "Panda",
    "Jaguar", "Snow Leopard", "Bison", "Scorpion", "Leopard",
    "Tarantula", "Orangutan", "Koala", "Cheetah", "Bald Eagle",
    "Poison Dart Frog", "Anaconda", "Cassowary", "Wolverine", "Hyena",
    "Camel", "Arctic Fox", "Baboon", "Stingray", "Box Jellyfish",
    "Piranha", "Giant Anteater", "Sloth Bear", "Tasmanian Devil", "Platypus",
    "Armadillo", "Skunk", "Raccoon", "Ostrich", "Emu",
    "Llama", "Alpaca", "Wild Horse", "Wild Donkey", "Feral Hog",
    "Coyote", "Bobcat", "Lynx", "Red Fox", "Badger",
    "Hedgehog", "Monitor Lizard"
]

# -------------------------------
# Storage
# -------------------------------
def load_used_images():
    if os.path.exists(USED_IMAGES_FILE):
        with open(USED_IMAGES_FILE, "r") as f:
            return json.load(f)
    return []

def save_used_images(ids):
    used = load_used_images()
    used.extend(ids)
    with open(USED_IMAGES_FILE, "w") as f:
        json.dump(list(set(used)), f)

# -------------------------------
# Pixabay - Download Images
# -------------------------------
def get_images_for_all_keywords():
    api_key = os.environ["PIXABAY_KEY"]
    used = load_used_images()
    
    all_images = []
    all_ids = []
    successful_keywords = []
    
    print(f"📥 Starting download for {len(KEYWORDS)} keywords...")
    
    for keyword in KEYWORDS:
        try:
            print(f"  Downloading: {keyword}")
            
            url = "https://pixabay.com/api/"
            params = {
                "key": api_key,
                "q": keyword,
                "image_type": "photo",
                "per_page": 10,
                "safesearch": "true"
            }
            
            r = requests.get(url, params=params, timeout=15)
            hits = r.json()["hits"]
            
            if not hits:
                print(f"    ⚠️ No images found for: {keyword}")
                continue
            
            # Filter out used images
            available = [img for img in hits if img["id"] not in used]
            
            if not available:
                print(f"    ⚠️ All images used for: {keyword}, using any")
                available = hits
            
            # Pick random image
            img = random.choice(available)
            
            # Download image
            img_data = requests.get(img["largeImageURL"]).content
            
            all_images.append(img_data)
            all_ids.append(img["id"])
            successful_keywords.append(keyword)
            
            print(f"    ✅ Downloaded: {keyword}")
            time.sleep(1)  # Small delay to be nice to API
            
        except Exception as e:
            print(f"    ❌ Error with {keyword}: {e}")
            continue
    
    return all_images, all_ids, successful_keywords

# -------------------------------
# Facebook - Post Images
# -------------------------------
def post_all_images(images, keywords):
    page_id = os.environ["FB_PAGE_ID"]
    token = os.environ["FB_PAGE_TOKEN"]
    
    print(f"\n📤 Starting upload of {len(images)} images...")
    
    media_ids = []
    
    # First upload all images as unpublished
    for i, (image, keyword) in enumerate(zip(images, keywords)):
        try:
            print(f"  Uploading {i+1}/{len(images)}: {keyword}")
            
            url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
            files = {"source": (f"{keyword.replace(' ', '_')}.jpg", image, "image/jpeg")}
            data = {
                "published": "false",
                "access_token": token
            }
            
            response = requests.post(url, files=files, data=data)
            media_id = response.json()["id"]
            media_ids.append({"media_fbid": media_id})
            
            print(f"    ✅ Uploaded")
            time.sleep(2)  # Facebook API likes a little delay
            
        except Exception as e:
            print(f"    ❌ Failed: {e}")
            continue
    
    if not media_ids:
        print("❌ No images uploaded successfully")
        return
    
    # Now post them all as a carousel
    print(f"\n🎯 Creating post with {len(media_ids)} images...")
    
    # Create hashtags from keywords
    keyword_hashtags = " ".join([f"#{kw.replace(' ', '')}" for kw in keywords[:10]])
    message = f"{keyword_hashtags}\n\n#Wildlife #Animals #Nature #AnimalFacts"
    
    url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
    data = {
        "message": message,
        "attached_media": json.dumps(media_ids),
        "access_token": token
    }
    
    response = requests.post(url, data=data)
    
    if response.status_code == 200:
        print(f"✅ Successfully posted {len(media_ids)} images!")
    else:
        print(f"❌ Post failed: {response.text}")

# -------------------------------
# Main Function
# -------------------------------
def main():
    print("🚀 Starting animal image download and post")
    print(f"🔑 Keywords: {len(KEYWORDS)} total\n")
    
    # 1. Download all images
    images, ids, keywords = get_images_for_all_keywords()
    
    if not images:
        print("❌ No images downloaded. Exiting.")
        return
    
    print(f"\n📊 Downloaded {len(images)}/{len(KEYWORDS)} images successfully")
    
    # 2. Post all images at once
    post_all_images(images, keywords)
    
    # 3. Save used image IDs
    save_used_images(ids)
    
    print(f"\n✅ Done! Processed {len(images)} images")

if __name__ == "__main__":
    main()