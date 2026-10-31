# iPhone隠し神機能⑤ カメラ起動中に音量ボタンでシャッター／長押しで動画（QuickTake・iPhone XS/XR以降）（v3：ショート＋60秒パート）
import math
from PIL import Image, ImageDraw, ImageEnhance
from shortlib import *

SERIES = dict(key="w20261102_second", title="iPhone隠し神機能", spoken="iPhone隠し、かみ機能",
              hook_split=("iPhone", "隠し神機能"), total=5)
NUM, SLUG = 5, "volume_shutter"
NEXT = "まとめは日曜の17:30"
SCREEN_CROP = (0, 40, 400, 836)            # keep the left edge (volume buttons) and the shutter
HOOK = "9割が知らない\n[カメラの神ワザ]"
HOOK_SPOKEN = "9割が知らない、カメラのかみワザ！"
TELOPS = [("b1", "[音量ボタン]を\n押すだけ"), ("b2", "[シャッター]が\n切れる！"),
          ("b3", "長押しで\n[動画撮影]"), ("b4", "指を離すと\n[録画ストップ]")]
ACTIONS = [("b1", "b2+0.9", "音量ボタンを押す"), ("b2+0.9", "b3", "画面タッチ不要"),
           ("b3", "b4", "音量ボタン長押し"), ("b4", "cta", "指を離す")]
BODY = [
    ("b1", "カメラを開いたら、音量ボタンを押すだけで、", 0.1),
    ("b2", "シャッターが切れます！画面に触らなくてOK。", 0.3),
    ("b3", "長押しすると、そのまま動画が撮れて、", 0.2),
    ("b4", "指を離すと、録画が止まります。", 0.0),
]
BODY_HOLD = 1.2
CTA = dict(lines=[("音量ボタンで", WHITE, 100), ("シャッター！", YEL, 120)], spoken="保存して試してね！",
           chip="長押し動画はiPhone XS/XR以降")

