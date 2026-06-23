import os, json, io, re, datetime
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import requests
from PIL import Image, ImageDraw, ImageFont

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
LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "brand-logo.jpg")
os.makedirs(TEMP_DIR, exist_ok=True)


def load_history():
    try:
        with open(HISTORY_FILE) as f:
            return json.load(f)
    except:
        return []


def save_history(h):
    with open(HISTORY_FILE, "w") as f:
        json.dump(h, f, indent=2)


def generate_card(description):
    SIZE = 1080
    img = Image.new("RGB", (SIZE, SIZE), "#0a0a1a")
    draw = ImageDraw.Draw(img)

    # pitch gradient
    for y in range(SIZE):
        t = y / SIZE
        draw.line([(0, y), (SIZE, y)], fill=(int(10 + t * 30), int(26 + t * 60), int(10 + t * 30)))

    # top bar
    draw.rectangle([0, 0, SIZE, 8], fill="#e63946")

    # bottom bar
    draw.rectangle([0, SIZE - 60, SIZE, SIZE], fill="#0d0d1a")

    # fonts
    try:
        font_lg = ImageFont.truetype("arial.ttf", 72)
        font_md = ImageFont.truetype("arial.ttf", 44)
        font_sm = ImageFont.truetype("arial.ttf", 30)
        font_xs = ImageFont.truetype("arial.ttf", 22)
    except:
        font_lg = font_md = font_sm = font_xs = ImageFont.load_default()

    # parse teams: split on "vs" or "VS"
    parts = re.split(r"\s+vs\s+", description, maxsplit=1, flags=re.IGNORECASE)
    team1 = parts[0].strip() if len(parts) > 1 else ""
    rest = parts[1].strip() if len(parts) > 1 else description
    # extract second team (up to first dash, comma, or newline)
    team2 = ""
    extra_line = rest
    if team1:
        m = re.match(r"([A-Za-z\s]+)", rest)
        if m:
            team2 = m.group(1).strip()
            extra_line = rest[len(team2):].strip().lstrip("–-—, ")
    else:
        team2 = ""

    # VS circle
    if team1 and team2:
        cx, cy = SIZE // 2, 320
        r = 70
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#e63946")
        bbox = draw.textbbox((0, 0), "VS", font=font_md)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw // 2, cy - 20), "VS", fill="white", font=font_md)

        # team names
        for i, (name, x_off) in enumerate([(team1, -1), (team2, 1)]):
            b = draw.textbbox((0, 0), name.upper(), font=font_lg)
            w = b[2] - b[0]
            draw.text((SIZE // 2 + x_off * (140 + w // 2) - (w if x_off < 0 else 0), 230), name.upper(), fill="white", font=font_lg)
    else:
        # no vs found – just render the whole description centered
        bbox = draw.textbbox((0, 0), description.upper(), font=font_lg)
        tw = bbox[2] - bbox[0]
        if tw > SIZE - 120:
            # wrap
            lines = []
            words = description.split()
            line = ""
            for wd in words:
                test = line + " " + wd if line else wd
                bb = draw.textbbox((0, 0), test, font=font_md)
                if bb[2] - bb[0] > SIZE - 120 and line:
                    lines.append(line)
                    line = wd
                else:
                    line = test
            if line:
                lines.append(line)
            y_off = 280
            for line in lines:
                bb = draw.textbbox((0, 0), line.upper(), font=font_md)
                tw = bb[2] - bb[0]
                draw.text(((SIZE - tw) // 2, y_off), line.upper(), fill="white", font=font_md)
                y_off += 60
        else:
            draw.text(((SIZE - tw) // 2, 280), description.upper(), fill="white", font=font_lg)

    # extra info (from rest after team2)
    info_lines = [l.strip() for l in extra_line.split("\n") if l.strip()]
    info_lines = [l for l in info_lines if l]
    if info_lines:
        y_start = 460 if team1 and team2 else 400
        for i, line in enumerate(info_lines[:4]):
            bb = draw.textbbox((0, 0), line, font=font_sm)
            tw = bb[2] - bb[0]
            draw.text(((SIZE - tw) // 2, y_start + i * 55), line, fill="#bbbbbb", font=font_sm)

    # logo
    if os.path.exists(LOGO_PATH):
        logo = Image.open(LOGO_PATH).convert("RGBA")
        ls = 100
        logo = logo.resize((ls, ls), Image.LANCZOS)
        mask = Image.new("L", (ls, ls), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, ls, ls], fill=255)
        logo_rgba = Image.new("RGBA", logo.size, (0, 0, 0, 0))
        logo_rgba.paste(logo)
        img_rgba = img.convert("RGBA")
        img_rgba.paste(logo_rgba, (SIZE // 2 - ls // 2, SIZE - 150), mask)
        img = img_rgba.convert("RGB")
        draw = ImageDraw.Draw(img)

    # brand name
    bb = draw.textbbox((0, 0), "MATCH DAY", font=font_xs)
    tw = bb[2] - bb[0]
    draw.text(((SIZE - tw) // 2, SIZE - 40), "MATCH DAY", fill="#555555", font=font_xs)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf, img


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "service": "Match Day Poster"})


@app.route("/api/post", methods=["POST"])
def post():
    if not TOKEN or not PAGE_ID:
        return jsonify({"error": "FB_PAGE_ACCESS_TOKEN or FB_PAGE_ID not set"}), 500

    description = request.form.get("description", "").strip()
    if not description:
        return jsonify({"error": "No description provided"}), 400

    try:
        buf, img = generate_card(description)

        url = f"https://graph.facebook.com/v20.0/{PAGE_ID}/photos"
        data = {"access_token": TOKEN, "caption": description}
        r = requests.post(url, files={"source": ("card.png", buf, "image/png")}, data=data, timeout=60)

        if r.status_code == 200:
            j = r.json()
            post_id = j.get("post_id", j.get("id", ""))
            pid = post_id.split("_")[-1] if "_" in post_id else post_id
            fb_url = f"https://www.facebook.com/{PAGE_ID}/posts/{pid}"

            entry = {
                "post_id": post_id,
                "caption": description,
                "fb_url": fb_url,
                "timestamp": datetime.datetime.now().isoformat(),
            }
            hist = load_history()
            hist.insert(0, entry)
            save_history(hist[:50])

            # save card to temp for frontend preview
            card_filename = f"card_{post_id}.png"
            img.save(os.path.join(TEMP_DIR, card_filename))
            card_url = f"/tmp/{card_filename}"

            return jsonify({"success": True, "post_id": post_id, "fb_url": fb_url, "caption": description, "card_url": card_url})
        fb_err = r.json().get("error", {})
        fb_msg = fb_err.get("message", str(r.text))
        fb_code = fb_err.get("code", 0)
        if fb_code == 368:
            fb_msg = "Facebook is temporarily limiting posts from this page. This usually resolves within a few hours. Try again later."
        return jsonify({"error": fb_msg}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/history")
def history():
    return jsonify(load_history())


@app.route("/tmp/<filename>")
def serve_temp(filename):
    return send_from_directory(TEMP_DIR, filename)


@app.route("/")
def serve_index():
    return send_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
