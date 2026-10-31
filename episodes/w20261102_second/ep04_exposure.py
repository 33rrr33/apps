# iPhone隠し神機能④ カメラで被写体をタップ→太陽マークを上下にスライドして明るさ（露出）を調整（v3：ショート＋60秒パート）
import math
from PIL import Image, ImageDraw, ImageEnhance
from shortlib import *

SERIES = dict(key="w20261102_second", title="iPhone隠し神機能", spoken="iPhone隠し、かみ機能",
              hook_split=("iPhone", "隠し神機能"), total=5)
NUM, SLUG = 4, "exposure"
NEXT = "音量ボタンでシャッター"
SCREEN_CROP = (0, 96, 400, 836)            # viewfinder + modes + shutter (skip the empty top/bottom)
HOOK = "写真が暗い人\n{全員損}してます"
HOOK_SPOKEN = "写真が暗い人、全員損してます！"
TELOPS = [("b1", "被写体を\n[タップ]"), ("b2", "太陽マークを\n[上にスライド]"),
          ("b3", "[明るさ]が\nその場で変わる！"), ("b4", "下にスライドで\n[暗め]にもできる")]
ACTIONS = [("b1", "b2", "被写体をタップ"), ("b2", "b3", "太陽マークを上下"),
           ("b3", "b4", "明るくなった！"), ("b4", "cta", "下にスライド")]
BODY = [
    ("b1", "カメラで、被写体をタップすると、", 0.2),
    ("b2", "横に太陽マークが出るので、上にスライド。", 0.3),
    ("b3", "明るさを、その場で調整できます！", 0.3),
    ("b4", "下にスライドすれば、暗めにもできます。", 0.0),
]
BODY_HOLD = 1.4
CTA = dict(lines=[("被写体をタップして", WHITE, 96), ("太陽マークを上下！", YEL, 116)], spoken="保存して試してね！",
           chip="暗い写真もその場で明るく")

PART = dict(
    title="カメラの明るさをスライドで調整",
    intro="逆光で、写真が暗くなってしまったこと、ありませんか？",
    steps=[
        ("カメラを起動", "まず、カメラアプリを開きます。逆光だと、このように被写体が暗く写ってしまいます。", ("body", "b1+0.3")),
        ("被写体をタップ", "明るくしたい被写体を、画面でタップします。黄色い四角が出て、そこにピントが合います。", ("b1+0.3", "b2+0.9")),
        ("太陽マークを上にスライド", "四角の横に、太陽のマークが出ます。画面を指で上にスライドすると、太陽が上に動いて、明るくなります。", ("b2+0.9", "b3+0.6")),
        ("下にスライドで暗く", "反対に、下にスライドすると暗くなります。明るすぎる景色を、落ち着いた雰囲気にしたい時に便利です。", ("b4+0.2", "b4+1.8")),
        ("シャッターで撮影", "ちょうどいい明るさになったら、シャッターを押して撮影します。", ("b4+1.6", "cta")),
        ("長押しで固定", "さらに、被写体を長押しすると、AE/AFロックと表示されて、ピントと明るさを固定できます。", ("cta+0.2", "cta+2.6")),
    ],
    outro="被写体をタップして、太陽マークを上下にスライド。暗い写真とは、もうお別れです。",
)

# ---- big centered iPhone (same layout as the iPhone series) ----
BW, BH = 400, 860
BX0, BY0 = 340, 560

def big_phone(c, ps):
    ly = Image.new("RGBA", (BW + 40, BH + 40), (0, 0, 0, 0))
    rr(ly, (0, 0, BW + 39, BH + 39), 64, (36, 36, 40), outline=(120, 120, 130), width=5)
    m = Image.new("L", (BW, BH), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, BW - 1, BH - 1), 52, fill=255)
    rr(ps, (BW / 2 - 64, 16, BW / 2 + 64, 52), 18, (0, 0, 0))
    ps.putalpha(Image.fromarray(np.minimum(np.array(ps.getchannel("A")), np.array(m))))
    ly.alpha_composite(ps, (20, 20))
    shadow(c, (BX0 - 20, BY0 - 20, BX0 + BW + 20, BY0 + BH + 20), 64, blur=26, off=18, a=160)
    c.alpha_composite(ly, (BX0 - 20, BY0 - 20))