PART = dict(
    title="音量ボタンでシャッター",
    intro="写真を撮るとき、画面のシャッターボタンを押していませんか？",
    steps=[
        ("カメラを起動", "まず、カメラアプリを開きます。モードは、写真のままでOKです。", ("body", "b1+0.8")),
        ("音量ボタンを押す", "本体の横にある、音量ボタンを押します。上げるボタンでも、下げるボタンでも大丈夫です。", ("b1+0.6", "b2+0.4")),
        ("シャッターが切れる", "これでシャッターが切れます。画面をタップしないので、両手でしっかり持ったまま撮れます。", ("b2+0.2", "b3")),
        ("長押しで動画撮影", "音量ボタンを長押しすると、写真モードのまま、動画の撮影が始まります。クイックテイクという機能です。", ("b3", "b4")),
        ("離すと録画終了", "ボタンから指を離すと、録画が止まって、動画が保存されます。", ("b4", "cta")),
        ("対応機種", "長押しでの動画撮影は、iPhone XS、XR以降のモデルで使えます。それより前の機種でも、音量ボタンでのシャッターは使えます。", ("cta", "cta+1.0")),
    ],
    outro="カメラを開いたら、音量ボタンでシャッター。ぜひ試してみてください。",
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
VUP, VDN, ACT = (262, 336), (356, 430), (186, 226)   # y ranges of the side buttons (left edge)

def times(T):
    k = dict(p1=T.at["b2"] - 0.15, p2=T.at["b2"] + 1.5, hold=T.at["b3"] + 0.5, rel=T.at["b4"] + 0.6,
             done=T.at["b2"] + 0.4)
    k["rec"] = k["hold"] + 0.45                       # QuickTake starts after a short hold
    return k

def pressed_at(t, k):
    for a in (k["p1"], k["p2"]):
        if a - 0.05 <= t < a + 0.2: return True
    return k["hold"] <= t < k["rel"]

def screen(t, k):
    ps = Image.new("RGBA", (BW, BH), (0, 0, 0, 255))
    d = ImageDraw.Draw(ps)
    rr(ps, (BW / 2 - 64, 16, BW / 2 + 64, 52), 18, (20, 20, 22))          # Dynamic Island
    recording = k["rec"] <= t < k["rel"]
    # top controls: flash / chevron (or the red video timer) / Live Photos
    d.ellipse((22, 62, 62, 102), fill=(40, 40, 44))
    d.polygon([(45, 68), (33, 85), (42, 85), (38, 97), (52, 79), (43, 79)], fill=WHITE)
    if recording:
        s = int(t - k["rec"])
        rr(ps, (138, 66, 262, 98), 8, (255, 59, 48))
        txt(ps, (200, 82), f"00:00:{s:02d}", 20, WHITE, anchor="mm")
    else:
        d.line((188, 86, 200, 78, 212, 86), fill=WHITE, width=3)
    d.ellipse((338, 62, 378, 102), fill=(40, 40, 44))
    for r, w in ((15, 2), (9, 2), (4, 0)):
        if w: d.ellipse((358 - r, 82 - r, 358 + r, 82 + r), outline=WHITE, width=w)
        else: d.ellipse((358 - r, 82 - r, 358 + r, 82 + r), fill=WHITE)
    d.line((346, 70, 370, 94), fill=WHITE, width=2)
    # viewfinder (the dog wags while the video records)
    img = SCENE.copy()
    if t >= k["hold"]:
        dx = int(8 * math.sin((t - k["hold"]) * 9)) if recording else 0
        img = img.rotate(0, translate=(dx, 0), fillcolor=(90, 160, 80))
    ps.paste(img.convert("RGB"), (0, VY0))
    for a in (k["p1"], k["p2"]):
        if a <= t < a + 0.25: rra(ps, (0, VY0, BW, VY0 + VH), 0, (0, 0, 0, int(230 * (1 - (t - a) / 0.25))))
    if recording:
        rra(ps, (0, VY0, BW, VY0 + VH), 0, (0, 0, 0, 0))
    # zoom buttons
    rra(ps, (130, VY0 + VH - 64, 270, VY0 + VH - 14), 25, (0, 0, 0, 90))
    for x, s, on in ((168, ".5", False), (232, "1×", True)):
        rra(ps, (x - 21, VY0 + VH - 60, x + 21, VY0 + VH - 18), 21, (0, 0, 0, 140))
        txt(ps, (x, VY0 + VH - 39), s, 17 if on else 15, YEL if on else WHITE, anchor="mm")
    # modes
    for x, s, on in ((-6, "シネマティック", False), (112, "ビデオ", False), (200, "写真", True), (292, "ポートレート", False), (402, "パノラマ", False)):
        txt(ps, (x, 684), s, 19, YEL if on else (235, 235, 240), anchor="mm")
    # bottom row: thumbnail / shutter / flip
    shots = sum(1 for a in (k["p1"], k["p2"]) if t >= a + 0.1)
    if t >= k["rel"] + 0.1 or shots:
        th = SCENE.convert("RGB").resize((52, 69)).crop((0, 8, 52, 60))
        m = Image.new("L", th.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 51, 51), 8, fill=255)
        ps.paste(th, (36, 744), m)
        if t >= k["rel"] + 0.1:                      # video thumbnail: small play mark
            d.polygon([(54, 760), (54, 780), (72, 770)], fill=WHITE)
    else:
        rr(ps, (36, 744, 88, 796), 8, (70, 80, 90))
    d.ellipse((200 - 44, 770 - 44, 200 + 44, 770 + 44), outline=WHITE, width=5)
    if recording:
        d.ellipse((200 - 36, 770 - 36, 200 + 36, 770 + 36), fill=(255, 59, 48))
    else:
        r = 32 if any(a - 0.05 <= t < a + 0.15 for a in (k["p1"], k["p2"])) else 36
        d.ellipse((200 - r, 770 - r, 200 + r, 770 + r), fill=WHITE)
    d.ellipse((316, 746, 364, 794), fill=(40, 40, 44))
    d.arc((326, 756, 354, 784), 200, 340, fill=WHITE, width=3)
    d.arc((326, 756, 354, 784), 20, 160, fill=WHITE, width=3)
    # ---- side buttons drawn at the screen's left edge (the phone's left side) ----
    on = pressed_at(t, k)
    rr(ps, (-14, ACT[0], 16, ACT[1]), 10, (120, 120, 128))
    rr(ps, (-14, VDN[0], 16, VDN[1]), 10, (120, 120, 128))
    push = 8 if on else 0
    if on:
        fade(ps, 1.0, lambda l: ImageDraw.Draw(l).rounded_rectangle((-14, VUP[0] - 12, 40, VUP[1] + 12), 18, fill=(255, 214, 10, 120)))
    rr(ps, (-14, VUP[0], 16 + push, VUP[1]), 10, YEL if on else (120, 120, 128))
    txt(ps, (36 + push, (VUP[0] + VUP[1]) / 2), "+", 36, YEL if on else WHITE, anchor="mm", stroke=4)
    txt(ps, (36, (VDN[0] + VDN[1]) / 2), "−", 36, WHITE, anchor="mm", stroke=4)
    # label bubble pointing at the volume buttons
    by = (VUP[0] + VDN[1]) / 2
    def lab(l):
        dd = ImageDraw.Draw(l)
        dd.polygon([(56, by), (76, by - 16), (76, by + 16)], fill=(255, 214, 10, 255) if on else (20, 20, 24, 230))
        rr(l, (74, by - 38, 270, by + 38), 18, (255, 214, 10) if on else (20, 20, 24))
        txt(l, (172, by), "音量ボタン", 32, INK if on else YEL, anchor="mm")
    fade(ps, 1.0, lab)
    if k["hold"] + 0.15 <= t < k["rel"]:
        rr(ps, (84, by + 46, 260, by + 86), 12, (255, 59, 48))
        txt(ps, (172, by + 66), "長押し中…", 24, WHITE, anchor="mm")
    # finger on the button (translucent white circle, half off the edge)
    finger = None
    for a in (k["p1"], k["p2"]):
        if a - 0.3 <= t < a + 0.3: finger = a
    if k["hold"] - 0.3 <= t < k["rel"] + 0.25: finger = k["hold"]
    if finger is not None:
        cy = (VUP[0] + VUP[1]) / 2
        fx = -10 + (10 if on else 0)
        fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((fx - 40, cy - 40, fx + 40, cy + 40), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))
    return ps

