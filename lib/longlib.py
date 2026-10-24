"""5-minute landscape "完全版" videos (1920x1080) — the weekly long-form companion to the Shorts.

A long episode module (longs/<name>.py) provides:
    INTRO_TITLE = ("MacとiPhoneの", "連携技10選")      big title on the opening scene
    OUTRO_TITLE = "まとめ：MacとiPhoneの連携技10選"
    TIP_WORD    = "連携技"                             used on each tip's title card ("連携技 3")
    TIP_TARGET  = 27.5                                 minimum seconds per tip (pauses are stretched to reach it)
    INTRO, OUTRO  lists of narration lines
    TIPS  list of dict(key, name, req, title, steps=[(spoken, on_screen), ...], point=(spoken, on_screen))
    TIP_FN  dict key -> draw function(ctx); built-in drawings (clip, handoff, mirror, camera, scan, call, sms,
            hotspot, notif, code) can be reused by key. Phases: 0 title, 1..len(steps) steps, then point.
Run:  python3 lib/longlib.py longs/<name>.py [info|stills <t>...|render]
Spoken text: write 神 as かみ etc. (the TTS engine reads kanji its own way).
"""
import math, json, wave, sys, os, subprocess, asyncio, ssl, importlib.util
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shortlib as SL

ROOT = SL.ROOT
W, H, FPS = 1920, 1080, 30
F900, F500 = SL.font_path(900), SL.font_path(500)
YEL, WHITE, BLUE, RED, GREEN, GRAY = (255, 214, 10), (255, 255, 255), (10, 132, 255), (255, 69, 58), (48, 209, 88), (142, 142, 147)
INK = (28, 28, 32)

# ---------------- episode + timeline (filled by setup()) ----------------
INTRO, TIPS, OUTRO, CFG = [], [], [], {}
DURS, TEXT, SCENES, CUES = {}, {}, [], []
TOTAL, N, WORK = 0.0, 0, ""
EXTRA_TIP_FN = {}

def all_lines():
    out = [(f"intro{i}", s) for i, s in enumerate(INTRO)]
    for n, tip in enumerate(TIPS):
        out.append((f"t{n}_title", tip["title"]))
        for k, (v, _) in enumerate(tip["steps"]): out.append((f"t{n}_s{k}", v))
        out.append((f"t{n}_point", tip["point"][0]))
    out += [(f"outro{i}", s) for i, s in enumerate(OUTRO)]
    return out

def tts():
    import edge_tts, edge_tts.communicate as cm
    ca = "/root/.ccr/ca-bundle.crt"
    if os.path.exists(ca): cm._SSL_CTX = ssl.create_default_context(cafile=ca)
    vo = os.path.join(WORK, "vo"); os.makedirs(vo, exist_ok=True)
    lines = dict(all_lines())
    p = os.path.join(vo, "durs.json")
    if os.path.exists(p):
        d = json.load(open(p))
        if d.get("lines") == lines: return d["durs"]
    sem = asyncio.Semaphore(6)
    async def one(i, text):
        async with sem:
            for k in range(4):
                try:
                    return await edge_tts.Communicate(text, "ja-JP-NanamiNeural", rate=CFG.get("rate", "+10%")).save(f"{vo}/{i}.mp3")
                except Exception:
                    if k == 3: raise
                    await asyncio.sleep(2)
    async def main(): await asyncio.gather(*(one(i, t) for i, t in lines.items()))
    asyncio.run(main())
    durs = {}
    for i in lines:
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", f"{vo}/{i}.mp3", "-af",
            "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
            "-ar", "44100", "-ac", "1", f"{vo}/{i}.wav"], check=True, stdin=subprocess.DEVNULL)
        durs[i] = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{vo}/{i}.wav"],
                                       capture_output=True, text=True).stdout)
    json.dump({"lines": lines, "durs": durs}, open(p, "w"), ensure_ascii=False, indent=1)
    return durs

def build():
    t = 0.0
    st = t; t += 0.5
    for i in range(len(INTRO)):
        CUES.append((f"intro{i}", t)); t += DURS[f"intro{i}"] + 0.35
    t += 0.9
    SCENES.append(dict(kind="intro", idx=0, start=st, end=t, phases=[st]))
    target = CFG.get("tip_target", 27.5)
    for n in range(len(TIPS)):
        st = t
        ns = len(TIPS[n]["steps"])
        ids = [f"t{n}_title"] + [f"t{n}_s{k}" for k in range(ns)] + [f"t{n}_point"]
        base_gaps = [1.1] + [0.8] * ns
        need = 0.5 + sum(DURS[i] for i in ids) + sum(base_gaps) + 1.8
        extra = max(0.0, target - need) / len(base_gaps)
        t += 0.5
        ph = []
        for j, cid in enumerate(ids):
            ph.append(t); CUES.append((cid, t))
            t += DURS[cid] + (base_gaps[j] + extra if j < len(base_gaps) else 1.8)
        SCENES.append(dict(kind="tip", idx=n, start=st, end=t, phases=ph))
    st = t; t += 0.6
    ph = []
    for i in range(len(OUTRO)):
        ph.append(t); CUES.append((f"outro{i}", t)); t += DURS[f"outro{i}"] + 0.4
    t += 2.0
    SCENES.append(dict(kind="outro", idx=0, start=st, end=t, phases=ph))
    return t

def setup(mod):
    global TOTAL, N, WORK, DURS
    INTRO[:] = mod.INTRO; TIPS[:] = mod.TIPS; OUTRO[:] = mod.OUTRO
    CFG.update(intro_title=mod.INTRO_TITLE, outro_title=mod.OUTRO_TITLE, tip_word=getattr(mod, "TIP_WORD", "ワザ"),
               tip_target=getattr(mod, "TIP_TARGET", 27.5), rate=getattr(mod, "RATE", "+10%"))
    EXTRA_TIP_FN.update(getattr(mod, "TIP_FN", {}))
    WORK = os.path.join(SL.CACHE, "long_" + os.path.splitext(os.path.basename(mod.__file__))[0]); os.makedirs(WORK, exist_ok=True)
    DURS = tts()
    for i, s in all_lines(): TEXT[i] = s
    TOTAL = build(); N = int(TOTAL * FPS)


# ---------------- helpers ----------------
_fc = {}
def font(size, bold=True):
    k = (size, bold)
    if k not in _fc: _fc[k] = ImageFont.truetype(F900 if bold else F500, size)
    return _fc[k]

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_inout(x): x = clamp(x); return 3 * x * x - 2 * x ** 3
def back_out(x, s=1.7):
    x = clamp(x) - 1
    return x * x * ((s + 1) * x + s) + 1

def txt(img, xy, s, size, fill, bold=True, anchor="la", stroke=0, sf=(0, 0, 0)):
    ImageDraw.Draw(img).text(xy, s, font=font(size, bold), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=sf)

def rr(img, box, r, fill, outline=None, width=0):
    ImageDraw.Draw(img).rounded_rectangle([int(v) for v in box], int(r), fill=fill, outline=outline, width=width)

def fade(base, alpha, fn, *a):
    if alpha <= 0.01: return
    ly = Image.new("RGBA", base.size, (0, 0, 0, 0))
    fn(ly, *a)
    if alpha < 0.99:
        ly.putalpha(ly.getchannel("A").point(lambda v: int(v * alpha)))
    base.alpha_composite(ly)

def shadow(img, box, r, blur=14, off=8, a=110):
    x0, y0, x1, y1 = [int(v) for v in box]
    pad = blur * 3
    sh = Image.new("RGBA", (x1 - x0 + pad * 2, y1 - y0 + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad, pad + x1 - x0, pad + y1 - y0), r, fill=(0, 0, 0, a))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)), (x0 - pad, y0 - pad + off))

def window(img, box, title=None, bg=(250, 250, 252, 255), bar=(232, 232, 236, 255), tcol=(60, 60, 66)):
    x0, y0, x1, y1 = box
    shadow(img, box, 14)
    rr(img, box, 14, bg)
    rr(img, (x0, y0, x1, y0 + 34), 14, bar)
    ImageDraw.Draw(img).rectangle((x0, y0 + 20, x1, y0 + 34), fill=bar)
    d = ImageDraw.Draw(img)
    for i, c in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        d.ellipse((x0 + 14 + i * 22, y0 + 11, x0 + 27 + i * 22, y0 + 24), fill=c)
    if title: txt(img, ((x0 + x1) / 2, y0 + 17), title, 16, tcol, anchor="mm")

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
    """Wrap into the same number of lines as wrap(), but with balanced widths."""
    lines = wrap(s, f, maxw)
    if len(lines) < 2: return lines
    lo, hi = f.getlength(s) / len(lines), maxw
    for _ in range(14):
        mid = (lo + hi) / 2
        if len(wrap(s, f, mid)) > len(lines): lo = mid
        else: hi = mid
    return wrap(s, f, hi + 1)

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

