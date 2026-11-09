# iPhone爆速神操作④（11/9週） コントロールセンターのアイコンを長押しで詳細（懐中電灯の明るさ・通信の詳細）（v3）
import math
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="w20261109_first", title="iPhone爆速神操作", spoken="iPhone爆速、かみ操作",
              hook_split=("iPhone", "爆速神操作"), total=5)
NUM, SLUG = 4, "cc_longpress"
NEXT = "AssistiveTouch"
SCREEN_CROP = (0, 40, 400, 700)
# 2026-11-09 実験：短縮版（約13秒・エンドカードなし）
DURATION, END_CARD = 13.5, False
HOOK = "タップしかしない人\n{全員損}してます"
HOOK_SPOKEN = "タップしかしてない人、全員損してます！"
TELOPS = [("b1", "コントロールセンター\n{タップだけ}…？"), ("b2", "懐中電灯を\n[長押し]"),
          ("b3", "明るさを\n[細かく調整]できる！"), ("b4", "通信ボタンも\n[長押しで詳細]")]
ACTIONS = [("b1", "b2", "右上から下にスワイプ"), ("b2", "b3", "懐中電灯を長押し"),
           ("b3", "b4", "指で上下にスライド"), ("b4", "cta", "通信ボタンを長押し")]
BODY = [
    ("b1", "コントロールセンター、長押ししてますか？", 0.15),
    ("b2", "懐中電灯を長押しすると、", 0.15),
    ("b3", "明るさを細かく調整できます！", 0.2),
    ("b4", "通信ボタンも長押しで詳細に。", 0.0),
]
BODY_HOLD = 0.9
CTA = dict(lines=[("アイコンを", WHITE, 100), ("長押し！", YEL, 132)], spoken="保存してね！",
           chip="懐中電灯・通信・明るさなど")

PART = dict(
    title="コントロールセンターの長押し",
    intro="コントロールセンターのボタン、タップしてオンとオフを切り替えるだけになっていませんか？",
    steps=[
        ("コントロールセンターを開く", "まず、画面の右上から下にスワイプして、コントロールセンターを開きます。", ("body", "b2")),
        ("懐中電灯を長押し", "次に、懐中電灯のボタンを、少し長めに押してみてください。", ("b2", "b3")),
        ("明るさを細かく調整", "大きなバーが出てくるので、指で上下にスライドすると、ライトの明るさを細かく調整できます。", ("b3", "b4")),
        ("通信ボタンも長押し", "左上の、機内モードやWiFiがまとまったボタンを長押しすると、エアドロップやインターネット共有まで表示されます。", ("b4", "cta")),
        ("ほかのボタンでも", "画面の明るさのバーなど、ほかのボタンも長押しすると、隠れたメニューが出るものがあります。", ("b2+0.3", "b3")),
    ],
    outro="コントロールセンターは、タップだけでなく長押しも。ぜひいろいろ試してみてください。",
)

# ---- big centered iPhone (fallback layout) ----
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

TILE = (60, 60, 60, 230)
ON_BLUE = (10, 132, 255)

def times(T):
    return dict(open=T.at["b1"] + 0.2, press=T.at["b2"] + 0.2, big=T.at["b2"] + 0.9, slide=T.at["b3"] + 0.1,
                slid=T.at["b3"] + 1.2, conn=T.at["b4"] + 0.2, conn_open=T.at["b4"] + 0.9)

def finger(ps, x, y):
    fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((x - 30, y - 30, x + 30, y + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))

def round_btn(ps, cx, cy, r, col, label):
    ImageDraw.Draw(ps).ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)
    txt(ps, (cx, cy), label, 16, WHITE, anchor="mm")

def flashlight_icon(d, cx, cy, s, col):
    d.rectangle((cx - s * 0.18, cy - s * 0.05, cx + s * 0.18, cy + s * 0.5), fill=col)
    d.polygon([(cx - s * 0.32, cy - s * 0.45), (cx + s * 0.32, cy - s * 0.45), (cx + s * 0.18, cy - s * 0.05), (cx - s * 0.18, cy - s * 0.05)], fill=col)

