import logging
import os
import requests
from concurrent.futures import ThreadPoolExecutor
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
            logger.error("RAPIDAPI_KEY missing!")
            return []

        try:
            logger.info("Polling live matches...")
            res = requests.get(f"{self.base_url}/fixtures", params={"live": "all"}, headers=self.headers, timeout=15)
            if res.status_code == 429:
                logger.error("RATE LIMIT EXCEEDED")
                return []
            if res.status_code != 200:
                logger.error(f"API Error: {res.status_code}")
                return []

            fixtures = res.json().get("response", [])
            events_to_post = []

            for fix in fixtures:
                comp_name = fix["league"]["name"].lower()
                if not any(keyword in comp_name for keyword in ["world cup", "champions league", "premier league", "nepal"]):
                    continue
                
                fix_id = fix["fixture"]["id"]
                events_res = requests.get(f"{self.base_url}/fixtures/events", params={"fixture": fix_id}, headers=self.headers, timeout=15)
                if events_res.status_code == 200:
                    ev_data = events_res.json().get("response", [])
                    for ev in ev_data:
                        ev_type = ev["type"]
                        if ev_type not in ["Goal", "Card"]: continue
                        
                        ev_id = f"real_{fix_id}_{ev['time']}_{ev['player']['id']}"
                        detail_type = "goal" if ev_type == "Goal" else ("red" if "Red" in ev["detail"] else "card")

                        events_to_post.append({
                            "id": ev_id,
                            "event": detail_type,
                            "home": fix["teams"]["home"]["name"],
                            "away": fix["teams"]["away"]["name"],
                            "home_code": fix["teams"]["home"].get("country", {}).get("code", "np"),
                            "away_code": fix["teams"]["away"].get("country", {}).get("code", "in"),
                            "scorer": ev["player"]["name"],
                            "minute": str(ev["time"]),
                            "comp": fix["league"]["name"],
                            "card_type": "RED" if detail_type == "red" else "YELLOW"
                        })
            return events_to_post

        except Exception as e:
            logger.error(f"API Provider Exception: {e}")
            return []

    def get_recent_results(self, limit=10):
        try:
            res = requests.get(f"{self.base_url}/fixtures", params={"last": limit}, headers=self.headers, timeout=15)
            if res.status_code != 200: return []
            
            fixtures = res.json().get("response", [])
            results = []
            for fix in fixtures:
                results.append({
                    "id": f"hist_{fix['fixture']['id']}",
                    "event": "fulltime",
                    "home": fix["teams"]["home"]["name"],
                    "away": fix["teams"]["away"]["name"],
                    "home_code": fix["teams"]["home"].get("country", {}).get("code", "np"),
                    "away_code": fix["teams"]["away"].get("country", {}).get("code", "in"),
                    "sh": str(fix["goals"]["home"]),
                    "sa": str(fix["goals"]["away"]),
                    "comp": fix["league"]["name"]
                })
            return results
        except Exception as e:
            logger.error(f"History Fetch Error: {e}")
            return []

def process_event(event_data):
    """Helper to handle a single event post."""
    from src.app import app, make_event_image, make_caption, post_to_fb
    with app.app_context():
        event_id = event_data["id"]
        if is_event_posted(event_id): return False
        
        try:
            img_path = make_event_image(event_data["event"], event_data)
            if not img_path: return False
            caption = make_caption(event_data["event"], event_data)
            result = post_to_fb(img_path, caption)
            if "error" not in result:
                mark_event_posted(event_id, event_data["event"], caption)
                import os
                if os.path.exists(img_path): os.remove(img_path)
                return True
        except Exception as e:
            logger.error(f"Processing error for {event_id}: {e}")
    return False

def automation_job():
    """Background task using ThreadPoolExecutor for faster processing."""
    logger.info("Checking for new sports events...")
    provider = SportsAPIProvider()
    events = provider.get_latest_events()
    
    if not events:
        logger.info("No new high-value events found.")
        return

    # la-cerne fast-processing: Process multiple goals in parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(process_event, events)

def sync_history_job():
    """Fetch the last 10 games and post them to FB in parallel."""
    provider = SportsAPIProvider()
    recent_games = provider.get_recent_results(limit=10)
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(process_event, recent_games))
    
    posted_count = sum(1 for r in results if r)
    logger.info(f"History Sync complete. Posted {posted_count} games.")
    return posted_count

def start_scheduler():
    scheduler = BackgroundScheduler()
    interval = int(os.environ.get("POLL_INTERVAL_MINUTES", 15))
    scheduler.add_job(automation_job, 'interval', minutes=interval)
    scheduler.start()
    logger.info(f"Turbo-charged Scheduler started. Polling every {interval} min.")
    return scheduler
