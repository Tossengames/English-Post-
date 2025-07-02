import datetime
import sys
import os
import random_post
import teacher_post
from common import read_json, write_json

# Define your desired posting times in 24-hour format (UTC)
# GitHub Actions runs on UTC, so convert your local times to UTC.
# Current EEST (Egypt Standard Time) is UTC+3.
# Example for Egypt:
# Morning (Teacher Lesson) at 9:00 AM EEST -> 6:00 AM UTC
# Midday (Random Post) at 1:00 PM EEST -> 10:00 AM UTC
# Evening (Teacher Lesson) at 6:00 PM EEST -> 3:00 PM UTC
POSTING_TIMES_UTC = {
    "morning": "06:00",  # Corresponds to 9:00 AM EEST
    "midday": "10:00",   # Corresponds to 1:00 PM EEST
    "evening": "15:00"   # Corresponds to 6:00 PM EEST
}

def get_post_type_for_current_time(current_utc_hour_minute: str) -> str:
    """Determines if it's time for a specific post type."""
    if current_utc_hour_minute == POSTING_TIMES_UTC["morning"]:
        return "teacher"
    elif current_utc_hour_minute == POSTING_TIMES_UTC["midday"]:
        return "random"
    elif current_utc_hour_minute == POSTING_TIMES_UTC["evening"]:
        return "teacher"
    return None

def main():
    # Get current UTC time
    now_utc = datetime.datetime.utcnow()
    current_utc_hour_minute = now_utc.strftime("%H:%M")
    current_hour = now_utc.hour

    print(f"Current UTC time: {current_utc_hour_minute}")

    # Manual trigger logic for GitHub Actions workflow_dispatch
    manual_post_type = os.getenv("MANUAL_POST_TYPE")
    if manual_post_type:
        print(f"Manual trigger detected for post type: {manual_post_type}")
        if manual_post_type == "random":
            print("Executing random_post.main()")
            random_post.main()
        elif manual_post_type == "teacher":
            print("Executing teacher_post.main()")
            teacher_post.main()
        elif manual_post_type == "debug": # A useful type for testing without actual posting
            print("Debug mode: Simulating post generation without actual Facebook API call.")
            # You could add logic here to generate content but explicitly NOT call post_to_facebook
            # For now, it will still call post_to_facebook, which will log its 'simulation'
            if random.random() > 0.5: # Simple way to pick one for debug
                print("Debug: Simulating a teacher post generation.")
                teacher_post.main()
            else:
                print("Debug: Simulating a random post generation.")
                random_post.main()
        else:
            print(f"Unknown manual post type: {manual_post_type}")
        sys.exit(0) # Exit after manual post

    # Automatic schedule logic
    post_type = get_post_type_for_current_time(current_utc_hour_minute)

    # Check if a post for this specific hour has already been made today to prevent duplicates
    post_state = read_json("post_state.json")
    today_date = now_utc.strftime("%Y-%m-%d")

    # Initialize or reset post_state for a new day
    if post_state.get("last_run_date") != today_date:
        print(f"New day detected ({today_date}). Resetting daily post tracker.")
        post_state["last_run_date"] = today_date
        post_state["posts_today_hours"] = [] # Store hours for which a post was made
        write_json("post_state.json", post_state) # Save immediately to prevent race conditions on very first run

    made_posts_today_hours = post_state.get("posts_today_hours", [])
    if f"{current_hour:02d}" in made_posts_today_hours: # Format hour with leading zero
        print(f"A post has already been made for hour {current_hour:02d} UTC today. Skipping current scheduled run to prevent duplicates.")
        sys.exit(0)

    if post_type == "teacher":
        print("It's time for a teacher lesson post (scheduled)!")
        teacher_post.main()
        # Log the hour only if the main logic for teacher_post was attempted
        post_state["posts_today_hours"].append(f"{current_hour:02d}")
        write_json("post_state.json", post_state)
    elif post_type == "random":
        print("It's time for a random post (scheduled)!")
        random_post.main()
        # Log the hour only if the main logic for random_post was attempted
        post_state["posts_today_hours"].append(f"{current_hour:02d}")
        write_json("post_state.json", post_state)
    else:
        print(f"No specific post scheduled for {current_utc_hour_minute} UTC. Skipping this run.")
        # Do not update post_state["posts_today_hours"] if no post was attempted for this hour.

if __name__ == "__main__":
    main()