def home_bg():
    ps = grad(BW, BH, (255, 140, 90), (120, 60, 200))
    txt(ps, (56, 36), "9:41", 22, WHITE, anchor="lm")
    cols = [(52, 199, 89), (10, 132, 255), (255, 159, 10), (255, 59, 48), (175, 82, 222), (90, 200, 250), (255, 214, 10), (142, 142, 147)]
    names = ["メッセージ", "Safari", "写真", "カメラ", "メモ", "天気", "時計", "設定"]
    for i in range(16):
        x = 26 + (i % 4) * 92; y = 90 + (i // 4) * 110
        rr(ps, (x, y, x + 66, y + 66), 16, cols[i % 8])
        txt(ps, (x + 33, y + 84), names[i % 8], 13, WHITE, bold=False, anchor="mm")
    rra(ps, (14, BH - 120, BW - 14, BH - 24), 30, (255, 255, 255, 60))
    for i in range(4): rr(ps, (34 + i * 90, BH - 106, 100 + i * 90, BH - 40), 16, cols[i])
    return ps

def cc_screen(t, k):
    ps = home_bg()
    a = e_at(t, k["open"], 0.35) if t >= k["open"] else 0
    ps.alpha_composite(Image.new("RGBA", (BW, BH), (20, 20, 26, int(200 * a))))
    if a <= 0:
        if t >= k["open"] - 0.4: finger(ps, BW - 50, 40 + 200 * clamp((t - k["open"] + 0.4) / 0.4))
        return ps
    d = ImageDraw.Draw(ps)
    # connectivity block (top-left)
    cb = (24, 90, 196, 262)
    rra(ps, cb, 30, TILE)
    for (cx, cy, col, lab) in ((66, 132, (255, 159, 10), "機内"), (154, 132, ON_BLUE, "通信"), (66, 220, ON_BLUE, "Wi-Fi"), (154, 220, ON_BLUE, "BT")):
        round_btn(ps, cx, cy, 32, col, lab)
    # music tile
    rra(ps, (208, 90, 376, 262), 30, TILE)
    txt(ps, (292, 150), "再生停止中", 16, (200, 200, 205), bold=False, anchor="mm")
    # brightness / volume sliders
    for x0, lab in ((208, "明るさ"), (296, "音量")):
        rra(ps, (x0, 276, x0 + 80, 452), 26, TILE)
        rr(ps, (x0, 380, x0 + 80, 452), 26, (235, 235, 240))
        txt(ps, (x0 + 40, 416), lab, 14, INK, anchor="mm")
    # bottom row: flashlight, timer, calculator, camera
    lit = t >= k["slide"] - 0.2 and t < k["conn"]
    for i, lab in enumerate(["", "タイマー", "計算機", "カメラ"]):
        x = 24 + i * 88; box = (x, 470, x + 72, 542)
        rra(ps, box, 20, (245, 245, 250, 255) if (i == 0 and lit) else TILE)
        if i == 0: flashlight_icon(d, x + 36, 506, 40, INK if lit else WHITE)
        else: txt(ps, (x + 36, 506), lab, 13, WHITE, anchor="mm")
    # long-press flashlight -> big slider
    if k["press"] - 0.4 <= t < k["big"]:
        p = clamp((t - k["press"]) / (k["big"] - k["press"]))
        finger(ps, 60, 506)
        if p > 0:
            ImageDraw.Draw(ps).arc((60 - 44, 506 - 44, 60 + 44, 506 + 44), -90, -90 + 360 * p, fill=YEL, width=6)
    if k["big"] <= t < k["conn"]:
        e = e_at(t, k["big"], 0.3)
        def big(l):
            l.alpha_composite(Image.new("RGBA", l.size, (10, 10, 14, 170)))
            sx0, sy0, sx1, sy1 = 130, 160, 270, 560
            rra(l, (sx0, sy0, sx1, sy1), 40, (70, 70, 76, 240))
            q = 0.3
            if t >= k["slide"]: q = 0.3 + 0.55 * ease_inout((t - k["slide"]) / (k["slid"] - k["slide"]))
            fy = sy1 - (sy1 - sy0) * q
            rr(l, (sx0, int(fy), sx1, sy1), 40, (250, 250, 252))
            flashlight_icon(ImageDraw.Draw(l), (sx0 + sx1) / 2, sy1 - 50, 50, INK)
            if t >= k["slide"] - 0.2:
                ImageDraw.Draw(l).ellipse(((sx0 + sx1) / 2 - 30, fy - 30, (sx0 + sx1) / 2 + 30, fy + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3)
        fade(ps, e, big)
    # long-press connectivity block -> expanded panel
    if k["conn"] - 0.4 <= t < k["conn_open"]:
        p = clamp((t - k["conn"]) / (k["conn_open"] - k["conn"]))
        finger(ps, 110, 176)
        if p > 0: ImageDraw.Draw(ps).arc((110 - 44, 176 - 44, 110 + 44, 176 + 44), -90, -90 + 360 * p, fill=YEL, width=6)
    if t >= k["conn_open"]:
        e = e_at(t, k["conn_open"], 0.3)
        def panel(l):
            l.alpha_composite(Image.new("RGBA", l.size, (10, 10, 14, 170)))
            rra(l, (40, 140, BW - 40, 520), 34, (70, 70, 76, 240))
            items = [((255, 159, 10), "機内モード"), (ON_BLUE, "モバイル通信"), (ON_BLUE, "Wi-Fi"), (ON_BLUE, "Bluetooth"),
                     (ON_BLUE, "AirDrop"), ((52, 199, 89), "インターネット共有")]
            for j, (col, lab) in enumerate(items):
                cx = 110 + (j % 2) * 170; cy = 210 + (j // 2) * 110
                round_btn(l, cx, cy, 30, col, "")
                hi = lab == "AirDrop"
                txt(l, (cx, cy + 48), lab, 16, YEL if hi else WHITE, bold=hi, anchor="mm")
        fade(ps, e, panel)
    return ps

def SCREEN(t, T): return cc_screen(t, times(T))

def draw_body(c, t, T):
    big_phone(c, cc_screen(t, times(T)))

def draw_hook_art(ly, t): pass

def sfx(T):
    k = times(T)
    return [("whoosh", k["open"]), ("pop", k["big"]), ("whoosh", k["slide"] + 0.3), ("ding", k["slid"]), ("pop", k["conn_open"])]

def stills(T):
    k = times(T)
    return [k["open"] + 0.6, k["press"] + 0.5, (k["slide"] + k["slid"]) / 2, k["conn"] + 0.5, k["conn_open"] + 0.6]
