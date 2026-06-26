import json
import os
from datetime import datetime
from football_api import match_to_summary
from card_generator import generate_card
from enricher import enrich_match

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "match_state.json")
PLAYER_IMAGES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "player_images.json")

def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"matches": {}, "last_check": None}

def save_state(state):
    state["last_check"] = datetime.utcnow().isoformat()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def load_player_images():
    try:
        with open(PLAYER_IMAGES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def match_key(match_id):
    return str(match_id)

def normalize_event_type(event_type):
    if not event_type: return "kickoff"
    text = str(event_type).strip().lower()
    if text in ("yellow", "yellow card"): return "yellow card"
    if text in ("red", "red card"): return "red card"
    if text in ("full-time", "fulltime"): return "full-time"
    if text in ("kickoff", "kick-off"): return "kickoff"
    if text in ("own goal", "penalty"): return "goal"
    if text == "goal": return "goal"
    return text

def event_key(event):
    return "|".join([
        normalize_event_type(event.get("type")),
        str(event.get("player", "") or "").strip().lower(),
        str(event.get("minute", "") or "").strip().lower(),
        str(event.get("score", "") or "").strip(),
    ])

def get_all_matches():
    state = load_state()
    return list(state.get("matches", {}).values())

def get_match(match_id):
    state = load_state()
    return state.get("matches", {}).get(match_key(match_id))

def get_match_timeline(match_id):
    match = get_match(match_id)
    return match.get("events", []) if match else []

def update_match(raw):
    state = load_state()
    key = match_key(raw.get("id"))
    saved = state.get("matches", {}).get(key, {})
    summary = match_to_summary(raw)
    
    # Enrichment
    enriched = enrich_match(summary)
    
    current_events = list(saved.get("events", []))
    existing_keys = {event_key(ev) for ev in current_events}
    new_events = []

    # Score-based goal detection
    if "espn_home_score" in enriched and saved.get("espn_home_score") is not None:
        if enriched["espn_home_score"] > saved["espn_home_score"]:
            new_events.append(build_event("goal", summary, score=f"{enriched['espn_home_score']}-{enriched['espn_away_score']}"))
        if enriched["espn_away_score"] > saved["espn_away_score"]:
            new_events.append(build_event("goal", summary, score=f"{enriched['espn_home_score']}-{enriched['espn_away_score']}"))

    if summary["status"] in ("LIVE", "IN_PLAY", "PAUSED"):
        kickoff = build_event("kickoff", summary, minute="0")
        if event_key(kickoff) not in existing_keys:
            new_events.append(kickoff)
    
    if summary["status"] == "FINISHED":
        full_time = build_event("full-time", summary, minute="90+")
        if event_key(full_time) not in existing_keys:
            new_events.append(full_time)

    current_events.extend(new_events)
    updated = dict(summary)
    updated.update(enriched)
    updated["events"] = current_events
    updated["last_status"] = summary["status"]
    state.setdefault("matches", {})[key] = updated
    save_state(state)
    return new_events, updated

def build_event(event_type, match, player="", minute="", score=""):
    event_type = normalize_event_type(event_type)
    return {
        "type": event_type,
        "player": player or "",
        "minute": minute or "",
        "score": score or f"{match.get('home_score','?')}-{match.get('away_score','?')}",
    }

def generate_card_for_event(match, event):
    home = match.get("home_team", "")
    away = match.get("away_team", "")
    event_type = normalize_event_type(event.get("type", "kickoff"))
    player = event.get("player", "")
    minute = event.get("minute", "")
    score = event.get("score", "")

    if event_type == "goal":
        desc = f"⚽ GOAL! {player if player and player.lower() != 'unknown' else 'A goal'} scored! Score: {score}."
    elif event_type == "full-time":
        desc = f"🏁 FULL TIME: {home} {match.get('home_score')}-{match.get('away_score')} {away}."
    elif event_type == "kickoff":
        desc = f"⏱️ KICK OFF: {home} vs {away} is underway!"
    else:
        desc = f"{home} vs {away} - {event_type.upper()}!"

    player_images = load_player_images()
    image_urls = []
    if player in player_images:
        image_urls = [player_images[player]]

    context = {"match": match, "event": event, "player_image_urls": image_urls}
    buf, img = generate_card(desc, context=context)
    return buf, img, desc