def lock_icon(img, x, y, s, col):
    d = ImageDraw.Draw(img)
    d.arc((x + s * .2, y, x + s * .8, y + s * .7), 180, 360, fill=col, width=max(2, int(s * .1)))
    d.line((x + s * .2, y + s * .35, x + s * .2, y + s * .5), fill=col, width=max(2, int(s * .1)))
    d.line((x + s * .8, y + s * .35, x + s * .8, y + s * .5), fill=col, width=max(2, int(s * .1)))
    rr(img, (x, y + s * .45, x + s, y + s * 1.05), s * .12, col)

# ---------------- static art ----------------
def grad(w, h, c0, c1, horiz=False):
    a = np.linspace(0, 1, w if horiz else h)
    a = a[None, :, None] if horiz else a[:, None, None]
    g = np.array(c0)[None, None, :] * (1 - a) + np.array(c1)[None, None, :] * a
    g = g * np.ones((h, w, 1))
    return Image.fromarray(g.astype(np.uint8), "RGB").convert("RGBA")

def make_bg():
    g = np.array(grad(W, H, (10, 14, 34), (26, 14, 48)).convert("RGB")).astype(float)
    yy, xx = np.mgrid[0:H, 0:W]
    for cx, cy, r, col in [(300, 200, 700, (40, 80, 255)), (1700, 950, 800, (170, 50, 255))]:
        g += np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (r * r)))[..., None] * np.array(col) * 0.28
    return Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).convert("RGBA")
BG = make_bg()

MX0, MY0, MW, MH = 90, 220, 820, 500
PX0, PY0, PW, PH = 995, 340, 190, 420
MAC_WALL = grad(MW, MH, (64, 92, 200), (150, 70, 170))
PH_WALL = grad(PW, PH, (255, 140, 90), (120, 60, 200))

def make_devices():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow(im, (70, 200, 930, 775), 26, blur=24, off=18, a=150)
    rr(im, (70, 200, 930, 740), 26, (22, 22, 26), outline=(70, 70, 78), width=3)
    d = ImageDraw.Draw(im)
    d.polygon([(20, 740), (980, 740), (950, 776), (50, 776)], fill=(196, 198, 204))
    rr(im, (420, 740, 580, 750), 5, (160, 162, 168))
    shadow(im, (985, 330, 1195, 770), 36, blur=20, off=14, a=150)
    rr(im, (985, 330, 1195, 770), 36, (36, 36, 40), outline=(110, 110, 120), width=3)
    return im
DEVICES = make_devices()

def mac_base():
    ms = MAC_WALL.copy()
    ImageDraw.Draw(ms).rectangle((0, 0, MW, 22), fill=(255, 255, 255, 70))
    txt(ms, (MW - 14, 11), "10:24", 13, WHITE, anchor="rm")
    ImageDraw.Draw(ms).ellipse((14, 5, 26, 17), fill=WHITE)
    return ms

def phone_base():
    ps = PH_WALL.copy()
    txt(ps, (30, 18), "9:41", 13, WHITE, anchor="lm")
    return ps

def finish_phone(ps):
    m = Image.new("L", (PW, PH), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, PW - 1, PH - 1), 28, fill=255)
    rr(ps, (PW / 2 - 34, 8, PW / 2 + 34, 28), 10, (0, 0, 0))
    ps.putalpha(Image.fromarray(np.minimum(np.array(ps.getchannel("A")), np.array(m))))
    return ps

# ---------------- per-tip screen drawings ----------------
class Ctx:
    def __init__(self, T, phases):
        self.T, self.phases = T, phases
        self.ms, self.ps = mac_base(), phone_base()
        self.fly = []
    def el(self, k):
        return self.T - self.phases[k] if k < len(self.phases) else -1
    def e(self, k, dur=0.5, delay=0.0):
        el = self.el(k) - delay
        return ease_out(el / dur) if el > 0 else 0.0
    def on(self, k, delay=0.0): return self.el(k) >= delay
    def ph(self):
        p = 0
        for k, s in enumerate(self.phases):
            if self.T >= s: p = k
        return p

def fly_chip(ctx, k, start, dur, frm, to, label, col=BLUE):
    el = ctx.el(k) - start
    if 0 <= el <= dur:
        ctx.fly.append((frm, to, el / dur, label, col))

PHONE_C = (PX0 + PW / 2, PY0 + PH / 2)
def mpt(x, y): return (MX0 + x, MY0 + y)

def draw_page(img, box, big):
    x0, y0, x1, y1 = box
    rr(img, box, 10 if big else 0, WHITE)
    s = 1.0 if not big else 1.6
    rr(img, (x0 + 10, y0 + 8, x1 - 10, y0 + 8 + 22 * s), 11 * s, (236, 236, 240))
    txt(img, ((x0 + x1) / 2, y0 + 8 + 11 * s), "cafe-guide.jp", int(12 * s), (90, 90, 96), bold=False, anchor="mm")
    hy = y0 + 18 + 26 * s
    ih = int((y1 - y0) * 0.38)
    hero = grad(int(x1 - x0 - 20), ih, (214, 150, 90), (120, 70, 40))
    img.alpha_composite(hero, (int(x0 + 10), int(hy)))
    d = ImageDraw.Draw(img)
    d.ellipse((x0 + (x1 - x0) * .4, hy + ih * .3, x0 + (x1 - x0) * .6, hy + ih * .75), fill=(250, 245, 235))
    ty = hy + ih + 12
    txt(img, (x0 + 14, ty), "週末行きたい", int(18 * s), INK)
    txt(img, (x0 + 14, ty + 24 * s), "カフェ10選", int(18 * s), INK)
    for i in range(3):
        ly = ty + 58 * s + i * 16 * s
        if ly + 8 < y1 - 6:
            rr(img, (x0 + 14, ly, x1 - 14 - (40 if i == 2 else 0), ly + 7 * s), 3, (220, 220, 226))

def dock(img, extra=None, bounce=0.0, ring=0.0):
    icons = [(10, 132, 255), (52, 199, 89), (255, 159, 10), (255, 59, 48), (175, 82, 222)]
    n = len(icons) + (1 if extra else 0)
    s, g = 46, 10
    w = n * (s + g) + g + (16 if extra else 0)
    x0 = MW / 2 - w / 2
    rr(img, (x0, MH - 66, x0 + w, MH - 8), 18, (255, 255, 255, 90))
    x = x0 + g
    for c in icons:
        app_icon(img, x, MH - 60, s, c, "safari" if c == (10, 132, 255) else None); x += s + g
    if extra:
        x += 8
        ImageDraw.Draw(img).line((x - 9, MH - 58, x - 9, MH - 16), fill=(255, 255, 255, 140), width=2)
        by = -abs(math.sin(bounce * math.pi * 3)) * 22 * (1 - bounce) if bounce < 1 else 0
        app_icon(img, x, MH - 60 + by, s, (10, 132, 255), "safari")
        rr(img, (x + s - 18, MH - 66 + by, x + s + 2, MH - 40 + by), 5, (40, 40, 44))
        rr(img, (x + s - 15, MH - 63 + by, x + s - 1, MH - 43 + by), 3, (120, 180, 255))
        if ring > 0:
            r = 34 + 8 * math.sin(ring * 8)
            cx, cy = x + s / 2, MH - 37
            ImageDraw.Draw(img).ellipse((cx - r, cy - r, cx + r, cy + r), outline=YEL, width=4)
        return (x + s / 2, MH - 37)

def pills(img, items, y, a):
    def f(ly):
        x = 40
        for s, c in items:
            w = font(20).getlength(s) + 40
            rr(ly, (x, y, x + w, y + 40), 20, c)
            txt(ly, (x + w / 2, y + 20), s, 20, WHITE, anchor="mm")
            x += w + 14
    fade(img, a, f)

