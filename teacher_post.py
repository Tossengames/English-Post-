import sys
import os
import json # Make sure json is imported if not already

# --- (Your existing functions like read_json, write_json, get_next_lesson, get_next_teacher, etc.) ---

def main():
    # Load configuration and state
    teacher_meta = read_json("teacher_meta.json")
    post_state = read_json("post_state.json") # This will be empty dict if file doesn't exist

    # Initialize post_state if it's empty or missing keys
    if "current_teacher_index" not in post_state:
        post_state["current_teacher_index"] = 0
    if "days_since_last_exam" not in post_state:
        post_state["days_since_last_exam"] = 0
    if "post_slot_of_day" not in post_state:
        post_state["post_slot_of_day"] = 0
    if "teachers" not in post_state:
        post_state["teachers"] = {}

    # --- Parse Command-Line Arguments ---
    specific_teacher_id = None
    manual_post_slot_override = None # This will hold the 0, 1, or 2 from the workflow input

    if len(sys.argv) > 1 and sys.argv[1] != 'None':
        specific_teacher_id = sys.argv[1]

    if len(sys.argv) > 2 and sys.argv[2] != 'None': # Check if manual_post_slot was provided
        try:
            manual_post_slot_override = int(sys.argv[2])
            print(f"Manual post slot override detected: {manual_post_slot_override}")
        except ValueError:
            print(f"Warning: Invalid manual_post_slot value '{sys.argv[2]}'. Ignoring override.")
            manual_post_slot_override = None # Reset if not a valid number

    # --- Determine the current_slot for THIS run ---
    # If a manual override is provided, use it. Otherwise, use the slot from post_state.json.
    current_slot = post_state.get("post_slot_of_day", 0) # Default to 0 if not found
    if manual_post_slot_override is not None:
        current_slot = manual_post_slot_override % 3 # Ensure it's 0, 1, or 2
        print(f"Running for manual slot: {current_slot}")
    else:
        print(f"Running for scheduled/sequential slot: {current_slot}")

    post_content = None # Initialize post_content
    # --- Logic for posting based on current_slot ---
    if specific_teacher_id:
        print(f"Generating post for specific teacher ID: {specific_teacher_id}")
        teacher_info = teacher_meta.get(specific_teacher_id)
        if teacher_info:
            lesson_content = get_next_lesson(specific_teacher_id, teacher_meta, post_state) # lesson_index advances here
            if lesson_content:
                post_content = generate_teacher_post(specific_teacher_id, lesson_content, teacher_info)
            else:
                print(f"Could not get next lesson for specific teacher {specific_teacher_id}.")
        else:
            print(f"Specific teacher ID {specific_teacher_id} not found in teacher_meta.json.")
    elif current_slot == 0 or current_slot == 2:
        # Teacher post for slot 0 or 2
        selected_teacher_id = get_next_teacher(teacher_meta, post_state) # Teacher ID rotates per full cycle
        if selected_teacher_id:
            teacher_info = teacher_meta.get(selected_teacher_id)
            lesson_content = get_next_lesson(selected_teacher_id, teacher_meta, post_state) # lesson_index advances here
            if lesson_content:
                post_content = generate_teacher_post(selected_teacher_id, lesson_content, teacher_info)
            else:
                print(f"Could not get next lesson for teacher {selected_teacher_id}.")
        else:
            print("No teacher selected for post.")
    elif current_slot == 1:
        # Random post for slot 1
        post_content = generate_random_post() # You'll need to ensure this function exists and works
    else:
        print(f"Unexpected post slot: {current_slot}")

    # --- Post to Facebook ---
    if post_content:
        post_successful = post_to_facebook(post_content)
        if post_successful:
            print("Content successfully posted to Facebook.")
            # --- IMPORTANT STATE UPDATE LOGIC ---
            # Only update post_slot_of_day if it's NOT a manual override.
            # Teacher-specific lesson_index (updated by get_next_lesson) and current_teacher_index
            # (updated later) should always persist if the post was successful.
            if manual_post_slot_override is None:
                # Advance post_slot_of_day for the next scheduled run
                post_state["post_slot_of_day"] = (current_slot + 1) % 3

                # Advance teacher index and days_since_last_exam ONLY after the 3rd post of the day (slot 2 completing)
                if post_state["post_slot_of_day"] == 0: # This means slot 2 just completed
                    advance_teacher_index(post_state, teacher_meta)
                    post_state["days_since_last_exam"] = (post_state.get("days_since_last_exam", 0) + 1) % 7 # Assuming weekly exams, adjust modulo as needed
            else:
                print("Manual override, not advancing post_slot_of_day for scheduled sequence.")

            write_json("post_state.json", post_state) # Always write post_state to save lesson/teacher index advancements
            log_post(post_content) # Assuming you have a log_post function that writes to post_log.json
        else:
            print("Failed to post content to Facebook. Post state not updated for failed post.")
    else:
        print("No content generated to post.")

    # --- (Ensure read_json and write_json are correctly implemented to handle file existence) ---
    # Example for read_json (put this in common.py or similar):
    # def read_json(filename):
    #     try:
    #         with open(filename, 'r', encoding='utf-8') as f:
    #             return json.load(f)
    #     except (FileNotFoundError, json.JSONDecodeError):
    #         return {} # Return empty dict if file not found or invalid JSON

    # Example for write_json (put this in common.py or similar):
    # def write_json(filename, data):
    #     with open(filename, 'w', encoding='utf-8') as f:
    #         json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
