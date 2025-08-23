import os
import google.generativeai as genai
import random
import tempfile
import subprocess
import re
import requests
import textwrap
import asyncio
import edge_tts

def generate_simple_word():
    """Generate one simple English word with example - ensure randomness"""
    # List of diverse word categories to ensure variety
    word_categories = [
        "common household items", "food and drinks", "animals", "transportation",
        "clothing", "weather", "emotions", "school supplies", "body parts",
        "colors", "jobs", "sports", "technology", "nature", "time concepts"
    ]
    
    category = random.choice(word_categories)
    
    prompt = f"""Generate ONE simple English word related to {category} with a clear example sentence.
    Return ONLY in this exact format: word .| example
    Example: car .| I have a red car.
    
    Rules:
    - No contractions (use 'do not' instead of 'don't')
    - No special characters or apostrophes
    - Simple, common word suitable for beginners
    - Clear, practical example sentence
    - Include a period after the word
    - Choose a word that hasn't been used recently
    - Make it educational and useful for language learners"""
    
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    
    try:
        if '|' in response.text:
            word_part, example = response.text.strip().split('|', 1)
            word = word_part.replace('.', '').strip()
            return word.strip(), example.strip()
    except:
        pass
    
    # Expanded fallbacks with more variety
    fallbacks = [
        ("car", "I have a red car"),
        ("book", "I read a good book every night"),
        ("house", "This is my beautiful house"),
        ("school", "I go to school every day"),
        ("water", "I drink water every morning"),
        ("computer", "I use my computer for work"),
        ("phone", "My phone is very important"),
        ("friend", "I have a good friend"),
        ("family", "I love my family very much"),
        ("food", "I enjoy eating delicious food"),
        ("music", "I listen to music every day"),
        ("sun", "The sun is very bright today"),
        ("rain", "I do not like walking in the rain"),
        ("time", "What time is it now"),
        ("work", "I go to work every morning"),
        ("dog", "My dog likes to play in the park"),
        ("cat", "The cat sleeps on the sofa"),
        ("tree", "There is a big tree in my garden"),
        ("chair", "Please sit on this comfortable chair"),
        ("table", "We eat dinner at the table"),
        ("window", "I look out the window every morning"),
        ("door", "Please close the door when you leave"),
        ("pen", "I write with a blue pen"),
        ("paper", "I draw pictures on white paper"),
        ("teacher", "My teacher helps me learn English"),
        ("student", "I am a good student in class")
    ]
    return random.choice(fallbacks)

