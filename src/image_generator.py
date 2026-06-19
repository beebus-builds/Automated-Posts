from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import os, requests, io, tempfile, time
from math import sin, pi, cos
import random

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRAND_LOGO_PATH = os.path.join(_ROOT, "src", "static", "brand-logo.jpg")

def _out_path(name=None):
    ts = str(int(time.time() * 1000))
    return os.path.join(_ROOT, name or f"post_{ts}.png")

# --- BRAND CONSTANTS (Based on Logo) ---
COLORS = {
    "NAVY": (26, 35, 50),       # Deep Brand Navy
    "RED": (220, 20, 60),       # Vibrant Brand Red
    "WHITE": (255, 255, 255),
    "GOLD": (251, 191, 36),
    "BLACK": (10, 10, 15),
    "GRAY": (128, 128, 128),
    "WHITE_30": (255, 255, 255, 30),
    "WHITE_50": (255, 255, 255, 50),
    "RED_GLOW": (220, 20, 60, 100),
    "NAVY_GLOW": (26, 35, 50, 150),
}

W, H = 1080, 1080

# --- FONTS ---
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
        try: return ImageFont.truetype(path, size)
        except: pass
    return ImageFont.load_default()

# --- ASSET FETCHERS ---

def _fetch_image(url):
    """Fetch image from URL and return as PIL Image."""
    try:
        r = requests.get(url, timeout=10)
        return Image.open(io.BytesIO(r.content)).convert("RGBA")
    except Exception as e:
        print(f"Error fetching image {url}: {e}")
        return None

def _get_flag(country_code):
    """Fetch national flag from flagcdn.com."""
    if not country_code: return None
    # Example: 'np' -> https://flagcdn.com/w320/np.png
    url = f"https://flagcdn.com/w320/{country_code.lower()}.png"
    return _fetch_image(url)

def _mask_circle(img, size=None):
    """Mask an image into a perfect circle."""
    if img is None: return None
    
    # Square crop
    min_dim = min(img.size)
    left = (img.size[0] - min_dim) / 2
    top = (img.size[1] - min_dim) / 2
    img = img.crop((left, top, left + min_dim, top + min_dim))
    
    if size:
        img = img.resize((size, size), Image.Resampling.LANCZOS)
    
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, img.size[0], img.size[1]), fill=255)
    
    output = Image.new("RGBA", img.size, (0,0,0,0))
    output.paste(img, (0,0), mask)
    return output

# --- DRAWING UTILITIES ---

def _draw_text(draw, text, font, y, cx, fill="white", anchor="mt"):
    draw.text((cx, y), text, fill=fill, font=font, anchor=anchor)

def _draw_text_shadow(draw, text, font, y, cx, fill="white", shadow_color=(0,0,0,150), anchor="mt"):
    draw.text((cx+4, y+4), text, fill=shadow_color, font=font, anchor=anchor)
    draw.text((cx, y), text, fill=fill, font=font, anchor=anchor)

