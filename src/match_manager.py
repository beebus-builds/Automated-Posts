"""Match state manager — tracks matches, events, and generates cards."""
import json, os
from datetime import datetime
from cache import cache
from card_generator import generate_card
from football_api import match_to_summary
from scraper import enrich_match

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "match_state.json")


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except:
        return {"matches": {}, "last_check": ""}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def get_all_matches():
    state = load_state()
    return list(state.get("matches", {}).values())


def get_match(match_id):
    state = load_state()
    return state.get("matches", {}).get(str(match_id))


def get_match_timeline(match_id):
    match = get_match(match_id)
    if match:
        return match.get("events", [])
    return []


def update_match(raw, enable_scraper=True):
    """Update a match from raw API data + optional web scraper. Returns new events list."""
    state = load_state()
    mid = str(raw.get("id"))
    summary = match_to_summary(raw)

    if mid not in state["matches"]:
        state["matches"][mid] = {**summary, "events": [], "last_status": ""}

    prev = state["matches"][mid]
    new_events = []
    old_status = prev.get("last_status", "")
    new_status = summary.get("status", "")

    # 1. Detect score changes (goals) from API
    old_home, old_away = prev.get("home_score"), prev.get("away_score")
    new_home, new_away = summary.get("home_score"), summary.get("away_score")

    if new_home is not None and old_home is not None:
        if new_home > old_home:
            new_events.append({
                "type": "goal", "team": "home", "minute": summary.get("minute", "?"),
                "player": "Unknown", "score": f"{new_home}-{new_away}", "source": "api",
            })
        if new_away > old_away:
            new_events.append({
                "type": "goal", "team": "away", "minute": summary.get("minute", "?"),
                "player": "Unknown", "score": f"{new_home}-{new_away}", "source": "api",
            })

    # 2. Detect status changes
    if old_status != new_status:
        if new_status in ("LIVE", "IN_PLAY"):
            new_events.append({"type": "kickoff", "team": "", "minute": "0", "player": "", "score": "0-0", "source": "api"})
        elif new_status == "PAUSED":
            new_events.append({"type": "half-time", "team": "", "minute": "45+", "player": "",
                               "score": f"{summary.get('home_score', '?')}-{summary.get('away_score', '?')}", "source": "api"})
        elif new_status == "FINISHED":
            new_events.append({"type": "full-time", "team": "", "minute": "90+", "player": "",
                               "score": f"{summary.get('home_score', '?')}-{summary.get('away_score', '?')}", "source": "api"})

    # 3. Enrich with ESPN data (scores + goal detection via score changes)
    espn_events = []
    if enable_scraper and new_status in ("LIVE", "IN_PLAY", "PAUSED", "FINISHED"):
        enriched = enrich_match(summary)
        if "espn_home_score" in enriched:
            prev_espn_home = prev.get("espn_home_score")
            prev_espn_away = prev.get("espn_away_score")
            if prev_espn_home is not None:
                if enriched["espn_home_score"] > prev_espn_home:
                    espn_events.append({
                        "type": "goal", "team": "home", "minute": enriched.get("minute", "?"),
                        "player": "Unknown", "score": f"{enriched['espn_home_score']}-{enriched['espn_away_score']}",
                        "source": "espn",
                    })
                if enriched["espn_away_score"] > prev_espn_away:
                    espn_events.append({
                        "type": "goal", "team": "away", "minute": enriched.get("minute", "?"),
                        "player": "Unknown", "score": f"{enriched['espn_home_score']}-{enriched['espn_away_score']}",
                        "source": "espn",
                    })
            # Store ESPN scores for next check
            prev["espn_home_score"] = enriched["espn_home_score"]
            prev["espn_away_score"] = enriched["espn_away_score"]
            prev["espn_id"] = enriched.get("espn_id")

    # Merge all new events
    all_new = new_events + espn_events
    existing_events = prev.get("events", [])
    prev["events"] = existing_events + all_new

    # Update stored state
    for k in ["status", "minute", "home_score", "away_score", "home_ht", "away_ht"]:
        if summary.get(k) is not None:
            prev[k] = summary.get(k)
    prev["last_status"] = new_status
    state["last_check"] = datetime.now().isoformat()

    save_state(state)
    return all_new, prev


def generate_card_for_event(match, event):
    """Generate a card image for a match event."""
    home = match.get("home_team", "")
    away = match.get("away_team", "")
    event_type = event.get("type", "kickoff")
    player = event.get("player", "")
    minute = event.get("minute", "")
    score = event.get("score", "")

    # Create detailed caption
    if event_type in ("goal", "own goal", "penalty"):
        desc = f"⚽ GOAL! {player if player and player.lower() != 'unknown' else 'A goal'} scored at {minute}'. Score: {score}. "
    elif event_type == "full-time":
        desc = f"🏁 FULL TIME: {home} {match.get('home_score')}-{match.get('away_score')} {away}. "
    elif event_type == "kickoff":
        desc = f"⏱️ KICK OFF: {home} vs {away} is underway! "
    elif event_type == "half-time":
        desc = f"⏸️ HALF TIME: {home} {match.get('home_ht', '?')}-{match.get('away_ht', '?')} {away}. "
    else:
        desc = f"{home} vs {away} - {event_type.upper()}! "
        if player: desc += f"{player} {minute} - "
        if score: desc += f"Score: {score} - "

    venue = match.get("venue")
    if venue: desc += f"Venue: {venue}. "
    comp = match.get("competition")
    if comp: desc += f"{comp}."

    buf, img = generate_card(desc)
    return buf, img, desc