def get_background_image():
    """Get background image with diverse keywords"""
    local_images = []
    if os.path.exists('backgrounds'):
        local_images = [f for f in os.listdir('backgrounds') if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if local_images:
        return os.path.join('backgrounds', random.choice(local_images))
    
    if "PIXABAY_KEY" in os.environ:
        try:
            image_keywords = ["flowers", "nature", "landscape", "mountains", "sky", 
                            "books", "abstract", "education", "learning", "classroom",
                            "minimal", "gradient", "pattern", "texture", "geometric"]
            keyword = random.choice(image_keywords)
            response = requests.get(
                "https://pixabay.com/api/",
                params={
                    "key": os.environ["PIXABAY_KEY"],
                    "q": keyword,
                    "image_type": "photo",
                    "orientation": "vertical",
                    "per_page": 50,
                    "safesearch": "true"
                }
            )
            if response.status_code == 200:
                images = response.json().get('hits', [])
                if images:
                    image_url = random.choice(images)['largeImageURL']
                    temp_dir = tempfile.mkdtemp()
                    image_path = os.path.join(temp_dir, "background.jpg")
                    img_response = requests.get(image_url)
                    if img_response.status_code == 200:
                        with open(image_path, 'wb') as f:
                            f.write(img_response.content)
                        return image_path
        except:
            pass
    return None

async def edge_tts_generate(text, path, voice):
    """Generate speech using Edge TTS with specified voice"""
    tts = edge_tts.Communicate(text, voice)
    await tts.save(path)

def get_random_voice():
    """Get a random voice from available Edge TTS voices"""
    voices = [
        "en-US-AriaNeural",
        "en-US-JennyNeural",
        "en-US-GuyNeural",
        "en-GB-SoniaNeural",
        "en-GB-RyanNeural",
        "en-AU-NatashaNeural",
        "en-AU-WilliamNeural",
        "en-CA-ClaraNeural",
        "en-CA-LiamNeural",
        "en-IN-NeerjaNeural",
        "en-IN-PrabhatNeural",
        "en-IE-EmilyNeural",
        "en-IE-ConnorNeural",
        "en-NZ-MollyNeural",
        "en-NZ-MitchellNeural"
    ]
    return random.choice(voices)

def create_voiceover(word, example, output_path):
    """Create voiceover using Edge TTS with random voice and pauses"""
    temp_dir = tempfile.mkdtemp()
    
    # Get a different random voice for each generation
    voice = get_random_voice()
    print(f"Using voice: {voice}")
    
    parts = [
        ("Repeat after me.", 2),
        (f"{word}.", 3),
        (f"Again. {word}.", 3),
        (f"One more time. {word}.", 3),
        ("Here's an example.", 2),
        (f"{example}.", 3),
        ("Like and follow for more!", 0),
    ]
    files = []
    for i, (text, pause) in enumerate(parts, start=1):
        file_path = os.path.join(temp_dir, f"part{i}.mp3")
        asyncio.run(edge_tts_generate(text, file_path, voice))
        files.append((file_path, pause))

    concat_file = os.path.join(temp_dir, "concat.txt")
    with open(concat_file, 'w') as f:
        for i, (file, pause) in enumerate(files):
            f.write(f"file '{file}'\n")
            if pause > 0:
                f.write(f"duration {pause}\n")

    ffmpeg_cmd = [
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
        '-i', concat_file, '-c', 'copy', output_path
    ]
    subprocess.run(ffmpeg_cmd, check=True)
    return True

def create_beautiful_video(word, example, output_path):
    temp_dir = tempfile.mkdtemp()
    voice_path = os.path.join(temp_dir, "voiceover.mp3")
    create_voiceover(word, example, voice_path)

    bg_image = get_background_image()
    if bg_image and os.path.exists(bg_image):
        input_source = ['-loop', '1', '-i', bg_image]
        scale_filter = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
        duration = 22
    else:
        colors = ["0x3498db", "0xe74c3c", "0x2ecc71", "0xf39c12", "0x9b59b6", 
                 "0x1abc9c", "0xd35400", "0x34495e", "0x16a085", "0x8e44ad"]
        bg_color = random.choice(colors)
        input_source = ['-f', 'lavfi', '-i', f'color=c={bg_color}:s=1080x1920:d=22']
        scale_filter = "null"
        duration = 22

    ffmpeg_cmd = [
        'ffmpeg', '-y',
        *input_source,
        '-i', voice_path,
        '-filter_complex',
        f"[0:v]{scale_filter},"
        f"drawtext=text='ENGLISH WORD PRACTICE':fontcolor=white:fontsize=60:box=1:boxcolor=black@0.4:boxborderw=6:x=(w-text_w)/2:y=80,"
        f"drawtext=text='Repeat After Me':fontcolor=white:fontsize=45:box=1:boxcolor=black@0.4:boxborderw=4:x=(w-text_w)/2:y=160,"
        f"drawtext=text='word:':fontcolor=white:fontsize=50:x=100:y=350,"
        f"drawtext=text='{word}':fontcolor=white:fontsize=100:box=1:boxcolor=black@0.5:boxborderw=10:x=(w-text_w)/2:y=450,"
        f"drawtext=text='example:':fontcolor=white:fontsize=50:x=100:y=650,"
        f"drawtext=text='{example}':fontcolor=white:fontsize=50:box=1:boxcolor=black@0.5:boxborderw=8:x=(w-text_w)/2:y=750,"
        f"drawtext=text='Like and follow for more lessons!':fontcolor=white:fontsize=40:box=1:boxcolor=black@0.4:boxborderw=5:x=(w-text_w)/2:y=950",
        '-c:v', 'libx264', '-c:a', 'aac', '-t', str(duration),
        '-shortest', output_path
    ]
    subprocess.run(ffmpeg_cmd, check=True)
    return True

def post_to_facebook(video_path, word, example):
    try:
        with open(video_path, 'rb') as video_file:
            response = requests.post(
                f"https://graph.facebook.com/v19.0/{os.environ['FB_PAGE_ID']}/videos",
                params={
                    "access_token": os.environ["FB_PAGE_TOKEN"],
                    "description": f"📚 English Word Practice: {word}\n\nword: {word}\nexample: {example}\n\nLike and follow for more lessons! 🎯\n\n#LearnEnglish #EnglishVocabulary #WordPractice #ESL #LanguageLearning"
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
    print("=== English Word Practice Video Creator ===")
    word, example = generate_simple_word()
    print(f"Word: {word}")
    print(f"Example: {example}")

    video_path = "beautiful_english_video.mp4"
    if create_beautiful_video(word, example, video_path):
        print(f"✅ Video created: {video_path}")
        if all(key in os.environ for key in ["FB_PAGE_ID", "FB_PAGE_TOKEN"]):
            print("📤 Posting to Facebook...")
            post_to_facebook(video_path, word, example)
        else:
            print("ℹ️ Facebook credentials not found - video saved locally")

        with open("video_description.txt", "w") as f:
            f.write(f"📚 English Word Practice: {word}\n\n")
            f.write(f"word: {word}\n")
            f.write(f"example: {example}\n\n")
            f.write("Like and follow for more lessons! 🎯\n\n")
            f.write("#LearnEnglish #EnglishVocabulary #WordPractice #ESL #LanguageLearning")

if __name__ == "__main__":
    main()