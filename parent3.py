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
    
    def add_post(self, voiceover_script, video_path=None):
        """Add a post to history"""
        post_id = hashlib.md5(voiceover_script.encode()).hexdigest()
        self.history[post_id] = {
            'script': voiceover_script,
            'date': datetime.now().isoformat(),
            'video_path': video_path,
        }
        self.save_history()
    
    def is_duplicate_content(self, voiceover_script):
        """Check if exact content has been used before"""
        post_id = hashlib.md5(voiceover_script.encode()).hexdigest()
        return post_id in self.history

def generate_voiceover_script(post_history):
    """Generate a natural, engaging voiceover script using Gemini"""
    
    # Common issues moms/parents face
    mom_issues = [
        "bedtime battles", "picky eating", "tantrums in public", 
        "sibling rivalry", "homework struggles", "screen time",
        "morning chaos", "backtalk", "mealtime messes",
        "constant messes", "mom guilt", "balancing work and family",
        "bedtime stalling", "messy rooms", "endless questions",
        "fussy eating", "homework meltdowns", "chore resistance"
    ]
    
    # Try AI generation first
    for attempt in range(5):  # Try 5 times to get a unique topic
        issue = random.choice(mom_issues)
        
        # CRITICAL: New prompt for natural, engaging content
        prompt = f"""Write a 15-20 second, natural-sounding voiceover script for a parenting Instagram Reel about {issue}.

        **Requirements:**
        - Sound like a real mom talking to a friend, not a robot
        - Start with a strong, relatable hook/question
        - Describe the struggle naturally within the flow
        - Share ONE simple, actionable tip or mindset shift
        - End with encouragement
        - Maximum 50 words, very concise
        - DO NOT use labels like "Problem:" or "Solution:"
        - Write in a single, flowing paragraph

        **Example Style:**
        "Ugh, is bedtime taking forever at your house too? I used to get so stressed when my kids kept coming out of their rooms. Now I use a '3 things' rule: one hug, one drink, one story. Then lights out. It's been a game-changer!"

        Write ONLY the script text, nothing else."""
        
        try:
            genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            
            voiceover_script = response.text.strip()
            
            # Check for duplicates
            if not post_history.is_duplicate_content(voiceover_script):
                return voiceover_script
            else:
                print(f"Duplicate content detected. Trying again...")
        except Exception as e:
            print(f"Gemini API error: {e}")
            continue
    
    # Fallback scripts
    fallback_scripts = [
        "Is your kid suddenly a picky eater? Mine went from eating everything to just plain pasta. The trick? Serve a 'safe food' they like, plus one new thing, with zero pressure. It takes the mealtime power struggle off the table.",
        "Morning routines feeling impossible? I was always yelling 'hurry up!'. Now we do a 5-minute 'ready check' where they show me shoes, coat, and backpack. Turns it into a game and saves my sanity.",
        "Tired of the toy explosion? My living room was a disaster zone. Now we do a '10-item pickup' to a fun song before bath time. They think it's a race, and my house isn't a total wreck anymore."
    ]
    
    for script in fallback_scripts:
        if not post_history.is_duplicate_content(script):
            return script
    
    return None

def get_background_image(script):
    """Get background image - try Pixabay first, then AI"""
    temp_dir = tempfile.mkdtemp()
    image_path = os.path.join(temp_dir, "background.jpg")
    
    # Extract keywords for image search
    keywords = ["mother", "parenting", "family", "kids"]
    for word in ["bedtime", "sleep"]:
        if word in script.lower():
            keywords = ["bedtime", "mother child", "sleeping child"]
            break
    for word in ["eat", "food", "meal"]:
        if word in script.lower():
            keywords = ["family dinner", "child eating", "healthy food"]
            break
    for word in ["toy", "mess", "clean"]:
        if word in script.lower():
            keywords = ["playroom", "toys", "cleaning"]
            break
    
    pixabay_prompt = random.choice(keywords)
    
    print(f"Trying Pixabay for: {pixabay_prompt}")
    
    # Try Pixabay first
    if get_pixabay_image(pixabay_prompt, image_path):
        print("✅ Pixabay image found")
        return image_path
    
    # If Pixabay fails, try AI image generation
    ai_prompt = f"mother with child, happy, loving, {pixabay_prompt}, realistic photo, vertical, 4k, warm lighting"
    
    print(f"Trying AI image generation: {ai_prompt}")
    
    if get_ai_generated_image(ai_prompt, image_path):
        print("✅ AI image generated successfully")
        return image_path
    
    # If both fail
    print("❌ Could not get image")
    return None