# ---- the scene in the viewfinder: a dog in a park (from s03 ep03), backlit ----
VY0, VH = 110, 533                          # 3:4 viewfinder
PW_, PH_ = 400, 520

def make_scene():
    im = Image.new("RGBA", (PW_, PH_), (0, 0, 0, 255))
    im.alpha_composite(grad(PW_, 330, (120, 190, 250), (200, 230, 255)), (0, 0))
    im.alpha_composite(grad(PW_, PH_ - 300, (110, 190, 90), (60, 140, 60)), (0, 300))
    d = ImageDraw.Draw(im)
    d.rectangle((300, 150, 322, 320), fill=(110, 80, 50))
    d.ellipse((240, 60, 390, 210), fill=(70, 150, 70))
    d.ellipse((20, 40, 120, 90), fill=(255, 255, 255, 230))
    d.ellipse((70, 30, 160, 85), fill=(255, 255, 255, 230))
    for x in range(0, PW_, 26):
        d.line((x, 330, x + 6, 312), fill=(80, 160, 70), width=3)
    fur, dark = (232, 178, 110), (170, 110, 60)
    d.ellipse((110, 300, 300, 450), fill=fur)
    d.rounded_rectangle((130, 400, 165, 490), 16, fill=fur)
    d.rounded_rectangle((245, 400, 280, 490), 16, fill=fur)
    d.ellipse((285, 300, 345, 340), fill=fur)
    d.ellipse((100, 190, 250, 330), fill=fur)
    d.polygon([(105, 220), (120, 150), (160, 205)], fill=dark)
    d.polygon([(245, 220), (230, 150), (190, 205)], fill=dark)
    d.ellipse((140, 245, 160, 265), fill=INK); d.ellipse((190, 245, 210, 265), fill=INK)
    d.ellipse((152, 275, 198, 320), fill=(250, 235, 215))
    d.ellipse((165, 280, 185, 294), fill=INK)
    return im.resize((BW, VH), Image.LANCZOS)

SCENE = make_scene()
FX, FY = 175, VY0 + 262                     # the dog's face (tap point)
SUN_X = FX + 82

def times(T):
    k = dict(tap=T.at["b1"] + 0.6, up0=T.at["b2"] + 1.0, up1=T.at["b2"] + 2.1,
             dn0=T.at["b4"] + 0.5, dn1=T.at["b4"] + 1.3, shot=T.cta - 0.45,
             lp=T.cta + 0.6, lock=T.cta + 1.4, done=T.at["b3"] + 0.3)
    return k

def exposure(t, k):
    """Exposure bias: 0 = the dark auto exposure, 1 = brighter, then down to 0.55."""
    e = 0.0
    if t >= k["up0"]: e = ease_inout((t - k["up0"]) / (k["up1"] - k["up0"]))
    if t >= k["dn0"]: e = 1 - 0.45 * ease_inout((t - k["dn0"]) / (k["dn1"] - k["dn0"]))
    return e

def sun(d, x, y, r=9, col=(255, 214, 10)):
    d.ellipse((x - r, y - r, x + r, y + r), fill=col)
    for i in range(8):
        a = i * math.pi / 4
        d.line((x + (r + 4) * math.cos(a), y + (r + 4) * math.sin(a), x + (r + 9) * math.cos(a), y + (r + 9) * math.sin(a)), fill=col, width=3)

