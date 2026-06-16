import requests
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from image_generator import generate_schedule_image

load_dotenv()

FOOTBALL_API_KEY = os.environ.get('FOOTBALL_API_KEY')
FB_PAGE_ACCESS_TOKEN = os.environ.get('FB_PAGE_ACCESS_TOKEN')
FB_PAGE_ID = os.environ.get('FB_PAGE_ID')

def get_matches():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    url = f"https://api.football-data.org/v4/matches?dateFrom={today}"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json().get("matches", [])

def post_photo(path, message):
    url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/photos"
    with open(path, "rb") as f:
        r = requests.post(url, files={"source": f}, data={"caption": message, "access_token": FB_PAGE_ACCESS_TOKEN})
    r.raise_for_status()
    print("Posted successfully!")

def main():
    matches = get_matches()
    if not matches:
        print("No matches found today.")
        return

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%B %d, %Y")

    lines = []
    seen = set()
    for m in matches:
        home = m.get("homeTeam", {}).get("name", "?")
        away = m.get("awayTeam", {}).get("name", "?")
        key = f"{home}-{away}"
        if key in seen:
            continue
        seen.add(key)
        status = m.get("status", "")
        sc = m.get("score", {}).get("fullTime", {})
        sh, sa = sc.get("home"), sc.get("away")
        utc = m.get("utcDate", "")
        time_str = utc[11:16] if "T" in utc else ""
        if status == "FINISHED" and sh is not None:
            lines.append(f"{home} {sh} - {sa} {away}  FINAL")
        elif status == "IN_PLAY":
            lines.append(f"{home} vs {away}  LIVE")
        else:
            lines.append(f"{home} vs {away}  {time_str}")

    msg_lines = [lines[i] for i in range(min(len(lines), 6))]
    matches_text = "\n".join(msg_lines)

    img = generate_schedule_image(matches_text, date_str)

    message = "Today's football fixtures:\n"
    for l in msg_lines:
        message += f"\n{l}"

    post_photo(img, message)
    os.remove(img)

if __name__ == "__main__":
    main()
