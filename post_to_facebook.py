import os
import json
import datetime
import sys
import requests
import google.generativeai as genai
import random # Make sure random is imported at the top

# --- Configuration (from environment variables) ---
FB_PAGE_ID = os.getenv('FB_PAGE_ID')
FB_PAGE_TOKEN = os.getenv('FB_PAGE_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# --- Constants ---
# These are your fixed UTC posting times (originally 8 AM, 10 AM, 12 PM, 2 PM, 4 PM, 6 PM EEST)
# EEST (Eastern European Summer Time) is UTC+3.
# So, 8 AM EEST is 5 AM UTC, 10 AM EEST is 7 AM UTC, etc.
POSTING_TIMES_UTC = ["05:00", "07:00", "09:00", "11:00", "13:00", "15:00"] # 6 slots
EXAM_INTERVAL_DAYS = 7 # Number of days between exam posts (for Slot 0)

# --- Gemini API Configuration ---
genai.configure(api_key=GEMINI_API_KEY)
GEMINI_MODEL = genai.GenerativeModel('gemini-pro')

# --- File Operations ---
def read_json(filename, default_value=None):
    """Reads a JSON file, returns its content, or a default value if file doesn't exist."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {filename} not found. Returning default value.")
        # Ensure correct default for list-like JSONs like random_topics
        if default_value is not None:
            return default_value
        # For dictionary-like JSONs (like teacher_meta, post_state, post_log)
        return {} 
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filename}. Returning default value.")
        if default_value is not None:
            return default_value
        return {}

def write_json(filename, data):
    """Writes data to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# --- Post to Facebook Function ---
def post_to_facebook(message):
    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
    params = {
        'message': message,
        'access_token': FB_PAGE_TOKEN
    }
    response = requests.post(url, params=params)
    if response.status_code == 200:
        print("Successfully posted to Facebook!")
        print(response.json())
        return True
    else:
        print(f"Error posting to Facebook: {response.status_code}")
        print(response.json())
        return False

# --- Post Generation Logic (Moved from main script) ---
def generate_ai_post(prompt_text):
    try:
        response = GEMINI_MODEL.generate_content(prompt_text)
        if hasattr(response, 'text') and response.text.strip():
            return response.text.strip()
        else:
            print("Gemini API response was empty or did not contain text.")
            return None
    except Exception as e:
        print(f"Error generating AI content: {e}")
        # Attempt to get text from candidate if primary response failed
        if response and response.candidates: # 'response' might not be defined if the API call truly failed at its core
            for candidate in response.candidates:
                if candidate.content and hasattr(candidate.content, 'parts') and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text.strip():
                            print("Using text from candidate due to primary response issue.")
                            return part.text.strip()
        return None

# --- Teacher Post Module ---
class TeacherPost:
    def __init__(self, post_state, post_log):
        self.post_state = post_state
        self.post_log = post_log
        # Load teacher_meta.json directly
        self.teacher_meta_data = read_json("teacher_meta.json", default_value={})
        if not self.teacher_meta_data:
            print("ERROR: teacher_meta.json not found or empty. Teacher posts will not function.")
            sys.exit(1) # Exit if critical teacher data is missing

    def get_teacher_by_id(self, teacher_id):
        # Teacher IDs are now strings in teacher_meta.json (e.g., "1", "2", "3")
        return self.teacher_meta_data.get(str(teacher_id), None)

    def prepare_teacher_post(self, teacher_id_str):
        teacher = self.get_teacher_by_id(teacher_id_str)
        if not teacher:
            print(f"Teacher with ID {teacher_id_str} not found in teacher_meta.json.")
            return None

        teacher_progress = self.post_state["teacher_progress"].setdefault(teacher_id_str, {"lesson_index": 0})
        current_lesson_index = teacher_progress["lesson_index"]

        if current_lesson_index >= len(teacher["lesson_queue"]):
            print(f"Teacher {teacher['name']} has completed all their lessons.")
            return None # Indicate no more lessons

        lesson_topic = teacher["lesson_queue"][current_lesson_index]
        
        # Use the posting_style directly from teacher_meta.json
        posting_style = teacher["posting_style"]

        base_prompt = (
            f"You are an English teacher named {teacher['name']}. Your persona and teaching style are: '{posting_style}'. "
            f"Your current lesson topic is: '{lesson_topic}'. "
            f"Explain this topic clearly and concisely, including key points. "
            f"Your post should be engaging and encourage interaction, always including a call to action to like, share, and comment. "
            f"Keep it within 150-200 words, using the specified Arabic dialect if mentioned in the posting style.\n\n"
        )

        is_exam = False
        # Teacher ID "1" (string) is for the exam post logic
        if teacher_id_str == "1" and self.post_state["days_since_last_exam"] >= EXAM_INTERVAL_DAYS:
            print(f"It's time for an exam post for Teacher {teacher['name']}!")
            prompt = (
                f"{base_prompt}\n\nAdditionally, include a small, engaging quiz or a question "
                f"at the end related to the lesson or general English knowledge, "
                f"to test understanding. Make it interactive, asking users to comment their answers."
            )
            is_exam = True
        else:
            prompt = base_prompt
        
        return prompt, is_exam, teacher_id_str, current_lesson_index

    def main(self, current_post_slot=None, specific_teacher_id=None, post_state=None, post_log=None):
        self.post_state = post_state if post_state is not None else self.post_state
        self.post_log = post_log if post_log is not None else self.post_log

        teacher_to_post_id = None
        if specific_teacher_id:
            teacher_to_post_id = str(specific_teacher_id) # Ensure it's a string
            print(f"Generating post for specific teacher ID: {teacher_to_post_id}")
        else: # Scheduled run, determine teacher based on current slot
            if current_post_slot is None:
                print("Error: current_post_slot must be provided for scheduled teacher posts.")
                return False
            
            # Map slots to teacher IDs (which are strings now)
            teacher_map = {0: "1", 2: "2", 4: "3"} # Slot -> Teacher ID (string)
            teacher_to_post_id = teacher_map.get(current_post_slot)

            if not teacher_to_post_id:
                print(f"Error: No teacher mapped to slot {current_post_slot}. This should not happen for teacher slots.")
                return False

            print(f"Generating post for scheduled teacher ID: {teacher_to_post_id} for slot {current_post_slot}")

        post_data = self.prepare_teacher_post(teacher_to_post_id)
        if not post_data:
            print(f"No content generated for teacher ID {teacher_to_post_id}.")
            return False

        prompt, is_exam_post, teacher_id_str, current_lesson_index = post_data
        ai_post_content = generate_ai_post(prompt)

        if ai_post_content:
            print("Generated AI Post Content:")
            print(ai_post_content)
            
            success = post_to_facebook(ai_post_content)
            if success:
                # Log the post
                self.post_log.append({
                    "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                    "type": "teacher",
                    "teacher_id": teacher_id_str,
                    "lesson_index": current_lesson_index,
                    "is_exam": is_exam_post,
                    "content": ai_post_content[:200] + "..." if len(ai_post_content) > 200 else ai_post_content
                })
                # Update teacher progress and exam status
                if not is_exam_post: # Only advance lesson if it's not an exam post
                    self.post_state["teacher_progress"][teacher_id_str]["lesson_index"] += 1
                    print(f"Advanced lesson for Teacher ID {teacher_id_str} to index {self.post_state['teacher_progress'][teacher_id_str]['lesson_index']}")
                else:
                    print(f"Teacher ID {teacher_id_str} posted an exam. Lesson index NOT advanced.")
                
                return True
        return False

# --- Random Post Module ---
class RandomPost:
    def __init__(self, post_state, post_log):
        self.post_state = post_state
        self.post_log = post_log
        self.random_topics = read_json("random_topics.json", default_value=[])

    def get_random_topic(self):
        if not self.random_topics:
            print("No random topics found in random_topics.json.")
            return None
        return random.choice(self.random_topics)

    def main(self, current_post_slot=None, post_state=None, post_log=None):
        self.post_state = post_state if post_state is not None else self.post_state
        self.post_log = post_log if post_log is not None else self.post_log

        if current_post_slot is None:
            print("Error: current_post_slot must be provided for random posts.")
            return False

        topic_data = self.get_random_topic()
        if not topic_data:
            return False
        
        prompt = (
            f"Create an engaging Facebook post about: {topic_data['topic']}. "
            f"Include interesting facts or a brief explanation from this content: {topic_data['content']}. "
            f"The post should be positive, concise (150-200 words), and encourage interaction "
            f"(e.g., ask a question related to the topic for comments). "
            f"Always include a call to action to like, share, and comment."
        )

        ai_post_content = generate_ai_post(prompt)

        if ai_post_content:
            print("Generated AI Post Content:")
            print(ai_post_content)
            
            success = post_to_facebook(ai_post_content)
            if success:
                # Log the post
                self.post_log.append({
                    "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                    "type": "random",
                    "topic": topic_data["topic"],
                    "content": ai_post_content[:200] + "..." if len(ai_post_content) > 200 else ai_post_content
                })
                return True
        return False


# --- Main Orchestration Logic ---
def get_current_slot_index(current_time_str):
    """
    Determines if the current time matches any of the scheduled posting times.
    Returns the index of the matching slot, or -1 if no match.
    """
    for i, scheduled_time in enumerate(POSTING_TIMES_UTC):
        if current_time_str == scheduled_time:
            return i
    return -1


def main():
    post_state = read_json("post_state.json", default_value={
        "days_since_last_exam": 0,
        "teacher_progress": {
            "1": {"lesson_index": 0},
            "2": {"lesson_index": 0},
            "3": {"lesson_index": 0}
        },
        "current_post_cycle_index": 0, # The primary index for daily post sequence (0-5)
        "posts_today_hours": [], # Tracks the *hours* for which a post was made today
        "last_run_date": ""
    })
    post_log = read_json("post_log.json", default_value=[])

    # Initialize missing keys if they don't exist
    post_state.setdefault("days_since_last_exam", 0)
    post_state.setdefault("teacher_progress", {
        "1": {"lesson_index": 0},
        "2": {"lesson_index": 0},
        "3": {"lesson_index": 0}
    })
    post_state.setdefault("current_post_cycle_index", 0)
    post_state.setdefault("posts_today_hours", [])
    post_state.setdefault("last_run_date", "")

    # Get current UTC time
    now_utc = datetime.datetime.now(datetime.UTC) # FIX: Use timezone-aware UTC
    current_utc_hour_minute = now_utc.strftime("%H:%M")
    today_date = now_utc.strftime("%Y-%m-%d")

    print(f"Current UTC time: {current_utc_hour_minute}")

    # --- Handle Manual Workflow Dispatch ---
    manual_run_slot_str = os.getenv("MANUAL_RUN_SLOT")
    specific_teacher_id = os.getenv("SPECIFIC_TEACHER_ID")

    manual_run_attempted = False
    manual_run_successful = False

    # If specific_teacher_id is provided, it's a direct teacher test and overrides slot logic
    if specific_teacher_id and specific_teacher_id not in ('None', ''): # Robustness: check for 'None' string
        manual_run_attempted = True
        print(f"Manual trigger: Specific Teacher ID test for {specific_teacher_id}")
        teacher_post_handler = TeacherPost(post_state, post_log)
        if teacher_post_handler.main(specific_teacher_id=specific_teacher_id, post_state=post_state, post_log=post_log):
            manual_run_successful = True
    elif manual_run_slot_str and manual_run_slot_str not in ('None', ''): # Robustness: check for 'None' string
        manual_run_attempted = True
        try:
            manual_run_slot = int(manual_run_slot_str)
            if not (0 <= manual_run_slot <= 5):
                raise ValueError("Slot out of range (0-5)")
            print(f"Manual trigger: Running for specific slot: {manual_run_slot}")
            
            if manual_run_slot % 2 == 0: # Teacher slots (0, 2, 4)
                teacher_post_handler = TeacherPost(post_state, post_log)
                if teacher_post_handler.main(current_post_slot=manual_run_slot, post_state=post_state, post_log=post_log):
                    manual_run_successful = True
            else: # Random slots (1, 3, 5)
                random_post_handler = RandomPost(post_state, post_log)
                if random_post_handler.main(current_post_slot=manual_run_slot, post_state=post_state, post_log=post_log):
                    manual_run_successful = True
        except (ValueError, TypeError) as e:
            print(f"Warning: Manual run input '{manual_run_slot_str}' error: {e}. Not proceeding with manual run.")
            manual_run_successful = False # Ensure this is false if conversion or range failed

    if manual_run_attempted: # If a manual run was even attempted, we save state and exit.
        write_json("post_state.json", post_state)
        write_json("post_log.json", post_log)
        if manual_run_successful:
            print("Manual run completed and state/log saved.")
        else:
            print("Manual run attempted but failed or had invalid input. State/log saved.")
        sys.exit(0) # Exit cleanly if a manual run was processed, whether successful or not


    # --- Handle Scheduled Runs (REVERTED TO ORIGINAL LOGIC) ---
    
    # Reset daily cycle index and posts_today_hours at the start of a new day
    if post_state.get("last_run_date") != today_date:
        print(f"New day detected ({today_date}). Resetting daily post tracker and cycle index.")
        post_state["last_run_date"] = today_date
        post_state["posts_today_hours"] = [] # Clear tracked hours for new day
        post_state["current_post_cycle_index"] = 0 # Reset to Slot 0 for the start of the day cycle
        # IMPORTANT: Save state immediately after resetting for new day, so subsequent runs see it
        write_json("post_state.json", post_state) 
        print("Post state reset for new day and saved.")
    
    # Determine the expected slot for the current time
    expected_slot_index = get_current_slot_index(current_utc_hour_minute)

    if expected_slot_index == -1:
        print(f"No specific post scheduled for {current_utc_hour_minute} UTC. Skipping this run.")
        sys.exit(0)

    # Prevent duplicate posts for the same time slot on the same day
    current_scheduled_hour = POSTING_TIMES_UTC[expected_slot_index].split(':')[0]
    if current_scheduled_hour in post_state.get("posts_today_hours", []):
        print(f"A post for {current_utc_hour_minute} UTC (slot {expected_slot_index}) has already been triggered today. Skipping duplicate.")
        sys.exit(0)

    # Ensure posts are triggered in the correct sequence for the day
    if expected_slot_index != post_state["current_post_cycle_index"]:
        print(f"Scheduled time ({current_utc_hour_minute}, slot {expected_slot_index}) does not match expected cycle index ({post_state['current_post_cycle_index']}). Skipping this run to maintain sequence.")
        sys.exit(0)

    # If all checks pass, proceed with posting
    print(f"Proceeding with post for scheduled slot: {expected_slot_index}")
    current_slot_to_process = expected_slot_index

    # Determine post type based on current_slot_to_process
    if current_slot_to_process % 2 == 0: # Teacher posts (0, 2, 4)
        print("It's time for a teacher lesson post (scheduled)!")
        teacher_post_handler = TeacherPost(post_state, post_log)
        teacher_post_handler.main(current_post_slot=current_slot_to_process, post_state=post_state, post_log=post_log)

        # Handle exam counter reset if it was an exam post (slot 0 only)
        if current_slot_to_process == 0 and post_state.get("teacher_progress", {}).get("1", {}).get("lesson_index", 0) > 0 and post_state["days_since_last_exam"] >= EXAM_INTERVAL_DAYS:
            post_state["days_since_last_exam"] = 0
            print("Exam posted, resetting days_since_last_exam.")
        
    else: # Random posts (1, 3, 5)
        print("It's time for a random post (scheduled)!")
        random_post_handler = RandomPost(post_state, post_log)
        random_post_handler.main(current_post_slot=current_slot_to_process, post_state=post_state, post_log=post_log) 

    # After a successful post call, update the state for the next scheduled run
    post_state["posts_today_hours"].append(current_scheduled_hour) # Track the hour for which post was made
    post_state["current_post_cycle_index"] = (current_slot_to_process + 1) % len(POSTING_TIMES_UTC)
    
    # If we just completed the last slot of the day (slot 5), advance exam counter.
    if post_state["current_post_cycle_index"] == 0: # Means all 6 posts completed and cycle reset
        post_state["days_since_last_exam"] = post_state.get("days_since_last_exam", 0) + 1
        print(f"Daily cycle complete. Incrementing days_since_last_exam to: {post_state['days_since_last_exam']}")
    
    # Save post_state and post_log at the end of the main orchestration
    write_json("post_state.json", post_state)
    write_json("post_log.json", post_log)
    print("Post state and log updated successfully for scheduled run.")


if __name__ == "__main__":
    main()

