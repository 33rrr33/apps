# Macの神設定② トラックパッドの「タップでクリック」（システム設定 → トラックパッド）
import math
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="s04_mac_settings", title="Macの神設定", spoken="Macの、かみ設定",
              hook_split=("Macの", "神設定"), total=3)
NUM, SLUG = 2, "tap_to_click"
NEXT = "Finderのパスバー"
BODY = [
    ("b1", "トラックパッドを、カチッと押し込まなくても、", 0.3),
    ("b2", "軽く触れるだけで、クリックできるようになります！", 0.3),
    ("b3", "設定のトラックパッドで、タップでクリックをオン。", 0.3),
    ("b4", "指が疲れにくく、音も静かになります。", 0.0),
]
BODY_HOLD = 0.9
CTA = dict(lines=[("トラックパッド →", WHITE, 90), ("タップでクリック", YEL, 116)], spoken="保存して試してね！",
           chip="押し込まずにトンッ")

TP = (330, 1215, 750, 1420)          # trackpad on the canvas

def times(T):
    return dict(press=T.at["b1"] + 0.8, tap1=T.at["b2"] + 0.5, tap2=T.at["b2"] + 1.3, tap3=T.at["b2"] + 1.5,
                settings=T.at["b3"], on=T.at["b3"] + 1.6, done=T.at["b2"] + 0.8, extra=T.at["b4"] + 0.5)

