import os, json, requests, re, tempfile, shutil
from flask import Flask, request, jsonify, render_template, send_file
from dotenv import load_dotenv
from .image_generator import (
    draw_goal_card, draw_yellow_card, draw_red_card, draw_sub_card,
    # Add other draw functions as they are implemented
)

load_dotenv()

app = Flask(__name__, static_folder="static", static_url_path="")

TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")
PAGE_ID = os.environ.get("FB_PAGE_ID")
HISTORY_FILE = "history.json"

def load_history():
    try:
        with open(HISTORY_FILE) as f: return json.load(f)
    except: return []

def save_history(h):
    with open(HISTORY_FILE, "w") as f: json.dump(h, f, indent=2)

def post_to_fb(img_path, caption, is_video=False):
    if not TOKEN or not PAGE_ID:
        return {"error": "Missing FB_PAGE_ACCESS_TOKEN or FB_PAGE_ID"}
    try:
        url = f"https://graph.facebook.com/v20.0/{PAGE_ID}/{'videos' if is_video else 'photos'}"
        with open(img_path, "rb") as f:
            data = {"access_token": TOKEN}
            if is_video: data["description"] = caption
            else: data["caption"] = caption
            r = requests.post(url, files={"source": f}, data=data, timeout=30)
        if r.status_code == 200:
            return {"id": r.json().get("id"), "post_id": r.json().get("post_id")}
        return {"error": r.json().get("error", {}).get("message", str(r.json()))}
    except Exception as e:
        return {"error": str(e)}

def generate_video(img_path, output_path, caption):
    import subprocess, shutil
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg: return None
    safe = "".join(c for c in caption if c.isalnum() or c in " .,!?-:;")[:80]
    cmd = [
        ffmpeg, "-y", "-loop", "1", "-i", img_path,
        "-vf", "zoompan=z='if(lte(zoom,1.08),zoom+0.0015,1.08)':d=200:fps=24",
        "-c:v", "libx264", "-t", "8", "-pix_fmt", "yuv420p", "-preset", "fast", "-movflags", "+faststart", output_path
    ]
    try:
        subprocess.run(cmd, capture_output=True, timeout=30)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 4096:
            return output_path
    except: pass
    return None

