import os, json
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app, resources={r"/api/*": {"origins": "*"}})

TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")
PAGE_ID = os.environ.get("FB_PAGE_ID")

# Auto-resolve to Page Access Token
if TOKEN and PAGE_ID:
    try:
        r = requests.get("https://graph.facebook.com/v20.0/me/accounts", params={"access_token": TOKEN}, timeout=10)
        for acc in r.json().get("data", []):
            if acc.get("id") == PAGE_ID:
                pt = acc.get("access_token")
                if pt: TOKEN = pt; break
    except: pass

HISTORY_FILE = "history.json"
def load_history():
    try:
        with open(HISTORY_FILE) as f: return json.load(f)
    except: return []

def save_history(h):
    with open(HISTORY_FILE, "w") as f: json.dump(h, f, indent=2)

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "service": "Match Day Poster"})

@app.route("/api/post", methods=["POST"])
def post():
    """Accept image + caption, post to Facebook. Returns post ID."""
    if not TOKEN or not PAGE_ID:
        return jsonify({"error": "FB_PAGE_ACCESS_TOKEN or FB_PAGE_ID not set"}), 500

    caption = request.form.get("caption", "")
    is_video = request.form.get("video", "").lower() == "true"

    if "image" not in request.files:
        return jsonify({"error": "No image file provided. Send multipart/form-data with field 'image'"}), 400

    f = request.files["image"]
    if f.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    try:
        url = f"https://graph.facebook.com/v20.0/{PAGE_ID}/{'videos' if is_video else 'photos'}"
        data = {"access_token": TOKEN}
        if is_video: data["description"] = caption
        else: data["caption"] = caption

        r = requests.post(url, files={"source": (f.filename, f.stream, f.content_type)}, data=data, timeout=60)
        if r.status_code == 200:
            j = r.json()
            post_id = j.get("post_id", j.get("id", ""))
            fb_url = f"https://www.facebook.com/{PAGE_ID}/posts/{post_id.split('_')[-1] if '_' in post_id else post_id}"

            entry = {"post_id": post_id, "caption": caption, "timestamp": __import__("datetime").datetime.now().isoformat(), "is_video": is_video}
            hist = load_history(); hist.insert(0, entry); save_history(hist[:50])

            return jsonify({"success": True, "post_id": post_id, "fb_url": fb_url, "caption": caption})
        return jsonify({"error": r.json().get("error", {}).get("message", str(r.text))}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/history")
def history():
    return jsonify(load_history())

FRONTEND_DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist")

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path and os.path.exists(os.path.join(FRONTEND_DIST, path)):
        return send_from_directory(FRONTEND_DIST, path)
    index = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.exists(index):
        return send_file(index)
    return jsonify({"error": "Frontend not built. Run: cd frontend && npm run build"}), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
