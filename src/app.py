import os, json, requests
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
        if is_video:
            url = f"https://graph.facebook.com/v20.0/{PAGE_ID}/videos"
            with open(img_path, "rb") as f:
                r = requests.post(url, files={"source": f},
                                  data={"description": caption, "access_token": TOKEN}, timeout=60)
        else:
            url = f"https://graph.facebook.com/v20.0/{PAGE_ID}/photos"
            with open(img_path, "rb") as f:
                r = requests.post(url, files={"source": f},
                                  data={"caption": caption, "access_token": TOKEN}, timeout=30)
        if r.status_code == 200:
            return {"id": r.json().get("id"), "post_id": r.json().get("post_id")}
        return {"error": r.json().get("error", {}).get("message", str(r.json()))}
    except Exception as e:
        return {"error": str(e)}


def make_event_image(event, data):
    home = data.get("home", "")
    away = data.get("away", "")
    comp = data.get("comp", "")

    if event == "live":
        return live_image(home, away, comp, data.get("time", ""))

    if event == "goal":
        return goal_image(home, away,
                          int(data.get("sh", 0)), int(data.get("sa", 0)),
                          data.get("scorer", "Unknown"), data.get("minute", "?"),
                          data.get("assist") or None, comp)

    if event == "card":
        return card_image(data.get("team", home), data.get("player", "Unknown"),
                          data.get("minute", "?"), data.get("card_type", "YELLOW"), comp)

    if event == "sub":
        return sub_image(data.get("team", home), data.get("off", "Unknown"),
                         data.get("on", "Unknown"), data.get("minute", "?"), comp)

    if event == "halftime":
        return halftime_image(home, away,
                              int(data.get("sh", 0)), int(data.get("sa", 0)),
                              data.get("scorers", ""), comp)

    if event == "secondhalf":
        return secondhalf_image(home, away,
                                int(data.get("sh", 0)), int(data.get("sa", 0)), comp)

    if event == "fulltime":
        sc = [s.strip() for s in data.get("scorers", "").split(",") if s.strip()]
        return fulltime_image(home, away,
                              int(data.get("sh", 0)), int(data.get("sa", 0)), sc, comp)

    if event == "summary":
        ev = [e.strip() for e in data.get("events", "").split(",") if e.strip()]
        return summary_image(home, away,
                             int(data.get("sh", 0)), int(data.get("sa", 0)), ev, comp)

    if event == "schedule":
        lines = data.get("lines", "").split(",") if data.get("lines") else []
        return schedule_image(lines, data.get("date", ""))

    return None


def make_caption(event, data):
    home = data.get("home", "")
    away = data.get("away", "")

    if event == "live":
        return f"The match is underway! {home} vs {away}\n{data.get('comp', '')}"

    if event == "goal":
        sh, sa = data.get("sh", "0"), data.get("sa", "0")
        side = home if data.get("team_side") == "home" else away
        c = f"GOAL! {data.get('scorer', 'Unknown')} ({side})\n{home} {sh} - {sa} {away}"
        if data.get("assist"): c += f"\nAssist: {data.get('assist')}"
        return c

    if event == "card":
        ct = "Red card!" if data.get("card_type", "").upper() == "RED" else "Yellow card"
        return f"{ct} {data.get('player', 'Unknown')} ({data.get('team', home)})"

    if event == "sub":
        return f"Substitution: {data.get('off', '')} OFF, {data.get('on', '')} ON\n{data.get('team', home)}"

    if event == "halftime":
        return f"Half time: {home} {data.get('sh', '0')} - {data.get('sa', '0')} {away}"

    if event == "secondhalf":
        return f"Second half underway! {home} {data.get('sh', '0')} - {data.get('sa', '0')} {away}"

    if event == "fulltime":
        return f"Full time! {home} {data.get('sh', '0')} - {data.get('sa', '0')} {away}"

    if event == "summary":
        return f"Match Summary: {home} {data.get('sh', '0')} - {data.get('sa', '0')} {away}"

    if event == "schedule":
        return f"Today's matches - {data.get('date', '')}"

    return "Football update!"


def generate_video(img_path, output_path, caption):
    """Generate a short highlight video from image using FFmpeg."""
    import subprocess
    import shutil

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return None

    cmd = [
        ffmpeg, "-y", "-loop", "1", "-i", img_path,
        "-vf", "zoompan=z='if(lte(zoom,1.08),zoom+0.0015,1.08)':d=200:fps=24",
        "-c:v", "libx264", "-t", "8", "-pix_fmt", "yuv420p", "-preset", "fast",
        "-movflags", "+faststart", output_path
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=30)
    if result.returncode != 0:
        return None
    if os.path.exists(output_path) and os.path.getsize(output_path) > 4096:
        return output_path
    return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/manifest.json")
def manifest():
    return send_from_directory("static", "manifest.json")


@app.route("/sw.js")
def service_worker():
    return send_from_directory("static", "sw.js", mimetype="application/javascript")


@app.route("/api/history")
def history():
    return jsonify(load_history())


@app.route("/api/post", methods=["POST"])
def post_event():
    data = request.get_json() or request.form.to_dict()
    event = data.get("event", "")
    include_video = data.get("video", "").lower() == "true"

    if not event:
        return jsonify({"error": "No event type specified"}), 400

    try:
        img = make_event_image(event, data)
        if not img:
            return jsonify({"error": f"Unknown event: {event}"}), 400

        caption = make_caption(event, data)
        result = post_to_fb(img, caption)

        video_result = None
        if include_video and "error" not in result:
            vid_path = img.replace(".png", ".mp4")
            vid = generate_video(img, vid_path, caption)
            if vid:
                vr = post_to_fb(vid, caption + "\n\n#Highlight #Reels", is_video=True)
                if "error" not in vr:
                    video_result = vr
                os.remove(vid)

        os.remove(img)

        entry = {
            "event": event,
            "caption": caption,
            "data": {k: v for k, v in data.items() if k != "event"},
            "result": result,
            "video_result": video_result,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        }
        hist = load_history()
        hist.insert(0, entry)
        save_history(hist[:50])

        if "error" in result:
            return jsonify({"error": result["error"], "caption": caption}), 500

        return jsonify({
            "success": True,
            "post_id": result.get("post_id"),
            "caption": caption,
            "fb_url": f"https://www.facebook.com/{PAGE_ID}/posts/{result.get('post_id','').split('_')[-1] if '_' in result.get('post_id','') else result.get('post_id')}",
            "video_posted": video_result is not None,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
