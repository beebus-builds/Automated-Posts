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

import random

def _draw_grunge_bg(draw, W, H, color1, color2):
    # Base deep dark gradient
    for i in range(H):
        alpha = int(30 * (1 - i/H))
        draw.line([(0, i), (W, i)], fill=(8+alpha, 8+alpha, 14+alpha))
    
    # Color splashes (simulated grunge)
    for _ in range(15):
        x = random.randint(0, W)
        y = random.randint(0, H)
        size = random.randint(200, 600)
        # Draw a "splash" of team color with low opacity
        overlay = Image.new("RGBA", (W, H), (0,0,0,0))
        od = ImageDraw.Draw(overlay)
        c = color1 if random.random() > 0.5 else color2
        od.ellipse([x-size, y-size, x+size, y+size], fill=(c[0], c[1], c[2], 30))
        # Add some "splatters" (small dots)
        for _ in range(20):
            sx, sy = x + random.randint(-size, size), y + random.randint(-size, size)
            od.ellipse([sx, sy, sx+2, sy+2], fill=(c[0], c[1], c[2], 100))
        
        # Use alpha composite to blend into main img
        # This is handled in _draw_pro_base
        return overlay # simplified for this helper

def _draw_pro_base(label, color):
    _init()
    W, H = 1200, 1200
    img = Image.new("RGB", (W, H), (5, 5, 10))
    draw = ImageDraw.Draw(img)
    
    # Atmospheric Radial Glow
    for r in range(H, 0, -20):
        alpha = int(20 * (1 - r/H))
        draw.ellipse([600-r, 600-r, 600+r, 600+r], outline=(color[0], color[1], color[2], alpha), width=2)
    
    # Grunge splatter effects
    overlay = Image.new("RGBA", (W, H), (0,0,0,0))
    od = ImageDraw.Draw(overlay)
    for _ in range(20):
        x, y = random.randint(0, W), random.randint(0, H)
        s = random.randint(100, 400)
        c = color if random.random() > 0.5 else (255, 255, 255)
        od.ellipse([x-s, y-s, x+s, y+s], fill=(c[0], c[1], c[2], 20))
        # Small sparks
        for _ in range(10):
            sx, sy = x + random.randint(-s, s), y + random.randint(-s, s)
            od.ellipse([sx, sy, sx+3, sy+3], fill=(c[0], c[1], c[2], 150))
            
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)
    
    # Top Logo placeholder/Header
    _cx(draw, label.upper(), _f(60, bold=True), 40, 600, "white")
    
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
    img, draw = _draw_pro_base(" ", EVENT_COLORS["GOAL"])
    
    # 1. Background accents (Red/Green split for Portugal match)
    # Red splash on left, Green on right
    overlay = Image.new("RGBA", (1200, 1200), (0,0,0,0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([0, 0, 700, 1200], fill=(200, 0, 0, 40))
    od.rectangle([500, 0, 1200, 1200], fill=(0, 150, 0, 40))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)
    
    # 2. Massive Textured "GOAL!" Text
    # Shadow for depth
    _cx(draw, "GOAL!", _f(240, bold=True), 180, 550, (80, 0, 0))
    # Main white text
    _cx(draw, "GOAL!", _f(240, bold=True), 170, 550, "white")
    
    # 3. Huge Player Cutout (Right Side)
    pimg = get_player_img(scorer, (800, 800))
    if pimg:
        # Positioned to overlap the GOAL text and dominate the right side
        img.paste(pimg, (450, 150), pimg if pimg.mode == "RGBA" else None)
    
    # 4. Scorer Banner (Brush-stroke style)
    banner_color = (200, 0, 0)
    draw.rounded_rectangle([(100, 440), (750, 520)], 15, fill=banner_color, outline="white", width=2)
    _cx(draw, scorer.upper(), _f(70, bold=True), 455, 425, "white")
    
    # Team name below banner
    _cx(draw, home.upper(), _f(40, bold=True), 530, 425, (0, 200, 0))
    
    # 5. Minute with Ball Icon
    _cx(draw, f"{minute}'", _f(60, bold=True), 660, 150, "white")
    
    # 6. Hexagonal Scoreboard at bottom
    points = [(150, 920), (300, 870), (600, 870), (900, 870), (1050, 920), (1050, 1050), (150, 1050)]
    draw.polygon(points, fill=(10, 10, 20), outline="white", width=3)
    
    # Flags in Hexagons
    fh = get_flag(home, (140, 90))
    if fh: img.paste(fh, (210, 890), fh if fh.mode == "RGBA" else None)
    _cx(draw, home.upper(), _f(24, bold=True), 980, 280, "white")
    
    fa = get_flag(away, (140, 90))
    if fa: img.paste(fa, (850, 890), fa if fa.mode == "RGBA" else None)
    _cx(draw, away.upper(), _f(24, bold=True), 980, 920, "white")
    
    # Large Score
    _cx(draw, f"{sh} - {sa}", _f(140, bold=True), 880, 600, "white")
    
    if comp:
        _cx(draw, comp.upper(), _f(24, bold=True), 1120, 600, "gray")
        
    path = "post_image.png"
    img.save(path)
    return path

def card_image(team, player, minute, card_type, comp):
    key = "RED" if "RED" in card_type.upper() else "YELLOW"
    color = EVENT_COLORS[key]
    img, draw = _draw_pro_base(" ", color)
    
    # Grunge Split Background
    overlay = Image.new("RGBA", (1200, 1200), (0,0,0,0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([0, 0, 1200, 1200], fill=(color[0], color[1], color[2], 30))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)
    
    # Massive "YELLOW CARD" or "RED CARD" Text
    _cx(draw, key.upper(), _f(180, bold=True), 150, 600, color)
    _cx(draw, "CARD", _f(140, bold=True), 300, 600, "white")
    
    # Huge Player Cutout (Right Side)
    pimg = get_player_img(player, (700, 700))
    if pimg:
        img.paste(pimg, (500, 300), pimg if pimg.mode == "RGBA" else None)
    
    # The Actual Card Graphic (Floating)
    card_w, card_h = 250, 350
    draw.rounded_rectangle([(150, 300), (150 + card_w, 300 + card_h)], 20, fill=color, outline="white", width=8)
    
    # Name and Team
    draw.rounded_rectangle([(100, 800), (600, 950)], 20, fill=(10, 10, 20), outline=color, width=3)
    _cx(draw, player.upper(), _f(60, bold=True), 830, 350, "white")
    _cx(draw, f"{team.upper()} - {minute}'", _f(30, bold=True), 880, 350, "gray")
    
    if comp:
        _cx(draw, comp.upper(), _f(24, bold=True), 1120, 600, "gray")
        
    path = "post_image.png"
    img.save(path)
    return path

def sub_image(team, player_off, player_on, minute, comp):
    img, draw = _draw_pro_base(" ", EVENT_COLORS["SUB"])
    
    # 1. Red/Green Split Background
    overlay = Image.new("RGBA", (1200, 1200), (0,0,0,0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([0, 0, 600, 1200], fill=(150, 0, 0, 40))
    od.rectangle([600, 0, 1200, 1200], fill=(0, 150, 0, 40))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)
    
    # 2. Massive "SUBSTITUTION" Text
    _cx(draw, "SUBSTITUTION", _f(120, bold=True), 100, 600, "white")
    
    # 3. Large Player Cutouts
    p_size = 700
    p_off = get_player_img(player_off, (p_size, p_size))
    p_on = get_player_img(player_on, (p_size, p_size))
    
    if p_off: img.paste(p_off, (100, 300), p_off if p_off.mode == "RGBA" else None)
    if p_on: img.paste(p_on, (500, 300), p_on if p_on.mode == "RGBA" else None)
    
    # 4. Professional Name Blocks
    # OFF Block
    draw.rounded_rectangle([(100, 850), (550, 950)], 10, fill=(20, 10, 10), outline=(255, 0, 0), width=3)
    _cx(draw, f"OUT {player_off.upper()}", _f(44, bold=True), 870, 325, "white")
    
    # ON Block
    draw.rounded_rectangle([(650, 850), (1100, 950)], 10, fill=(10, 20, 10), outline=(0, 255, 0), width=3)
    _cx(draw, f"IN {player_on.upper()}", _f(44, bold=True), 870, 875, "white")
    
    # 5. Bottom Score/Flags
    points = [(400, 1000), (550, 950), (850, 950), (1000, 1000), (1000, 1100), (400, 1100)]
    draw.polygon(points, fill=(10, 10, 20), outline="white", width=2)
    fh = get_flag(team, (100, 60))
    if fh: img.paste(fh, (450, 970), fh if fh.mode == "RGBA" else None)
    _cx(draw, f"{team.upper()} {minute}'", _f(30, bold=True), 1020, 600, "white")
    
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
    img, draw = _draw_pro_base(" ", EVENT_COLORS["FULLTIME"])
    
    # 1. Atmospheric Background
    overlay = Image.new("RGBA", (1200, 1200), (0,0,0,0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([0, 0, 600, 1200], fill=(50, 0, 0, 30))
    od.rectangle([600, 0, 1200, 1200], fill=(0, 50, 0, 30))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)
    
    # 2. Massive "FULL TIME" Text
    _cx(draw, "FULL TIME", _f(160, bold=True), 150, 600, "white")
    
    # 3. Star Players on sides
    # Home star
    ph = get_player_img(home, (600, 600))
    if ph: img.paste(ph, (0, 400), ph if ph.mode == "RGBA" else None)
    # Away star
    pa = get_player_img(away, (600, 600))
    if pa: img.paste(pa, (600, 400), pa if pa.mode == "RGBA" else None)
    
    # 4. Centered Score Hexagon
    points = [(400, 500), (500, 450), (700, 450), (800, 500), (800, 600), (400, 600)]
    draw.polygon(points, fill=(10, 10, 20), outline="white", width=3)
    
    # Flags
    fh = get_flag(home, (100, 60))
    if fh: img.paste(fh, (420, 470), fh if fh.mode == "RGBA" else None)
    fa = get_flag(away, (100, 60))
    if fa: img.paste(fa, (680, 470), fa if fa.mode == "RGBA" else None)
    
    # Score
    _cx(draw, f"{sh} - {sa}", _f(120, bold=True), 470, 600, "white")
    _cx(draw, home.upper(), _f(24, bold=True), 550, 460, "white")
    _cx(draw, away.upper(), _f(24, bold=True), 550, 740, "white")
    
    # 5. Detailed Match Stats Grid at bottom
    stats_y = 750
    draw.rounded_rectangle([(100, stats_y), (1100, stats_y + 350)], 20, fill=(15, 15, 30), outline="white", width=2)
    
    # Scorer List
    _cx(draw, "MATCH EVENTS", _f(32, bold=True), stats_y + 30, 600, EVENT_COLORS["FULLTIME"])
    y = stats_y + 80
    if scorers:
        for s in scorers[:5]:
            _cx(draw, s.upper(), _f(28), y, 600, "white")
            y += 40
    else:
        _cx(draw, "NO GOALS", _f(28), stats_y + 100, 600, "gray")
        
    # Match Stats (Mocked for look)
    stats = [("POSSESSION", f"{sh*10}% vs {sa*10}%"), ("SHOTS", f"{sh*5} vs {sa*5}"), ("CORNERS", "5 vs 3")]
    for i, (label, val) in enumerate(stats):
        x_pos = 200 + i*300
        draw.rounded_rectangle([(x_pos, 1050), (x_pos + 250, 1120)], 10, fill=(20, 20, 40), outline="gray", width=1)
        _cx(draw, label, _f(18, bold=True), 1060, x_pos + 125, "gray")
        _cx(draw, val, _f(24, bold=True), 1080, x_pos + 125, "white")
    
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
