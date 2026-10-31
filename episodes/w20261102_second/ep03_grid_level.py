# iPhone隠し神機能③ 設定→カメラ→「グリッド」「水平」をオン。カメラにグリッドと水平器（真下に向けると十字）が出る（v3）
import math
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="w20261102_second", title="iPhone隠し神機能", spoken="iPhone隠し、かみ機能",
              hook_split=("iPhone", "隠し神機能"), total=5)
NUM, SLUG = 3, "grid_level"
NEXT = "明るさをスライドで調整"
SCREEN_CROP = (0, 140, 400, 700)          # settings rows / the viewfinder
HOOK = "写真が傾く人\n{この設定オフです}"
HOOK_SPOKEN = "写真が傾く人、この設定オフです！"
TELOPS = [("b1", "設定アプリの\n[カメラ]を開く"), ("b2", "[グリッド]と\n[水平]をオン"),
          ("b3", "線が出て\n[傾きが一発でわかる]"), ("b4", "真下に向けると\n[十字で水平チェック]")]
ACTIONS = [("b1", "b2", "設定→カメラ"), ("b2", "b3", "グリッド・水平をオン"),
           ("b3", "b4", "カメラを起動"), ("b4", "cta", "真下に向ける")]
BODY = [
    ("b1", "設定アプリで、カメラを開いて、", 0.3),
    ("b2", "グリッドと、水平をオンにします。", 0.3),
    ("b3", "カメラに線が出て、傾きがひと目でわかります！", 0.3),
    ("b4", "真下に向けると、十字で水平もわかります。", 0.0),
]
BODY_HOLD = 1.0
CTA = dict(lines=[("設定→カメラ→", WHITE, 96), ("グリッドをオン！", YEL, 120)], spoken="保存して試してね！",
           chip="iOS 17以降は「水平」も一緒にオン")

