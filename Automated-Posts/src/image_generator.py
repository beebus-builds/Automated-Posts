from PIL import Image, ImageDraw, ImageFont
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
    "guinea": "gn", "gabon": "ga", "angola": "ao", "mozambique": "mz",
    "congo": "cg", "uganda": "ug", "rwanda": "rw", "madagascar": "mg",
    "niger": "ne", "chad": "td", "ethiopia": "et", "kenya": "ke",
    "tanzania": "tz", "zimbabwe": "zw", "botswana": "bw", "namibia": "na",
    "malawi": "mw", "mauritius": "mu", "gambia": "gm",
}

TEAM_COLORS = {
    "france": (20, 50, 180), "senegal": (0, 133, 67), "brazil": (0, 155, 58),
    "argentina": (116, 172, 223), "germany": (0, 0, 0), "italy": (0, 102, 204),
    "netherlands": (255, 112, 0), "spain": (255, 196, 0), "england": (206, 17, 38),
    "portugal": (0, 153, 0), "belgium": (255, 200, 0), "uruguay": (0, 56, 168),
    "mexico": (0, 104, 71), "usa": (59, 89, 152), "japan": (0, 51, 160),
    "south korea": (0, 68, 134), "australia": (0, 74, 168), "nigeria": (0, 119, 27),
    "cameroon": (0, 115, 47), "morocco": (193, 25, 42), "tunisia": (227, 25, 43),
    "egypt": (206, 17, 38), "ghana": (239, 207, 0), "ivory coast": (255, 145, 0),
    "denmark": (202, 24, 41), "sweden": (0, 106, 167), "croatia": (255, 255, 255),
    "serbia": (0, 70, 150), "switzerland": (213, 43, 30), "poland": (220, 20, 60),
    "turkey": (230, 50, 50), "russia": (40, 40, 100), "ukraine": (0, 87, 184),
    "peru": (209, 40, 40), "colombia": (255, 200, 0), "chile": (0, 57, 166),
    "ecuador": (255, 200, 0), "paraguay": (206, 50, 50), "venezuela": (200, 180, 0),
    "costa rica": (0, 57, 166), "honduras": (0, 100, 180), "jamaica": (0, 119, 27),
    "canada": (255, 50, 50), "qatar": (128, 0, 32), "saudi arabia": (0, 107, 44),
    "china": (222, 45, 38), "india": (255, 153, 51), "south africa": (0, 120, 50),
    "algeria": (0, 100, 50), "iraq": (0, 100, 50), "jordan": (200, 0, 0),
    "austria": (200, 0, 0), "bosnia-herzegovina": (0, 70, 150), "czechia": (20, 60, 140),
    "ghana": (0, 100, 50), "panama": (0, 100, 200), "uzbekistan": (30, 120, 60),
}

def _get_code(team):
    t = team.lower().strip()
    if t in COUNTRY_CODES: return COUNTRY_CODES[t]
    for name, code in COUNTRY_CODES.items():
        if name in t or t in name: return code
    return None

def _get_color(team):
    t = team.lower().strip()
    if t in TEAM_COLORS: return TEAM_COLORS[t]
    for name, c in TEAM_COLORS.items():
        if name in t or t in name: return c
    return (60, 60, 80)

def get_flag(team, size=(80, 80)):
    code = _get_code(team)
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

def get_player_img(name, size=(70, 70)):
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

