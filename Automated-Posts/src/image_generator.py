from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, requests, io

FONT_BOLD = None
FONT_REGULAR = None
FLAG_CACHE = {}
PLAYER_CACHE = {}
BADGE_CACHE = {}
SPORTSDB_KEY = "123"

COUNTRY_CODES = {
    "france": "fr", "senegal": "sn", "iraq": "iq", "norway": "no",
    "iran": "ir", "new zealand": "nz", "argentina": "ar", "algeria": "dz",
    "austria": "at", "jordan": "jo", "portugal": "pt", "congo dr": "cd",
    "england": "gb-eng", "croatia": "hr", "ghana": "gh", "panama": "pa",
    "uzbekistan": "uz", "colombia": "co", "czechia": "cz", "south africa": "za",
    "switzerland": "ch", "bosnia-herzegovina": "ba", "brazil": "br",
    "germany": "de", "italy": "it", "netherlands": "nl", "spain": "es",
    "belgium": "be", "uruguay": "uy", "mexico": "mx", "usa": "us",
    "japan": "jp", "south korea": "kr", "australia": "au", "nigeria": "ng",
    "cameroon": "cm", "morocco": "ma", "tunisia": "tn", "egypt": "eg",
    "saudi arabia": "sa", "ecuador": "ec", "canada": "ca", "qatar": "qa",
    "poland": "pl", "denmark": "dk", "serbia": "rs", "wales": "gb-wls",
    "scotland": "gb-sct", "turkey": "tr", "russia": "ru", "ukraine": "ua",
    "sweden": "se", "hungary": "hu", "romania": "ro", "greece": "gr",
    "paraguay": "py", "chile": "cl", "peru": "pe", "venezuela": "ve",
    "costa rica": "cr", "honduras": "hn", "jamaica": "jm", "bolivia": "bo",
    "ireland": "ie", "iceland": "is", "slovakia": "sk", "slovenia": "si",
    "montenegro": "me", "albania": "al", "north macedonia": "mk",
    "finland": "fi", "luxembourg": "lu", "cyprus": "cy", "israel": "il",
    "bulgaria": "bg", "latvia": "lv", "estonia": "ee", "lithuania": "lt",
    "moldova": "md", "bosnia": "ba", "ivory coast": "ci", "mali": "ml",
    "burkina faso": "bf", "zambia": "zm", "cape verde": "cv",
}

TEAM_COLORS = {
    "france": (20, 50, 180), "senegal": (0, 133, 67), "brazil": (0, 155, 58),
    "argentina": (116, 172, 223), "germany": (0, 0, 0), "italy": (0, 102, 204),
    "netherlands": (255, 112, 0), "spain": (255, 196, 0), "england": (206, 17, 38),
    "portugal": (0, 153, 0), "belgium": (255, 200, 0), "uruguay": (0, 56, 168),
    "mexico": (0, 104, 71), "usa": (59, 89, 152), "japan": (0, 51, 160),
    "south korea": (0, 68, 134), "australia": (0, 74, 168), "nigeria": (0, 119, 27),
}

def _init():
    global FONT_BOLD, FONT_REGULAR
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
              "C:/Windows/Fonts/arialbd.ttf"]:
        if os.path.exists(p): FONT_BOLD = p; break
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/TTF/DejaVuSans.ttf",
              "C:/Windows/Fonts/arial.ttf"]:
        if os.path.exists(p): FONT_REGULAR = p; break

def _f(size, bold=False):
    _init()
    p = FONT_BOLD if bold else FONT_REGULAR
    return ImageFont.truetype(p, size) if p else ImageFont.load_default()

