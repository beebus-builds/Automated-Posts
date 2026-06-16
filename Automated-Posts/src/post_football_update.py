import requests
import os
import random
import json
from dotenv import load_dotenv

load_dotenv()

FOOTBALL_API_KEY = os.environ.get('FOOTBALL_API_KEY')
FB_PAGE_ACCESS_TOKEN = os.environ.get('FB_PAGE_ACCESS_TOKEN')
FB_PAGE_ID = os.environ.get('FB_PAGE_ID')

TRACKING_FILE = "posted_matches.json"

def load_posted_matches():
    try:
        with open(TRACKING_FILE, "r") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_posted_matches(ids):
    with open(TRACKING_FILE, "w") as f:
        json.dump(list(ids), f)

def get_football_data():
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    url = f"https://api.football-data.org/v4/matches?status=SCHEDULED&dateFrom={today}"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def post_to_facebook(message):
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/feed"
    payload = {
        "message": message,
        "access_token": FB_PAGE_ACCESS_TOKEN
    }
    response = requests.post(url, data=payload)
    response.raise_for_status()
    print("Post successful!")

def get_human_intro():
    intros = [
        "Happy match day, football fans! Here's what's on the menu today:",
        "Grab your drinks, it's time for some football! Check out today's lineup:",
        "Who's excited for today's action? Here are the matches to look out for:",
        "Football never sleeps! Here's today's schedule:"
    ]
    return random.choice(intros)

def get_human_outro():
    outros = [
        "\nWho are you supporting today? Let me know below!",
        "\nAny predictions for these games? Drop them in the comments!",
        "\nWhich match are you most looking forward to? Let's discuss!",
        "\nLet the games begin! Enjoy the action!"
    ]
    return random.choice(outros)

def main():
    posted_ids = load_posted_matches()
    data = get_football_data()
    matches = data.get('matches', [])

    new_matches = [m for m in matches if m.get('id') not in posted_ids]

    if not new_matches:
        print("No new matches to post. All scheduled matches have been posted already.")
        return

    message = f"{get_human_intro()}\n\n"
    for match in new_matches[:5]:
        mid = match.get('id')
        comp = match.get('competition', {}).get('name', 'Unknown League')
        home = match.get('homeTeam', {}).get('name', 'TBD')
        away = match.get('awayTeam', {}).get('name', 'TBD')
        time = match.get('utcDate', '').split('T')[1][:5]

        message += f"{comp}\n{home} vs {away} at {time} UTC\n\n"
        posted_ids.add(mid)

    message += f"{get_human_outro()}\n\n#FootballUpdates #Soccer #MatchDay"

    print(f"Drafted message:\n{message}")
    post_to_facebook(message)
    save_posted_matches(posted_ids)
    print(f"Tracked {len(posted_ids)} matches total.")

if __name__ == "__main__":
    main()