def get_pixabay_image(prompt, output_path):
    """Get image from Pixabay API"""
    if "PIXABAY_KEY" not in os.environ:
        return False
    
    try:
        response = requests.get(
            "https://pixabay.com/api/",
            params={
                "key": os.environ["PIXABAY_KEY"],
                "q": prompt,
                "image_type": "photo",
                "orientation": "vertical",
                "per_page": 20,
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
                    with open(output_path, 'wb') as f:
                        f.write(img_response.content)
                    return True
    except Exception as e:
        print(f"Pixabay API error: {e}")
    
    return False

def get_ai_generated_image(prompt, output_path):
    """Generate AI image using Pollinations.ai"""
    try:
        clean_prompt = prompt.replace(" ", "%20").replace(",", "%2C")
        api_url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1080&height=1920"
        
        response = requests.get(api_url, timeout=30)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"Pollinations.ai error: {e}")
    
    return False

async def edge_tts_generate(text, path, voice):
    """Generate speech using Edge TTS"""
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
        time.sleep(1)
        return True
    except Exception as e:
        print(f"gTTS failed: {e}")
        return False

def create_voiceover(script):
    """Create voiceover with natural delivery"""
    temp_dir = tempfile.mkdtemp()
    
    # Use empathetic female voice
    voice = "en-US-AriaNeural"
    output_path = os.path.join(temp_dir, "voiceover.mp3")
    
    print("Creating voiceover...")
    
    # Try Edge TTS first if available
    if EDGE_TTS_AVAILABLE:
        print("Trying Edge TTS...")
        try:
            success = asyncio.run(edge_tts_generate(script, output_path, voice))
            if success:
                print("✅ Voiceover created with Edge TTS")
                return output_path
        except Exception as e:
            print(f"Edge TTS async error: {e}")
    
    # Fallback to gTTS
    print("Falling back to gTTS...")
    if gtts_generate(script, output_path):
        print("✅ Voiceover created with gTTS")
        return output_path
    
    print("❌ All TTS methods failed")
    return None

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
    """Create vertical video with text overlay - FIXED VERSION"""
    temp_dir = tempfile.mkdtemp()
    voice_path = os.path.join(temp_dir, "voiceover.mp3")
    
    if not create_voiceover(script):
        print("❌ Failed to create voiceover")
        return False

    # Get actual duration
    duration = get_audio_duration(voice_path)
    print(f"Video duration: {duration:.2f} seconds")
    
    bg_image = get_background_image(script)
    
    if bg_image is None:
        print("❌ Skipping video creation due to no background image")
        return False
    
    # Vertical format
    width, height = 1080, 1920
    
    # Prepare text for display (split into lines)
    lines = textwrap.wrap(script, width=40)
    if len(lines) > 4:  # Limit display lines
        lines = lines[:4]
    
    # Create text overlay command
    drawtext_filters = []
    y_start = 300
    line_height = 100
    
    for i, line in enumerate(lines):
        # Escape single quotes for shell
        line_escaped = line.replace("'", "'\\''")
        y_pos = y_start + (i * line_height)
        drawtext_filters.append(f"drawtext=text='{line_escaped}':fontcolor=#FFD700:fontsize=60:fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:box=1:boxcolor=#000000@0.6:boxborderw=5:x=(w-text_w)/2:y={y_pos}")
    
    # Join all filters
    filter_chain = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},"
    filter_chain += ','.join(drawtext_filters)
    
    # SIMPLE, RELIABLE FFMPEG COMMAND - This is the fix for no sound/text
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-loop', '1',
        '-i', bg_image,
        '-i', voice_path,
        '-filter_complex', filter_chain,
        '-map', '0:v',
        '-map', '1:a',
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-t', str(duration),
        '-shortest',
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        output_path
    ]
    
    print("Running FFmpeg command...")
    try:
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"FFmpeg stderr: {result.stderr}")
            print(f"FFmpeg stdout: {result.stdout}")
            
            # Try even simpler approach
            print("Trying alternative simple approach...")
            return create_simple_video_fallback(bg_image, voice_path, duration, script, output_path)
        
        # Verify the output file has audio
        if os.path.exists(output_path):
            # Check if video has audio stream
            check_cmd = ['ffprobe', '-i', output_path, '-show_streams', '-select_streams', 'a', '-loglevel', 'error']
            check_result = subprocess.run(check_cmd, capture_output=True, text=True)
            if check_result.returncode != 0:
                print("⚠️ Warning: Output video may not have audio track")
            else:
                print("✅ Video has audio track")
        
        return True
    except Exception as e:
        print(f"FFmpeg error: {e}")
        return False

