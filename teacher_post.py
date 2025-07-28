import random
from common import ask_ai, post_to_facebook, clean_ai_output, get_pixabay_image_url

# Image Keywords
PIXABAY_KEYWORDS = [
    "grammar", "dictionary", "education", "writing", "test", 
    "exam", "IELTS", "language", "vocabulary", "question", 
    "quiz", "interview", "speaking", "pronunciation", "phonetics"
]

# Lesson Topics
LESSON_TOPICS = [
    # Grammar Topics
    "🔍 Present perfect vs. past simple - spot the difference",
    "💡 Conditionals (all types) with real-world examples",
    "🛠️ Modal verbs advanced usage in professional contexts",
    "🎭 Passive voice constructions in academic writing",
    "⚠️ Articles (a, an, the) - most common mistakes",
    "🔗 Prepositions in phrasal verbs - complete guide",
    "🔄 Gerunds vs. infinitives - when to use which",
    "🗣️ Reported speech transformations with examples",
    "✂️ Relative clauses reduction techniques",
    "📜 Inversion in formal English - advanced structures",
    
    # Vocabulary Topics
    "📚 Academic vocabulary for high-scoring essays",
    "💼 Business English phrases for professionals",
    "✍️ IELTS writing task vocabulary boosters",
    "🔤 Synonyms for overused words - upgrade your vocabulary",
    "🤝 Collocations with common verbs - natural combinations",
    "🎩 Formal vs. informal vocabulary - context matters",
    "🌐 Idioms for academic writing - use them correctly",
    "💬 Phrasal verbs in context - business edition",
    "🧩 Word formation prefixes/suffixes - build vocabulary",
    "🚫 False friends in English - words that trick you",
    
    # Pronunciation Topics
    "🔊 Commonly mispronounced words - fix them now",
    "🎙️ Silent letters in English - complete guide",
    "🗣️ Difficult English sounds for non-natives",
    "👄 Tongue twisters to improve pronunciation",
    "🎵 Stress patterns in English words",
    "🇺🇸🇬🇧 American vs. British pronunciation differences",
    "📢 Homophones - words that sound the same",
    "🎤 Pronunciation for IELTS speaking test",
    "👂 Minimal pairs practice - train your ear",
    "💬 Connected speech in natural conversation",
    
    # Question/Quiz Topics
    "❓ Common grammar mistakes - can you spot them?",
    "🔎 Spot the error - advanced edition",
    "🔄 Sentence transformation challenge",
    "📝 Word order exercises - rearrange correctly",
    "⏳ Choose the correct tense - timed quiz",
    "📖 Vocabulary gap-fill - academic text",
    "✅ Which sentence is correct? Grammar test",
    "✏️ Paraphrasing practice - essential skill",
    "✂️ Error correction challenge - find all mistakes",
    "🏆 Grammar jeopardy - test your knowledge",
    
    # IELTS Practice
    "🎤 IELTS speaking part 1 - model answers",
    "✍️ IELTS writing task 1 - band 9 structure",
    "👂 IELTS listening section - proven strategies",
    "📚 IELTS reading - time management tips",
    "📊 IELTS speaking band descriptors explained",
    "🖋️ IELTS writing task 2 - essay types breakdown",
    "💯 IELTS interview techniques for high scores",
    "📈 IELTS vocabulary for band 7+",
    "🗣️ IELTS pronunciation tips for clear speech",
    "⏱️ IELTS test day - time management strategies",
    
    # New Pronunciation Focus
    "🔊 10 words English learners mispronounce",
    "🗣️ Pronunciation guide: /θ/ vs /ð/ sounds",
    "👂 Listen & repeat: Difficult word pairs",
    "🎤 Business words professionals mispronounce",
    "📢 Stress patterns in academic vocabulary",
    "🇺🇸 American English pronunciation tips",
    "🇬🇧 British English pronunciation guide",
    "💬 Linking sounds in natural speech",
    "👄 Mouth positions for difficult sounds",
    "📝 Phonetic transcription practice"
]

# Posting Styles
POST_STYLES = {
    "Grammar Focus": {
        "hashtags": "#EnglishGrammar #GrammarQuiz #LearnEnglish 📚",
        "structure": "📝 Explanation with 3 examples\n💡 1 practice question\n🔍 Answer with explanation"
    },
    "Vocabulary Builder": {
        "hashtags": "#EnglishVocabulary #WordOfTheDay #LanguageLearning 📖", 
        "structure": "✨ 5 useful words/phrases\n📖 Definitions & examples\n💬 Practice sentences"
    },
    "Quiz Time": {
        "hashtags": "#EnglishQuiz #TestYourEnglish #GrammarChallenge ❓",
        "structure": "🧠 5-question quiz\n⏳ Take 30 seconds per question\n✅ Answers explained"
    },
    "IELTS Prep": {
        "hashtags": "#IELTSPrep #IELTSTips #EnglishTest 🎯",
        "structure": "📊 Practical advice\n✍️ Sample questions\n💡 Expert tips"
    },
    "Pronunciation Guide": {
        "hashtags": "#EnglishPronunciation #SpeakClearly #Phonetics 🔈",
        "structure": "🔊 Word list with phonetic symbols\n👄 Pronunciation tips\n🎙️ Practice sentences"
    }
}

def get_educational_image():
    """Get a random educational image"""
    return get_pixabay_image_url(random.choice(PIXABAY_KEYWORDS))

def generate_lesson_post():
    """Generate a formatted lesson post"""
    topic = random.choice(LESSON_TOPICS)
    
    # Choose style based on topic type
    if "IELTS" in topic:
        style_name, style = "IELTS Prep", POST_STYLES["IELTS Prep"]
    elif "quiz" in topic.lower() or "question" in topic.lower() or "challenge" in topic.lower():
        style_name, style = "Quiz Time", POST_STYLES["Quiz Time"]
    elif any(word in topic.lower() for word in ["vocabulary", "words", "phrases", "synonyms"]):
        style_name, style = "Vocabulary Builder", POST_STYLES["Vocabulary Builder"]
    elif any(word in topic.lower() for word in ["pronounce", "pronunciation", "phonetic", "sound", "speak"]):
        style_name, style = "Pronunciation Guide", POST_STYLES["Pronunciation Guide"]
    else:
        style_name, style = "Grammar Focus", POST_STYLES["Grammar Focus"]
    
    prompt = f"""
    Create an engaging English learning post about:
    {topic}
    
    Requirements:
    1. Title on first line with relevant emoji
    2. Content in clear, professional English with emojis
    3. Structure: {style['structure']}
    4. Include practical examples
    5. For pronunciation: include phonetic symbols
    6. End with exactly these 3 hashtags: {style['hashtags']}
    
    Notes:
    - Use emojis to make it visually appealing
    - Keep explanations concise but thorough
    - For quizzes, include answers with explanations
    - For pronunciation: use IPA symbols when helpful
    - Make it interactive and engaging
    """
    
    response = ask_ai(prompt)
    if response:
        content = clean_ai_output(response)
        
        # Ensure proper hashtags
        lines = content.split('\n')
        main_content = []
        hashtags = []
        
        for line in lines:
            if line.startswith('#'):
                hashtags.extend(line.split())
            else:
                main_content.append(line)
        
        # Use specified hashtags
        final_hashtags = style['hashtags']
        
        # Rebuild content
        formatted_content = '\n'.join(main_content).strip()
        formatted_content += '\n\n' + final_hashtags
        
        return formatted_content, get_educational_image(), topic
    
    return None, None, None

def main():
    print("--- Generating English Learning Post ---")
    post, image, topic = generate_lesson_post()
    
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