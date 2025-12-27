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
        self.template_history = {}
    
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
    
    def add_post(self, problem, solution, hook, template_type, video_path=None):
        """Add a post to history"""
        post_id = hashlib.md5(f"{problem}{solution}".encode()).hexdigest()
        self.history[post_id] = {
            'problem': problem,
            'solution': solution,
            'hook': hook,
            'template_type': template_type,
            'date': datetime.now().isoformat(),
            'video_path': video_path,
            'topic': problem.lower()
        }
        self.template_history[post_id] = template_type
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
    
    def get_next_template(self):
        """Get next template type, avoiding recent ones"""
        template_types = ['question', 'confession', 'challenge', 'reveal', 'story', 'secret', 'warning', 'promise']
        
        # If we have history, find least recently used template
        if self.template_history:
            recent_templates = list(self.template_history.values())[-3:]  # Last 3 used templates
            available = [t for t in template_types if t not in recent_templates]
            if available:
                return random.choice(available)
        
        return random.choice(template_types)

def generate_mom_issue_solution(post_history):
    """Generate a common mom issue and practical solution using Gemini"""
    
    # Get template type for this post
    template_type = post_history.get_next_template()
    
    # Template-specific hooks and formats
    template_configs = {
        'question': {
            'prompt_keyword': 'question format',
            'hook_patterns': [
                "Struggling with {issue}?",
                "Tired of {issue}?",
                "Does your child {issue}?",
                "Overwhelmed by {issue}?"
            ]
        },
        'confession': {
            'prompt_keyword': 'confession format',
            'hook_patterns': [
                "I used to struggle with {issue} too...",
                "Confession: I almost gave up on {issue}",
                "Mom truth: {issue} was my biggest challenge"
            ]
        },
        'challenge': {
            'prompt_keyword': 'challenge format',
            'hook_patterns': [
                "The {issue} challenge every mom faces",
                "Biggest parenting challenge: {issue}",
                "Overcoming the {issue} struggle"
            ]
        },
        'reveal': {
            'prompt_keyword': 'reveal format',
            'hook_patterns': [
                "What no one tells you about {issue}",
                "The secret to fixing {issue}",
                "Revealing the truth about {issue}"
            ]
        },
        'story': {
            'prompt_keyword': 'story format',
            'hook_patterns': [
                "When my child wouldn't stop {issue}...",
                "The day {issue} changed everything",
                "My {issue} breakthrough story"
            ]
        },
        'secret': {
            'prompt_keyword': 'secret format',
            'hook_patterns': [
                "The mom secret for {issue}",
                "Shhh... my {issue} hack",
                "What experienced moms know about {issue}"
            ]
        },
        'warning': {
            'prompt_keyword': 'warning format',
            'hook_patterns': [
                "Warning: {issue} could be hurting your child",
                "Don't make this {issue} mistake",
                "The {issue} trap most moms fall into"
            ]
        },
        'promise': {
            'prompt_keyword': 'promise format',
            'hook_patterns': [
                "I promise this works for {issue}",
                "Guaranteed fix for {issue}",
                "This will solve your {issue} problem"
            ]
        }
    }
    
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
        config = template_configs[template_type]
        hook_pattern = random.choice(config['hook_patterns'])
        
        prompt = f"""Generate a COMMON MOM/PARENTING PROBLEM and PRACTICAL SOLUTION about: {issue}
        Use a {config['prompt_keyword']}.

        Format EXACTLY like this:
        PROBLEM|SOLUTION|HOOK
        
        Requirements:
        PROBLEM: Describe one specific, relatable parenting struggle (1 sentence)
        SOLUTION: Provide one actionable, evidence-based solution (1-2 sentences)
        HOOK: Start with: "{hook_pattern.format(issue=issue)}" - make it engaging and attention-grabbing
        
        Example for {template_type} format:
        PROBLEM|SOLUTION|HOOK
        Your toddler throws food at every meal|Serve meals in silicone suction plates and offer only 2-3 foods at a time to reduce overwhelm|{random.choice(config['hook_patterns']).format(issue="mealtime battles")}
        
        Make it:
        - Highly relatable to moms/parents
        - Actionable and practical
        - Evidence-based when possible
        - Non-judgmental and supportive
        - Clear and concise
        - Match the {template_type} tone
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
                    return problem, solution, hook, template_type
                else:
                    print(f"Duplicate topic detected: {problem}. Trying again...")
        except Exception as e:
            print(f"Gemini API error: {e}")
            continue
    
    # Fallback if AI fails
    fallback_issues = [
        ("Kids refusing to brush teeth", "Make it a game - have a 'toothbrush race' or use fun character brushes", "Struggling with toothbrush tantrums?", 'question'),
        ("Endless 'why' questions", "Answer with 'What do you think?' to encourage critical thinking", "I used to get so frustrated with constant questions...", 'confession'),
        ("Messy playroom chaos", "Use picture labels on bins and have 5-minute nightly clean-up races", "The organization challenge every mom faces", 'challenge'),
        ("Morning routine taking forever", "Create a visual checklist with photos for each step", "What no one tells you about morning routines", 'reveal'),
        ("Kids fighting in the car", "Assign 'car jobs' like DJ or navigator to prevent boredom", "When my kids wouldn't stop fighting in the car...", 'story'),
    ]
    
    for problem, solution, hook, fallback_type in fallback_issues:
        if not post_history.is_duplicate_topic(problem):
            return problem, solution, hook, fallback_type
    
    return None, None, None, None

def escape_text(text):
    """Escape text for use in FFmpeg filter strings"""
    # Escape single quotes by replacing them with '\''
    text = text.replace("'", "'\\''")
    # Remove other problematic characters
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    return text

def get_background_image(hook, problem, template_type):
    """Get background image - try Pixabay first, then AI"""
    temp_dir = tempfile.mkdtemp()
    image_path = os.path.join(temp_dir, "background.jpg")
    
    # Template-specific search terms
    template_keywords = {
        'question': ["worried mother", "concerned parent", "problem solving"],
        'confession': ["honest moment", "real parenting", "authentic mother"],
        'challenge': ["overcoming challenge", "determined mom", "persistent parent"],
        'reveal': ["surprise moment", "discovery", "lightbulb moment"],
        'story': ["storytelling", "family moment", "personal journey"],
        'secret': ["secret sharing", "whispering", "confidential"],
        'warning': ["warning sign", "caution", "protective mother"],
        'promise': ["hope", "solution", "happy resolution"]
    }
    
    # Create a search prompt for Pixabay
    keyword = random.choice(template_keywords.get(template_type, ["mother child"]))
    pixabay_prompt = f"{keyword} {problem}"
    
    print(f"Trying Pixabay for: {pixabay_prompt}")
    
    # Try Pixabay first
    if get_pixabay_image(pixabay_prompt, image_path):
        print("✅ Pixabay image found")
        return image_path
    
    # If Pixabay fails, try AI image generation
    ai_prompt = f"mother dealing with {problem.lower()}, {template_type} moment, emotional, realistic, vertical, 4k, golden hour lighting"
    
    print(f"Trying AI image generation: {ai_prompt}")
    
    if get_ai_generated_image(ai_prompt, image_path):
        print("✅ AI image generated successfully")
        return image_path
    
    # If both fail, skip image
    print("❌ Could not get image from Pixabay or AI")
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
                "per_page": 30,
                "safesearch": "true",
                "category": "people",
                "colors": "gold,yellow",  # Prefer gold/yellow tones
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

def create_voiceover(hook, problem, solution, template_type):
    """Create voiceover with template-specific delivery"""
    temp_dir = tempfile.mkdtemp()
    
    # Use empathetic female voice
    voice = "en-US-AriaNeural"
    
    # Template-specific delivery styles
    delivery_styles = {
        'question': f"{hook} I know it's tough. {problem} Here's what actually works: {solution}",
        'confession': f"{hook} {problem} But then I discovered this: {solution}",
        'challenge': f"{hook} {problem} Here's how to overcome it: {solution}",
        'reveal': f"{hook} {problem} The solution surprised me too: {solution}",
        'story': f"{hook} {problem} Here's what changed everything: {solution}",
        'secret': f"{hook} {problem} Here's the secret fix: {solution}",
        'warning': f"{hook} {problem} Do this instead: {solution}",
        'promise': f"{hook} {problem} I promise this will help: {solution}"
    }
    
    spoken_text = delivery_styles.get(template_type, f"{hook} {problem} {solution}")
    output_path = os.path.join(temp_dir, "voiceover.mp3")
    
    print(f"Creating voiceover with {template_type} style...")
    
    # Try Edge TTS first if available
    if EDGE_TTS_AVAILABLE:
        print("Trying Edge TTS...")
        try:
            success = asyncio.run(edge_tts_generate(spoken_text, output_path, voice))
            if success:
                print("✅ Voiceover created with Edge TTS")
                return output_path
        except Exception as e:
            print(f"Edge TTS async error: {e}")
    
    # Fallback to gTTS
    print("Falling back to gTTS...")
    if gtts_generate(spoken_text, output_path):
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
        return 12  # Slightly longer fallback

def get_template_layout(template_type, hook, problem, solution):
    """Get different layouts based on template type"""
    
    # Gold and black color scheme variations
    gold_colors = ["gold", "goldenrod", "darkgoldenrod", "goldenrod1", "gold2"]
    black_colors = ["black", "gray10", "gray15", "gray20"]
    
    primary_gold = random.choice(gold_colors)
    primary_black = random.choice(black_colors)
    
    # Template-specific layouts
    layouts = {
        'question': {
            'title': "MOM QUESTION",
            'hook_prefix': "🤔 ",
            'problem_prefix': "💡 Issue: ",
            'solution_prefix': "✅ Fix: ",
            'bg_overlay': "color=black@0.3",
            'title_y': 200,
            'hook_y': 350,
            'problem_y': 650,
            'solution_y': 950,
            'cta_y': 1400  # Lower CTA position
        },
        'confession': {
            'title': "MOM CONFESSION",
            'hook_prefix': "💬 ",
            'problem_prefix': "😓 Struggle: ",
            'solution_prefix': "✨ Discovery: ",
            'bg_overlay': "color=black@0.4",
            'title_y': 180,
            'hook_y': 320,
            'problem_y': 600,
            'solution_y': 900,
            'cta_y': 1450
        },
        'challenge': {
            'title': "PARENTING CHALLENGE",
            'hook_prefix': "⚡ ",
            'problem_prefix': "🔥 Problem: ",
            'solution_prefix': "🏆 Solution: ",
            'bg_overlay': "color=black@0.2",
            'title_y': 220,
            'hook_y': 380,
            'problem_y': 700,
            'solution_y': 1000,
            'cta_y': 1550
        },
        'reveal': {
            'title': "MOM REVEAL",
            'hook_prefix': "🔍 ",
            'problem_prefix': "📝 Reality: ",
            'solution_prefix': "💎 Truth: ",
            'bg_overlay': "color=black@0.35",
            'title_y': 190,
            'hook_y': 340,
            'problem_y': 620,
            'solution_y': 920,
            'cta_y': 1480
        },
        'story': {
            'title': "MOM STORY",
            'hook_prefix': "📖 ",
            'problem_prefix': "🎭 Scene: ",
            'solution_prefix': "🌟 Ending: ",
            'bg_overlay': "color=black@0.25",
            'title_y': 210,
            'hook_y': 360,
            'problem_y': 640,
            'solution_y': 940,
            'cta_y': 1500
        },
        'secret': {
            'title': "MOM SECRET",
            'hook_prefix': "🤫 ",
            'problem_prefix': "⚠️ Problem: ",
            'solution_prefix': "🔑 Secret: ",
            'bg_overlay': "color=black@0.45",
            'title_y': 180,
            'hook_y': 330,
            'problem_y': 610,
            'solution_y': 910,
            'cta_y': 1470
        },
        'warning': {
            'title': "MOM WARNING",
            'hook_prefix': "🚨 ",
            'problem_prefix': "❌ Don't: ",
            'solution_prefix': "✅ Do: ",
            'bg_overlay': "color=black@0.4",
            'title_y': 200,
            'hook_y': 350,
            'problem_y': 630,
            'solution_y': 930,
            'cta_y': 1520
        },
        'promise': {
            'title': "MOM PROMISE",
            'hook_prefix': "🤝 ",
            'problem_prefix': "💭 Struggle: ",
            'solution_prefix': "🤲 Promise: ",
            'bg_overlay': "color=black@0.3",
            'title_y': 190,
            'hook_y': 340,
            'problem_y': 620,
            'solution_y': 920,
            'cta_y': 1490
        }
    }
    
    layout = layouts.get(template_type, layouts['question'])
    
    # Wrap text
    wrapped_hook = textwrap.fill(hook, width=35)
    wrapped_problem = textwrap.fill(problem, width=40)
    wrapped_solution = textwrap.fill(solution, width=40)
    
    return {
        'title': layout['title'],
        'hook': f"{layout['hook_prefix']}{wrapped_hook}",
        'problem': f"{layout['problem_prefix']}{wrapped_problem}",
        'solution': f"{layout['solution_prefix']}{wrapped_solution}",
        'bg_overlay': layout['bg_overlay'],
        'primary_gold': primary_gold,
        'primary_black': primary_black,
        'title_y': layout['title_y'],
        'hook_y': layout['hook_y'],
        'problem_y': layout['problem_y'],
        'solution_y': layout['solution_y'],
        'cta_y': layout['cta_y']
    }

def create_vertical_video(hook, problem, solution, template_type, output_path):
    """Create vertical video with dynamic template layouts"""
    temp_dir = tempfile.mkdtemp()
    
    # Create voiceover
    voice_path = create_voiceover(hook, problem, solution, template_type)
    if voice_path is None:
        print("❌ Failed to create voiceover")
        return False

    # Get actual duration from the voiceover file
    duration = get_audio_duration(voice_path)
    print(f"Video duration: {duration:.2f} seconds")
    
    bg_image = get_background_image(hook, problem, template_type)
    
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

    # Get layout configuration
    layout = get_template_layout(template_type, hook, problem, solution)
    
    # Escape text for FFmpeg
    escaped_title = escape_text(layout['title'])
    escaped_hook = escape_text(layout['hook'])
    escaped_problem = escape_text(layout['problem'])
    escaped_solution = escape_text(layout['solution'])
    
    # Create a filter script file
    filter_script = os.path.join(temp_dir, "filter.txt")
    with open(filter_script, 'w') as f:
        # Base video filter with dark overlay
        f.write(f"[0:v]{video_filters},{layout['bg_overlay']}[v];")
        
        # Add text layers with gold and black theme
        f.write(f"""
        [v]drawtext=text='{escaped_title}':fontcolor={layout['primary_gold']}:fontsize=80:font=serif:box=1:boxcolor={layout['primary_black']}@0.7:boxborderw=10:x=(w-text_w)/2:y={layout['title_y']},
        drawtext=text='{escaped_hook}':fontcolor=white:fontsize=60:font=sans:box=1:boxcolor={layout['primary_gold']}@0.5:boxborderw=8:x=(w-text_w)/2:y={layout['hook_y']},
        drawtext=text='{escaped_problem}':fontcolor=white:fontsize=52:font=sans:box=1:boxcolor={layout['primary_black']}@0.6:boxborderw=6:x=(w-text_w)/2:y={layout['problem_y']},
        drawtext=text='{escaped_solution}':fontcolor={layout['primary_gold']}:fontsize=56:font=serif:box=1:boxcolor={layout['primary_black']}@0.8:boxborderw=8:x=(w-text_w)/2:y={layout['solution_y']},
        drawtext=text='Follow for more mom wisdom':fontcolor={layout['primary_gold']}:fontsize=38:font=sans:box=1:boxcolor={layout['primary_black']}@0.9:boxborderw=4:x=(w-text_w)/2:y={layout['cta_y']}
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