def tip_clip(c):
    ms, ps = c.ms, c.ps
    rr(ps, (0, 0, PW, PH), 0, (255, 253, 245))
    txt(ps, (30, 18), "9:41", 13, INK, anchor="lm")
    txt(ps, (16, 46), "メモ", 22, (200, 150, 0))
    lines = ["明日 10:00", "渋谷駅 ハチ公前"]
    if c.on(1):
        a = c.e(1, 0.3)
        rr(ps, (12, 90, 178, 146), 6, (10, 132, 255, int(90 * a)))
        fade(ps, a, lambda l: (rr(l, (40, 58, 120, 84), 10, (30, 30, 34)), txt(l, (80, 71), "コピー", 15, WHITE, anchor="mm")))
    for i, s in enumerate(lines): txt(ps, (18, 96 + i * 26), s, 18, INK, bold=False)
    if c.on(3, 0.9):
        a = c.e(3, 0.4, 0.9)
        fade(ps, a, lambda l: (txt(l, (18, 170), "apple.com/jp", 16, BLUE, bold=False)))
    window(ms, (110, 50, 710, 440), "メモ")
    if c.on(2, 0.8):
        a = c.e(2, 0.4, 0.8)
        fade(ms, a, lambda l: [txt(l, (140, 110 + i * 40), s, 28, INK) for i, s in enumerate(lines)])
        if c.ph() == 2:
            sc = back_out(clamp((c.el(2) - 0.8) / 0.35))
            fade(ms, min(1, sc), lambda l: (rr(l, (560, 330, 680, 410), 16, YEL), txt(l, (620, 370), "⌘V", 40, INK, anchor="mm")))
    if c.on(3):
        rr(ms, (136, 200, 370, 236), 6, (10, 132, 255, 70))
        txt(ms, (140, 202), "apple.com/jp", 24, BLUE, bold=False)
    fly_chip(c, 2, 0.0, 0.8, (PX0 + 95, PY0 + 110), mpt(260, 130), "明日 10:00…")
    fly_chip(c, 3, 0.1, 0.8, mpt(250, 220), (PX0 + 95, PY0 + 175), "apple.com/jp")
    if c.on(4): pills(ms, [("Wi-Fi", BLUE), ("Bluetooth", BLUE), ("Handoff", GREEN)], 450, c.e(4, 0.4))

def tip_handoff(c):
    ms, ps = c.ms, c.ps
    draw_page(ps, (0, 34, PW, PH), False)
    txt(ps, (30, 18), "9:41", 13, INK, anchor="lm")
    if c.on(1):
        pass
    extra = c.on(2)
    pos = dock(ms, extra, bounce=clamp(c.el(2) / 1.2) if extra else 0, ring=(c.T if c.ph() == 2 else 0))
    if c.on(3):
        e = c.e(3, 0.55)
        bx = (120, 36, 700, 410)
        sx, sy = pos
        box = (sx + (bx[0] - sx) * e, sy + (bx[1] - sy) * e, sx + (bx[2] - sx) * e, sy + (bx[3] - sy) * e)
        if e > 0.05:
            ly = Image.new("RGBA", (MW, MH), (0, 0, 0, 0))
            window(ly, tuple(int(v) for v in box), "Safari" if e > 0.6 else None)
            if e > 0.6:
                draw_page(ly, (box[0] + 6, box[1] + 36, box[2] - 6, box[3] - 6), True)
            ms.alpha_composite(ly)
        if c.ph() == 3 and c.el(3) < 0.6:
            cursor(ms, sx + 6, sy - 6, clamp(c.el(3) / 0.5))
    if c.on(4): pills(ms, [("メール", BLUE), ("メモ", (255, 159, 10)), ("マップ", GREEN)], 418, c.e(4, 0.4))

def home_grid(img, x0, y0, w, cols=4, rows=5):
    cs = [(10, 132, 255), (52, 199, 89), (255, 159, 10), (255, 59, 48), (175, 82, 222), (90, 200, 250), (255, 204, 0), (88, 86, 214)]
    s = w / cols * 0.68
    g = w / cols
    for r in range(rows):
        for q in range(cols):
            app_icon(img, x0 + q * g + (g - s) / 2, y0 + r * g * 1.05, s, cs[(r * cols + q * 3) % len(cs)])

def tip_mirror(c):
    ms, ps = c.ms, c.ps
    ps.alpha_composite(grad(PW, PH, (20, 30, 60), (60, 30, 80)))
    txt(ps, (PW / 2, 110), "9:41", 52, WHITE, anchor="mm")
    lock_icon(ps, PW / 2 - 9, 50, 18, WHITE)
    txt(ps, (PW / 2, 150), "10月20日 火曜日", 13, WHITE, bold=False, anchor="mm")
    if c.on(3):
        fade(ps, 1, lambda l: (rr(l, (30, 330, 160, 364), 17, (255, 255, 255, 50)), txt(l, (95, 347), "Macで使用中", 13, WHITE, anchor="mm")))
    dock(ms)
    if c.ph() == 1 or (c.on(1) and not c.on(2)):
        # highlight launch icon above the dock
        a = c.e(1, 0.4)
        def f(l):
            app_icon(l, MW / 2 - 40, 210, 80, (40, 40, 46), "phone")
            rr(l, (MW / 2 - 120, 306, MW / 2 + 120, 344), 19, (0, 0, 0, 150))
            txt(l, (MW / 2, 325), "iPhoneミラーリング", 18, WHITE, anchor="mm")
        fade(ms, a, f)
    if c.on(2):
        e = back_out(clamp(c.el(2) / 0.5), 1.2)
        w, h = int(170 * e), int(370 * e)
        if w > 10:
            ly = Image.new("RGBA", (180, 380), (0, 0, 0, 0))
            rr(ly, (0, 0, 179, 379), 28, (30, 30, 34))
            scr = grad(166, 366, (255, 140, 90), (120, 60, 200))
            home_grid(scr, 8, 50, 150)
            m = Image.new("L", (166, 366), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 165, 365), 24, fill=255)
            scr.putalpha(m)
            ly.alpha_composite(scr, (7, 7))
            ly = ly.resize((w, h), Image.BICUBIC)
            shadow(ms, (MW / 2 - w / 2, 230 - h / 2, MW / 2 + w / 2, 230 + h / 2), 24)
            ms.alpha_composite(ly, (int(MW / 2 - w / 2), int(230 - h / 2)))
    if c.on(3):
        el = c.el(3)
        tx, ty = MW / 2 - 50, 120
        p = ease_inout(el / 1.2)
        x, y = 640 + (tx - 640) * p, 420 + (ty - 420) * p
        cl = clamp((el - 1.2) / 0.4) if el > 1.2 else 0
        cursor(ms, x, y, cl if cl < 1 else 0)
        rr(ms, (560, 380, 780, 440), 12, (0, 0, 0, 140))
        txt(ms, (670, 410), "キーボードで操作", 18, WHITE, anchor="mm")

def person(img, box, blur_bg=False):
    x0, y0, x1, y1 = [int(v) for v in box]
    bg = grad(x1 - x0, y1 - y0, (120, 140, 160), (60, 70, 90))
    d = ImageDraw.Draw(bg)
    for i in range(5):
        d.rectangle((40 + i * 120, 40, 90 + i * 120, 180 - i * 12), fill=(150 + i * 10, 120, 90))
    if blur_bg: bg = bg.filter(ImageFilter.GaussianBlur(10))
    d = ImageDraw.Draw(bg)
    w, h = x1 - x0, y1 - y0
    d.ellipse((w / 2 - 140, h * .62, w / 2 + 140, h * 1.3), fill=(70, 90, 140))
    d.ellipse((w / 2 - 62, h * .22, w / 2 + 62, h * .62), fill=(240, 200, 170))
    d.chord((w / 2 - 66, h * .18, w / 2 + 66, h * .5), 180, 360, fill=(50, 35, 30))
    img.alpha_composite(bg, (x0, y0))

