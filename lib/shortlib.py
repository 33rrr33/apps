"""Shared engine for the daily 15-second YouTube Shorts (1080x1920, 30fps).

An episode module (episodes/<series>/epNN_<slug>.py) provides:
    SERIES   dict(key, title, spoken, total)   e.g. title="MacとiPhoneの神連携機能", spoken="MacとiPhoneの、かみ連携機能"
    NUM      episode number inside the series (1..5)
    BODY     list of (cue_id, spoken_text, gap_after_seconds)
    BODY_HOLD seconds to keep the body scene after the last body line (room for animations)
    CTA      dict(lines=[(text, color, size)], spoken=..., chip=optional str)
    draw_body(c, t, T)   draws the main scene; T gives cue times (T.at["b1"], T.end["b1"], T.body, T.cta)
    sfx(T)   optional -> list of (kind, time) with kind in pop/click/ding/whoosh
    stills(T) optional -> list of times for the preview sheet

Run:  python3 lib/shortlib.py episodes/<series>/epNN_<slug>.py [stills|render]
"""
import asyncio, importlib.util, json, math, os, ssl, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, ".cache")
OUT_DIR = os.path.join(ROOT, "out")
W, H, FPS, TOTAL = 1080, 1920, 30, 15.0
YEL, WHITE, BLUE, RED, GREEN, GRAY, INK, PURPLE, ORANGE = (255, 214, 10), (255, 255, 255), (10, 132, 255), (255, 69, 58), (48, 209, 88), (142, 142, 147), (28, 28, 32), (175, 82, 222), (255, 159, 10)

# ---------------------------------------------------------------- fonts
FONT_URLS = {
    900: "https://fonts.gstatic.com/s/notosansjp/v57/-F6jfjtqLzI2JPCgQBnw7HFyzSD-AsregP8VFLgk75s.ttf",
    500: "https://fonts.gstatic.com/s/notosansjp/v57/-F6jfjtqLzI2JPCgQBnw7HFyzSD-AsregP8VFCMj75s.ttf",
}
def font_path(w):
    p = os.path.join(CACHE, f"NotoSansJP-{w}.ttf")
    if not os.path.exists(p) or os.path.getsize(p) < 100000:
        os.makedirs(CACHE, exist_ok=True)
        subprocess.run(["curl", "-sSfL", "-o", p, FONT_URLS[w]], check=True)
    return p

_fc = {}
def font(size, bold=True):
    k = (int(size), bold)
    if k not in _fc: _fc[k] = ImageFont.truetype(font_path(900 if bold else 500), int(size))
    return _fc[k]

# ---------------------------------------------------------------- math / easing
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_inout(x): x = clamp(x); return 3 * x * x - 2 * x ** 3
def back_out(x, s=1.7):
    x = clamp(x) - 1
    return x * x * ((s + 1) * x + s) + 1
def e_at(t, start, dur=0.4): return ease_out((t - start) / dur) if t > start else 0.0

# ---------------------------------------------------------------- drawing helpers
def txt(img, xy, s, size, fill, bold=True, anchor="la", stroke=0, sf=(10, 10, 20)):
    ImageDraw.Draw(img).text(xy, s, font=font(size, bold), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=sf)

def rr(img, box, r, fill, outline=None, width=0):
    """Opaque rounded rect (overwrites pixels). Use rra() for translucent fills."""
    ImageDraw.Draw(img).rounded_rectangle([int(v) for v in box], int(r), fill=fill, outline=outline, width=width)

def fade(base, alpha, fn, *a):
    """Draw fn(layer) on a transparent layer and blend it onto base with the given alpha."""
    if alpha <= 0.01: return
    ly = Image.new("RGBA", base.size, (0, 0, 0, 0))
    fn(ly, *a)
    if alpha < 0.99: ly.putalpha(ly.getchannel("A").point(lambda v: int(v * alpha)))
    base.alpha_composite(ly)

def rra(img, box, r, fill, **kw):
    """Rounded rect that alpha-blends instead of overwriting pixels."""
    fade(img, 1, lambda l: rr(l, box, r, fill, **kw))

def shadow(img, box, r, blur=14, off=8, a=110):
    x0, y0, x1, y1 = [int(v) for v in box]
    pad = blur * 3
    sh = Image.new("RGBA", (x1 - x0 + pad * 2, y1 - y0 + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad, pad + x1 - x0, pad + y1 - y0), r, fill=(0, 0, 0, a))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)), (x0 - pad, y0 - pad + off))

def grad(w, h, c0, c1, horiz=False):
    a = np.linspace(0, 1, w if horiz else h)
    a = a[None, :, None] if horiz else a[:, None, None]
    g = (np.array(c0)[None, None, :] * (1 - a) + np.array(c1)[None, None, :] * a) * np.ones((h, w, 1))
    return Image.fromarray(g.astype(np.uint8), "RGB").convert("RGBA")

