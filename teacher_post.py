import random
from common import ask_ai, post_to_facebook, clean_ai_output, get_pixabay_image_url

# Image Keywords - Nature themes
PIXABAY_KEYWORDS = [
    "flowers", "landscape", "mountains", "forest", "ocean",
    "sunset", "animals", "wildlife", "butterfly", "waterfall",
    "garden", "spring", "autumn", "winter", "summer"
]

# Lesson Topics - 65 English learning topics for Arabic speakers
LESSON_TOPICS = [
    # Grammar Tips (25 topics)
    "🔍 Present Perfect vs Past Simple - Key Differences",
    "💡 All Conditional Types Explained Simply",
    "🛠️ How to Use Modal Verbs Correctly",
    "🎭 Passive Voice Made Easy",
    "⚠️ Common Article Mistakes and Fixes",
    "📝 Reported Speech - Rules and Examples",
    "🔄 Essential Phrasal Verbs You Need",
    "⏳ Future Tenses Comparison (Will/Going to/Present Continuous)",
    "🔤 Countable vs Uncountable Nouns",
    "🤔 Question Tags - How to Form Them Correctly",
    "📌 Relative Clauses (Who/Which/That/Where)",
    "✨ Gerunds vs Infinitives - Common Verbs",
    "🧩 Prepositions of Time and Place",
    "🆚 Comparative and Superlative Adjectives",
    "🔗 Linking Words for Better Writing",
    "📊 Quantifiers (Some/Any/Much/Many)",
    "🔄 Subject-Verb Agreement Rules",
    "🎯 Demonstratives (This/That/These/Those)",
    "📌 Possessive Forms ('s vs of)",
    "🔄 Word Order in English Questions",
    "⏰ Time Expressions with Different Tenses",
    "🔤 Irregular Plural Nouns",
    "🔄 So vs Such - When to Use Each",
    "🎯 Either/Neither - Correct Usage",
    "📌 Adverbs of Frequency Placement",

    # Vocabulary Tips (25 topics)
    "📚 5 Advanced Academic Words You Need",
    "💼 Essential Business English Phrases",
    "✍️ Must-Know IELTS Vocabulary",
    "🔤 Alternatives to Overused Words",
    "🤝 Common Verb Collocations",
    "🏥 Medical and Health Vocabulary",
    "💻 Technology Terms Everyone Should Know",
    "✈️ Travel and Airport Vocabulary",
    "🍳 Cooking and Kitchen Terms",
    "🛒 Shopping and Money Expressions",
    "🎓 University and Education Terms",
    "⚽ Sports and Fitness Vocabulary",
    "🎨 Art and Culture Related Words",
    "🌳 Environment and Ecology Terms",
    "👔 Job Interview Vocabulary",
    "📱 Social Media and Internet Slang",
    "🏠 House and Furniture Vocabulary",
    "🚗 Car and Driving Terms",
    "👗 Clothing and Fashion Words",
    "🐾 Animal Related Vocabulary",
    "🌦️ Weather Expressions",
    "💑 Relationship and Dating Terms",
    "🎭 Theater and Performance Words",
    "📉 Business and Finance Vocabulary",
    "👶 Baby and Parenting Terms",
    "⚖️ Law and Legal Vocabulary",

    # Pronunciation Focus (15 topics)
    "🔊 English Sounds Arabs Find Difficult",
    "🗣️ Mastering the TH Sound",
    "🎙️ R vs L Pronunciation Guide",
    "👄 Commonly Mispronounced Words",
    "🔈 Silent Letters in English",
    "🎵 Word Stress Patterns",
    "📢 Sentence Intonation Rules",
    "👂 Homophones (Same Sound, Different Meaning)",
    "💬 Linking Sounds in Natural Speech",
    "📖 -ED Ending Pronunciation Rules",
    "🔊 V vs W Sound Difference",
    "🗣️ P vs B Pronunciation Tips",
    "🎙️ Schwa Sound - The Most Common Vowel",
    "👄 Contractions in Spoken English",
    "🔈 Difficult Consonant Clusters"
]

# Posting Styles
POST_STYLES = {
    "Grammar Tips": {
        "hashtags": "#English_Grammar #Learn_English #English_Tips 🧠",
        "structure": "🎯 Rule Explanation\n💡 Example Sentences\n🔑 Why This Matters\n✨ Practical Tip"
    },
    "Vocabulary Tips": {
        "hashtags": "#English_Vocab #Word_of_the_Day #Learn_English 📖",
        "structure": "🚀 3 Words/Phrases\n📌 Meaning\n💡 Example\n💎 Usage Tip"
    },
    "Pronunciation Guide": {
        "hashtags": "#English_Pronunciation #Speak_English #Learn_English 🗣️",
        "structure": "🔊 Sound/Rule Focus\n💡 Example Words\n🎯 Practice Exercise\n🔈 Pronunciation Tip"
    }
}

# Engagement Messages
ENGAGEMENT_MSGS = [
    "💬 Practice in the comments - we'll correct you!",
    "🌟 Like if you found this helpful!",
    "📌 Save this for later practice!",
    "🔔 Turn on notifications for daily lessons!"
]

def get_nature_image():
    """Get a random nature image"""
    return get_pixabay_image_url(random.choice(PIXABAY_KEYWORDS))

def generate_english_post():
    """Generate an English learning post for Arabic speakers"""
    topic = random.choice(LESSON_TOPICS)
    
    # Choose style based on topic
    if any(word in topic for word in ["Grammar", "Verb", "Tense", "Article"]):
        style_name, style = "Grammar Tips", POST_STYLES["Grammar Tips"]
    elif any(word in topic for word in ["Vocab", "Word", "Phrase", "Collocation"]):
        style_name, style = "Vocabulary Tips", POST_STYLES["Vocabulary Tips"]
    else:
        style_name, style = "Pronunciation Guide", POST_STYLES["Pronunciation Guide"]
    
    prompt = f"""
    Create an English learning post in Arabic about:
    {topic}
    
    Requirements:
    1. Arabic title with emoji
    2. Content in Arabic explaining English concepts
    3. Structure: {style['structure']}
    4. For pronunciation posts:
       - Show English words only
       - Add Arabic pronunciation guides in parentheses
    5. Include at the end:
       - "{random.choice(ENGAGEMENT_MSGS)}"
       - "👍 Like and follow for daily English lessons"
       - "🎓 Advanced lessons on Telegram: https://t.me/alleliteenglish"
    6. Hashtags: {style['hashtags']}
    
    Important:
    - Never provide pronunciation guides for Arabic words
    - Focus only on English pronunciation
    - Keep explanations simple and practical
    - Use 3-5 emojis per post
    """
    
    response = ask_ai(prompt)
    if response:
        content = clean_ai_output(response)
        
        # Format hashtags properly
        lines = content.split('\n')
        main_content = []
        final_hashtags = style['hashtags']
        
        for line in lines:
            if not line.startswith('#'):
                main_content.append(line)
        
        formatted_content = '\n'.join(main_content).strip()
        formatted_content += '\n\n' + final_hashtags
        
        return formatted_content, get_nature_image(), topic
    
    return None, None, None

def main():
    print("--- Generating English Learning Post ---")
    post, image, topic = generate_english_post()
    
    if post:
        print("\n--- Final Content ---")
        print(post)
        
        if post_to_facebook(post, image):
            print(f"\nPosted successfully: {topic}")
        else:
            print("\nPosting failed")
    else:
        print("Failed to generate content")

if __name__ == "__main__":
    main()