def tip_camera(c):
    ms, ps = c.ms, c.ps
    ps.alpha_composite(grad(PW, PH, (20, 20, 24), (40, 40, 46)))
    if c.on(1):
        a = c.e(1, 0.4)
        def f(l):
            rr(l, (PW / 2 - 30, 150, PW / 2 + 30, 270), 10, None, outline=WHITE, width=4)
            ang = (c.el(1) * 2) % 2
            d = ImageDraw.Draw(l)
            d.arc((PW / 2 - 70, 140, PW / 2 + 70, 280), 200, 200 + 90 * min(1, ang), fill=YEL, width=5)
            txt(l, (PW / 2, 310), "横向きに固定", 16, WHITE, anchor="mm")
        if not c.on(2): fade(ps, a, f)
    if c.on(2):
        app_icon(ps, PW / 2 - 36, 150, 72, GREEN, "cam")
        txt(ps, (PW / 2, 250), "連係カメラ", 18, WHITE, anchor="mm")
        txt(ps, (PW / 2, 276), "MacBookに接続中", 12, (180, 180, 186), bold=False, anchor="mm")
    window(ms, (60, 36, 760, 470), "FaceTime", bg=(30, 30, 34, 255), bar=(50, 50, 56, 255), tcol=(220, 220, 225))
    if c.on(2):
        a = c.e(2, 0.5)
        ly = Image.new("RGBA", (MW, MH), (0, 0, 0, 0))
        person(ly, (70, 72, 750, 460), blur_bg=c.on(4, 0.3))
        if a < 1: ly.putalpha(ly.getchannel("A").point(lambda v: int(v * a)))
        ms.alpha_composite(ly)
    else:
        txt(ms, (410, 260), "カメラを選択してください", 24, (160, 160, 168), anchor="mm")
    if c.on(3):
        a = c.e(3, 0.4)
        fade(ms, a, lambda l: (rr(l, (90, 90, 370, 130), 20, (0, 0, 0, 160)), txt(l, (230, 110), "カメラ：iPhoneのカメラ", 18, WHITE, anchor="mm"),
                                rr(l, (650, 90, 730, 130), 20, YEL), txt(l, (690, 110), "4K", 20, INK, anchor="mm")))
    if c.on(4):
        a = c.e(4, 0.4)
        fade(ms, a, lambda l: (rr(l, (90, 410, 290, 450), 20, (0, 0, 0, 160)), txt(l, (190, 430), "ポートレート ON", 18, WHITE, anchor="mm"),
                                ImageDraw.Draw(l).rectangle((300, 100, 520, 330), outline=YEL, width=3)))

def finder_win(ms, newfile=0.0):
    window(ms, (60, 36, 760, 470), "書類")
    rr(ms, (60, 70, 210, 470), 0, (238, 238, 242))
    for i, s in enumerate(["よく使う項目", "デスクトップ", "書類", "ダウンロード"]):
        txt(ms, (80, 90 + i * 34), s, 15, (90, 90, 96) if i else GRAY, bold=i == 2)
    items = ["請求書", "企画書", "議事録", "写真"]
    for i, s in enumerate(items):
        x, y = 250 + (i % 4) * 120, 110
        rr(ms, (x, y, x + 70, y + 54), 8, (100, 170, 245))
        rr(ms, (x, y - 8, x + 30, y + 6), 4, (100, 170, 245))
        txt(ms, (x + 35, y + 76), s, 14, INK, bold=False, anchor="mm")
    if newfile > 0:
        def f(l):
            x, y = 250, 230
            l2 = Image.new("RGBA", (MW, MH), (0, 0, 0, 0))
            ImageDraw.Draw(l2).polygon([(x + 10, y - 8), (x + 50, y - 8), (x + 64, y + 6), (x + 64, y + 64), (x + 10, y + 64)], fill=WHITE, outline=(200, 200, 205))
            rr(l2, (x + 18, y + 36, x + 56, y + 54), 4, RED); txt(l2, (x + 37, y + 45), "PDF", 11, WHITE, anchor="mm")
            rr(l2, (x - 18, y + 76, x + 92, y + 100), 8, BLUE); txt(l2, (x + 37, y + 88), "スキャン.pdf", 14, WHITE, anchor="mm")
            l.alpha_composite(l2)
        fade(ms, newfile, f)

def menu(img, x, y, items, hi, w=230):
    h = 16 + len(items) * 34
    shadow(img, (x, y, x + w, y + h), 10)
    rr(img, (x, y, x + w, y + h), 10, (246, 246, 248, 250), outline=(210, 210, 215))
    for i, s in enumerate(items):
        if i == hi: rr(img, (x + 6, y + 8 + i * 34, x + w - 6, y + 8 + i * 34 + 32), 6, BLUE)
        txt(img, (x + 18, y + 24 + i * 34), s, 16, WHITE if i == hi else INK, bold=i == hi, anchor="lm")

def tip_scan(c):
    ms, ps = c.ms, c.ps
    finder_win(ms, newfile=c.e(3, 0.4, 1.3) if c.on(3) else 0)
    if c.on(1) and not c.on(3):
        hi = 3 if c.el(1) > 0.8 else -1
        menu(ms, 400, 170, ["新規フォルダ", "情報を見る", "名前を変更", "iPhoneから読み込む  ›"], hi)
        if not c.on(2): cursor(ms, 420 + (c.el(1) > 0.8) * 60, 300 if c.el(1) > 0.8 else 200)
        if c.on(2):
            menu(ms, 630, 268, ["写真を撮る", "書類をスキャン", "スケッチを追加"], 1 if c.el(2) > 0.5 else -1, w=170)
            cursor(ms, 690, 334)
    if c.on(2):
        ps.alpha_composite(grad(PW, PH, (30, 30, 30), (55, 50, 45)))
        wob = math.sin(c.T * 3) * 3
        poly = [(40 + wob, 110), (155, 105 + wob), (165, 300), (28, 310 - wob)]
        ImageDraw.Draw(ps).polygon(poly, fill=(245, 245, 240))
        for i in range(5):
            ImageDraw.Draw(ps).line((52, 140 + i * 30, 145, 138 + i * 30), fill=(170, 170, 175), width=4)
        ImageDraw.Draw(ps).polygon(poly, outline=YEL, width=3)
        ImageDraw.Draw(ps).ellipse((PW / 2 - 26, 340, PW / 2 + 26, 392), outline=WHITE, width=4)
        ImageDraw.Draw(ps).ellipse((PW / 2 - 20, 346, PW / 2 + 20, 386), fill=WHITE)
        txt(ps, (PW / 2, 60), "書類をスキャン", 15, YEL, anchor="mm")
        if c.on(3):
            fl = clamp(1 - abs(c.el(3) - 0.35) / 0.15)
            if fl > 0: ps.alpha_composite(Image.new("RGBA", (PW, PH), (255, 255, 255, int(230 * fl))))
    fly_chip(c, 3, 0.5, 0.8, (PX0 + 95, PY0 + 200), mpt(285, 255), "PDF", RED)
    if c.on(4): pills(ms, [("写真を撮る", BLUE), ("スケッチを追加", (175, 82, 222))], 418, c.e(4, 0.4))

def settings_screen(ps, title, rows, toggles_on):
    ps.alpha_composite(Image.new("RGBA", (PW, PH), (242, 242, 247, 255)))
    txt(ps, (30, 18), "9:41", 13, INK, anchor="lm")
    txt(ps, (14, 50), title, 22, INK)
    y = 96
    for i, s in enumerate(rows):
        rr(ps, (8, y, PW - 8, y + 60), 10, WHITE)
        lines = wrap(s, font(13), 104)
        for j, ln in enumerate(lines[:2]): txt(ps, (18, y + 30 + (j - (len(lines[:2]) - 1) / 2) * 17), ln, 13, INK, anchor="lm")
        toggle(ps, PW - 64, y + 16, toggles_on[i])
        y += 70

