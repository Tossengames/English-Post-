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
    def __init__(self, history_file="parenting_history.json"):
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
    
    def add_post(self, title, tip, video_path=None):
        """Add a post to history"""
        post_id = hashlib.md5(f"{title}{tip}".encode()).hexdigest()
        self.history[post_id] = {
            'title': title,
            'tip': tip,
            'date': datetime.now().isoformat(),
            'video_path': video_path,
            'topic': title.lower()
        }
        self.save_history()
    
    def is_duplicate_topic(self, title):
        """Check if a topic has been used before"""
        topic = title.lower()
        for post_data in self.history.values():
            if post_data.get('topic', '').lower() == topic:
                return True
        return False
    
    def is_duplicate_content(self, title, tip):
        """Check if exact content has been used before"""
        post_id = hashlib.md5(f"{title}{tip}".encode()).hexdigest()
        return post_id in self.history

def generate_parenting_tip(post_history):
    """Generate a parenting tip using Gemini 2.5 Flash"""
    
    # List of diverse parenting topics
    parenting_topics = [
        "child development", "parenting strategies", "positive discipline",
        "emotional intelligence", "educational activities", "child nutrition",
        "sleep training", "behavior management", "early childhood education",
        "parent-child bonding", "safety tips for children", "digital parenting",
        "school readiness", "social skills development", "healthy habits",
        "creative play", "stress management for parents", "family routines",
        "communication with children", "building confidence in kids"
    ]
    
    # Try AI generation first
    for attempt in range(5):  # Try 5 times to get a unique topic
        category = random.choice(parenting_topics)
        
        prompt = f"""Generate ONE practical parenting tip about {category}.
        Return ONLY in this exact format: title .| tip
        
        Rules:
        - Make it practical and useful for parents
        - Keep it concise (one sentence)
        - Focus on evidence-based advice
        - Ensure information is accurate
        - Do not include phrases like "Did you know" or "Remember this"
        - Make it sound natural and direct
        - Title should be specific to the topic
        - Use commas to create natural pauses in speech"""
        
        try:
            genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            
            if '|' in response.text:
                title_part, tip = response.text.strip().split('|', 1)
                title = title_part.replace('.', '').strip()
                title, tip = title.strip(), tip.strip()
                
                # Check if this topic has been used before
                if not post_history.is_duplicate_topic(title) and not post_history.is_duplicate_content(title, tip):
                    return title, tip
                else:
                    print(f"Duplicate topic detected: {title}. Trying again...")
        except Exception as e:
            print(f"Gemini API error: {e}")
            continue
    
    # If we can't get a unique topic after 5 attempts, return None
    return None, None

def escape_text(text):
    """Escape text for use in FFmpeg filter strings"""
    # Escape single quotes by replacing them with '\''
    text = text.replace("'", "'\\''")
    # Remove other problematic characters
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    return text

def get_dark_color():
    """Generate darker, more visible colors for text on white background"""
    dark_colors = [
        "darkblue", "darkred", "darkgreen", "darkmagenta", "darkcyan",
        "black", "navy", "maroon", "purple", "indigo", "brown", "olive"
    ]
    return random.choice(dark_colors)

def get_pixabay_image(prompt, output_path):
    """Get image from Pixabay API"""
    if "PIXABAY_KEY" not in os.environ:
        return False
    
    try:
        # Map parenting topics to search keywords
        keyword_map = {
            "child development": "child learning",
            "parenting strategies": "family parenting",
            "positive discipline": "child discipline",
            "emotional intelligence": "child emotions",
            "educational activities": "children playing",
            "child nutrition": "healthy food children",
            "sleep training": "baby sleeping",
            "behavior management": "child behavior",
            "early childhood education": "preschool",
            "parent-child bonding": "family love",
            "safety tips": "child safety",
            "digital parenting": "technology children",
            "school readiness": "school children",
            "social skills": "children playing together",
            "healthy habits": "children exercise",
            "creative play": "creative children",
            "stress management": "relaxed parents",
            "family routines": "family routine",
            "communication": "parent talking child",
            "building confidence": "confident child"
        }
        
        # Find the best keyword based on prompt
        best_keyword = "family parenting"
        for topic, keyword in keyword_map.items():
            if topic in prompt.lower():
                best_keyword = keyword
                break
        
        response = requests.get(
            "https://pixabay.com/api/",
            params={
                "key": os.environ["PIXABAY_KEY"],
                "q": best_keyword,
                "image_type": "photo",
                "orientation": "vertical",
                "per_page": 50,
                "safesearch": "true",
                "category": "people",  # Focus on people/family category
                "editors_choice": "true"  # Higher quality images
            },
            timeout=30
        )
        
        if response.status_code == 200:
            images = response.json().get('hits', [])
            if images:
                # Filter for vertical images
                vertical_images = [img for img in images if img.get('imageHeight', 0) > img.get('imageWidth', 1)]
                if vertical_images:
                    image_url = random.choice(vertical_images)['largeImageURL']
                else:
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
        # Clean up the prompt for URL
        clean_prompt = prompt.replace(" ", "%20").replace(",", "%2C")
        api_url = f"https://image.pollinations.ai/prompt/{clean_prompt}"
        
        response = requests.get(api_url, timeout=30)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"Pollinations.ai error: {e}")
    
    return False

