# english_learning_page_post.py
import os
import requests
import feedparser
from datetime import datetime, timedelta
from dotenv import load_dotenv
import re
import json
from bs4 import BeautifulSoup
import time
import random
from urllib.parse import urljoin

load_dotenv()

FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")
GEMINI = os.getenv("GEMINI_API_KEY")

# English language learning focused RSS feeds
ENGLISH_LEARNING_SOURCES = [
    "https://www.bbc.co.uk/learningenglish/english/feed",
    "https://learningenglish.voanews.com/api/zq$omekvi_v",
    "https://www.englishclub.com/efl/feed/",
    "https://www.esl-lab.com/feed/",
    "https://www.dailyesl.com/feed/",
    "https://www.englishpage.com/feed/",
    "https://www.usingenglish.com/feed/",
    "https://www.englishcentral.com/blog/feed/"
]

# Enhanced headers to avoid blocking
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# English learning focused writing styles
WRITING_STYLES = [
    {
        "name": "Grammar Guide",
        "tone": "educational and clear",
        "voice": "This grammar point helps learners understand...",
        "perspective": "explains English grammar rules and usage"
    },
    {
        "name": "Vocabulary Builder", 
        "tone": "informative and practical",
        "voice": "Learn these essential words and phrases...",
        "perspective": "focuses on vocabulary expansion and usage"
    },
    {
        "name": "Pronunciation Coach",
        "tone": "helpful and technical",
        "voice": "Master the sounds of English with this guide...",
        "perspective": "teaches pronunciation and speaking skills"
    },
    {
        "name": "Conversation Teacher",
        "tone": "practical and engaging",
        "voice": "Use these expressions in daily conversations...",
        "perspective": "focuses on practical speaking skills"
    },
    {
        "name": "Writing Instructor",
        "tone": "structured and educational",
        "voice": "Improve your writing with these techniques...",
        "perspective": "teaches writing skills and composition"
    }
]

# English learning style headlines
ENGLISH_LEARNING_HEADLINES = [
    "Learn English: {}",
    "English Lesson: {}",
    "Grammar Focus: {}",
    "Vocabulary: {}",
    "Speaking Practice: {}",
    "English Tips: {}",
    "Language Learning: {}",
    "English Skills: {}",
    "Study English: {}",
    "Practice English: {}"
]

def safe_feed_parse(url):
    """Safely parse RSS feed with error handling and retries"""
    try:
        print(f"📡 Parsing RSS feed: {url}")
        feed = feedparser.parse(url)
        
        if hasattr(feed, 'bozo') and feed.bozo and hasattr(feed.bozo_exception, 'getStatus'):
            status = feed.bozo_exception.getStatus()
            if status:
                print(f"⚠️ RSS feed returned status: {status}")
                return None
            
        if not feed.entries:
            print(f"⚠️ No entries found in RSS feed")
            return None
            
        print(f"✅ Found {len(feed.entries)} entries")
        return feed
        
    except Exception as e:
        print(f"❌ Error parsing RSS feed {url}: {e}")
        return None

