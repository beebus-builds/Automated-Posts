from PIL import Image, ImageDraw, ImageFont
import os

FONT_BOLD = None
FONT_REGULAR = None

def _init_fonts():
    global FONT_BOLD, FONT_REGULAR
    candidates_bold = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/ARIALBD.TTF",
    ]
    candidates_regular = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/ARIAL.TTF",
    ]
    for p in candidates_bold:
        if os.path.exists(p):
            FONT_BOLD = p
            break
    for p in candidates_regular:
        if os.path.exists(p):
            FONT_REGULAR = p
            break

def _get_font(size, bold=False):
    path = FONT_BOLD if bold else FONT_REGULAR
    if path:
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def _center_text(draw, text, font, y, fill="white"):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    draw.text(((1200 - w) // 2, y), text, fill=fill, font=font)
    return y + (bbox[3] - bbox[1]) + 10

BANNER = {
    "GOAL": ("GOAL!", (255, 215, 0)),
    "RED_CARD": ("RED CARD", (220, 40, 40)),
    "YELLOW_CARD": ("YELLOW CARD", (255, 200, 0)),
    "LIVE": ("LIVE", (40, 140, 255)),
    "FULL_TIME": ("FULL TIME", (50, 200, 50)),
    "HALF_TIME": ("HALF TIME", (255, 165, 0)),
}

def _draw_base(event_type):
    _init_fonts()
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), (18, 18, 34))
    draw = ImageDraw.Draw(img)
    label, color = BANNER.get(event_type, ("UPDATE", (100, 100, 100)))
    draw.rectangle([(0, 0), (W, 80)], fill=color)
    font_large = _get_font(44, bold=True)
    _center_text(draw, f"  {label}  ", font_large, 12, "white")
    return img, draw

def generate_goal_image(home, away, score_home, score_away, scorer, minute, assist, competition):
    img, draw = _draw_base("GOAL")
    font_score = _get_font(72, bold=True)
    font_info = _get_font(32)
    font_small = _get_font(22)
    score_text = f"{home}  {score_home} - {score_away}  {away}"
    _center_text(draw, score_text, font_score, 160)
    detail = scorer
    if minute is not None:
        detail += f"  |  {minute}'"
    _center_text(draw, detail, font_info, 320, fill=(255, 215, 0))
    if assist:
        _center_text(draw, f"Assist: {assist}", font_small, 380, fill="gray")
    if competition:
        _center_text(draw, competition, font_small, 540, fill="gray")
    path = "post_image.png"
    img.save(path)
    return path

def generate_card_image(team, player, minute, card_type, competition):
    event = "RED_CARD" if "RED" in card_type.upper() else "YELLOW_CARD"
    img, draw = _draw_base(event)
    font_team = _get_font(56, bold=True)
    font_info = _get_font(36)
    font_small = _get_font(22)
    _center_text(draw, team, font_team, 170)
    detail = player
    if minute is not None:
        detail += f"  |  {minute}'"
    color = (220, 40, 40) if "RED" in card_type.upper() else (255, 200, 0)
    _center_text(draw, detail, font_info, 300, fill=color)
    if competition:
        _center_text(draw, competition, font_small, 540, fill="gray")
    path = "post_image.png"
    img.save(path)
    return path

def generate_fulltime_image(home, away, score_home, score_away, goals_list, competition):
    img, draw = _draw_base("FULL_TIME")
    font_score = _get_font(72, bold=True)
    font_goal = _get_font(22)
    font_small = _get_font(22)
    score_text = f"{home}  {score_home} - {score_away}  {away}"
    _center_text(draw, score_text, font_score, 160)
    y = 280
    for g in goals_list:
        _center_text(draw, g, font_goal, y, fill="lightgray")
        y += 35
    if competition:
        _center_text(draw, competition, font_small, 540, fill="gray")
    path = "post_image.png"
    img.save(path)
    return path

def generate_live_image(home, away, competition, kickoff):
    img, draw = _draw_base("LIVE")
    font_vs = _get_font(60, bold=True)
    font_info = _get_font(28)
    font_small = _get_font(22)
    _center_text(draw, f"{home}  vs  {away}", font_vs, 180)
    if kickoff:
        _center_text(draw, f"Kick-off: {kickoff}", font_info, 330, fill="lightblue")
    if competition:
        _center_text(draw, competition, font_small, 540, fill="gray")
    path = "post_image.png"
    img.save(path)
    return path
