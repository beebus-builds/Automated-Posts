"""football-data.org API client with caching"""
import os, time, requests
from cache import cache

API_KEY = os.environ.get("FOOTBALL_API_KEY", "0d8e8764bcad4be199bd73e88f71d680")
BASE = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": API_KEY}


def _get(path, ttl=30):
    url = f"{BASE}{path}"
    cached = cache.get(url)
    if cached:
        return cached
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            cache.set(url, r.json(), ttl)
            return r.json()
    except:
        pass
    return None


def get_today_matches():
    """Get all matches for today."""
    data = _get("/matches", ttl=15)
    if not data:
        return []
    return data.get("matches", [])


def get_match(match_id):
    """Get a specific match by ID."""
    return _get(f"/matches/{match_id}", ttl=10)


def get_team_matches(team_id, limit=10):
    """Get recent matches for a team."""
    data = _get(f"/teams/{team_id}/matches?limit={limit}", ttl=60)
    if not data:
        return []
    return data.get("matches", [])


def get_competition_matches(comp_code):
    """Get matches for a competition (e.g. WC for World Cup)."""
    data = _get(f"/competitions/{comp_code}/matches", ttl=30)
    if not data:
        return []
    return data.get("matches", [])


def get_standings(comp_code):
    """Get competition standings."""
    data = _get(f"/competitions/{comp_code}/standings", ttl=120)
    if not data:
        return []
    return data.get("standings", [])


def match_to_summary(m):
    """Convert raw API match to a clean summary dict."""
    sc = m.get("score", {})
    ft = sc.get("fullTime", {}) or {}
    ht = sc.get("halfTime", {}) or {}

    # Extract events if available (scorers)
    events = []
    for scorer in sc.get("scorers", []) or []:
        events.append({
            "type": "goal",
            "player": scorer.get("player", {}).get("name", "Unknown"),
            "minute": scorer.get("minute", 0),
            "team": "home" if scorer.get("team", None) else "away",
        })

    return {
        "id": m.get("id"),
        "status": m.get("status", "SCHEDULED"),
        "minute": m.get("minute", ""),
        "competition": m.get("competition", {}).get("name", ""),
        "comp_emblem": m.get("competition", {}).get("emblem", ""),
        "home_team": m["homeTeam"]["name"],
        "away_team": m["awayTeam"]["name"],
        "home_crest": m["homeTeam"].get("crest", ""),
        "away_crest": m["awayTeam"].get("crest", ""),
        "home_id": m["homeTeam"].get("id"),
        "away_id": m["awayTeam"].get("id"),
        "home_score": ft.get("home"),
        "away_score": ft.get("away"),
        "home_ht": ht.get("home"),
        "away_ht": ht.get("away"),
        "date": m.get("utcDate", ""),
        "venue": m.get("venue", ""),
        "stage": m.get("stage", ""),
        "group": m.get("group", ""),
        "events": events,
    }
