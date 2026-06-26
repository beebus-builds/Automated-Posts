"""Force post one test match to verify flags on Facebook"""
import os, json, requests
import sys; sys.path.insert(0, 'src')
from match_manager import load_state, generate_card_for_event
from dotenv import load_dotenv

load_dotenv()

# Token exchange
USER_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")
PAGE_ID = os.environ.get("FB_PAGE_ID")
r = requests.get("https://graph.facebook.com/v20.0/me/accounts", params={"access_token": USER_TOKEN}, timeout=10)
TOKEN = USER_TOKEN
for acc in r.json().get("data", []):
    if acc.get("id") == PAGE_ID:
        TOKEN = acc.get("access_token")
        break

# Create a test match data structure for Portugal vs Colombia
test_match = {
    "home_team": "Portugal",
    "away_team": "Colombia",
    "competition": "FIFA World Cup 2026",
    "status": "SCHEDULED",
    "venue": "Estádio do Dragão"
}
test_event = {"type": "kickoff", "minute": "0", "score": "0-0"}

print("Generating and posting test card...")
buf, img, desc = generate_card_for_event(test_match, test_event)
buf.seek(0)

# Post
data = {"access_token": TOKEN, "caption": "Testing flag display: Portugal vs Colombia graphic."}
files = {"source": ("card.png", buf, "image/png")}
r = requests.post(f"https://graph.facebook.com/v20.0/{PAGE_ID}/photos", 
                  data=data, files=files, timeout=60)

if r.status_code == 200:
    print(f"Success! Post ID: {r.json().get('id')}")
else:
    print(f"Failed: {r.text}")