def generate_hashtags(problem, solution, template_type):
    """Generate relevant mom/parenting hashtags with template variations"""
    
    # Template-specific hashtag sets
    template_hashtags = {
        'question': ["#MomQuestions", "#ParentingQandA", "#AskAMom"],
        'confession': ["#MomConfessions", "#RealParenting", "#MomTruths"],
        'challenge': ["#ParentingChallenges", "#MomStruggles", "#OvercomingParenting"],
        'reveal': ["#ParentingReveals", "#MomSecretsRevealed", "#TruthAboutParenting"],
        'story': ["#MomStories", "#ParentingJourney", "#MyMomStory"],
        'secret': ["#MomSecrets", "#ParentingHacks", "#SecretMomTips"],
        'warning': ["#MomWarnings", "#ParentingAdvice", "#WhatNotToDo"],
        'promise': ["#MomPromises", "#ParentingSolutions", "#GuaranteedParenting"]
    }
    
    base_hashtags = [
        "#MomWisdom", "#ParentingTips", "#Motherhood", 
        "#RaisingKids", "#FamilyLife", "#MomLife",
        "#ParentingAdvice", "#MomHacks", "#PracticalParenting",
        "#ParentingWin", "#MomSupport", "#ToddlerTips"
    ]
    
    # Add template-specific hashtags
    hashtags = template_hashtags.get(template_type, []) + base_hashtags
    
    # Add problem-specific hashtags
    problem_lower = problem.lower()
    
    if any(word in problem_lower for word in ["bedtime", "sleep"]):
        hashtags.extend(["#BedtimeStruggles", "#SleepTraining", "#ToddlerSleep"])
    elif any(word in problem_lower for word in ["eat", "food", "meal"]):
        hashtags.extend(["#PickyEater", "#Mealtime", "#KidsNutrition"])
    elif any(word in problem_lower for word in ["tantrum", "meltdown", "behavior"]):
        hashtags.extend(["#Tantrums", "#ChildBehavior", "#GentleParenting"])
    elif any(word in problem_lower for word in ["sibling", "fight"]):
        hashtags.extend(["#SiblingRivalry", "#Siblings", "#FamilyDynamics"])
    
    return " ".join(hashtags[:15])