def wrap(s, f, maxw):
    lines, cur = [], ""
    for ch in s:
        if f.getlength(cur + ch) > maxw and cur and ch not in "、。！？」）":
            lines.append(cur); cur = ch
        else:
            cur += ch
    if cur: lines.append(cur)
    return lines

def bwrap(s, f, maxw):
    """wrap() with balanced line widths (avoids a lone character on the last line)."""
    lines = wrap(s, f, maxw)
    if len(lines) < 2: return lines
    lo, hi = f.getlength(s) / len(lines), maxw
    for _ in range(14):
        mid = (lo + hi) / 2
        if len(wrap(s, f, mid)) > len(lines): lo = mid
        else: hi = mid
    return wrap(s, f, hi + 1)

def window(img, box, title=None, bg=(250, 250, 252, 255), bar=(232, 232, 236, 255), tcol=(60, 60, 66)):
    x0, y0, x1, y1 = box
    shadow(img, box, 14)
    rr(img, box, 14, bg)
    rr(img, (x0, y0, x1, y0 + 34), 14, bar)
    ImageDraw.Draw(img).rectangle((x0, y0 + 20, x1, y0 + 34), fill=bar)
    d = ImageDraw.Draw(img)
    for i, col in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        d.ellipse((x0 + 14 + i * 22, y0 + 11, x0 + 27 + i * 22, y0 + 24), fill=col)
    if title: txt(img, ((x0 + x1) / 2, y0 + 17), title, 16, tcol, anchor="mm")

def cursor(img, x, y, click=0.0):
    d = ImageDraw.Draw(img)
    if click > 0:
        r = 10 + 26 * click
        d.ellipse((x - r, y - r, x + r, y + r), outline=(255, 214, 10, int(255 * (1 - click))), width=4)
    pts = [(x, y), (x, y + 26), (x + 7, y + 20), (x + 12, y + 31), (x + 17, y + 29), (x + 12, y + 18), (x + 21, y + 18)]
    d.polygon(pts, fill=(0, 0, 0), outline=(255, 255, 255))

def toggle(img, x, y, on):
    rr(img, (x, y, x + 46, y + 28), 14, GREEN if on else (200, 200, 205))
    cx = x + 32 if on else x + 14
    ImageDraw.Draw(img).ellipse((cx - 12, y + 2, cx + 12, y + 26), fill=WHITE)

def app_icon(img, x, y, s, col, kind=None):
    """Simple app icon. kind: safari / phone / bubble / cam / None."""
    rr(img, (x, y, x + s, y + s), s * 0.23, col)
    d = ImageDraw.Draw(img)
    if kind == "safari":
        d.ellipse((x + s * .15, y + s * .15, x + s * .85, y + s * .85), fill=WHITE)
        d.polygon([(x + s * .62, y + s * .3), (x + s * .45, y + s * .55), (x + s * .55, y + s * .45)], fill=RED)
        d.polygon([(x + s * .38, y + s * .7), (x + s * .45, y + s * .55), (x + s * .55, y + s * .45)], fill=GRAY)
    elif kind == "phone":
        rr(img, (x + s * .32, y + s * .14, x + s * .68, y + s * .86), s * .08, WHITE)
        rr(img, (x + s * .36, y + s * .2, x + s * .64, y + s * .78), s * .04, col)
    elif kind == "bubble":
        d.ellipse((x + s * .18, y + s * .22, x + s * .82, y + s * .72), fill=WHITE)
        d.polygon([(x + s * .3, y + s * .62), (x + s * .24, y + s * .82), (x + s * .45, y + s * .68)], fill=WHITE)
    elif kind == "cam":
        rr(img, (x + s * .15, y + s * .32, x + s * .62, y + s * .7), s * .06, WHITE)
        d.polygon([(x + s * .62, y + s * .51), (x + s * .85, y + s * .34), (x + s * .85, y + s * .68)], fill=WHITE)

def check(img, x, y, s, col=WHITE, w=5):
    ImageDraw.Draw(img).line([(x, y + s * .5), (x + s * .38, y + s * .85), (x + s, y)], fill=col, width=w, joint="curve")

def bubble(img, x, y, s, col, right, tc=WHITE, size=18, maxw=300):
    """Chat bubble; x is the left edge (or right edge if right=True). Returns its height."""
    f = font(size, False)
    lines = wrap(s, f, maxw)
    w = max(f.getlength(l) for l in lines) + 28
    h = len(lines) * (size + 8) + 16
    x0 = x - w if right else x
    rr(img, (x0, y, x0 + w, y + h), 18, col)
    for i, l in enumerate(lines): txt(img, (x0 + 14, y + 8 + i * (size + 8)), l, size, tc, bold=False)
    return h

