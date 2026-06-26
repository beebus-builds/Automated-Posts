import os, json, datetime, queue, sys
from flask import Flask, request, jsonify, send_file, send_from_directory, Response
from flask_cors import CORS
from dotenv import load_dotenv
import requests

# Ensure src directory is in sys.path for local imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


load_dotenv()

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static"), static_url_path="/static")
CORS(app, resources={r"/api/*": {"origins": "*"}})

TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")
PAGE_ID = os.environ.get("FB_PAGE_ID")

if TOKEN and PAGE_ID:
    try:
        r = requests.get("https://graph.facebook.com/v20.0/me/accounts", params={"access_token": TOKEN}, timeout=10)
        for acc in r.json().get("data", []):
            if acc.get("id") == PAGE_ID:
                pt = acc.get("access_token")
                if pt: TOKEN = pt; break
    except:
        pass

HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "history.json")
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tmp")
os.makedirs(TEMP_DIR, exist_ok=True)

from card_generator import generate_card
from football_api import get_today_matches, match_to_summary
from match_manager import get_all_matches, get_match, get_match_timeline, update_match
from pipeline import PipelineThread

# Start background pipeline
event_clients = []


def publish_event(payload):
    """Fan out pipeline updates to connected browser EventSource clients."""
    dead_clients = []
    for client in list(event_clients):
        try:
            client.put_nowait(payload)
        except Exception:
            dead_clients.append(client)
    for client in dead_clients:
        if client in event_clients:
            event_clients.remove(client)


pipeline = PipelineThread(TOKEN, PAGE_ID, on_update=publish_event)
pipeline.start()


def load_history():
    try:
        with open(HISTORY_FILE) as f:
            return json.load(f)
    except:
        return []


def save_history(h):
    with open(HISTORY_FILE, "w") as f:
        json.dump(h, f, indent=2)


@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "Match Day Poster",
        "pipeline": pipeline.running,
        "pipeline_last_check": pipeline.last_check,
    })


@app.route("/api/matches")
def api_matches():
    """Return all matches (from cache + live API)."""
    raw = get_today_matches()
    matches = [match_to_summary(m) for m in raw]
    # merge in saved state for enriched events
    saved = {m["id"]: m for m in get_all_matches()}
    for m in matches:
        mid = m["id"]
        if mid in saved:
            m["events"] = saved[mid].get("events", [])
    return jsonify(matches)


@app.route("/api/matches/<int:match_id>")
def api_match(match_id):
    m = get_match(match_id)
    if m:
        return jsonify(m)
    # fallback to raw API
    from football_api import get_match as get_raw_match
    raw = get_raw_match(match_id)
    if raw:
        return jsonify(match_to_summary(raw))
    return jsonify({"error": "Match not found"}), 404


@app.route("/api/matches/<int:match_id>/timeline")
def api_timeline(match_id):
    return jsonify(get_match_timeline(match_id))


@app.route("/api/events")
def api_events():
    """Push match and pipeline updates to the browser as soon as they are detected."""
    client = queue.Queue(maxsize=20)
    event_clients.append(client)

    def stream():
        try:
            yield "event: ready\ndata: {\"type\":\"ready\"}\n\n"
            while True:
                try:
                    payload = client.get(timeout=25)
                    yield f"event: {payload.get('type', 'message')}\ndata: {json.dumps(payload)}\n\n"
                except queue.Empty:
                    yield "event: heartbeat\ndata: {\"type\":\"heartbeat\"}\n\n"
        finally:
            if client in event_clients:
                event_clients.remove(client)

    return Response(stream(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


@app.route("/api/history")
def history():
    return jsonify(load_history())



@app.route("/api/pipeline/status")
def pipeline_status():
    return jsonify({
        "running": pipeline.running,
        "last_check": pipeline.last_check,
        "total_posted": len(pipeline.results),
        "recent": pipeline.results[-5:] if pipeline.results else [],
    })


@app.route("/api/pipeline/toggle", methods=["POST"])
def pipeline_toggle():
    global pipeline
    if pipeline.running:
        pipeline.stop()
    else:
        pipeline = PipelineThread(TOKEN, PAGE_ID, on_update=publish_event)
        pipeline.start()
    return jsonify({"running": pipeline.running})


@app.route("/tmp/<filename>")
def serve_temp(filename):
    return send_from_directory(TEMP_DIR, filename)


@app.route("/")
def serve_index():
    return send_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
