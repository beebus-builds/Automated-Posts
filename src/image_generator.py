from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, requests, io
from math import sin, pi

FONT_BOLD = None
FONT_REGULAR = None
FLAG_CACHE = {}
PLAYER_CACHE = {}
BADGE_CACHE = {}
SPORTSDB_KEY = "123"

EVENT_COLORS = {
    "LIVE": (40, 140, 255),
    "GOAL": (255, 215, 0),
    "YELLOW": (255, 200, 0),
    "RED": (255, 50, 50),
    "SUB": (140, 80, 200),
    "HALFTIME": (255, 165, 0),
    "FULLTIME": (50, 200, 50),
    "SUMMARY": (80, 80, 120),
}

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
    "buggaria": "bg", "latvia": "lv", "estonia": "ee", "lithuania": "lt",
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

def _get_color(team):
    t = team.lower().strip()
    if t in TEAM_COLORS: return TEAM_COLORS[t]
    import hashlib
    h = hashlib.md5(t.encode()).hexdigest()
    return (int(h[:2], 16) + 40, int(h[2:4], 16) + 40, int(h[4:6], 16) + 40)

def _wave_flag(img, amplitude=6, period=50):
    w, h = img.size
    result = Image.new("RGBA", (w, h))
    for x in range(w):
        offset = int(amplitude * sin(2 * pi * x / period))
        for y in range(h):
            sy = min(max(y + offset, 0), h - 1)
            if x < w and sy < h:
                result.putpixel((x, y), img.getpixel((x % w, sy % h)))
    return result

def get_flag(team, size=(120, 120)):
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
            raw = Image.open(io.BytesIO(r.content)).convert("RGBA").resize(size, Image.LANCZOS)
            waved = _wave_flag(raw, amplitude=5, period=45)
            FLAG_CACHE[url] = waved
            return waved
    except: pass
    return None

def get_player_img(name, size=(180, 180)):
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

def get_team_badge(team, size=(150, 150)):
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
    W, H = 1200, 1200
    img = Image.new("RGB", (W, H), (10, 10, 16))
    draw = ImageDraw.Draw(img)
    
    # Background gradient
    for i in range(H):
        alpha = int(45 * (1 - i/H))
        c = (8+alpha, 8+alpha, 14+alpha)
        draw.line([(0, i), (W, i)], fill=c)
        
    # Modern cyber/tech grid lines (diagonal accents)
    for x in range(0, W, 100):
        draw.line([(x, 0), (x - 300, H)], fill=(22, 22, 38), width=2)
    
    # Neon top bar
    draw.rectangle([(0, 0), (W, 100)], fill=(12, 12, 20))
    draw.line([(0, 100), (W, 100)], fill=color, width=4)
    
    # Glows
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([( -200, -200), (400, 400)], fill=(color[0], color[1], color[2], 35))
    gd.ellipse([(800, -200), (1400, 400)], fill=(color[0], color[1], color[2], 35))
    gd.ellipse([(400, 400), (800, 800)], fill=(color[0], color[1], color[2], 25))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(img)
    
    # Header Label Text
    _cx(draw, label.upper(), _f(52, bold=True), 22, 600, "white")
    
    return img, draw