def draw_page(img, box, big):
    """A generic web article (cafe guide) inside box."""
    x0, y0, x1, y1 = box
    rr(img, box, 10 if big else 0, WHITE)
    s = 1.6 if big else 1.0
    rr(img, (x0 + 10, y0 + 8, x1 - 10, y0 + 8 + 22 * s), 11 * s, (236, 236, 240))
    txt(img, ((x0 + x1) / 2, y0 + 8 + 11 * s), "cafe-guide.jp", 12 * s, (90, 90, 96), bold=False, anchor="mm")
    hy = y0 + 18 + 26 * s
    ih = int((y1 - y0) * 0.38)
    img.alpha_composite(grad(int(x1 - x0 - 20), ih, (214, 150, 90), (120, 70, 40)), (int(x0 + 10), int(hy)))
    ImageDraw.Draw(img).ellipse((x0 + (x1 - x0) * .4, hy + ih * .3, x0 + (x1 - x0) * .6, hy + ih * .75), fill=(250, 245, 235))
    ty = hy + ih + 12
    txt(img, (x0 + 14, ty), "週末行きたい", 18 * s, INK)
    txt(img, (x0 + 14, ty + 24 * s), "カフェ10選", 18 * s, INK)
    for i in range(3):
        ly = ty + 58 * s + i * 16 * s
        if ly + 8 < y1 - 6:
            rr(img, (x0 + 14, ly, x1 - 14 - (40 if i == 2 else 0), ly + 7 * s), 3, (220, 220, 226))

# ---------------------------------------------------------------- standard stage: Mac + iPhone
# Keep text, badges and important UI above y≈1550: the Shorts overlay covers the bottom.
MX0, MY0, MW, MH = 80, 600, 920, 510          # Mac screen (canvas coords)
PX0, PY0, PW, PH = 732, 932, 256, 566         # iPhone screen (canvas coords) – in front of the Mac's lower right
MAC_WALL = None

def make_bg():
    g = np.array(grad(W, H, (10, 14, 34), (28, 12, 50)).convert("RGB")).astype(float)
    yy, xx = np.mgrid[0:H, 0:W]
    for cx, cy, r, col in [(150, 350, 600, (40, 80, 255)), (950, 1500, 650, (170, 50, 255))]:
        g += np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (r * r)))[..., None] * np.array(col) * 0.3
    return Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).convert("RGBA")
BG = make_bg()

def mac_screen_base():
    global MAC_WALL
    if MAC_WALL is None: MAC_WALL = grad(MW, MH, (64, 92, 200), (150, 70, 170))
    ms = MAC_WALL.copy()
    rra(ms, (0, 0, MW, 26), 0, (255, 255, 255, 70))
    ImageDraw.Draw(ms).ellipse((16, 6, 30, 20), fill=WHITE)
    txt(ms, (MW - 16, 13), "10:24", 15, WHITE, anchor="rm")
    return ms

def phone_screen_base(col=(255, 255, 255, 255), dark_text=True):
    ps = Image.new("RGBA", (PW, PH), col)
    txt(ps, (38, 25), "9:41", 17, INK if dark_text else WHITE, anchor="lm")
    return ps

def mac_frame(c):
    shadow(c, (60, 580, 1020, 1150), 28, blur=24, off=18, a=150)
    rr(c, (60, 580, 1020, 1130), 28, (22, 22, 26), outline=(70, 70, 78), width=3)
    ImageDraw.Draw(c).polygon([(10, 1130), (1070, 1130), (1040, 1168), (40, 1168)], fill=(196, 198, 204))
    rr(c, (460, 1130, 620, 1140), 5, (160, 162, 168))

def phone_frame(c):
    shadow(c, (718, 918, 1002, 1512), 46, blur=22, off=16, a=170)
    rr(c, (718, 918, 1002, 1512), 46, (36, 36, 40), outline=(120, 120, 130), width=4)

def finish_phone(ps):
    m = Image.new("L", (PW, PH), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, PW - 1, PH - 1), 38, fill=255)
    rr(ps, (PW / 2 - 44, 12, PW / 2 + 44, 38), 13, (0, 0, 0))
    ps.putalpha(Image.fromarray(np.minimum(np.array(ps.getchannel("A")), np.array(m))))
    return ps

def stage(c, ms=None, ps=None):
    """Compose the Mac (ms: MWxMH image) and iPhone (ps: PWxPH image). Pass None to hide a device."""
    if ms is not None:
        mac_frame(c); c.alpha_composite(ms, (MX0, MY0))
    if ps is not None:
        phone_frame(c); c.alpha_composite(finish_phone(ps), (PX0, PY0))

