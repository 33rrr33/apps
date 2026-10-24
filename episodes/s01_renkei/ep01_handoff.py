# MacとiPhoneの神連携機能① Handoff — reference episode (published 2026-10-21)
import math
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="s01_renkei", title="MacとiPhoneの神連携機能", spoken="MacとiPhoneの、かみ連携機能",
              hook_split=("MacとiPhoneの", "神連携機能"), total=5)
DURATION = 15.0   # made before the switch to 20s
NUM, SLUG = 1, "handoff"
BODY = [
    ("b1", "iPhoneで見てたページ、", 0.45),
    ("b2", "MacのDockの右端をクリックすると、", 0.25),
    ("b3", "続きからそのまま開けます！", 0.0),
]
BODY_HOLD = 1.7
CTA = dict(lines=[("同じApple IDで", WHITE, 96), ("Handoffをオン", YEL, 130)], spoken="保存して試してね！")

def times(T):
    icon = T.at["b2"] + 0.3                 # Handoff icon pops into the Dock
    click = T.end["b2"] - 0.1               # cursor clicks it
    return dict(icon=icon, click=click, open=click + 0.15, done=T.at["b3"] + 0.5, extra=T.at["b3"] + 1.6)

ICON = 58
DOCK = [(10, 132, 255), (52, 199, 89), (255, 159, 10), (255, 59, 48), (175, 82, 222)]

def dock(ms, t, k):
    extra = t >= k["icon"]
    n = len(DOCK) + (1 if extra else 0)
    w = n * (ICON + 12) + 12 + (18 if extra else 0)
    x0 = 330 - w / 2                       # left of centre: the phone covers the screen's lower right
    rra(ms, (x0, MH - 82, x0 + w, MH - 10), 22, (255, 255, 255, 90))
    x = x0 + 12
    for col in DOCK:
        app_icon(ms, x, MH - 75, ICON, col, "safari" if col == DOCK[0] else None); x += ICON + 12
    if not extra: return None
    x += 9
    ImageDraw.Draw(ms).line((x - 10, MH - 72, x - 10, MH - 20), fill=WHITE, width=2)
    b = clamp((t - k["icon"]) / 1.4)
    by = -abs(math.sin(b * math.pi * 3)) * 30 * (1 - b)
    s = ICON * back_out(clamp((t - k["icon"]) / 0.3))
    ix, iy = x + (ICON - s) / 2, MH - 75 + (ICON - s) / 2 + by
    app_icon(ms, ix, iy, s, (10, 132, 255), "safari")
    rr(ms, (ix + s - 22, iy - 8, ix + s + 2, iy + 26), 6, (40, 40, 44))        # small phone badge
    rr(ms, (ix + s - 18, iy - 4, ix + s - 2, iy + 22), 3, (120, 180, 255))
    cx, cy = x + ICON / 2, MH - 46
    if k["icon"] + 0.3 < t < k["open"]:
        r = 44 + 7 * math.sin(t * 9)
        ImageDraw.Draw(ms).ellipse((cx - r, cy - r, cx + r, cy + r), outline=YEL, width=5)
    return (cx, cy)

def mac(t, k):
    ms = mac_screen_base()
    pos = dock(ms, t, k)
    if pos and k["icon"] + 0.6 < t < k["open"] + 0.4:
        p = ease_out((t - k["icon"] - 0.6) / max(0.3, k["click"] - k["icon"] - 0.6))
        cursor(ms, 300 + (pos[0] + 6 - 300) * p, 200 + (pos[1] - 4 - 200) * p,
               clamp((t - k["click"]) / 0.35) if t >= k["click"] else 0)
    if t >= k["open"] and pos:
        e = ease_out((t - k["open"]) / 0.55)
        bx = (60, 40, 720, 420); sx, sy = pos
        box = tuple(int(v) for v in (sx + (bx[0] - sx) * e, sy + (bx[1] - sy) * e, sx + (bx[2] - sx) * e, sy + (bx[3] - sy) * e))
        if box[2] - box[0] > 30:
            ly = Image.new("RGBA", (MW, MH), (0, 0, 0, 0))
            window(ly, box, "Safari" if e > 0.6 else None)
            if e > 0.6:
                draw_page(ly, (box[0] + 6, box[1] + 36, box[2] - 6, box[3] - 6), True)
                rr(ly, (box[2] - 14, box[1] + 120, box[2] - 9, box[1] + 200), 3, (180, 180, 190))
            ms.alpha_composite(ly)
    return ms

def phone(t, T, k):
    ps = phone_screen_base()
    draw_page(ps, (0, 46, PW, PH), False)
    txt(ps, (38, 25), "9:41", 17, INK, anchor="lm")
    if T.at["b1"] <= t < k["icon"]:
        fade(ps, e_at(t, T.at["b1"], 0.3), lambda l: rr(l, (PW - 10, 160, PW - 5, 240), 3, (160, 160, 170)))
    return ps

def draw_body(c, t, T):
    k = times(T)
    stage(c, mac(t, k), phone(t, T, k))
    if t < T.at["b2"]:
        telop(c, t, T.body, [("① iPhoneで見てたページ", WHITE)])
    elif t < T.at["b3"]:
        telop(c, t, T.at["b2"], [("② Dockの右端をクリック", YEL)])
    else:
        telop(c, t, T.at["b3"], [("続きからそのまま開く！", YEL)], size=92)
    badge(c, t, k["done"], "スクロール位置もそのまま", 1290, GREEN, size=42, cx=370)
    badge(c, t, k["extra"], "メール・メモでもOK", 1400, PURPLE, size=42, cx=370)

def sfx(T):
    k = times(T)
    return [("pop", k["icon"]), ("click", k["click"]), ("whoosh", k["open"] + 0.25), ("ding", k["done"]), ("pop", k["extra"])]

def stills(T):
    k = times(T)
    return [T.at["b1"] + 0.8, k["icon"] + 0.8, k["click"] + 0.1, k["done"] + 0.3, k["extra"] + 0.6]
