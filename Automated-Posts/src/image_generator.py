from PIL import Image, ImageDraw, ImageFont
import os

FONT_BOLD = None
FONT_REGULAR = None

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

def _c(draw, text, font, y, fill="white"):
    b = draw.textbbox((0, 0), text, font=font)
    draw.text(((1200 - (b[2] - b[0])) // 2, y), text, fill=fill, font=font)
    return y + (b[3] - b[1]) + 8

def _base(color, label):
    _init()
    img = Image.new("RGB", (1200, 630), (18, 18, 34))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (1200, 80)], fill=color)
    _c(draw, label, _f(44, bold=True), 14)
    return img, draw

BANNER = {
    "LIVE": ((40, 140, 255), "LIVE"),
    "GOAL": ((255, 215, 0), "GOAL"),
    "RED": ((220, 40, 40), "RED CARD"),
    "YELLOW": ((255, 200, 0), "YELLOW CARD"),
    "FULLTIME": ((50, 200, 50), "FULL TIME"),
    "HALFTIME": ((255, 165, 0), "HALF TIME"),
    "SUB": ((140, 80, 200), "SUBSTITUTION"),
    "SECOND_HALF": ((40, 140, 255), "SECOND HALF"),
    "SUMMARY": ((30, 30, 60), "MATCH SUMMARY"),
}

def live_image(home, away, comp, time_str=""):
    img, draw = _base(*BANNER["LIVE"])
    _c(draw, f"{home} vs {away}", _f(52, bold=True), 180)
    if time_str: _c(draw, f"Kickoff: {time_str}", _f(26), 320, "lightblue")
    if comp: _c(draw, comp, _f(22), 540, "gray")
    p = "post_image.png"; img.save(p); return p

def goal_image(home, away, sh, sa, scorer, minute, assist, comp):
    img, draw = _base(*BANNER["GOAL"])
    _c(draw, f"{home} {sh} - {sa} {away}", _f(64, bold=True), 160)
    _c(draw, f"{scorer}  {minute}'", _f(36), 300, (255, 215, 0))
    if assist: _c(draw, f"Assist: {assist}", _f(24), 370, "gray")
    if comp: _c(draw, comp, _f(22), 540, "gray")
    p = "post_image.png"; img.save(p); return p

def card_image(team, player, minute, card_type, comp):
    key = "RED" if "RED" in card_type.upper() else "YELLOW"
    img, draw = _base(*BANNER[key])
    _c(draw, team, _f(56, bold=True), 170)
    c = (220, 40, 40) if key == "RED" else (255, 200, 0)
    _c(draw, f"{player}  {minute}'", _f(36), 300, c)
    if comp: _c(draw, comp, _f(22), 540, "gray")
    p = "post_image.png"; img.save(p); return p

def sub_image(team, player_off, player_on, minute, comp):
    img, draw = _base(*BANNER["SUB"])
    _c(draw, team, _f(46, bold=True), 150)
    _c(draw, f"OUT: {player_off}", _f(30), 270, (255, 100, 100))
    _c(draw, f"IN:  {player_on}", _f(30), 330, (100, 255, 100))
    _c(draw, f"{minute}'", _f(28), 410, "gray")
    if comp: _c(draw, comp, _f(22), 540, "gray")
    p = "post_image.png"; img.save(p); return p

def halftime_image(home, away, sh, sa, scorers_text, comp):
    img, draw = _base(*BANNER["HALFTIME"])
    _c(draw, f"{home} {sh} - {sa} {away}", _f(64, bold=True), 150)
    if scorers_text:
        _c(draw, scorers_text, _f(26), 300, "lightgray")
    _c(draw, "Second half coming up!", _f(24), 450, "orange")
    if comp: _c(draw, comp, _f(22), 540, "gray")
    p = "post_image.png"; img.save(p); return p

def secondhalf_image(home, away, sh, sa, comp):
    img, draw = _base(*BANNER["SECOND_HALF"])
    _c(draw, f"{home} vs {away}", _f(52, bold=True), 170)
    _c(draw, f"{sh} - {sa}", _f(48, bold=True), 280)
    if comp: _c(draw, comp, _f(22), 540, "gray")
    p = "post_image.png"; img.save(p); return p

def fulltime_image(home, away, sh, sa, scorers, comp):
    img, draw = _base(*BANNER["FULLTIME"])
    _c(draw, f"{home} {sh} - {sa} {away}", _f(64, bold=True), 140)
    _c(draw, "FULL TIME", _f(28), 230, (50, 200, 50))
    y = 290
    for s in scorers:
        _c(draw, s, _f(22), y, "lightgray"); y += 30
    if comp: _c(draw, comp, _f(22), 540, "gray")
    p = "post_image.png"; img.save(p); return p

def summary_image(home, away, sh, sa, events, comp):
    img, draw = _base(*BANNER["SUMMARY"])
    _c(draw, f"{home} {sh} - {sa} {away}", _f(52, bold=True), 100)
    _c(draw, "MATCH SUMMARY", _f(24), 180, "gray")
    y = 230
    for e in events[:8]:
        _c(draw, e, _f(20), y, "lightgray"); y += 28
    p = "post_image.png"; img.save(p); return p

def schedule_image(lines, date_str):
    img, draw = _base((40, 140, 255), "MATCH DAY")
    _c(draw, date_str, _f(24), 90, "lightgray")
    y = 150
    for l in lines[:6]:
        _c(draw, l.strip(), _f(28), y); y += 45
    _c(draw, "Follow for live updates!", _f(20), 550, "gray")
    p = "post_image.png"; img.save(p); return p