# ---------------------------------------------------------------- big text elements
def telop(c, t, start, lines, y0=380, size=84):
    """Pop-in headline(s). lines: list of (text, color). Auto-shrinks to fit 1000px."""
    for i, (s, col) in enumerate(lines):
        p = clamp((t - start - i * 0.15) / 0.3)
        if p <= 0: continue
        f = font(size); sz = size
        while f.getlength(s) > 1000: sz -= 4; f = font(sz)
        ly = Image.new("RGBA", (1080, 220), (0, 0, 0, 0))
        txt(ly, (540, 110), s, sz, col, anchor="mm", stroke=9)
        k = back_out(p)
        ly = ly.resize((max(1, int(1080 * k)), max(1, int(220 * k))), Image.BICUBIC)
        c.alpha_composite(ly, (int(540 - ly.width / 2), int(y0 + i * (size + 30) - ly.height / 2)))

def badge(c, t, start, s, cy, col, tc=WHITE, size=52, cx=540):
    p = clamp((t - start) / 0.3)
    if p <= 0: return
    f = font(size); w = f.getlength(s) + 90
    ly = Image.new("RGBA", (int(w), size + 50), (0, 0, 0, 0))
    rr(ly, (0, 0, w - 1, size + 49), (size + 50) // 2, col)
    txt(ly, (w / 2, (size + 50) / 2), s, size, tc, anchor="mm")
    k = back_out(p)
    ly = ly.resize((max(1, int(ly.width * k)), max(1, int(ly.height * k))), Image.BICUBIC)
    c.alpha_composite(ly, (int(cx - ly.width / 2), int(cy - ly.height / 2)))

def fly(c, t, start, dur, frm, to, label, col):
    """A labelled chip flying along an arc from frm to to (canvas coords)."""
    if not (start <= t <= start + dur): return
    e = ease_inout((t - start) / dur)
    x = frm[0] + (to[0] - frm[0]) * e
    y = frm[1] + (to[1] - frm[1]) * e - math.sin(e * math.pi) * 220
    f = font(30); w = f.getlength(label) + 44
    ly = Image.new("RGBA", (int(w) + 50, 110), (0, 0, 0, 0))
    shadow(ly, (25, 25, 25 + w, 83), 29, blur=8, off=4)
    rr(ly, (25, 25, 25 + w, 83), 29, col)
    txt(ly, (25 + w / 2, 54), label, 30, WHITE, anchor="mm")
    s = 1 + 0.3 * math.sin(e * math.pi)
    ly = ly.resize((int(ly.width * s), int(ly.height * s)), Image.BICUBIC)
    c.alpha_composite(ly, (int(x - ly.width / 2), int(y - ly.height / 2)))

def keycaps(c, t, start, keys, cy, press_t=None, cx=540, scale=1.0):
    """Keyboard keys, e.g. keys=[("⌘","command"), ("V",None)]. Pops in at start, pressed at press_t."""
    p = clamp((t - start) / 0.35)
    if p <= 0: return
    pressed = press_t is not None and press_t <= t < press_t + 0.4
    widths = [220 if word else 150 for _, word in keys]
    total = sum(widths) + 70 * (len(keys) - 1)
    ly = Image.new("RGBA", (total + 20, 220), (0, 0, 0, 0))
    x = 10
    for i, ((sym, word), w) in enumerate(zip(keys, widths)):
        dy = 10 if pressed else 0
        rr(ly, (x, 26, x + w, 196), 26, (120, 120, 132))
        rr(ly, (x, 10 + dy, x + w, 182 + dy - (0 if pressed else 4)), 26, (255, 236, 150) if pressed else (246, 246, 250))
        if word:
            txt(ly, (x + w / 2, 72 + dy), sym, 74, INK, anchor="mm")
            txt(ly, (x + w / 2, 140 + dy), word, 30, (60, 60, 70), bold=False, anchor="mm")
        else:
            sz = 80 if len(sym) <= 2 else 46
            txt(ly, (x + w / 2, 96 + dy), sym, sz, INK, anchor="mm")
        if i < len(keys) - 1: txt(ly, (x + w + 35, 100), "+", 60, WHITE, anchor="mm")
        x += w + 70
    k = back_out(p) * scale
    ly = ly.resize((max(1, int(ly.width * k)), max(1, int(ly.height * k))), Image.BICUBIC)
    c.alpha_composite(ly, (int(cx - ly.width / 2), int(cy - ly.height / 2)))

def big_cross(c, t, start, cx=540, cy=860, r=230):
    if t <= start: return
    p = ease_out((t - start) / 0.3)
    ly = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ly)
    d.line((cx - r * p, cy - r * p, cx + r * p, cy + r * p), fill=RED, width=44)
    d.line((cx + r * p, cy - r * p, cx - r * p, cy + r * p), fill=RED, width=44)
    c.alpha_composite(ly)

# ---------------------------------------------------------------- standard scenes
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩"

