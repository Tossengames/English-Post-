import datetime
import sys
import os
import random_post
import teacher_post
from common import read_json, write_json

# Define your desired posting times in 24-hour format (UTC)
# GitHub Actions runs on UTC, so convert your local times to UTC.
# Example for Egypt EEST (UTC+3):
# Morning (Teacher Lesson) at 9:00 AM EEST -> 6:00 AM UTC
# Midday (Random Post) at 1:00 PM EEST -> 10:00 AM UTC
# Evening (Teacher Lesson) at 6:00 PM EEST -> 3:00 PM UTC
POSTING_TIMES_UTC = {
    "morning": "06:00",  # Example: 6 AM UTC
    "midday": "10:00",   # Example: 10 AM UTC
    "evening": "15:00"   # Example: 3 PM UTC
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
            random_post.main()
        elif manual_post_type == "teacher":
            teacher_post.main()
        else:
            print(f"Unknown manual post type: {manual_post_type}")
        sys.exit(0) # Exit after manual post

    # Automatic schedule logic
    post_type = get_post_type_for_current_time(current_utc_hour_minute)

    # To avoid multiple runs for the same scheduled hour due to minor delays,
    # you might want to add a check in `post_state.json` to see if a post
    # has already been made for this specific time slot today.
    # For simplicity, this example just checks the hour.
    
    post_state = read_json("post_state.json")
    today_date = now_utc.strftime("%Y-%m-%d")
    
    # Initialize post_state if it's a new day
    if post_state.get("last_run_date") != today_date:
        post_state["last_run_date"] = today_date
        post_state["posts_today"] = []
        write_json("post_state.json", post_state)

    # Check if a post for this hour has already been made today
    made_posts_today = post_state.get("posts_today", [])
    if f"{current_hour}" in made_posts_today:
        print(f"A post has already been made for hour {current_hour} UTC today. Skipping.")
        sys.exit(0)

    if post_type == "teacher":
        print("It's time for a teacher lesson post!")
        teacher_post.main()
        post_state["posts_today"].append(f"{current_hour}")
        write_json("post_state.json", post_state)
    elif post_type == "random":
        print("It's time for a random post!")
        random_post.main()
        post_state["posts_today"].append(f"{current_hour}")
        write_json("post_state.json", post_state)
    else:
        print(f"No specific post scheduled for {current_utc_hour_minute} UTC. Skipping.")

if __name__ == "__main__":
    main()

