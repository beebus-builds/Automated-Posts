import os, re, io, requests
from PIL import Image, ImageDraw, ImageFont

LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "brand-logo.jpg")

# Team → ISO country code mapping
TEAM_CODES = {
    "portugal": "pt", "uzbekistan": "uz", "brazil": "br", "argentina": "ar",
    "france": "fr", "germany": "de", "spain": "es", "italy": "it",
    "england": "gb-eng", "netherlands": "nl", "belgium": "be", "croatia": "hr",
    "uruguay": "uy", "colombia": "co", "chile": "cl", "ecuador": "ec",
    "paraguay": "py", "peru": "pe", "bolivia": "bo", "venezuela": "ve",
    "mexico": "mx", "usa": "us", "canada": "ca", "costarica": "cr",
    "japan": "jp", "south korea": "kr", "saudi arabia": "sa", "iran": "ir",
    "australia": "au", "qatar": "qa", "united arab emirates": "ae",
    "morocco": "ma", "egypt": "eg", "nigeria": "ng", "senegal": "sn",
    "ghana": "gh", "cameroon": "cm", "ivory coast": "ci", "algeria": "dz",
    "tunisia": "tn", "south africa": "za", "denmark": "dk", "sweden": "se",
    "norway": "no", "switzerland": "ch", "poland": "pl", "austria": "at",
    "ukraine": "ua", "russia": "ru", "turkey": "tr", "czech republic": "cz",
    "serbia": "rs", "wales": "gb-wls", "scotland": "gb-sct", "hungary": "hu",
    "romania": "ro", "bulgaria": "bg", "slovakia": "sk", "slovenia": "si",
    "greece": "gr", "ireland": "ie", "iceland": "is",
}

# Nation-specific color schemes
NATION_COLORS = {
    "portugal": ("#FF0000", "#006600"),
    "uzbekistan": ("#0099B5", "#1EB53A"),
    "brazil": ("#009739", "#FFDF00"),
    "argentina": ("#75AADB", "#FFFFFF"),
    "france": ("#002395", "#ED2939"),
    "germany": ("#000000", "#DD0000"),
    "spain": ("#C60B1E", "#FFC400"),
    "italy": ("#008C45", "#CD212A"),
    "england": ("#CF081F", "#FFFFFF"),
    "netherlands": ("#FF6600", "#21468B"),
}

# Event type config
EVENT_STYLES = {
    "goal": {"icon": "⚽", "label": "GOAL", "color": "#FFD700", "glow": "rgba(255,215,0,0.3)"},
    "kickoff": {"icon": "▶", "label": "KICK OFF", "color": "#00FF88", "glow": "rgba(0,255,136,0.3)"},
    "half-time": {"icon": "⏸", "label": "HALF TIME", "color": "#FF8800", "glow": "rgba(255,136,0,0.3)"},
    "halftime": {"icon": "⏸", "label": "HALF TIME", "color": "#FF8800", "glow": "rgba(255,136,0,0.3)"},
    "full-time": {"icon": "⏹", "label": "FULL TIME", "color": "#FF0044", "glow": "rgba(255,0,68,0.3)"},
    "fulltime": {"icon": "⏹", "label": "FULL TIME", "color": "#FF0044", "glow": "rgba(255,0,68,0.3)"},
    "yellow card": {"icon": "🟨", "label": "YELLOW CARD", "color": "#FFDD00", "glow": "rgba(255,221,0,0.3)"},
    "yellow": {"icon": "🟨", "label": "YELLOW CARD", "color": "#FFDD00", "glow": "rgba(255,221,0,0.3)"},
    "red card": {"icon": "🟥", "label": "RED CARD", "color": "#FF0000", "glow": "rgba(255,0,0,0.3)"},
    "red": {"icon": "🟥", "label": "RED CARD", "color": "#FF0000", "glow": "rgba(255,0,0,0.3)"},
    "substitution": {"icon": "🔄", "label": "SUBSTITUTION", "color": "#0088FF", "glow": "rgba(0,136,255,0.3)"},
    "player in": {"icon": "⬆", "label": "PLAYER IN", "color": "#00CC66", "glow": "rgba(0,204,102,0.3)"},
    "player out": {"icon": "⬇", "label": "PLAYER OUT", "color": "#FF6600", "glow": "rgba(255,102,0,0.3)"},
    "penalty": {"icon": "🎯", "label": "PENALTY", "color": "#FF0066", "glow": "rgba(255,0,102,0.3)"},
    "own goal": {"icon": "⚽", "label": "OWN GOAL", "color": "#CC0000", "glow": "rgba(204,0,0,0.3)"},
}


def get_country_code(team_name):
    key = team_name.lower().strip()
    if key in TEAM_CODES:
        return TEAM_CODES[key]
    # try partial match
    for name, code in TEAM_CODES.items():
        if name in key or key in name:
            return code
    return None


