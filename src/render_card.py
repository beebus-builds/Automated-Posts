import os, tempfile
from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "cards")
_env = Environment(loader=FileSystemLoader(_TEMPLATE_DIR), autoescape=select_autoescape(["html"]))

def _initials(name):
    return "".join(w[0].upper() for w in name.split()[:2] if w) if name else "?"

def render_card(template_name, data, output_path):
    from playwright.sync_api import sync_playwright

    tmpl = _env.get_template(f"{template_name}.html")

    enriched = dict(data)
    for key in ("scorer", "player_off", "player_on", "player"):
        val = enriched.get(key, "")
        if val:
            enriched[f"{key}_initials"] = _initials(val)

    for src_key, dst_key in [("scorer", "initials"), ("player", "initials")]:
        if not enriched.get(dst_key) and enriched.get(src_key):
            enriched[dst_key] = _initials(enriched[src_key])
    if not enriched.get("initials"):
        enriched["initials"] = enriched.get("player_initials") or enriched.get("scorer_initials") or "?"

    enriched.setdefault("reason", "")
    enriched.setdefault("competition", data.get("comp", "World Cup 2026"))
    enriched.setdefault("off_number", "10")
    enriched.setdefault("on_number", "7")

    html = tmpl.render(**enriched)

    tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8")
    tmp.write(html)
    tmp.close()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1080, "height": 1080}, device_scale_factor=1)
        page = ctx.new_page()
        page.goto(f"file://{tmp.name}", wait_until="networkidle")
        page.screenshot(path=output_path, clip={"x": 0, "y": 0, "width": 1080, "height": 1080})
        page.close()
        ctx.close()
        browser.close()

    os.unlink(tmp.name)
    return output_path
