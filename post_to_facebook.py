import os
import json
import datetime
import sys
import requests
import google.generativeai as genai

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
        return default_value if default_value is not None else {}
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filename}. Returning default value.")
        return default_value if default_value is not None else {}

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
        # Check if response.text exists and is not empty
        if hasattr(response, 'text') and response.text.strip():
            return response.text.strip()
        else:
            print("Gemini API response was empty or did not contain text.")
            return None
    except Exception as e:
        print(f"Error generating AI content: {e}")
        # Attempt to get text from candidate if primary response failed
        if response and response.candidates:
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
        self.teachers_data = read_json("teachers.json", default_value=[])
        self.teaching_styles = read_json("teaching_styles.json", default_value={})
        self.english_levels = read_json("english_levels.json", default_value={})

    def get_teacher_by_id(self, teacher_id):
        return next((t for t in self.teachers_data if t["id"] == int(teacher_id)), None)

    def get_random_teacher(self):
        # Filter out teachers who have completed all their lessons
        available_teachers = [
            t for t in self.teachers_data
            if self.post_state["teacher_progress"].get(str(t["id"]), {}).get("lesson_index", 0) < len(t["lessons"])
        ]
        if not available_teachers:
            print("All teachers have completed their lessons. Please add more lessons or reset progress.")
            return None
        return random.choice(available_teachers)

    def prepare_teacher_post(self, teacher):
        teacher_id_str = str(teacher["id"])
        teacher_progress = self.post_state["teacher_progress"].setdefault(teacher_id_str, {"lesson_index": 0})
        current_lesson_index = teacher_progress["lesson_index"]

        if current_lesson_index >= len(teacher["lessons"]):
            print(f"Teacher {teacher['name']} has completed all their lessons.")
            return None # Indicate no more lessons

        lesson = teacher["lessons"][current_lesson_index]
        
        style = self.teaching_styles.get(teacher["style_id"], {"name": "General", "description": ""})
        level = self.english_levels.get(teacher["level_id"], {"name": "General", "description": ""})

        base_prompt = (
            f"You are an English teacher named {teacher['name']} with a {style['name']} teaching style. "
            f"You teach students at an {level['name']} English level. "
            f"Your current lesson is about: {lesson['topic']}. "
            f"Explain this topic clearly and concisely, including key points. "
            f"Your post should be engaging and encourage interaction. "
            f"Keep it within 150-200 words.\n\n"
            f"Lesson Content: {lesson['content']}"
        )

        if teacher["id"] == 1 and self.post_state["days_since_last_exam"] >= EXAM_INTERVAL_DAYS:
            print(f"It's time for an exam post for Teacher {teacher['name']}!")
            prompt = (
                f"{base_prompt}\n\nAdditionally, include a small, engaging quiz or a question "
                f"at the end related to the lesson or general English knowledge, "
                f"to test understanding. Make it interactive, asking users to comment their answers."
            )
            is_exam = True
        else:
            prompt = base_prompt
            is_exam = False
        
        return prompt, is_exam, teacher_id_str, current_lesson_index

    def main(self, current_post_slot=None, specific_teacher_id=None, post_state=None, post_log=None):
        self.post_state = post_state if post_state is not None else self.post_state
        self.post_log = post_log if post_log is not None else self.post_log

        if specific_teacher_id:
            teacher = self.get_teacher_by_id(specific_teacher_id)
            if not teacher:
                print(f"Error: Teacher with ID {specific_teacher_id} not found.")
                return False
            print(f"Generating post for specific teacher: {teacher['name']} (ID: {specific_teacher_id})")
        else: # Scheduled run, determine teacher based on current slot
            if current_post_slot is None:
                print("Error: current_post_slot must be provided for scheduled teacher posts.")
                return False
            
            # Map slots to teachers
            teacher_map = {0: 1, 2: 2, 4: 3} # Slot -> Teacher ID
            teacher_id_for_slot = teacher_map.get(current_post_slot)

            if not teacher_id_for_slot:
                print(f"Error: No teacher mapped to slot {current_post_slot}. This should not happen for teacher slots.")
                return False

            teacher = self.get_teacher_by_id(teacher_id_for_slot)
            if not teacher:
                print(f"Error: Teacher with ID {teacher_id_for_slot} not found for slot {current_post_slot}.")
                return False
            print(f"Generating post for scheduled teacher: {teacher['name']} (ID: {teacher_id_for_slot}) for slot {current_post_slot}")

        post_data = self.prepare_teacher_post(teacher)
        if not post_data:
            print(f"No content generated for teacher {teacher['name']}.")
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
                    "teacher_id": teacher["id"],
                    "lesson_index": current_lesson_index,
                    "is_exam": is_exam_post,
                    "content": ai_post_content[:200] + "..." if len(ai_post_content) > 200 else ai_post_content
                })
                # Update teacher progress and exam status
                if not is_exam_post: # Only advance lesson if it's not an exam post
                    self.post_state["teacher_progress"][teacher_id_str]["lesson_index"] += 1
                    print(f"Advanced lesson for Teacher {teacher['name']} to index {self.post_state['teacher_progress'][teacher_id_str]['lesson_index']}")
                else:
                    print(f"Teacher {teacher['name']} posted an exam. Lesson index NOT advanced.")
                
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
            f"(e.g., ask a question related to the topic for comments)."
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

import random # Import random module needed for random_post