def tip_call(c):
    ms, ps = c.ms, c.ps
    ph = c.ph()
    if ph in (1, 3, 4) and c.on(1):
        ps.alpha_composite(grad(PW, PH, (40, 50, 70), (20, 20, 30)))
        txt(ps, (PW / 2, 100), "田中さん", 26, WHITE, anchor="mm")
        txt(ps, (PW / 2, 130), "携帯電話" if ph == 1 else "Macで通話中", 14, (200, 200, 206), bold=False, anchor="mm")
        if ph == 1:
            d = ImageDraw.Draw(ps)
            d.ellipse((24, 320, 80, 376), fill=RED); d.ellipse((110, 320, 166, 376), fill=GREEN)
    if ph == 2:
        settings_screen(ps, "電話", ["他のデバイスでの通話", "MacBook Pro"], [c.el(2) > 0.8, c.el(2) > 1.5])
    if c.on(1) and not c.on(3):
        a = c.e(1, 0.4)
        pulse = (math.sin(c.T * 8) + 1) / 2
        def f(l):
            shadow(l, (430, 36, 800, 136), 16)
            rr(l, (430, 36, 800, 136), 16, (246, 246, 248, 245))
            app_icon(l, 446, 54, 44, GREEN, "phone")
            txt(l, (504, 58), "田中さん", 20, INK)
            txt(l, (504, 86), "iPhoneから着信", 14, GRAY, bold=False)
            rr(l, (640, 60, 712, 98), 10, RED); txt(l, (676, 79), "拒否", 16, WHITE, anchor="mm")
            rr(l, (720, 60, 790, 98), 10, GREEN); txt(l, (755, 79), "応答", 16, WHITE, anchor="mm")
            ImageDraw.Draw(l).rounded_rectangle((716, 56, 794, 102), 12, outline=(255, 214, 10, int(255 * pulse)), width=3)
        fade(ms, a, f)
    if c.on(3):
        a = c.e(3, 0.4)
        def f(l):
            window(l, (200, 50, 620, 450), "FaceTime")
            for i, (n, s) in enumerate([("田中さん", "携帯電話"), ("佐藤さん", "自宅"), ("歯医者", "03-xxxx")]):
                y = 100 + i * 70
                ImageDraw.Draw(l).ellipse((224, y, 270, y + 46), fill=(170, 170, 180))
                txt(l, (286, y + 6), n, 18, INK); txt(l, (286, y + 30), s, 13, GRAY, bold=False)
                app_icon(l, 550, y + 6, 36, GREEN, "phone")
            rr(l, (230, 380, 590, 430), 25, GREEN); txt(l, (410, 405), "発信中…", 20, WHITE, anchor="mm")
        fade(ms, a, f)

def bubble(img, x, y, s, col, right, tc=WHITE, size=18, maxw=300):
    f = font(size, False)
    lines = wrap(s, f, maxw)
    w = max(f.getlength(l) for l in lines) + 28
    h = len(lines) * (size + 8) + 16
    x0 = x - w if right else x
    rr(img, (x0, y, x0 + w, y + h), 18, col)
    for i, l in enumerate(lines): txt(img, (x0 + 14, y + 8 + i * (size + 8)), l, size, tc, bold=False)
    return h

def tip_sms(c):
    ms, ps = c.ms, c.ps
    window(ms, (40, 30, 780, 470), None)
    rr(ms, (40, 64, 250, 470), 0, (240, 240, 244))
    for i, (n, sel) in enumerate([("佐藤さん", True), ("母", False), ("山田さん", False), ("宅配業者", False)]):
        y = 76 + i * 64
        if sel: rr(ms, (48, y, 242, y + 58), 8, BLUE)
        ImageDraw.Draw(ms).ellipse((58, y + 9, 98, y + 49), fill=(180, 180, 190))
        txt(ms, (108, y + 18), n, 16, WHITE if sel else INK, anchor="lm")
        txt(ms, (108, y + 40), "SMS", 12, WHITE if sel else GRAY, bold=False, anchor="lm")
    txt(ms, (515, 82), "佐藤さん（SMS）", 16, INK, anchor="mm")
    y = 110
    msgs = [(1, 0.0, "今日何時に着く？", False), (1, 0.9, "18時ごろ！", True),
            (3, 0.2, "了解！駅に着いたら連絡するね", False), (3, 1.0, "OK！改札の前で待ってるね。今日は寒いから暖かくしてきてね", True)]
    for k, dl, s, right in msgs:
        if c.on(k, dl):
            a = c.e(k, 0.3, dl)
            hh = [0]
            def f(l, s=s, right=right, y=y):
                hh[0] = bubble(l, 760 if right else 270, y, s, GREEN if right else (229, 229, 234), right, tc=WHITE if right else INK)
            fade(ms, a, f)
            y += hh[0] + 12
    if c.on(3) and c.el(3) < 1.0:
        rr(ms, (270, 420, 760, 456), 18, WHITE, outline=(200, 200, 206))
        txt(ms, (290, 438), "了解！駅に着いたら" if c.el(3) < 0.3 else "OK！改札の前で待…", 15, INK, bold=False, anchor="lm")
    if c.on(2) and not c.on(3):
        settings_screen(ps, "メッセージ", ["テキストメッセージ転送", "MacBook Pro"], [True, c.el(2) > 1.2])
    else:
        ps.alpha_composite(Image.new("RGBA", (PW, PH), (255, 255, 255, 255)))
        txt(ps, (30, 18), "9:41", 13, INK, anchor="lm")
        txt(ps, (PW / 2, 52), "佐藤さん", 15, INK, anchor="mm")
        if c.on(1): bubble(ps, 10, 80, "今日何時に着く？", (229, 229, 234), False, tc=INK, size=12, maxw=130)
        if c.on(1, 0.9): bubble(ps, PW - 10, 118, "18時ごろ！", GREEN, True, size=12, maxw=130)
    if c.on(4): pills(ms, [("→ 10個目の技へ", (255, 159, 10))], 476 - 60, c.e(4, 0.4))

def wifi_icon(img, x, y, s, col):
    d = ImageDraw.Draw(img)
    for i, r in enumerate([s, s * .66, s * .33]):
        d.arc((x - r, y - r, x + r, y + r), 225, 315, fill=col, width=max(2, int(s * .14)))
    d.ellipse((x - s * .1, y - s * .1, x + s * .1, y + s * .1), fill=col)

def link_icon(img, x, y, s, col):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((x - s, y - s * .35, x, y + s * .35), int(s * .35), outline=col, width=3)
    d.rounded_rectangle((x - s * .2, y - s * .35, x + s * .8, y + s * .35), int(s * .35), outline=col, width=3)

def tip_hotspot(c):
    ms, ps = c.ms, c.ps
    connected = c.on(3, 0.8)
    if connected: link_icon(ms, MW - 90, 11, 12, WHITE)
    else: wifi_icon(ms, MW - 84, 17, 12, WHITE)
    window(ms, (40, 60, 420, 440), "Safari")
    if connected:
        txt(ms, (230, 250), "接続しました", 22, INK, anchor="mm")
        check(ms, 214, 190, 32, GREEN, 6)
    else:
        txt(ms, (230, 230), "インターネットに", 20, GRAY, anchor="mm")
        txt(ms, (230, 260), "接続されていません", 20, GRAY, anchor="mm")
    if c.on(1) and not c.on(3, 1.6):
        a = c.e(1, 0.3)
        def f(l):
            x0, y0, x1, y1 = 460, 30, 800, 400
            shadow(l, (x0, y0, x1, y1), 14)
            rr(l, (x0, y0, x1, y1), 14, (246, 246, 248, 250))
            txt(l, (x0 + 18, y0 + 26), "Wi-Fi", 20, INK, anchor="lm"); toggle(l, x1 - 64, y0 + 12, True)
            txt(l, (x0 + 18, y0 + 70), "パーソナルホットスポット", 14, GRAY, anchor="lm")
            if c.on(2):
                sel = c.on(3, 0.3)
                pulse = (math.sin(c.T * 7) + 1) / 2 if not sel else 0
                rr(l, (x0 + 8, y0 + 86, x1 - 8, y0 + 140), 8, BLUE if sel else (225, 230, 245))
                if not sel: ImageDraw.Draw(l).rounded_rectangle((x0 + 8, y0 + 86, x1 - 8, y0 + 140), 8, outline=(255, 190, 0, int(255 * pulse)), width=3)
                ImageDraw.Draw(l).ellipse((x0 + 18, y0 + 96, x0 + 52, y0 + 130), fill=WHITE if sel else BLUE)
                link_icon(l, x0 + 37, y0 + 113, 9, BLUE if sel else WHITE)
                txt(l, (x0 + 64, y0 + 113), "あなたのiPhone", 17, WHITE if sel else INK, anchor="lm")
                txt(l, (x1 - 20, y0 + 113), "5G", 14, WHITE if sel else GRAY, bold=False, anchor="rm")
            else:
                txt(l, (x0 + 18, y0 + 110), "検索中…", 15, GRAY, bold=False, anchor="lm")
            txt(l, (x0 + 18, y0 + 170), "その他のネットワーク", 14, GRAY, anchor="lm")
            txt(l, (x0 + 18, y0 + 205), "見つかりません", 15, (170, 170, 175), bold=False, anchor="lm")
            if c.on(2) and not c.on(3): cursor(l, x0 + 200, y0 + 120)
        fade(ms, a, f)
    if connected:
        rr(ps, (PW / 2 - 50, 6, PW / 2 + 50, 30), 12, GREEN)
        link_icon(ps, PW / 2 - 4, 18, 7, WHITE)
        a = c.e(3, 0.4, 0.8)
        fade(ps, a, lambda l: (rr(l, (10, 60, PW - 10, 130), 14, (255, 255, 255, 220)), txt(l, (PW / 2, 84), "インターネット共有", 14, INK, anchor="mm"),
                                txt(l, (PW / 2, 108), "1台接続中", 13, GREEN, anchor="mm")))

