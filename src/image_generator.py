from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, requests, io
from math import sin, pi
import random

# --- BRAND CONSTANTS & HELPERS ---
COLORS = {
    "NAVY": (26, 35, 50),
    "NAVY_DARK": (13, 20, 25),
    "RED": (220, 20, 60),
    "YELLOW": (255, 215, 0),
    "WHITE": (255, 255, 255),
    "CREAM": (245, 245, 220),
    "BLACK": (0, 0, 0),
    "GRAY": (128, 128, 128)
}

def _f(size, bold=False):
    return ImageFont.load_default()

def _cx(draw, text, font, y, cx, fill="white", outline=None):
    b = draw.textbbox((0, 0), text, font=font)
    w = b[2] - b[0]
    if outline:
        draw.text((cx - w // 2 - 2, y - 2), text, fill=outline, font=font)
    draw.text((cx - w // 2, y), text, fill=fill, font=font)

def get_player_img(name, size=(400, 400)):
    # Placeholder: In production, this fetches and caches player images
    return Image.new("RGBA", size, (200, 200, 200, 255))

def get_flag(team, size=(120, 80)):
    return Image.new("RGBA", size, (100, 100, 100, 255))

# --- TEMPLATE IMPLEMENTATIONS ---

def draw_goal_card(scorer, minute, team_name, player_img=None, flag_img=None):
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), COLORS["NAVY_DARK"])
    draw = ImageDraw.Draw(img)
    
    # 1. Top Section - "GOAL!" (Y=80, 120pt, White + Red Outline)
    _cx(draw, "GOAL!", _f(120, bold=True), 80, W//2, COLORS["WHITE"], outline=COLORS["RED"])
    
    # 2. Middle Section - Player Photo (400x400 circle at Y=250)
    p_size = 400
    if player_img:
        mask = Image.new("L", (p_size, p_size), 0)
        ImageDraw.Draw(mask).ellipse([(0,0), (p_size, p_size)], fill=255)
        img.paste(player_img.resize((p_size, p_size)), (W//2 - p_size//2, 250), mask)
    draw.ellipse([(W//2 - p_size//2, 250), (W//2 + p_size//2, 250 + p_size)], outline="white", width=8)
    
    # 3. Player Name & Team
    _cx(draw, scorer.upper(), _f(48, bold=True), 680, W//2, COLORS["WHITE"])
    _cx(draw, team_name.upper(), _f(32), 740, W//2, COLORS["RED"])
    
    # 4. Bottom Section - Hexagon Badge
    pts = [(440, 820), (540, 800), (640, 820), (640, 960), (540, 980), (440, 960)]
    draw.polygon(pts, fill=COLORS["RED"])
    _cx(draw, f"{minute}'", _f(56, bold=True), 860, 540, COLORS["WHITE"])
    
    img.save("post_image.png")
    return "post_image.png"

# [Implement draw_yellow_card, draw_red_card, draw_sub_card, etc. following same pattern...]

def draw_yellow_card(player, team, minute, player_img=None):
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), COLORS["NAVY_DARK"])
    draw = ImageDraw.Draw(img)
    # [Implementation following Yellow Card specs...]
    img.save("post_image.png")
    return "post_image.png"

# ... (Implement others similarly)
