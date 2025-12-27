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
    
    def add_post(self, problem, solution, hook, video_path=None):
        """Add a post to history"""
        post_id = hashlib.md5(f"{problem}{solution}".encode()).hexdigest()
        self.history[post_id] = {
            'problem': problem,
            'solution': solution,
            'hook': hook,
            'date': datetime.now().isoformat(),
            'video_path': video_path,
            'topic': problem.lower()
        }
        self.save_history()
    
    def is_duplicate_topic(self, problem):
        """Check if a topic has been used before"""
        topic = problem.lower()
        for post_data in self.history.values():
            if post_data.get('topic', '').lower() == topic:
                return True
        return False
    
    def is_duplicate_content(self, problem, solution):
        """Check if exact content has been used before"""
        post_id = hashlib.md5(f"{problem}{solution}".encode()).hexdigest()
        return post_id in self.history

def generate_mom_issue_solution(post_history):
    """Generate a common mom issue and practical solution using Gemini"""
    
    # Common issues moms/parents face
    mom_issues = [
        "bedtime battles", "picky eating", "tantrums in public", 
        "sibling rivalry", "homework struggles", "screen time addiction",
        "morning routine chaos", "potty training resistance", "separation anxiety",
        "sharing problems", "backtalk and defiance", "mealtime messes",
        "home organization with kids", "lack of me-time", "mom guilt",
        "balancing work and family", "sleep deprivation", "meal planning stress",
        "holiday stress with kids", "handling meltdowns", "discipline consistency",
        "chores and responsibility", "friendship issues", "school anxiety",
        "holiday gift overwhelm", "summer boredom", "holiday traveling with kids",
        "managing kid's extracurriculars", "dealing with comparison", "self-care neglect"
    ]
    
    # Try AI generation first
    for attempt in range(5):  # Try 5 times to get a unique topic
        issue = random.choice(mom_issues)
        
        prompt = f"""Generate a COMMON MOM/PARENTING PROBLEM and PRACTICAL SOLUTION about: {issue}

        Format EXACTLY like this:
        PROBLEM|SOLUTION|HOOK
        
        Requirements:
        PROBLEM: Describe one specific, relatable parenting struggle (1 sentence)
        SOLUTION: Provide one actionable, evidence-based solution (1-2 sentences)
        HOOK: Start with "Struggling with [issue]?" or "Tired of [issue]?" or "Mom hack for [issue]:" - make it engaging and attention-grabbing
        
        Example:
        PROBLEM|SOLUTION|HOOK
        Your toddler throws food at every meal|Serve meals in silicone suction plates and offer only 2-3 foods at a time to reduce overwhelm|Tired of cleaning food off walls after every meal?
        
        Make it:
        - Highly relatable to moms/parents
        - Actionable and practical
        - Evidence-based when possible
        - Non-judgmental and supportive
        - Clear and concise
        """
        
        try:
            genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            
            if response.text.count('|') == 2:
                problem, solution, hook = response.text.strip().split('|')
                problem, solution, hook = problem.strip(), solution.strip(), hook.strip()
                
                # Check if this topic has been used before
                if not post_history.is_duplicate_topic(problem) and not post_history.is_duplicate_content(problem, solution):
                    return problem, solution, hook
                else:
                    print(f"Duplicate topic detected: {problem}. Trying again...")
        except Exception as e:
            print(f"Gemini API error: {e}")
            continue
    
    # Fallback if AI fails
    fallback_issues = [
        ("Kids refusing to brush teeth", "Make it a game - have a 'toothbrush race' or use fun character brushes", "Struggling with toothbrush tantrums?"),
        ("Endless 'why' questions", "Answer with 'What do you think?' to encourage critical thinking", "Exhausted by constant 'why' questions?"),
        ("Messy playroom chaos", "Use picture labels on bins and have 5-minute nightly clean-up races", "Tired of tripping over toys?"),
        ("Morning routine taking forever", "Create a visual checklist with photos for each step", "Mornings feeling like a marathon?"),
        ("Kids fighting in the car", "Assign 'car jobs' like DJ or navigator to prevent boredom", "Car rides turning into battle zones?"),
    ]
    
    for problem, solution, hook in fallback_issues:
        if not post_history.is_duplicate_topic(problem):
            return problem, solution, hook
    
    return None, None, None

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
        # Map mom issues to search keywords
        keyword_map = {
            "bedtime": "bedtime children",
            "eating": "child eating",
            "tantrums": "child tantrum",
            "sibling": "siblings playing",
            "homework": "homework children",
            "screen": "tablet children",
            "morning": "morning routine family",
            "potty": "potty training",
            "anxiety": "worried child",
            "sharing": "children sharing",
            "defiance": "stubborn child",
            "mealtime": "family dinner",
            "organization": "organized home",
            "guilt": "stressed mom",
            "balancing": "working mom",
            "sleep": "tired mom",
            "meal planning": "meal prep",
            "stress": "stressed parents",
            "meltdown": "child crying",
            "discipline": "parent teaching",
            "chores": "children chores",
            "friendship": "children playing",
            "school": "school children",
            "gift": "holiday gifts",
            "boredom": "bored children",
            "traveling": "family travel",
            "extracurricular": "sports children",
            "comparison": "mother daughter",
            "self-care": "mom relaxing"
        }
        
        # Find the best keyword based on prompt
        best_keyword = "mother children"
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
                "category": "people",
                "editors_choice": "true"
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

