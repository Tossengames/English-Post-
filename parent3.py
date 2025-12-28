import os
import google.generativeai as genai
import random
import tempfile
import subprocess
import requests
import textwrap
import json
import re
import asyncio
from datetime import datetime
import hashlib

# Try to import Edge TTS, fallback to gTTS
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    from gtts import gTTS
    import time

class PostHistory:
    def __init__(self, history_file="mom_issues_history.json"):
        self.history_file = history_file
        self.history = self.load_history()
    
    def load_history(self):
        """Load post history from JSON file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_history(self):
        """Save post history to JSON file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except:
            pass
    
    def add_post(self, script, video_path=None):
        """Add a post to history"""
        post_id = hashlib.md5(script.encode()).hexdigest()
        self.history[post_id] = {
            'script': script,
            'date': datetime.now().isoformat(),
            'video_path': video_path,
        }
        self.save_history()
    
    def is_duplicate_content(self, script):
        """Check if exact content has been used before"""
        post_id = hashlib.md5(script.encode()).hexdigest()
        return post_id in self.history

def generate_mom_script(post_history):
    """Generate a natural, engaging parenting script using Gemini"""
    
    mom_issues = [
        "bedtime battles", "picky eating", "tantrums in public", 
        "sibling rivalry", "homework struggles", "screen time",
        "morning chaos", "backtalk", "mealtime messes",
        "constant messes", "mom guilt", "balancing work and family"
    ]
    
    for attempt in range(5):
        issue = random.choice(mom_issues)
        
        # NATURAL, CONVERSATIONAL PROMPT - NO TEMPLATES
        prompt = f"""Write a 15-20 second natural, conversational script for a mom Instagram Reel about {issue}.
        
        Requirements:
        - Sound like a real mom talking to a friend
        - Start with a relatable question or statement
        - Share ONE simple, actionable tip naturally
        - End with encouragement
        - Keep it under 50 words
        - DO NOT use phrases like "Problem:" or "Solution:" 
        - Write as ONE flowing paragraph
        
        Example: "Is bedtime taking forever at your house too? I found that doing a '3 things' rule really helps - one hug, one story, one song. Then lights out. It's made our evenings so much more peaceful!"
        
        Write ONLY the script text."""
        
        try:
            genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            
            script = response.text.strip()
            
            # Check if this content has been used before
            if script and not post_history.is_duplicate_content(script):
                return script
            else:
                print(f"Duplicate content detected. Trying again...")
        except Exception as e:
            print(f"Gemini API error: {e}")
            continue
    
    # Fallback scripts if AI fails
    fallback_scripts = [
        "Morning routines feeling impossible? I was always yelling 'hurry up!'. Now we do a 5-minute 'ready check' where they show me shoes, coat, and backpack. Turns it into a game instead of a battle.",
        "Tired of the toy explosion? My living room was a disaster zone. Now we do a '10-item pickup' to a fun song before bath time. They think it's a race, and my house isn't a total wreck anymore.",
        "Does your kid only eat like 3 foods? Mine too! I found that putting a tiny 'no pressure' portion of something new on their plate every day really helps. Just seeing it regularly makes a difference."
    ]
    
    for script in fallback_scripts:
        if not post_history.is_duplicate_content(script):
            return script
    
    return None