def series_tag(c, ep):
    s = f"{ep.SERIES['title']}  #{ep.NUM}"
    w = font(36).getlength(s) + 60
    rra(c, (540 - w / 2, 170, 540 + w / 2, 226), 28, (255, 255, 255, 40), outline=(255, 255, 255, 120), width=2)
    txt(c, (540, 198), s, 36, WHITE, anchor="mm")

def hook_scene(c, t, ep):
    top, bottom = ep.SERIES.get("hook_split", (ep.SERIES["title"], ""))
    telop(c, t, 0.15, [(top, WHITE)], y0=640, size=104)
    telop(c, t, 0.45, [(bottom + CIRCLED[ep.NUM - 1], YEL)], y0=800, size=150)
    badge(c, t, 1.2, getattr(ep, "HOOK_BADGE", "知らないと損してる…！"), 1010, RED)
    p = e_at(t, 0.6, 0.5)
    if p <= 0: return
    icon = getattr(ep, "draw_hook_art", None)
    ly = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if icon: icon(ly, t)
    else: _hook_devices(ly, t)
    if p < 1: ly.putalpha(ly.getchannel("A").point(lambda v: int(v * p)))
    c.alpha_composite(ly)

def _hook_devices(ly, t):
    rr(ly, (250, 1170, 700, 1440), 18, (22, 22, 26), outline=(90, 90, 100), width=3)
    ly.alpha_composite(grad(420, 240, (64, 92, 200), (150, 70, 170)), (265, 1185))
    ImageDraw.Draw(ly).polygon([(220, 1440), (730, 1440), (712, 1462), (238, 1462)], fill=(196, 198, 204))
    rr(ly, (720, 1230, 840, 1470), 22, (36, 36, 40), outline=(120, 120, 130), width=3)
    ly.alpha_composite(grad(104, 224, (255, 140, 90), (120, 60, 200)), (728, 1238))
    d = ImageDraw.Draw(ly)
    for k in range(3):
        q = (t * 0.9 + k / 3) % 1
        r = 30 + q * 130
        d.arc((715 - r, 1340 - r, 715 + r, 1340 + r), 200, 340, fill=(255, 214, 10, int(255 * (1 - q))), width=7)

def cta_scene(c, t, ep, T):
    s = T.cta
    for i, (text, col, size) in enumerate(ep.CTA["lines"]):
        telop(c, t, s + i * 0.25, [(text, col)], y0=600 + sum(ep.CTA["lines"][j][2] + 40 for j in range(i)), size=size)
    y = 980
    if ep.CTA.get("chip"):
        badge(c, t, s + 0.9, ep.CTA["chip"], y, (70, 70, 84), size=40); y += 140
    badge(c, t, s + 1.4, "保存して試してみてね！", y, RED); y += 150
    total = ep.SERIES.get("total", 5)
    nxt = f"フォローで{CIRCLED[ep.NUM]}もチェック" if ep.NUM < total else "次のシリーズもお楽しみに！"
    badge(c, t, s + 2.0, nxt, y, WHITE, tc=INK, size=44)

# ---------------------------------------------------------------- timeline
class Timeline:
    pass

def build_timeline(ep, durs):
    T = Timeline(); T.at, T.end = {}, {}
    def put(cid, at):
        T.at[cid] = at; T.end[cid] = at + durs[cid]
    put("hook", 0.3)
    T.body = T.end["hook"] + 0.35
    t = T.body + 0.1
    for cid, _, gap in ep.BODY:
        put(cid, t); t = T.end[cid] + gap
    T.cta = T.end[ep.BODY[-1][0]] + getattr(ep, "BODY_HOLD", 1.5)
    put("cta", T.cta + 0.3)
    if T.end["cta"] > TOTAL - 0.8:
        raise SystemExit(f"Too long: narration ends at {T.end['cta']:.2f}s (max {TOTAL - 0.8}s). Shorten lines or gaps/BODY_HOLD.")
    return T

def all_lines(ep):
    lines = {"hook": f"{ep.SERIES['spoken']}、その{ep.NUM}！"}
    for cid, text, _ in ep.BODY: lines[cid] = text
    lines["cta"] = ep.CTA["spoken"]
    return lines

