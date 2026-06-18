import os, time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _out_path(name=None):
    return os.path.join(_ROOT, name or f"post_{int(time.time()*1000)}_{os.getpid()}.png")

def _render(template_name, data, output_path=None):
    import sys
    _SRC = os.path.dirname(os.path.abspath(__file__))
    if _SRC not in sys.path:
        sys.path.insert(0, _SRC)
    from render_card import render_card
    output_path = output_path or _out_path()
    return render_card(template_name, data, output_path)

def draw_goal_card(scorer, minute, team_name, player_img=None, flag_img=None, output_path=None):
    return _render("goal", {
        "scorer": scorer,
        "minute": minute,
        "team_name": team_name,
    }, output_path)

def draw_yellow_card(player, team, minute, player_img=None, output_path=None):
    return _render("yellow_card", {
        "player": player,
        "team": team,
        "minute": minute,
        "reason": "Unsporting Behavior",
    }, output_path)

def draw_red_card(player, team, minute, player_img=None, output_path=None):
    return _render("red_card", {
        "player": player,
        "team": team,
        "minute": minute,
        "reason": "Serious Foul Play",
    }, output_path)

def draw_sub_card(player_off, player_on, team, minute, output_path=None):
    return _render("sub", {
        "player_off": player_off,
        "player_on": player_on,
        "team": team,
        "minute": minute,
    }, output_path)

def draw_halftime_image(home, away, sh, sa, comp, output_path=None):
    return _render("halftime", {
        "home": home,
        "away": away,
        "sh": sh,
        "sa": sa,
        "competition": comp,
    }, output_path)

def draw_fulltime_image(home, away, sh, sa, comp, output_path=None):
    return _render("fulltime", {
        "home": home,
        "away": away,
        "sh": sh,
        "sa": sa,
        "competition": comp,
    }, output_path)

def draw_summary_image(home, away, events, comp, output_path=None):
    return draw_fulltime_image(home, away, 0, 0, comp, output_path)

def draw_live_image(home, away, comp, output_path=None):
    return _render("fulltime", {
        "home": home,
        "away": away,
        "sh": "?",
        "sa": "?",
        "competition": comp,
    }, output_path)