def get_team_badge(team, size=(60, 60)):
    key = team.lower().strip()
    if key in BADGE_CACHE: return BADGE_CACHE[key]
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
                        BADGE_CACHE[key] = img
                        return img
    except: pass
    BADGE_CACHE[key] = None
    return None

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
    """Center text horizontally at a specific x coordinate"""
    b = draw.textbbox((0, 0), text, font=font)
    w = b[2] - b[0]
    draw.text((cx - w // 2, y), text, fill=fill, font=font)

def _create_base():
    _init()
    img = Image.new("RGB", (1200, 630), (14, 14, 28))
    draw = ImageDraw.Draw(img)
    # Subtle gradient overlay
    for i in range(630):
        alpha = int(40 * (1 - i / 630))
        c = (14 + alpha, 14 + alpha, 28 + alpha * 2)
        draw.line([(0, i), (1200, i)], fill=c)
    return img, draw

def _draw_banner(draw, color, label):
    draw.rounded_rectangle([(0, 0), (1200, 70)], radius=0, fill=color)
    _cx(draw, label, _f(38, bold=True), 14, 600, "white")

def _draw_team_block(draw, img, home, away, y_base, score_text=None, accent=None):
    # Home side
    fh = get_flag(home, (84, 84))
    home_x = 150
    if fh:
        img.paste(fh, (home_x - 42, y_base - 20), fh)
    else:
        c = _get_color(home)
        draw.ellipse([(home_x - 42, y_base - 20), (home_x + 42, y_base + 64)], fill=c)
        _cx(draw, home[:3].upper(), _f(28, bold=True), y_base + 5, home_x, "white")

    # Away side
    fa = get_flag(away, (84, 84))
    away_x = 1050
    if fa:
        img.paste(fa, (away_x - 42, y_base - 20), fa)
    else:
        c = _get_color(away)
        draw.ellipse([(away_x - 42, y_base - 20), (away_x + 42, y_base + 64)], fill=c)
        _cx(draw, away[:3].upper(), _f(28, bold=True), y_base + 5, away_x, "white")

    # Team names
    _cx(draw, home.upper(), _f(26, bold=True), y_base + 95, home_x, "white")
    _cx(draw, away.upper(), _f(26, bold=True), y_base + 95, away_x, "white")

    # Separator dot
    cx = 600
    draw.ellipse([(cx - 6, y_base + 15), (cx + 6, y_base + 27)], fill="gray")

    # Score
    if score_text:
        _cx(draw, score_text, _f(72, bold=True), y_base - 5, cx, accent or "white")

    return y_base + 140

def _draw_accent_line(draw, y, color):
    draw.rectangle([(200, y), (1000, y + 2)], fill=color)

EVENT_COLORS = {
    "LIVE": (40, 140, 255), "GOAL": (255, 215, 0), "RED": (220, 40, 40),
    "YELLOW": (255, 200, 0), "FULLTIME": (50, 200, 50), "HALFTIME": (255, 165, 0),
    "SUB": (140, 80, 200), "SUMMARY": (60, 60, 100),
}

EVENT_LABELS = {
    "LIVE": "LIVE", "GOAL": "GOAL", "RED": "RED CARD", "YELLOW": "YELLOW CARD",
    "FULLTIME": "FULL TIME", "HALFTIME": "HALF TIME", "SUB": "SUBSTITUTION",
    "SUMMARY": "MATCH SUMMARY",
}

def live_image(home, away, comp, time_str=""):
    img, draw = _create_base()
    _draw_banner(draw, EVENT_COLORS["LIVE"], EVENT_LABELS["LIVE"])
    _draw_team_block(draw, img, home, away, 170)
    if time_str:
        _cx(draw, f"Kickoff: {time_str} UTC", _f(24), 380, 600, (100, 180, 255))
    if comp:
        _draw_accent_line(draw, 440, EVENT_COLORS["LIVE"])
        _cx(draw, comp, _f(20), 450, 600, "gray")
    path = "post_image.png"; img.save(path); return path

def goal_image(home, away, sh, sa, scorer, minute, assist, comp):
    img, draw = _create_base()
    _draw_banner(draw, EVENT_COLORS["GOAL"], "GOAL")
    _draw_team_block(draw, img, home, away, 120, f"{sh} - {sa}", (255, 215, 0))
    pimg = get_player_img(scorer, (70, 70))
    cx = 600
    if pimg:
        mask = Image.new("L", (70, 70), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse([(0, 0), (70, 70)], fill=255)
        img.paste(pimg, (cx - 35, 280), mask)
    else:
        draw.ellipse([(cx - 35, 280), (cx + 35, 350)], fill=(255, 215, 0))
        _cx(draw, scorer[:2].upper(), _f(24, bold=True), 300, cx, (14, 14, 28))
    _cx(draw, f"{scorer}  {minute}'", _f(32, bold=True), 360, cx, (255, 215, 0))
    _draw_accent_line(draw, 300, EVENT_COLORS["GOAL"])
    if assist:
        _cx(draw, f"Assist: {assist}", _f(22), 410, 600, "gray")
    if comp:
        _cx(draw, comp, _f(20), 500, 600, "gray")
    path = "post_image.png"; img.save(path); return path

def card_image(team, player, minute, card_type, comp):
    key = "RED" if "RED" in card_type.upper() else "YELLOW"
    img, draw = _create_base()
    _draw_banner(draw, EVENT_COLORS[key], EVENT_LABELS[key])
    cx = 600
    pimg = get_player_img(player, (80, 80))
    if pimg:
        mask = Image.new("L", (80, 80), 0)
        ImageDraw.Draw(mask).ellipse([(0, 0), (80, 80)], fill=255)
        img.paste(pimg, (cx - 40, 120), mask)
    else:
        fg = get_flag(team, (80, 80))
        if fg:
            img.paste(fg, (cx - 40, 120), fg)
        else:
            c = _get_color(team)
            draw.ellipse([(cx - 40, 120), (cx + 40, 200)], fill=c)
            _cx(draw, team[:3].upper(), _f(26, bold=True), 140, cx, "white")
    _cx(draw, team.upper(), _f(28, bold=True), 220, cx, "white")
    _draw_accent_line(draw, 260, EVENT_COLORS[key])
    _cx(draw, f"{player}  {minute}'", _f(30, bold=True), 275, cx, EVENT_COLORS[key])
    if comp:
        _cx(draw, comp, _f(20), 450, 600, "gray")
    path = "post_image.png"; img.save(path); return path

def sub_image(team, player_off, player_on, minute, comp):
    img, draw = _create_base()
    _draw_banner(draw, EVENT_COLORS["SUB"], EVENT_LABELS["SUB"])
    fg = get_flag(team, (70, 70))
    cx = 600
    if fg:
        img.paste(fg, (cx - 35, 120), fg)
    else:
        c = _get_color(team)
        draw.ellipse([(cx - 35, 120), (cx + 35, 190)], fill=c)
        _cx(draw, team[:3].upper(), _f(24, bold=True), 135, cx, "white")
    _cx(draw, team.upper(), _f(26, bold=True), 210, cx, "white")
    _cx(draw, f"OFF: {player_off}", _f(26), 270, cx, (255, 100, 100))
    _cx(draw, f"ON:  {player_on}", _f(26), 310, cx, (100, 255, 100))
    _cx(draw, f"{minute}'", _f(24), 360, cx, "gray")
    if comp:
        _cx(draw, comp, _f(20), 450, 600, "gray")
    path = "post_image.png"; img.save(path); return path

def halftime_image(home, away, sh, sa, scorers_text, comp):
    img, draw = _create_base()
    _draw_banner(draw, EVENT_COLORS["HALFTIME"], EVENT_LABELS["HALFTIME"])
    _draw_team_block(draw, img, home, away, 140, f"{sh} - {sa}", (255, 165, 0))
    if scorers_text:
        _cx(draw, f"Scorers: {scorers_text}", _f(22), 350, 600, "lightgray")
    _cx(draw, "Second half coming up!", _f(24), 400, 600, (255, 200, 100))
    if comp:
        _cx(draw, comp, _f(20), 450, 600, "gray")
    path = "post_image.png"; img.save(path); return path

def secondhalf_image(home, away, sh, sa, comp):
    img, draw = _create_base()
    _draw_banner(draw, EVENT_COLORS["LIVE"], "SECOND HALF")
    _draw_team_block(draw, img, home, away, 150, f"{sh} - {sa}")
    if comp:
        _cx(draw, comp, _f(20), 450, 600, "gray")
    path = "post_image.png"; img.save(path); return path

def fulltime_image(home, away, sh, sa, scorers, comp):
    img, draw = _create_base()
    _draw_banner(draw, EVENT_COLORS["FULLTIME"], EVENT_LABELS["FULLTIME"])
    _draw_team_block(draw, img, home, away, 120, f"{sh} - {sa}", (50, 200, 50))
    _cx(draw, "FULL TIME", _f(26, bold=True), 270, 600, (50, 200, 50))
    y = 320
    for s in scorers[:4]:
        _cx(draw, s, _f(22), y, 600, "lightgray"); y += 30
    if comp:
        _cx(draw, comp, _f(20), 450, 600, "gray")
    path = "post_image.png"; img.save(path); return path

def summary_image(home, away, sh, sa, events, comp):
    img, draw = _create_base()
    _draw_banner(draw, EVENT_COLORS["SUMMARY"], EVENT_LABELS["SUMMARY"])
    _draw_team_block(draw, img, home, away, 80, f"{sh} - {sa}")
    _draw_accent_line(draw, 235, (80, 80, 120))
    y = 255
    for e in events[:6]:
        _cx(draw, e, _f(20), y, 600, "lightgray"); y += 28
    path = "post_image.png"; img.save(path); return path

POS_ABBR = {"Goalkeeper": "GK", "Defender": "DF", "Midfielder": "MF", "Attacker": "FW"}

def lineup_image(home, away, home_starters, home_bench, away_starters, away_bench, comp):
    W, H = 1200, 900
    _init()
    img = Image.new("RGB", (W, H), (14, 14, 28))
    draw = ImageDraw.Draw(img)
    for i in range(H):
        alpha = int(30 * (1 - i / H))
        c = (14 + alpha, 14 + alpha, 28 + alpha * 2)
        draw.line([(0, i), (W, i)], fill=c)
    draw.rectangle([(0, 0), (W, 70)], fill=(40, 140, 255))
    _cx(draw, "STARTING LINEUPS", _f(36, bold=True), 14, 600, "white")

    def draw_squad(players, bench, x_center, team_name, y_start, color):
        _cx(draw, team_name.upper(), _f(28, bold=True), y_start, x_center, color)
        y = y_start + 50
        for p in players[:11]:
            name = p.get("name", "Unknown")
            num = p.get("shirtNumber")
            pos = POS_ABBR.get(p.get("position", ""), p.get("position", "")[:2].upper())
            num_str = f"{num}" if num else "-"
            bg_color = (color[0] // 3, color[1] // 3, color[2] // 3)
            pimg = get_player_img(name, (32, 32))
            lx = x_center - 230
            if pimg:
                mask = Image.new("L", (32, 32), 0)
                ImageDraw.Draw(mask).ellipse([(0, 0), (32, 32)], fill=255)
                img.paste(pimg, (lx, y + 3), mask)
                lx += 40
            draw.rounded_rectangle([(x_center - 240, y), (x_center + 240, y + 38)], radius=6, fill=bg_color, outline=color)
            _cx(draw, num_str, _f(18, bold=True), y + 5, x_center - 210, color)
            _cx(draw, pos, _f(16), y + 6, x_center - 160, "gray")
            _cx(draw, name, _f(20), y + 6, x_center + 20, "white")
            y += 44
        if bench:
            y += 10
            _cx(draw, "SUBS", _f(18, bold=True), y, x_center, "gray")
            y += 30
            for p in bench[:5]:
                name = p.get("name", "")
                num = p.get("shirtNumber")
                num_str = f"{num}" if num else "-"
                _cx(draw, f"{num_str}  {name}", _f(18), y, x_center, "lightgray")
                y += 28

    home_color = _get_color(home)
    away_color = _get_color(away)
    draw_squad(home_starters or [], home_bench or [], 300, home, 90, home_color)
    draw_squad(away_starters or [], away_bench or [], 900, away, 90, away_color)

    if comp:
        _cx(draw, comp, _f(20), H - 40, 600, "gray")
    path = "post_image.png"; img.save(path); return path

def schedule_image(lines, date_str):
    img, draw = _create_base()
    _draw_banner(draw, (40, 140, 255), "MATCH DAY")
    _cx(draw, date_str, _f(22), 90, 600, "lightgray")
    y = 150
    for l in lines[:6]:
        parts = l.split("  ") if "  " in l else [l]
        _cx(draw, parts[0], _f(26, bold=True), y, 600, "white")
        if len(parts) > 1:
            _cx(draw, parts[1], _f(20), y + 30, 600, "gray")
        y += 70
    _cx(draw, "Follow for live updates!", _f(18), 560, 600, "gray")
    path = "post_image.png"; img.save(path); return path