def finder(t, k):
    ms = mac_screen_base()
    box = (60, 50, MW - 60, MH - 30)
    window(ms, box, "書類")
    x0, y0, x1, y1 = box
    sel = t >= k["tap1"]
    names = ["企画書", "見積もり", "写真", "メモ", "請求書", "旅行"]
    for i, n in enumerate(names):
        x = x0 + 60 + (i % 3) * 230; y = y0 + 70 + (i // 3) * 180
        if i == 1 and sel: rr(ms, (x - 16, y - 12, x + 112, y + 132), 12, (200, 220, 255))
        rr(ms, (x, y, x + 96, y + 78), 10, (90, 170, 250)); rr(ms, (x, y - 8, x + 40, y + 6), 5, (90, 170, 250))
        if i == 1 and sel: rr(ms, (x - 4, y + 96, x + 100, y + 122), 8, BLUE)
        txt(ms, (x + 48, y + 109), n, 16, WHITE if (i == 1 and sel) else INK, anchor="mm")
    if t >= k["tap3"]:
        a = e_at(t, k["tap3"], 0.3)
        def opened(l):
            window(l, (220, 110, 760, 440), "見積もり")
            for j in range(6): rr(l, (250, 170 + j * 40, 730 - (120 if j % 2 else 0), 186 + j * 40), 6, (225, 225, 232))
        fade(ms, a, opened)
    cx, cy = x0 + 60 + 230 + 60, y0 + 70 + 50
    clk = 0
    for at in (k["tap1"], k["tap2"], k["tap3"]):
        if at <= t < at + 0.3: clk = (t - at) / 0.3
    if t < k["tap3"]: cursor(ms, cx, cy, clk)
    return ms

def settings(t, k):
    ms = mac_screen_base()
    box = (40, 40, MW - 40, MH - 20)
    window(ms, box, None)
    x0, y0, x1, y1 = box
    rr(ms, (x0, y0 + 34, x0 + 220, y1), 0, (238, 238, 242))
    for i, s in enumerate(["一般", "外観", "ディスプレイ", "キーボード", "マウス", "トラックパッド", "プリンタ"]):
        y = y0 + 50 + i * 44
        if i == 5: rr(ms, (x0 + 10, y, x0 + 210, y + 36), 8, BLUE)
        txt(ms, (x0 + 24, y + 18), s, 16, WHITE if i == 5 else INK, bold=i == 5, anchor="lm")
    txt(ms, (x0 + 250, y0 + 64), "トラックパッド", 22, INK, anchor="lm")
    rr(ms, (x0 + 250, y0 + 90, x1 - 20, y0 + 122), 8, (226, 226, 232))
    rr(ms, (x0 + 252, y0 + 92, x0 + 440, y0 + 120), 7, WHITE)
    for j, s in enumerate(["ポイントとクリック", "スクロール", "ジェスチャ"]):
        txt(ms, (x0 + 346 + j * 190, y0 + 106), s, 14, INK, bold=j == 0, anchor="mm")
    rows = ["軌跡の速さ", "クリック", "調べる＆データ検出", "副ボタンのクリック", "タップでクリック"]
    on = t >= k["on"]
    for i, s in enumerate(rows):
        y = y0 + 140 + i * 56
        hi = i == 4 and t >= k["settings"] + 0.8
        rr(ms, (x0 + 250, y, x1 - 20, y + 48), 8, (255, 236, 150) if hi else WHITE)
        txt(ms, (x0 + 268, y + 24), s, 16, INK, bold=i == 4, anchor="lm")
        if i == 0:
            rr(ms, (x1 - 230, y + 21, x1 - 40, y + 27), 3, (200, 200, 206)); ImageDraw.Draw(ms).ellipse((x1 - 150, y + 13, x1 - 128, y + 35), fill=WHITE, outline=(180, 180, 186))
        elif i == 1: txt(ms, (x1 - 40, y + 24), "中", 15, GRAY, bold=False, anchor="rm")
        elif i == 4:
            toggle(ms, x1 - 86, y + 10, on)
            if hi:
                pz = (math.sin(t * 8) + 1) / 2
                ImageDraw.Draw(ms).rounded_rectangle((x0 + 250, y, x1 - 20, y + 48), 8, outline=(255, 190, 0, int(255 * pz)), width=3)
            if k["settings"] + 1.0 <= t < k["on"] + 0.5:
                cursor(ms, x1 - 60, y + 26, clamp((t - k["on"]) / 0.3) if t >= k["on"] else 0)
        else: toggle(ms, x1 - 86, y + 10, True)
    return ms

def trackpad(c, t, k):
    press = 0
    if k["press"] <= t < k["press"] + 0.5: press = math.sin((t - k["press"]) / 0.5 * math.pi)
    x0, y0, x1, y1 = TP
    sh = int(6 * press)
    shadow(c, TP, 26, blur=18, off=10, a=140)
    rr(c, (x0 + sh, y0 + sh, x1 - sh, y1 - sh), 26, (int(206 - 30 * press), int(208 - 30 * press), int(214 - 30 * press)),
       outline=(150, 152, 160), width=3)
    ly = Image.new("RGBA", c.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ly)
    fx, fy = (x0 + x1) / 2 + 30, (y0 + y1) / 2
    show = k["press"] - 0.5 <= t < k["tap3"] + 0.6 or (k["settings"] > t >= k["tap1"] - 0.4)
    if t >= k["settings"]: show = False
    taps = [k["tap1"], k["tap2"], k["tap3"]]
    lift = 0
    for at in taps:
        if at - 0.2 <= t < at: lift = (at - t) / 0.2
    if show:
        r = 40 + 8 * press
        d.ellipse((fx - r, fy - r - 18 * lift, fx + r, fy + r - 18 * lift), fill=(255, 220, 190, 235), outline=(200, 150, 120, 255), width=3)
        for at in taps:
            if at <= t < at + 0.5:
                s = (t - at) / 0.5; rr_ = 40 + s * 90
                d.ellipse((fx - rr_, fy - rr_, fx + rr_, fy + rr_), outline=(255, 214, 10, int(255 * (1 - s))), width=6)
    c.alpha_composite(ly)
    if k["press"] <= t < k["press"] + 0.8:
        txt(c, (x1 + 20, y0 + 30), "カチッ", 44, (255, 120, 120), anchor="lm", stroke=6)
    for at in taps:
        if at <= t < at + 0.5:
            txt(c, (x1 + 20, y0 + 30), "トン", 44, YEL, anchor="lm", stroke=6)

def draw_body(c, t, T):
    k = times(T)
    stage(c, finder(t, k) if t < k["settings"] else settings(t, k), None)
    trackpad(c, t, k)
    if t < T.at["b2"]:
        telop(c, t, T.body, [("カチッと押し込まなくていい", WHITE)], size=84)
    elif t < T.at["b3"]:
        telop(c, t, T.at["b2"], [("軽く触れるだけでクリック！", YEL)], size=88)
    elif t < T.at["b4"]:
        telop(c, t, T.at["b3"], [("トラックパッド → タップでクリック", YEL)], size=80)
    else:
        telop(c, t, T.at["b4"], [("指がラク・音も静か", YEL)], size=100)
    if t < T.at["b4"]:
        badge(c, t, k["done"], "ダブルクリックもトントンでOK", 1505, GREEN, size=40)
    else:
        badge(c, t, k["extra"], "長時間の作業でも疲れにくい", 1505, PURPLE, size=40)

def draw_hook_art(ly, t):
    x0, y0, x1, y1 = 340, 1190, 740, 1400
    rr(ly, (x0, y0, x1, y1), 26, (206, 208, 214), outline=(150, 152, 160), width=3)
    d = ImageDraw.Draw(ly)
    q = (t * 1.1) % 1
    fx, fy = 560, 1295
    lift = 20 * abs(math.sin(q * math.pi))
    d.ellipse((fx - 38, fy - 38 - lift, fx + 38, fy + 38 - lift), fill=(255, 220, 190, 235), outline=(200, 150, 120, 255), width=3)
    if q < 0.5:
        r = 40 + q * 160
        d.ellipse((fx - r, fy - r, fx + r, fy + r), outline=(255, 214, 10, int(255 * (1 - q * 2))), width=6)

def sfx(T):
    k = times(T)
    return [("click", k["press"]), ("pop", k["tap1"]), ("pop", k["tap2"]), ("pop", k["tap3"]), ("whoosh", k["settings"]),
            ("click", k["on"]), ("ding", k["on"] + 0.2), ("pop", k["extra"])]

def stills(T):
    k = times(T)
    return [k["press"] + 0.2, k["tap1"] + 0.2, k["tap3"] + 0.5, k["on"] + 0.3, k["extra"] + 0.5]