# ---------------------------------------------------------------- TTS
def tts(ep, workdir):
    """Japanese narration (edge-tts, Nanami). Write 神 as かみ etc. in spoken text: the engine reads kanji its own way."""
    import edge_tts, edge_tts.communicate as cm
    ca = "/root/.ccr/ca-bundle.crt"
    if os.path.exists(ca): cm._SSL_CTX = ssl.create_default_context(cafile=ca)
    vo = os.path.join(workdir, "vo"); os.makedirs(vo, exist_ok=True)
    lines = all_lines(ep)
    rate = getattr(ep, "RATE", "+25%")
    async def one(k, s):
        for i in range(4):
            try:
                return await edge_tts.Communicate(s, "ja-JP-NanamiNeural", rate=rate).save(f"{vo}/{k}.mp3")
            except Exception:
                if i == 3: raise
                await asyncio.sleep(2)
    async def main(): await asyncio.gather(*(one(k, s) for k, s in lines.items()))
    asyncio.run(main())
    durs = {}
    for k in lines:
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", f"{vo}/{k}.mp3", "-af",
                        "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
                        "-ar", "44100", "-ac", "1", f"{vo}/{k}.wav"], check=True, stdin=subprocess.DEVNULL)
        durs[k] = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{vo}/{k}.wav"],
                                       capture_output=True, text=True).stdout)
    json.dump({"lines": lines, "durs": durs}, open(f"{vo}/durs.json", "w"), ensure_ascii=False, indent=1)
    return durs

def load_durs(ep, workdir):
    p = os.path.join(workdir, "vo", "durs.json")
    if os.path.exists(p):
        d = json.load(open(p))
        if d["lines"] == all_lines(ep): return d["durs"]
    return tts(ep, workdir)

# ---------------------------------------------------------------- audio
SR = 44100