def smart_parse(text):
    original = text
    text_lower = text.lower().strip()

    known_teams = [
        "Argentina", "Brazil", "Portugal", "Spain", "France", "Germany",
        "Italy", "Netherlands", "England", "Belgium", "Croatia", "Denmark",
        "Switzerland", "Uruguay", "Colombia", "Japan", "South Korea",
        "Senegal", "Morocco", "Nigeria", "Cameroon", "Ghana", "Algeria",
        "Tunisia", "Egypt", "Ivory Coast", "Congo DR", "Mali", "Burkina Faso",
        "USA", "Mexico", "Canada", "Costa Rica", "Jamaica", "Honduras",
        "Australia", "New Zealand", "Saudi Arabia", "Iran", "Qatar",
        "Turkey", "Poland", "Russia", "Czech Republic", "Sweden", "Norway",
        "Scotland", "Wales", "Austria", "Hungary", "Serbia", "Romania",
        "Ukraine", "Greece", "Chile", "Peru", "Ecuador", "Paraguay",
        "Bolivia", "Venezuela", "South Africa", "Zambia", "Zimbabwe",
        "Angola", "Cape Verde", "Guinea", "Togo", "Benin", "Mozambique",
        "Tanzania", "Uganda", "Kenya", "Ethiopia", "Sudan",
        "Croatia", "Slovakia", "Slovenia", "Bosnia", "Montenegro",
        "Albania", "North Macedonia", "Northern Ireland", "Republic of Ireland",
        "Fiji", "Samoa", "Papua New Guinea", "Tahiti", "Solomon Islands",
        "India", "China", "Thailand", "Vietnam", "Indonesia", "Malaysia",
        "Philippines", "Singapore", "Iraq", "Syria", "Lebanon", "Jordan",
        "Oman", "Bahrain", "Kuwait", "UAE", "Yemen", "Palestine",
        "Korea DPR", "Hong Kong", "Chinese Taipei", "Myanmar", "Cambodia",
        "Laos", "Mongolia", "Bhutan", "Nepal", "Bangladesh", "Sri Lanka",
        "Maldives", "Brunei", "Timor-Leste", "Macau", "Guam",
    ]
    known_lower = {t.lower(): t for t in known_teams}

    data = {"comp": "FIFA World Cup 2026", "sh": 0, "sa": 0, "home": "", "away": ""}

    # Extract teams: support "TeamA vs TeamB", "TeamA v TeamB", "TeamA - TeamB"
    team_delimiters = [r"\s+vs\.?\s+", r"\sv\.\s+", r"\s+&\s+", r"\s+and\s+", r"\s*[-–]\s*"]
    for delim in team_delimiters:
        m = re.search(rf"(\w[\w\s]*?){delim}(\w[\w\s]*?)$", text_lower)
        if m:
            a, b = m.group(1).strip(), m.group(2).strip()
            if a and b:
                data["home"] = known_lower.get(a, a.title())
                data["away"] = known_lower.get(b, b.title())
                break

    # Also try to extract teams from score context: "TeamA 1-0 TeamB"
    if not data["home"] or not data["away"]:
        m = re.match(r"([a-zA-Z\s]+?)\s+(\d+)\s*[-–]\s*(\d+)\s+([a-zA-Z\s]+)", text_lower)
        if m:
            a, sh, sa, b = m.group(1).strip(), m.group(2), m.group(3), m.group(4).strip()
            data["home"] = known_lower.get(a, a.title())
            data["away"] = known_lower.get(b, b.title())
            data["sh"] = int(sh)
            data["sa"] = int(sa)

    # If still no teams, try matching known team names in text
    if not data["home"] or not data["away"]:
        found = [known_lower[t] for t in known_lower if t in text_lower]
        if len(found) >= 2:
            data["home"] = found[0]
            data["away"] = found[1]
        elif len(found) == 1:
            data["home"] = found[0]
            data["away"] = "Opponent"

    # Fallback defaults
    if not data["home"]: data["home"] = "Team 1"
    if not data["away"]: data["away"] = "Team 2"

    # Score
    if "sh" not in data or (data["sh"] == 0 and data["sa"] == 0):
        score_match = re.search(r"(\d+)\s*[-–]\s*(\d+)", text_lower)
        if score_match:
            data["sh"] = int(score_match.group(1))
            data["sa"] = int(score_match.group(2))

    # Minute
    min_match = re.search(r"(\d+)\s*(?:'|min|th\s*minute|minute)", text_lower)
    data["minute"] = min_match.group(1) if min_match else "?"

    # Determine event type
    if any(k in text_lower for k in ["goal", "scored", "scores", "goalll"]):
        event = "goal"
        # Scorer: try "by X", "X scores", "X goal", or capitalized name near minute
        scorer = None
        scorer_patterns = [
            r"(?:by|scored\s*by|goal\s*by)\s+([A-Za-z\s.]+?)(?:\s+\d+|'|\s*$)",
            r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s+(?:scores|goal|with|makes)",
            r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s+\d+",
        ]
        for pat in scorer_patterns:
            m = re.search(pat, original)
            if m:
                cand = m.group(1).strip()
                if len(cand) > 2 and cand.lower() not in ["the", "and", "for", "vs", "goal"]:
                    scorer = cand
                    break
        # Fallback: take capitalized word before the score
        if not scorer or scorer == "Unknown":
            m = re.search(r"([A-Z][a-z]+)\s+\d+\s*[-–]\s*\d+", original)
            if m:
                scorer = m.group(1).strip()
        data["scorer"] = scorer if scorer else "Unknown"
        data["minute"] = data.get("minute", "?")
        assist_match = re.search(r"(?:assist|assisted\s*by)\s+([A-Za-z\s.]+?)(?:\s*$|\s+\d+)", original)
        data["assist"] = assist_match.group(1).strip().title() if assist_match else None
        # Determine which team scored based on who has the lead
        if data["sh"] > data["sa"]:
            data["team_side"] = "home"
        elif data["sa"] > data["sh"]:
            data["team_side"] = "away"
        else:
            data["team_side"] = "home"

    elif any(k in text_lower for k in ["card", "yellow", "red", "booking"]):
        event = "card"
        data["card_type"] = "RED" if "red" in text_lower else "YELLOW"
        # Player name: often capitalized, before "card"/"gets"/"received"/"booking"
        player_match = re.search(r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s+(?:gets|received|shown|card|booking|yellow|red)", original)
        data["player"] = player_match.group(1).strip() if player_match else "Unknown"
        data["minute"] = data.get("minute", "?")
        data["team"] = data["home"]

    elif any(k in text_lower for k in ["sub", "substitution", "replaced", "comes on", "comes off"]):
        event = "sub"
        data["minute"] = data.get("minute", "?")
        data["team"] = data["home"]
        off_match = re.search(r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s+off", original)
        on_match = re.search(r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s+on", original)
        data["off"] = off_match.group(1).strip() if off_match else "Unknown"
        data["on"] = on_match.group(1).strip() if on_match else "Unknown"

    elif re.search(r"half\s*time|halftime|half-time", text_lower):
        event = "halftime"
        data["scorers"] = ""

    elif re.search(r"full\s*time|fulltime|full-time|final\s*score|match\s*ended", text_lower):
        event = "fulltime"
        data["scorers"] = ""

    elif any(k in text_lower for k in ["live", "kickoff", "starts", "underway", "1st half", "first half"]):
        event = "live"
        data["time"] = "Now"

    elif re.search(r"2nd half|second half", text_lower):
        event = "secondhalf"

    else:
        event = "summary"
        data["events"] = original

    return event, data

@app.route("/api/parse", methods=["POST"])
def parse_text():
    text = request.json.get("text", "")
    event, data = smart_parse(text)
    return jsonify({"event": event, "data": data})

@app.route("/")
def index(): return render_template("dashboard.html")

def make_caption(event, data):
    home = data.get("home", "Team 1")
    away = data.get("away", "Team 2")
    sh = data.get("sh", 0)
    sa = data.get("sa", 0)
    captions = {
        "goal": f"GOAL! {data.get('scorer', '?')} {data.get('minute', '?')}'\n{home} {sh} - {sa} {away}" + (f"\nAssist: {data.get('assist')}" if data.get('assist') else ""),
        "card": f"{'RED' if data.get('card_type')=='RED' else 'YELLOW'} CARD\n{data.get('player')} ({data.get('team')})",
        "sub": f"SUBSTITUTION\n{data.get('off')} OFF, {data.get('on')} ON ({data.get('team')})",
        "live": f"The match is underway! {home} vs {away}",
        "halftime": f"HALF TIME\n{home} {sh} - {sa} {away}",
        "secondhalf": f"SECOND HALF\n{home} {sh} - {sa} {away}",
        "fulltime": f"FULL TIME\n{home} {sh} - {sa} {away}",
        "summary": f"MATCH SUMMARY\n{home} {sh} - {sa} {away}",
    }
    return captions.get(event, "Football update!")

def make_event_image(event, data):
    home = data.get("home", "Team 1")
    away = data.get("away", "Team 2")
    comp = data.get("comp", "FIFA World Cup 2026")
    if event == "goal": return draw_goal_card(data.get("scorer", "Unknown"), data.get("minute", "?"), home, None)
    # Temporary placeholders to prevent crashes while I implement the rest:
    return None

@app.route("/api/preview", methods=["POST"])
def preview():
    data = request.get_json()
    if not data: return jsonify({"error": "No data"}), 400
    event = data.get("event", "")
    if not event: return jsonify({"error": "No event"}), 400
    try:
        img_path = make_event_image(event, data)
        if not img_path: return jsonify({"error": "Unknown event"}), 400
        caption = make_caption(event, data)
        out = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        shutil.copy2(img_path, out.name)
        os.remove(img_path)
        return jsonify({"preview_url": f"/api/image/{os.path.basename(out.name)}", "caption": caption, "event": event})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/image/<name>")
def serve_preview(name):
    path = os.path.join(tempfile.gettempdir(), name)
    if not os.path.exists(path): return jsonify({"error": "not found"}), 404
    return send_file(path, mimetype="image/png")

@app.route("/api/post", methods=["POST"])
def post_event():
    data = request.get_json() or request.form.to_dict()
    text = data.get("text")
    include_video = data.get("video", "").lower() == "true"
    if text:
        event, parsed_data = smart_parse(text)
        data = parsed_data
    else:
        event = data.get("event", "")
    if not event: return jsonify({"error": "No event detected"}), 400
    try:
        img = make_event_image(event, data)
        if not img: return jsonify({"error": "Unknown event"}), 400
        caption = make_caption(event, data)
        result = post_to_fb(img, caption)
        video_result = None
        if include_video and "error" not in result:
            vid_path = img.replace(".png", ".mp4")
            vid = generate_video(img, vid_path, caption)
            if vid:
                vr = post_to_fb(vid, caption + "\n\n#Highlight #Reels", is_video=True)
                if "error" not in vr: video_result = vr
                os.remove(vid)
        os.remove(img)
        entry = {"event": event, "caption": caption, "data": data, "result": result, "video_result": video_result, "timestamp": __import__("datetime").datetime.now().isoformat()}
        hist = load_history(); hist.insert(0, entry); save_history(hist[:50])
        if "error" in result: return jsonify({"error": result["error"], "caption": caption}), 500
        return jsonify({"success": True, "post_id": result.get("post_id"), "caption": caption, "fb_url": f"https://www.facebook.com/{PAGE_ID}/posts/{result.get('post_id','').split('_')[-1] if '_' in result.get('post_id','') else result.get('post_id')}", "video_posted": video_result is not None})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/api/history")
def history(): return jsonify(load_history())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
