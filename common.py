# common.py
import os
import requests
import json
from datetime import datetime

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")

def ask_ai(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    try:
        res = requests.post(url, headers=headers, data=json.dumps(data))
        res.raise_for_status()
        result = res.json()
        return result["contents"][0]["parts"][0]["text"]
    except Exception as e:
        print(f"❌ AI generation error: {e}")
        return None

def post_to_facebook(message, image_url=None):
    url = f"https://graph.facebook.com/{FB_PAGE_ID}/photos" if image_url else f"https://graph.facebook.com/{FB_PAGE_ID}/feed"
    payload = {
        'message': message,
        'access_token': FB_PAGE_TOKEN,
    }

    if image_url:
        payload['url'] = image_url

    try:
        res = requests.post(url, data=payload)
        res.raise_for_status()
        print("✅ Post published successfully.")
    except Exception as e:
        print(f"❌ Facebook post error: {e}")
