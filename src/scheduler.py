import logging
from apscheduler.schedulers.background import BackgroundScheduler
from src.database import is_event_posted, mark_event_posted
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Automation")

class SportsAPIProvider:
    """Interface for Sports API. Replace get_latest_events with real API call."""
    def get_latest_events(self):
        # DEMO: Simulating a random goal event for testing
        # In production, this would be: requests.get("https://api-football-v1.p.rapidapi.com/...")
        if random.random() < 0.3: # 30% chance of a goal per check
            return [{
                "id": f"demo_goal_{random.randint(1000, 9999)}",
                "event": "goal",
                "home": "Nepal",
                "away": "India",
                "home_code": "np",
                "away_code": "in",
                "scorer": "Bibash Poudel",
                "minute": str(random.randint(1, 90)),
                "comp": "Friendly Match"
            }]
        return []

def automation_job():
    """The background task that polls for events and posts to FB."""
    from src.app import app, make_event_image, make_caption, post_to_fb
    with app.app_context():
        logger.info("Checking for new sports events...")
        provider = SportsAPIProvider()
        events = provider.get_latest_events()
        
        for event_data in events:
            event_id = event_data["id"]
            if is_event_posted(event_id):
                logger.info(f"Event {event_id} already posted. Skipping.")
                continue
            
            logger.info(f"New event detected: {event_data['event']}! Generating post...")
            try:
                img_path = make_event_image(event_data["event"], event_data)
                if not img_path:
                    logger.error("Failed to generate image.")
                    continue
                
                caption = make_caption(event_data["event"], event_data)
                result = post_to_fb(img_path, caption)
                
                if "error" not in result:
                    logger.info(f"Successfully posted event {event_id} to Facebook.")
                    mark_event_posted(event_id, event_data["event"], caption)
                else:
                    logger.error(f"FB Error: {result['error']}")
                
                # Cleanup image
                import os
                if os.path.exists(img_path):
                    os.remove(img_path)
                    
            except Exception as e:
                logger.error(f"Automation error: {e}")

def start_scheduler():
    """Initialize and start the background scheduler."""
    scheduler = BackgroundScheduler()
    # Check for updates every 5 minutes
    scheduler.add_job(automation_job, 'interval', minutes=5)
    scheduler.start()
    logger.info("Automation Scheduler started. Polling every 5 minutes.")
    return scheduler
