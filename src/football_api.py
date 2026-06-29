import os, requests
from datetime import datetime, timedelta
from cache import cache

# API Configuration for SportAPI
RAPID_KEY = os.environ.get("RAPIDAPI_KEY", "")
RAPID_HOST = "sportapi7.p.rapidapi.com"
BASE = f"https://{RAPID_HOST}/api/v1"
HEADERS = {
    "x-rapidapi-key": RAPID_KEY,
    "x-rapidapi-host": RAPID_HOST,
    "Content-Type": "application/json"
}

def _get(path, ttl=30):
    url = f"{BASE}{path}"
    cached = cache.get(url)
    if cached: return cached
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json()
            cache.set(url, data, ttl)
            return data
    except Exception as e:
        print(f"API Error: {e}")
    return None

def get_today_matches(comp_code="1"):
    return get_upcoming_matches(days=0, comp_code=comp_code)

def get_upcoming_matches(days=3, comp_code="1"):
    """Fetches upcoming events by looping through the requested days."""
    all_events = []
    for i in range(days + 1):
        date_str = (datetime.utcnow() + timedelta(days=i)).strftime("%Y-%m-%d")
        data = _get(f"/category/{comp_code}/scheduled-events/{date_str}")
        if data and "events" in data:
            all_events.extend(data["events"])
    return all_events

def get_past_matches(days=3, comp_code="1"):
    """Fetches finished events by looping through the requested days."""
    all_events = []
    for i in range(days + 1):
        date_str = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        data = _get(f"/category/{comp_code}/finished-events/{date_str}")
        if data and "events" in data:
            all_events.extend(data["events"])
    return all_events

def get_standings(competition_code="1"):
    return []

def match_to_summary(m):
    return {
        "id": m.get("id"),
        "status": "FINISHED" if m.get("finished") else "SCHEDULED",
        "home_team": m.get("homeTeam", {}).get("name", "Unknown"),
        "away_team": m.get("awayTeam", {}).get("name", "Unknown"),
        "home_score": m.get("homeScore", {}).get("current"),
        "away_score": m.get("awayScore", {}).get("current"),
        "date": m.get("startTimestamp", ""),
    }