def get_background_image(script):
    """Get background image - try Pixabay first, then AI"""
    temp_dir = tempfile.mkdtemp()
    image_path = os.path.join(temp_dir, "background.jpg")
    
    # Create a search prompt for Pixabay based on script content
    script_lower = script.lower()
    
    if "bedtime" in script_lower or "sleep" in script_lower:
        pixabay_prompt = "bedtime story mother child"
    elif "eat" in script_lower or "food" in script_lower:
        pixabay_prompt = "family dinner children eating"
    elif "morning" in script_lower or "routine" in script_lower:
        pixabay_prompt = "morning family getting ready"
    elif "toy" in script_lower or "mess" in script_lower:
        pixabay_prompt = "children playing toys"
    elif "sibling" in script_lower or "squabbl" in script_lower:
        pixabay_prompt = "siblings playing together"
    else:
        pixabay_prompt = "mother child happy family"
    
    print(f"Trying Pixabay for: {pixabay_prompt}")
    
    # Try Pixabay first
    if "PIXABAY_KEY" in os.environ:
        try:
            response = requests.get(
                "https://pixabay.com/api/",
                params={
                    "key": os.environ["PIXABAY_KEY"],
                    "q": pixabay_prompt,
                    "image_type": "photo",
                    "orientation": "vertical",
                    "per_page": 30,
                    "safesearch": "true",
                    "category": "people"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                images = response.json().get('hits', [])
                if images:
                    image_url = random.choice(images)['largeImageURL']
                    img_response = requests.get(image_url, timeout=30)
                    if img_response.status_code == 200:
                        with open(image_path, 'wb') as f:
                            f.write(img_response.content)
                        print("✅ Pixabay image found")
                        return image_path
        except Exception as e:
            print(f"Pixabay API error: {e}")
    
    # If Pixabay fails, try AI image generation
    ai_prompt = f"mother with child, happy, loving, {pixabay_prompt}, realistic photo, vertical, 4k"
    
    print(f"Trying AI image generation: {ai_prompt}")
    
    try:
        clean_prompt = ai_prompt.replace(" ", "%20").replace(",", "%2C")
        api_url = f"https://image.pollinations.ai/prompt/{clean_prompt}"
        
        response = requests.get(api_url, timeout=30)
        if response.status_code == 200:
            with open(image_path, 'wb') as f:
                f.write(response.content)
            print("✅ AI image generated successfully")
            return image_path
    except Exception as e:
        print(f"Pollinations.ai error: {e}")
    
    print("❌ Could not get image from Pixabay or AI")
    return None

async def edge_tts_generate(text, path, voice):
    """Generate speech using Edge TTS with specified voice"""
    try:
        tts = edge_tts.Communicate(text, voice)
        await tts.save(path)
        return True
    except Exception as e:
        print(f"Edge TTS failed: {e}")
        return False

def gtts_generate(text, path):
    """Generate speech using gTTS (fallback)"""
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(path)
        time.sleep(1)  # Ensure file is written
        return True
    except Exception as e:
        print(f"gTTS failed: {e}")
        return False

def create_voiceover(script, output_path):
    """Create voiceover with natural delivery"""
    temp_dir = tempfile.mkdtemp()
    
    # Use empathetic female voice
    voice = "en-US-AriaNeural"
    
    # Use the script directly - it's already conversational
    spoken_text = script
    
    print("Creating natural voiceover...")
    
    # Try Edge TTS first if available
    if EDGE_TTS_AVAILABLE:
        print("Trying Edge TTS...")
        try:
            success = asyncio.run(edge_tts_generate(spoken_text, output_path, voice))
            if success:
                print("✅ Voiceover created with Edge TTS")
                return True
        except Exception as e:
            print(f"Edge TTS async error: {e}")
    
    # Fallback to gTTS
    print("Falling back to gTTS...")
    if gtts_generate(spoken_text, output_path):
        print("✅ Voiceover created with gTTS")
        return True
    
    print("❌ All TTS methods failed")
    return False

def get_audio_duration(audio_path):
    """Get the duration of an audio file in seconds"""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', audio_path
        ], capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except:
        return 15  # Fallback duration

def create_vertical_video(script, output_path):
    """Create vertical video with ONLY CTA at bottom"""
    temp_dir = tempfile.mkdtemp()
    voice_path = os.path.join(temp_dir, "voiceover.mp3")
    
    if not create_voiceover(script, voice_path):
        print("❌ Failed to create voiceover")
        return False

    # Get actual duration from the voiceover file
    duration = get_audio_duration(voice_path)
    print(f"Video duration: {duration:.2f} seconds")
    
    bg_image = get_background_image(script)
    
    if bg_image is None:
        print("❌ Skipping video creation due to no background image")
        return False
    
    # Vertical format for Shorts/Reels (9:16 aspect ratio)
    width, height = 1080, 1920

    if not os.path.exists(bg_image):
        print("❌ Background image file not found")
        return False

    # SIMPLE FFMPEG - ONLY CTA AT BOTTOM, NO OTHER TEXT
    # Use gold (#FFD700) and black (#000000) theme
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-loop', '1', '-i', bg_image,
        '-i', voice_path,
        '-vf', f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},"
               f"drawtext=text='Follow for more mom tips':fontcolor=#FFD700:fontsize=50:"
               f"box=1:boxcolor=#000000@0.7:boxborderw=4:x=(w-text_w)/2:y={height-150}",
        '-c:v', 'libx264', '-c:a', 'aac',
        '-t', str(duration),
        '-shortest',
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        output_path
    ]
    
    try:
        subprocess.run(ffmpeg_cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e}")
        return False