def _draw_brand_logo(img, x, y, size=200):
    """Paste brand logo with a subtle glow."""
    if not os.path.exists(BRAND_LOGO_PATH): return
    logo = Image.open(BRAND_LOGO_PATH).convert("RGBA")
    logo = logo.resize((size, size), Image.Resampling.LANCZOS)
    
    # Soft glow behind logo
    glow = Image.new("RGBA", (size+40, size+40), (0,0,0,0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([0, 0, size+40, size+40], fill=COLORS["WHITE_30"])
    glow = glow.filter(ImageFilter.GaussianBlur(radius=15))
    
    img.paste(glow, (x - 20, y - 20), glow)
    img.paste(logo, (x, y), logo)

def _draw_dynamic_bg(img, color_main=COLORS["NAVY"]):
    """Create a brand-aligned background with gradients and brush-like accents."""
    draw = ImageDraw.Draw(img)
    # Background gradient
    overlay = Image.new("RGBA", (W, H), (0,0,0,0))
    od = ImageDraw.Draw(overlay)
    od.ellipse([W//4, -W//4, 3*W//4, H], fill=tuple(int(c*0.8) for c in color_main) + (100,))
    img.paste(overlay, (0,0), overlay)
    
    # Brand accent diagonals (Dynamic feel)
    draw = ImageDraw.Draw(img)
    draw.polygon([ (0, 0), (W//3, 0), (0, H//3) ], fill=COLORS["RED"])
    draw.polygon([ (W, H), (2*W//3, H), (W, 2*H//3) ], fill=COLORS["RED"])

# === MAIN TEMPLATES ===

def draw_goal_card(scorer, minute, team_name, country_code="np", player_img_url=None, output_path=None):
    output_path = output_path or _out_path()
    img = Image.new("RGBA", (W, H), COLORS["BLACK"])
    _draw_dynamic_bg(img, COLORS["NAVY"])
    draw = ImageDraw.Draw(img)

    # 1. National Flag (Large and Dynamic)
    flag = _get_flag(country_code)
    if flag:
        flag = flag.resize((600, 300), Image.Resampling.LANCZOS)
        # Slight rotation for energy
        rotated_flag = flag.rotate(5, expand=True, resample=Image.BICUBIC)
        img.paste(rotated_flag, (W//2 - rotated_flag.size[0]//2, 150), rotated_flag)

    # 2. Player Image (The Hero)
    player = _fetch_image(player_img_url) if player_img_url else None
    player_circle = _mask_circle(player, size=450)
    if player_circle:
        # Glow behind player
        glow = Image.new("RGBA", (500, 500), (0,0,0,0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse([0, 0, 500, 500], fill=COLORS["RED_GLOW"])
        glow = glow.filter(ImageFilter.GaussianBlur(radius=30))
        img.paste(glow, (W//2 - 250, 350), glow)
        img.paste(player_circle, (W//2 - 225, 375), player_circle)

    # 3. Score/Goal Text
    _draw_text_shadow(draw, "GOAL!", _f("BebasNeue-Regular.ttf", 180), 200, W//2, COLORS["WHITE"])
    
    # 4. Player & Minute
    _draw_text_shadow(draw, scorer.upper(), _f("Montserrat-Bold.ttf", 60), 750, W//2, COLORS["WHITE"])
    _draw_text(draw, f"MINUTE {minute}'", _f("Roboto-Regular.ttf", 30), 820, W//2, COLORS["RED"])
    _draw_text(draw, team_name.upper(), _f("Montserrat-Bold.ttf", 40), 870, W//2, COLORS["WHITE"])

    # 5. Brand Logo
    _draw_brand_logo(img, W - 250, 50, size=150)

    img = img.convert("RGB")
    img.save(output_path)
    return output_path

def draw_yellow_card(player, team, minute, country_code="np", player_img_url=None, output_path=None):
    output_path = output_path or _out_path()
    img = Image.new("RGBA", (W, H), COLORS["BLACK"])
    _draw_dynamic_bg(img, COLORS["NAVY"])
    draw = ImageDraw.Draw(img)

    # Brand Accents
    draw.rectangle([0, 0, W, 20], fill=COLORS["GOLD"])

    # Flag
    flag = _get_flag(country_code)
    if flag:
        flag = flag.resize((300, 150), Image.Resampling.LANCZOS)
        img.paste(flag, (W//2 - 150, 100), flag)

    # Player
    player = _fetch_image(player_img_url) if player_img_url else None
    player_circle = _mask_circle(player, size=400)
    if player_circle:
        img.paste(player_circle, (W//2 - 200, 300), player_circle)

    # Text
    _draw_text_shadow(draw, "YELLOW CARD", _f("BebasNeue-Regular.ttf", 120), 650, W//2, COLORS["GOLD"])
    _draw_text_shadow(draw, player.upper(), _f("Montserrat-Bold.ttf", 50), 760, W//2, COLORS["WHITE"])
    _draw_text(draw, f"Minute {minute}'", _f("Roboto-Regular.ttf", 30), 820, W//2, COLORS["GOLD"])

    _draw_brand_logo(img, W - 250, 50, size=150)

    img = img.convert("RGB")
    img.save(output_path)
    return output_path

def draw_red_card(player, team, minute, country_code="np", player_img_url=None, output_path=None):
    output_path = output_path or _out_path()
    img = Image.new("RGBA", (W, H), COLORS["BLACK"])
    _draw_dynamic_bg(img, COLORS["RED"])
    draw = ImageDraw.Draw(img)

    # Flag
    flag = _get_flag(country_code)
    if flag:
        flag = flag.resize((300, 150), Image.Resampling.LANCZOS)
        img.paste(flag, (W//2 - 150, 100), flag)

    # Player (with red overlay)
    player = _fetch_image(player_img_url) if player_img_url else None
    player_circle = _mask_circle(player, size=400)
    if player_circle:
        # Red tint overlay
        overlay = Image.new("RGBA", player_circle.size, COLORS["RED"] + (100,))
        player_circle = Image.alpha_composite(player_circle, overlay)
        img.paste(player_circle, (W//2 - 200, 300), player_circle)

    # Text
    _draw_text_shadow(draw, "SENT OFF", _f("BebasNeue-Regular.ttf", 120), 650, W//2, COLORS["WHITE"])
    _draw_text_shadow(draw, player.upper(), _f("Montserrat-Bold.ttf", 50), 760, W//2, COLORS["WHITE"])
    _draw_text(draw, f"Minute {minute}'", _f("Roboto-Regular.ttf", 30), 820, W//2, COLORS["WHITE"])

    _draw_brand_logo(img, W - 250, 50, size=150)

    img = img.convert("RGB")
    img.save(output_path)
    return output_path

def draw_sub_card(player_off, player_on, team, minute, country_code="np", player_img_url_off=None, player_img_url_on=None, output_path=None):
    output_path = output_path or _out_path()
    img = Image.new("RGBA", (W, H), COLORS["BLACK"])
    _draw_dynamic_bg(img, COLORS["NAVY"])
    draw = ImageDraw.Draw(img)

    # Flag
    flag = _get_flag(country_code)
    if flag:
        flag = flag.resize((200, 100), Image.Resampling.LANCZOS)
        img.paste(flag, (W//2 - 100, 50), flag)

    # Players
    p_off = _mask_circle(_fetch_image(player_img_url_off), size=300) if player_img_url_off else None
    p_on = _mask_circle(_fetch_image(player_img_url_on), size=300) if player_img_url_on else None
    
    if p_off: img.paste(p_off, (W//2 - 350, 300), p_off)
    if p_on: img.paste(p_on, (W//2 + 50, 300), p_on)

    # Arrows & Text
    _draw_text_shadow(draw, "SUBSTITUTION", _f("BebasNeue-Regular.ttf", 80), 200, W//2, COLORS["WHITE"])
    _draw_text(draw, "OUT", _f("Montserrat-Bold.ttf", 30), 620, W//2 - 200, COLORS["RED"], anchor="mm")
    _draw_text(draw, "IN", _f("Montserrat-Bold.ttf", 30), 620, W//2 + 200, COLORS["GOLD"], anchor="mm")
    _draw_text(draw, player_off.upper(), _f("Montserrat-Bold.ttf", 30), 670, W//2 - 200, COLORS["WHITE"], anchor="mm")
    _draw_text(draw, player_on.upper(), _f("Montserrat-Bold.ttf", 30), 670, W//2 + 200, COLORS["WHITE"], anchor="mm")

    _draw_brand_logo(img, W - 250, 50, size=150)

    img = img.convert("RGB")
    img.save(output_path)
    return output_path

def draw_halftime_image(home, away, sh, sa, comp, home_code="np", away_code="in", output_path=None):
    output_path = output_path or _out_path()
    img = Image.new("RGBA", (W, H), COLORS["BLACK"])
    _draw_dynamic_bg(img, COLORS["NAVY"])
    draw = ImageDraw.Draw(img)

    # Flags
    f_home = _get_flag(home_code)
    f_away = _get_flag(away_code)
    if f_home:
        f_home = f_home.resize((250, 125), Image.Resampling.LANCZOS)
        img.paste(f_home, (100, 200), f_home)
    if f_away:
        f_away = f_away.resize((250, 125), Image.Resampling.LANCZOS)
        img.paste(f_away, (W - 350, 200), f_away)

    # Score
    _draw_text_shadow(draw, "HALF TIME", _f("BebasNeue-Regular.ttf", 120), 150, W//2, COLORS["WHITE"])
    _draw_text_shadow(draw, f"{sh} - {sa}", _f("BebasNeue-Regular.ttf", 200), 350, W//2, COLORS["WHITE"])
    
    _draw_text(draw, home.upper(), _f("Montserrat-Bold.ttf", 40), 320, 225, COLORS["WHITE"], anchor="mm")
    _draw_text(draw, away.upper(), _f("Montserrat-Bold.ttf", 40), 320, W - 225, COLORS["WHITE"], anchor="mm")

    _draw_brand_logo(img, W - 250, 50, size=150)

    img = img.convert("RGB")
    img.save(output_path)
    return output_path

def draw_fulltime_image(home, away, sh, sa, comp, home_code="np", away_code="in", output_path=None):
    output_path = output_path or _out_path()
    img = Image.new("RGBA", (W, H), COLORS["BLACK"])
    _draw_dynamic_bg(img, COLORS["NAVY"])
    draw = ImageDraw.Draw(img)

    # Flags
    f_home = _get_flag(home_code)
    f_away = _get_flag(away_code)
    if f_home:
        f_home = f_home.resize((250, 125), Image.Resampling.LANCZOS)
        img.paste(f_home, (100, 200), f_home)
    if f_away:
        f_away = f_away.resize((250, 125), Image.Resampling.LANCZOS)
        img.paste(f_away, (W - 350, 200), f_away)

    # Score
    _draw_text_shadow(draw, "FULL TIME", _f("BebasNeue-Regular.ttf", 120), 150, W//2, COLORS["GOLD"])
    _draw_text_shadow(draw, f"{sh} - {sa}", _f("BebasNeue-Regular.ttf", 240), 350, W//2, COLORS["WHITE"])
    
    _draw_text(draw, home.upper(), _f("Montserrat-Bold.ttf", 40), 320, 225, COLORS["WHITE"], anchor="mm")
    _draw_text(draw, away.upper(), _f("Montserrat-Bold.ttf", 40), 320, W - 225, COLORS["WHITE"], anchor="mm")

    _draw_brand_logo(img, W - 250, 50, size=150)

    img = img.convert("RGB")
    img.save(output_path)
    return output_path

def draw_summary_image(home, away, events, comp, output_path=None):
    """Wrapper for full-time image to maintain compatibility with app.py"""
    return draw_fulltime_image(home, away, "0", "0", comp, output_path=output_path)

def draw_live_image(home, away, comp, home_code="np", away_code="in", output_path=None):
    output_path = output_path or _out_path()
    img = Image.new("RGBA", (W, H), COLORS["BLACK"])
    _draw_dynamic_bg(img, COLORS["NAVY"])
    draw = ImageDraw.Draw(img)

    # Flags
    f_home = _get_flag(home_code)
    f_away = _get_flag(away_code)
    if f_home:
        f_home = f_home.resize((200, 100), Image.Resampling.LANCZOS)
        img.paste(f_home, (W//2 - 250, 300), f_home)
    if f_away:
        f_away = f_away.resize((200, 100), Image.Resampling.LANCZOS)
        img.paste(f_away, (W//2 + 50, 300), f_away)

    _draw_text_shadow(draw, "MATCH LIVE", _f("BebasNeue-Regular.ttf", 100), 200, W//2, COLORS["RED"])
    _draw_text_shadow(draw, f"{home} VS {away}", _f("Montserrat-Bold.ttf", 60), 450, W//2, COLORS["WHITE"])

    _draw_brand_logo(img, W - 250, 50, size=150)

    img = img.convert("RGB")
    img.save(output_path)
    return output_path