def _cx(draw, text, font, y, cx, fill="white"):
    b = draw.textbbox((0, 0), text, font=font)
    w = b[2] - b[0]
    draw.text((cx - w // 2, y), text, fill=fill, font=font)

def get_flag(team, size=(100, 100)):
    t = team.lower().strip()
    code = COUNTRY_CODES.get(t)
    if not code:
        for name, c in COUNTRY_CODES.items():
            if name in t or t in name: code = c; break
    if not code: return None
    url = f"https://flagcdn.com/w80/{code}.png"
    if url in FLAG_CACHE: return FLAG_CACHE[url]
    try:
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            img = Image.open(io.BytesIO(r.content)).convert("RGBA").resize(size, Image.LANCZOS)
            FLAG_CACHE[url] = img
            return img
    except: pass
    return None

def get_player_img(name, size=(120, 120)):
    if not name: return None
    key = name.lower().strip()
    if key in PLAYER_CACHE: return PLAYER_CACHE[key]
    try:
        url = f"https://www.thesportsdb.com/api/v1/json/{SPORTSDB_KEY}/searchplayers.php?p={requests.utils.quote(name)}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json().get("player", [])
            if data:
                img_url = data[0].get("strThumb") or data[0].get("strCutout")
                if img_url:
                    ir = requests.get(img_url, timeout=5)
                    if ir.status_code == 200:
                        img = Image.open(io.BytesIO(ir.content)).convert("RGBA").resize(size, Image.LANCZOS)
                        PLAYER_CACHE[key] = img
                        return img
    except: pass
    PLAYER_CACHE[key] = None
    return None

def get_team_badge(team, size=(100, 100)):
    t = team.lower().strip()
    if t in BADGE_CACHE: return BADGE_CACHE[t]
    try:
        url = f"https://www.thesportsdb.com/api/v1/json/{SPORTSDB_KEY}/searchteams.php?t={requests.utils.quote(team)}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json().get("teams", [])
            if data:
                b_url = data[0].get("strBadge")
                if b_url:
                    ir = requests.get(b_url, timeout=5)
                    if ir.status_code == 200:
                        img = Image.open(io.BytesIO(ir.content)).convert("RGBA").resize(size, Image.LANCZOS)
                        BADGE_CACHE[t] = img
                        return img
    except: pass
    BADGE_CACHE[t] = None
    return None

def _draw_pro_base(label, color):
    _init()
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), (10, 10, 20))
    draw = ImageDraw.Draw(img)
    
    # Background gradient
    for i in range(H):
        alpha = int(50 * (1 - i/H))
        c = (10+alpha, 10+alpha, 20+alpha*2)
        draw.line([(0, i), (W, i)], fill=c)
    
    # Accent Top Bar
    draw.rectangle([(0, 0), (W, 70)], fill=color)
    _cx(draw, label.upper(), _f(40, bold=True), 15, 600, "white")
    
    # Side Glows
    draw.ellipse([( -100, -100), (300, 300)], fill=(30, 30, 60))
    draw.ellipse([(900, -100), (1300, 300)], fill=(30, 30, 60))
    
    return img, draw

def live_image(home, away, comp, time_str=""):
    img, draw = _draw_pro_base("LIVE", (40, 140, 255))
    _draw_match_center(draw, img, home, away, "vs", 180, (40, 140, 255))
    if time_str:
        _cx(draw, f"Kickoff: {time_str} UTC", _f(24), 380, 600, "lightblue")
    if comp:
        draw.rounded_rectangle([(400, 460), (800, 500)], 10, fill=(40, 140, 255))
        _cx(draw, comp.upper(), _f(20, bold=True), 468, 600, "white")
    path = "post_image.png"; img.save(path); return path

def goal_image(home, away, sh, sa, scorer, minute, assist, comp):
    img, draw = _draw_pro_base("GOAL", (255, 215, 0))
    _draw_match_center(draw, img, home, away, f"{sh} - {sa}", 160, (255, 215, 0))
    
    pimg = get_player_img(scorer, (150, 150))
    cx = 600
    if pimg:
        mask = Image.new("L", (150, 150), 0)
        ImageDraw.Draw(mask).ellipse([(0, 0), (150, 150)], fill=255)
        img.paste(pimg, (cx - 75, 280), mask)
    else:
        draw.ellipse([(cx - 75, 280), (cx + 75, 400)], fill=(255, 215, 0))
        _cx(draw, scorer[:2].upper(), _f(40, bold=True), 310, cx, (14, 14, 28))
    
    _cx(draw, f"{scorer}  {minute}'", _f(36, bold=True), 440, cx, (255, 215, 0))
    if assist:
        _cx(draw, f"Assist: {assist}", _f(22), 480, cx, "lightgray")
    if comp:
        _cx(draw, comp, _f(20), 540, 600, "gray")
    path = "post_image.png"; img.save(path); return path

def card_image(team, player, minute, card_type, comp):
    key = "RED" if "RED" in card_type.upper() else "YELLOW"
    img, draw = _draw_pro_base(key, EVENT_COLORS[key])
    
    pimg = get_player_img(player, (150, 150))
    cx = 600
    if pimg:
        mask = Image.new("L", (150, 150), 0)
        ImageDraw.Draw(mask).ellipse([(0, 0), (150, 150)], fill=255)
        img.paste(pimg, (cx - 75, 140), mask)
    else:
        c = _get_color(team)
        draw.ellipse([(cx - 75, 140), (cx + 75, 260)], fill=c)
        _cx(draw, team[:3].upper(), _f(36, bold=True), 160, cx, "white")
    
    _cx(draw, team.upper(), _f(28, bold=True), 250, cx, "white")
    _draw_accent_line(draw, 300, EVENT_COLORS[key])
    _cx(draw, f"{player}  {minute}'", _f(32, bold=True), 315, cx, EVENT_COLORS[key])
    if comp:
        _cx(draw, comp, _f(20), 500, 600, "gray")
    path = "post_image.png"; img.save(path); return path

