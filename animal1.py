#!/usr/bin/env python3

import os
import requests
import json
import random
from io import BytesIO
import time

USED_IMAGES_FILE = "posted_animals.json"

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
# Pixabay
# -------------------------------
def get_animal_images(count):
    api_key = os.environ["PIXABAY_KEY"]
    used = load_used_images()

    url = "https://pixabay.com/api/"
    params = {
        "key": api_key,
        "q": "animals",
        "image_type": "photo",
        "per_page": 100,
        "safesearch": "true"
    }

    r = requests.get(url, params=params, timeout=15)
    hits = r.json()["hits"]
    random.shuffle(hits)

    images = []
    ids = []

    for img in hits:
        if img["id"] not in used:
            img_data = requests.get(img["largeImageURL"]).content
            images.append(img_data)
            ids.append(img["id"])
            if len(images) == count:
                break

    if len(images) < count:
        raise Exception("Not enough new images")

    return images, ids

# -------------------------------
# Facebook
# -------------------------------
def upload_unpublished(image):
    page_id = os.environ["FB_PAGE_ID"]
    token = os.environ["FB_PAGE_TOKEN"]

    url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
    files = {"source": ("animal.jpg", image, "image/jpeg")}
    data = {
        "published": "false",
        "access_token": token
    }

    r = requests.post(url, files=files, data=data)
    return r.json()["id"]

def post_single(image):
    page_id = os.environ["FB_PAGE_ID"]
    token = os.environ["FB_PAGE_TOKEN"]

    hashtags = "#Animals #Wildlife #Nature #AnimalLovers 🐾"

    url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
    files = {"source": ("animal.jpg", image, "image/jpeg")}
    data = {
        "message": hashtags,
        "access_token": token
    }

    requests.post(url, files=files, data=data)

def post_carousel(images):
    page_id = os.environ["FB_PAGE_ID"]
    token = os.environ["FB_PAGE_TOKEN"]

    media_ids = []
    for img in images:
        media_id = upload_unpublished(img)
        media_ids.append({"media_fbid": media_id})
        time.sleep(1)  # safer

    url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
    data = {
        "message": "#Animals #Wildlife #Nature #AnimalLovers 🐾",
        "attached_media": json.dumps(media_ids),
        "access_token": token
    }

    requests.post(url, data=data)

# -------------------------------
# Main
# -------------------------------
def main():
    print("🐾 Animal Auto Poster Started")

    is_carousel = random.choice([True, False])

    if is_carousel:
        count = random.randint(3, 6)
        print(f"📸 Posting carousel ({count} images)")
        images, ids = get_animal_images(count)
        post_carousel(images)
        save_used_images(ids)
    else:
        print("🖼️ Posting single image")
        images, ids = get_animal_images(1)
        post_single(images[0])
        save_used_images(ids)

    print("✅ Done")

if __name__ == "__main__":
    main()