def notif_banner(l, y, col, kind, app, body, glow=0):
    x0, x1 = 450, 800
    shadow(l, (x0, y, x1, y + 78), 14)
    rr(l, (x0, y, x1, y + 78), 14, (246, 246, 248, 245))
    if glow: ImageDraw.Draw(l).rounded_rectangle((x0, y, x1, y + 78), 14, outline=YEL, width=4)
    app_icon(l, x0 + 14, y + 16, 46, col, kind)
    txt(l, (x0 + 72, y + 24), app, 16, INK, anchor="lm")
    txt(l, (x0 + 72, y + 52), body, 15, (80, 80, 86), bold=False, anchor="lm")
    rr(l, (x1 - 80, y + 12, x1 - 14, y + 36), 8, (220, 220, 226)); txt(l, (x1 - 47, y + 24), "iPhone", 12, INK, anchor="mm")

def tip_notif(c):
    ms, ps = c.ms, c.ps
    ps.alpha_composite(Image.new("RGBA", (PW, PH), (8, 8, 10, 255)))
    ImageDraw.Draw(ps).polygon([(0, 80), (PW, 0), (PW, 40), (0, 140)], fill=(255, 255, 255, 14))
    txt(ps, (PW / 2, PH / 2), "（画面オフ）", 14, (90, 90, 96), bold=False, anchor="mm")
    dock(ms)
    if c.on(1) and not c.on(2):
        a = c.e(1, 0.4)
        def f(l):
            shadow(l, (230, 120, 590, 300), 16)
            rr(l, (230, 120, 590, 300), 16, (246, 246, 248, 250))
            app_icon(l, 380, 140, 60, (40, 40, 46), "phone")
            txt(l, (410, 230), "iPhoneミラーリング", 20, INK, anchor="mm")
            rr(l, (330, 252, 490, 286), 17, GREEN); txt(l, (410, 269), "設定済み", 16, WHITE, anchor="mm")
        fade(ms, a, f)
    items = [(GREEN, "bubble", "メッセージ", "今日のランチどうする？"), (RED, None, "カレンダー", "15:00 打ち合わせ"), (BLUE, None, "天気", "明日は雨の予報です")]
    if c.on(2) and not c.on(3, 0.9):
        for i, (col, kind, app, body) in enumerate(items):
            if c.on(2, i * 0.7):
                e = c.e(2, 0.4, i * 0.7)
                fade(ms, e, lambda l, i=i, col=col, kind=kind, app=app, body=body, e=e:
                     notif_banner(l, 34 + i * 90 - (1 - e) * 30 + 0, col, kind, app, body, glow=c.on(3) and i == 0))
        if c.on(3): cursor(ms, 560, 70, clamp(c.el(3) / 0.5))
    if c.on(3, 0.9):
        e = back_out(clamp((c.el(3) - 0.9) / 0.5), 1.2)
        w, h = int(170 * e), int(370 * e)
        if w > 10:
            ly = Image.new("RGBA", (170, 370), (0, 0, 0, 0))
            rr(ly, (0, 0, 169, 369), 26, (30, 30, 34))
            rr(ly, (7, 7, 162, 362), 22, WHITE)
            rr(ly, (7, 7, 162, 60), 22, GREEN); ImageDraw.Draw(ly).rectangle((7, 40, 162, 60), fill=GREEN)
            txt(ly, (85, 40), "メッセージ", 14, WHITE, anchor="mm")
            bubble(ly, 16, 80, "今日のランチどうする？", (229, 229, 234), False, tc=INK, size=11, maxw=110)
            bubble(ly, 154, 140, "駅前のカフェは？", GREEN, True, size=11, maxw=110)
            ly = ly.resize((w, h), Image.BICUBIC)
            shadow(ms, (MW / 2 - w / 2, 240 - h / 2, MW / 2 + w / 2, 240 + h / 2), 24)
            ms.alpha_composite(ly, (int(MW / 2 - w / 2), int(240 - h / 2)))

def tip_code(c):
    ms, ps = c.ms, c.ps
    window(ms, (40, 30, 780, 470), None)
    rr(ms, (250, 40, 570, 62), 11, (236, 236, 240)); txt(ms, (410, 51), "mybank.example.jp", 13, (90, 90, 96), bold=False, anchor="mm")
    rr(ms, (230, 100, 590, 440), 16, (246, 247, 250), outline=(225, 225, 232))
    txt(ms, (410, 140), "ログイン", 26, INK, anchor="mm")
    txt(ms, (410, 178), "SMSに届いた認証コードを入力", 14, GRAY, bold=False, anchor="mm")
    filled = c.on(3, 0.5)
    rr(ms, (270, 210, 550, 260), 10, WHITE, outline=BLUE if c.on(1) else (200, 200, 206), width=3 if c.on(1) else 1)
    if filled:
        txt(ms, (410, 235), "4 8 2 9 1 3", 26, INK, anchor="mm")
    elif c.on(1) and int(c.T * 2) % 2 == 0:
        ImageDraw.Draw(ms).line((286, 222, 286, 248), fill=BLUE, width=2)
    done = c.on(3, 1.1)
    rr(ms, (270, 370, 550, 416), 10, GREEN if done else BLUE)
    if done:
        check(ms, 352, 383, 20, WHITE, 4); txt(ms, (420, 393), "ログイン完了", 18, WHITE, anchor="mm")
    else:
        txt(ms, (410, 393), "ログイン", 18, WHITE, anchor="mm")
    if c.on(2) and not filled:
        a = c.e(2, 0.3)
        def f(l):
            shadow(l, (270, 266, 550, 340), 10)
            rr(l, (270, 266, 550, 340), 10, WHITE, outline=(210, 210, 215))
            app_icon(l, 284, 280, 44, GREEN, "bubble")
            txt(l, (340, 290), "メッセージから", 13, GRAY, bold=False, anchor="lm")
            txt(l, (340, 318), "482913", 22, INK, anchor="lm")
            if c.on(3): ImageDraw.Draw(l).rounded_rectangle((270, 266, 550, 340), 10, outline=YEL, width=3)
        fade(ms, a, f)
        if c.on(3): cursor(ms, 450, 300, clamp(c.el(3) / 0.45))
    if c.on(1):
        e = c.e(1, 0.4)
        def f(l):
            y = 40 + (1 - e) * -40
            rr(l, (8, y, PW - 8, y + 86), 16, (246, 246, 248, 245))
            app_icon(l, 18, y + 12, 30, GREEN, "bubble")
            txt(l, (56, y + 26), "SMS", 13, INK, anchor="lm")
            txt(l, (18, y + 58), "認証コード：482913", 13, INK, anchor="lm")
        fade(ps, e, f)
    if c.on(4): pills(ms, [("テキストメッセージ転送 ON", GREEN)], 476 - 60, c.e(4, 0.4))

TIP_FN = dict(clip=tip_clip, handoff=tip_handoff, mirror=tip_mirror, camera=tip_camera, scan=tip_scan,
              call=tip_call, sms=tip_sms, hotspot=tip_hotspot, notif=tip_notif, code=tip_code)

# ---------------- composition ----------------
def subtitle(c, t):
    cur = None
    for cid, st in CUES:
        if st - 0.05 <= t <= st + DURS[cid] + 0.25: cur = cid
    if not cur: return
    f = font(42)
    lines = bwrap(TEXT[cur], f, 1700)
    y0 = 1000 - (len(lines) - 1) * 28
    ly = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for i, ln in enumerate(lines):
        txt(ly, (W / 2, y0 + i * 56), ln, 42, WHITE, anchor="mm", stroke=7, sf=(10, 10, 20))
    c.alpha_composite(ly)

