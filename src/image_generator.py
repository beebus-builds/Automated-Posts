from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, requests, io
from math import sin, pi, cos
import random

# --- BRAND CONSTANTS ---
COLORS = {
    "NAVY": (26, 35, 50),
    "NAVY_DARK": (13, 20, 25),
    "RED": (220, 20, 60),
    "YELLOW": (255, 215, 0),
    "WHITE": (255, 255, 255),
    "CREAM": (245, 245, 220),
    "BLACK": (5, 5, 10),
    "GRAY": (128, 128, 128),
    "LIGHT_GRAY": (200, 200, 200),
    "GREEN": (34, 197, 94),
    "GOLD": (251, 191, 36)
}

# --- DYNAMIC FONT DOWNLOADER ---
FONT_PATHS = {
    "Montserrat-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Bold.ttf",
    "BebasNeue-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-Regular.ttf",
    "Roboto-Regular.ttf": "https://github.com/google/fonts/raw/main/apache/roboto/static/Roboto-Regular.ttf"
}

def _init_fonts():
    os.makedirs("fonts", exist_ok=True)
    for name, url in FONT_PATHS.items():
        path = os.path.join("fonts", name)
        if not os.path.exists(path):
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    with open(path, "wb") as f:
                        f.write(r.content)
            except Exception as e:
                print(f"Error downloading font {name}: {e}")

_init_fonts()

def _f(name, size):
    path = os.path.join("fonts", name)
    if os.path.exists(path):
        try:
            return ImageFont.truetype(path, size)
        except:
            pass
    return ImageFont.load_default()

# --- HELPER DRAWING FUNCTIONS ---

def _cx(draw, text, font, y, cx, fill="white", outline=None, outline_w=3):
    b = draw.textbbox((0, 0), text, font=font)
    w = b[2] - b[0]
    tx, ty = cx - w // 2, y
    if outline:
        for dx in range(-outline_w, outline_w + 1):
            for dy in range(-outline_w, outline_w + 1):
                if dx != 0 or dy != 0:
                    draw.text((tx + dx, ty + dy), text, fill=outline, font=font)
    draw.text((tx, ty), text, fill=fill, font=font)

def draw_mountain_silhouette(draw, fill_color=(13, 20, 25), height=120):
    # Procedural peaks across the 1080px width
    peaks = [
        (0, 1080),
        (0, 1080 - height + 20),
        (150, 1080 - height - 10),
        (300, 1080 - height + 30),
        (450, 1080 - height - 30),
        (600, 1080 - height + 10),
        (750, 1080 - height - 40),
        (900, 1080 - height + 20),
        (1080, 1080 - height - 10),
        (1080, 1080)
    ]
    draw.polygon(peaks, fill=fill_color)