def main():
    post_state = read_json("post_state.json", default_value={
        "current_teacher_index": 0, # Legacy, might not be used directly anymore
        "days_since_last_exam": 0,
        "post_slot_of_day": 0, # Legacy, might not be used directly anymore
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

    # Initialize current_post_cycle_index and other necessary defaults if not present
    post_state.setdefault("current_post_cycle_index", 0)
    post_state.setdefault("days_since_last_exam", 0)
    post_state.setdefault("teacher_progress", {
        "1": {"lesson_index": 0},
        "2": {"lesson_index": 0},
        "3": {"lesson_index": 0}
    })
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

    # If specific_teacher_id is provided, it's a direct teacher test and overrides slot logic
    if specific_teacher_id and specific_teacher_id not in ('None', ''): # Robustness: check for 'None' string
        print(f"Manual trigger: Specific Teacher ID test for {specific_teacher_id}")
        teacher_post_handler = TeacherPost(post_state, post_log)
        teacher_post_handler.main(specific_teacher_id=specific_teacher_id, post_state=post_state, post_log=post_log)
        write_json("post_state.json", post_state) # Save state after manual teacher run
        write_json("post_log.json", post_log) # Save log after manual teacher run
        print("Manual run for specific teacher completed and state/log saved.")
        sys.exit(0)
    
    # If manual_run_slot is provided (and not 'None' string), handle it
    if manual_run_slot_str and manual_run_slot_str not in ('None', ''): # Robustness: check for 'None' string
        try:
            manual_run_slot = int(manual_run_slot_str)
            if not (0 <= manual_run_slot <= 5):
                raise ValueError("Slot out of range (0-5)")
            print(f"Manual trigger: Running for specific slot: {manual_run_slot}")
            
            if manual_run_slot % 2 == 0: # Teacher slots (0, 2, 4)
                teacher_post_handler = TeacherPost(post_state, post_log)
                teacher_post_handler.main(current_post_slot=manual_run_slot, post_state=post_state, post_log=post_log)
            else: # Random slots (1, 3, 5)
                random_post_handler = RandomPost(post_state, post_log)
                random_post_handler.main(current_post_slot=manual_run_slot, post_state=post_state, post_log=post_log) 
            
            write_json("post_state.json", post_state) # Save state after manual slot run
            write_json("post_log.json", post_log) # Save log after manual slot run
            print("Manual run for specific slot completed and state/log saved.")
            sys.exit(0)

        except (ValueError, TypeError) as e:
            print(f"Warning: Invalid MANUAL_RUN_SLOT '{manual_run_slot_str}'. Error: {e}. Falling back to scheduled logic if no specific teacher ID.")


    # --- Handle Scheduled Runs ---
    
    # Reset daily cycle index and posts_today_hours at the start of a new day
    if post_state.get("last_run_date") != today_date:
        print(f"New day detected ({today_date}). Resetting daily post tracker and cycle index.")
        post_state["last_run_date"] = today_date
        post_state["posts_today_hours"] = [] # Clear tracked hours for new day
        post_state["current_post_cycle_index"] = 0 # Reset to Slot 0 for the start of the day cycle
        # IMPORTANT: Save state immediately after resetting for new day, so subsequent runs see it
        write_json("post_state.json", post_state) 
        print("Post state reset for new day and saved.")
    
    # --- TEMPORARY TEST OVERRIDE START ---
    # FOR TESTING ONLY: This section bypasses the exact time matching and sequential slot check
    # to allow rapid cycling through all post types (0-5) for testing.
    # The workflow cron (e.g., every 2 minutes) will trigger this, and each time,
    # it will try to process the next slot in the sequence.
    current_slot_to_process = post_state["current_post_cycle_index"]
    print(f"*** TEST MODE ACTIVE *** Forcing processing of slot {current_slot_to_process} to observe sequence.")
    # --- TEMPORARY TEST OVERRIDE END ---

    # Determine post type based on current_slot_to_process (which is now determined by the TEST MODE override)
    if current_slot_to_process % 2 == 0: # Teacher posts (0, 2, 4)
        print(f"Executing Teacher post for Slot {current_slot_to_process}...")
        teacher_post_handler = TeacherPost(post_state, post_log)
        teacher_post_handler.main(current_post_slot=current_slot_to_process, post_state=post_state, post_log=post_log)

        # Handle exam counter reset if it was an exam post (slot 0 only)
        # This logic remains, even in test mode, to simulate day progression
        if current_slot_to_process == 0:
            if post_state["days_since_last_exam"] >= EXAM_INTERVAL_DAYS:
                post_state["days_since_last_exam"] = 0 # Reset only if an exam was actually due and posted
                print("Exam posted, resetting days_since_last_exam.")
            # If no exam was due, days_since_last_exam will be incremented at the end of the 6-post cycle
        
    else: # Random posts (1, 3, 5)
        print(f"Executing Random post for Slot {current_slot_to_process}...")
        random_post_handler = RandomPost(post_state, post_log)
        random_post_handler.main(current_post_slot=current_slot_to_process, post_state=post_state, post_log=post_log) 

    # After a successful post call, update the cycle index for the next run
    # This is crucial for the sequential testing.
    post_state["posts_today_hours"].append(current_utc_hour_minute.split(':')[0]) # Still log the actual hour, though less relevant for forced test
    post_state["current_post_cycle_index"] = (current_slot_to_process + 1) % len(POSTING_TIMES_UTC)
    
    # If we just completed the last slot of the day (slot 5), advance exam counter.
    # This check relies on the cycle index wrapping back to 0.
    if post_state["current_post_cycle_index"] == 0: # Means all 6 posts completed and cycle reset
        post_state["days_since_last_exam"] = post_state.get("days_since_last_exam", 0) + 1
        print(f"Daily cycle complete. Incrementing days_since_last_exam to: {post_state['days_since_last_exam']}")
    
    # Save post_state and post_log at the end of the main orchestration
    write_json("post_state.json", post_state)
    write_json("post_log.json", post_log)
    print("Post state and log updated successfully for scheduled run.")


if __name__ == "__main__":
    main()
