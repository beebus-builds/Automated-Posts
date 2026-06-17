import os, requests
from dotenv import load_dotenv
from src.image_generator import fulltime_image

load_dotenv()

TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")
PAGE_ID = os.environ.get("FB_PAGE_ID")

def make_post():
    home = "Argentina"
    away = "Algeria"
    sh = 3
    sa = 0
    comp = "FIFA World Cup - Group Stage"
    scorers = [
        "L. Messi 22' (PEN)",
        "L. Martinez 54'",
        "J. Alvarez 82'"
    ]
    
    print("Generating ultra-premium fulltime graphic...")
    img_path = fulltime_image(home, away, sh, sa, scorers, comp)
    print(f"Graphic saved to {img_path}")
    
    msg = f"FULL TIME! 🇦🇷 {home} {sh} - {sa} {away} 🇩🇿\n\nWhat a dominant performance by Argentina to start their World Cup campaign! 🏆🔥\n\n⚽ Scorers:\n"
    for s in scorers:
        msg += f"- {s}\n"
    msg += "\n#WorldCup2026 #Argentina #MatchDay #FootballLive"
    
    print(f"\nPost Caption:\n{msg}\n")
    
    if not TOKEN or "EAAR" not in TOKEN:
        print("Error: FB_PAGE_ACCESS_TOKEN is missing or invalid in .env")
        return
        
    try:
        print("Attempting to post to Facebook...")
        with open(img_path, "rb") as f:
            r = requests.post(
                f"https://graph.facebook.com/v20.0/{PAGE_ID}/photos",
                files={"source": f},
                data={"caption": msg, "access_token": TOKEN},
                timeout=15
            )
        if r.status_code == 200:
            print(f"Successfully posted! FB Post ID: {r.json().get('id')}")
        else:
            print(f"Failed to post to FB: Status Code {r.status_code}")
            print(r.json())
    except Exception as e:
        print(f"Network error: {e}")

if __name__ == "__main__":
    make_post()
