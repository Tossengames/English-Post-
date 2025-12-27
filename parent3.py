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
    
    mom_issues = [
        "bedtime battles", "picky eating", "tantrums in public", 
        "sibling rivalry", "homework struggles", "screen time",
        "morning chaos", "backtalk", "mealtime messes",
        "constant messes", "mom guilt", "balancing work and family"
    ]
    
    for attempt in range(5):
        issue = random.choice(mom_issues)
        
        prompt = f"""Write a 15-second, natural-sounding voiceover for a parenting Instagram Reel about {issue}.

        Requirements:
        - Sound like a real mom talking to a friend
        - Start with a relatable question or statement
        - Share ONE simple, actionable tip
        - End with encouragement
        - 40-50 words maximum
        - NO labels like "Problem:" or "Solution:"
        - Write as ONE flowing paragraph

        Example: "Is bedtime a nightly battle at your house? I used to get so stressed. Now we do a 5-minute 'snuggle countdown' where we read one short book and give three hugs. It's made all the difference!"

        Write ONLY the script text."""
        
        try:
            genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            
            voiceover_script = response.text.strip()
            
            if voiceover_script and not post_history.is_duplicate_content(voiceover_script):
                return voiceover_script
        except Exception as e:
            print(f"Gemini API error: {e}")
            continue
    
    # Fallback scripts
    fallback_scripts = [
        "Morning routines feeling impossible? I was always yelling 'hurry up!'. Now we do a 5-minute 'ready check' where they show me shoes, coat, and backpack. Turns it into a game and saves my sanity.",
        "Tired of the toy explosion? My living room was a disaster zone. Now we do a '10-item pickup' to a fun song before bath time. They think it's a race, and my house isn't a total wreck anymore."
    ]
    
    for script in fallback_scripts:
        if not post_history.is_duplicate_content(script):
            return script
    
    return None

