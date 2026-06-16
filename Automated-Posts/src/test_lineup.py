import os, requests
from dotenv import load_dotenv
load_dotenv()
from image_generator import lineup_image

TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")
PAGE_ID = os.environ.get("FB_PAGE_ID")

# Mock data for a professional test
home_starters = [
    {"name": "Mike Maignan", "position": "Goalkeeper", "shirtNumber": 1},
    {"name": "Theo Hernandez", "position": "Defender", "shirtNumber": 19},
    {"name": "Dayot Upamecano", "position": "Defender", "shirtNumber": 4},
    {"name": "William Saliba", "position": "Defender", "shirtNumber": 2},
    {"name": "Jules Kounde", "position": "Defender", "shirtNumber": 15},
    {"name": "Aurélien Tchouaméni", "position": "Midfielder", "shirtNumber": 8},
    {"name": "Eduardo Camavinga", "position": "Midfielder", "shirtNumber": 12},
    {"name": "Antoine Griezmann", "position": "Midfielder", "shirtNumber": 7},
    {"name": "Ousmane Dembélé", "position": "Attacker", "shirtNumber": 11},
    {"name": "Kylian Mbappé", "position": "Attacker", "shirtNumber": 10},
    {"name": "Marcus Thuram", "position": "Attacker", "shirtNumber": 9},
]
home_bench = [{"name": "Hugo Lloris", "shirtNumber": 16}]
away_starters = [
    {"name": "Edouard Mendy", "position": "Goalkeeper", "shirtNumber": 16},
    {"name": "Kalidou Koulibaly", "position": "Defender", "shirtNumber": 2},
    {"name": "Ismaïla Sarr", "position": "Attacker", "shirtNumber": 11},
    {"name": "Sadio Mané", "position": "Attacker", "shirtNumber": 10},
]
away_bench = []

img = lineup_image("France", "Senegal", home_starters, home_bench, away_starters, away_bench, "FIFA World Cup")

with open(img, "rb") as f:
    r = requests.post(f"https://graph.facebook.com/v20.0/{PAGE_ID}/photos",
                      files={"source": f},
                      data={"caption": "Lineups are IN! 🇫🇷 vs 🇸🇳\n\nFrance starts with Mbappé and Griezmann up front. Senegal looks strong with Mané. Who takes the 3 points? ⚽", "access_token": TOKEN})
print(r.json())
os.remove(img)