def _draw_match_center(draw, img, home, away, score_text, y_pos, accent=None):
    W = 1200
    bg_top = y_pos - 40
    bg_bot = y_pos + 380
    draw.rounded_rectangle([(80, bg_top), (1120, bg_bot)], 24, fill=(18, 18, 32), outline=(255, 255, 255, 20), width=2)
    
    # Flags (always shown, large) — behind badges
    fh = get_flag(home, (200, 140))
    fa = get_flag(away, (200, 140))
    flag_y = y_pos + 10
    if fh:
        img.paste(fh, (280 - 100, flag_y), fh if fh.mode == "RGBA" else None)
    if fa:
        img.paste(fa, (920 - 100, flag_y), fa if fa.mode == "RGBA" else None)
    
    # Team badges overlaid on flags
    bh = get_team_badge(home, (120, 120))
    ba = get_team_badge(away, (120, 120))
    mask_circle = Image.new("L", (120, 120), 0)
    ImageDraw.Draw(mask_circle).ellipse([(0, 0), (120, 120)], fill=255)
    badge_y = y_pos + 60
    
    if bh:
        img.paste(bh, (280 - 60, badge_y), mask_circle if bh.mode == "RGBA" else None)
    else:
        c = _get_color(home)
        draw.ellipse([(280 - 60, badge_y), (280 + 60, badge_y + 120)], fill=c)
        _cx(draw, home[:3].upper(), _f(36, bold=True), badge_y + 45, 280, "white")
        
    if ba:
        img.paste(ba, (920 - 60, badge_y), mask_circle if ba.mode == "RGBA" else None)
    else:
        c = _get_color(away)
        draw.ellipse([(920 - 60, badge_y), (920 + 60, badge_y + 120)], fill=c)
        _cx(draw, away[:3].upper(), _f(36, bold=True), badge_y + 45, 920, "white")
        
    # Names below flags
    _cx(draw, home.upper(), _f(36, bold=True), y_pos + 170, 280, "white")
    _cx(draw, away.upper(), _f(36, bold=True), y_pos + 170, 920, "white")
    
    # Score or VS text
    if score_text:
        _cx(draw, score_text, _f(96, bold=True), y_pos + 45, 600, accent or "white")

def _draw_accent_line(draw, y, color):
    draw.rounded_rectangle([(200, y), (1000, y + 3)], radius=2, fill=color)

def live_image(home, away, comp, time_str=""):
    img, draw = _draw_pro_base("LIVE", EVENT_COLORS["LIVE"])
    _draw_match_center(draw, img, home, away, "VS", 220, EVENT_COLORS["LIVE"])
    
    # Descriptive bottom section
    draw.rounded_rectangle([(300, 640), (900, 740)], 20, fill=(24, 24, 40), outline=EVENT_COLORS["LIVE"], width=2)
    _cx(draw, "MATCH DAY IN PROGRESS", _f(28, bold=True), 655, 600, EVENT_COLORS["LIVE"])
    if time_str:
        _cx(draw, f"Kickoff Time: {time_str} UTC", _f(24), 695, 600, "lightblue")
        
    if comp:
        draw.rounded_rectangle([(200, 840), (1000, 920)], 15, fill=(35, 35, 55))
        _cx(draw, comp.upper(), _f(26, bold=True), 862, 600, "white")
        
    path = "post_image.png"
    img.save(path)
    return path

