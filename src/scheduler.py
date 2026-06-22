import logging
import os
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from src.database import is_event_posted, mark_event_posted

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Automation")

class SportsAPIProvider:
    """Optimized integration with API-Football via RapidAPI."""
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
            # Optimization: Fetch only the basic live list first
            logger.info("Polling live matches...")
            res = requests.get(f"{self.base_url}/fixtures", params={"live": "all"}, headers=self.headers, timeout=15)
            if res.status_code == 429:
                logger.error("RATE LIMIT EXCEEDED: API is blocking requests. Switch to a paid plan or increase interval.")
                return []
            if res.status_code != 200:
                logger.error(f"API Error: {res.status_code}")
                return []

            fixtures = res.json().get("response", [])
            events_to_post = []

            for fix in fixtures:
                # Only process "High-Value" matches (World Cup, UCL, PL) to save API calls
                comp_name = fix["league"]["name"].lower()
                if not any(keyword in comp_name for keyword in ["world cup", "champions league", "premier league", "nepal"]):
                    continue
                
                fix_id = fix["fixture"]["id"]
                
                # Fetch detailed events ONLY for the filtered matches
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

def automation_job():
    """Background task to poll and post."""
    from src.app import app, make_event_image, make_caption, post_to_fb
    with app.app_context():
        logger.info("Automation Cycle Started...")
        provider = SportsAPIProvider()
        events = provider.get_latest_events()
        
        if not events:
            logger.info("No new high-value events found in this cycle.")
            return

        for event_data in events:
            event_id = event_data["id"]
            if is_event_posted(event_id): continue
            
            logger.info(f"🚨 NEW EVENT: {event_data['event']} by {event_data['scorer']}!")
            try:
                img_path = make_event_image(event_data["event"], event_data)
                if not img_path: continue
                
                caption = make_caption(event_data["event"], event_data)
                result = post_to_fb(img_path, caption)
                
                if "error" not in result:
                    logger.info(f"SUCCESS: Posted {event_id}")
                    mark_event_posted(event_id, event_data["event"], caption)
                else:
                    logger.error(f"FB Error: {result['error']}")
                
                import os
                if os.path.exists(img_path): os.remove(img_path)
                    
            except Exception as e:
                logger.error(f"Automation error: {e}")

def start_scheduler():
    scheduler = BackgroundScheduler()
    interval = int(os.environ.get("POLL_INTERVAL_MINUTES", 15))
    scheduler.add_job(automation_job, 'interval', minutes=interval)
    scheduler.start()
    logger.info(f"Optimized Scheduler started. Polling every {interval} min.")
    return scheduler
