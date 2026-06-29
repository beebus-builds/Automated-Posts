"""Background pipeline: monitors matches, detects events, posts to Facebook."""
import os, threading, time
from datetime import datetime
from football_api import get_upcoming_matches, get_past_matches
from match_manager import update_match, generate_card_for_event

FB_PIPELINE_ENABLED = os.environ.get("FB_PIPELINE_ENABLED", "0") == "1"
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "15"))


def check_and_post(token, page_id):
    """Check for match updates, generate cards, post new events."""
    # Fetch both to ensure we catch all status changes
    raw_matches = get_upcoming_matches() + get_past_matches()
    if not raw_matches:
        return []

    posted = []
    for raw in raw_matches:
        try:
            new_events, match = update_match(raw)
            for ev in new_events:
                item = {
                    "event": ev,
                    "match": {
                        "id": match.get("id"),
                        "home_team": match.get("home_team"),
                        "away_team": match.get("away_team"),
                    },
                    "detected_at": datetime.now().isoformat(),
                }
                if FB_PIPELINE_ENABLED:
                    if not token or not page_id:
                        item["fb_status"] = "skipped (credentials missing)"
                        posted.append(item)
                        continue
                    buf, img, desc = generate_card_for_event(match, ev)
                    buf.seek(0)
                    r = __import__("requests").post(
                        f"https://graph.facebook.com/v20.0/{page_id}/photos",
                        data={"access_token": token, "caption": desc},
                        files={"source": ("card.png", buf, "image/png")},
                        timeout=30,
                    )
                    item["fb_status"] = r.status_code
                    item["fb_response"] = r.json() if r.status_code == 200 else r.json().get("error", {}).get("message", "")
                else:
                    item["fb_status"] = "skipped (pipeline disabled)"
                posted.append(item)
        except Exception as e:
            posted.append({
                "event": {"type": "error"},
                "fb_status": str(e),
                "detected_at": datetime.now().isoformat(),
            })

    return posted


class PipelineThread(threading.Thread):
    """Background thread that polls API and processes matches."""

    def __init__(self, token, page_id, on_update=None):
        super().__init__(daemon=True)
        self.token = token
        self.page_id = page_id
        self.on_update = on_update
        self.running = False
        self.last_check = None
        self.results = []
        self._stop_event = threading.Event()

    def run(self):
        self.running = True
        self._stop_event.clear()
        while self.running:
            try:
                result = check_and_post(self.token, self.page_id)
                if result:
                    self.results.extend(result)
                    if self.on_update:
                        self.on_update({
                            "type": "match_updates",
                            "updates": result,
                        })
                self.last_check = datetime.now().isoformat()
            except Exception as exc:
                pass
            self._stop_event.wait(POLL_INTERVAL)

    def stop(self):
        self.running = False
        self._stop_event.set()
