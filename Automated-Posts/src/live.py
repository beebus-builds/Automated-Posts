import requests, os, json, time
from datetime import datetime, timezone
from dotenv import load_dotenv
from image_generator import (live_image, goal_image, card_image, sub_image,
    halftime_image, secondhalf_image, fulltime_image, summary_image, schedule_image)

load_dotenv()

KEY = os.environ.get("FOOTBALL_API_KEY")
TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")
PAGE_ID = os.environ.get("FB_PAGE_ID")
STATE_FILE = "match_state.json"

def load_state():
    try:
        with open(STATE_FILE) as f: return json.load(f)
    except: return {}

def save_state(s):
    with open(STATE_FILE, "w") as f: json.dump(s, f, indent=2)

def api(path):
    r = requests.get(f"https://api.football-data.org/v4/{path}", headers={"X-Auth-Token": KEY}, timeout=15)
    r.raise_for_status()
    return r.json()

def post_photo(path, msg):
    with open(path, "rb") as f:
        r = requests.post(f"https://graph.facebook.com/v20.0/{PAGE_ID}/photos",
                          files={"source": f},
                          data={"caption": msg, "access_token": TOKEN})
    r.raise_for_status()
    print(f"  Posted: {r.json().get('id')}")
    os.remove(path)

INTROS = {
    "LIVE": "The match is underway!",
    "GOAL": "GOAL!",
    "RED": "Red card! Sent off!",
    "YELLOW": "Yellow card shown.",
    "FULLTIME": "Full time! Final result:",
}

def process_matches(state, matches):
    posted = False
    for m in matches:
        mid = str(m.get("id"))
        status = m.get("status")
        home = m.get("homeTeam", {}).get("name", "Home")
        away = m.get("awayTeam", {}).get("name", "Away")
        comp = m.get("competition", {}).get("name", "")
        utc = m.get("utcDate", "")

        if mid not in state:
            state[mid] = {
                "last_status": status, "goals": [], "cards": [], "subs": [],
                "started": False, "halftime": False, "secondhalf": False, "fulltime": False,
                "summary_posted": False, "home": home, "away": away,
            }
        s = state[mid]

        if status == "IN_PLAY" and not s["started"]:
            kickoff = utc[11:16] if "T" in utc else ""
            img = live_image(home, away, comp, kickoff)
            post_photo(img, f"{INTROS['LIVE']} {home} vs {away}\n{comp}")
            s["started"] = True; posted = True

        if status in ("IN_PLAY", "PAUSED", "FINISHED"):
            try:
                detail = api(f"matches/{mid}").get("match", {})
            except: continue

            sc = detail.get("score", {}).get("fullTime", {})
            sh, sa = sc.get("home"), sc.get("away")

            for g in (detail.get("goals") or []):
                key = f"{g.get('minute')}_{g.get('extraTime') or ''}"
                if key not in s["goals"]:
                    scorer = g.get("scorer", {}).get("name", "Unknown")
                    assist = g.get("assist", {}).get("name") if g.get("assist") else None
                    is_home = g.get("team", {}).get("id") == m.get("homeTeam", {}).get("id")
                    img = goal_image(home, away, sh, sa, scorer, g.get("minute"), assist, comp)
                    team_side = home if is_home else away
                    msg = f"{INTROS['GOAL']} {scorer} ({team_side})!"
                    msg += f"\n{home} {sh or '?'} - {sa or '?'} {away}"
                    if assist: msg += f"\nAssist: {assist}"
                    post_photo(img, msg)
                    s["goals"].append(key); posted = True

            for b in (detail.get("bookings") or []):
                player = b.get("player", {}).get("name", "Unknown")
                key = f"{b.get('minute')}_{player}"
                if key not in s["cards"]:
                    card_type = b.get("card", "YELLOW")
                    is_home = b.get("team", {}).get("id") == m.get("homeTeam", {}).get("id")
                    team_name = home if is_home else away
                    img = card_image(team_name, player, b.get("minute"), card_type, comp)
                    msg = f"{INTROS[card_type.upper() if card_type.upper() in INTROS else 'YELLOW']} {player} ({team_name})"
                    post_photo(img, msg)
                    s["cards"].append(key); posted = True

            for sub in (detail.get("substitutions") or []):
                player_on = sub.get("playerIn", {}).get("name", "Unknown")
                key = f"{sub.get('minute')}_{player_on}"
                if key not in s["subs"]:
                    is_home = sub.get("team", {}).get("id") == m.get("homeTeam", {}).get("id")
                    team_name = home if is_home else away
                    img = sub_image(team_name, sub.get("playerOut", {}).get("name", "Unknown"), player_on, sub.get("minute"), comp)
                    msg = f"Substitution: {sub.get('playerOut', {}).get('name', 'Player')} OFF, {player_on} ON\n{team_name}"
                    post_photo(img, msg)
                    s["subs"].append(key); posted = True

            if status == "PAUSED" and not s["halftime"]:
                hsc = detail.get("score", {}).get("halfTime", {})
                shh, sah = hsc.get("home"), hsc.get("away")
                if shh is not None:
                    gl = [f"{g.get('scorer',{}).get('name','')} {g.get('minute')}'" for g in (detail.get("goals") or []) if g.get("minute", 0) <= 45]
                    img = halftime_image(home, away, shh, sah, " | ".join(gl), comp)
                    post_photo(img, f"Half time: {home} {shh} - {sah} {away}")
                    s["halftime"] = True; posted = True

            if status == "FINISHED" and not s["fulltime"] and sh is not None:
                gl = [f"{g.get('scorer',{}).get('name','')} {g.get('minute','')}'" for g in (detail.get("goals") or [])]
                img = fulltime_image(home, away, sh, sa, gl, comp)
                msg = f"{INTROS['FULLTIME']} {home} {sh} - {sa} {away}"
                post_photo(img, msg)
                s["fulltime"] = True; posted = True

            if status == "FINISHED" and s["fulltime"] and not s["summary_posted"]:
                events = []
                for g in (detail.get("goals") or []): events.append(f"Goal: {g.get('scorer',{}).get('name','')} {g.get('minute')}'")
                for b in (detail.get("bookings") or []): events.append(f"{b.get('card')} card: {b.get('player',{}).get('name','')} {b.get('minute')}'")
                if not events: events.append("Low-scoring game")
                img = summary_image(home, away, sh, sa, events, comp)
                msg = f"Match Summary: {home} {sh} - {sa} {away}"
                post_photo(img, msg)
                s["summary_posted"] = True; posted = True

        s["last_status"] = status
    return posted

def check_and_post():
    state = load_state()
    try:
        data = api("matches")
        matches = data.get("matches", [])
    except Exception as e:
        print(f"API error: {e}")
        return False
    posted = process_matches(state, matches)
    save_state(state)
    if posted:
        print("Events posted successfully.")
    return posted

if __name__ == "__main__":
    LOOP = os.environ.get("LOOP_MODE", "").lower() == "true"
    if LOOP:
        print("Pro Live Tracker running (checking every 6s)...")
        while True:
            try:
                if check_and_post():
                    print("Events posted.")
            except Exception as e:
                print(f"Error: {e}")
            time.sleep(6)
    else:
        check_and_post()
