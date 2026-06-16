from flask import Flask, jsonify
import os
from dotenv import load_dotenv
from .live import check_and_post, load_state

load_dotenv()

app = Flask(__name__)


@app.route("/")
def index():
    return jsonify({"status": "ok", "service": "Football Live Poster"})


@app.route("/check")
def check():
    try:
        posted = check_and_post()
        return jsonify({"posted": posted, "status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route("/status")
def status():
    state = load_state()
    return jsonify({"matches": len(state), "state": state})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