def _lowpass(x, fc, order=2):
    """Zero-phase lowpass via FFT (no scipy needed)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / np.sqrt(1 + (f / fc) ** (2 * order)), len(x))

def _highpass(x, fc, order=2):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / np.sqrt(1 + (fc / np.maximum(f, 1e-3)) ** (2 * order)), len(x))

def _hz(m): return 440.0 * 2 ** ((m - 69) / 12)

def bgm(n, seed=0, bpm=124):
    """Upbeat, stylish house loop: four-on-the-floor, swung hats, claps, Rhodes-like chord stabs
    (Dm9 - G13 - Cmaj9 - Am9), syncopated bass, ping-pong plucks, kick sidechain. Returns (n, 2)."""
    rng = np.random.default_rng(seed)
    beat = 60 / bpm; six = beat / 4
    t_all = np.arange(n) / SR
    drums, keys, bass, pluck, pad = (np.zeros((n, 2)) for _ in range(5))

    def put(buf, sig, at, g=1.0, pan=0.0):
        s = int(round(at * SR))
        if s >= n: return
        if s < 0: sig, s = sig[-s:], 0
        e = min(n, s + len(sig))
        buf[s:e, 0] += sig[: e - s] * g * (1 - max(0, pan))
        buf[s:e, 1] += sig[: e - s] * g * (1 + min(0, pan))

    def tt(sec): return np.arange(int(sec * SR)) / SR

    # --- drum sounds
    x = tt(0.32)
    kick = np.sin(2 * np.pi * np.cumsum(48 + 160 * np.exp(-x * 38)) / SR) * np.exp(-x * 9)
    kick[:60] += np.linspace(0.6, 0, 60) * rng.standard_normal(60) * 0.3
    x = tt(0.25)
    nz = _highpass(rng.standard_normal(len(x)), 900)
    clap_env = sum(np.exp(-np.maximum(x - d, 0) * 90) * (x >= d) for d in (0, 0.011, 0.022)) + 0.6 * np.exp(-x * 18)
    clap = _lowpass(nz, 6000) * clap_env * 0.5
    x = tt(0.05); hat_c = _highpass(rng.standard_normal(len(x)), 7000) * np.exp(-x * 90)
    x = tt(0.16); hat_o = _highpass(rng.standard_normal(len(x)), 7500) * np.exp(-x * 22)

    # --- tonal sounds
    def rhodes(m, dur):
        f = _hz(m); x = tt(dur + 0.25)
        idx = 1.6 * np.exp(-x * 7) + 0.25
        s = np.sin(2 * np.pi * f * x + idx * np.sin(2 * np.pi * f * x))
        s += 0.18 * np.sin(2 * np.pi * f * 4.01 * x) * np.exp(-x * 14)          # tine "ping"
        env = np.minimum(1, x / 0.004) * np.exp(-x * 2.4)
        env *= np.clip(1 - (x - dur) / 0.25, 0, 1)                                 # release
        return s * env
    def bass_note(m, dur):
        f = _hz(m); x = tt(dur + 0.05)
        s = np.sin(2 * np.pi * f * x) + 0.35 * np.sin(4 * np.pi * f * x) + 0.12 * np.sin(6 * np.pi * f * x)
        return s * np.minimum(1, x / 0.006) * np.exp(-x * 3) * np.clip(1 - (x - dur) / 0.05, 0, 1)
    def pluck_note(m):
        f = _hz(m); x = tt(0.22)
        s = sum(np.sin(2 * np.pi * f * k * x) / k for k in (1, 3, 5, 7))
        return s * np.minimum(1, x / 0.002) * np.exp(-x * 22)
    def pad_chord(ms, dur):
        x = tt(dur)
        s = sum(np.sin(2 * np.pi * _hz(m) * d * x + rng.uniform(0, 6)) for m in ms for d in (0.997, 1.0, 1.003))
        return s * np.minimum(1, x / 0.3) * np.minimum(1, (dur - x) / 0.3)

    CHORDS = [  # (bass root, Rhodes voicing, arp notes)
        (38, [53, 57, 60, 64], [65, 69, 72, 76, 72, 69]),     # Dm9
        (43, [53, 59, 64, 69], [65, 71, 76, 81, 76, 71]),     # G13
        (36, [52, 55, 59, 62], [64, 67, 71, 74, 71, 67]),     # Cmaj9
        (45, [55, 59, 60, 64], [67, 71, 72, 76, 72, 71]),     # Am9
    ]
    STABS = [(0, 3), (6, 2), (10, 3), (14, 2)]                 # (16th step, length in 16ths) — house syncopation
    BASS = [(0, 2, 0), (3, 1, 0), (6, 2, 12), (8, 2, 0), (11, 1, 7), (14, 2, 0)]   # (step, len, interval)
    bar = beat * 4
    nbars = int(n / SR / bar) + 2
    for b in range(nbars):
        root, voicing, arp = CHORDS[b % 4]
        t0 = b * bar
        for step, ln in STABS:
            for j, m in enumerate(voicing):
                put(keys, rhodes(m, ln * six * 0.9), t0 + step * six + j * 0.004, 0.30, pan=(j - 1.5) * 0.3)
        for step, ln, iv in BASS:
            put(bass, bass_note(root + iv, ln * six * 0.85), t0 + step * six, 0.42)
        for s16 in range(16):
            swing = six * 0.18 if s16 % 2 else 0
            put(pluck, pluck_note(arp[s16 % len(arp)]), t0 + s16 * six + swing, 0.07, pan=0.5 if s16 % 2 else -0.5)
        put(pad, pad_chord(voicing, bar), t0, 0.03)
        for k in range(4):
            put(drums, kick, t0 + k * beat, 0.85)
            if k in (1, 3): put(drums, clap, t0 + k * beat, 0.28, pan=0.05)
            put(drums, hat_o, t0 + k * beat + beat / 2, 0.13, pan=0.25)
        for s16 in range(16):
            swing = six * 0.18 if s16 % 2 else 0
            vel = (0.5, 0.25, 0.0, 0.3)[s16 % 4]
            if vel: put(drums, hat_c, t0 + s16 * six + swing, 0.26 * vel, pan=-0.3)

    # ping-pong delay on the plucks (dotted 8th)
    d = int(beat * 0.75 * SR)
    wet = np.zeros_like(pluck); src = pluck.copy()
    for k in range(1, 5):
        src = np.roll(src[:, ::-1], d, axis=0); src[:d] = 0; src *= 0.45
        wet += src
    pluck = pluck + _lowpass_stereo(wet, 3500)
    # sidechain: everything melodic ducks on each kick
    ph = (t_all % beat)
    sc = (0.3 + 0.7 * (1 - np.exp(-ph / 0.075)))[:, None]
    keys = _lowpass_stereo(keys, 5000); pad = _lowpass_stereo(pad, 2500)
    haas = int(0.014 * SR)                                     # widen keys/pad: delay the right channel
    for buf in (keys, pad): buf[haas:, 1] = buf[:-haas, 1].copy(); buf[:haas, 1] = 0
    mix = drums + (keys + _lowpass_stereo(bass, 900) + pluck + pad) * sc
    # short intro fade-in so the first kick doesn't click
    mix *= np.minimum(1, t_all / 0.02)[:, None]
    return mix / (np.max(np.abs(mix)) + 1e-9) * 0.55

def _lowpass_stereo(x, fc):
    return np.stack([_lowpass(x[:, 0], fc), _lowpass(x[:, 1], fc)], 1)

def make_audio(path, ep, T, workdir):
    sr = SR; n = int(sr * TOTAL)
    out = np.zeros(n); rng = np.random.default_rng(ep.NUM)
    def add(sig, at, g=1.0):
        s = int(at * sr)
        if s < 0: sig, s = sig[-s:], 0
        e = min(n, s + len(sig))
        if s < n: out[s:e] += sig[: e - s] * g
    def env(ls, dec):
        x = np.arange(int(ls * sr)) / sr
        return x, np.exp(-x * dec)
    def whoosh(at, g=0.4):
        x, _ = env(0.35, 0)
        k = np.convolve(rng.standard_normal(len(x)), np.ones(12) / 12, mode="same")
        add(k * np.sin(np.pi * x / x[-1]) ** 2, at - 0.2, g)
    def pop(at, f=900):
        x, e = env(0.12, 40); add(np.sin(2 * np.pi * (f + 600 * np.exp(-x * 60)) * x) * e, at, 0.28)
    def click(at):
        x, e = env(0.05, 120); add((rng.standard_normal(len(x)) * 0.6 + np.sin(2 * np.pi * 2400 * x)) * e, at, 0.45)
    def ding(at):
        x, e = env(0.9, 5)
        add((np.sin(2 * np.pi * 1318.5 * x) + 0.6 * np.sin(2 * np.pi * 1975.5 * x)) * e, at, 0.18)
        add((np.sin(2 * np.pi * 1760 * x) + 0.5 * np.sin(2 * np.pi * 2637 * x)) * e, at + 0.1, 0.15)
    kinds = dict(pop=pop, click=click, ding=ding, whoosh=whoosh)
    for s in (T.body, T.cta): whoosh(s)
    for a in (0.15, 0.45, 1.2, T.cta + 1.4, T.cta + 2.0): pop(a)
    for kind, at in (ep.sfx(T) if hasattr(ep, "sfx") else []): kinds[kind](at)
    voice = np.zeros(n)
    for k, at in T.at.items():
        with wave.open(os.path.join(workdir, "vo", f"{k}.wav")) as w:
            v = np.frombuffer(w.readframes(w.getnframes()), np.int16) / 32768.0
        s = int(at * sr); e = min(n, s + len(v)); voice[s:e] += v[: e - s]
    win = int(0.15 * sr)
    mask = np.convolve((np.abs(voice) > 0.01).astype(float), np.ones(win) / win, mode="same")
    duck = (1 - 0.5 * np.clip(mask * 4, 0, 1))[:, None]
    music = bgm(n, seed=ep.NUM) * duck
    mix = music + ((out * 0.8) * (1 - 0.3 * np.clip(mask * 4, 0, 1)) + voice * 1.1)[:, None]
    mix *= np.clip((TOTAL - np.arange(n) / sr) / 0.6, 0, 1)[:, None]
    mix = np.tanh(mix * 1.2) * 0.88
    pcm = (mix * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())

# ---------------------------------------------------------------- frame + runner
def frame(ep, T, t):
    c = BG.copy()
    series_tag(c, ep)
    if t < T.body: hook_scene(c, t, ep)
    elif t < T.cta: ep.draw_body(c, t, T)
    else: cta_scene(c, t, ep, T)
    for s in (T.body, T.cta):
        if s <= t < s + 0.12:
            c.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(120 * (1 - (t - s) / 0.12)))))
    if TOTAL - t < 0.5:
        c.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * clamp(1 - (TOTAL - t) / 0.5)))))
    rra(c, (0, 0, W, 10), 0, (255, 255, 255, 40))
    ImageDraw.Draw(c).rectangle((0, 0, int(W * t / TOTAL), 10), fill=YEL + (255,))
    return c.convert("RGB")

def load_episode(path):
    spec = importlib.util.spec_from_file_location("episode", path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

def out_name(ep):
    return f"{ep.SERIES['key']}_{ep.NUM:02d}_{ep.SLUG}"

def main():
    path = sys.argv[1]; mode = sys.argv[2] if len(sys.argv) > 2 else "render"
    ep = load_episode(path)
    workdir = os.path.join(CACHE, out_name(ep)); os.makedirs(workdir, exist_ok=True); os.makedirs(OUT_DIR, exist_ok=True)
    durs = load_durs(ep, workdir)
    T = build_timeline(ep, durs)
    print("cues:", {k: round(v, 2) for k, v in T.at.items()}, "body", round(T.body, 2), "cta", round(T.cta, 2))
    if mode == "stills":
        ts = [1.8] + (ep.stills(T) if hasattr(ep, "stills") else [T.body + 0.8, (T.body + T.cta) / 2, T.cta - 0.3]) + [T.cta + 2.4]
        ims = [frame(ep, T, x).resize((360, 640)) for x in ts]
        sheet = Image.new("RGB", (360 * len(ims), 640))
        for k, im in enumerate(ims): sheet.paste(im, (k * 360, 0))
        p = os.path.join(OUT_DIR, out_name(ep) + "_sheet.png"); sheet.save(p); print("sheet:", p)
        return
    make_audio(os.path.join(workdir, "audio.wav"), ep, T, workdir)
    out = os.path.join(OUT_DIR, out_name(ep) + ".mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-i", os.path.join(workdir, "audio.wav"), "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for k in range(int(TOTAL * FPS)): p.stdin.write(frame(ep, T, k / FPS).tobytes())
    p.stdin.close(); p.wait()
    print("video:", out)

if __name__ == "__main__":
    # re-import so episodes and the runner share one module instance
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import shortlib
    shortlib.main()
