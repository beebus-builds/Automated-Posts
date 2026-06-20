import logging
import os
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from src.database import is_event_posted, mark_event_posted

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Automation")

class SportsAPIProvider:
    """Real-time integration with API-Football via RapidAPI."""
    def __init__(self):
        self.api_key = os.environ.get("RAPIDAPI_KEY")
        self.base_url = "https://api-football-v1.p.rapidapi.com/v3"
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }

    def get_latest_events(self):
        if not self.api_key:
            logger.error("RAPIDAPI_KEY not found in environment variables!")
            return []

        try:
            # 1. Fetch all live fixtures
            logger.info("Fetching live matches...")
            res = requests.get(f"{self.base_url}/fixtures", params={"live": "all"}, headers=self.headers, timeout=15)
            if res.status_code != 200:
                logger.error(f"API Error: {res.status_code}")
                return []

            data = res.json()
            fixtures = data.get("response", [])
            events_to_post = []

            for fix in fixtures:
                fix_id = fix["fixture"]["id"]
                home_team = fix["teams"]["home"]
                away_team = fix["teams"]["away"]
                
                # Extract Goal Events
                goals = fix.get("goals", [])
                for goal in goals:
                    # Unique ID for this goal: matchId_team_minute
                    # API-Football goals usually have a unique ID in the event details, 
                    # but we can construct one from fixture_id and timestamp/minute.
                    # To be safe, we'll fetch detailed events for this fixture.
                    pass

                # Since the live endpoint gives a summary, we fetch detailed events for the match
                events_res = requests.get(f"{self.base_url}/fixtures/events", params={"fixture": fix_id}, headers=self.headers, timeout=15)
                if events_res.status_code == 200:
                    ev_data = events_res.json().get("response", [])
                    for ev in ev_data:
                        ev_type = ev["type"]
                        if ev_type not in ["Goal", "Card"]: continue
                        
                        # Construct Unique Event ID
                        ev_id = f"real_{fix_id}_{ev['time']}_{ev['player']['id']}"
                        
                        # Map API data to our Image Generator format
                        event_map = {
                            "Goal": "goal",
                            "Card": "card"
                        }
                        
                        # Determine if it's a Yellow or Red card
                        detail_type = event_map[ev_type]
                        if ev_type == "Card":
                            detail_type = "red" if "Red" in ev["detail"] else "card"

                        events_to_post.append({
                            "id": ev_id,
                            "event": detail_type,
                            "home": home_team["name"],
                            "away": away_team["name"],
                            "home_code": home_team.get("country", {}).get("code", "np"),
                            "away_code": away_team.get("country", {}).get("code", "in"),
                            "scorer": ev["player"]["name"],
                            "minute": str(ev["time"]),
                            "comp": fix["league"]["name"],
                            "card_type": "RED" if detail_type == "red" else "YELLOW"
                        })

            return events_to_post

        except Exception as e:
            logger.error(f"API Provider Exception: {e}")
            return []

def automation_job():
    """The background task that polls for events and posts to FB."""
    from src.app import app, make_event_image, make_caption, post_to_fb
    with app.app_context():
        logger.info("Checking for real-world football events...")
        provider = SportsAPIProvider()
        events = provider.get_latest_events()
        
        for event_data in events:
            event_id = event_data["id"]
            if is_event_posted(event_id):
                continue
            
            logger.info(f"New Real Event: {event_data['event']} by {event_data['scorer']}!")
            try:
                img_path = make_event_image(event_data["event"], event_data)
                if not img_path: continue
                
                caption = make_caption(event_data["event"], event_data)
                result = post_to_fb(img_path, caption)
                
                if "error" not in result:
                    logger.info(f"Successfully posted {event_id} to Facebook.")
                    mark_event_posted(event_id, event_data["event"], caption)
                else:
                    logger.error(f"FB Error: {result['error']}")
                
                import os
                if os.path.exists(img_path):
                    os.remove(img_path)
                    
            except Exception as e:
                logger.error(f"Automation error: {e}")

def start_scheduler():
    """Initialize and start the background scheduler."""
    scheduler = BackgroundScheduler()
    # Poll every 5 minutes for new events
    scheduler.add_job(automation_job, 'interval', minutes=5)
    scheduler.start()
    logger.info("Real-time Automation Scheduler started.")
    return scheduler