def extract_learning_images(article_url, article_title):
    """Extract relevant learning images from article page - MAX 5 IMAGES"""
    images = []
    seen_urls = set()
    
    try:
        print(f"🔍 Scraping images from: {article_url}")
        response = requests.get(article_url, headers=REQUEST_HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get base URL for proper relative URL handling
        base_url = '/'.join(article_url.split('/')[:3])
        
        # Method 1: Look for Open Graph images
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            img_url = og_image['content']
            if validate_image_url(img_url) and img_url not in seen_urls:
                # Handle relative OG image URLs
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/'):
                    img_url = base_url + img_url
                elif not img_url.startswith('http'):
                    img_url = urljoin(article_url, img_url)
                    
                if is_relevant_learning_image(img_url, article_title):
                    images.append({'url': img_url, 'priority': 10})
                    seen_urls.add(img_url)
                    print(f"  📸 Found relevant OG image: {img_url}")
        
        # Method 2: Look for Twitter card images
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        if twitter_image and twitter_image.get('content'):
            img_url = twitter_image['content']
            if validate_image_url(img_url) and img_url not in seen_urls:
                # Handle relative Twitter image URLs
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/'):
                    img_url = base_url + img_url
                elif not img_url.startswith('http'):
                    img_url = urljoin(article_url, img_url)
                    
                if is_relevant_learning_image(img_url, article_title):
                    images.append({'url': img_url, 'priority': 9})
                    seen_urls.add(img_url)
                    print(f"  📸 Found relevant Twitter image: {img_url}")
        
        # Method 3: Look for article images with strict learning relevance filtering
        image_selectors = [
            'article img',
            '.content img',
            '.entry-content img',
            '.post-content img',
            'main img',
            '[class*="featured"] img',
            '[class*="hero"] img',
            '[class*="article-image"] img',
            '.lesson-image img',
            '.educational-img img',
            '.learning-img img',
            '.grammar-image img',
            '.vocabulary-img img'
        ]
        
        for selector in image_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    # Stop if we already have 5 images
                    if len(images) >= 5:
                        break
                        
                    img_src = element.get('src') or element.get('data-src') or element.get('data-lazy-src')
                    if img_src:
                        # Handle ALL relative URLs properly
                        if img_src.startswith('//'):
                            img_src = 'https:' + img_src
                        elif img_src.startswith('/'):
                            img_src = base_url + img_src
                        elif not img_src.startswith('http'):
                            img_src = urljoin(article_url, img_src)
                        
                        if (validate_image_url(img_src) and 
                            img_src not in seen_urls and 
                            not is_duplicate_image(img_src, seen_urls) and
                            is_relevant_learning_image(img_src, article_title)):
                            
                            # Skip very small images (likely icons)
                            width = element.get('width')
                            height = element.get('height')
                            if width and height:
                                try:
                                    if int(width) < 200 or int(height) < 200:
                                        continue
                                except:
                                    pass
                            
                            # Check alt text for learning relevance
                            alt_text = element.get('alt', '').lower()
                            
                            # Skip generic/boring images
                            skip_indicators = ['icon', 'logo', 'button', 'spacer', 'border', 'arrow', 'avatar', 'profile', 'author', 'writer']
                            if any(indicator in alt_text for indicator in skip_indicators):
                                continue
                            
                            # Calculate priority based on relevance to learning topics
                            priority = 5
                            if any(word in alt_text for word in ['grammar', 'vocabulary', 'pronunciation', 'lesson', 'exercise']):
                                priority = 9
                            if any(word in alt_text for word in ['learning', 'education', 'study', 'teach', 'teacher']):
                                priority = 8
                            if any(word in alt_text for word in ['english', 'language', 'speaking', 'writing', 'reading']):
                                priority = 7
                            if any(word in alt_text for word in ['classroom', 'student', 'learn', 'practice', 'skill']):
                                priority = 6
                            
                            images.append({'url': img_src, 'priority': priority})
                            seen_urls.add(img_src)
                            print(f"  📸 Found relevant learning image: {img_src} (priority: {priority})")
                                
            except Exception as e:
                continue
        
        # Remove duplicates by URL pattern
        unique_images = []
        seen_patterns = set()
        
        for img in images:
            url = img['url']
            # Create a pattern to identify similar images
            pattern = re.sub(r'-\d+x\d+', '', url)  # Remove size dimensions
            pattern = re.sub(r'\?.*$', '', pattern)  # Remove query parameters
            pattern = re.sub(r'-\d+\.', '.', pattern)  # Remove numbered suffixes
            
            if pattern not in seen_patterns:
                unique_images.append(img)
                seen_patterns.add(pattern)
        
        # Sort by priority and return MAX 5 relevant images
        sorted_images = sorted(unique_images, key=lambda x: x['priority'], reverse=True)
        image_urls = [img['url'] for img in sorted_images[:5]]  # MAX 5 IMAGES
        
        print(f"✅ Found {len(image_urls)} relevant learning images (max 5)")
        return image_urls
        
    except Exception as e:
        print(f"❌ Error scraping images from {article_url}: {e}")
        return []

def is_relevant_learning_image(img_url, article_title):
    """Check if image is relevant to English learning content"""
    # Skip images that are clearly not related to education
    skip_patterns = [
        'avatar', 'profile', 'author', 'writer', 'logo', 
        'icon', 'advertisement', 'ad-', 'sponsor', 'author',
        'headshot', 'team', 'staff', 'social-media'
    ]
    
    if any(pattern in img_url.lower() for pattern in skip_patterns):
        return False
    
    # Check if image filename suggests relevance to learning topics
    learning_indicators = [
        'grammar', 'vocabulary', 'pronunciation', 'lesson', 'exercise',
        'learning', 'education', 'study', 'teach', 'teacher',
        'english', 'language', 'speaking', 'writing', 'reading',
        'classroom', 'student', 'learn', 'practice', 'skill',
        'word', 'sentence', 'phrase', 'expression', 'dialogue'
    ]
    
    # Check if image URL contains learning-related words
    if any(indicator in img_url.lower() for indicator in learning_indicators):
        return True
    
    # Also check article title for context
    if any(indicator in article_title.lower() for indicator in learning_indicators):
        return True
    
    return True  # Default to True if we can't determine

def is_duplicate_image(url, seen_urls):
    """Check if image is likely a duplicate"""
    # Remove common variations that don't change the actual image
    base_url = re.sub(r'-\d+x\d+', '', url)  # Remove size dimensions
    base_url = re.sub(r'\?.*$', '', base_url)  # Remove query parameters
    
    for seen_url in seen_urls:
        seen_base = re.sub(r'-\d+x\d+', '', seen_url)
        seen_base = re.sub(r'\?.*$', '', seen_base)
        if base_url == seen_base:
            return True
    return False

def validate_image_url(url):
    """Validate if URL is likely an image"""
    if not url or not isinstance(url, str):
        return False
    image_patterns = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
    return any(pattern in url.lower() for pattern in image_patterns)

def translate_to_arabic(text):
    """Translate English text to formal Arabic using Gemini"""
    try:
        print("🔄 Translating content to formal Arabic...")
        
        translation_prompt = f"""
        Translate the following English language learning content into formal Arabic (الفصحى). 
        The content is for Arabic speakers learning English, so maintain educational tone.
        
        IMPORTANT TRANSLATION RULES:
        1. Use formal Modern Standard Arabic (الفصحى)
        2. Keep educational and professional tone
        3. Maintain all language learning concepts accurately
        4. Preserve the structure and meaning
        5. Use proper Arabic educational terminology
        6. Keep hashtags in English but translate their meaning in context
        
        English content to translate:
        {text}
        
        Provide only the Arabic translation without any additional text or explanations.
        """
        
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent",
            params={"key": GEMINI},
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": translation_prompt}]}]},
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            if "candidates" in data and data["candidates"]:
                arabic_content = data["candidates"][0]["content"]["parts"][0]["text"]
                print("✅ Successfully translated to Arabic")
                return arabic_content.strip()
            else:
                print(f"❌ No valid candidates found in translation response")
                raise Exception("No valid translation candidates")
        else:
            print(f"❌ Translation API Status {response.status_code}: {response.text}")
            raise Exception(f"Translation API error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error in translation: {e}")
        # Return original text if translation fails
        return text

def fb_post_with_images(message, image_urls):
    """Post to Facebook with any number of relevant images - MAX 5 IMAGES"""
    if not image_urls:
        return fb_post_text_only(message)
    
    # Apply MAX 5 images limit
    images_to_post = image_urls[:5]
    print(f"📤 Posting with {len(images_to_post)} relevant images (max 5)")
    
    # Try carousel for 2+ images, single image for 1 image
    if len(images_to_post) >= 2:
        result = fb_post_carousel(message, images_to_post)
        if result:
            return result
    
    # Single image fallback
    if len(images_to_post) >= 1:
        result = fb_post_single_photo(message, images_to_post[0])
        if result:
            return result
    
    # Final fallback to text
    return fb_post_text_only(message)

def fb_post_carousel(message, image_urls):
    """Post multiple images to Facebook as a carousel - MAX 5 IMAGES"""
    try:
        if not image_urls or len(image_urls) < 2:
            return None
        
        # Apply MAX 5 images limit for carousel
        images_to_post = image_urls[:5]
        print(f"📤 Posting carousel with {len(images_to_post)} images")
        
        # First, upload each image and get their IDs
        photo_ids = []
        for i, image_url in enumerate(images_to_post):
            try:
                print(f"  📸 Uploading image {i+1}")
                post_url = f"https://graph.facebook.com/v18.0/{FB_PAGE_ID}/photos"
                params = {
                    "access_token": FB_PAGE_TOKEN,
                    "url": image_url,
                    "published": "false"
                }
                
                response = requests.post(post_url, params=params, timeout=30)
                result = response.json()
                
                if 'id' in result:
                    photo_ids.append(result['id'])
                    print(f"  ✅ Image {i+1} uploaded successfully")
                else:
                    print(f"  ❌ Failed to upload image {i+1}: {result}")
                    
            except Exception as e:
                print(f"  ❌ Error uploading image {i+1}: {e}")
                continue
        
        if len(photo_ids) < 2:
            print("❌ Not enough images uploaded successfully")
            return None
        
        # Now create the carousel post with attached media
        post_url = f"https://graph.facebook.com/v18.0/{FB_PAGE_ID}/feed"
        data = {
            "message": message,
            "access_token": FB_PAGE_TOKEN,
            "attached_media": json.dumps([{"media_fbid": photo_id} for photo_id in photo_ids])
        }
        
        response = requests.post(post_url, data=data, timeout=30)
        result = response.json()
        
        if 'id' in result:
            print(f"✅ Carousel post successful with {len(photo_ids)} images!")
            return result
        else:
            print(f"❌ Carousel post failed: {result}")
            return None
            
    except Exception as e:
        print(f"❌ Error in carousel post: {e}")
        return None

def fb_post_single_photo(message, image_url):
    """Post to Facebook with a single image using direct URL"""
    try:
        if not image_url:
            return fb_post_text_only(message)
            
        print(f"📤 Posting with single image")
        
        post_url = f"https://graph.facebook.com/v18.0/{FB_PAGE_ID}/photos"
        params = {
            "access_token": FB_PAGE_TOKEN,
            "url": image_url,
            "message": message,
            "published": "true"
        }
        
        response = requests.post(post_url, params=params, timeout=30)
        result = response.json()
        
        if 'id' in result:
            print("✅ Single photo post successful!")
            return result
        else:
            print(f"❌ Single photo post failed: {result}")
            return fb_post_text_only(message)
            
    except Exception as e:
        print(f"❌ Error in single photo post: {e}")
        return fb_post_text_only(message)

def fb_post_text_only(message):
    """Post text-only message to Facebook"""
    try:
        print("📝 Posting text-only message")
        post_url = f"https://graph.facebook.com/v18.0/{FB_PAGE_ID}/feed"
        data = {
            "message": message,
            "access_token": FB_PAGE_TOKEN
        }
        response = requests.post(post_url, data=data, timeout=10)
        result = response.json()
        print("✅ Text-only post successful!")
        return result
    except Exception as e:
        print(f"❌ Text-only post failed: {e}")
        return None

def get_complete_article_content(entry_url):
    """Fetch complete article content from the actual page"""
    try:
        print(f"🌐 Fetching complete article from: {entry_url}")
        response = requests.get(entry_url, headers=REQUEST_HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form']):
            element.decompose()
        
        # Try to find article content using multiple selectors
        content_selectors = [
            'article',
            '[class*="content"]',
            '[class*="article"]',
            '[class*="post-content"]',
            '.entry-content',
            '.post-content',
            '.article-content',
            '.story-content',
            '.main-content',
            '.body-content',
            '.lesson-content',
            '.educational-content'
        ]
        
        content = ""
        for selector in content_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True, separator='\n')
                    if len(text) > 200:
                        content = text
                        print(f"✅ Found content using selector: {selector}")
                        break
                if content:
                    break
            except Exception as e:
                continue
        
        if not content:
            # Fallback: get body text but exclude navigation etc.
            body = soup.find('body')
            if body:
                # Remove common non-content elements
                for element in body.select('nav, header, footer, aside, .menu, .navigation'):
                    element.decompose()
                content = body.get_text(strip=True, separator='\n')
                print("⚠️ Using fallback body text")
        
        # Clean up excessive whitespace
        content = re.sub(r'\n\s*\n', '\n\n', content)
        
        return content[:4000]
            
    except Exception as e:
        print(f"❌ Error fetching complete content: {e}")
        return None

def clean_facebook_text(text):
    """Clean and format text for Facebook with better readability"""
    # Remove all markdown formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)
    text = re.sub(r'[`~]', '', text)
    text = re.sub(r'#{2,}', '', text)
    
    # Ensure proper spacing and formatting
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip()
    
    return text

def is_english_learning_entry(entry):
    """Check if an entry is about English language learning ONLY"""
    if not entry:
        return False
    
    title = getattr(entry, 'title', '').lower()
    link = getattr(entry, 'link', '')
    summary = getattr(entry, 'summary', '').lower() if hasattr(entry, 'summary') else ''
    
    # Skip if no title or link
    if not title or not link:
        return False
    
    # STRICTLY EXCLUDE unwanted content
    exclude_indicators = [
        'politics', 'political', 'election', 'government',
        'war', 'military', 'defense', 'security',
        'crime', 'arrest', 'investigation', 'police', 'court',
        'blog', 'personal', 'diary', 'my experience', 'opinion',
        'economy', 'stock', 'market', 'finance', 'business',
        'tech', 'gadget', 'device', 'innovation', 'robot',
        'shopping', 'fashion', 'beauty', 'cosmetics',
        'travel', 'tourist', 'destination', 'hotel', 'flight'  # Exclude travel content
    ]
    
    if any(exclude_word in title for exclude_word in exclude_indicators):
        return False
    
    # INCLUDE only English learning content
    learning_indicators = [
        'english', 'grammar', 'vocabulary', 'pronunciation', 'speaking',
        'writing', 'reading', 'listening', 'lesson', 'exercise',
        'learn', 'study', 'practice', 'skill', 'language',
        'verb', 'tense', 'sentence', 'phrase', 'expression',
        'fluent', 'conversation', 'dialogue', 'comprehension',
        'test', 'exam', 'toefl', 'ielts', 'course', 'class'
    ]
    
    # Check title and summary for learning indicators
    content_to_check = title + " " + summary
    if any(indicator in content_to_check for indicator in learning_indicators):
        return True
    
    return False

def get_single_english_article():
    """Get one complete English learning article"""
    # Shuffle feeds to distribute load
    shuffled_feeds = ENGLISH_LEARNING_SOURCES.copy()
    random.shuffle(shuffled_feeds)
    
    for rss_url in shuffled_feeds:
        try:
            feed = safe_feed_parse(rss_url)
            if not feed or not feed.entries:
                continue
                
            # Try multiple entries from this feed
            for entry in feed.entries[:15]:
                if not is_english_learning_entry(entry):
                    continue
                
                title = getattr(entry, 'title', '').strip()
                link = getattr(entry, 'link', '')
                
                print(f"🎯 Found potential English learning article: {title}")
                
                # Get complete article content
                full_content = get_complete_article_content(link)
                if full_content and len(full_content) > 200:
                    # Extract relevant learning images from the article page - MAX 5
                    images = extract_learning_images(link, title)
                    
                    return {
                        'title': title,
                        'content': full_content,
                        'link': link,
                        'source': rss_url.split('//')[1].split('/')[0],
                        'images': images
                    }
                else:
                    print(f"⚠️ Insufficient content for: {title}")
                    
        except Exception as e:
            print(f"❌ Error processing RSS feed {rss_url}: {e}")
            continue
    
    return None

def generate_learning_headline(title):
    """Generate an English learning-style headline"""
    # Clean the title
    clean_title = re.sub(r'\s*[-:|]\s*.*$', '', title)
    clean_title = clean_title.strip()
    
    # Shorten very long titles
    if len(clean_title) > 60:
        words = clean_title.split()
        if len(words) > 8:
            clean_title = ' '.join(words[:8]) + '...'
    
    # Pick a learning headline template
    headline_template = random.choice(ENGLISH_LEARNING_HEADLINES)
    return headline_template.format(clean_title)

def get_ai_english_lesson():
    """Generate English learning content using AI"""
    writing_style = random.choice(WRITING_STYLES)
    
    print(f"🎭 Selected writing style: {writing_style['name']}")
    
    prompt = f"""
    Write an engaging, third-person educational post about English language learning. Focus exclusively on teaching English concepts.

    WRITING STYLE: {writing_style['name']} - {writing_style['tone']}
    VOICE: {writing_style['voice']}

    CRITICAL RULES:
    - WRITE IN THIRD PERSON ONLY (no "I", "my", "we", "our")
    - Focus ONLY on English language learning and teaching
    - Include clear explanations and examples
    - Provide practical learning tips and exercises
    - No markdown formatting
    - Include relevant language learning hashtags

    Content focus:
    - Grammar rules and explanations
    - Vocabulary building techniques
    - Pronunciation guides
    - Speaking and conversation practice
    - Writing skills improvement
    - Reading comprehension strategies
    - Common mistakes and corrections

    Structure:
    [Learning headline]

    [Clear explanation of the English concept]

    [Practical examples and usage]

    [Learning tips and practice exercises]

    [Common mistakes to avoid]

    [Encouragement for continued learning]

    [Relevant language learning hashtags]

    Make it helpful for Arabic speakers learning English!
    """

    try:
        print("🤖 Generating AI English learning content...")
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent",
            params={"key": GEMINI},
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if "candidates" in data and data["candidates"]:
                ai_content = data["candidates"][0]["content"]["parts"][0]["text"]
                
                # Clean the content
                cleaned_content = clean_facebook_text(ai_content)
                print("✅ Successfully generated AI English learning content")
                return cleaned_content
            else:
                print(f"❌ No valid candidates found in AI response")
                raise Exception("No valid candidates")
        else:
            print(f"❌ API Status {response.status_code}: {response.text}")
            raise Exception(f"API error: {response.status_code}")

    except Exception as e:
        print(f"❌ Error generating AI English lesson: {e}")
        # Fallback content with learning focus
        fallback_topics = [
            "Learn English: Common Grammar Mistakes\n\nMany English learners struggle with similar grammar challenges. Understanding these common errors can significantly improve your language accuracy and confidence in speaking and writing.\n\nExample: The difference between 'much' and 'many' - use 'much' for uncountable nouns (much water) and 'many' for countable nouns (many books). Practice by categorizing everyday items around you.\n\nWhat grammar topics do you find most challenging?\n\n#EnglishGrammar #LearnEnglish #LanguageLearning #EnglishTips",
            
            "Vocabulary: Essential English Phrases\n\nExpanding your vocabulary with useful phrases helps you sound more natural in conversations. Focus on learning complete expressions rather than individual words for better fluency.\n\nPractice these: 'How have you been?' for asking about someone's recent life, and 'What do you think?' for seeking opinions. Try using each phrase in three different sentences today.\n\nWhich English phrases do you use most often?\n\n#EnglishVocabulary #SpeakingEnglish #LearnEnglish #LanguageSkills",
            
            "Pronunciation: Mastering English Sounds\n\nClear pronunciation makes communication more effective. Many English sounds don't exist in other languages, so focused practice is essential for improvement.\n\nTip: Practice the 'th' sound by placing your tongue between your teeth. Words like 'think', 'this', and 'mother' are great for practice. Record yourself and compare with native speakers.\n\nWhat English sounds are most difficult for you?\n\n#EnglishPronunciation #SpeakingPractice #LearnEnglish #LanguageLearning"
        ]
        return random.choice(fallback_topics)

def generate_english_learning_post():
    """Generate ONE English learning post with relevant images - MAX 5 IMAGES, translated to Arabic"""
    print("📚 Looking for English learning content...")
    
    article = get_single_english_article()
    
    if article:
        print(f"📝 Processing English learning article: {article['title']}")
        print(f"📊 Content length: {len(article['content'])} characters")
        print(f"🖼️ Relevant learning images found: {len(article['images'])} (max 5)")
        
        writing_style = random.choice(WRITING_STYLES)
        
        print(f"🎭 Using writing style: {writing_style['name']}")

        prompt = f"""
        Write an engaging, third-person educational post about this English language learning topic. Focus exclusively on teaching English to Arabic speakers.

        WRITING STYLE: {writing_style['name']} - {writing_style['tone']}
        VOICE: {writing_style['voice']}

        ARTICLE TITLE: {article['title']}
        ARTICLE CONTENT: {article['content'][:3500]}
        SOURCE: {article['source']}

        CRITICAL RULES:
        - WRITE IN THIRD PERSON ONLY (no "I", "my", "we", "our")
        - Focus ONLY on English language teaching and learning
        - Provide clear explanations and practical examples
        - Include learning tips and practice exercises
        - No markdown formatting
        - Include relevant language learning hashtags

        Structure:
        [Learning headline]

        [Clear explanation of the English concept]

        [Practical examples and usage in context]

        [Step-by-step learning tips]

        [Practice exercises or challenges]

        [Common mistakes and how to avoid them]

        [Encouragement for continued practice]

        [Relevant English learning hashtags]

        Make it practical and helpful for Arabic speakers learning English!
        """

        try:
            print("🤖 Generating English learning post with Gemini...")
            response = requests.post(
                "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent",
                params={"key": GEMINI},
                headers={"Content-Type": "application/json"},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                if "candidates" in data and data["candidates"]:
                    english_post = data["candidates"][0]["content"]["parts"][0]["text"]
                    
                    cleaned_post = clean_facebook_text(english_post)
                    print("✅ Successfully generated English learning post")
                    
                    # Translate to formal Arabic
                    arabic_post = translate_to_arabic(cleaned_post)
                    
                    # Post with any number of relevant learning images - MAX 5
                    fb_post_with_images(arabic_post, article['images'])
                    return
                else:
                    print(f"❌ No valid candidates found in Gemini response")
                    raise Exception("No valid candidates")
            else:
                print(f"❌ API Status {response.status_code}: {response.text}")
                raise Exception(f"API error: {response.status_code}")

        except Exception as e:
            print(f"❌ Error with Gemini API: {e}")
            # Fallback with learning headline
            print("🔄 Using learning fallback format...")
            headline = generate_learning_headline(article['title'])
            english_fallback = (
                f"{headline}\n\n"
                f"This English language concept helps learners improve their communication skills. "
                f"Understanding this topic can make speaking and writing in English more natural and accurate.\n\n"
                f"Practice is essential for mastering English. Try using this concept in your daily conversations "
                f"or writing exercises to build confidence and fluency over time.\n\n"
                f"What English skills are you currently working to improve?\n\n"
                f"#LearnEnglish #EnglishLearning #LanguageSkills #StudyEnglish"
            )
            
            # Translate to Arabic
            arabic_fallback = translate_to_arabic(english_fallback)
            fb_post_with_images(arabic_fallback, article['images'])
    else:
        print("❌ No English learning articles found. Generating AI English lesson...")
        english_content = get_ai_english_lesson()
        
        # Translate to Arabic
        arabic_content = translate_to_arabic(english_content)
        fb_post_text_only(arabic_content)

if __name__ == '__main__':
    generate_english_learning_post()