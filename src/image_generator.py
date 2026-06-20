from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import os, requests, io, tempfile, time, numpy as np
from math import sin, pi, cos

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRAND_LOGO_PATH = os.path.join(_ROOT, "src", "static", "brand-logo.jpg")

def _out_path(name=None):
    ts = str(int(time.time() * 1000))
    return os.path.join(_ROOT, name or f"post_{ts}.png")

# --- BRAND CONSTANTS ---
COLORS = {
    "NAVY": (26, 35, 50),
    "RED": (220, 20, 60),
    "WHITE": (255, 255, 255),
    "GOLD": (251, 191, 36),
    "BLACK": (10, 10, 15),
    "GRAY": (128, 128, 128),
    "WHITE_30": (255, 255, 255, 30),
    "WHITE_50": (255, 255, 255, 50),
    "RED_GLOW": (220, 20, 60, 120),
    "NAVY_GLOW": (26, 35, 50, 180),
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
                    with open(path, "wb") as f: f.write(r.content)
            except: pass

_init_fonts()

def _f(name, size):
    path = os.path.join("fonts", name)
    if os.path.exists(path):
        try: return ImageFont.truetype(path, size)
        except: pass
    return ImageFont.load_default()

# --- ADVANCED ASSET UTILS ---

def _fetch_image(url):
    if not url: return None
    try:
        r = requests.get(url, timeout=10)
        return Image.open(io.BytesIO(r.content)).convert("RGBA")
    except: return None

def _get_waving_flag(country_code):
    """Fetches flag and applies a sine-wave warp for a 'moving' feel."""
    if not country_code: return None
    url = f"https://flagcdn.com/w640/{country_code.lower()}.png"
    img = _fetch_image(url)
    if not img: return None
    
    # Warp for waving effect
    img = img.resize((600, 300), Image.Resampling.LANCZOS)
    width, height = img.size
    pixels = img.load()
    new_img = Image.new("RGBA", (width, height), (0,0,0,0))
    new_pixels = new_img.load()
    
    # Wave parameters
    amplitude = 8
    frequency = 0.05
    
    for y in range(height):
        offset = int(amplitude * sin(frequency * y))
        for x in range(width):
            if 0 <= x + offset < width:
                new_pixels[x, y] = pixels[x + offset, y]
                
    return new_img

def _get_premium_silhouette(name, size=450):
    """Creates a brand-aligned gradient silhouette if no photo is provided."""
    img = Image.new("RGBA", (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    
    # Gradient Circle
    for r in range(size // 2, 0, -1):
        color = (
            int(30 + 40 * (1 - r/(size//2))), 
            int(40 + 50 * (1 - r/(size//2))), 
            int(60 + 70 * (1 - r/(size//2)))
        )
        draw.ellipse([size//2-r, size//2-r, size//2+r, size//2+r], fill=color + (255,))
    
    # Initials
    initials = "".join(w[0].upper() for w in name.split()[:2]) if name else "?"
    draw.text((size//2, size//2), initials, fill=COLORS["WHITE"], font=_f("Montserrat-Bold.ttf", size//4), anchor="mm")
    
    return img

def _mask_circle(img, size=450):
    if img is None: return None
    min_dim = min(img.size)
    left = (img.size[0] - min_dim) / 2
    top = (img.size[1] - min_dim) / 2
    img = img.crop((left, top, left + min_dim, top + min_dim))
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, img.size[0], img.size[1]), fill=255)
    
    output = Image.new("RGBA", img.size, (0,0,0,0))
    output.paste(img, (0,0), mask)
    return output

def _add_action_elements(img):
    """Adds speed lines and particles for high energy."""
    draw = ImageDraw.Draw(img)
    # Particles
    for _ in range(60):
        x, y = random.randint(0, W), random.randint(0, H)
        size = random.randint(1, 3)
        color = random.choice([COLORS["WHITE"], COLORS["RED"]]) + (random.randint(100, 200),)
        draw.ellipse([x, y, x+size, y+size], fill=color)
    
    # Speed Lines (diagonal)
    overlay = Image.new("RGBA", (W, H), (0,0,0,0))
    od = ImageDraw.Draw(overlay)
    for i in range(0, W, 100):
        od.line([i, 0, i-200, H], fill=COLORS["WHITE_30"], width=2)
    img.paste(overlay, (0,0), overlay)

def _draw_text_shadow(draw, text, font, y, cx, fill="white", anchor="mt"):
    draw.text((cx+5, y+5), text, fill=(0,0,0,180), font=font, anchor=anchor)
    draw.text((cx, y), text, fill=fill, font=font, anchor=anchor)

def _draw_brand_logo(img, x, y, size=200):
    if not os.path.exists(BRAND_LOGO_PATH): return
    logo = Image.open(BRAND_LOGO_PATH).convert("RGBA")
    logo = logo.resize((size, size), Image.Resampling.LANCZOS)
    img.paste(logo, (x, y), logo)

def _draw_dynamic_bg(img, color_main=COLORS["NAVY"]):
    draw = ImageDraw.Draw(img)
    # Radial Depth
    overlay = Image.new("RGBA", (W, H), (0,0,0,0))
    od = ImageDraw.Draw(overlay)
    od.ellipse([W//4, -W//4, 3*W//4, H], fill=tuple(int(c*0.7) for c in color_main) + (150,))
    img.paste(overlay, (0,0), overlay)
    
    # Brand Accents
    draw.polygon([ (0, 0), (W//3, 0), (0, H//3) ], fill=COLORS["RED"])
    draw.polygon([ (W, H), (2*W//3, H), (W, 2*H//3) ], fill=COLORS["RED"])
    _add_action_elements(img)

# === FINALTEMPLATES ===

def draw_goal_card(scorer, minute, team_name, country_code="np", player_img_url=None, output_path=None):
    output_path = output_path or _out_path()
    img = Image.new("RGBA", (W, H), COLORS["BLACK"])
    _draw_dynamic_bg(img, COLORS["NAVY"])
    draw = ImageDraw.Draw(img)

    # 1. Waving Flag
    flag = _get_waving_flag(country_code)
    if flag:
        img.paste(flag, (W//2 - flag.size[0]//2, 120), flag)

    # 2. Hero Player (or Silhouette)
    player_raw = _fetch_image(player_img_url) if player_img_url else _get_premium_silhouette(scorer)
    player = _mask_circle(player_raw)
    if player:
        # Heavy Glow
        glow = Image.new("RGBA", (550, 550), (0,0,0,0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse([0, 0, 550, 550], fill=COLORS["RED_GLOW"])
        glow = glow.filter(ImageFilter.GaussianBlur(radius=40))
        img.paste(glow, (W//2 - 275, 325), glow)
        img.paste(player, (W//2 - 225, 375), player)

    # 3. Typography
    _draw_text_shadow(draw, "GOAL!", _f("BebasNeue-Regular.ttf", 200), 220, W//2, COLORS["WHITE"])
    _draw_text_shadow(draw, scorer.upper(), _f("Montserrat-Bold.ttf", 70), 750, W//2, COLORS["WHITE"])
    _draw_text_shadow(draw, f"MINUTE {minute}'", _f("Roboto-Regular.ttf", 34), 830, W//2, COLORS["RED"])
    _draw_text_shadow(draw, team_name.upper(), _f("Montserrat-Bold.ttf", 44), 890, W//2, COLORS["WHITE"])

    _draw_brand_logo(img, W - 250, 50, size=150)
    img.convert("RGB").save(output_path)
    return output_path

def draw_yellow_card(player, team, minute, country_code="np", player_img_url=None, output_path=None):
    output_path = output_path or _out_path()
    img = Image.new("RGBA", (W, H), COLORS["BLACK"])
    _draw_dynamic_bg(img, COLORS["NAVY"])
    draw = ImageDraw.Draw(img)

    flag = _get_waving_flag(country_code)
    if flag: img.paste(flag, (W//2 - flag.size[0]//2, 100), flag)

    player_raw = _fetch_image(player_img_url) if player_img_url else _get_premium_silhouette(player)
    player = _mask_circle(player_raw, size=400)
    if player: img.paste(player, (W//2 - 200, 300), player)

    _draw_text_shadow(draw, "YELLOW CARD", _f("BebasNeue-Regular.ttf", 140), 650, W//2, COLORS["GOLD"])
    _draw_text_shadow(draw, player.upper(), _f("Montserrat-Bold.ttf", 60), 780, W//2, COLORS["WHITE"])
    _draw_text_shadow(draw, f"Minute {minute}'", _f("Roboto-Regular.ttf", 34), 850, W//2, COLORS["GOLD"])

    _draw_brand_logo(img, W - 250, 50, size=150)
    img.convert("RGB").save(output_path)
    return output_path

def draw_red_card(player, team, minute, country_code="np", player_img_url=None, output_path=None):
    output_path = output_path or _out_path()
    img = Image.new("RGBA", (W, H), COLORS["BLACK"])
    _draw_dynamic_bg(img, COLORS["RED"])
    draw = ImageDraw.Draw(img)

    flag = _get_waving_flag(country_code)
    if flag: img.paste(flag, (W//2 - flag.size[0]//2, 100), flag)

    player_raw = _fetch_image(player_img_url) if player_img_url else _get_premium_silhouette(player)
    player = _mask_circle(player_raw, size=400)
    if player:
        overlay = Image.new("RGBA", player.size, COLORS["RED"] + (120,))
        player = Image.alpha_composite(player, overlay)
        img.paste(player, (W//2 - 200, 300), player)

    _draw_text_shadow(draw, "SENT OFF", _f("BebasNeue-Regular.ttf", 140), 650, W//2, COLORS["WHITE"])
    _draw_text_shadow(draw, player.upper(), _f("Montserrat-Bold.ttf", 60), 780, W//2, COLORS["WHITE"])
    _draw_text_shadow(draw, f"Minute {minute}'", _f("Roboto-Regular.ttf", 34), 850, W//2, COLORS["WHITE"])

    _draw_brand_logo(img, W - 250, 50, size=150)
    img.convert("RGB").save(output_path)
    return output_path

def draw_sub_card(player_off, player_on, team, minute, country_code="np", player_img_url_off=None, player_img_url_on=None, output_path=None):
    output_path = output_path or _out_path()
    img = Image.new("RGBA", (W, H), COLORS["BLACK"])
    _draw_dynamic_bg(img, COLORS["NAVY"])
    draw = ImageDraw.Draw(img)

    flag = _get_waving_flag(country_code)
    if flag: img.paste(flag, (W//2 - flag.size[0]//2, 80), flag)

    p_off_raw = _fetch_image(player_img_url_off) if player_img_url_off else _get_premium_silhouette(player_off)
    p_on_raw = _fetch_image(player_img_url_on) if player_img_url_on else _get_premium_silhouette(player_on)
    p_off = _mask_circle(p_off_raw, size=300)
    p_on = _mask_circle(p_on_raw, size=300)
    
    if p_off: img.paste(p_off, (W//2 - 350, 350), p_off)
    if p_on: img.paste(p_on, (W//2 + 50, 350), p_on)

    _draw_text_shadow(draw, "SUBSTITUTION", _f("BebasNeue-Regular.ttf", 100), 250, W//2, COLORS["WHITE"])
    _draw_text_shadow(draw, "OUT", _f("Montserrat-Bold.ttf", 34), 670, W//2 - 200, COLORS["RED"], anchor="mm")
    _draw_text_shadow(draw, "IN", _f("Montserrat-Bold.ttf", 34), 670, W//2 + 200, COLORS["GOLD"], anchor="mm")
    _draw_text_shadow(draw, player_off.upper(), _f("Montserrat-Bold.ttf", 34), 720, W//2 - 200, COLORS["WHITE"], anchor="mm")
    _draw_text_shadow(draw, player_on.upper(), _f("Montserrat-Bold.ttf", 34), 720, W//2 + 200, COLORS["WHITE"], anchor="mm")

    _draw_brand_logo(img, W - 250, 50, size=150)
    img.convert("RGB").save(output_path)
    return output_path

def draw_halftime_image(home, away, sh, sa, comp, home_code="np", away_code="in", output_path=None):
    output_path = output_path or _out_path()
    img = Image.new("RGBA", (W, H), COLORS["BLACK"])
    _draw_dynamic_bg(img, COLORS["NAVY"])
    draw = ImageDraw.Draw(img)

    f_home = _get_waving_flag(home_code)
    f_away = _get_waving_flag(away_code)
    if f_home: img.paste(f_home, (100, 250), f_home)
    if f_away: img.paste(f_away, (W - 700, 250), f_away)

    _draw_text_shadow(draw, "HALF TIME", _f("BebasNeue-Regular.ttf", 140), 180, W//2, COLORS["WHITE"])
    _draw_text_shadow(draw, f"{sh} - {sa}", _f("BebasNeue-Regular.ttf", 240), 380, W//2, COLORS["WHITE"])
    _draw_text_shadow(draw, home.upper(), _f("Montserrat-Bold.ttf", 44), 330, 225, COLORS["WHITE"], anchor="mm")
    _draw_text_shadow(draw, away.upper(), _f("Montserrat-Bold.ttf", 44), 330, W - 225, COLORS["WHITE"], anchor="mm")

    _draw_brand_logo(img, W - 250, 50, size=150)
    img.convert("RGB").save(output_path)
    return output_path

def draw_fulltime_image(home, away, sh, sa, comp, home_code="np", away_code="in", output_path=None):
    output_path = output_path or _out_path()
    img = Image.new("RGBA", (W, H), COLORS["BLACK"])
    _draw_dynamic_bg(img, COLORS["NAVY"])
    draw = ImageDraw.Draw(img)

    f_home = _get_waving_flag(home_code)
    f_away = _get_waving_flag(away_code)
    if f_home: img.paste(f_home, (100, 250), f_home)
    if f_away: img.paste(f_away, (W - 700, 250), f_away)

    _draw_text_shadow(draw, "FULL TIME", _f("BebasNeue-Regular.ttf", 140), 180, W//2, COLORS["GOLD"])
    _draw_text_shadow(draw, f"{sh} - {sa}", _f("BebasNeue-Regular.ttf", 280), 380, W//2, COLORS["WHITE"])
    _draw_text_shadow(draw, home.upper(), _f("Montserrat-Bold.ttf", 44), 330, 225, COLORS["WHITE"], anchor="mm")
    _draw_text_shadow(draw, away.upper(), _f("Montserrat-Bold.ttf", 44), 330, W - 225, COLORS["WHITE"], anchor="mm")

    _draw_brand_logo(img, W - 250, 50, size=150)
    img.convert("RGB").save(output_path)
    return output_path

def draw_summary_image(home, away, events, comp, output_path=None):
    return draw_fulltime_image(home, away, "0", "0", comp, output_path=output_path)

def draw_live_image(home, away, comp, home_code="np", away_code="in", output_path=None):
    output_path = output_path or _out_path()
    img = Image.new("RGBA", (W, H), COLORS["BLACK"])
    _draw_dynamic_bg(img, COLORS["NAVY"])
    draw = ImageDraw.Draw(img)

    f_home = _get_waving_flag(home_code)
    f_away = _get_waving_flag(away_code)
    if f_home: img.paste(f_home, (W//2 - 300, 300), f_home)
    if f_away: img.paste(f_away, (W//2 + 100, 300), f_away)

    _draw_text_shadow(draw, "MATCH LIVE", _f("BebasNeue-Regular.ttf", 120), 200, W//2, COLORS["RED"])
    _draw_text_shadow(draw, f"{home} VS {away}", _f("Montserrat-Bold.ttf", 64), 480, W//2, COLORS["WHITE"])

    _draw_brand_logo(img, W - 250, 50, size=150)
    img.convert("RGB").save(output_path)
    return output_path