def screen(t, k):
    ps = Image.new("RGBA", (BW, BH), (0, 0, 0, 255))
    d = ImageDraw.Draw(ps)
    rr(ps, (BW / 2 - 64, 16, BW / 2 + 64, 52), 18, (20, 20, 22))          # Dynamic Island
    # top controls: flash / chevron / Live Photos
    d.ellipse((22, 62, 62, 102), fill=(40, 40, 44))
    d.polygon([(45, 68), (33, 85), (42, 85), (38, 97), (52, 79), (43, 79)], fill=WHITE)
    d.line((188, 86, 200, 78, 212, 86), fill=WHITE, width=3)
    d.ellipse((338, 62, 378, 102), fill=(40, 40, 44))
    for r, w in ((15, 2), (9, 2), (4, 0)):
        if w: d.ellipse((358 - r, 82 - r, 358 + r, 82 + r), outline=WHITE, width=w)
        else: d.ellipse((358 - r, 82 - r, 358 + r, 82 + r), fill=WHITE)
    d.line((346, 70, 370, 94), fill=WHITE, width=2)
    # viewfinder
    e = exposure(t, k)
    lift = 0.36 + 0.7 * e
    img = ImageEnhance.Brightness(SCENE.convert("RGB")).enhance(lift)
    if e > 0.55: img = ImageEnhance.Contrast(img).enhance(1 - 0.12 * (e - 0.55))
    ps.paste(img, (0, VY0))
    flash_a = 0.0
    if k["shot"] <= t < k["shot"] + 0.25: flash_a = 1 - (t - k["shot"]) / 0.25
    if flash_a > 0: rra(ps, (0, VY0, BW, VY0 + VH), 0, (0, 0, 0, int(230 * flash_a)))
    # zoom buttons
    rra(ps, (130, VY0 + VH - 64, 270, VY0 + VH - 14), 25, (0, 0, 0, 90))
    for x, s, on in ((168, ".5", False), (232, "1×", True)):
        rra(ps, (x - 21, VY0 + VH - 60, x + 21, VY0 + VH - 18), 21, (0, 0, 0, 140))
        txt(ps, (x, VY0 + VH - 39), s, 17 if on else 15, YEL if on else WHITE, anchor="mm")
    # focus square + sun slider
    if t >= k["tap"]:
        p = e_at(t, k["tap"], 0.25)
        h = 58 + 34 * (1 - p)
        d.rectangle((FX - h, FY - h, FX + h, FY + h), outline=(255, 214, 10), width=3)
        for sx, sy in ((FX, FY - h), (FX, FY + h - 6)):
            d.line((sx, sy, sx, sy + 6), fill=(255, 214, 10), width=3)
        for sx, sy in ((FX - h, FY), (FX + h - 6, FY)):
            d.line((sx, sy, sx + 6, sy), fill=(255, 214, 10), width=3)
        sy = FY - 95 * e
        if t >= k["up0"] - 0.2:                    # the vertical track appears while dragging
            d.line((SUN_X, FY - 120, SUN_X, sy - 20), fill=(255, 214, 10), width=2)
            d.line((SUN_X, sy + 20, SUN_X, FY + 120), fill=(255, 214, 10), width=2)
        sun(d, SUN_X, sy)
    # AE/AF lock (long press; shown in the 60s part)
    if t >= k["lock"]:
        a = e_at(t, k["lock"], 0.2)
        def lab(l):
            rr(l, (BW / 2 - 78, VY0 + 14, BW / 2 + 78, VY0 + 48), 8, (255, 214, 10))
            txt(l, (BW / 2, VY0 + 31), "AE/AFロック", 19, INK, anchor="mm")
        fade(ps, a, lab)
    # modes
    for x, s, on in ((-6, "シネマティック", False), (112, "ビデオ", False), (200, "写真", True), (292, "ポートレート", False), (402, "パノラマ", False)):
        txt(ps, (x, 684), s, 19, YEL if on else (235, 235, 240), anchor="mm")
    # bottom row: thumbnail / shutter / flip
    shot = t >= k["shot"] + 0.1
    if shot:
        th = ImageEnhance.Brightness(SCENE.convert("RGB")).enhance(0.36 + 0.7 * 0.55).resize((52, 69)).crop((0, 8, 52, 60))
        m = Image.new("L", th.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 51, 51), 8, fill=255)
        ps.paste(th, (36, 744), m)
    else:
        rr(ps, (36, 744, 88, 796), 8, (70, 80, 90))
    pressed = k["shot"] - 0.05 <= t < k["shot"] + 0.15
    d.ellipse((200 - 44, 770 - 44, 200 + 44, 770 + 44), outline=WHITE, width=5)
    r = 32 if pressed else 36
    d.ellipse((200 - r, 770 - r, 200 + r, 770 + r), fill=WHITE)
    d.ellipse((316, 746, 364, 794), fill=(40, 40, 44))
    d.arc((326, 756, 354, 784), 200, 340, fill=WHITE, width=3)
    d.arc((326, 756, 354, 784), 20, 160, fill=WHITE, width=3)
    # finger
    fp = None
    if k["tap"] - 0.25 <= t < k["tap"] + 0.25: fp = (FX, FY)
    for a0, a1, y0, y1 in ((k["up0"], k["up1"], FY + 60, FY - 60), (k["dn0"], k["dn1"], FY - 50, FY + 10)):
        if a0 - 0.25 <= t < a1 + 0.2:
            q = ease_inout((t - a0) / (a1 - a0))
            fp = (SUN_X + 45, y0 + (y1 - y0) * q)
            if t >= a0:
                ax = SUN_X + 45
                d.line((ax, y0, ax, fp[1]), fill=(255, 214, 10), width=6)
    if k["shot"] - 0.2 <= t < k["shot"] + 0.25: fp = (200, 770)
    if k["lp"] - 0.2 <= t < k["lock"] + 0.6:
        fp = (FX, FY)
        if t >= k["lp"]:
            ring = clamp((t - k["lp"]) / (k["lock"] - k["lp"]))
            d.arc((FX - 44, FY - 44, FX + 44, FY + 44), -90, -90 + 360 * ring, fill=WHITE, width=6)
    if fp:
        fx, fy = fp
        fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((fx - 30, fy - 30, fx + 30, fy + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))
    return ps

