# post_to_facebook.py (Modified)
import datetime
import sys
import os
# Import the main functions from teacher_post and random_post
import teacher_post
import random_post
from common import read_json, write_json

# Define your desired posting times in 24-hour format (UTC)
# GitHub Actions runs on UTC, so convert your local times to UTC.
# Current EEST (Egypt Standard Time) is UTC+3.
# 6 posts a day:
# Slot 0 (Teacher 1): 8:00 AM EEST -> 5:00 AM UTC
# Slot 1 (Random):    10:00 AM EEST -> 7:00 AM UTC
# Slot 2 (Teacher 2): 12:00 PM EEST -> 9:00 AM UTC
# Slot 3 (Random):    2:00 PM EEST -> 11:00 AM UTC
# Slot 4 (Teacher 3): 4:00 PM EEST -> 1:00 PM UTC (13:00 UTC)
# Slot 5 (Random):    6:00 PM EEST -> 3:00 PM UTC (15:00 UTC)
POSTING_TIMES_UTC = [
    "05:00",  # Slot 0: Teacher 1 or Exam
    "07:00",  # Slot 1: Random Post
    "09:00",  # Slot 2: Teacher 2
    "11:00",  # Slot 3: Random Post
    "13:00",  # Slot 4: Teacher 3
    "15:00"   # Slot 5: Random Post
]

def get_current_slot_index(current_utc_hour_minute: str) -> int:
    """
    Determines the slot index for the current UTC time.
    Returns the 0-indexed slot number (0-5) or -1 if no match.
    """
    for i, time_str in enumerate(POSTING_TIMES_UTC):
        if current_utc_hour_minute == time_str:
            return i
    return -1

def main():
    post_state = read_json("post_state.json")
    post_log = read_json("post_log.json")

    # Initialize current_post_cycle_index for the daily cycle
    post_state.setdefault("current_post_cycle_index", 0) # 0 to 5 for 6 daily slots
    post_state.setdefault("days_since_last_exam", 0)
    post_state.setdefault("teachers", {}) # Ensure this is initialized for teacher_post.py

    # Get current UTC time
    now_utc = datetime.datetime.utcnow()
    current_utc_hour_minute = now_utc.strftime("%H:%M")
    today_date = now_utc.strftime("%Y-%m-%d")

    print(f"Current UTC time: {current_utc_hour_minute}")

    # --- Handle Manual Workflow Dispatch ---
    manual_run_slot_str = os.getenv("MANUAL_RUN_SLOT")
    specific_teacher_id = os.getenv("SPECIFIC_TEACHER_ID") # For manual teacher test

    if manual_run_slot_str:
        # If specific_teacher_id is provided, it's a direct teacher test and overrides slot logic
        if specific_teacher_id and specific_teacher_id not in ('None', ''):
            print(f"Manual trigger: Specific Teacher ID test for {specific_teacher_id}")
            teacher_post.main(specific_teacher_id=specific_teacher_id)
            sys.exit(0)
        
        # Otherwise, it's a manual run for a specific slot in the daily cycle
        try:
            manual_run_slot = int(manual_run_slot_str)
            if not (0 <= manual_run_slot <= 5):
                raise ValueError("Slot out of range (0-5)")
            print(f"Manual trigger: Running for specific slot: {manual_run_slot}")
            
            # This is the key change: call the appropriate script based on the manual slot
            if manual_run_slot % 2 == 0: # Teacher slots (0, 2, 4)
                teacher_post.main(current_post_slot=manual_run_slot)
            else: # Random slots (1, 3, 5)
                random_post.main() # random_post.main doesn't need slot info
            sys.exit(0)

        except (ValueError, TypeError) as e:
            print(f"Warning: Invalid MANUAL_RUN_SLOT '{manual_run_slot_str}'. Error: {e}. Falling back to scheduled logic if no specific teacher ID.")
            # Continue to scheduled logic if manual slot is invalid and no specific teacher ID

    # --- Handle Scheduled Runs ---

    # Reset daily cycle index and posts_today_hours at the start of a new day
    if post_state.get("last_run_date") != today_date:
        print(f"New day detected ({today_date}). Resetting daily post tracker and cycle index.")
        post_state["last_run_date"] = today_date
        post_state["posts_today_hours"] = [] # Track which hours have been posted for today
        post_state["current_post_cycle_index"] = 0 # Reset daily cycle index
        write_json("post_state.json", post_state)

    # Determine the expected slot for the current time
    expected_slot_index = get_current_slot_index(current_utc_hour_minute)

    if expected_slot_index == -1:
        print(f"No specific post scheduled for {current_utc_hour_minute} UTC. Skipping this run.")
        sys.exit(0)

    # Prevent duplicate posts for the same time slot on the same day
    # Check if the exact hour of the current scheduled time has already been processed today.
    current_scheduled_hour = POSTING_TIMES_UTC[expected_slot_index].split(':')[0]
    if current_scheduled_hour in post_state.get("posts_today_hours", []):
        print(f"A post for {current_utc_hour_minute} UTC (slot {expected_slot_index}) has already been triggered today. Skipping duplicate.")
        sys.exit(0)

    # Ensure we are executing the correct slot in sequence, or allow if it's the very first run of the day
    # This prevents out-of-order execution if a cron job fires late for a previous slot.
    if expected_slot_index != post_state["current_post_cycle_index"]:
        print(f"Scheduled time ({current_utc_hour_minute}, slot {expected_slot_index}) does not match expected cycle index ({post_state['current_post_cycle_index']}). Skipping this run to maintain sequence.")
        # Optionally, you could try to process late posts here, but for strict sequential, skip.
        sys.exit(0)

    print(f"Processing scheduled slot {expected_slot_index} for {current_utc_hour_minute} UTC.")

    # Determine post type based on current_post_cycle_index
    if expected_slot_index % 2 == 0: # Teacher posts (0, 2, 4)
        print("It's time for a teacher lesson post (scheduled)!")
        teacher_post.main(current_post_slot=expected_slot_index)
    else: # Random posts (1, 3, 5)
        print("It's time for a random post (scheduled)!")
        random_post.main() # random_post.main handles its own posting

    # After a successful post, update the state
    post_state["posts_today_hours"].append(current_scheduled_hour)
    post_state["current_post_cycle_index"] = (expected_slot_index + 1) % len(POSTING_TIMES_UTC)
    
    # If we just completed the last slot of the day (slot 5), advance exam counter.
    if post_state["current_post_cycle_index"] == 0: # Means all 6 posts completed and cycle reset
        post_state["days_since_last_exam"] = post_state.get("days_since_last_exam", 0) + 1
        print(f"Daily cycle complete. Incrementing days_since_last_exam to: {post_state['days_since_last_exam']}")
    
    write_json("post_state.json", post_state)
    print("Post state updated successfully for scheduled run.")

if __name__ == "__main__":
    main()

