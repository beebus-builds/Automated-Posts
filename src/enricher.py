"""Match event enrichment — supplements football-data.org with ESPN data."""
import requests
from cache import cache

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"

def _fetch_json(url, ttl=10):
    cached = cache.get(url)
    if cached: return cached
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            j = r.json()
            cache.set(url, j, ttl)
            return j
    except: pass
    return None

def find_espn_match(home_team, away_team):
    data = _fetch_json(f"{ESPN_BASE}/FIFA.WORLD/events", ttl=60)
    if not data: return None
    home_lower, away_lower = home_team.lower(), away_team.lower()
    home_parts, away_parts = home_lower.split(), away_lower.split()
    for ev in data.get("events", []):
        competitors = ev.get("competitors", [])
        names = [c.get("displayName", "").lower() for c in competitors]
        if any(home_lower in n for n in names) and any(away_lower in n for n in names):
            return ev
        for n in names:
            if any(p in n for p in home_parts) and any(p in n for p in away_parts):
                return ev
    return None

def get_espn_scores(event_id):
    data = _fetch_json(f"{ESPN_BASE}/FIFA.WORLD/events", ttl=15)
    if not data: return None, None, None
    for ev in data.get("events", []):
        if ev.get("id") == event_id:
            competitors = ev.get("competitors", [])
            status = ev.get("fullStatus", {}).get("type", {}).get("name", "")
            home_score = away_score = None
            for c in competitors:
                try:
                    score_val = int(c.get("score")) if c.get("score") else None
                except: score_val = None
                if c.get("homeAway") == "home": home_score = score_val
                elif c.get("homeAway") == "away": away_score = score_val
            return home_score, away_score, status
    return None, None, None

def enrich_match(match_summary):
    home = match_summary["home_team"]
    away = match_summary["away_team"]
    espn_ev = find_espn_match(home, away)
    if not espn_ev: return match_summary
    eid = espn_ev.get("id")
    espn_home_score, espn_away_score, espn_status = get_espn_scores(eid)
    enriched = dict(match_summary)
    if espn_home_score is not None:
        enriched["espn_home_score"] = int(espn_home_score) if espn_home_score else None
        enriched["espn_away_score"] = int(espn_away_score) if espn_away_score else None
    enriched["espn_status"] = espn_status
    enriched["espn_id"] = eid
    return enriched