def get_background_image(title, tip):
    """Get background image - try Pixabay first, then AI"""
    temp_dir = tempfile.mkdtemp()
    image_path = os.path.join(temp_dir, "background.jpg")
    
    # Create a search prompt for Pixabay
    pixabay_prompt = f"{title} {tip}"
    
    print(f"Trying Pixabay for: {title}")
    
    # Try Pixabay first
    if get_pixabay_image(pixabay_prompt, image_path):
        print("✅ Pixabay image found")
        return image_path
    
    # If Pixabay fails, try AI image generation
    ai_prompt = f"beautiful vertical background about {title.lower()}, {tip.lower()}, professional photography, high quality, 4k, family friendly"
    
    print(f"Trying AI image generation: {ai_prompt}")
    
    if get_ai_generated_image(ai_prompt, image_path):
        print("✅ AI image generated successfully")
        return image_path
    
    # If both fail, skip image
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

def create_voiceover(title, tip, output_path):
    """Create voiceover using Edge TTS if available, otherwise gTTS"""
    temp_dir = tempfile.mkdtemp()
    
    # CHANGED: Use male voice instead of female
    voice = "en-US-GuyNeural"  # Changed from "en-US-AriaNeural"
    
    # Create the text to be spoken
    spoken_text = f"{tip}"
    
    print("Creating voiceover with natural pauses...")
    
    # Try Edge TTS first if available
    if EDGE_TTS_AVAILABLE:
        print("Trying Edge TTS...")
        try:
            success = asyncio.run(edge_tts_generate(spoken_text, output_path, voice))
            if success:
                print("✅ Voiceover created with Edge TTS (Male voice with natural pauses)")
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
        return 10  # Fallback duration

def create_vertical_video(title, tip, output_path):
    """Create vertical video optimized for Facebook Shorts/Reels"""
    temp_dir = tempfile.mkdtemp()
    voice_path = os.path.join(temp_dir, "voiceover.mp3")
    
    if not create_voiceover(title, tip, voice_path):
        print("❌ Failed to create voiceover")
        return False

    # Get actual duration from the voiceover file
    duration = get_audio_duration(voice_path)
    print(f"Video duration: {duration:.2f} seconds")
    
    bg_image = get_background_image(title, tip)
    
    if bg_image is None:
        print("❌ Skipping video creation due to no background image")
        return False
    
    # Vertical format for Shorts/Reels (9:16 aspect ratio)
    width, height = 1080, 1920

    if os.path.exists(bg_image):
        # Use the obtained image
        input_source = ['-loop', '1', '-i', bg_image]
        video_filters = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},format=yuv420p"
    else:
        print("❌ Background image file not found")
        return False

    # Escape text for FFmpeg
    escaped_title = escape_text(title)
    escaped_tip = escape_text(tip)
    
    # Wrap text for better readability
    wrapped_tip = textwrap.fill(escaped_tip, width=35)
    
    # CHANGED: Get darker, more visible colors for text
    header_color = get_dark_color()
    title_color = get_dark_color()
    tip_color = get_dark_color()
    
    # Ensure we don't get the same color for all text elements
    while title_color == header_color:
        title_color = get_dark_color()
    while tip_color == header_color or tip_color == title_color:
        tip_color = get_dark_color()
    
    print(f"Using colors - Header: {header_color}, Title: {title_color}, Tip: {tip_color}")
    
    # Create a filter script file
    filter_script = os.path.join(temp_dir, "filter.txt")
    with open(filter_script, 'w') as f:
        f.write(f"""
        [0:v]{video_filters},
        drawtext=text='PARENTING TIPS':fontcolor={header_color}:fontsize=70:box=1:boxcolor=white@1.0:boxborderw=15:x=(w-text_w)/2:y=350,
        drawtext=text='{escaped_title}':fontcolor={title_color}:fontsize=60:box=1:boxcolor=white@1.0:boxborderw=10:x=(w-text_w)/2:y=500,
        drawtext=text='{wrapped_tip}':fontcolor={tip_color}:fontsize=50:box=1:boxcolor=white@1.0:boxborderw=10:x=(w-text_w)/2:y=700
        """)
    
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        *input_source,
        '-i', voice_path,
        '-filter_complex_script', filter_script,
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

