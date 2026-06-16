import requests
import os
import json
import random
from datetime import datetime, timezone
from dotenv import load_dotenv
from image_generator import generate_goal_image, generate_card_image, generate_fulltime_image, generate_live_image

load_dotenv()

FOOTBALL_API_KEY = os.environ.get('FOOTBALL_API_KEY')
FB_PAGE_ACCESS_TOKEN = os.environ.get('FB_PAGE_ACCESS_TOKEN')
FB_PAGE_ID = os.environ.get('FB_PAGE_ID')

STATE_FILE = "match_state.json"

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def get_matches():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    url = f"https://api.football-data.org/v4/matches?dateFrom={today}&dateTo={today}"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json().get("matches", [])

def get_match_detail(match_id):
    url = f"https://api.football-data.org/v4/matches/{match_id}"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    data = r.json()
    return data.get("match", data)

def post_photo_to_facebook(image_path, message):
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/photos"
    with open(image_path, "rb") as f:
        files = {"source": f}
        data = {"caption": message, "access_token": FB_PAGE_ACCESS_TOKEN}
        r = requests.post(url, files=files, data=data)
    r.raise_for_status()
    print(f"Photo posted: {r.json().get('id')}")

def get_intro(event_type):
    options = {
        "GOAL": [
            "GOAL! The net bulges!",
            "They've scored! What a moment!",
            "Into the back of the net!",
        ],
        "RED_CARD": [
            "Sent off! The referee reaches for the red card.",
            "RED CARD! They're down to 10 men.",
        ],
        "YELLOW_CARD": [
            "Booked! Name goes into the referee's notebook.",
            "Yellow card shown for a heavy challenge.",
        ],
        "LIVE": [
            "The match is underway!",
            "Kick-off! The game has started.",
        ],
        "FULL_TIME": [
            "Full time! The final whistle blows.",
            "It's all over! Here's the final result.",
        ],
    }
    return random.choice(options.get(event_type, ["Update!"]))

def process_matches(state, matches):
    posted_any = False

    for m in matches:
        mid = str(m.get("id"))
        status = m.get("status", "")
        home = m.get("homeTeam", {}).get("name", "Home")
        away = m.get("awayTeam", {}).get("name", "Away")
        comp = m.get("competition", {}).get("name", "")
        utc_date = m.get("utcDate", "")

        if mid not in state:
            state[mid] = {
                "last_status": status,
                "posted_goals": [],
                "posted_cards": [],
                "posted_start": False,
                "posted_fulltime": False,
                "home": home,
                "away": away,
                "comp": comp,
            }
        ms = state[mid]

        if status in ("IN_PLAY", "PAUSED") and not ms.get("posted_start"):
            detail = get_match_detail(mid) if status == "IN_PLAY" else m
            kickoff = utc_date.split("T")[1][:5] if "T" in utc_date else ""
            img = generate_live_image(home, away, comp, kickoff)
            msg = f"{get_intro('LIVE')} {home} vs {away}!"
            if comp:
                msg += f"\n{comp}"
            post_photo_to_facebook(img, msg)
            os.remove(img)
            ms["posted_start"] = True
            posted_any = True

        if status in ("IN_PLAY", "PAUSED", "FINISHED"):
            if detail_needed := status in ("IN_PLAY", "PAUSED"):
                detail = get_match_detail(mid) if ms.get("last_status") != status else m
            else:
                detail = get_match_detail(mid)

            score_h = detail.get("score", {}).get("fullTime", {}).get("home")
            score_a = detail.get("score", {}).get("fullTime", {}).get("away")

            goals = detail.get("goals", []) or []
            for g in goals:
                minute = g.get("minute")
                extra = g.get("extraTime")
                key = f"{minute}_{extra}" if extra else str(minute)
                if key not in ms["posted_goals"]:
                    scorer = g.get("scorer", {}).get("name", "Unknown")
                    assist = g.get("assist", {}).get("name") if g.get("assist") else None
                    team_id = g.get("team", {}).get("id")
                    is_home = team_id == m.get("homeTeam", {}).get("id")
                    sh, sa = (score_h, score_a) if score_h is not None else ("?", "?")
                    img = generate_goal_image(
                        home, away, sh if is_home else sh, sa if not is_home else sa,
                        scorer, minute, assist, comp
                    )
                    team_side = home if is_home else away
                    msg = f"{get_intro('GOAL')} {scorer} scores for {team_side}!"
                    msg += f"\n{home} {sh} - {sa} {away}"
                    if assist:
                        msg += f"\nAssist: {assist}"
                    post_photo_to_facebook(img, msg)
                    os.remove(img)
                    ms["posted_goals"].append(key)
                    posted_any = True

            bookings = detail.get("bookings", []) or []
            for b in bookings:
                minute = b.get("minute")
                key = f"{minute}_{b.get('player', {}).get('name', '')}"
                card_type = b.get("card", "YELLOW")
                if key not in ms["posted_cards"]:
                    player = b.get("player", {}).get("name", "Unknown")
                    team_id = b.get("team", {}).get("id")
                    is_home = team_id == m.get("homeTeam", {}).get("id")
                    team_name = home if is_home else away
                    img = generate_card_image(team_name, player, minute, card_type, comp)
                    msg = f"{get_intro(card_type.upper() + '_CARD')} {player} ({team_name})"
                    post_photo_to_facebook(img, msg)
                    os.remove(img)
                    ms["posted_cards"].append(key)
                    posted_any = True

            if status == "FINISHED" and not ms.get("posted_fulltime") and score_h is not None:
                goals_list = []
                for g in goals:
                    s = g.get("scorer", {}).get("name", "")
                    m = g.get("minute", "")
                    goals_list.append(f"{s} {m}'")
                img = generate_fulltime_image(home, away, score_h, score_a, goals_list, comp)
                msg = f"{get_intro('FULL_TIME')} {home} {score_h} - {score_a} {away}"
                post_photo_to_facebook(img, msg)
                os.remove(img)
                ms["posted_fulltime"] = True
                posted_any = True

        ms["last_status"] = status

    return posted_any

def main():
    state = load_state()
    matches = get_matches()
    posted = process_matches(state, matches)
    if posted:
        save_state(state)
        print("Updates posted successfully.")
    else:
        print("No new events to post.")

if __name__ == "__main__":
    main()
