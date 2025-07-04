import os
import json
import datetime
import sys
import requests
import google.generativeai as genai
import random 

# --- Configuration (from environment variables) ---
FB_PAGE_ID = os.getenv('FB_PAGE_ID')
FB_PAGE_TOKEN = os.getenv('FB_PAGE_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# --- Constants ---
POSTING_TIMES_UTC = ["05:00", "07:00", "09:00", "11:00", "13:00", "15:00"] # 6 slots

# --- Gemini API Configuration ---
genai.configure(api_key=GEMINI_API_KEY)
GEMINI_MODEL = genai.GenerativeModel('gemini-1.5-flash') 

# --- File Operations ---
def read_json(filename, default_value=None):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Warning: {filename} not found or corrupted. Initializing with default value.")
        if default_value is not None:
            return default_value
        return {}

def write_json(filename, data):
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

# --- Post Generation Logic ---
def generate_ai_post(prompt_text):
    response = None
    try:
        response = GEMINI_MODEL.generate_content(prompt_text)
        if hasattr(response, 'text') and response.text.strip():
            return response.text.strip()
        else:
            print("Gemini API primary response was empty or did not contain text.")
            if response and response.candidates:
                for candidate in response.candidates:
                    if candidate.content and hasattr(candidate.content, 'parts') and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text.strip():
                                print("Using text from candidate due to primary response issue.")
                                return part.text.strip()
            return None
    except Exception as e:
        print(f"Error generating AI content: {e}")
        return None

# --- Teacher Post Module ---
class TeacherPost:
    def __init__(self, post_state, post_log):
        self.post_state = post_state
        self.post_log = post_log
        self.teacher_meta_data = read_json("teacher_meta.json", default_value={})
        if not self.teacher_meta_data:
            print("ERROR: teacher_meta.json not found or empty. Teacher posts will not function.")
            sys.exit(1)

    def get_teacher_by_id(self, teacher_id):
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
            return None

        lesson_topic = teacher["lesson_queue"][current_lesson_index]
        posting_style = teacher["posting_style"]

        prompt = (
            f"You are an English teacher named {teacher['name']}. Your persona and teaching style are: '{posting_style}'. "
            f"Your current lesson topic is: '{lesson_topic}'. "
            f"Explain this topic clearly and concisely, including key points. "
            f"Your post should be engaging and encourage interaction, always including a call to action to like, share, and comment. "
            f"Keep it within 150-200 words, using the specified Arabic dialect if mentioned in the posting style.\n\n"
        )
        
        return prompt, teacher_id_str, current_lesson_index

    def main(self, current_post_slot=None, specific_teacher_id=None, post_state=None, post_log=None):
        self.post_state = post_state if post_state is not None else self.post_state
        self.post_log = post_log if post_log is not None else self.post_log

        teacher_to_post_id = None
        if specific_teacher_id:
            teacher_to_post_id = str(specific_teacher_id)
            print(f"Generating post for specific teacher ID: {teacher_to_post_id}")
        else:
            if current_post_slot is None:
                print("Error: current_post_slot must be provided for teacher posts.")
                return False
            
            teacher_map = {0: "1", 2: "2", 4: "3"}
            teacher_to_post_id = teacher_map.get(current_post_slot)

            if not teacher_to_post_id:
                print(f"Error: No teacher mapped to slot {current_post_slot}. This should not happen for teacher slots.")
                return False

            print(f"Generating post for scheduled teacher ID: {teacher_to_post_id} for slot {current_post_slot}")

        post_data = self.prepare_teacher_post(teacher_to_post_id)
        if not post_data:
            print(f"No content generated for teacher ID {teacher_to_post_id}.")
            return False

        prompt, teacher_id_str, current_lesson_index = post_data
        ai_post_content = generate_ai_post(prompt)

        if ai_post_content:
            print("Generated AI Post Content:")
            print(ai_post_content)
            
            success = post_to_facebook(ai_post_content)
            if success:
                self.post_log.append({
                    "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                    "type": "teacher",
                    "teacher_id": teacher_id_str,
                    "lesson_index": current_lesson_index,
                    "content": ai_post_content[:200] + "..." if len(ai_post_content) > 200 else ai_post_content
                })
                self.post_state["teacher_progress"][teacher_id_str]["lesson_index"] += 1
                print(f"Advanced lesson for Teacher ID {teacher_id_str} to index {self.post_state['teacher_progress'][teacher_id_str]['lesson_index']}")
                
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
    for i, scheduled_time in enumerate(POSTING_TIMES_UTC):
        if current_time_str == scheduled_time:
            return i
    return -1

def main():
    post_state = read_json("post_state.json", default_value={
        "teacher_progress": {
            "1": {"lesson_index": 0},
            "2": {"lesson_index": 0},
            "3": {"lesson_index": 0}
        },
        "current_post_cycle_index": 0,
        "posts_today_hours": [],
        "last_run_date": ""
    })
    post_log = read_json("post_log.json", default_value=[])

    post_state.setdefault("teacher_progress", {
        "1": {"lesson_index": 0},
        "2": {"lesson_index": 0},
        "3": {"lesson_index": 0}
    })
    post_state.setdefault("current_post_cycle_index", 0)
    post_state.setdefault("posts_today_hours", [])
    post_state.setdefault("last_run_date", "")

    now_utc = datetime.datetime.now(datetime.UTC)
    current_utc_hour_minute = now_utc.strftime("%H:%M")
    today_date = now_utc.strftime("%Y-%m-%d")

    print(f"Current UTC time: {current_utc_hour_minute}")

    # --- New Day Reset (ALWAYS process this first for any type of run) ---
    if post_state.get("last_run_date") != today_date:
        print(f"New day detected ({today_date}). Resetting daily post tracker and cycle index.")
        post_state["last_run_date"] = today_date
        post_state["posts_today_hours"] = []
        post_state["current_post_cycle_index"] = 0 # Reset cycle for new day
        write_json("post_state.json", post_state)
        print("Post state reset for new day and saved.")

    # --- Determine Run Type and Slot to Process ---
    current_slot_to_process = -1 # Default to no slot determined
    
    # Check for manual specific overrides first (these exit the script after completion)
    specific_teacher_id = os.getenv("SPECIFIC_TEACHER_ID")
    manual_run_slot_str = os.getenv("MANUAL_RUN_SLOT")
    
    if specific_teacher_id and specific_teacher_id not in ('None', ''):
        print(f"Manual override: Specific Teacher ID requested: {specific_teacher_id}")
        teacher_post_handler = TeacherPost(post_state, post_log)
        post_succeeded = teacher_post_handler.main(specific_teacher_id=specific_teacher_id, post_state=post_state, post_log=post_log)
        write_json("post_state.json", post_state)
        write_json("post_log.json", post_log)
        print(f"Manual run (specific teacher ID) {'successful' if post_succeeded else 'failed'}. State/log saved. Exiting.")
        sys.exit(0)
    elif manual_run_slot_str and manual_run_slot_str not in ('None', ''):
        try:
            manual_slot = int(manual_run_slot_str)
            if 0 <= manual_slot <= (len(POSTING_TIMES_UTC) - 1):
                current_slot_to_process = manual_slot
                print(f"Manual override: Specific Slot requested: {current_slot_to_process}")
            else:
                print(f"Warning: Manual slot '{manual_run_slot_str}' out of range (0-{len(POSTING_TIMES_UTC) - 1}). This manual request will be ignored.")
        except (ValueError, TypeError):
            print(f"Warning: Manual slot '{manual_run_slot_str}' is not a valid number. This manual request will be ignored.")
        # If specific slot requested, we will process it below (unless invalid)
    
    # NEW LOGIC: Manual Force Next Cycle Post
    force_next_cycle_post_env = os.getenv("FORCE_NEXT_CYCLE_POST")
    if current_slot_to_process == -1 and force_next_cycle_post_env and force_next_cycle_post_env.lower() == 'true':
        current_slot_to_process = post_state["current_post_cycle_index"]
        print(f"Manual override: Forcing next post in cycle for slot: {current_slot_to_process}")
    
    # Default logic: Scheduled Run (only if no manual overrides determined a slot)
    if current_slot_to_process == -1:
        expected_slot_index = get_current_slot_index(current_utc_hour_minute)
        if expected_slot_index == -1:
            print(f"No specific post scheduled for {current_utc_hour_minute} UTC. Skipping this run.")
            sys.exit(0) # Exit if no scheduled slot matches
        
        current_slot_to_process = expected_slot_index
        
        # For scheduled runs, ensure we are in the correct sequence.
        if current_slot_to_process != post_state["current_post_cycle_index"]:
            print(f"Scheduled time ({current_utc_hour_minute}, slot {current_slot_to_process}) does not match expected cycle index ({post_state['current_post_cycle_index']}). Skipping this run to maintain sequence.")
            sys.exit(0)

        print(f"Proceeding with post for scheduled slot: {current_slot_to_process}")

    # --- Execute Post based on determined slot ---
    if current_slot_to_process != -1: # Ensure a valid slot was determined by any run type
        current_scheduled_hour = POSTING_TIMES_UTC[current_slot_to_process].split(':')[0]

        # Prevent duplicate posts for the *same hour* on the same day if using cycle/scheduled logic
        # Note: Specific Teacher ID or Specific Slot manual runs would bypass this if they exit early.
        if (os.getenv("FORCE_NEXT_CYCLE_POST") or not os.getenv("MANUAL_RUN_SLOT") and not os.getenv("SPECIFIC_TEACHER_ID")) and \
           current_scheduled_hour in post_state.get("posts_today_hours", []):
            print(f"A post for {POSTING_TIMES_UTC[current_slot_to_process]} UTC (slot {current_slot_to_process}) has already been processed today. Skipping duplicate to avoid double posting.")
            sys.exit(0)

        post_succeeded = False
        if current_slot_to_process % 2 == 0:
            print("It's time for a teacher lesson post!")
            teacher_post_handler = TeacherPost(post_state, post_log)
            post_succeeded = teacher_post_handler.main(current_post_slot=current_slot_to_process, post_state=post_state, post_log=post_log)
        else:
            print("It's time for a random post!")
            random_post_handler = RandomPost(post_state, post_log)
            post_succeeded = random_post_handler.main(current_post_slot=current_slot_to_process, post_state=post_state, post_log=post_log) 
        
        if post_succeeded:
            # Update cycle state if the post itself was successful and it was part of the cycle progression
            # (i.e., not a specific teacher/slot manual override that already exited)
            if not (os.getenv("SPECIFIC_TEACHER_ID") or os.getenv("MANUAL_RUN_SLOT")): # Only update cycle for scheduled/force_next_cycle
                post_state["posts_today_hours"].append(current_scheduled_hour)
                post_state["current_post_cycle_index"] = (current_slot_to_process + 1) % len(POSTING_TIMES_UTC)
                print(f"Advanced cycle index to: {post_state['current_post_cycle_index']}")
            
            write_json("post_state.json", post_state)
            write_json("post_log.json", post_log)
            print("Post state and log updated successfully for run.")
        else:
            print("Post failed or no content generated. State/log not updated for this slot.")

    else:
        print("No valid post slot determined for this run type.")

    sys.exit(0) # Ensure script always exits after processing


if __name__ == "__main__":
    main()
