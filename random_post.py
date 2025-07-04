# random_post.py (Example - you'll need to apply these changes to your actual file)
import os
import random
# Remove read_json, write_json from common import here
from common import ask_ai, post_to_facebook, clean_ai_output
import datetime

# ... (other imports and functions in random_post.py) ...

# Modified main function to accept post_state and post_log as arguments
def main(current_post_slot: int = None, post_state: dict = None, post_log: dict = None):
    """
    Main function for random post generation and posting.
    Accepts post_state and post_log dictionaries to modify them directly.
    """
    # If post_state or post_log are not passed (e.g., direct script execution for testing), load them
    if post_state is None:
        post_state = read_json("post_state.json")
    if post_log is None:
        post_log = read_json("post_log.json")

    # Your existing random post generation logic here
    # Example:
    post_type = random.choice(["did_you_know", "vocabulary_challenge", "grammar_tip"])
    post_content = ""
    image_to_post = None # If random posts use images
    
    if post_type == "did_you_know":
        post_content = generate_did_you_know_post()
    elif post_type == "vocabulary_challenge":
        post_content = generate_vocabulary_challenge_post()
    elif post_type == "grammar_tip":
        post_content = generate_grammar_tip_post()

    print(f"Generated Random Post: {post_type}")

    if post_content:
        if post_to_facebook(post_content, image_to_post): # Assuming post_to_facebook handles actual API call
            post_log.setdefault("posts", []).append({
                "timestamp": datetime.datetime.now().isoformat(),
                "type": f"random_{post_type}",
                "content_preview": post_content[:200] + "...",
                "image_used": image_to_post if image_to_post else "none",
                "slot_index": current_post_slot
            })
            print("Random post content sent to Facebook. Log will be saved by main orchestrator.")
        else:
            print("Failed to post random content to Facebook.")

    # IMPORTANT: DO NOT save post_state.json or post_log.json here.
    # The calling script (post_to_facebook.py) will do it.

# For direct testing of random_post.py
if __name__ == "__main__":
    local_post_state = read_json("post_state.json") # For local testing
    local_post_log = read_json("post_log.json") # For local testing
    main(post_state=local_post_state, post_log=local_post_log)
    write_json("post_state.json", local_post_state) # Save after local test
    write_json("post_log.json", local_post_log) # Save after local test
