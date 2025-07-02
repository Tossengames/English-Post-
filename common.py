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
        response = requests.post(url, headers=headers, data=json.dumps(data))
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print("❌ AI generation error:", e)
        return None

def post_to_facebook(message, image_path=None):
    url = f"https://graph.facebook.com/{FB_PAGE_ID}/photos" if image_path else f"https://graph.facebook.com/{FB_PAGE_ID}/feed"
    data = {
        "access_token": FB_PAGE_TOKEN,
        "message": message
    }

    if image_path:
        files = {"source": open(image_path, "rb")}
    else:
        files = None

    try:
        response = requests.post(url, data=data, files=files)
        print("✅ Post published successfully.")
    except Exception as e:
        print("❌ Facebook post error:", e)