PART = dict(
    title="グリッドと水平器",
    intro="写真が、なんとなく斜めになってしまう。そんな人は、カメラの設定を1つ変えるだけで解決します。",
    steps=[
        ("設定アプリを開く", "まず、設定アプリを開いて、下にスクロールし、カメラをタップします。", ("body", "b2")),
        ("「グリッド」をオン", "構図という項目の中にある、グリッドをオンにします。", ("b2", "b2+0.9")),
        ("「水平」もオン", "その下の、水平もオンにしておきましょう。", ("b2+0.8", "b3")),
        ("カメラに線が出る", "カメラを起動すると、画面が線で9つに区切られます。真ん中の線が黄色くなったら、まっすぐの合図です。", ("b3", "b3+2.0")),
        ("線は写真に写らない", "ちなみに、このグリッドの線は、撮った写真には写らないので安心してください。", ("b3+0.6", "b4")),
        ("真下に向けると十字", "料理や書類を真上から撮るときは、iPhoneを真下に向けます。2つの十字が重なって黄色になれば、水平です。", ("b4", "cta")),
    ],
    outro="設定、カメラ、グリッド。これだけで写真がぐっと上手に見えます。",
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

def times(T):
    return dict(tapcam=T.at["b1"] + 1.2, campage=T.at["b1"] + 1.45, grid=T.at["b2"] + 0.5, level=T.at["b2"] + 1.3,
                cam=T.at["b3"], straight=T.at["b3"] + 1.8, top=T.at["b4"], align=T.at["b4"] + 1.8,
                done=T.at["b3"] + 2.0)

def finger(ps, fx, fy):
    fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((fx - 30, fy - 30, fx + 30, fy + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))

# ---------------------------------------------------------------- Settings
ROOT_ROWS = [("一般", (142, 142, 147)), ("アクセシビリティ", (10, 132, 255)), ("カメラ", (99, 99, 102)),
             ("コントロールセンター", (142, 142, 147)), ("画面表示と明るさ", (10, 132, 255)), ("壁紙", (50, 173, 230))]
RY0, RH = 230, 60
CAM_ROW = 2

def settings_root(t, k):
    ps = Image.new("RGBA", (BW, BH), (242, 242, 247, 255))
    txt(ps, (56, 36), "9:41", 22, INK, anchor="lm")
    txt(ps, (22, 182), "設定", 38, INK, anchor="lm")
    rr(ps, (16, RY0, BW - 16, RY0 + RH * len(ROOT_ROWS)), 14, WHITE)
    d = ImageDraw.Draw(ps)
    for i, (name, col) in enumerate(ROOT_ROWS):
        y = RY0 + i * RH
        if i == CAM_ROW and k["tapcam"] - 0.1 <= t: d.rectangle((16, y, BW - 16, y + RH), fill=(209, 209, 214))
        rr(ps, (30, y + 14, 62, y + 46), 8, col)
        if name == "カメラ":
            rr(ps, (35, y + 22, 57, y + 40), 4, WHITE); d.ellipse((40, y + 25, 52, y + 37), fill=col); d.ellipse((43, y + 28, 49, y + 34), fill=WHITE)
        else:
            d.ellipse((40, y + 24, 52, y + 36), fill=WHITE)
        txt(ps, (76, y + RH / 2), name, 20, INK, bold=False, anchor="lm")
        txt(ps, (BW - 32, y + RH / 2), "›", 26, (196, 196, 199), bold=False, anchor="rm")
        if i < len(ROOT_ROWS) - 1: d.line((76, y + RH, BW - 16, y + RH), fill=(225, 225, 230), width=1)
    if k["tapcam"] - 0.5 <= t < k["campage"]: finger(ps, 160, RY0 + CAM_ROW * RH + RH / 2)
    return ps

CAM_ROWS = ["フォーマット", "ビデオ撮影", "スローモーション撮影", "設定を保持"]
COMP = ["グリッド", "水平", "前面カメラを反転"]
CY0 = 210
SY0 = CY0 + RH * len(CAM_ROWS) + 48     # 構図 section

def comp_row_y(i): return SY0 + i * RH

def settings_camera(t, k):
    ps = Image.new("RGBA", (BW, BH), (242, 242, 247, 255))
    txt(ps, (56, 36), "9:41", 22, INK, anchor="lm")
    txt(ps, (16, 172), "‹ 設定", 22, BLUE, bold=False, anchor="lm")
    txt(ps, (BW / 2, 172), "カメラ", 22, INK, anchor="mm")
    d = ImageDraw.Draw(ps)
    rr(ps, (16, CY0, BW - 16, CY0 + RH * len(CAM_ROWS)), 14, WHITE)
    for i, name in enumerate(CAM_ROWS):
        y = CY0 + i * RH
        txt(ps, (34, y + RH / 2), name, 20, INK, bold=False, anchor="lm")
        txt(ps, (BW - 32, y + RH / 2), "›", 26, (196, 196, 199), bold=False, anchor="rm")
        if i < len(CAM_ROWS) - 1: d.line((34, y + RH, BW - 16, y + RH), fill=(225, 225, 230), width=1)
    txt(ps, (34, SY0 - 16), "構図", 16, GRAY, bold=False, anchor="ls")
    rr(ps, (16, SY0, BW - 16, SY0 + RH * len(COMP)), 14, WHITE)
    ons = [t >= k["grid"], t >= k["level"], False]
    for i, name in enumerate(COMP):
        y = comp_row_y(i)
        hi = (i == 0 and k["grid"] <= t < k["grid"] + 0.6) or (i == 1 and k["level"] <= t < k["level"] + 0.6)
        if hi: fade(ps, 1.0, lambda l, y=y: rr(l, (18, y + 4, BW - 18, y + RH - 4), 10, (255, 214, 10, 70)))
        txt(ps, (34, y + RH / 2), name, 20, INK, bold=i < 2, anchor="lm")
        toggle(ps, BW - 80, y + RH / 2 - 14, ons[i])
        if i < len(COMP) - 1: d.line((34, y + RH, BW - 16, y + RH), fill=(225, 225, 230), width=1)
    fp = None
    if k["grid"] - 0.4 <= t < k["grid"] + 0.2: fp = (BW - 57, comp_row_y(0) + RH / 2)
    elif k["level"] - 0.4 <= t < k["level"] + 0.2: fp = (BW - 57, comp_row_y(1) + RH / 2)
    if fp: finger(ps, *fp)
    return ps

# ---------------------------------------------------------------- Camera
VF = (0, 120, 400, 653)                  # 4:3 viewfinder in screen coords

def make_scene():
    w, h = 700, 700
    im = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    im.alpha_composite(grad(w, 360, (120, 180, 240), (230, 200, 170)), (0, 0))
    im.alpha_composite(grad(w, 340, (40, 110, 160), (20, 60, 100)), (0, 360))
    d = ImageDraw.Draw(im)
    d.ellipse((420, 230, 500, 310), fill=(255, 236, 170))
    for y in range(380, 700, 28): d.line((0, y, w, y), fill=(60, 130, 180), width=2)
    d.polygon([(0, 560), (260, 520), (700, 600), (700, 700), (0, 700)], fill=(220, 200, 160))   # beach
    return im

SCENE = make_scene()

def make_food():
    w, h = 400, 533
    im = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    im.alpha_composite(grad(w, h, (176, 128, 88), (140, 98, 64)), (0, 0))
    d = ImageDraw.Draw(im)
    for y in range(20, h, 50): d.line((0, y, w, y + 6), fill=(158, 112, 76), width=2)
    d.ellipse((60, 126, 340, 406), fill=(248, 248, 244)); d.ellipse((92, 158, 308, 374), fill=(236, 236, 230))
    d.ellipse((120, 190, 280, 340), fill=(240, 180, 60))                  # omelette rice
    d.arc((140, 220, 260, 300), 200, 340, fill=(200, 40, 40), width=8)
    d.ellipse((150, 300, 180, 330), fill=(70, 160, 70))
    return im

FOOD = make_food()

def grid_lines(ps, box, col=(255, 255, 255, 140)):
    x0, y0, x1, y1 = box
    def f(l):
        dl = ImageDraw.Draw(l)
        for q in (1, 2):
            dl.line((x0 + (x1 - x0) * q / 3, y0, x0 + (x1 - x0) * q / 3, y1), fill=col, width=2)
            dl.line((x0, y0 + (y1 - y0) * q / 3, x1, y0 + (y1 - y0) * q / 3), fill=col, width=2)
    fade(ps, 1.0, f)

def cam_chrome(ps):
    d = ImageDraw.Draw(ps)
    txt(ps, (56, 36), "9:41", 22, WHITE, anchor="lm")
    txt(ps, (BW / 2, 88), "︿", 22, WHITE, bold=False, anchor="mm")
    by = 700
    for i, (m, x) in enumerate((("タイムラプス", 46), ("ビデオ", 140), ("写真", 210), ("ポートレート", 296))):
        txt(ps, (x, by), m, 17, YEL if m == "写真" else WHITE, anchor="mm")
    d.ellipse((BW / 2 - 38, 742, BW / 2 + 38, 818), outline=WHITE, width=5)
    d.ellipse((BW / 2 - 30, 750, BW / 2 + 30, 810), fill=WHITE)
    rr(ps, (34, 756, 82, 804), 8, (90, 120, 150))
    d.ellipse((BW - 82, 756, BW - 34, 804), fill=(50, 50, 54))

def camera_screen(t, k):
    ps = Image.new("RGBA", (BW, BH), (0, 0, 0, 255))
    x0, y0, x1, y1 = VF
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if t < k["top"]:
        # horizon: starts tilted, the user straightens the phone
        p = ease_inout(clamp((t - (k["cam"] + 0.4)) / (k["straight"] - k["cam"] - 0.4)))
        ang = 6.0 * (1 - p)
        sc = SCENE.rotate(ang, resample=Image.BICUBIC)
        sx, sy = (sc.width - (x1 - x0)) // 2, (sc.height - (y1 - y0)) // 2
        ps.alpha_composite(sc.crop((sx, sy, sx + x1 - x0, sy + y1 - y0)), (x0, y0))
        grid_lines(ps, VF)
        level = ang < 0.3
        col = YEL if level else WHITE
        d = ImageDraw.Draw(ps)
        # level indicator: fixed side segments + a centre segment that tilts with the phone
        d.line((cx - 130, cy, cx - 72, cy), fill=col, width=5); d.line((cx + 72, cy, cx + 130, cy), fill=col, width=5)
        a = math.radians(ang)
        dx, dy = 60 * math.cos(a), 60 * math.sin(a)
        d.line((cx - dx, cy + dy, cx + dx, cy - dy), fill=col, width=6)
    else:
        ps.alpha_composite(FOOD, (x0, y0))
        grid_lines(ps, VF)
        p = ease_inout(clamp((t - (k["top"] + 0.4)) / (k["align"] - k["top"] - 0.4)))
        ox, oy = 56 * (1 - p), -40 * (1 - p)
        ok = p >= 0.99
        d = ImageDraw.Draw(ps)
        def cross(x, y, col, w):
            d.line((x - 22, y, x + 22, y), fill=col, width=w); d.line((x, y - 22, x, y + 22), fill=col, width=w)
        cross(cx, cy, YEL if ok else WHITE, 4)                 # fixed centre
        cross(cx + ox, cy + oy, YEL, 4)                         # moves with the phone's tilt
    cam_chrome(ps)
    return ps

def screen(t, k):
    if t < k["campage"]: return settings_root(t, k)
    if t < k["cam"]: return settings_camera(t, k)
    return camera_screen(t, k)

def SCREEN(t, T): return screen(t, times(T))

def draw_body(c, t, T):                   # fallback (non-v3 renderers)
    k = times(T)
    big_phone(c, screen(t, k))
    if t < T.at["b2"]:
        telop(c, t, T.body, [("設定→カメラ", WHITE)], y0=400, size=96)
    elif t < T.at["b3"]:
        telop(c, t, T.at["b2"], [("グリッドと水平をオン", YEL)], y0=400, size=88)
    elif t < T.at["b4"]:
        telop(c, t, T.at["b3"], [("傾きがひと目でわかる", YEL)], y0=400, size=88)
    else:
        telop(c, t, T.at["b4"], [("真下で十字が重なる", YEL)], y0=400, size=88)
    badge(c, t, k["done"], "線は写真に写らない", 1505, GREEN, size=44)

def draw_hook_art(ly, t):
    x0, y0 = 340, 1170
    rr(ly, (x0, y0, x0 + 400, y0 + 240), 16, (20, 20, 24))
    d = ImageDraw.Draw(ly)
    for q in (1, 2):
        d.line((x0 + 400 * q / 3, y0, x0 + 400 * q / 3, y0 + 240), fill=WHITE, width=2)
        d.line((x0, y0 + 80 * q, x0 + 400, y0 + 80 * q), fill=WHITE, width=2)
    ang = 8 * math.sin(t * 3)
    a = math.radians(ang); cx, cy = x0 + 200, y0 + 120
    d.line((cx - 60 * math.cos(a), cy + 60 * math.sin(a), cx + 60 * math.cos(a), cy - 60 * math.sin(a)), fill=YEL, width=5)

def sfx(T):
    k = times(T)
    return [("click", k["tapcam"]), ("whoosh", k["campage"]), ("click", k["grid"]), ("click", k["level"]),
            ("whoosh", k["cam"]), ("ding", k["straight"]), ("whoosh", k["top"]), ("ding", k["align"])]

def stills(T):
    k = times(T)
    return [k["tapcam"] - 0.1, k["level"] + 0.3, k["cam"] + 0.6, k["straight"] + 0.3, k["align"] + 0.3]