def SCREEN(t, T): return screen(t, times(T))

def draw_body(c, t, T):
    k = times(T)
    big_phone(c, screen(t, k))
    if t < T.at["b2"]:
        telop(c, t, T.body, [("音量ボタンを押すだけ", WHITE)], y0=400, size=90)
    elif t < T.at["b3"]:
        telop(c, t, T.at["b2"], [("シャッターが切れる！", YEL)], y0=400, size=96)
    elif t < T.at["b4"]:
        telop(c, t, T.at["b3"], [("長押しで動画撮影", YEL)], y0=400, size=100)
    else:
        telop(c, t, T.at["b4"], [("離すと録画ストップ", YEL)], y0=400, size=96)
    badge(c, t, k["done"], "画面に触らずに撮れる", 1505, GREEN, size=44)

def draw_hook_art(ly, t):
    x0, y0 = 420, 1160
    rr(ly, (x0, y0, x0 + 240, y0 + 300), 36, (36, 36, 40), outline=(120, 120, 130), width=4)
    on = (t * 1.5) % 1 < 0.3
    rr(ly, (x0 - 14, y0 + 80, x0 + 4, y0 + 150), 6, YEL if on else (110, 110, 118))
    ImageDraw.Draw(ly).ellipse((x0 + 90, y0 + 220, x0 + 150, y0 + 280), fill=WHITE)

def sfx(T):
    k = times(T)
    return [("click", k["p1"]), ("click", k["p2"]), ("pop", k["rec"]), ("ding", k["done"]), ("pop", k["rel"])]

def stills(T):
    k = times(T)
    return [k["p1"] + 0.05, k["p2"] + 0.6, k["rec"] + 1.2, k["rel"] + 0.5, T.cta - 0.2]
