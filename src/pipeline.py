"""Background pipeline: monitors matches, detects events, posts to Facebook."""
import os, threading, time
from datetime import datetime
from football_api import get_today_matches
from match_manager import update_match, generate_card_for_event

FB_PIPELINE_ENABLED = os.environ.get("FB_PIPELINE_ENABLED", "0") == "1"
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "15"))


def check_and_post(token, page_id):
    """Check for match updates, generate cards, post new events."""
    raw_matches = get_today_matches()
    if not raw_matches:
        return []

    posted = []
    for raw in raw_matches:
        status = raw.get("status", "")
        if status not in ("LIVE", "IN_PLAY", "PAUSED", "FINISHED", "TIMED"):
            continue

        try:
            new_events, match = update_match(raw)
            for ev in new_events:
                item = {
                    "event": ev,
                    "match": {
                        "id": match.get("id"),
                        "home_team": match.get("home_team"),
                        "away_team": match.get("away_team"),
                        "competition": match.get("competition"),
                        "status": match.get("status"),
                        "home_score": match.get("home_score"),
                        "away_score": match.get("away_score"),
                    },
                    "detected_at": datetime.now().isoformat(),
                }
                if FB_PIPELINE_ENABLED:
                    if not token or not page_id:
                        item["fb_status"] = "skipped (Facebook credentials missing)"
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
                    item["caption"] = desc
                    item["fb_status"] = r.status_code
                    item["fb_response"] = r.json() if r.status_code == 200 else r.json().get("error", {}).get("message", "")
                else:
                    item["fb_status"] = "skipped (pipeline disabled)"
                posted.append(item)
        except Exception as e:
            posted.append({
                "event": {"type": "error"},
                "match": {"id": raw.get("id")},
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
                            "last_check": datetime.now().isoformat(),
                        })
                self.last_check = datetime.now().isoformat()
                if self.on_update:
                    self.on_update({
                        "type": "pipeline_tick",
                        "last_check": self.last_check,
                        "total_events": len(self.results),
                    })
            except Exception as exc:
                if self.on_update:
                    self.on_update({
                        "type": "pipeline_error",
                        "error": str(exc),
                        "last_check": datetime.now().isoformat(),
                    })
            self._stop_event.wait(POLL_INTERVAL)

    def stop(self):
        self.running = False
        self._stop_event.set()