def header(c, n, tip, e):
    ly = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ly)
    d.ellipse((60, 46, 160, 146), fill=YEL)
    txt(ly, (110, 96), f"{n + 1:02d}", 46, INK, anchor="mm")
    txt(ly, (186, 96), tip["name"], 62, WHITE, anchor="lm", stroke=3, sf=(10, 10, 20))
    req = tip["req"]
    fw = font(26).getlength(req) + 48
    rr(ly, (1860 - fw, 74, 1860, 118), 22, (255, 255, 255, 30), outline=(255, 255, 255, 140), width=2)
    txt(ly, (1860 - fw / 2, 96), req, 26, WHITE, anchor="mm")
    for i in range(len(TIPS)):
        x = 1860 - (len(TIPS) - 1 - i) * 26
        ImageDraw.Draw(ly).ellipse((x - 8, 140, x + 8, 156), fill=YEL if i == n else (255, 255, 255, 70 if i > n else 160))
    off = int((1 - e) * -60)
    if e < 1: ly.putalpha(ly.getchannel("A").point(lambda v: int(v * e)))
    c.alpha_composite(ly, (0, off))

def steps_panel(c, ctx, tip):
    x0, x1 = 1250, 1860
    ph = ctx.ph()
    for i, (_, label) in enumerate(tip["steps"]):
        k = i + 1
        if not ctx.on(k): continue
        e = ctx.e(k, 0.45)
        y = 210 + i * (150 if len(tip["steps"]) <= 3 else 118)
        def f(l, i=i, label=label, y=y, k=k):
            active = ph == k
            ch = 126 if len(tip["steps"]) <= 3 else 104
            rr(l, (x0, y, x1, y + ch), 20, (255, 255, 255, 46 if active else 22), outline=YEL if active else None, width=4 if active else 0)
            cy = y + ch / 2
            ImageDraw.Draw(l).ellipse((x0 + 22, cy - 28, x0 + 78, cy + 28), fill=BLUE if not active else YEL)
            txt(l, (x0 + 50, cy), str(i + 1), 30, WHITE if not active else INK, anchor="mm")
            lines = bwrap(label, font(34), x1 - x0 - 130)
            for j, ln in enumerate(lines):
                txt(l, (x0 + 100, cy + (j - (len(lines) - 1) / 2) * 44), ln, 34, WHITE, anchor="lm")
        ly = Image.new("RGBA", (W, H), (0, 0, 0, 0)); f(ly)
        if e < 1: ly.putalpha(ly.getchannel("A").point(lambda v: int(v * e)))
        c.alpha_composite(ly, (int((1 - e) * 80), 0))
    kp = len(tip["steps"]) + 1
    if ctx.on(kp):
        e = ctx.e(kp, 0.4)
        sc = back_out(e)
        ly = Image.new("RGBA", (x1 - x0, 170), (0, 0, 0, 0))
        rr(ly, (0, 0, x1 - x0 - 1, 169), 20, YEL)
        rr(ly, (20, -1, 150, 40), 10, INK)
        txt(ly, (85, 19), "POINT", 22, YEL, anchor="mm")
        lines = bwrap(tip["point"][1], font(36), x1 - x0 - 50)
        for j, ln in enumerate(lines):
            txt(ly, ((x1 - x0) / 2, 100 + (j - (len(lines) - 1) / 2) * 46), ln, 36, INK, anchor="mm")
        if sc < 0.999:
            ly = ly.resize((max(1, int(ly.width * sc)), max(1, int(ly.height * sc))), Image.BICUBIC)
        c.alpha_composite(ly, (int((x0 + x1) / 2 - ly.width / 2), int(700 + 85 - ly.height / 2)))

def draw_fly(c, fly):
    for (fx, fy), (tx, ty), p, label, col in fly:
        e = ease_inout(p)
        x = fx + (tx - fx) * e
        y = fy + (ty - fy) * e - math.sin(e * math.pi) * 160
        f = font(22)
        w = f.getlength(label) + 34
        ly = Image.new("RGBA", (int(w) + 40, 90), (0, 0, 0, 0))
        shadow(ly, (20, 20, 20 + w, 64), 22, blur=8, off=4)
        rr(ly, (20, 20, 20 + w, 64), 22, col)
        txt(ly, (20 + w / 2, 42), label, 22, WHITE, anchor="mm")
        s = 1 + 0.25 * math.sin(e * math.pi)
        ly = ly.resize((int(ly.width * s), int(ly.height * s)), Image.BICUBIC)
        c.alpha_composite(ly, (int(x - ly.width / 2), int(y - ly.height / 2)))

def title_card(c, ctx, n, tip):
    """Big centered number + name over the stage while the title line plays."""
    el = ctx.el(0)
    if el < 0 or ctx.on(1): return
    a = clamp(el / 0.25) * clamp((ctx.phases[1] - ctx.T) / 0.3)
    sc = back_out(clamp(el / 0.45))
    ly = Image.new("RGBA", (W, H), (0, 0, 0, int(150 * a)))
    c.alpha_composite(ly)
    t1 = Image.new("RGBA", (1400, 420), (0, 0, 0, 0))
    txt(t1, (700, 110), f"{CFG['tip_word']} {n + 1}", 90, YEL, anchor="mm", stroke=8, sf=(10, 10, 20))
    f = font(120)
    size = 120
    while f.getlength(tip["name"]) > 1350: size -= 6; f = font(size)
    txt(t1, (700, 280), tip["name"], size, WHITE, anchor="mm", stroke=10, sf=(10, 10, 20))
    t1 = t1.resize((max(1, int(1400 * sc)), max(1, int(420 * sc))), Image.BICUBIC)
    if a < 1: t1.putalpha(t1.getchannel("A").point(lambda v: int(v * a)))
    c.alpha_composite(t1, (int(W / 2 - t1.width / 2), int(470 - t1.height / 2)))

def scene_tip(c, sc, t):
    n = sc["idx"]; tip = TIPS[n]
    ctx = Ctx(t, sc["phases"])
    {**TIP_FN, **EXTRA_TIP_FN}[tip["key"]](ctx)
    c.alpha_composite(DEVICES)
    c.alpha_composite(ctx.ms, (MX0, MY0))
    c.alpha_composite(finish_phone(ctx.ps), (PX0, PY0))
    header(c, n, tip, ease_out((t - sc["start"]) / 0.5))
    steps_panel(c, ctx, tip)
    draw_fly(c, ctx.fly)
    title_card(c, ctx, n, tip)

def mini_devices(c, cx, cy, s, t):
    ly = Image.new("RGBA", (900, 520), (0, 0, 0, 0))
    rr(ly, (60, 20, 700, 420), 22, (22, 22, 26), outline=(90, 90, 100), width=3)
    ly.alpha_composite(grad(608, 368, (64, 92, 200), (150, 70, 170)), (76, 36))
    ImageDraw.Draw(ly).polygon([(20, 420), (740, 420), (715, 448), (45, 448)], fill=(196, 198, 204))
    rr(ly, (720, 140, 860, 440), 26, (36, 36, 40), outline=(110, 110, 120), width=3)
    ly.alpha_composite(grad(124, 284, (255, 140, 90), (120, 60, 200)).resize((124, 284)), (728, 148))
    # pulsing link between
    d = ImageDraw.Draw(ly)
    for i in range(3):
        p = ((t * 0.8 + i / 3) % 1)
        r = 30 + p * 120
        d.arc((700 - r, 290 - r, 700 + r, 290 + r), 200, 340, fill=(255, 214, 10, int(255 * (1 - p))), width=6)
    ly = ly.resize((int(900 * s), int(520 * s)), Image.BICUBIC)
    c.alpha_composite(ly, (int(cx - ly.width / 2), int(cy - ly.height / 2)))

