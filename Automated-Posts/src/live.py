import requests, os, json, time
from datetime import datetime, timezone
from dotenv import load_dotenv
from image_generator import live_image, goal_image, card_image, fulltime_image, schedule_image

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

def check_and_post():
    state = load_state()
    data = api("matches")
    matches = data.get("matches", [])

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
                "last_status": status, "goals": [], "cards": [],
                "started": False, "fulltime": False
            }
        s = state[mid]

        if status in ("IN_PLAY", "PAUSED") and not s["started"]:
            detail = api(f"matches/{mid}").get("match", {})
            kickoff = utc[11:16] if "T" in utc else ""
            img = live_image(home, away, comp, kickoff)
            post_photo(img, f"{INTROS['LIVE']} {home} vs {away}")
            s["started"] = True
            posted = True

        if status in ("IN_PLAY", "PAUSED", "FINISHED"):
            detail = api(f"matches/{mid}").get("match", {})
            sc = detail.get("score", {}).get("fullTime", {})
            sh, sa = sc.get("home"), sc.get("away")

            for g in (detail.get("goals") or []):
                key = f"{g.get('minute')}_{g.get('extraTime') or ''}"
                if key not in s["goals"]:
                    scorer = g.get("scorer", {}).get("name", "Unknown")
                    assist = g.get("assist", {}).get("name") if g.get("assist") else None
                    is_home = g.get("team", {}).get("id") == m.get("homeTeam", {}).get("id")
                    hsc = sh if is_home else (sh if sh else "?")
                    asc = sa if not is_home else (sa if sa else "?")
                    img = goal_image(home, away, hsc, asc, scorer, g.get("minute"), assist, comp)
                    team_side = home if is_home else away
                    msg = f"{INTROS['GOAL']} {scorer} ({team_side})"
                    msg += f"\n{home} {sh or '?'} - {sa or '?'} {away}"
                    if assist: msg += f"\nAssist: {assist}"
                    post_photo(img, msg)
                    s["goals"].append(key)
                    posted = True

            for b in (detail.get("bookings") or []):
                player = b.get("player", {}).get("name", "Unknown")
                key = f"{b.get('minute')}_{player}"
                if key not in s["cards"]:
                    card_type = b.get("card", "YELLOW")
                    is_home = b.get("team", {}).get("id") == m.get("homeTeam", {}).get("id")
                    team_name = home if is_home else away
                    img = card_image(team_name, player, b.get("minute"), card_type, comp)
                    ekey = "RED" if card_type == "RED" else "YELLOW"
                    msg = f"{INTROS[ekey]} {player} ({team_name})"
                    post_photo(img, msg)
                    s["cards"].append(key)
                    posted = True

            if status == "FINISHED" and not s["fulltime"] and sh is not None:
                gl = [f"{g.get('scorer',{}).get('name','')} {g.get('minute','')}'" for g in (detail.get("goals") or [])]
                img = fulltime_image(home, away, sh, sa, gl, comp)
                msg = f"{INTROS['FULLTIME']} {home} {sh} - {sa} {away}"
                post_photo(img, msg)
                s["fulltime"] = True
                posted = True

        s["last_status"] = status

    if posted: save_state(state)
    return posted

if __name__ == "__main__":
    LOOP = os.environ.get("LOOP_MODE", "").lower() == "true"
    if LOOP:
        print("Live tracker running (checking every 6s)...")
        while True:
            try:
                if check_and_post():
                    print("Events posted.")
                else:
                    print("No new events.")
            except Exception as e:
                print(f"Error: {e}")
            time.sleep(6)
    else:
        check_and_post()
