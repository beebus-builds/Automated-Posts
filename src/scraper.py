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
    if cached:
        return cached
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            j = r.json()
            cache.set(url, j, ttl)
            return j
    except:
        pass
    return None


def find_espn_match(home_team, away_team):
    """Find ESPN event ID for a match by team names."""
    # Full events endpoint has all 72 World Cup matches
    data = _fetch_json(f"{ESPN_BASE}/FIFA.WORLD/events", ttl=60)
    if not data:
        return None

    home_lower = home_team.lower()
    away_lower = away_team.lower()
    home_parts = home_lower.split()
    away_parts = away_lower.split()

    for ev in data.get("events", []):
        competitors = ev.get("competitors", [])
        names = [c.get("displayName", "").lower() for c in competitors]
        # Exact match first
        if any(home_lower in n for n in names) and any(away_lower in n for n in names):
            return ev
        # Partial match
        for n in names:
            if any(p in n for p in home_parts) and any(p in n for p in away_parts):
                return ev
    return None


def get_espn_scores(event_id):
    """Get scores for a match from the events endpoint."""
    data = _fetch_json(f"{ESPN_BASE}/FIFA.WORLD/events", ttl=15)
    if not data:
        return None, None, None

    for ev in data.get("events", []):
        if ev.get("id") == event_id:
            competitors = ev.get("competitors", [])
            status = ev.get("fullStatus", {}).get("type", {}).get("name", "")
            home_score = away_score = None
            for c in competitors:
                try:
                    score_val = int(c.get("score")) if c.get("score") else None
                except (ValueError, TypeError):
                    score_val = None
                if c.get("homeAway") == "home":
                    home_score = score_val
                elif c.get("homeAway") == "away":
                    away_score = score_val
            return home_score, away_score, status
    return None, None, None


def get_all_espn_matches():
    """Get all matches from ESPN with scores and status."""
    data = _fetch_json(f"{ESPN_BASE}/FIFA.WORLD/events", ttl=30)
    if not data:
        return []

    matches = []
    for ev in data.get("events", []):
        competitors = ev.get("competitors", [])
        names = [c.get("displayName", "") for c in competitors]
        scores = {c.get("displayName", ""): c.get("score") for c in competitors}
        status = ev.get("fullStatus", {}).get("type", {}).get("name", "")
        matches.append({
            "id": ev.get("id"),
            "name": ev.get("name"),
            "teams": names,
            "scores": scores,
            "status": status,
        })
    return matches


def enrich_match(match_summary):
    """Enrich a football-data.org match summary with ESPN data."""
    home = match_summary["home_team"]
    away = match_summary["away_team"]
    espn_ev = find_espn_match(home, away)
    if not espn_ev:
        return match_summary

    # Get ESPN score and status
    eid = espn_ev.get("id")
    espn_home_score, espn_away_score, espn_status = get_espn_scores(eid)

    enriched = dict(match_summary)
    if espn_home_score is not None:
        enriched["espn_home_score"] = int(espn_home_score) if espn_home_score else None
        enriched["espn_away_score"] = int(espn_away_score) if espn_away_score else None
    enriched["espn_status"] = espn_status
    enriched["espn_id"] = eid
    return enriched


def merge_scraped_events(existing_events, scraped_events, match_summary):
    """Merge scraped events into match state, avoiding duplicates."""
    new_events = []
    existing_keys = set()
    for ev in existing_events:
        key = f"{ev.get('type')}:{ev.get('player')}:{ev.get('minute')}"
        existing_keys.add(key)

    for ev in scraped_events:
        key = f"{ev.get('type')}:{ev.get('player')}:{ev.get('minute')}"
        if key not in existing_keys:
            # Add score context
            ev["score"] = f"{match_summary.get('home_score', '?')}-{match_summary.get('away_score', '?')}"
            new_events.append(ev)
            existing_keys.add(key)

    return new_events