def sub_image(team, player_off, player_on, minute, comp):
    img, draw = _draw_pro_base("SUB", EVENT_COLORS["SUB"])
    # Team block center
    _cx(draw, team.upper(), _f(32, bold=True), 140, 600, "white")
    
    # Player cards
    y_start = 220
    draw.rounded_rectangle([(300, y_start), (550, y_start + 60)], 15, fill=(30, 30, 50), outline=(140, 80, 200))
    _cx(draw, f"OFF: {player_off}", _f(24), y_start + 15, 425, (255, 100, 100))
    
    draw.rounded_rectangle([(650, y_start), (900, y_start + 60)], 15, fill=(30, 30, 50), outline=(140, 80, 200))
    _cx(draw, f"ON:  {player_on}", _f(24), y_start + 15, 775, (100, 255, 100))
    
    _cx(draw, f"{minute}'", _f(28, bold=True), 320, 600, "gray")
    if comp:
        _cx(draw, comp, _f(20), 500, 600, "gray")
    path = "post_image.png"; img.save(path); return path

def halftime_image(home, away, sh, sa, scorers_text, comp):
    img, draw = _draw_pro_base("HALFTIME", EVENT_COLORS["HALFTIME"])
    _draw_match_center(draw, img, home, away, f"{sh} - {sa}", 140, (255, 165, 0))
    if scorers_text:
        _cx(draw, f"Scorers: {scorers_text}", _f(22), 350, 600, "lightgray")
    _cx(draw, "Second half coming up!", _f(26), 420, 600, (255, 200, 100))
    if comp:
        _cx(draw, comp, _f(20), 500, 600, "gray")
    path = "post_image.png"; img.save(path); return path

def secondhalf_image(home, away, sh, sa, comp):
    img, draw = _draw_pro_base("LIVE", EVENT_COLORS["LIVE"])
    _cx(draw, "SECOND HALF", _f(38, bold=True), 14, 600, "white")
    _draw_match_center(draw, img, home, away, f"{sh} - {sa}", 170)
    if comp:
        _cx(draw, comp, _f(20), 500, 600, "gray")
    path = "post_image.png"; img.save(path); return path

def fulltime_image(home, away, sh, sa, scorers, comp):
    img, draw = _draw_pro_base("FULLTIME", EVENT_COLORS["FULLTIME"])
    _draw_match_center(draw, img, home, away, f"{sh} - {sa}", 120, (50, 200, 50))
    _cx(draw, "FINAL RESULT", _f(28, bold=True), 270, 600, (50, 200, 50))
    y = 320
    for s in scorers[:5]:
        _cx(draw, s, _f(22), y, 600, "lightgray"); y += 30
    if comp:
        _cx(draw, comp, _f(20), 500, 600, "gray")
    path = "post_image.png"; img.save(path); return path

def summary_image(home, away, sh, sa, events, comp):
    img, draw = _draw_pro_base("SUMMARY", EVENT_COLORS["SUMMARY"])
    _draw_match_center(draw, img, home, away, f"{sh} - {sa}", 80)
    _draw_accent_line(draw, 230, (80, 80, 120))
    y = 260
    for e in events[:6]:
        _cx(draw, e, _f(20), y, 600, "lightgray"); y += 30
    path = "post_image.png"; img.save(path); return path

def schedule_image(lines, date_str):
    img, draw = _draw_pro_base("MATCH DAY", (40, 140, 255))
    _cx(draw, date_str, _f(24), 90, 600, "lightgray")
    y = 150
    for l in lines[:6]:
        parts = l.split("  ") if "  " in l else [l]
        _cx(draw, parts[0], _f(26, bold=True), y, 600, "white")
        if len(parts) > 1:
            _cx(draw, parts[1], _f(20), y + 30, 600, "gray")
        y += 70
    _cx(draw, "Follow for live updates!", _f(18), 560, 600, "gray")
    path = "post_image.png"; img.save(path); return path

def _draw_match_center(draw, img, home, away, score_text, y_pos, accent=None):
    # Team flags
    fh = get_flag(home, (100, 100))
    fa = get_flag(away, (100, 100))
    
    # Home flag/circle
    if fh: img.paste(fh, (150, y_pos - 50), fh)
    else:
        c = _get_color(home)
        draw.ellipse([(150, y_pos - 50), (250, y_pos + 50)], fill=c)
        _cx(draw, home[:3].upper(), _f(24, bold=True), y_pos + 15, 200, "white")
    
    # Away flag/circle
    if fa: img.paste(fa, (950, y_pos - 50), fa)
    else:
        c = _get_color(away)
        draw.ellipse([(950, y_pos - 50), (1050, y_pos + 50)], fill=c)
        _cx(draw, away[:3].upper(), _f(24, bold=True), y_pos + 15, 1000, "white")
    
    # Names
    _cx(draw, home.upper(), _f(28, bold=True), y_pos + 70, 200, "white")
    _cx(draw, away.upper(), _f(28, bold=True), y_pos + 70, 1000, "white")
    
    # Score
    if score_text:
        _cx(draw, score_text, _f(80, bold=True), y_pos - 20, 600, accent or "white")

def _draw_accent_line(draw, y, color):
    draw.rounded_rectangle([(200, y), (1000, y + 2)], 1, 1, fill=color)
