from PIL import Image, ImageDraw, ImageFont
import os, requests, io
from urllib.parse import quote

FONT_BOLD = None
FONT_REGULAR = None
FLAG_CACHE = {}

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
    "costa rica": "cr", "honduras": "hn", "jamaica": "jm", "trinidad and tobago": "tt",
    "haiti": "ht", "cuba": "cu", "bolivia": "bo", "ireland": "ie",
    "northern ireland": "gb-nir", "iceland": "is", "slovakia": "sk",
    "slovenia": "si", "montenegro": "me", "albania": "al", "north macedonia": "mk",
    "georgia": "ge", "armenia": "am", "azerbaijan": "az", "kazakhstan": "kz",
    "finland": "fi", "luxembourg": "lu", "cyprus": "cy", "israel": "il",
    "bulgaria": "bg", "latvia": "lv", "estonia": "ee", "lithuania": "lt",
    "moldova": "md", "bosnia": "ba", "ivory coast": "ci", "cote d'ivoire": "ci",
    "mali": "ml", "burkina faso": "bf", "zambia": "zm", "cape verde": "cv",
    "guinea": "gn", "gabon": "ga", "angola": "ao", "mozambique": "mz",
    "congo": "cg", "equatorial guinea": "gq", "benin": "bj", "togo": "tg",
    "sudan": "sd", "uganda": "ug", "rwanda": "rw", "madagascar": "mg",
    "comoros": "km", "mauritania": "mr", "niger": "ne", "chad": "td",
    "central african republic": "cf", "sierra leone": "sl", "liberia": "lr",
    "ethiopia": "et", "kenya": "ke", "tanzania": "tz", "zimbabwe": "zw",
    "botswana": "bw", "namibia": "na", "lesotho": "ls", "swaziland": "sz",
    "malawi": "mw", "seychelles": "sc", "mauritius": "mu", "gambia": "gm",
    "guinea-bissau": "gw", "sao tome and principe": "st",
}

def get_flag_url(team_name):
    key = team_name.lower().strip()
    code = COUNTRY_CODES.get(key)
    if not code:
        for name, c in COUNTRY_CODES.items():
            if name in key or key in name:
                code = c; break
    if code:
        return f"https://flagcdn.com/w80/{code}.png"
    return None

def get_flag_image(team_name, size=(64, 64)):
    url = get_flag_url(team_name)
    if not url:
        return None
    if url in FLAG_CACHE:
        return FLAG_CACHE[url]
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            img = Image.open(io.BytesIO(r.content)).convert("RGBA").resize(size, Image.LANCZOS)
            FLAG_CACHE[url] = img
            return img
    except:
        pass
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

def _c(draw, text, font, y, fill="white", center=True):
    b = draw.textbbox((0, 0), text, font=font)
    w = b[2] - b[0]
    x = (1200 - w) // 2 if center else 0
    draw.text((x, y), text, fill=fill, font=font)
    return y + (b[3] - b[1]) + 6

def _draw_team_block(draw, img, home, away, y_pos, score_text="", highlight_color=None):
    flag_h = get_flag_image(home, (80, 80))
    flag_a = get_flag_image(away, (80, 80))

    if flag_h:
        img.paste(flag_h, (200, y_pos), flag_h)
        tx = 300
    else:
        tx = 220
        draw.rounded_rectangle([(180, y_pos), (280, y_pos+80)], 10, fill=(60, 60, 80))
        _c(draw, home[:3].upper(), _f(32, bold=True), y_pos+20, fill="white", center=False)

    _c(draw, home, _f(36, bold=True), y_pos+20, "white")
    draw.text((tx, y_pos+60), home, fill="gray", font=_f(18))

    cx = 600
    if score_text:
        _c(draw, score_text, _f(72, bold=True), y_pos-10, fill=highlight_color or "white")

    if flag_a:
        img.paste(flag_a, (800, y_pos), flag_a)
    else:
        draw.rounded_rectangle([(780, y_pos), (880, y_pos+80)], 10, fill=(60, 60, 80))
        _c(draw, away[:3].upper(), _f(32, bold=True), y_pos+20, fill="white", center=False)

    _c(draw, away, _f(36, bold=True), y_pos+20, "white")
    draw.text((840, y_pos+60), away, fill="gray", font=_f(18))

BANNER = {
    "LIVE": ((40, 140, 255), "LIVE"),
    "GOAL": ((255, 215, 0), "GOAL"),
    "RED": ((220, 40, 40), "RED CARD"),
    "YELLOW": ((255, 200, 0), "YELLOW CARD"),
    "FULLTIME": ((50, 200, 50), "FULL TIME"),
    "HALFTIME": ((255, 165, 0), "HALF TIME"),
    "SUB": ((140, 80, 200), "SUBSTITUTION"),
    "SUMMARY": ((30, 30, 60), "MATCH SUMMARY"),
}

def _create_base(color, label):
    _init()
    img = Image.new("RGB", (1200, 630), (18, 18, 34))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (1200, 80)], fill=color)
    _c(draw, f"  {label}  ", _f(44, bold=True), 14)
    return img, draw

