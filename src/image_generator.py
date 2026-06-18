from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, requests, io, tempfile, time
from math import sin, pi, cos
import random

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _out_path(name=None):
    ts = str(int(time.time() * 1000))
    return os.path.join(_ROOT, name or f"post_{ts}.png")

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
    "GOLD": (251, 191, 36),
    "WHITE_30": (255, 255, 255, 30),
    "WHITE_50": (255, 255, 255, 50),
    "WHITE_100": (255, 255, 255, 100),
    "WHITE_180": (255, 255, 255, 180),
    "BLACK_40": (0, 0, 0, 40),
    "BLACK_80": (0, 0, 0, 80),
    "BLACK_150": (0, 0, 0, 150),
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
        try:
            return ImageFont.truetype(path, size)
        except:
            pass
    return ImageFont.load_default()

# --- DRAWING UTILITIES ---

def _draw_text(draw, text, font, y, cx, fill="white", anchor="mt", letter_spacing=None):
    """Draw text centered at (cx, y) with optional letter spacing."""
    if letter_spacing:
        spacing = letter_spacing
        total_w = sum(draw.textbbox((0, 0), ch, font=font)[2] - draw.textbbox((0, 0), ch, font=font)[0] for ch in text) + spacing * (len(text) - 1)
        x_start = cx - total_w // 2
        for ch in text:
            if ch == " ":
                x_start += spacing + (draw.textbbox((0, 0), " ", font=font)[2] - draw.textbbox((0, 0), " ", font=font)[0])
                continue
            b = draw.textbbox((0, 0), ch, font=font)
            ch_w = b[2] - b[0]
            draw.text((x_start, y), ch, fill=fill, font=font, anchor="mt")
            x_start += ch_w + spacing
    else:
        draw.text((cx, y), text, fill=fill, font=font, anchor=anchor)

def _draw_text_with_shadow(draw, text, font, y, cx, fill="white", shadow_color=(0,0,0,150), shadow_offset=(4,4), anchor="mt", letter_spacing=None):
    """Draw text with a drop shadow."""
    if letter_spacing:
        _draw_text(draw, text, font, y + shadow_offset[1], cx + shadow_offset[0], shadow_color, anchor, letter_spacing)
        _draw_text(draw, text, font, y, cx, fill, anchor, letter_spacing)
    else:
        draw.text((cx + shadow_offset[0], y + shadow_offset[1]), text, fill=shadow_color, font=font, anchor=anchor)
        draw.text((cx, y), text, fill=fill, font=font, anchor=anchor)

def _draw_glow_text(draw, text, font, y, cx, fill="white", glow_color=(220, 20, 60, 100), glow_radius=12, anchor="mt"):
    """Draw text with a glow effect behind it."""
    glow = Image.new("RGBA", (W, H), (0,0,0,0))
    gd = ImageDraw.Draw(glow)
    gd.text((cx, y), text, fill=glow_color, font=font, anchor=anchor)
    glow = glow.filter(ImageFilter.GaussianBlur(radius=glow_radius))
    draw._image.paste(glow, (0,0), glow)
    draw.text((cx, y), text, fill=fill, font=font, anchor=anchor)