def scene_intro(c, sc, t):
    el = t - sc["start"]
    mini_devices(c, W / 2, 690, 0.95, t)
    for i, (s, size, col, y, dl) in enumerate([(CFG["intro_title"][0], 110, WHITE, 170, 0.2), (CFG["intro_title"][1], 170, YEL, 330, 0.6)]):
        p = clamp((el - dl) / 0.45)
        if p <= 0: continue
        ly = Image.new("RGBA", (1600, 260), (0, 0, 0, 0))
        txt(ly, (800, 130), s, size, col, anchor="mm", stroke=12, sf=(10, 10, 20))
        k = back_out(p)
        ly = ly.resize((max(1, int(1600 * k)), max(1, int(260 * k))), Image.BICUBIC)
        c.alpha_composite(ly, (int(W / 2 - ly.width / 2), int(y - ly.height / 2)))
    if el > 1.4:
        a = ease_out((el - 1.4) / 0.4)
        def f(l):
            w = font(40).getlength("知ってるだけで毎日がラクになる") + 80
            rr(l, (W / 2 - w / 2, 830, W / 2 + w / 2, 900), 35, RED)
            txt(l, (W / 2, 865), "知ってるだけで毎日がラクになる", 40, WHITE, anchor="mm")
        fade(c, a, f)

def scene_outro(c, sc, t):
    el = t - sc["start"]
    p = ease_out(el / 0.5)
    txt(c, (W / 2, 110 - (1 - p) * 40), CFG["outro_title"], 64, WHITE, anchor="mm", stroke=6, sf=(10, 10, 20))
    for i, tip in enumerate(TIPS):
        q = clamp((el - 0.3 - i * 0.12) / 0.35)
        if q <= 0: continue
        cols = 2 if len(TIPS) > 5 else 1
        rows = math.ceil(len(TIPS) / cols)
        col, row = i // rows, i % rows
        x, y = (160 + col * 820) if cols == 2 else 570, 200 + row * 112
        def f(l, i=i, tip=tip, x=x, y=y):
            rr(l, (x, y, x + 780, y + 92), 18, (255, 255, 255, 28))
            ImageDraw.Draw(l).ellipse((x + 18, y + 16, x + 78, y + 76), fill=YEL)
            txt(l, (x + 48, y + 46), f"{i + 1:02d}", 28, INK, anchor="mm")
            txt(l, (x + 100, y + 46), tip["name"], 36, WHITE, anchor="lm")
        ly = Image.new("RGBA", (W, H), (0, 0, 0, 0)); f(ly)
        e = ease_out(q)
        if e < 1: ly.putalpha(ly.getchannel("A").point(lambda v: int(v * e)))
        c.alpha_composite(ly, (int((1 - e) * 60), 0))
    if len(sc["phases"]) > 2 and t >= sc["phases"][2]:
        e = back_out(clamp((t - sc["phases"][2]) / 0.4))
        ly = Image.new("RGBA", (900, 110), (0, 0, 0, 0))
        rr(ly, (0, 10, 400, 100), 45, (255, 255, 255, 235)); txt(ly, (200, 55), "高評価", 38, INK, anchor="mm")
        rr(ly, (440, 10, 900, 100), 45, RED); txt(ly, (670, 55), "チャンネル登録", 38, WHITE, anchor="mm")
        ly = ly.resize((max(1, int(900 * e)), max(1, int(110 * e))), Image.BICUBIC)
        c.alpha_composite(ly, (int(W / 2 - ly.width / 2), int(820 - ly.height / 2)))

def frame(i):
    t = i / FPS
    c = BG.copy()
    sc = next((s for s in SCENES if s["start"] <= t < s["end"]), SCENES[-1])
    {"intro": scene_intro, "tip": scene_tip, "outro": scene_outro}[sc["kind"]](c, sc, t)
    subtitle(c, t)
    # transitions: dip from black at scene start, flash
    k = t - sc["start"]
    if k < 0.25 and sc["start"] > 0:
        c.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * (1 - k / 0.25)))))
    if sc["end"] - t < 0.2 and sc is not SCENES[-1]:
        c.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * (1 - (sc["end"] - t) / 0.2)))))
    if sc is SCENES[-1] and TOTAL - t < 0.8:
        c.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * clamp(1 - (TOTAL - t) / 0.8)))))
    d = ImageDraw.Draw(c)
    d.rectangle((0, H - 8, W, H), fill=(255, 255, 255, 30))
    d.rectangle((0, H - 8, int(W * t / TOTAL), H), fill=YEL + (255,))
    return c.convert("RGB")

def frame_bytes(i): return frame(i).tobytes()

# ---------------- audio ----------------
def make_audio(path):
    sr = SL.SR
    n = int(sr * TOTAL)
    out = np.zeros(n)
    rng = np.random.default_rng(7)
    def add(sig, at, g=1.0):
        s = int(at * sr)
        if s < 0: sig, s = sig[-s:], 0
        e = min(n, s + len(sig))
        if s < n: out[s:e] += sig[: e - s] * g
    def env(ls, dec):
        x = np.arange(int(ls * sr)) / sr
        return x, np.exp(-x * dec)
    def whoosh(at):
        x, _ = env(0.4, 0)
        k = np.convolve(rng.standard_normal(len(x)), np.ones(14) / 14, mode="same")
        add(k * np.sin(np.pi * x / x[-1]) ** 2, at - 0.2, 0.35)
    def pop(at, f=880):
        x, e = env(0.12, 40)
        add(np.sin(2 * np.pi * (f + 500 * np.exp(-x * 60)) * x) * e, at, 0.22)
    for sc in SCENES:
        whoosh(sc["start"])
        if sc["kind"] == "tip":
            for k, ph in enumerate(sc["phases"]): pop(ph + 0.03, 700 + k * 120)
    voice = np.zeros(n)
    for cid, at in CUES:
        with wave.open(os.path.join(WORK, "vo", f"{cid}.wav")) as w:
            v = np.frombuffer(w.readframes(w.getnframes()), np.int16) / 32768.0
        s = int(at * sr); e = min(n, s + len(v)); voice[s:e] += v[: e - s]
    win = int(0.2 * sr)
    mask = np.clip(np.convolve((np.abs(voice) > 0.01).astype(float), np.ones(win) / win, mode="same") * 4, 0, 1)
    music = SL.bgm(n, seed=7) * 0.7 * (1 - 0.5 * mask)[:, None]          # long-form: a touch quieter than Shorts
    mix = music + (out * 0.8 + voice * 1.15)[:, None]
    mix *= np.clip((TOTAL - np.arange(n) / sr) / 1.0, 0, 1)[:, None]
    mix = np.tanh(mix * 1.1) * 0.88
    pcm = (mix * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())

def load(path):
    spec = importlib.util.spec_from_file_location("long_episode", path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

def main():
    mod = load(sys.argv[1]); mode = sys.argv[2] if len(sys.argv) > 2 else "render"
    setup(mod)
    name = os.path.splitext(os.path.basename(sys.argv[1]))[0]
    os.makedirs(SL.OUT_DIR, exist_ok=True)
    if mode == "info":
        print("total", round(TOTAL, 1))
        for s in SCENES: print(s["kind"], s["idx"], round(s["start"], 1), round(s["end"] - s["start"], 1))
    elif mode == "stills":
        ts = [float(x) for x in sys.argv[3:]]
        if not ts:   # default: intro + each tip at title and each phase, outro
            ts = [3.0]
            for s in SCENES:
                if s["kind"] == "tip": ts += [s["phases"][0] + 0.8] + [p + 2.0 for p in s["phases"][1:]]
            ts += [SCENES[-1]["end"] - 2.5]
        with Pool(4) as pool: ims = pool.map(frame, [int(x * FPS) for x in ts])
        cols = 6; rows = math.ceil(len(ims) / cols)
        sheet = Image.new("RGB", (480 * cols, 270 * rows))
        for k, im in enumerate(ims): sheet.paste(im.resize((480, 270)), ((k % cols) * 480, (k // cols) * 270))
        p = os.path.join(SL.OUT_DIR, name + "_sheet.png"); sheet.save(p); print("sheet:", p, "total", round(TOTAL, 1))
    else:
        make_audio(os.path.join(WORK, "audio.wav"))
        out = os.path.join(SL.OUT_DIR, name + ".mp4")
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-i", os.path.join(WORK, "audio.wav"), "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                              "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
        with Pool(4) as pool:
            for k, b in enumerate(pool.imap(frame_bytes, range(N), chunksize=10)):
                p.stdin.write(b)
                if k % 1800 == 0: print("frame", k, "/", N, flush=True)
        p.stdin.close(); p.wait()
        print("video:", out, "total", round(TOTAL, 1))

if __name__ == "__main__":
    main()