def generate_hashtags(title, tip):
    """Generate relevant parenting hashtags"""
    base_hashtags = [
        "#ParentingTips", "#ParentingAdvice", "#ChildDevelopment", 
        "#PositiveParenting", "#FamilyLife", "#ParentingHacks",
        "#RaisingKids", "#MomLife", "#DadLife", "#ParentingJourney",
        "#FamilyFirst", "#ParentingGoals", "#ModernParenting"
    ]
    
    # Add topic-specific hashtags
    title_lower = title.lower()
    tip_lower = tip.lower()
    
    if "sleep" in title_lower or "sleep" in tip_lower:
        base_hashtags.extend(["#SleepTraining", "#BedtimeRoutine", "#BabySleep"])
    elif "nutrition" in title_lower or "food" in tip_lower:
        base_hashtags.extend(["#ChildNutrition", "#HealthyKids", "#KidsFood"])
    elif "education" in title_lower or "learning" in tip_lower:
        base_hashtags.extend(["#EarlyEducation", "#LearningThroughPlay", "#EducationalActivities"])
    elif "discipline" in title_lower or "behavior" in tip_lower:
        base_hashtags.extend(["#PositiveDiscipline", "#ChildBehavior", "#BehaviorManagement"])
    elif "emotion" in title_lower or "emotional" in tip_lower:
        base_hashtags.extend(["#EmotionalIntelligence", "#SocialEmotionalLearning"])
    
    return " ".join(base_hashtags[:15])

def post_to_facebook(video_path, title, tip):
    try:
        hashtags = generate_hashtags(title, tip)
        
        with open(video_path, 'rb') as video_file:
            response = requests.post(
                f"https://graph.facebook.com/v19.0/{os.environ['FB_PAGE_ID']}/videos",
                params={
                    "access_token": os.environ["FB_PAGE_TOKEN"],
                    "description": f"👨‍👩‍👧‍👦 {title}\n\n{tip}\n\n{hashtags}"
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
    print("=== Parenting Tips Video Creator ===")
    
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
    
    # Generate unique parenting tip with natural punctuation
    title, tip = generate_parenting_tip(post_history)
    
    if title is None or tip is None:
        print("❌ Could not generate a unique parenting tip after multiple attempts")
        print("Please try again later or add more topics to the list")
        return
    
    print(f"Title: {title}")
    print(f"Tip (with natural pauses): {tip}")

    video_path = "parenting_tips_shorts.mp4"
    if create_vertical_video(title, tip, video_path):
        print(f"✅ Vertical video created: {video_path}")
        
        # Add to post history
        post_history.add_post(title, tip, video_path)
        
        if all(key in os.environ for key in ["FB_PAGE_ID", "FB_PAGE_TOKEN"]):
            print("📤 Posting to Facebook Shorts...")
            if post_to_facebook(video_path, title, tip):
                print("✅ Post completed successfully!")
            else:
                print("❌ Failed to post to Facebook")
        else:
            print("ℹ️ Facebook credentials not found - video saved locally")

        # Save description with hashtags
        hashtags = generate_hashtags(title, tip)
        with open("video_description.txt", "w") as f:
            f.write(f"👨‍👩‍👧‍👦 {title}\n\n")
            f.write(f"{tip}\n\n")
            f.write(f"{hashtags}")
    else:
        print("❌ Failed to create video - skipping")

if __name__ == "__main__":
    main()