def get_background_image(script, temp_dir):
    """Get background image in the specified temp directory"""
    image_path = os.path.join(temp_dir, "background.jpg")
    
    # Extract keywords
    script_lower = script.lower()
    if "sibling" in script_lower or "squabbling" in script_lower:
        keywords = ["siblings playing", "brother sister", "family kids"]
    elif "bedtime" in script_lower or "sleep" in script_lower:
        keywords = ["bedtime story", "mother child sleeping", "bedtime routine"]
    elif "eat" in script_lower or "food" in script_lower:
        keywords = ["family dinner", "child eating", "healthy food kids"]
    elif "morning" in script_lower or "routine" in script_lower:
        keywords = ["morning family", "breakfast kids", "getting ready"]
    else:
        keywords = ["mother child", "happy family", "parenting love"]
    
    pixabay_prompt = random.choice(keywords)
    
    print(f"Searching for image: {pixabay_prompt}")
    
    # Try Pixabay
    if "PIXABAY_KEY" in os.environ:
        try:
            response = requests.get(
                "https://pixabay.com/api/",
                params={
                    "key": os.environ["PIXABAY_KEY"],
                    "q": pixabay_prompt,
                    "image_type": "photo",
                    "orientation": "vertical",
                    "per_page": 20,
                    "safesearch": "true"
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
                        print("✅ Pixabay image downloaded")
                        return image_path
        except Exception as e:
            print(f"Pixabay error: {e}")
    
    # Try AI generation as fallback
    try:
        clean_prompt = pixabay_prompt.replace(" ", "%20")
        api_url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1080&height=1920"
        
        response = requests.get(api_url, timeout=30)
        if response.status_code == 200:
            with open(image_path, 'wb') as f:
                f.write(response.content)
            print("✅ AI image generated")
            return image_path
    except Exception as e:
        print(f"AI image error: {e}")
    
    return None

async def edge_tts_generate(text, path, voice="en-US-AriaNeural"):
    """Generate speech using Edge TTS"""
    try:
        tts = edge_tts.Communicate(text, voice)
        await tts.save(path)
        return True
    except Exception as e:
        print(f"Edge TTS failed: {e}")
        return False

def create_voiceover(script, temp_dir):
    """Create voiceover in the specified temp directory"""
    voice_path = os.path.join(temp_dir, "voiceover.mp3")
    
    print("Creating voiceover...")
    
    # Try Edge TTS first
    if EDGE_TTS_AVAILABLE:
        try:
            success = asyncio.run(edge_tts_generate(script, voice_path))
            if success:
                print("✅ Voiceover created with Edge TTS")
                return voice_path
        except Exception as e:
            print(f"Edge TTS error: {e}")
    
    # Fallback to gTTS
    try:
        tts = gTTS(text=script, lang='en', slow=False)
        tts.save(voice_path)
        time.sleep(1)
        print("✅ Voiceover created with gTTS")
        return voice_path
    except Exception as e:
        print(f"gTTS error: {e}")
    
    return None

def get_audio_duration(audio_path):
    """Get the duration of an audio file"""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', audio_path
        ], capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except:
        return 15.0

def create_video_with_text(script, output_path="mom_reel.mp4"):
    """Main function to create video with all assets in same temp directory"""
    
    # Create ONE temp directory for all files
    temp_dir = tempfile.mkdtemp()
    print(f"Working in temp directory: {temp_dir}")
    
    # Step 1: Create voiceover
    voice_path = create_voiceover(script, temp_dir)
    if not voice_path or not os.path.exists(voice_path):
        print(f"❌ Voiceover file not created or not found at: {voice_path}")
        return False
    
    print(f"Voiceover exists: {os.path.exists(voice_path)}, size: {os.path.getsize(voice_path) if os.path.exists(voice_path) else 0} bytes")
    
    # Step 2: Get background image
    image_path = get_background_image(script, temp_dir)
    if not image_path or not os.path.exists(image_path):
        print("❌ Could not get background image")
        return False
    
    print(f"Background image exists: {os.path.exists(image_path)}")
    
    # Step 3: Get audio duration
    duration = get_audio_duration(voice_path)
    print(f"Audio duration: {duration:.2f} seconds")
    
    # Step 4: Prepare text for display
    lines = textwrap.wrap(script, width=35)
    if len(lines) > 4:
        lines = lines[:4]
    
    # Build the FFmpeg filter
    width, height = 1080, 1920
    drawtext_parts = []
    y_start = 400
    
    for i, line in enumerate(lines):
        # Properly escape for FFmpeg
        line_escaped = line.replace("'", "'\\\\\\''")
        y_pos = y_start + (i * 100)
        drawtext_parts.append(f"drawtext=text='{line_escaped}':fontcolor=#FFD700:fontsize=60:box=1:boxcolor=#000000@0.7:boxborderw=5:x=(w-text_w)/2:y={y_pos}")
    
    # Combine all filters
    video_filter = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},"
    video_filter += ','.join(drawtext_parts)
    
    # SIMPLE FFMPEG COMMAND - All files in same temp directory
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-loop', '1',
        '-i', image_path,      # Background image
        '-i', voice_path,      # Voiceover audio
        '-filter_complex', video_filter,
        '-map', '0:v:0',       # Map video from first input
        '-map', '1:a:0',       # Map audio from second input
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-t', str(duration),
        '-shortest',
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        output_path
    ]
    
    print("Running FFmpeg...")
    print(f"Image: {image_path}")
    print(f"Audio: {voice_path}")
    
    try:
        # Run with timeout
        result = subprocess.run(
            ffmpeg_cmd, 
            capture_output=True, 
            text=True,
            timeout=60  # 60 second timeout
        )
        
        print(f"FFmpeg return code: {result.returncode}")
        
        if result.returncode != 0:
            print("FFmpeg failed!")
            print(f"STDERR:\n{result.stderr[:500]}")  # First 500 chars
            print(f"STDOUT:\n{result.stdout}")
            
            # Try ultra-simple fallback
            return create_ultra_simple_video(image_path, voice_path, duration, output_path)
        
        print("✅ FFmpeg completed successfully")
        
        # Verify output
        if os.path.exists(output_path):
            filesize = os.path.getsize(output_path)
            print(f"✅ Video created: {output_path} ({filesize/1024/1024:.1f} MB)")
            
            # Quick check for audio
            check_cmd = ['ffprobe', '-i', output_path, '-show_streams', '-select_streams', 'a', '-loglevel', 'quiet']
            check_result = subprocess.run(check_cmd, capture_output=True, text=True)
            if check_result.returncode == 0:
                print("✅ Video has audio track")
            else:
                print("⚠️ Video may not have audio")
            
            return True
        else:
            print("❌ Output file not created")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ FFmpeg timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"❌ FFmpeg exception: {e}")
        return False