def get_background_image(hook, problem):
    """Get background image - try Pixabay first, then AI"""
    temp_dir = tempfile.mkdtemp()
    image_path = os.path.join(temp_dir, "background.jpg")
    
    # Create a search prompt for Pixabay
    pixabay_prompt = f"{hook} {problem}"
    
    print(f"Trying Pixabay for: {problem}")
    
    # Try Pixabay first
    if get_pixabay_image(pixabay_prompt, image_path):
        print("✅ Pixabay image found")
        return image_path
    
    # If Pixabay fails, try AI image generation
    ai_prompt = f"mother dealing with {problem.lower()}, realistic photo, emotional, supportive, vertical, 4k"
    
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

def create_voiceover(hook, problem, solution, output_path):
    """Create voiceover with strong hook and natural delivery"""
    temp_dir = tempfile.mkdtemp()
    
    # Use empathetic female voice
    voice = "en-US-AriaNeural"
    
    # Create the text to be spoken with engaging delivery
    spoken_text = f"{hook}. I know this struggle. {problem} Here's what actually works: {solution}"
    
    print("Creating voiceover with engaging hook...")
    
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
        return 12  # Slightly longer fallback for problem-solution format

def create_vertical_video(hook, problem, solution, output_path):
    """Create vertical video with problem-solution format"""
    temp_dir = tempfile.mkdtemp()
    voice_path = os.path.join(temp_dir, "voiceover.mp3")
    
    if not create_voiceover(hook, problem, solution, voice_path):
        print("❌ Failed to create voiceover")
        return False

    # Get actual duration from the voiceover file
    duration = get_audio_duration(voice_path)
    print(f"Video duration: {duration:.2f} seconds")
    
    bg_image = get_background_image(hook, problem)
    
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
    escaped_hook = escape_text(hook)
    escaped_problem = escape_text(problem)
    escaped_solution = escape_text(solution)
    
    # Wrap text for better readability
    wrapped_hook = textwrap.fill(escaped_hook, width=35)
    wrapped_problem = textwrap.fill(escaped_problem, width=40)
    wrapped_solution = textwrap.fill(escaped_solution, width=40)
    
    # Get contrasting colors
    hook_color = "darkred"  # Attention-grabbing for hook
    problem_color = "darkblue"  # Sober color for problem
    solution_color = "darkgreen"  # Positive color for solution
    
    # Create a filter script file
    filter_script = os.path.join(temp_dir, "filter.txt")
    with open(filter_script, 'w') as f:
        f.write(f"""
        [0:v]{video_filters},
        drawtext=text='MOM HACKS':fontcolor=purple:fontsize=80:box=1:boxcolor=white@1.0:boxborderw=15:x=(w-text_w)/2:y=200,
        drawtext=text='{wrapped_hook}':fontcolor={hook_color}:fontsize=65:box=1:boxcolor=white@1.0:boxborderw=10:x=(w-text_w)/2:y=350,
        drawtext=text='THE STRUGGLE:':fontcolor=navy:fontsize=50:box=1:boxcolor=white@1.0:boxborderw=5:x=(w-text_w)/2:y=550,
        drawtext=text='{wrapped_problem}':fontcolor={problem_color}:fontsize=45:box=1:boxcolor=white@1.0:boxborderw=5:x=(w-text_w)/2:y=650,
        drawtext=text='TRY THIS:':fontcolor=darkgreen:fontsize=50:box=1:boxcolor=white@1.0:boxborderw=5:x=(w-text_w)/2:y=950,
        drawtext=text='{wrapped_solution}':fontcolor={solution_color}:fontsize=45:box=1:boxcolor=white@1.0:boxborderw=5:x=(w-text_w)/2:y=1050,
        drawtext=text='Follow for more mom solutions!':fontcolor=darkmagenta:fontsize=40:x=(w-text_w)/2:y=1400
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

def generate_hashtags(problem, solution):
    """Generate relevant mom/parenting hashtags"""
    base_hashtags = [
        "#MomHacks", "#ParentingProblems", "#MomLife", 
        "#ParentingSolutions", "#Motherhood", "#RaisingKids",
        "#ParentingTips", "#MomStruggles", "#PracticalParenting",
        "#FamilyLife", "#ParentingWin", "#MomAdvice",
        "#ToddlerLife", "#ParentingHacks", "#RealMotherhood"
    ]
    
    # Add problem-specific hashtags
    problem_lower = problem.lower()
    
    if any(word in problem_lower for word in ["bedtime", "sleep"]):
        base_hashtags.extend(["#BedtimeStruggles", "#SleepTraining", "#ToddlerSleep"])
    elif any(word in problem_lower for word in ["eat", "food", "meal"]):
        base_hashtags.extend(["#PickyEater", "#Mealtime", "#KidsNutrition"])
    elif any(word in problem_lower for word in ["tantrum", "meltdown", "behavior"]):
        base_hashtags.extend(["#Tantrums", "#ChildBehavior", "#GentleParenting"])
    elif any(word in problem_lower for word in ["sibling", "fight"]):
        base_hashtags.extend(["#SiblingRivalry", "#Siblings", "#FamilyDynamics"])
    elif any(word in problem_lower for word in ["homework", "school"]):
        base_hashtags.extend(["#HomeworkHelp", "#SchoolStruggles", "#Education"])
    elif any(word in problem_lower for word in ["screen", "tv", "tablet"]):
        base_hashtags.extend(["#ScreenTime", "#DigitalParenting", "#TechAddiction"])
    
    return " ".join(base_hashtags[:15])

def post_to_facebook(video_path, hook, problem, solution):
    try:
        hashtags = generate_hashtags(problem, solution)
        
        with open(video_path, 'rb') as video_file:
            response = requests.post(
                f"https://graph.facebook.com/v19.0/{os.environ['FB_PAGE_ID']}/videos",
                params={
                    "access_token": os.environ["FB_PAGE_TOKEN"],
                    "description": f"🤱 {hook}\n\n💡 PROBLEM: {problem}\n\n✅ SOLUTION: {solution}\n\n{hashtags}\n\n👇 Follow for daily mom solutions!"
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
    print("=== Mom Solutions Video Creator ===")
    print("Creating problem-solution videos for common parenting struggles...")
    
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
    
    # Generate unique mom issue and solution
    problem, solution, hook = generate_mom_issue_solution(post_history)
    
    if problem is None or solution is None or hook is None:
        print("❌ Could not generate a unique mom issue after multiple attempts")
        return
    
    print(f"\n🎯 HOOK: {hook}")
    print(f"💡 PROBLEM: {problem}")
    print(f"✅ SOLUTION: {solution}")

    video_path = "mom_solutions_shorts.mp4"
    if create_vertical_video(hook, problem, solution, video_path):
        print(f"✅ Problem-Solution video created: {video_path}")
        
        # Add to post history
        post_history.add_post(problem, solution, hook, video_path)
        
        if all(key in os.environ for key in ["FB_PAGE_ID", "FB_PAGE_TOKEN"]):
            print("📤 Posting to Facebook Shorts...")
            if post_to_facebook(video_path, hook, problem, solution):
                print("✅ Post completed successfully!")
            else:
                print("❌ Failed to post to Facebook")
        else:
            print("ℹ️ Facebook credentials not found - video saved locally")

        # Save description with hashtags
        hashtags = generate_hashtags(problem, solution)
        with open("video_description.txt", "w") as f:
            f.write(f"🤱 {hook}\n\n")
            f.write(f"💡 PROBLEM: {problem}\n\n")
            f.write(f"✅ SOLUTION: {solution}\n\n")
            f.write(f"{hashtags}\n\n")
            f.write("👇 Follow for daily mom solutions!")
    else:
        print("❌ Failed to create video - skipping")

if __name__ == "__main__":
    main()