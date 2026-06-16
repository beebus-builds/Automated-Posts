from PIL import Image, ImageDraw, ImageFont
import os

FONT_BOLD = None
FONT_REGULAR = None

def _init_fonts():
    global FONT_BOLD, FONT_REGULAR
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
              "C:/Windows/Fonts/arialbd.ttf"]:
        if os.path.exists(p):
            FONT_BOLD = p
            break
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/TTF/DejaVuSans.ttf",
              "C:/Windows/Fonts/arial.ttf"]:
        if os.path.exists(p):
            FONT_REGULAR = p
            break

def _font(size, bold=False):
    _init_fonts()
    path = FONT_BOLD if bold else FONT_REGULAR
    return ImageFont.truetype(path, size) if path else ImageFont.load_default()

def _center(draw, text, font, y, fill="white"):
    b = draw.textbbox((0, 0), text, font=font)
    draw.text(((1200 - (b[2] - b[0])) // 2, y), text, fill=fill, font=font)
    return y + (b[3] - b[1]) + 8

def generate_schedule_image(matches_text, date_str):
    _init_fonts()
    img = Image.new("RGB", (1200, 630), (18, 18, 34))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (1200, 80)], fill=(40, 140, 255))
    f_big = _font(44, bold=True)
    _center(draw, "MATCH DAY", f_big, 14, "white")
    f_date = _font(24)
    _center(draw, date_str, f_date, 90, "lightgray")
    lines = matches_text.split("\n")
    f_match = _font(28)
    y = 150
    for line in lines:
        _center(draw, line.strip(), f_match, y, "white")
        y += 45
    _center(draw, "Follow for live updates!", _font(20), 550, "gray")
    path = "post_image.png"
    img.save(path)
    return path