def _rounded_panel(draw, x1, y1, x2, y2, fill=(255,255,255,40), border=(255,255,255,50), radius=20):
    """Draw a glass-morphism rounded rectangle panel."""
    overlay = Image.new("RGBA", (W, H), (0,0,0,0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill, outline=border, width=1)
    draw._image.paste(overlay, (0,0), overlay)

def _radial_gradient(size, center_color, edge_color, center=None):
    """Create a radial gradient image."""
    Ws, Hs = size
    cx, cy = center or (Ws // 2, Hs // 2)
    img = Image.new("RGBA", size, edge_color)
    max_r = max(Ws, Hs)
    for r in range(max_r, 0, -1):
        alpha = int(255 * (1 - r / max_r))
        if alpha <= 0:
            continue
        clr = tuple(min(255, c * 2) for c in center_color) if alpha > 200 else center_color
        clr_alpha = clr + (alpha // 4,)
        overlay = Image.new("RGBA", size, (0,0,0,0))
        od = ImageDraw.Draw(overlay)
        od.ellipse([cx - r, cy - r, cx + r, cy + r], fill=clr_alpha)
        img = Image.alpha_composite(img, overlay)
    return img

def _noise_texture(size, opacity=15):
    """Create a subtle grain noise texture."""
    noise = Image.effect_noise(size, 64).convert("RGBA")
    pixels = noise.load()
    for y in range(size[1]):
        for x in range(size[0]):
            v = pixels[x, y][0]
            pixels[x, y] = (v, v, v, opacity)
    return noise

def _team_color_bar(draw, y, team_color=None):
    """Draw a thin horizontal team color bar."""
    color = team_color or COLORS["RED"]
    draw.rectangle([0, y, W, y + 4], fill=color)
    draw.rectangle([0, y + 6, W, y + 8], fill=COLORS["WHITE_30"])

def _player_circle(img, player_name, cx, cy, size, border_color=COLORS["WHITE"], border_width=6, glow=True):
    """Draw a circular player photo placeholder with glow and border."""
    p_size = size
    # Glow layer
    if glow:
        glow_layer = Image.new("RGBA", (p_size + 40, p_size + 40), (0,0,0,0))
        gd = ImageDraw.Draw(glow_layer)
        gd.ellipse([(0,0), (p_size + 40, p_size + 40)], fill=border_color + (40,))
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=20))
        img.paste(glow_layer, (cx - p_size // 2 - 20, cy - p_size // 2 - 20), glow_layer)

    # Player placeholder - gradient circle with initials
    player = Image.new("RGBA", (p_size, p_size), (0,0,0,0))
    pd = ImageDraw.Draw(player)
    # Gradient fill
    for r in range(p_size // 2, 0, -1):
        ratio = r / (p_size // 2)
        clr = (30 + int(40 * (1 - ratio)), 41 + int(50 * (1 - ratio)), 59 + int(70 * (1 - ratio)))
        pd.ellipse([p_size // 2 - r, p_size // 2 - r, p_size // 2 + r, p_size // 2 + r], fill=clr)
    # Initials
    initials = "".join(w[0].upper() for w in player_name.split()[:2])
    pd.text((p_size // 2, p_size // 2), initials, fill=COLORS["WHITE_180"], font=_f("Montserrat-Bold.ttf", size // 4), anchor="mm")

    # Mask to circle
    mask = Image.new("L", (p_size, p_size), 0)
    ImageDraw.Draw(mask).ellipse([(0,0), (p_size, p_size)], fill=255)
    img.paste(player, (cx - p_size // 2, cy - p_size // 2), mask)

    # Border
    draw = ImageDraw.Draw(img)
    draw.ellipse([cx - p_size // 2, cy - p_size // 2, cx + p_size // 2, cy + p_size // 2],
                 outline=border_color, width=border_width)

def _minute_badge(draw, minute, cx, y, color=COLORS["RED"], size=100):
    """Draw a pill-shaped minute badge."""
    w, h = size * 2, size // 2
    badge = Image.new("RGBA", (W, H), (0,0,0,0))
    bd = ImageDraw.Draw(badge)
    bd.rounded_rectangle([cx - w // 2, y - h // 2, cx + w // 2, y + h // 2],
                         radius=h // 2, fill=color + (230,), outline=COLORS["WHITE_50"], width=2)
    draw._image.paste(badge, (0,0), badge)
    _draw_text(draw, f"{minute}'", _f("BebasNeue-Regular.ttf", size // 2), y, cx, COLORS["WHITE"], anchor="mm")

# === TEMPLATES ===

def draw_goal_card(scorer, minute, team_name, player_img=None, flag_img=None, output_path=None):
    output_path = output_path or _out_path()
    img = Image.new("RGBA", (W, H), COLORS["NAVY_DARK"])
    draw = ImageDraw.Draw(img)

    # 1. Radial spotlight background
    gradient = _radial_gradient((W, H), (40, 55, 80), COLORS["NAVY_DARK"], center=(W // 2, 350))
    img = Image.alpha_composite(img, gradient)
    draw = ImageDraw.Draw(img)

    # 2. Subtle noise texture
    noise = _noise_texture((W, H), 8)
    img = Image.alpha_composite(img, noise)
    draw = ImageDraw.Draw(img)

    # 3. Team color top accent bar
    _team_color_bar(draw, 0, COLORS["RED"])

    # 4. "GOAL!" with red glow
    _draw_glow_text(draw, "GOAL!", _f("Montserrat-Bold.ttf", 140), 120, W // 2,
                    COLORS["WHITE"], COLORS["RED"], glow_radius=15)

    # 5. Player photo with glow
    _player_circle(img, scorer, W // 2, 390, 300, COLORS["RED"], 6, glow=True)
    draw = ImageDraw.Draw(img)

    # 6. Soccer ball icon near photo
    ball = Image.new("RGBA", (W, H), (0,0,0,0))
    bd = ImageDraw.Draw(ball)
    bx, by = W // 2 + 170, 500
    bd.ellipse([bx - 30, by - 30, bx + 30, by + 30], fill=COLORS["WHITE"], outline=COLORS["BLACK"], width=3)
    draw._image.paste(ball, (0,0), ball)

    # 7. Minute badge
    _minute_badge(draw, minute, W // 2, 620, COLORS["RED"], size=120)

    # 8. Player name - large, bold
    _draw_text_with_shadow(draw, scorer.upper(), _f("Montserrat-Bold.ttf", 52), 710, W // 2,
                           COLORS["WHITE"], COLORS["BLACK_150"], shadow_offset=(3,3))

    # 9. Team name
    _draw_text(draw, team_name.upper(), _f("Roboto-Regular.ttf", 28), 770, W // 2, COLORS["RED"])

    # 10. Glass panel for match context at bottom
    _rounded_panel(draw, 80, 850, 1000, 980, fill=COLORS["WHITE_30"], border=COLORS["WHITE_50"], radius=24)
    _draw_text(draw, f"{team_name.upper()}  •  World Cup 2026", _f("Roboto-Regular.ttf", 22), 890, W // 2, COLORS["WHITE_180"])

    # 11. Bottom line accent
    _team_color_bar(draw, H - 8, COLORS["RED"])

    img = img.convert("RGB")
    img.save(output_path)
    return output_path


def draw_yellow_card(player, team, minute, player_img=None, output_path=None):
    output_path = output_path or _out_path()
    img = Image.new("RGBA", (W, H), COLORS["NAVY_DARK"])
    draw = ImageDraw.Draw(img)

    # Warm radial gradient (yellow tint)
    gradient = _radial_gradient((W, H), (80, 60, 20), COLORS["NAVY_DARK"], center=(W // 2, 300))
    img = Image.alpha_composite(img, gradient)
    draw = ImageDraw.Draw(img)

    noise = _noise_texture((W, H), 8)
    img = Image.alpha_composite(img, noise)
    draw = ImageDraw.Draw(img)

    _team_color_bar(draw, 0, COLORS["YELLOW"])

    # Yellow Card visual — a real card shape with proper perspective
    card_overlay = Image.new("RGBA", (W, H), (0,0,0,0))
    cd = ImageDraw.Draw(card_overlay)
    card_w, card_h = 220, 300
    cx, cy = W // 2, 210
    cd.rounded_rectangle([cx - card_w // 2, cy - card_h // 2, cx + card_w // 2, cy + card_h // 2],
                          radius=18, fill=COLORS["YELLOW"] + (230,), outline=(255, 255, 200, 180), width=3)
    cd.text((cx, cy - 30), "!", fill=COLORS["BLACK"], font=_f("Montserrat-Bold.ttf", 100), anchor="mm")
    cd.text((cx, cy + 50), "CAUTION", fill=COLORS["BLACK"], font=_f("Roboto-Regular.ttf", 24), anchor="mm")
    draw._image.paste(card_overlay, (0,0), card_overlay)

    # "YELLOW CARD" text with shadow
    _draw_text_with_shadow(draw, "YELLOW CARD", _f("Montserrat-Bold.ttf", 56), 380, W // 2,
                           COLORS["YELLOW"], COLORS["BLACK_150"], shadow_offset=(3,3), letter_spacing=4)

    # Player photo
    _player_circle(img, player, W // 2, 570, 250, COLORS["YELLOW"], 6, glow=True)
    draw = ImageDraw.Draw(img)

    # Player name
    _draw_text_with_shadow(draw, player.upper(), _f("Montserrat-Bold.ttf", 44), 740, W // 2,
                           COLORS["WHITE"], COLORS["BLACK_150"], shadow_offset=(2,2))
    _draw_text(draw, team.upper(), _f("Roboto-Regular.ttf", 26), 790, W // 2, COLORS["YELLOW"])
    _draw_text(draw, "Unsporting Behavior", _f("Roboto-Regular.ttf", 22), 830, W // 2, COLORS["GRAY"])

    _minute_badge(draw, minute, W // 2, 910, COLORS["YELLOW"], size=100)

    _team_color_bar(draw, H - 8, COLORS["YELLOW"])

    img = img.convert("RGB")
    img.save(output_path)
    return output_path


def draw_red_card(player, team, minute, player_img=None, output_path=None):
    output_path = output_path or _out_path()
    img = Image.new("RGBA", (W, H), (10, 5, 5))
    draw = ImageDraw.Draw(img)

    # Red radial gradient
    gradient = _radial_gradient((W, H), (120, 10, 10), (10, 5, 5), center=(W // 2, 300))
    img = Image.alpha_composite(img, gradient)
    draw = ImageDraw.Draw(img)

    noise = _noise_texture((W, H), 10)
    img = Image.alpha_composite(img, noise)
    draw = ImageDraw.Draw(img)

    _team_color_bar(draw, 0, COLORS["RED"])

    # Red Card graphic
    card_overlay = Image.new("RGBA", (W, H), (0,0,0,0))
    cd = ImageDraw.Draw(card_overlay)
    card_w, card_h = 220, 300
    cx, cy = W // 2, 210
    cd.rounded_rectangle([cx - card_w // 2, cy - card_h // 2, cx + card_w // 2, cy + card_h // 2],
                          radius=18, fill=COLORS["RED"] + (230,), outline=(255, 150, 150, 150), width=3)
    cd.text((cx, cy), "✕", fill=COLORS["WHITE"], font=_f("Montserrat-Bold.ttf", 120), anchor="mm")
    draw._image.paste(card_overlay, (0,0), card_overlay)

    _draw_text_with_shadow(draw, "SENT OFF", _f("Montserrat-Bold.ttf", 60), 380, W // 2,
                           COLORS["RED"], COLORS["BLACK_150"], shadow_offset=(3,3), letter_spacing=5)

    # Player photo (desaturated - convert to grayscale feel by using darker overlay)
    _player_circle(img, player, W // 2, 570, 250, COLORS["RED"], 8, glow=True)
    draw = ImageDraw.Draw(img)

    # X overlay on photo
    x_overlay = Image.new("RGBA", (W, H), (0,0,0,0))
    xd = ImageDraw.Draw(x_overlay)
    xs, ys = W // 2 - 90, 570 - 90
    line_color = COLORS["RED"] + (180,)
    xd.line([(xs, ys), (xs + 180, ys + 180)], fill=line_color, width=12)
    xd.line([(xs + 180, ys), (xs, ys + 180)], fill=line_color, width=12)
    draw._image.paste(x_overlay, (0,0), x_overlay)

    _draw_text_with_shadow(draw, player.upper(), _f("Montserrat-Bold.ttf", 44), 760, W // 2,
                           COLORS["WHITE"], COLORS["BLACK_150"], shadow_offset=(2,2))
    _draw_text(draw, team.upper(), _f("Roboto-Regular.ttf", 26), 810, W // 2, COLORS["RED"])
    _draw_text(draw, "Serious Foul Play", _f("Roboto-Regular.ttf", 22), 850, W // 2, (255, 120, 120))

    _minute_badge(draw, minute, W // 2, 920, COLORS["RED"], size=100)

    _team_color_bar(draw, H - 8, COLORS["RED"])

    img = img.convert("RGB")
    img.save(output_path)
    return output_path


def draw_sub_card(player_off, player_on, team, minute, output_path=None):
    output_path = output_path or _out_path()
    img = Image.new("RGBA", (W, H), COLORS["NAVY_DARK"])
    draw = ImageDraw.Draw(img)

    gradient = _radial_gradient((W, H), (40, 50, 70), COLORS["NAVY_DARK"], center=(W // 2, 350))
    img = Image.alpha_composite(img, gradient)
    draw = ImageDraw.Draw(img)

    noise = _noise_texture((W, H), 8)
    img = Image.alpha_composite(img, noise)
    draw = ImageDraw.Draw(img)

    _team_color_bar(draw, 0, COLORS["WHITE"])

    # Header
    _draw_text_with_shadow(draw, "SUBSTITUTION", _f("Montserrat-Bold.ttf", 52), 80, W // 2,
                           COLORS["WHITE"], COLORS["BLACK_150"], shadow_offset=(2,2), letter_spacing=6)

    # Glass divider line
    divider_y = 550
    draw.line([(100, divider_y), (W - 100, divider_y)], fill=COLORS["WHITE_50"], width=1)

    # Left - Player OUT
    _player_circle(img, player_off, W // 2 - 200, 350, 220, COLORS["RED"], 6, glow=True)
    draw = ImageDraw.Draw(img)
    _draw_text(draw, "OUT", _f("Montserrat-Bold.ttf", 28), W // 2 - 200, 500, COLORS["RED"], anchor="mm")
    _draw_text(draw, player_off.upper(), _f("Montserrat-Bold.ttf", 30), 620, W // 2 - 200, COLORS["WHITE"], anchor="mm")
    _draw_text(draw, "#10", _f("BebasNeue-Regular.ttf", 36), 670, W // 2 - 200, COLORS["RED"], anchor="mm")

    # Arrow indicator
    draw.text((W // 2, divider_y), "⟶", fill=COLORS["WHITE"], font=_f("Roboto-Regular.ttf", 40), anchor="mm")

    # Right - Player IN
    _player_circle(img, player_on, W // 2 + 200, 350, 220, COLORS["GREEN"], 6, glow=True)
    draw = ImageDraw.Draw(img)
    _draw_text(draw, "IN", _f("Montserrat-Bold.ttf", 28), W // 2 + 200, 500, COLORS["GREEN"], anchor="mm")
    _draw_text(draw, player_on.upper(), _f("Montserrat-Bold.ttf", 30), 620, W // 2 + 200, COLORS["WHITE"], anchor="mm")
    _draw_text(draw, "#7", _f("BebasNeue-Regular.ttf", 36), 670, W // 2 + 200, COLORS["GREEN"], anchor="mm")

    # Bottom info
    _rounded_panel(draw, 200, 800, 880, 920, fill=COLORS["WHITE_30"], border=COLORS["WHITE_50"], radius=20)
    _draw_text(draw, team.upper(), _f("Roboto-Regular.ttf", 24), 835, W // 2, COLORS["WHITE_180"])
    _draw_text(draw, f"Minute {minute}'", _f("BebasNeue-Regular.ttf", 32), 885, W // 2, COLORS["WHITE"])

    _team_color_bar(draw, H - 8, COLORS["WHITE"])

    img = img.convert("RGB")
    img.save(output_path)
    return output_path


def draw_halftime_image(home, away, sh, sa, comp, output_path=None):
    output_path = output_path or _out_path()
    img = Image.new("RGBA", (W, H), COLORS["NAVY_DARK"])
    draw = ImageDraw.Draw(img)

    gradient = _radial_gradient((W, H), (50, 50, 70), COLORS["NAVY_DARK"], center=(W // 2, H // 2))
    img = Image.alpha_composite(img, gradient)
    draw = ImageDraw.Draw(img)

    noise = _noise_texture((W, H), 10)
    img = Image.alpha_composite(img, noise)
    draw = ImageDraw.Draw(img)

    _team_color_bar(draw, 0, COLORS["RED"])

    _draw_text_with_shadow(draw, "HALF TIME", _f("Montserrat-Bold.ttf", 64), 90, W // 2,
                           COLORS["WHITE"], COLORS["BLACK_150"], shadow_offset=(3,3), letter_spacing=8)

    # Score display — large central scoreboard
    score_bg = Image.new("RGBA", (W, H), (0,0,0,0))
    sd = ImageDraw.Draw(score_bg)
    sd.rounded_rectangle([200, 240, 880, 440], radius=30, fill=COLORS["WHITE_30"], outline=COLORS["WHITE_50"], width=2)
    draw._image.paste(score_bg, (0,0), score_bg)

    _draw_text_with_shadow(draw, sh, _f("BebasNeue-Regular.ttf", 120), 340, 380,
                           COLORS["WHITE"], COLORS["BLACK_150"], shadow_offset=(3,3))
    _draw_text(draw, ":", _f("Roboto-Regular.ttf", 60), 340, 540, COLORS["WHITE_100"])
    _draw_text_with_shadow(draw, sa, _f("BebasNeue-Regular.ttf", 120), 340, 700,
                           COLORS["WHITE"], COLORS["BLACK_150"], shadow_offset=(3,3))

    # Team names
    _draw_text(draw, home.upper(), _f("Montserrat-Bold.ttf", 28), 200, 170, COLORS["WHITE"])
    _draw_text(draw, away.upper(), _f("Montserrat-Bold.ttf", 28), 200, 478, COLORS["WHITE"])

    # Stats glass panel
    _rounded_panel(draw, 120, 560, 960, 780, fill=COLORS["WHITE_30"], border=COLORS["WHITE_50"], radius=24)
    _draw_text(draw, "FIRST HALF STATS", _f("Montserrat-Bold.ttf", 28), 600, W // 2, COLORS["WHITE_180"])
    _draw_text(draw, "Possession: 58%  —  42%", _f("Roboto-Regular.ttf", 22), 660, W // 2, COLORS["WHITE"])
    _draw_text(draw, "Shots: 7  —  4", _f("Roboto-Regular.ttf", 22), 700, W // 2, COLORS["WHITE"])
    _draw_text(draw, "Corners: 3  —  2", _f("Roboto-Regular.ttf", 22), 740, W // 2, COLORS["WHITE"])

    # Competition
    _draw_text(draw, comp.upper(), _f("Roboto-Regular.ttf", 20), 840, W // 2, COLORS["GRAY"])

    _team_color_bar(draw, H - 8, COLORS["RED"])

    img = img.convert("RGB")
    img.save(output_path)
    return output_path


def draw_fulltime_image(home, away, sh, sa, comp, output_path=None):
    output_path = output_path or _out_path()
    img = Image.new("RGBA", (W, H), COLORS["NAVY_DARK"])
    draw = ImageDraw.Draw(img)

    gradient = _radial_gradient((W, H), (60, 60, 90), COLORS["NAVY_DARK"], center=(W // 2, H // 2))
    img = Image.alpha_composite(img, gradient)
    draw = ImageDraw.Draw(img)

    noise = _noise_texture((W, H), 12)
    img = Image.alpha_composite(img, noise)
    draw = ImageDraw.Draw(img)

    _team_color_bar(draw, 0, COLORS["GOLD"])

    _draw_text_with_shadow(draw, "FULL TIME", _f("Montserrat-Bold.ttf", 72), 80, W // 2,
                           COLORS["GOLD"], COLORS["BLACK_150"], shadow_offset=(3,3), letter_spacing=8)

    # Huge score display
    _draw_text_with_shadow(draw, sh, _f("BebasNeue-Regular.ttf", 160), 320, 380,
                           COLORS["WHITE"], COLORS["BLACK_150"], shadow_offset=(5,5))
    _draw_text_with_shadow(draw, ":", _f("Roboto-Regular.ttf", 80), 340, 540,
                           COLORS["GOLD"], COLORS["BLACK_80"], shadow_offset=(3,3))
    _draw_text_with_shadow(draw, sa, _f("BebasNeue-Regular.ttf", 160), 320, 700,
                           COLORS["WHITE"], COLORS["BLACK_150"], shadow_offset=(5,5))

    # Team names
    _draw_text(draw, home.upper(), _f("Montserrat-Bold.ttf", 30), 190, 170, COLORS["WHITE"])
    _draw_text(draw, away.upper(), _f("Montserrat-Bold.ttf", 30), 190, 478, COLORS["WHITE"])

    # Match stats
    _rounded_panel(draw, 100, 550, 980, 840, fill=COLORS["WHITE_30"], border=COLORS["WHITE_50"], radius=24)
    _draw_text(draw, "MATCH STATISTICS", _f("Montserrat-Bold.ttf", 30), 590, W // 2, COLORS["GOLD"])
    _draw_text(draw, "Possession: 55%  —  45%", _f("Roboto-Regular.ttf", 22), 650, W // 2, COLORS["WHITE"])
    _draw_text(draw, "Total Shots: 12  —  8", _f("Roboto-Regular.ttf", 22), 700, W // 2, COLORS["WHITE"])
    _draw_text(draw, "Shots on Target: 5  —  3", _f("Roboto-Regular.ttf", 22), 750, W // 2, COLORS["WHITE"])
    _draw_text(draw, "Yellow Cards: 2  —  1", _f("Roboto-Regular.ttf", 22), 800, W // 2, COLORS["WHITE"])

    _draw_text(draw, comp.upper(), _f("Roboto-Regular.ttf", 20), 900, W // 2, COLORS["GRAY"])

    _team_color_bar(draw, H - 8, COLORS["GOLD"])

    img = img.convert("RGB")
    img.save(output_path)
    return output_path


def draw_summary_image(home, away, events, comp, output_path=None):
    return draw_fulltime_image(home, away, 0, 0, comp, output_path)


def draw_live_image(home, away, comp, output_path=None):
    output_path = output_path or _out_path()
    img = Image.new("RGBA", (W, H), COLORS["NAVY_DARK"])
    draw = ImageDraw.Draw(img)

    gradient = _radial_gradient((W, H), (50, 50, 70), COLORS["NAVY_DARK"], center=(W // 2, H // 2))
    img = Image.alpha_composite(img, gradient)
    draw = ImageDraw.Draw(img)

    noise = _noise_texture((W, H), 10)
    img = Image.alpha_composite(img, noise)
    draw = ImageDraw.Draw(img)

    _team_color_bar(draw, 0, COLORS["RED"])

    # Red dot + "LIVE" badge
    live_badge = Image.new("RGBA", (W, H), (0,0,0,0))
    ld = ImageDraw.Draw(live_badge)
    ld.rounded_rectangle([W // 2 - 80, 70, W // 2 + 80, 130], radius=30, fill=COLORS["RED"] + (230,),
                         outline=COLORS["WHITE_50"], width=2)
    draw._image.paste(live_badge, (0,0), live_badge)
    draw.ellipse([W // 2 - 40, 88, W // 2 - 20, 108], fill=COLORS["WHITE"])
    _draw_text(draw, "LIVE", _f("Montserrat-Bold.ttf", 26), 100, W // 2 + 10, COLORS["WHITE"], anchor="mm")

    _draw_text_with_shadow(draw, f"{home}", _f("Montserrat-Bold.ttf", 48), 320, W // 2,
                           COLORS["WHITE"], COLORS["BLACK_150"], shadow_offset=(3,3))
    _draw_text(draw, "VS", _f("Montserrat-Bold.ttf", 36), 440, W // 2, COLORS["RED"])
    _draw_text_with_shadow(draw, f"{away}", _f("Montserrat-Bold.ttf", 48), 560, W // 2,
                           COLORS["WHITE"], COLORS["BLACK_150"], shadow_offset=(3,3))

    _draw_text(draw, comp.upper(), _f("Roboto-Regular.ttf", 22), 680, W // 2, COLORS["GRAY"])

    _rounded_panel(draw, 200, 700, 880, 820, fill=COLORS["WHITE_30"], border=COLORS["WHITE_50"], radius=20)
    _draw_text(draw, "Match is in progress", _f("Roboto-Regular.ttf", 24), 760, W // 2, COLORS["WHITE_180"])

    _team_color_bar(draw, H - 8, COLORS["RED"])

    img = img.convert("RGB")
    img.save(output_path)
    return output_path