def create_simple_video_fallback(bg_image, voice_path, duration, script, output_path):
    """Fallback video creation without complex filters"""
    try:
        temp_dir = tempfile.mkdtemp()
        
        # First create a textless video
        temp_video = os.path.join(temp_dir, "temp.mp4")
        cmd1 = [
            'ffmpeg', '-y',
            '-loop', '1',
            '-i', bg_image,
            '-i', voice_path,
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-t', str(duration),
            '-shortest',
            '-pix_fmt', 'yuv420p',
            temp_video
        ]
        
        subprocess.run(cmd1, check=True, capture_output=True)
        
        # Add text as a separate, simpler step
        lines = textwrap.wrap(script, width=40)
        if len(lines) > 3:
            lines = lines[:3]
        
        drawtext_parts = []
        y_start = 400
        for i, line in enumerate(lines):
            line_escaped = line.replace("'", "'\\''")
            y_pos = y_start + (i * 120)
            drawtext_parts.append(f"drawtext=text='{line_escaped}':fontcolor=#FFD700:fontsize=70:box=1:boxcolor=#000000@0.7:x=(w-text_w)/2:y={y_pos}")
        
        filter_text = ','.join(drawtext_parts)
        
        cmd2 = [
            'ffmpeg', '-y',
            '-i', temp_video,
            '-vf', filter_text,
            '-c:v', 'libx264',
            '-c:a', 'copy',
            output_path
        ]
        
        subprocess.run(cmd2, check=True, capture_output=True)
        return True
        
    except Exception as e:
        print(f"Fallback video creation failed: {e}")
        return False

def generate_hashtags(script):
    """Generate relevant hashtags"""
    base_hashtags = [
        "#MomHacks", "#ParentingTips", "#Motherhood", 
        "#RaisingKids", "#FamilyLife", "#MomLife",
        "#ParentingAdvice", "#PracticalParenting", "#ParentingWin"
    ]
    
    script_lower = script.lower()
    
    if any(word in script_lower for word in ["bedtime", "sleep"]):
        base_hashtags.extend(["#BedtimeRoutine", "#SleepTraining"])
    elif any(word in script_lower for word in ["eat", "food", "meal"]):
        base_hashtags.extend(["#PickyEater", "#Mealtime"])
    elif any(word in script_lower for word in ["toy", "mess", "clean"]):
        base_hashtags.extend(["#CleanUp", "#HomeOrganization"])
    
    return " ".join(base_hashtags[:12])

def post_to_facebook(video_path, script):
    try:
        hashtags = generate_hashtags(script)
        
        with open(video_path, 'rb') as video_file:
            response = requests.post(
                f"https://graph.facebook.com/v19.0/{os.environ['FB_PAGE_ID']}/videos",
                params={
                    "access_token": os.environ["FB_PAGE_TOKEN"],
                    "description": f"{script}\n\n{hashtags}\n\n👇 Follow for more real mom tips!"
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
    print("=== Mom Wisdom Reel Creator ===")
    print("Creating natural, engaging parenting reels...")
    
    # Initialize post history
    post_history = PostHistory()
    
    # Generate natural voiceover script
    voiceover_script = generate_voiceover_script(post_history)
    
    if voiceover_script is None:
        print("❌ Could not generate a unique script")
        return
    
    print(f"\n🎙️ VOICEOVER SCRIPT:")
    print(f"\"{voiceover_script}\"")

    video_path = "mom_reel.mp4"
    if create_vertical_video(voiceover_script, video_path):
        print(f"✅ Video created: {video_path}")
        
        # Add to post history
        post_history.add_post(voiceover_script, video_path)
        
        if all(key in os.environ for key in ["FB_PAGE_ID", "FB_PAGE_TOKEN"]):
            print("📤 Posting to Facebook...")
            if post_to_facebook(video_path, voiceover_script):
                print("✅ Post completed successfully!")
            else:
                print("❌ Failed to post to Facebook")
        else:
            print("ℹ️ Facebook credentials not found - video saved locally")

        # Save description
        hashtags = generate_hashtags(voiceover_script)
        with open("video_description.txt", "w") as f:
            f.write(f"{voiceover_script}\n\n")
            f.write(f"{hashtags}\n\n")
            f.write("👇 Follow for more real mom tips!")
    else:
        print("❌ Failed to create video - skipping")

if __name__ == "__main__":
    main()