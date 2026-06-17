from flask import Flask, request, jsonify, render_template
import os, requests
from dotenv import load_dotenv
from .image_generator import (
    live_image, goal_image, card_image, sub_image,
    halftime_image, secondhalf_image, fulltime_image,
    summary_image, schedule_image, lineup_image
)

load_dotenv()

app = Flask(__name__)

TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")
PAGE_ID = os.environ.get("FB_PAGE_ID")


def post_to_fb(img_path, caption):
    if not TOKEN or not PAGE_ID:
        return {"error": "Missing FB_PAGE_ACCESS_TOKEN or FB_PAGE_ID"}
    with open(img_path, "rb") as f:
        r = requests.post(
            f"https://graph.facebook.com/v20.0/{PAGE_ID}/photos",
            files={"source": f},
            data={"caption": caption, "access_token": TOKEN},
            timeout=15,
        )
    if r.status_code == 200:
        return {"id": r.json().get("id"), "post_id": r.json().get("post_id")}
    return {"error": r.json().get("error", {}).get("message", str(r.json()))}


@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/post", methods=["POST"])
def post_event():
    event = request.form.get("event", "")
    home = request.form.get("home", "")
    away = request.form.get("away", "")
    comp = request.form.get("comp", "")

    try:
        if event == "live":
            img = live_image(home, away, comp, request.form.get("time", ""))
            caption = f"The match is underway! {home} vs {away}\n{comp}"

        elif event == "goal":
            sh = int(request.form.get("sh", 0))
            sa = int(request.form.get("sa", 0))
            scorer = request.form.get("scorer", "Unknown")
            minute = request.form.get("minute", "?")
            assist = request.form.get("assist") or None
            img = goal_image(home, away, sh, sa, scorer, minute, assist, comp)
            caption = f"GOAL! {scorer} ({home if request.form.get('team_side') == 'home' else away})\n{home} {sh} - {sa} {away}"
            if assist:
                caption += f"\nAssist: {assist}"

        elif event == "card":
            team = request.form.get("team", home)
            player = request.form.get("player", "Unknown")
            minute = request.form.get("minute", "?")
            card_type = request.form.get("card_type", "YELLOW")
            img = card_image(team, player, minute, card_type, comp)
            label = "Red card!" if card_type.upper() == "RED" else "Yellow card"
            caption = f"{label} {player} ({team})"

        elif event == "sub":
            team = request.form.get("team", home)
            off = request.form.get("off", "Unknown")
            on_p = request.form.get("on", "Unknown")
            minute = request.form.get("minute", "?")
            img = sub_image(team, off, on_p, minute, comp)
            caption = f"Substitution: {off} OFF, {on_p} ON\n{team}"

        elif event == "halftime":
            sh = int(request.form.get("sh", 0))
            sa = int(request.form.get("sa", 0))
            scorers = request.form.get("scorers", "")
            img = halftime_image(home, away, sh, sa, scorers, comp)
            caption = f"Half time: {home} {sh} - {sa} {away}"

        elif event == "secondhalf":
            sh = int(request.form.get("sh", 0))
            sa = int(request.form.get("sa", 0))
            img = secondhalf_image(home, away, sh, sa, comp)
            caption = f"Second half underway! {home} {sh} - {sa} {away}"

        elif event == "fulltime":
            sh = int(request.form.get("sh", 0))
            sa = int(request.form.get("sa", 0))
            scorers_raw = request.form.get("scorers", "")
            scorers_list = [s.strip() for s in scorers_raw.split(",") if s.strip()]
            img = fulltime_image(home, away, sh, sa, scorers_list, comp)
            caption = f"Full time! {home} {sh} - {sa} {away}"

        elif event == "summary":
            sh = int(request.form.get("sh", 0))
            sa = int(request.form.get("sa", 0))
            events_raw = request.form.get("events", "")
            events_list = [e.strip() for e in events_raw.split(",") if e.strip()]
            img = summary_image(home, away, sh, sa, events_list, comp)
            caption = f"Match Summary: {home} {sh} - {sa} {away}"

        else:
            return jsonify({"error": f"Unknown event: {event}"})

        result = post_to_fb(img, caption)
        os.remove(img)

        if "error" in result:
            return jsonify({"error": result["error"], "caption": caption})

        return jsonify({
            "success": True,
            "post_id": result.get("post_id"),
            "caption": caption,
            "fb_url": f"https://www.facebook.com/{PAGE_ID}/posts/{result.get('post_id','').split('_')[-1] if '_' in result.get('post_id','') else result.get('post_id')}"
        })

    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