def create_ultra_simple_video(image_path, voice_path, duration, output_path):
    """Ultra-simple video creation as last resort"""
    try:
        print("Trying ultra-simple video creation...")
        
        # First create video without audio
        temp_video = output_path.replace('.mp4', '_temp.mp4')
        cmd1 = [
            'ffmpeg', '-y',
            '-loop', '1',
            '-i', image_path,
            '-c:v', 'libx264',
            '-t', str(duration),
            '-pix_fmt', 'yuv420p',
            temp_video
        ]
        
        subprocess.run(cmd1, check=True, capture_output=True)
        
        # Then add audio
        cmd2 = [
            'ffmpeg', '-y',
            '-i', temp_video,
            '-i', voice_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-shortest',
            output_path
        ]
        
        subprocess.run(cmd2, check=True, capture_output=True)
        
        # Clean up
        if os.path.exists(temp_video):
            os.remove(temp_video)
            
        print("✅ Ultra-simple video created")
        return True
        
    except Exception as e:
        print(f"❌ Ultra-simple video failed: {e}")
        return False

def generate_hashtags(script):
    """Generate relevant hashtags"""
    base_hashtags = [
        "#MomHacks", "#ParentingTips", "#Motherhood", 
        "#RaisingKids", "#FamilyLife", "#MomLife"
    ]
    
    script_lower = script.lower()
    
    if any(word in script_lower for word in ["sibling", "squabbl"]):
        base_hashtags.extend(["#SiblingRivalry", "#Siblings"])
    elif any(word in script_lower for word in ["bedtime", "sleep"]):
        base_hashtags.extend(["#BedtimeRoutine", "#SleepTraining"])
    
    return " ".join(base_hashtags[:10])

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
            print("✅ Video posted to Facebook!")
            return True
        else:
            print(f"Facebook error: {response.status_code}")
            return False
    except Exception as e:
        print(f"Upload error: {e}")
        return False

def main():
    print("=== Mom Wisdom Reel Creator ===")
    
    # Initialize post history
    post_history = PostHistory()
    
    # Generate script
    script = generate_voiceover_script(post_history)
    if not script:
        print("❌ Could not generate script")
        return
    
    print(f"\n🎙️ SCRIPT:\n{script}\n")
    
    # Create video
    video_path = "mom_reel.mp4"
    if create_video_with_text(script, video_path):
        print(f"\n✅ Video created successfully: {video_path}")
        
        # Add to history
        post_history.add_post(script, video_path)
        
        # Post to Facebook if credentials exist
        if all(key in os.environ for key in ["FB_PAGE_ID", "FB_PAGE_TOKEN"]):
            print("📤 Posting to Facebook...")
            if post_to_facebook(video_path, script):
                print("✅ Post completed!")
            else:
                print("❌ Facebook post failed")
        else:
            print("ℹ️ No Facebook credentials - video saved locally")
            
        # Save description
        with open("description.txt", "w") as f:
            f.write(f"{script}\n\n{generate_hashtags(script)}\n\n👇 Follow for more tips!")
            
    else:
        print("❌ Video creation failed")

if __name__ == "__main__":
    main()