def get_nation_colors(team_name):
    key = team_name.lower().strip()
    if key in NATION_COLORS:
        return NATION_COLORS[key]
    for name, colors in NATION_COLORS.items():
        if name in key or key in name:
            return colors
    return None


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def fetch_flag(code, size=(160, 120)):
    if not code:
        return None
    url = f"https://flagcdn.com/w160/{code}.png"
    try:
        headers = {"User-Agent": "MatchDayPoster/1.0"}
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            img = Image.open(io.BytesIO(r.content)).convert("RGBA")
            return img.resize(size, Image.LANCZOS)
        else:
            print(f"Flag fetch status: {r.status_code}")
    except Exception as e:
        print(f"Flag fetch error: {e}")
        pass
    return None


def draw_rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def draw_text_with_glow(draw, xy, text, font, fill="white", glow_color="black", glow_radius=3):
    x, y = xy
    for dx in range(-glow_radius, glow_radius+1):
        for dy in range(-glow_radius, glow_radius+1):
            if dx*dx + dy*dy <= glow_radius*glow_radius:
                draw.text((x+dx, y+dy), text, font=font, fill=glow_color)
    draw.text((x, y), text, font=font, fill=fill)


def parse_description(desc):
    """Parse match description into structured data."""
    result = {
        "team1": "", "team2": "",
        "event_type": "kickoff",
        "event_detail": "",
        "player1": "", "player2": "",
        "minute": "",
        "score": "",
        "extra": "",
        "stadium": "",
        "date": "",
    }

    # Detect event type
    lower = desc.lower()
    for key in ["own goal", "yellow card", "red card", "substitution",
                 "half-time", "halftime", "full-time", "fulltime",
                 "player in", "player out", "penalty", "kickoff", "goal"]:
        if key in lower:
            result["event_type"] = key
            break

    # Extract score (e.g., "1-0", "2-1", "3-2")
    score_m = re.search(r'(\d+)\s*[-–—]\s*(\d+)', desc)
    if score_m:
        result["score"] = f"{score_m.group(1)}-{score_m.group(2)}"

    # Extract minute (e.g., "12'", "45+2'", "90'")
    min_m = re.search(r"(\d+\+?\d*)'", desc)
    if min_m:
        result["minute"] = min_m.group(1) + "'"

    # Split on "vs" or "VS"
    parts = re.split(r"\s+vs\s+", desc, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) == 2:
        result["team1"] = parts[0].strip()
        rest = parts[1].strip()
        # Extract team2 (up to dash, comma, newline)
        m = re.match(r"([A-Za-z\s]+?)(?:[,–—-]|\s+\d)", rest)
        if m:
            result["team2"] = m.group(1).strip()
            extra = rest[len(m.group(1)):].strip().lstrip(",–—- \t")
        else:
            words = rest.split()
            result["team2"] = words[0] if words else ""
            extra = " ".join(words[1:])
        result["extra"] = extra
    else:
        result["extra"] = desc

    # Extract stadium and date from extra
    extra = result["extra"]
    stadium_m = re.search(r'(?:at|@)\s+([A-Za-zÀ-ÿ\s\'\-]+?)(?=[,\.]|\s+\d|$)', extra)
    if stadium_m:
        result["stadium"] = stadium_m.group(1).strip()

    # Extract player names for goals/cards/subs
    # Look for name-like patterns (Capitalized words)
    extra_lower = extra.lower()
    event_type = result["event_type"]
    if event_type in ("goal", "own goal", "penalty"):
        # Try to extract player name from description
        m = re.search(r'([A-Z][a-zà-ÿ]+(?:\s+[A-Z][a-zà-ÿ]+)?)\s*(\d+\+?\d*\'|$)', extra)
        if m:
            result["player1"] = m.group(1).strip()
        # Check for assist
        assist_m = re.search(r'assist(?:ed\s+by)?\s+([A-Z][a-zà-ÿ]+(?:\s+[A-Z][a-zà-ÿ]+)?)', extra, re.I)
        if assist_m:
            result["player2"] = assist_m.group(1).strip()

    elif event_type in ("yellow card", "red card", "yellow", "red"):
        m = re.search(r'([A-Z][a-zà-ÿ]+(?:\s+[A-Z][a-zà-ÿ]+)?)\s*(\d+\+?\d*\'|$)', extra)
        if m:
            result["player1"] = m.group(1).strip()

    elif event_type in ("substitution", "player in", "player out"):
        m = re.search(r'(?:out|off?)\s+([A-Z][a-zà-ÿ]+(?:\s+[A-Z][a-zà-ÿ]+)?)', extra, re.I)
        if m:
            result["player1"] = m.group(1).strip()
        m2 = re.search(r'(?:in|on)\s+([A-Z][a-zà-ÿ]+(?:\s+[A-Z][a-zà-ÿ]+)?)', extra, re.I)
        if m2:
            result["player2"] = m2.group(1).strip()

    return result