def generate_hashtags(script):
    """Generate relevant mom/parenting hashtags"""
    base_hashtags = [
        "#MomTips", "#ParentingHacks", "#Motherhood", 
        "#RaisingKids", "#FamilyLife", "#MomLife",
        "#ParentingAdvice", "#MomWisdom", "#RealParenting"
    ]
    
    script_lower = script.lower()
    
    if "bedtime" in script_lower or "sleep" in script_lower:
        base_hashtags.extend(["#BedtimeRoutine", "#SleepHelp"])
    elif "eat" in script_lower or "food" in script_lower:
        base_hashtags.extend(["#PickyEater", "#MealtimeTips"])
    elif "morning" in script_lower:
        base_hashtags.extend(["#MorningRoutine", "#GetReady"])
    elif "toy" in script_lower or "mess" in script_lower:
        base_hashtags.extend(["#CleanUp", "#Organization"])
    
    return " ".join(base_hashtags[:12])

def post_to_facebook(video_path, script):
    try:
        hashtags = generate_hashtags(script)
        
        with open(video_path, 'rb') as video_file:
            response = requests.post(
                f"https://graph.facebook.com/v19.0/{os.environ['FB_PAGE_ID']}/videos",
                params={
                    "access_token": os.environ["FB_PAGE_TOKEN"],
                    "description": f"{script}\n\n{hashtags}\n\n👇 Follow for more real mom advice!"
                },
                files={"source": video_file},
                timeout=60
            )
        if response.status_code == 200:
            print("✅ Video posted successfully to Facebook!")
            return True
        else:
            print(f"❌ Facebook error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

def main():
    print("=== Mom Advice Reel Creator ===")
    print("Creating natural, conversational parenting reels...")
    
    # Initialize post history
    post_history = PostHistory()
    
    # Cleanup old posts (keep last 30 days)
    cutoff_date = datetime.now().timestamp() - (30 * 24 * 60 * 60)
    new_history = {}
    for post_id, post_data in post_history.history.items():
        post_date = datetime.fromisoformat(post_data['date']).timestamp()
        if post_date > cutoff_date:
            new_history[post_id] = post_data
    post_history.history = new_history
    post_history.save_history()
    
    # Generate natural mom script
    script = generate_mom_script(post_history)
    
    if script is None:
        print("❌ Could not generate a unique script after multiple attempts")
        return
    
    print(f"\n🎙️ SCRIPT:")
    print(f"{script}")

    video_path = "mom_advice_reel.mp4"
    if create_vertical_video(script, video_path):
        print(f"✅ Video created: {video_path}")
        
        # Add to post history
        post_history.add_post(script, video_path)
        
        if all(key in os.environ for key in ["FB_PAGE_ID", "FB_PAGE_TOKEN"]):
            print("📤 Posting to Facebook...")
            if post_to_facebook(video_path, script):
                print("✅ Post completed successfully!")
            else:
                print("❌ Failed to post to Facebook")
        else:
            print("ℹ️ Facebook credentials not found - video saved locally")

        # Save description with hashtags
        hashtags = generate_hashtags(script)
        with open("video_description.txt", "w") as f:
            f.write(f"{script}\n\n")
            f.write(f"{hashtags}\n\n")
            f.write("👇 Follow for more real mom advice!")
    else:
        print("❌ Failed to create video - skipping")

if __name__ == "__main__":
    main()