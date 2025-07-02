import os
import random
from common import read_json, write_json, ask_ai, post_to_facebook, get_current_day_of_week_arabic, clean_ai_output # Added clean_ai_output
import datetime

RANDOM_POST_TYPES_FILE = "random_types.json"

def get_random_post_type(random_types_config: dict) -> str:
    """Selects a random post type from the configuration based on weights."""
    if not random_types_config or not random_types_config.get("types"):
        print("No random post types configured in random_types.json.")
        return None

    types = random_types_config["types"]
    if not types:
        print("Random types list is empty.")
        return None

    weights = [item.get("weight", 1) for item in types]
    choices = [item["name"] for item in types]

    try:
        return random.choices(choices, weights=weights, k=1)[0]
    except Exception as e:
        print(f"Error selecting random post type: {e}. Falling back to first type if available.")
        return choices[0] if choices else None


def generate_random_post(post_type: str) -> str:
    """Generates a random educational post using AI."""
    day_of_week = datetime.datetime.now().strftime("%A")

    # **IMPORTANT: Updated Prompt for better formatting**
    base_prompt = f"""
    You are an English language educator for Arabic-speaking students.
    Your task is to create a concise, helpful, and educational Facebook post.
    
    **CRITICAL FORMATTING RULES:**
    1.  **NO MARKDOWN:** Do NOT use markdown characters for bolding, italics, or headings (e.g., **, *, ##). Write plain text.
    2.  **SEPARATE ENGLISH & ARABIC:** Always put English text on its own line(s), and its Arabic translation directly below it on new line(s). Do NOT mix English and Arabic on the same line.
        Example:
        Word: Hello
        الكلمة: مرحباً
        
        Example sentence: Hello, how are you?
        مثال الجملة: مرحباً، كيف حالك؟
    3.  Use clear paragraphs with double newlines between them.
    4.  Include 3-5 relevant hashtags in both Arabic and English at the very end of the post, each on a new line after the main content.
    5.  **Absolutely avoid any phrases that suggest you are an AI** (e.g., "As an AI model...", "Here's your post!", "I can help with that").
    6.  The content should be in formal Arabic, with English words or phrases integrated contextually.
    """

    if post_type == "Word of the Day":
        prompt = base_prompt + """
        Requirement: "Word of the Day". Choose a common English word, explain its meaning in Arabic, and provide an example of its use in an English sentence with an Arabic translation.
        """
    elif post_type == "Grammar Tip":
        prompt = base_prompt + """
        Requirement: "Grammar Tip". Choose a simple English grammar point (e.g., use of 'a'/'an', 'there/their/they're', common tenses), explain it concisely in Arabic, and provide one or two examples.
        """
    elif post_type == "Quiz":
        prompt = base_prompt + """
        Requirement: "Short Quiz". Create one or two short English questions (multiple choice or fill-in-the-blank) and provide the correct answer(s) at the end of the post (after some space or a new line to avoid immediate reveal). Remember to separate English question/options from Arabic translations.
        """
    elif post_type == "Dialogue":
        prompt = base_prompt + """
        Requirement: "Short Dialogue". Create a short, simple dialogue between two people in an everyday situation (e.g., ordering coffee, greetings, asking for directions). Provide the dialogue in English, each line followed by its Arabic translation on a new line.
        """
    elif post_type == "Exercise":
        prompt = base_prompt + """
        Requirement: "Exercise". Provide a simple exercise for students (e.g., rearrange words to form a sentence, match words with meanings, correct mistakes). Provide the instructions/questions in English followed by Arabic, and include an answer key at the end (after some space).
        """
    else:
        # Fallback for unknown types or general random content
        prompt = base_prompt + """
        Requirement: A general educational post about English learning tips or a short cultural fact related to the English language.
        """

    print(f"Generating random post of type: {post_type} for {day_of_week} (local time).")
    ai_generated_content = ask_ai(prompt)

    if not ai_generated_content:
        print("AI failed to generate random post. Falling back to simple message.")
        return f"مرحباً بكم! نتمنى لكم يوماً تعليمياً سعيداً في {get_current_day_of_week_arabic()}!\n#تعلم_الإنجليزي\n#لغة_انجليزية"

    # Apply cleanup after AI generation
    final_post_content = clean_ai_output(ai_generated_content)

    # Ensure hashtags are present and on separate lines at the end
    if "#" not in final_post_content[-50:]:
        if not final_post_content.strip().endswith('\n\n'):
            final_post_content += '\n\n'
        final_post_content += "#تعلم_اللغة_الإنجليزية\n#لغة_انجليزية\n#دروس_انجليزي\n#EnglishLearning\n#LearnEnglish"

    return final_post_content

def main():
    random_types_config = read_json(RANDOM_POST_TYPES_FILE)
    post_type = get_random_post_type(random_types_config)

    if not post_type:
        print("Failed to determine a random post type. Exiting random post process.")
        return

    post_content = generate_random_post(post_type)

    if post_to_facebook(post_content):
        post_log = read_json("post_log.json")
        post_log.setdefault("posts", []).append({
            "timestamp": datetime.datetime.now().isoformat(),
            "type": post_type,
            "content_preview": post_content[:200] + "..."
        })
        write_json("post_log.json", post_log)
        print("Post logged successfully.")
    else:
        print("Failed to post random content to Facebook.")

if __name__ == "__main__":
    main()