def post_to_facebook(video_path, hook, problem, solution, template_type):
    try:
        hashtags = generate_hashtags(problem, solution, template_type)
        
        # Template-specific emojis
        template_emojis = {
            'question': "🤔",
            'confession': "💬",
            'challenge': "⚡",
            'reveal': "🔍",
            'story': "📖",
            'secret': "🤫",
            'warning': "🚨",
            'promise': "🤝"
        }
        
        emoji = template_emojis.get(template_type, "🤱")
        
        with open(video_path, 'rb') as video_file:
            response = requests.post(
                f"https://graph.facebook.com/v19.0/{os.environ['FB_PAGE_ID']}/videos",
                params={
                    "access_token": os.environ["FB_PAGE_TOKEN"],
                    "description": f"{emoji} {hook}\n\n💡 PROBLEM: {problem}\n\n✅ SOLUTION: {solution}\n\n{hashtags}\n\n👇 Follow for daily mom wisdom!"
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
    print("=== Mom Wisdom Video Creator ===")
    print("Creating unique problem-solution videos with varied templates...")
    
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
    problem, solution, hook, template_type = generate_mom_issue_solution(post_history)
    
    if problem is None or solution is None or hook is None:
        print("❌ Could not generate a unique mom issue after multiple attempts")
        return
    
    print(f"\n🎭 TEMPLATE: {template_type.upper()}")
    print(f"🎯 HOOK: {hook}")
    print(f"💡 PROBLEM: {problem}")
    print(f"✅ SOLUTION: {solution}")

    video_path = f"mom_{template_type}_shorts.mp4"
    if create_vertical_video(hook, problem, solution, template_type, video_path):
        print(f"✅ {template_type.upper()} video created: {video_path}")
        
        # Add to post history
        post_history.add_post(problem, solution, hook, template_type, video_path)
        
        if all(key in os.environ for key in ["FB_PAGE_ID", "FB_PAGE_TOKEN"]):
            print("📤 Posting to Facebook Shorts...")
            if post_to_facebook(video_path, hook, problem, solution, template_type):
                print("✅ Post completed successfully!")
            else:
                print("❌ Failed to post to Facebook")
        else:
            print("ℹ️ Facebook credentials not found - video saved locally")

        # Save description with hashtags
        hashtags = generate_hashtags(problem, solution, template_type)
        with open("video_description.txt", "w") as f:
            f.write(f"🎭 {template_type.upper()} FORMAT\n\n")
            f.write(f"🎯 {hook}\n\n")
            f.write(f"💡 PROBLEM: {problem}\n\n")
            f.write(f"✅ SOLUTION: {solution}\n\n")
            f.write(f"{hashtags}\n\n")
            f.write("👇 Follow for daily mom wisdom!")
    else:
        print("❌ Failed to create video - skipping")

if __name__ == "__main__":
    main()