def generate_card(description):
    SIZE = 1080
    img = Image.new("RGB", (SIZE, SIZE), "#0a0a1a")
    draw = ImageDraw.Draw(img)

    # Parse description
    info = parse_description(description)

    # Get nation colors
    colors1 = get_nation_colors(info["team1"]) or ("#e63946", "#c1121f")
    colors2 = get_nation_colors(info["team2"]) or ("#1e90ff", "#0a58ca")

    # Event style
    ev = EVENT_STYLES.get(info["event_type"], EVENT_STYLES["kickoff"])

    # ============ BACKGROUND ============
    # Dark cinematic base
    bg = Image.new("RGB", (SIZE, SIZE), (8, 18, 30))
    # Warm spotlight (center glow)
    glow = Image.new("RGBA", (SIZE, SIZE), (0,0,0,0))
    gdraw = ImageDraw.Draw(glow)
    for r in range(400, 0, -8):
        fade = 1 - r/400
        gdraw.ellipse([SIZE//2 - r, 250 - r, SIZE//2 + r, 250 + r],
                      fill=(60, 50, 80, int(20 * fade)))
    bg = Image.alpha_composite(bg.convert("RGBA"), glow).convert("RGB")
    img = bg
    draw = ImageDraw.Draw(img)

    # Top and bottom dark bars
    draw.rectangle([0, 0, SIZE, 12], fill=hex_to_rgb(ev["color"]))
    draw.rectangle([0, SIZE-70, SIZE, SIZE], fill="#08081a")

    # Side light streaks
    for i in range(4):
        x = 60 + i * 320
        streak = Image.new("RGBA", (SIZE, SIZE), (0,0,0,0))
        sdraw = ImageDraw.Draw(streak)
        for h in range(100):
            fade = (1 - h/100) * 0.08
            x_off = int(h * 0.5)
            color = (*hex_to_rgb(colors1[0] if i % 2 == 0 else colors2[0]), int(255 * fade))
            sdraw.line([(x - 60 + x_off, h*10), (x + 60 - x_off, h*10)], fill=color, width=2)
        img = Image.alpha_composite(img.convert("RGBA"), streak).convert("RGB")
        draw = ImageDraw.Draw(img)

    # ============ FONTS ============
    try:
        font_lg = ImageFont.truetype("arial.ttf", 80)
        font_md = ImageFont.truetype("arial.ttf", 48)
        font_sm = ImageFont.truetype("arial.ttf", 32)
        font_xs = ImageFont.truetype("arial.ttf", 24)
        font_badge = ImageFont.truetype("arial.ttf", 36)
    except:
        font_lg = font_md = font_sm = font_xs = font_badge = ImageFont.load_default()

    # ============ EVENT BADGE ============
    badge_text = f"{ev['icon']} {ev['label']}"
    badge_color = hex_to_rgb(ev["color"])
    bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw = bbox[2] - bbox[0] + 60
    bh = bbox[3] - bbox[1] + 24
    bx = (SIZE - bw) // 2
    by = 40
    draw_rounded_rect(draw, (bx, by, bx+bw, by+bh), radius=30, fill=badge_color)
    draw.text(((SIZE - (bbox[2] - bbox[0]))//2, by + (bh - (bbox[3]-bbox[1]))//2 - 4),
              badge_text, font=font_badge, fill="white")

    # ============ FLAGS ============
    flag_size = (200, 150)
    code1 = get_country_code(info["team1"])
    code2 = get_country_code(info["team2"])

    flag1 = fetch_flag(code1, flag_size) if code1 else None
    flag2 = fetch_flag(code2, flag_size) if code2 else None

    # Create flag containers with rounded corners
    flag_y = 150
    gap = 280
    flag_x1 = (SIZE - gap) // 2 - flag_size[0]
    flag_x2 = (SIZE + gap) // 2

    # Flag backgrounds
    for fx, fc in [(flag_x1, colors1), (flag_x2, colors2)]:
        draw_rounded_rect(draw, (fx-10, flag_y-10, fx+flag_size[0]+10, flag_y+flag_size[1]+10),
                         radius=16, fill=hex_to_rgb(fc[0]))

    if flag1:
        img.paste(flag1, (flag_x1, flag_y), flag1)
    else:
        # Draw team initial as fallback
        init = info["team1"][:2].upper() if info["team1"] else "?"
        bbox = draw.textbbox((0, 0), init, font=font_lg)
        dw = bbox[2]-bbox[0]
        draw.text((flag_x1 + (flag_size[0]-dw)//2, flag_y + 40), init, font=font_lg, fill="white")

    if flag2:
        img.paste(flag2, (flag_x2, flag_y), flag2)
    else:
        init = info["team2"][:2].upper() if info["team2"] else "?"
        bbox = draw.textbbox((0, 0), init, font=font_lg)
        dw = bbox[2]-bbox[0]
        draw.text((flag_x2 + (flag_size[0]-dw)//2, flag_y + 40), init, font=font_lg, fill="white")

    # VS circle between flags
    vs_cx, vs_cy = SIZE // 2, flag_y + flag_size[1] // 2
    vs_r = 55
    draw.ellipse([vs_cx-vs_r, vs_cy-vs_r, vs_cx+vs_r, vs_cy+vs_r],
                 fill=hex_to_rgb(ev["color"]))
    # VS glow
    for gr in range(vs_r+10, vs_r+30, 4):
        draw.ellipse([vs_cx-gr, vs_cy-gr, vs_cx+gr, vs_cy+gr],
                     outline=(255,255,255, int(20 * (1 - (gr-vs_r-10)/20))), width=2)
    bbox = draw.textbbox((0, 0), "VS", font=font_md)
    vw = bbox[2] - bbox[0]
    draw.text((vs_cx - vw//2, vs_cy - 22), "VS", font=font_md, fill="white")

    # ============ TEAM NAMES ============
    name_y = flag_y + flag_size[1] + 30
    team1_name = info["team1"].upper() if info["team1"] else "HOME"
    team2_name = info["team2"].upper() if info["team2"] else "AWAY"

    for name, cx in [(team1_name, flag_x1 + flag_size[0]//2),
                      (team2_name, flag_x2 + flag_size[0]//2)]:
        bbox = draw.textbbox((0, 0), name, font=font_sm)
        nw = bbox[2] - bbox[0]
        draw.text_with_glow = lambda: None  # skip glow for team names, just draw
        draw.text((cx - nw//2, name_y), name, font=font_sm, fill="white")

    # ============ SCORE LINE (if exists) ============
    score_y = name_y + 55
    if info["score"]:
        bbox = draw.textbbox((0, 0), info["score"], font=font_lg)
        sw = bbox[2] - bbox[0]
        draw_text_with_glow(draw, ((SIZE - sw)//2, score_y), info["score"],
                           font=font_lg, fill=ev["color"], glow_color="#000000")

    # ============ EVENT DETAILS ============
    detail_y = score_y + 80 if info["score"] else score_y + 40

    # Player name + minute
    if info["player1"]:
        detail_text = info["player1"]
        if info["minute"]:
            detail_text += f" {info['minute']}"
        if info["event_type"] in ("goal", "own goal", "penalty") and info["player1"]:
            detail_text = f"⚽ {detail_text}"
        bbox = draw.textbbox((0, 0), detail_text, font=font_md)
        dw = bbox[2] - bbox[0]
        draw_text_with_glow(draw, ((SIZE - dw)//2, detail_y), detail_text,
                           font=font_md, fill="white", glow_color="#000000")
        detail_y += 60

    # Assist or second player
    if info["player2"]:
        if info["event_type"] in ("goal", "own goal", "penalty"):
            assist_text = f"Assist: {info['player2']}"
        elif info["event_type"] in ("substitution",):
            assist_text = f"⬆ {info['player2']}"
        else:
            assist_text = info["player2"]
        bbox = draw.textbbox((0, 0), assist_text, font=font_sm)
        aw = bbox[2] - bbox[0]
        draw.text(((SIZE - aw)//2, detail_y), assist_text, font=font_sm, fill="#cccccc")
        detail_y += 55

    # ============ MATCH INFO ============
    info_y = detail_y + 20
    meta_lines = []
    if info["stadium"]:
        meta_lines.append(f"📌 {info['stadium']}")
    # Get date/time from original description or use current
    date_m = re.search(r'(\w+day,\s+\w+\s+\d+,\s+\d{4})', description)
    if date_m:
        meta_lines.append(f"📅 {date_m.group(1)}")
    for line in meta_lines:
        bbox = draw.textbbox((0, 0), line, font=font_xs)
        lw = bbox[2] - bbox[0]
        draw.text(((SIZE - lw)//2, info_y), line, font=font_xs, fill="#888888")
        info_y += 35

    # ============ BOTTOM ============
    # Decorative line
    draw.line([(200, SIZE-155), (SIZE-200, SIZE-155)], fill="#333333", width=1)

    # Brand logo
    if os.path.exists(LOGO_PATH):
        logo = Image.open(LOGO_PATH).convert("RGBA")
        ls = 80
        logo = logo.resize((ls, ls), Image.LANCZOS)
        mask = Image.new("L", (ls, ls), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, ls, ls], fill=255)
        logo_rgba = Image.new("RGBA", logo.size, (0,0,0,0))
        logo_rgba.paste(logo)
        img_rgba = img.convert("RGBA")
        img_rgba.paste(logo_rgba, (SIZE//2 - ls//2, SIZE-145), mask)
        img = img_rgba.convert("RGB")
        draw = ImageDraw.Draw(img)

    # Brand name
    bbox = draw.textbbox((0, 0), "MATCH DAY", font=font_xs)
    tw = bbox[2] - bbox[0]
    draw.text(((SIZE - tw)//2, SIZE-55), "MATCH DAY", font=font_xs, fill="#444444")

    # ============ OUTPUT ============
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf, img


def _font(size, bold=False):
    candidates = [
        "arialbd.ttf" if bold else "arial.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _text_size(draw, text, font):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def _center_text(draw, xy, text, font, fill):
    x1, y1, x2, y2 = xy
    tw, th = _text_size(draw, text, font)
    draw.text((x1 + (x2 - x1 - tw) / 2, y1 + (y2 - y1 - th) / 2), text, font=font, fill=fill)


def _fit_text(draw, text, max_width, start_size, min_size=28, bold=True):
    size = start_size
    while size >= min_size:
        font = _font(size, bold=bold)
        if _text_size(draw, text, font)[0] <= max_width:
            return font
        size -= 4
    return _font(min_size, bold=bold)


def _rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask


def generate_card(description):
    """Generate a Facebook-ready square card using 2x supersampling."""
    output_size = int(os.environ.get("CARD_OUTPUT_SIZE", "1080"))
    render_scale = max(1, int(os.environ.get("CARD_RENDER_SCALE", "2")))
    size = output_size * render_scale

    def p(value):
        return int(round(value * render_scale))

    info = parse_description(description)
    colors1 = get_nation_colors(info["team1"]) or ("#e63946", "#c1121f")
    colors2 = get_nation_colors(info["team2"]) or ("#1e90ff", "#0a58ca")
    ev = EVENT_STYLES.get(info["event_type"], EVENT_STYLES["kickoff"])
    accent = hex_to_rgb(ev["color"])
    c1 = hex_to_rgb(colors1[0])
    c2 = hex_to_rgb(colors2[0])

    img = Image.new("RGB", (size, size), (7, 10, 24))
    overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle((0, 0, size // 2, size), fill=(*c1, 38))
    od.rectangle((size // 2, 0, size, size), fill=(*c2, 38))
    for radius, alpha in [(520, 60), (380, 46), (250, 36)]:
        od.ellipse((size // 2 - p(radius), p(150) - p(radius),
                    size // 2 + p(radius), p(150) + p(radius)), fill=(*accent, alpha))
    od.rectangle((0, 0, size, p(14)), fill=(*accent, 255))
    od.rectangle((0, size - p(86), size, size), fill=(5, 7, 18, 245))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    font_hero = _font(p(96), bold=True)
    font_score = _font(p(128), bold=True)
    font_title = _font(p(44), bold=True)
    font_body = _font(p(36), bold=True)
    font_meta = _font(p(24), bold=False)
    font_brand = _font(p(24), bold=True)

    badge_text = ev["label"].upper()
    bw, bh = _text_size(draw, badge_text, font_title)
    bx = (size - bw - p(88)) // 2
    by = p(42)
    draw.rounded_rectangle((bx, by, bx + bw + p(88), by + bh + p(34)), radius=p(32), fill=accent)
    draw.text((bx + p(44), by + p(14)), badge_text, font=font_title, fill="white")

    team1 = (info["team1"] or "HOME").upper()
    team2 = (info["team2"] or "AWAY").upper()
    flag_size = (p(250), p(170))
    flag_y = p(170)
    flag_x1 = p(138)
    flag_x2 = size - p(138) - flag_size[0]
    panel_h = p(322)

    for x, color in [(flag_x1 - p(30), c1), (flag_x2 - p(30), c2)]:
        panel = (x, flag_y - p(28), x + flag_size[0] + p(60), flag_y + panel_h)
        draw.rounded_rectangle(panel, radius=p(34), fill=(13, 18, 38), outline=color, width=p(3))

    code1 = get_country_code(info["team1"])
    code2 = get_country_code(info["team2"])
    flag1 = fetch_flag(code1, flag_size) if code1 else None
    flag2 = fetch_flag(code2, flag_size) if code2 else None
    for flag, x, name in [(flag1, flag_x1, team1), (flag2, flag_x2, team2)]:
        if flag:
            img.paste(flag, (x, flag_y), _rounded_mask(flag_size, p(16)))
        else:
            draw.rounded_rectangle((x, flag_y, x + flag_size[0], flag_y + flag_size[1]), radius=p(16), fill=(24, 31, 58))
            _center_text(draw, (x, flag_y, x + flag_size[0], flag_y + flag_size[1]), name[:2], font_hero, "white")

        team_font = _fit_text(draw, name, flag_size[0] + p(72), p(38), p(24), bold=True)
        tw, th = _text_size(draw, name, team_font)
        draw.text((x + flag_size[0] / 2 - tw / 2, flag_y + flag_size[1] + p(34)), name, font=team_font, fill="white")

    vs_r = p(64)
    vs_cx = size // 2
    vs_cy = flag_y + flag_size[1] // 2
    draw.ellipse((vs_cx - vs_r, vs_cy - vs_r, vs_cx + vs_r, vs_cy + vs_r), fill=accent)
    _center_text(draw, (vs_cx - vs_r, vs_cy - vs_r, vs_cx + vs_r, vs_cy + vs_r), "VS", font_body, "white")

    y = p(545)
    if info["score"]:
        sw, sh = _text_size(draw, info["score"], font_score)
        draw.text(((size - sw) / 2 + p(4), y + p(5)), info["score"], font=font_score, fill=(0, 0, 0))
        draw.text(((size - sw) / 2, y), info["score"], font=font_score, fill=ev["color"])
        y += p(132)

    detail = ""
    if info["player1"]:
        detail = info["player1"]
        if info["minute"]:
            detail += f"  {info['minute']}"
    elif info["extra"]:
        detail = info["extra"][:60]
    if detail:
        detail = detail.strip(" -")
        detail_font = _fit_text(draw, detail, p(860), p(54), p(30), bold=True)
        dw, dh = _text_size(draw, detail, detail_font)
        draw.text(((size - dw) / 2, y), detail, font=detail_font, fill="white")
        y += p(74)

    if info["player2"]:
        assist = f"Assist: {info['player2']}"
        aw, ah = _text_size(draw, assist, font_body)
        draw.text(((size - aw) / 2, y), assist, font=font_body, fill="#c8d0e7")
        y += p(56)

    meta = []
    if info["stadium"]:
        meta.append(info["stadium"])
    date_m = re.search(r'(\w+day,\s+\w+\s+\d+,\s+\d{4})', description)
    if date_m:
        meta.append(date_m.group(1))
    if meta:
        line = "  |  ".join(meta)
        mw, mh = _text_size(draw, line, font_meta)
        draw.text(((size - mw) / 2, y + p(18)), line, font=font_meta, fill="#9aa3bb")

    draw.line((p(210), size - p(160), size - p(210), size - p(160)), fill="#2d354f", width=p(2))

    if os.path.exists(LOGO_PATH):
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo_size = p(84)
        logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
        mask = Image.new("L", (logo_size, logo_size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, logo_size, logo_size), fill=255)
        img_rgba = img.convert("RGBA")
        img_rgba.paste(logo, (size // 2 - logo_size // 2, size - p(143)), mask)
        img = img_rgba.convert("RGB")
        draw = ImageDraw.Draw(img)

    brand = "MATCH DAY"
    bw, bh = _text_size(draw, brand, font_brand)
    draw.text(((size - bw) / 2, size - p(54)), brand, font=font_brand, fill="#69718a")

    if render_scale > 1:
        img = img.resize((output_size, output_size), Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf, img


def _fetch_image_url(url, size=None):
    if not url:
        return None
    try:
        r = requests.get(url, timeout=8, headers={"User-Agent": "MatchDayPoster/1.0"})
        if r.status_code != 200:
            return None
        img = Image.open(io.BytesIO(r.content)).convert("RGBA")
        if size:
            img.thumbnail(size, Image.LANCZOS)
        return img
    except Exception:
        return None


def _paste_cover(base, source, box, radius=0):
    x1, y1, x2, y2 = box
    width, height = x2 - x1, y2 - y1
    if not source:
        return
    src = source.convert("RGBA")
    scale = max(width / src.width, height / src.height)
    resized = src.resize((max(1, int(src.width * scale)), max(1, int(src.height * scale))), Image.LANCZOS)
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    cropped = resized.crop((left, top, left + width, top + height))
    mask = Image.new("L", (width, height), 255)
    if radius:
        mask = _rounded_mask((width, height), radius)
    base.paste(cropped, (x1, y1), mask)


def _draw_wrapped_center(draw, text, y, max_width, font_size, fill, line_gap, bold=True, min_size=28):
    words = [w for w in text.split() if w]
    if not words:
        return y
    font = _fit_text(draw, text, max_width, font_size, min_size, bold=bold)
    lines = []
    line = ""
    for word in words:
        test = f"{line} {word}".strip()
        if line and _text_size(draw, test, font)[0] > max_width:
            lines.append(line)
            line = word
        else:
            line = test
    if line:
        lines.append(line)
    for line in lines[:3]:
        tw, th = _text_size(draw, line, font)
        draw.text(((draw.im.size[0] - tw) / 2, y), line, font=font, fill=fill)
        y += th + line_gap
    return y


def generate_card(description, context=None):
    """Generate a detailed football media-style event graphic.

    The optional context dict can include:
    match, event, player_image_url, home_crest, away_crest, home_flag, away_flag.
    """
    context = context or {}
    match = context.get("match") or {}
    event = context.get("event") or {}
    info = parse_description(description)

    output_size = int(os.environ.get("CARD_OUTPUT_SIZE", "1080"))
    render_scale = max(1, int(os.environ.get("CARD_RENDER_SCALE", "2")))
    size = output_size * render_scale

    def p(value):
        return int(round(value * render_scale))

    home = match.get("home_team") or info["team1"] or "HOME"
    away = match.get("away_team") or info["team2"] or "AWAY"
    event_type = (event.get("type") or info["event_type"] or "update").lower()
    player = event.get("player") or info["player1"] or ""
    minute = str(event.get("minute") or info["minute"] or "").replace("'", "")
    score = event.get("score") or info["score"] or ""
    competition = match.get("competition") or ""
    source = (event.get("source") or "").upper()
    scoring_team = event.get("team") or ""

    colors1 = get_nation_colors(home) or ("#e63946", "#c1121f")
    colors2 = get_nation_colors(away) or ("#1e90ff", "#0a58ca")
    c1 = hex_to_rgb(colors1[0])
    c2 = hex_to_rgb(colors2[0])
    ev = EVENT_STYLES.get(event_type, EVENT_STYLES.get("kickoff"))
    accent = hex_to_rgb(ev["color"]) if ev else (255, 255, 255)

    img = Image.new("RGB", (size, size), (8, 10, 18))
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)

    # Editorial split background with pitch-like texture and strong event accent.
    ld.polygon([(0, 0), (p(690), 0), (p(520), size), (0, size)], fill=(*c1, 115))
    ld.polygon([(p(520), 0), (size, 0), (size, size), (p(390), size)], fill=(*c2, 100))
    for i in range(0, 18):
        x = p(-180 + i * 92)
        ld.line((x, 0, x + p(520), size), fill=(255, 255, 255, 13), width=p(2))
    for radius, alpha in [(560, 72), (390, 54), (230, 38)]:
        ld.ellipse((p(540) - p(radius), p(400) - p(radius), p(540) + p(radius), p(400) + p(radius)),
                   fill=(*accent, alpha))
    ld.rectangle((0, 0, size, p(18)), fill=(*accent, 255))
    ld.rectangle((0, size - p(116), size, size), fill=(4, 6, 14, 245))
    img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    draw = ImageDraw.Draw(img)

    font_kicker = _font(p(30), bold=True)
    font_headline = _font(p(108), bold=True)
    font_player = _font(p(62), bold=True)
    font_score = _font(p(58), bold=True)
    font_team = _font(p(28), bold=True)
    font_meta = _font(p(24), bold=True)
    font_brand = _font(p(24), bold=True)

    label_map = {
        "goal": "GOAL",
        "own goal": "OWN GOAL",
        "penalty": "PENALTY",
        "red": "RED CARD",
        "red card": "RED CARD",
        "yellow": "YELLOW CARD",
        "yellow card": "YELLOW CARD",
        "kickoff": "KICK OFF",
        "half-time": "HALF TIME",
        "halftime": "HALF TIME",
        "full-time": "FULL TIME",
        "fulltime": "FULL TIME",
        "substitution": "SUBSTITUTION",
    }
    label = label_map.get(event_type, "MATCH UPDATE")

    # Left editorial copy block.
    draw.rounded_rectangle((p(52), p(54), p(310), p(110)), radius=p(12), fill=accent)
    _center_text(draw, (p(52), p(54), p(310), p(110)), label, font_kicker, "white")

    headline = "GOAL!" if event_type in ("goal", "own goal", "penalty") else label
    hw, hh = _text_size(draw, headline, font_headline)
    draw.text((p(54) + p(5), p(138) + p(6)), headline, font=font_headline, fill=(0, 0, 0))
    draw.text((p(54), p(138)), headline, font=font_headline, fill="white")

    if player and player.lower() != "unknown":
        y = _draw_wrapped_center(draw, player.upper(), p(268), p(480), p(62), "#ffffff", p(10), bold=True, min_size=p(34))
    elif event_type == "goal":
        y = _draw_wrapped_center(draw, "SCORER PENDING", p(282), p(480), p(48), "#ffffff", p(10), bold=True, min_size=p(30))
    else:
        y = _draw_wrapped_center(draw, f"{home} vs {away}".upper(), p(282), p(480), p(44), "#ffffff", p(10), bold=True, min_size=p(28))

    details = []
    if minute and minute not in ("?", "None"):
        details.append(f"{minute}'")
    if competition:
        details.append(competition.upper())
    if source:
        details.append(source)
    if details:
        line = "  |  ".join(details)
        mw, mh = _text_size(draw, line, font_meta)
        draw.text((p(54), max(y + p(8), p(440))), line, font=font_meta, fill="#d6d9e8")

    # Player/photo panel. Real image when provided, otherwise a polished silhouette.
    photo_box = (p(590), p(118), p(1010), p(742))
    photo = _fetch_image_url(context.get("player_image_url") or event.get("player_image_url"), (p(900), p(900)))
    draw.rounded_rectangle(photo_box, radius=p(34), fill=(12, 16, 32), outline=(255, 255, 255), width=p(3))
    if photo:
        _paste_cover(img, photo, photo_box, radius=p(34))
        draw = ImageDraw.Draw(img)
        shade = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shade)
        sd.rounded_rectangle(photo_box, radius=p(34), fill=(0, 0, 0, 55))
        img = Image.alpha_composite(img.convert("RGBA"), shade).convert("RGB")
        draw = ImageDraw.Draw(img)
    else:
        px1, py1, px2, py2 = photo_box
        draw.ellipse((px1 + p(135), py1 + p(80), px2 - p(135), py1 + p(300)), fill=(48, 58, 96))
        draw.rounded_rectangle((px1 + p(92), py1 + p(285), px2 - p(92), py2 + p(120)), radius=p(150), fill=(42, 50, 84))
        fallback = (player if player and player.lower() != "unknown" else scoring_team or "LIVE").upper()[:2]
        _center_text(draw, (px1, py1 + p(210), px2, py1 + p(360)), fallback, font_headline, "#ffffff")

    # Score strip.
    strip = (p(58), p(758), p(1022), p(914))
    draw.rounded_rectangle(strip, radius=p(24), fill=(7, 9, 20), outline=(255, 255, 255), width=p(2))
    home_short = home.upper()
    away_short = away.upper()
    home_font = _fit_text(draw, home_short, p(300), p(34), p(20), bold=True)
    away_font = _fit_text(draw, away_short, p(300), p(34), p(20), bold=True)
    draw.text((p(112), p(804)), home_short, font=home_font, fill="white")
    draw.text((p(700), p(804)), away_short, font=away_font, fill="white")
    score_text = score if score else "VS"
    sw, sh = _text_size(draw, score_text, font_score)
    draw.rounded_rectangle((p(448), p(785), p(632), p(886)), radius=p(18), fill=accent)
    draw.text((p(540) - sw / 2, p(834) - sh / 2), score_text, font=font_score, fill="white")

    # Flags and crest/identity chips.
    flag_size = (p(88), p(62))
    for team, x in [(home, p(92)), (away, p(900))]:
        flag = fetch_flag(get_country_code(team), flag_size)
        if flag:
            img.paste(flag, (x, p(662)), _rounded_mask(flag_size, p(8)))
        else:
            draw.rounded_rectangle((x, p(662), x + flag_size[0], p(662) + flag_size[1]), radius=p(8), fill=(30, 35, 60))
            _center_text(draw, (x, p(662), x + flag_size[0], p(662) + flag_size[1]), team[:2].upper(), font_team, "white")

    comp = competition.upper() if competition else "MATCH DAY LIVE"
    comp_font = _fit_text(draw, comp, p(540), p(28), p(18), bold=True)
    cw, ch = _text_size(draw, comp, comp_font)
    draw.text((p(540) - cw / 2, p(946)), comp, font=comp_font, fill="#98a1be")

    if os.path.exists(LOGO_PATH):
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo_size = p(74)
        logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
        mask = Image.new("L", (logo_size, logo_size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, logo_size, logo_size), fill=255)
        img_rgba = img.convert("RGBA")
        img_rgba.paste(logo, (p(58), size - p(94)), mask)
        img = img_rgba.convert("RGB")
        draw = ImageDraw.Draw(img)

    brand = "MATCH DAY"
    bw, bh = _text_size(draw, brand, font_brand)
    draw.text((p(148), size - p(69)), brand, font=font_brand, fill="#dce2f2")

    footer = "AUTOMATED LIVE FOOTBALL UPDATE"
    fw, fh = _text_size(draw, footer, font_meta)
    draw.text((size - p(58) - fw, size - p(68)), footer, font=font_meta, fill="#68728f")

    if render_scale > 1:
        img = img.resize((output_size, output_size), Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf, img
