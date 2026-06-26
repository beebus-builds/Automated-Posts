"""football-data.org API client with caching"""
import os, time, requests
from datetime import datetime, timedelta
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


def get_today_matches(comp_code="WC"):
    """Get all matches for today for a competition."""
    data = _get(f"/competitions/{comp_code}/matches", ttl=15)
    if not data:
        return []
    # Filter for today's matches
    today = datetime.utcnow().strftime("%Y-%m-%d")
    matches = data.get("matches", [])
    return [m for m in matches if m["utcDate"].startswith(today)]


def get_match(match_id):
    """Get a specific match by ID."""
    return _get(f"/matches/{match_id}", ttl=10)


def get_matches_by_date_range(date_from, date_to, comp_code="WC"):
    """Get matches in a date range for a competition."""
    params = f"?dateFrom={date_from}&dateTo={date_to}"
    data = _get(f"/competitions/{comp_code}/matches{params}", ttl=30)
    if not data:
        return []
    return data.get("matches", [])


def get_upcoming_matches(days=3, comp_code="WC"):
    """Get upcoming scheduled matches for next N days."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    future = (datetime.utcnow() + timedelta(days=days)).strftime("%Y-%m-%d")
    all_matches = get_matches_by_date_range(today, future, comp_code)
    return [m for m in all_matches if m.get("status") in ["SCHEDULED", "TIMED"]]


def get_past_matches(days=3, comp_code="WC"):
    """Get recent finished matches from last N days."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    past = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    all_matches = get_matches_by_date_range(past, today, comp_code)
    return [m for m in all_matches if m.get("status") == "FINISHED"]


def get_standings(competition_code="WC"):
    """Get standings for a competition (e.g. WC, CL, PL)."""
    data = _get(f"/competitions/{competition_code}/standings", ttl=120)
    if not data:
        return []
    return data.get("standings", [])


def match_to_summary(m):
    """Convert raw API match to a clean summary dict."""
    sc = m.get("score", {})
    ft = sc.get("fullTime", {}) or {}
    ht = sc.get("halfTime", {}) or {}

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
    }
