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
                "last_status": status, "goals": [], "cards": [], "subs": [],
                "started": False, "halftime": False, "secondhalf": False, "fulltime": False,
                "summary_posted": False, "home": home, "away": away
            }
        s = state[mid]

        detail = None
        if status in ("IN_PLAY", "PAUSED", "FINISHED") and status != "TIMED":
            try:
                raw = api(f"matches/{mid}")
                detail = raw.get("match", raw)
            except:
                pass

        # Match started
        if status == "IN_PLAY" and not s["started"]:
            kickoff = utc[11:16] if "T" in utc else ""
            img = live_image(home, away, comp, kickoff)
            post_photo(img, f"The match is underway! {home} vs {away}")
            s["started"] = True; posted = True

        if detail is None:
            s["last_status"] = status
            continue

        sc = detail.get("score", {}).get("fullTime", {})
        sh, sa = sc.get("home"), sc.get("away")

        # Goals
        for g in (detail.get("goals") or []):
            minute = g.get("minute")
            key = f"{minute}_{g.get('extraTime') or ''}"
            if key not in s["goals"]:
                scorer = g.get("scorer", {}).get("name", "Unknown")
                assist = g.get("assist", {}).get("name") if g.get("assist") else None
                is_home = g.get("team", {}).get("id") == m.get("homeTeam", {}).get("id")
                hsc = sh if is_home else (sh if sh else "?")
                asc = sa if not is_home else (sa if sa else "?")
                img = goal_image(home, away, hsc, asc, scorer, minute, assist, comp)
                team_side = home if is_home else away
                msg = f"GOAL! {scorer} puts {team_side} ahead!" if (hsc if is_home else asc) == (hsc if not is_home else asc) else f"GOAL! {scorer} ({team_side})\n{home} {sh or '?'} - {sa or '?'} {away}"
                if assist: msg += f"\nAssist: {assist}"
                post_photo(img, msg)
                s["goals"].append(key); posted = True

        # Cards
        for b in (detail.get("bookings") or []):
            player = b.get("player", {}).get("name", "Unknown")
            minute = b.get("minute")
            key = f"{minute}_{player}"
            if key not in s["cards"]:
                card_type = b.get("card", "YELLOW")
                is_home = b.get("team", {}).get("id") == m.get("homeTeam", {}).get("id")
                team_name = home if is_home else away
                img = card_image(team_name, player, minute, card_type, comp)
                emoji = "RED CARD" if card_type == "RED" else "Yellow card"
                msg = f"{emoji}! {player} ({team_name})"
                post_photo(img, msg)
                s["cards"].append(key); posted = True

        # Substitutions
        for sub in (detail.get("substitutions") or []):
            minute = sub.get("minute")
            player_off = sub.get("playerOut", {}).get("name", "Unknown")
            player_on = sub.get("playerIn", {}).get("name", "Unknown")
            key = f"{minute}_{player_on}"
            if key not in s["subs"]:
                is_home = sub.get("team", {}).get("id") == m.get("homeTeam", {}).get("id")
                team_name = home if is_home else away
                img = sub_image(team_name, player_off, player_on, minute, comp)
                msg = f"Substitution: {player_off} OFF, {player_on} ON\n{team_name}"
                post_photo(img, msg)
                s["subs"].append(key); posted = True

        # Half time
        hsc = detail.get("score", {}).get("halfTime", {})
        hsh, hsa = hsc.get("home"), hsc.get("away")
        if status == "PAUSED" and not s["halftime"] and hsh is not None:
            scorers_text = ""
            goal_list = []
            for g in (detail.get("goals") or []):
                if g.get("minute", 0) <= 45:
                    goal_list.append(f"{g.get('scorer',{}).get('name','')} {g.get('minute')}'")
            scorers_text = "  |  ".join(goal_list) if goal_list else ""
            img = halftime_image(home, away, hsh, hsa, scorers_text, comp)
            msg = f"Half time: {home} {hsh} - {hsa} {away}"
            if scorers_text: msg += f"\nScorers: {scorers_text}"
            post_photo(img, msg)
            s["halftime"] = True; posted = True

        # Second half start
        if status == "IN_PLAY" and s["halftime"] and not s["secondhalf"]:
            img = secondhalf_image(home, away, sh or "?", sa or "?", comp)
            post_photo(img, f"Second half underway! {home} {sh or '?'} - {sa or '?'} {away}")
            s["secondhalf"] = True; posted = True

        # Full time
        if status == "FINISHED" and not s["fulltime"] and sh is not None:
            gl = [f"{g.get('scorer',{}).get('name','')} {g.get('minute','')}'" for g in (detail.get("goals") or [])]
            img = fulltime_image(home, away, sh, sa, gl, comp)
            msg = f"Full time! {home} {sh} - {sa} {away}"
            if gl: msg += f"\nScorers: {', '.join(gl)}"
            post_photo(img, msg)
            s["fulltime"] = True; posted = True

        # Match summary (after full time)
        if status == "FINISHED" and s["fulltime"] and not s["summary_posted"]:
            events = []
            for g in (detail.get("goals") or []):
                events.append(f"Goal: {g.get('scorer',{}).get('name','')} {g.get('minute')}'")
            for b in (detail.get("bookings") or []):
                card_emoji = "Red" if b.get("card") == "RED" else "Yellow"
                events.append(f"{card_emoji} card: {b.get('player',{}).get('name','')} {b.get('minute')}'")
            for sub in (detail.get("substitutions") or []):
                events.append(f"Sub: {sub.get('playerIn',{}).get('name','')} for {sub.get('playerOut',{}).get('name','')} {sub.get('minute')}'")
            if not events: events.append("A quiet match with no major events")
            img = summary_image(home, away, sh, sa, events, comp)
            msg = f"Match Summary:\n{home} {sh} - {sa} {away}"
            for e in events[:6]: msg += f"\n{e}"
            msg += "\n#Football #MatchDay"
            post_photo(img, msg)
            s["summary_posted"] = True; posted = True

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
                    pass
            except Exception as e:
                print(f"Error: {e}")
            time.sleep(6)
    else:
        check_and_post()