def draw_nepal_flag_brushstroke(img, x, y, width=300, height=150, opacity=100):
    overlay = Image.new("RGBA", (1080, 1080), (0,0,0,0))
    od = ImageDraw.Draw(overlay)
    # Nepali flag double-triangle shape
    points = [
        (x, y),
        (x + width, y + height // 2),
        (x + width // 4, y + height // 2),
        (x + width, y + height),
        (x, y + height)
    ]
    od.polygon(points, fill=(220, 20, 60, opacity), outline=(26, 35, 50, opacity), width=5)
    # White crescent moon & sun inside the flag triangles
    od.ellipse([x + 30, y + 30, x + 70, y + 70], fill=(255, 255, 255, opacity))
    od.ellipse([x + 30, y + 90, x + 70, y + 130], fill=(255, 255, 255, opacity))
    img.paste(overlay, (0,0), overlay)

def draw_soccer_ball(draw, x, y, size=80):
    cx, cy = x + size//2, y + size//2
    draw.ellipse([x, y, x+size, y+size], fill=COLORS["WHITE"], outline=COLORS["BLACK"], width=3)
    # Draw simple pentagonal ball pattern
    draw.polygon([(cx, cy - size//4), (cx - size//5, cy - size//10), (cx - size//8, cy + size//5), (cx + size//8, cy + size//5), (cx + size//5, cy - size//10)], fill=COLORS["BLACK"])
    draw.line([(cx, cy - size//4), (cx, cy - size//2)], fill=COLORS["BLACK"], width=2)
    draw.line([(cx - size//5, cy - size//10), (cx - size//2, cy - size//6)], fill=COLORS["BLACK"], width=2)
    draw.line([(cx + size//5, cy - size//10), (cx + size//2, cy - size//6)], fill=COLORS["BLACK"], width=2)

def draw_warning_icon(draw, x, y, size=60):
    draw.ellipse([x, y, x+size, y+size], fill=COLORS["YELLOW"], outline=COLORS["BLACK"], width=2)
    _cx(draw, "!", _f("Montserrat-Bold.ttf", 40), y + 5, x + size//2, COLORS["BLACK"])

def draw_x_icon(draw, x, y, size=100):
    # Cross overlay
    draw.line([(x, y), (x+size, y+size)], fill=(220, 20, 60, 180), width=15)
    draw.line([(x+size, y), (x, y+size)], fill=(220, 20, 60, 180), width=15)

def get_player_img_clean(name, size=(400, 400)):
    # Fallback placeholder cutout of a player
    img = Image.new("RGBA", size, (0,0,0,0))
    draw = ImageDraw.Draw(img)
    # Draw elegant silhouette with lighting glow
    draw.ellipse([size[0]//4, size[1]//5, size[0]*3//4, size[1]*3//5], fill=(56, 189, 248, 255)) # Head
    draw.polygon([(size[0]//10, size[1]), (size[0]*9//10, size[1]), (size[0]*3//4, size[1]*3//5), (size[0]//4, size[1]*3//5)], fill=(30, 41, 59, 255)) # Shoulders
    return img

# --- TEMPLATES ---

def draw_goal_card(scorer, minute, team_name, player_img=None, flag_img=None):
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), COLORS["NAVY_DARK"])
    draw = ImageDraw.Draw(img)
    
    # Background Navy Gradient
    for i in range(H):
        ratio = i / H
        r = int(26 * (1 - ratio) + 13 * ratio)
        g = int(35 * (1 - ratio) + 20 * ratio)
        b = int(50 * (1 - ratio) + 25 * ratio)
        draw.line([(0, i), (W, i)], fill=(r, g, b))
        
    # Nepali Flag Brushstroke (Top-right, 40% opacity)
    draw_nepal_flag_brushstroke(img, 750, 40, width=300, height=150, opacity=100)
    
    # "GOAL!" Text (Y=80, 120pt Montserrat Bold, White + Red Outline)
    _cx(draw, "GOAL!", _f("Montserrat-Bold.ttf", 120), 80, W//2, COLORS["WHITE"], outline=COLORS["RED"], outline_w=4)
    
    # Player Photo circle (400x400 circle at Y=250, white border 8px)
    p_size = 400
    p_img = player_img if player_img else get_player_img_clean(scorer, (p_size, p_size))
    mask = Image.new("L", (p_size, p_size), 0)
    ImageDraw.Draw(mask).ellipse([(0,0), (p_size, p_size)], fill=255)
    
    img.paste(p_img.resize((p_size, p_size)), (W//2 - p_size//2, 250), mask)
    draw.ellipse([(W//2 - p_size//2, 250), (W//2 + p_size//2, 250 + p_size)], outline="white", width=8)
    
    # Soccer ball icon overlay bottom-right of photo circle (80x80)
    draw_soccer_ball(draw, W//2 + p_size//4, 250 + p_size*3//4, size=80)
    
    # Player Name (Y=680, Bold, 48pt)
    _cx(draw, scorer.upper(), _f("Montserrat-Bold.ttf", 48), 680, W//2, COLORS["WHITE"])
    # Team Name (Y=740, Regular, 32pt)
    _cx(draw, team_name.upper(), _f("Roboto-Regular.ttf", 32), 740, W//2, COLORS["RED"])
    
    # Goal time badge: Red hexagon shape (200x180, Y=820)
    pts = [(440, 820), (540, 800), (640, 820), (640, 960), (540, 980), (440, 960)]
    draw.polygon(pts, fill=COLORS["RED"])
    _cx(draw, f"{minute}'", _f("BebasNeue-Regular.ttf", 56), 855, 540, COLORS["WHITE"])
    
    # Mountain silhouette bottom edge
    draw_mountain_silhouette(draw, height=120)
    
    img.save("post_image.png")
    return "post_image.png"

def draw_yellow_card(player, team, minute, player_img=None):
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), (15, 15, 20)) # Dark with glow
    draw = ImageDraw.Draw(img)
    
    # Top Section: Yellow card graphic slanted Y=60
    card_points = [(W//2 - 90, 60), (W//2 + 90, 50), (W//2 + 110, 310), (W//2 - 70, 320)]
    draw.polygon(card_points, fill=COLORS["YELLOW"], outline=COLORS["WHITE"], width=3)
    
    # "YELLOW CARD" text below card
    _cx(draw, "YELLOW CARD", _f("Montserrat-Bold.ttf", 64), 340, W//2, COLORS["YELLOW"])
    
    # Player photo centered (350x350, Y=400, yellow border 6px)
    p_size = 350
    p_img = player_img if player_img else get_player_img_clean(player, (p_size, p_size))
    mask = Image.new("L", (p_size, p_size), 0)
    ImageDraw.Draw(mask).ellipse([(0,0), (p_size, p_size)], fill=255)
    img.paste(p_img.resize((p_size, p_size)), (W//2 - p_size//2, 400), mask)
    draw.ellipse([(W//2 - p_size//2, 400), (W//2 + p_size//2, 400 + p_size)], outline=COLORS["YELLOW"], width=6)
    
    # Warning icon top-left overlay on photo
    draw_warning_icon(draw, W//2 - p_size//2 - 10, 400, size=60)
    
    # Text
    _cx(draw, player.upper(), _f("Montserrat-Bold.ttf", 44), 780, W//2, COLORS["WHITE"])
    _cx(draw, team.upper(), _f("Roboto-Regular.ttf", 30), 840, W//2, COLORS["YELLOW"])
    _cx(draw, "Unsporting Behavior", _f("Roboto-Regular.ttf", 24), 890, W//2, COLORS["GRAY"])
    
    # Match time Y=950
    _cx(draw, f"{minute}'", _f("BebasNeue-Regular.ttf", 40), 950, W//2, COLORS["WHITE"])
    
    img.save("post_image.png")
    return "post_image.png"

def draw_red_card(player, team, minute, player_img=None):
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), (15, 5, 5)) # Black to dark red
    draw = ImageDraw.Draw(img)
    
    # Red card slanted
    card_points = [(W//2 - 90, 60), (W//2 + 90, 70), (W//2 + 70, 320), (W//2 - 110, 310)]
    draw.polygon(card_points, fill=COLORS["RED"], outline=COLORS["WHITE"], width=3)
    
    _cx(draw, "SENT OFF!", _f("Montserrat-Bold.ttf", 72), 340, W//2, COLORS["RED"])
    
    p_size = 350
    p_img = player_img if player_img else get_player_img_clean(player, (p_size, p_size))
    # Slight desaturation filter simulation
    p_img = p_img.convert("L").convert("RGBA")
    
    mask = Image.new("L", (p_size, p_size), 0)
    ImageDraw.Draw(mask).ellipse([(0,0), (p_size, p_size)], fill=255)
    img.paste(p_img.resize((p_size, p_size)), (W//2 - p_size//2, 400), mask)
    draw.ellipse([(W//2 - p_size//2, 400), (W//2 + p_size//2, 400 + p_size)], outline=COLORS["RED"], width=8)
    
    # X icon overlay
    draw_x_icon(draw, W//2 - 50, 400 + p_size//2 - 50, size=100)
    
    # Text
    _cx(draw, player.upper(), _f("Montserrat-Bold.ttf", 44), 780, W//2, COLORS["WHITE"])
    _cx(draw, team.upper(), _f("Roboto-Regular.ttf", 30), 840, W//2, COLORS["RED"])
    _cx(draw, "Serious Foul Play", _f("Montserrat-Bold.ttf", 26), 890, W//2, (255, 100, 100))
    
    _cx(draw, f"{minute}'", _f("BebasNeue-Regular.ttf", 40), 950, W//2, COLORS["WHITE"])
    
    img.save("post_image.png")
    return "post_image.png"

def draw_sub_card(player_off, player_on, team, minute):
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), COLORS["NAVY_DARK"])
    draw = ImageDraw.Draw(img)
    
    _cx(draw, "SUBSTITUTION", _f("Montserrat-Bold.ttf", 56), 80, W//2, COLORS["WHITE"])
    
    # Player OUT (Left)
    p_size = 280
    p_off_img = get_player_img_clean(player_off, (p_size, p_size))
    mask = Image.new("L", (p_size, p_size), 0)
    ImageDraw.Draw(mask).ellipse([(0,0), (p_size, p_size)], fill=255)
    img.paste(p_off_img, (200 - p_size//2, 350), mask)
    draw.ellipse([(200 - p_size//2, 350), (200 + p_size//2, 350 + p_size)], outline=COLORS["RED"], width=5)
    _cx(draw, player_off.upper(), _f("Roboto-Regular.ttf", 32), 660, 200, COLORS["WHITE"])
    _cx(draw, "#10", _f("BebasNeue-Regular.ttf", 48), 320, 200, COLORS["RED"])
    
    # Divider line
    draw.line([(540, 350), (540, 750)], fill=(255, 255, 255, 128), width=2)
    _cx(draw, "OUT/IN", _f("Roboto-Regular.ttf", 24), 530, 540, COLORS["WHITE"])
    
    # Player IN (Right)
    p_on_img = get_player_img_clean(player_on, (p_size, p_size))
    img.paste(p_on_img, (880 - p_size//2, 350), mask)
    draw.ellipse([(880 - p_size//2, 350), (880 + p_size//2, 350 + p_size)], outline=COLORS["GREEN"], width=5)
    _cx(draw, player_on.upper(), _f("Roboto-Regular.ttf", 32), 660, 880, COLORS["WHITE"])
    _cx(draw, "#7", _f("BebasNeue-Regular.ttf", 48), 320, 880, COLORS["GREEN"])
    
    _cx(draw, f"{minute}'", _f("BebasNeue-Regular.ttf", 36), 900, W//2, COLORS["WHITE"])
    
    img.save("post_image.png")
    return "post_image.png"

def draw_halftime_image(home, away, sh, sa, comp):
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), COLORS["NAVY_DARK"])
    draw = ImageDraw.Draw(img)
    
    # Split Background
    for x in range(W):
        for y in range(H):
            # Diagonal split
            if x + y < 1080:
                img.putpixel((x, y), COLORS["NAVY"])
            else:
                img.putpixel((x, y), COLORS["RED"])
    draw = ImageDraw.Draw(img)
    
    _cx(draw, "HALF TIME", _f("Montserrat-Bold.ttf", 64), 80, W//2, COLORS["WHITE"])
    
    # Score Box
    draw.rounded_rectangle([(300, 300), (780, 480)], 20, fill=COLORS["WHITE"])
    _cx(draw, f"{sh}", _f("BebasNeue-Regular.ttf", 96), 330, 390, COLORS["NAVY"])
    _cx(draw, "-", _f("Roboto-Regular.ttf", 48), 350, 540, COLORS["GRAY"])
    _cx(draw, f"{sa}", _f("BebasNeue-Regular.ttf", 96), 330, 690, COLORS["RED"])
    
    _cx(draw, home.upper(), _f("Roboto-Regular.ttf", 28), 500, 200, COLORS["WHITE"])
    _cx(draw, away.upper(), _f("Roboto-Regular.ttf", 28), 500, 880, COLORS["WHITE"])
    
    # Stats Panel rounded rect (900x320)
    draw.rounded_rectangle([(90, 700), (990, 1020)], 20, fill=COLORS["WHITE"])
    _cx(draw, "POSSESSION: 58% - 42%", _f("Roboto-Regular.ttf", 24), 740, W//2, COLORS["BLACK"])
    _cx(draw, "SHOTS: 7 - 4", _f("Roboto-Regular.ttf", 24), 810, W//2, COLORS["BLACK"])
    _cx(draw, "CORNERS: 3 - 2", _f("Roboto-Regular.ttf", 24), 880, W//2, COLORS["BLACK"])
    
    img.save("post_image.png")
    return "post_image.png"

def draw_fulltime_image(home, away, sh, sa, comp):
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), COLORS["NAVY_DARK"])
    draw = ImageDraw.Draw(img)
    
    _cx(draw, "FULL TIME", _f("Montserrat-Bold.ttf", 72), 70, W//2, COLORS["WHITE"])
    
    # Large score display
    _cx(draw, f"{sh}", _f("BebasNeue-Regular.ttf", 120), 280, 350, COLORS["WHITE"])
    _cx(draw, "-", _f("Roboto-Regular.ttf", 60), 310, 540, COLORS["WHITE"])
    _cx(draw, f"{sa}", _f("BebasNeue-Regular.ttf", 120), 280, 730, COLORS["WHITE"])
    
    _cx(draw, home.upper(), _f("Montserrat-Bold.ttf", 32), 480, 200, COLORS["WHITE"])
    _cx(draw, away.upper(), _f("Montserrat-Bold.ttf", 32), 480, 880, COLORS["WHITE"])
    
    # Match Statistics Panel (950x400)
    draw.rounded_rectangle([(65, 600), (1015, 1000)], 20, fill=(255, 255, 255, 200))
    _cx(draw, "MATCH STATS", _f("Montserrat-Bold.ttf", 36), 620, W//2, COLORS["BLACK"])
    
    img.save("post_image.png")
    return "post_image.png"

# Match compatibility with existing routes
def draw_summary_image(home, away, events, comp):
    return draw_fulltime_image(home, away, 0, 0, comp)

def draw_live_image(home, away, comp):
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), COLORS["NAVY_DARK"])
    draw = ImageDraw.Draw(img)
    _cx(draw, "MATCH LIVE", _f("Montserrat-Bold.ttf", 64), 100, W//2, COLORS["WHITE"])
    _cx(draw, f"{home} vs {away}", _f("Montserrat-Bold.ttf", 40), 300, W//2, COLORS["WHITE"])
    img.save("post_image.png")
    return "post_image.png"