def live_image(home, away, comp, time_str=""):
    img, draw = _create_base(*BANNER["LIVE"])
    _draw_team_block(draw, img, home, away, 150, "vs", (40, 140, 255))
    if time_str:
        _c(draw, f"Kickoff: {time_str} UTC", _f(26), 400, "lightblue")
    if comp:
        _c(draw, comp, _f(22), 540, "gray")
    p = "post_image.png"; img.save(p); return p

def goal_image(home, away, sh, sa, scorer, minute, assist, comp):
    img, draw = _create_base(*BANNER["GOAL"])
    score = f"{sh} - {sa}"
    _draw_team_block(draw, img, home, away, 120, score, (255, 215, 0))
    _c(draw, f"{scorer}  {minute}'", _f(36), 310, (255, 215, 0))
    if assist:
        _c(draw, f"Assist: {assist}", _f(24), 380, "gray")
    if comp:
        _c(draw, comp, _f(22), 540, "gray")
    p = "post_image.png"; img.save(p); return p

def card_image(team, player, minute, card_type, comp):
    key = "RED" if "RED" in card_type.upper() else "YELLOW"
    img, draw = _create_base(*BANNER[key])
    flag = get_flag_image(team, (80, 80))
    if flag:
        img.paste(flag, (200, 140), flag)
    else:
        draw.rounded_rectangle([(200, 140), (300, 220)], 10, fill=(60, 60, 80))
        _c(draw, team[:3].upper(), _f(32, bold=True), 155)
    draw.text((320, 150), team, fill="white", font=_f(40, bold=True))
    c = (220, 40, 40) if key == "RED" else (255, 200, 0)
    _c(draw, f"{player}  {minute}'", _f(32), 300, c)
    if comp:
        _c(draw, comp, _f(22), 540, "gray")
    p = "post_image.png"; img.save(p); return p

def sub_image(team, player_off, player_on, minute, comp):
    img, draw = _create_base(*BANNER["SUB"])
    flag = get_flag_image(team, (80, 80))
    if flag:
        img.paste(flag, (100, 130), flag)
    draw.text((220, 145), team, fill="white", font=_f(40, bold=True))
    _c(draw, f"OFF: {player_off}", _f(28), 280, (255, 100, 100))
    _c(draw, f"ON:  {player_on}", _f(28), 340, (100, 255, 100))
    _c(draw, f"{minute}'", _f(28), 420, "gray")
    if comp:
        _c(draw, comp, _f(22), 540, "gray")
    p = "post_image.png"; img.save(p); return p

def halftime_image(home, away, sh, sa, scorers_text, comp):
    img, draw = _create_base(*BANNER["HALFTIME"])
    _draw_team_block(draw, img, home, away, 120, f"{sh} - {sa}", (255, 165, 0))
    if scorers_text:
        _c(draw, scorers_text, _f(24), 330, "lightgray")
    _c(draw, "Second half coming up!", _f(26), 430, "orange")
    if comp:
        _c(draw, comp, _f(22), 540, "gray")
    p = "post_image.png"; img.save(p); return p

def secondhalf_image(home, away, sh, sa, comp):
    img, draw = _create_base(*BANNER["SECOND_HALF"])
    _draw_team_block(draw, img, home, away, 140, f"{sh} - {sa}")
    if comp:
        _c(draw, comp, _f(22), 540, "gray")
    p = "post_image.png"; img.save(p); return p

def fulltime_image(home, away, sh, sa, scorers, comp):
    img, draw = _create_base(*BANNER["FULLTIME"])
    _draw_team_block(draw, img, home, away, 100, f"{sh} - {sa}", (50, 200, 50))
    _c(draw, "FULL TIME", _f(28), 250, (50, 200, 50))
    y = 310
    for s in scorers[:4]:
        _c(draw, s, _f(22), y, "lightgray"); y += 30
    if comp:
        _c(draw, comp, _f(22), 540, "gray")
    p = "post_image.png"; img.save(p); return p

def summary_image(home, away, sh, sa, events, comp):
    img, draw = _create_base(*BANNER["SUMMARY"])
    _draw_team_block(draw, img, home, away, 70, f"{sh} - {sa}")
    y = 230
    for e in events[:6]:
        _c(draw, e, _f(20), y, "lightgray"); y += 28
    p = "post_image.png"; img.save(p); return p

def schedule_image(lines, date_str):
    img, draw = _create_base((40, 140, 255), "MATCH DAY")
    _c(draw, date_str, _f(24), 90, "lightgray")
    y = 140
    for l in lines[:6]:
        parts = l.split("  ")
        if parts:
            _c(draw, "  ".join(parts[:2]), _f(26), y)
            if len(parts) > 2:
                _c(draw, parts[-1], _f(20), y+30, "gray")
            y += 60
    _c(draw, "Follow for live updates!", _f(20), 560, "gray")
    p = "post_image.png"; img.save(p); return p