def SCREEN(t, T): return screen(t, times(T))

def draw_body(c, t, T):
    k = times(T)
    big_phone(c, screen(t, k))
    if t < T.at["b2"]:
        telop(c, t, T.body, [("被写体をタップ", WHITE)], y0=400, size=100)
    elif t < T.at["b3"]:
        telop(c, t, T.at["b2"], [("太陽マークを上にスライド", YEL)], y0=400, size=80)
    elif t < T.at["b4"]:
        telop(c, t, T.at["b3"], [("明るさがその場で変わる", YEL)], y0=400, size=86)
    else:
        telop(c, t, T.at["b4"], [("下にスライドで暗めに", YEL)], y0=400, size=92)
    badge(c, t, k["done"], "アプリ不要・標準カメラでOK", 1505, GREEN, size=42)

def draw_hook_art(ly, t):
    x0, y0 = 380, 1160
    q = (t * 0.7) % 1
    s = ImageEnhance.Brightness(SCENE.convert("RGB")).enhance(0.45 + 0.6 * ease_inout(q)).resize((240, 320))
    ly.paste(s, (x0 + 40, y0 - 40))
    d = ImageDraw.Draw(ly)
    sun(d, x0 + 300, y0 + 220 - 120 * ease_inout(q), r=14)

def sfx(T):
    k = times(T)
    return [("click", k["tap"]), ("whoosh", k["up0"] + 0.2), ("ding", k["up1"]), ("whoosh", k["dn0"] + 0.2),
            ("click", k["shot"])]

def stills(T):
    k = times(T)
    return [k["tap"] + 0.3, (k["up0"] + k["up1"]) / 2, k["up1"] + 0.4, (k["dn0"] + k["dn1"]) / 2, k["shot"] + 0.3]
