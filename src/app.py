import os, json, requests, re
from flask import Flask, request, jsonify, render_template, send_from_directory
from dotenv import load_dotenv
from .image_generator import (
    live_image, goal_image, card_image, sub_image,
    halftime_image, secondhalf_image, fulltime_image,
    summary_image, schedule_image
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
    text = text.lower()
    data = {"home": "Portugal", "away": "Congo DR", "comp": "FIFA World Cup 2026", "sh": 0, "sa": 0}
    score_match = re.search(r"(\d+)\s*-\s*(\d+)", text)
    if score_match:
        data["sh"], data["sa"] = int(score_match.group(1)), int(score_match.group(2))
    min_match = re.search(r"(\d+)\s*('|min)", text)
    minute = min_match.group(1) if min_match else "?"
    if any(k in text for k in ["goal", "scored", "score"]):
        event = "goal"
        scorer_match = re.search(r"by\s+([a-zA-Z\s]+?)(?=\s+\d+|'|$)", text)
        data["scorer"] = scorer_match.group(1).strip() if scorer_match else "Unknown"
        data["minute"] = minute
        assist_match = re.search(r"assist\s+(?:by\s+)?([a-zA-Z\s]+?)(?=\s+|$)", text)
        data["assist"] = assist_match.group(1).strip() if assist_match else None
        data["team_side"] = "home" if "portugal" in text or "home" in text else "away"
    elif any(k in text for k in ["card", "yellow", "red"]):
        event = "card"
        data["card_type"] = "RED" if "red" in text else "YELLOW"
        player_match = re.search(r"([a-zA-Z\s]+?)\s+(?:gets|received|card)", text)
        data["player"] = player_match.group(1).strip() if player_match else "Unknown"
        data["minute"] = minute
        data["team"] = "Portugal" if "portugal" in text else "Congo DR"
    elif any(k in text for k in ["sub", "substitution", "off", "on"]):
        event = "sub"
        data["minute"] = minute
        data["team"] = "Portugal" if "portugal" in text else "Congo DR"
        off_match = re.search(r"([a-zA-Z\s]+?)\s+off", text)
        on_match = re.search(r"([a-zA-Z\s]+?)\s+on", text)
        data["off"] = off_match.group(1).strip() if off_match else "Unknown"
        data["on"] = on_match.group(1).strip() if on_match else "Unknown"
    elif "half time" in text: event = "halftime"; data["scorers"] = " la la"
    elif "full time" in text: event = "fulltime"; data["scorers"] = " la la"
    elif "live" in text or "start" in text: event = "live"; data["time"] = "Now"
    else: event = "summary"; data["events"] = text
    return event, data

@app.route("/")
def index(): return render_template("index.html")

@app.route("/api/preview")
def preview():
    data = request.args.to_dict()
    event = data.get("event", "")
    if not event: return jsonify({"error": "No event type specified"}), 400
    try:
        img = make_event_image(event, data)
        return send_from_directory(".", img)
    except Exception as e: return jsonify({"error": str(e)}), 500

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
        from .image_generator import (live_image, goal_image, card_image, sub_image, halftime_image, secondhalf_image, fulltime_image, summary_image, schedule_image)
        home, away, comp = data.get("home", "Portugal"), data.get("away", "Congo DR"), data.get("comp", "FIFA World Cup 2026")
        if event == "live": img = live_image(home, away, comp, data.get("time", ""))
        elif event == "goal": img = goal_image(home, away, int(data.get("sh",0)), int(data.get("sa",0)), data.get("scorer", "Unknown"), data.get("minute", "?"), data.get("assist"), comp)
        elif event == "card": img = card_image(data.get("team", home), data.get("player", "Unknown"), data.get("minute", "?"), data.get("card_type", "YELLOW"), comp)
        elif event == "sub": img = sub_image(data.get("team", home), data.get("off", "Unknown"), data.get("on", "Unknown"), data.get("minute", "?"), comp)
        elif event == "halftime": img = halftime_image(home, away, int(data.get("sh",0)), int(data.get("sa",0)), data.get("scorers", ""), comp)
        elif event == "fulltime": img = fulltime_image(home, away, int(data.get("sh",0)), int(data.get("sa",0)), [data.get("scorers", "")], comp)
        elif event == "summary": img = summary_image(home, away, int(data.get("sh",0)), int(data.get("sa",0)), [data.get("events", "")], comp)
        else: return jsonify({"error": "Unknown event"}), 400
        caption = f"{event.upper()} Update: {data.get('scorer', '')} {data.get('minute', '')}' {home} {data.get('sh',0)}-{data.get('sa',0)} {away}"
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