def goal_image(home, away, sh, sa, scorer, minute, assist, comp):
    img, draw = _draw_pro_base("GOAL", EVENT_COLORS["GOAL"])
    _draw_match_center(draw, img, home, away, f"{sh} - {sa}", 180, EVENT_COLORS["GOAL"])
    
    cx = 600
    y_player = 620
    p_size = 280
    
    draw.rounded_rectangle([(200, y_player - 30), (1000, y_player + 380)], 24, fill=(18, 18, 32), outline=EVENT_COLORS["GOAL"], width=3)
    
    pimg = get_player_img(scorer, (p_size, p_size))
    if pimg:
        mask = Image.new("L", (p_size, p_size), 0)
        ImageDraw.Draw(mask).ellipse([(0, 0), (p_size, p_size)], fill=255)
        draw.ellipse([(cx - p_size//2 - 5, y_player - 5), (cx + p_size//2 + 5, y_player + p_size + 5)], outline=EVENT_COLORS["GOAL"], width=5)
        img.paste(pimg, (cx - p_size//2, y_player), mask)
    else:
        draw.ellipse([(cx - p_size//2, y_player), (cx + p_size//2, y_player + p_size)], fill=EVENT_COLORS["GOAL"])
        _cx(draw, scorer[:2].upper(), _f(80, bold=True), y_player + p_size//2 - 30, cx, (14, 14, 28))
        
    _cx(draw, f"{scorer.upper()}", _f(52, bold=True), y_player + p_size + 25, cx, EVENT_COLORS["GOAL"])
    _cx(draw, f"MINUTE: {minute}'", _f(34, bold=True), y_player + p_size + 95, cx, "white")
    
    if assist:
        _cx(draw, f"ASSIST BY: {assist.upper()}", _f(26), y_player + p_size + 155, cx, "lightgray")
        
    if comp:
        _cx(draw, comp.upper(), _f(24, bold=True), 1120, 600, "gray")
        
    path = "post_image.png"
    img.save(path)
    return path

def card_image(team, player, minute, card_type, comp):
    key = "RED" if "RED" in card_type.upper() else "YELLOW"
    color = EVENT_COLORS[key]
    img, draw = _draw_pro_base(key, color)
    
    # Top info text
    _cx(draw, f"BOOKING RECEIVED IN {minute}'", _f(28, bold=True), 160, 600, color)
    
    cx = 600
    y_pos = 280
    
    # Outer glassy container
    draw.rounded_rectangle([(200, y_pos), (1000, y_pos + 620)], 24, fill=(18, 18, 32), outline=(255, 255, 255, 15), width=2)
    
    # Draw actual card graphic
    card_w, card_h = 140, 200
    draw.rounded_rectangle([(cx - card_w//2, y_pos + 60), (cx + card_w//2, y_pos + 60 + card_h)], 15, fill=color, outline="white", width=3)
    
    # Player Photo Circle — bigger
    p_size = 240
    pimg = get_player_img(player, (p_size, p_size))
    px = cx - p_size//2
    py = y_pos + 300
    if pimg:
        mask = Image.new("L", (p_size, p_size), 0)
        ImageDraw.Draw(mask).ellipse([(0, 0), (p_size, p_size)], fill=255)
        draw.ellipse([(px - 5, py - 5), (px + p_size + 5, py + p_size + 5)], outline=color, width=5)
        img.paste(pimg, (px, py), mask)
    else:
        c = _get_color(team)
        draw.ellipse([(px, py), (px + p_size, py + p_size)], fill=c)
        _cx(draw, team[:3].upper(), _f(56, bold=True), py + p_size//2 - 20, cx, "white")
        
    _cx(draw, player.upper(), _f(46, bold=True), py + p_size + 15, cx, "white")
    _cx(draw, team.upper(), _f(28, bold=True), py + p_size + 75, cx, "gray")
    
    if comp:
        _cx(draw, comp.upper(), _f(24), 1080, 600, "gray")
        
    path = "post_image.png"
    img.save(path)
    return path

def sub_image(team, player_off, player_on, minute, comp):
    img, draw = _draw_pro_base("SUBSTITUTION", EVENT_COLORS["SUB"])
    
    _cx(draw, team.upper(), _f(40, bold=True), 180, 600, "white")
    _cx(draw, f"MINUTE: {minute}'", _f(28, bold=True), 235, 600, "gray")
    
    # Dynamic graphical cards
    y_start = 330
    
    s_size = 220
    # Left Card (OFF) - Red Glow
    draw.rounded_rectangle([(100, y_start), (550, y_start + 520)], 24, fill=(26, 18, 20), outline=(255, 80, 80), width=3)
    _cx(draw, "PLAYER OUT", _f(28, bold=True), y_start + 25, 325, (255, 80, 80))
    pox, poy = 325 - s_size//2, y_start + 60
    p_off_img = get_player_img(player_off, (s_size, s_size))
    if p_off_img:
        mask = Image.new("L", (s_size, s_size), 0)
        ImageDraw.Draw(mask).ellipse([(0, 0), (s_size, s_size)], fill=255)
        img.paste(p_off_img, (pox, poy), mask)
    else:
        draw.ellipse([(pox, poy), (pox + s_size, poy + s_size)], fill=(255, 80, 80))
    _cx(draw, player_off.upper(), _f(30, bold=True), poy + s_size + 20, 325, "white")
    _cx(draw, "▼", _f(52), poy + s_size + 80, 325, (255, 80, 80))
    
    # Right Card (ON) - Green Glow
    draw.rounded_rectangle([(650, y_start), (1100, y_start + 520)], 24, fill=(18, 26, 20), outline=(80, 255, 80), width=3)
    _cx(draw, "PLAYER IN", _f(28, bold=True), y_start + 25, 875, (80, 255, 80))
    pix, piy = 875 - s_size//2, y_start + 60
    p_on_img = get_player_img(player_on, (s_size, s_size))
    if p_on_img:
        mask = Image.new("L", (s_size, s_size), 0)
        ImageDraw.Draw(mask).ellipse([(0, 0), (s_size, s_size)], fill=255)
        img.paste(p_on_img, (pix, piy), mask)
    else:
        draw.ellipse([(pix, piy), (pix + s_size, piy + s_size)], fill=(80, 255, 80))
    _cx(draw, player_on.upper(), _f(30, bold=True), piy + s_size + 20, 875, "white")
    _cx(draw, "▲", _f(52), piy + s_size + 80, 875, (80, 255, 80))
    
    if comp:
        _cx(draw, comp.upper(), _f(24, bold=True), 1080, 600, "gray")
        
    path = "post_image.png"
    img.save(path)
    return path

def halftime_image(home, away, sh, sa, scorers_text, comp):
    img, draw = _draw_pro_base("HALF TIME", EVENT_COLORS["HALFTIME"])
    _draw_match_center(draw, img, home, away, f"{sh} - {sa}", 200, EVENT_COLORS["HALFTIME"])
    
    y_pos = 620
    draw.rounded_rectangle([(150, y_pos), (1050, y_pos + 320)], 24, fill=(18, 18, 32), outline=EVENT_COLORS["HALFTIME"], width=2)
    
    _cx(draw, "HALF TIME REPORT", _f(32, bold=True), y_pos + 30, 600, EVENT_COLORS["HALFTIME"])
    _draw_accent_line(draw, y_pos + 85, (100, 100, 120))
    
    if scorers_text:
        _cx(draw, "SCORERS:", _f(22, bold=True), y_pos + 120, 600, "gray")
        _cx(draw, scorers_text.upper(), _f(28), y_pos + 160, 600, "white")
    else:
        _cx(draw, "NO GOALS SCORED YET IN THE FIRST HALF", _f(24), y_pos + 150, 600, "lightgray")
        
    _cx(draw, "SECOND HALF COMING UP SOON", _f(24, bold=True), y_pos + 250, 600, "lightblue")
    
    if comp:
        _cx(draw, comp.upper(), _f(24, bold=True), 1080, 600, "gray")
        
    path = "post_image.png"
    img.save(path)
    return path

def secondhalf_image(home, away, sh, sa, comp):
    img, draw = _draw_pro_base("LIVE", EVENT_COLORS["LIVE"])
    _cx(draw, "SECOND HALF UNDERWAY", _f(38, bold=True), 160, 600, "white")
    _draw_match_center(draw, img, home, away, f"{sh} - {sa}", 260, EVENT_COLORS["LIVE"])
    
    if comp:
        _cx(draw, comp.upper(), _f(24, bold=True), 1080, 600, "gray")
    path = "post_image.png"
    img.save(path)
    return path

def fulltime_image(home, away, sh, sa, scorers, comp):
    img, draw = _draw_pro_base("FULL TIME", EVENT_COLORS["FULLTIME"])
    _draw_match_center(draw, img, home, away, f"{sh} - {sa}", 160, EVENT_COLORS["FULLTIME"])
    
    y_pos = 580
    draw.rounded_rectangle([(150, y_pos), (1050, y_pos + 420)], 24, fill=(18, 18, 32), outline=EVENT_COLORS["FULLTIME"], width=2)
    _cx(draw, "MATCH DAY SUMMARY", _f(32, bold=True), y_pos + 30, 600, EVENT_COLORS["FULLTIME"])
    _draw_accent_line(draw, y_pos + 85, (100, 100, 120))
    
    y = y_pos + 120
    if scorers:
        _cx(draw, "GOALS:", _f(22, bold=True), y, 600, "gray")
        y += 40
        for s in scorers[:5]:
            _cx(draw, s.upper(), _f(26, bold=True), y, 600, "white")
            y += 45
    else:
        _cx(draw, "GOALLESS ENCOUNTER", _f(30, bold=True), y + 80, 600, "lightgray")
        
    if comp:
        _cx(draw, comp.upper(), _f(24, bold=True), 1100, 600, "gray")
        
    path = "post_image.png"
    img.save(path)
    return path

def summary_image(home, away, sh, sa, events, comp):
    img, draw = _draw_pro_base("SUMMARY", EVENT_COLORS["SUMMARY"])
    _draw_match_center(draw, img, home, away, f"{sh} - {sa}", 120, EVENT_COLORS["SUMMARY"])
    
    y_pos = 540
    draw.rounded_rectangle([(150, y_pos), (1050, y_pos + 520)], 24, fill=(18, 18, 32), outline=(100, 100, 120), width=2)
    _cx(draw, "MATCH TIMELINE", _f(32, bold=True), y_pos + 30, 600, EVENT_COLORS["SUMMARY"])
    _draw_accent_line(draw, y_pos + 85, (100, 100, 120))
    
    y = y_pos + 125
    for e in events[:7]:
        _cx(draw, e.upper(), _f(24, bold=True), y, 600, "lightgray")
        y += 50
        
    if comp:
        _cx(draw, comp.upper(), _f(24, bold=True), 1110, 600, "gray")
        
    path = "post_image.png"
    img.save(path)
    return path

def schedule_image(lines, date_str):
    img, draw = _draw_pro_base("MATCH SCHEDULE", (40, 140, 255))
    _cx(draw, date_str.upper(), _f(32, bold=True), 140, 600, "lightblue")
    
    # Solid background for the list
    draw.rounded_rectangle([(100, 210), (1100, 1080)], 24, fill=(18, 18, 32), outline=(40, 140, 255), width=2)
    
    y = 250
    for l in lines[:7]:
        parts = l.split("  ") if "  " in l else [l]
        _cx(draw, parts[0].upper(), _f(30, bold=True), y, 600, "white")
        if len(parts) > 1:
            _cx(draw, parts[1].upper(), _f(22), y + 42, 600, "gray")
        y += 110
        
    _cx(draw, "FOLLOW PAGE FOR LIVE REALTIME GRAPHICS & UPDATES", _f(20, bold=True), 1120, 600, "gray")
    path = "post_image.png"
    img.save(path)
    return path

def lineup_image(home, away, home_starters, home_bench, away_starters, away_bench, comp):
    img, draw = _draw_pro_base("LINEUPS", EVENT_COLORS["LIVE"])
    _draw_match_center(draw, img, home, away, "VS", 120, EVENT_COLORS["LIVE"])
    
    y = 500
    # Left Card (Home)
    draw.rounded_rectangle([(80, y), (560, y + 540)], 24, fill=(18, 18, 32), outline=(255, 255, 255, 15), width=2)
    _cx(draw, "STARTING XI", _f(26, bold=True), y + 25, 320, EVENT_COLORS["LIVE"])
    _draw_accent_line(draw, y + 70, (100, 100, 120))
    
    line_y = y + 90
    for p in home_starters[:9]:
        name = p.get("name", "")[:18]
        pos = p.get("position", "")[:4]
        draw.text((120, line_y), f"{pos:>4}", fill="gray", font=_f(18))
        draw.text((190, line_y), name.upper(), fill="white", font=_f(18, bold=True))
        line_y += 45
        
    # Right Card (Away)
    draw.rounded_rectangle([(640, y), (1120, y + 540)], 24, fill=(18, 18, 32), outline=(255, 255, 255, 15), width=2)
    _cx(draw, "STARTING XI", _f(26, bold=True), y + 25, 880, EVENT_COLORS["LIVE"])
    _draw_accent_line(draw, y + 70, (100, 100, 120))
    
    line_y = y + 90
    for p in away_starters[:9]:
        name = p.get("name", "")[:18]
        pos = p.get("position", "")[:4]
        draw.text((680, line_y), f"{pos:>4}", fill="gray", font=_f(18))
        draw.text((750, line_y), name.upper(), fill="white", font=_f(18, bold=True))
        line_y += 45
        
    # Bench
    y_bench = 1065
    draw.rounded_rectangle([(150, y_bench), (1050, y_bench + 70)], 15, fill=(24, 24, 40))
    all_bench = [p.get("name","") for p in (home_bench[:2] + away_bench[:2])]
    if all_bench:
        _cx(draw, f"BENCH PREVIEW: {', '.join(all_bench).upper()}", _f(18, bold=True), y_bench + 25, 600, "gray")
        
    if comp:
        _cx(draw, comp.upper(), _f(22, bold=True), 1150, 600, "gray")
        
    path = "post_image.png"
    img.save(path)
    return path
