# iPhone隠し神機能①（11/9週） 充電の上限を80%に（設定→バッテリー→充電・iPhone 15以降）（v3・短縮版）
import math
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="w20261109_second", title="iPhone隠し神機能", spoken="iPhone隠し、かみ機能",
              hook_split=("iPhone", "隠し神機能"), total=5, offset=5)
TITLE = "iPhoneを毎晩100%まで充電してる人へ #Shorts"
NUM, SLUG = 1, "charge_limit"
NEXT = "低電力モードをすぐ切り替え"
SCREEN_CROP = (0, 40, 400, 760)
# PDCA 実験 short_length：約12〜13秒・エンドカードなし
DURATION, END_CARD = 13.5, False
TAGS = {"length": "短縮版", "layout": "画面録画風", "hook_type": "煽り型"}
LAYOUT, FOCUS_Y, CAPTION_Y = "rec", 430, 1260
HOOK = "毎晩100%まで\n{充電してる人へ}"
HOOK_SPOKEN = "毎晩100%まで充電してる人へ！"
TELOPS = [("b1", "毎晩{100%}まで\n充電してない？"), ("b2", "バッテリーが\n{劣化しやすい}"),
          ("b3", "設定 → バッテリー →\n[充電]"), ("b4", "上限を[80%]に\nするだけ！")]
ACTIONS = [("b1", "b2", "寝る前に充電100%…"), ("b2", "b3", "満充電のままが長いと劣化"),
           ("b3", "b4", "設定 → バッテリー → 充電"), ("b4", "cta", "80%をタップ")]
BODY = [
    ("b1", "毎晩100%まで充電していると、", 0.15),
    ("b2", "バッテリーが傷みやすくなります。", 0.2),
    ("b3", "設定のバッテリー、充電を開いて、", 0.15),
    ("b4", "上限を80%にするだけ！", 0.0),
]
BODY_HOLD = 0.6
CTA = dict(lines=[("充電の上限は", WHITE, 100), ("80%に！", YEL, 140)], spoken="保存してね！",
           chip="iPhone 15以降")

PART = dict(
    title="充電の上限を80%に",
    intro="寝る前に充電して、朝まで100%のまま。実はこれ、バッテリーには負担なんです。",
    steps=[
        ("100%のままは負担", "バッテリーは、満充電の状態が長く続くと、劣化が進みやすいと言われています。", ("body", "b3")),
        ("設定 → バッテリー", "設定アプリを開いて、バッテリーをタップします。", ("b3", "b3+0.8")),
        ("「充電」を開く", "次に、充電を開きます。", ("b3+0.6", "b4")),
        ("上限を80%に", "充電の上限から、80%を選ぶだけで設定完了です。", ("b4", "cta")),
        ("iPhone 14以前は", "iPhone 14以前は、バッテリーの状態と充電にある、最適化されたバッテリー充電をオンにしておきましょう。", ("b3", "b3+0.6")),
    ],
    outro="少しの設定で、バッテリーを長持ちさせられます。ぜひ見直してみてください。",
)

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
    return dict(fill=T.at["b1"] - 1.0, full=T.at["b1"] + 1.2, settings=T.at["b3"], charge=T.at["b3"] + 0.9,
                pick=T.at["b4"] + 0.4)

def finger(ps, x, y):
    fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((x - 30, y - 30, x + 30, y + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))

def battery(ps, cx, cy, pct, col, w=200, h=96):
    d = ImageDraw.Draw(ps)
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), 22, outline=WHITE, width=6)
    d.rounded_rectangle((cx + w / 2 + 4, cy - 16, cx + w / 2 + 14, cy + 16), 4, fill=WHITE)
    fw = (w - 24) * pct / 100
    d.rounded_rectangle((cx - w / 2 + 12, cy - h / 2 + 12, cx - w / 2 + 12 + fw, cy + h / 2 - 12), 12, fill=col)

def lock_screen(t, k):
    ps = grad(BW, BH, (20, 24, 60), (60, 30, 90))
    txt(ps, (BW / 2, 150), "0:24", 80, WHITE, anchor="mm")
    txt(ps, (BW / 2, 210), "11月10日 火曜日", 20, WHITE, bold=False, anchor="mm")
    p = clamp((t - k["fill"]) / (k["full"] - k["fill"]))
    pct = int(60 + 40 * p)
    full = pct >= 100
    battery(ps, BW / 2, 400, pct, (255, 69, 58) if (full and t >= T_WARN(k)) else (48, 209, 88))
    txt(ps, (BW / 2, 480), f"{pct}%", 40, WHITE, anchor="mm")
    txt(ps, (BW / 2, 530), "充電中", 18, (200, 200, 210), bold=False, anchor="mm")
    if full and t >= T_WARN(k):
        rra(ps, (40, 580, BW - 40, 660), 18, (255, 69, 58, 200))
        txt(ps, (BW / 2, 620), "朝まで100%のまま…", 22, WHITE, anchor="mm")
    return ps

def T_WARN(k): return k["full"] + 0.6

def settings_screen(t, k):
    ps = Image.new("RGBA", (BW, BH), (242, 242, 247, 255))
    txt(ps, (56, 36), "9:41", 22, INK, anchor="lm")
    if t < k["charge"]:
        txt(ps, (24, 84), "‹ 設定", 20, BLUE, bold=False, anchor="lm")
        txt(ps, (24, 132), "バッテリー", 34, INK, anchor="lm")
        rows = ["バッテリー残量（%）", "低電力モード", "バッテリーの状態", "充電"]
        y = 180
        for i, r in enumerate(rows):
            hi = i == 3 and t >= k["settings"] + 0.4
            rr(ps, (16, y, BW - 16, y + 62), 12, (255, 236, 150) if hi else WHITE)
            txt(ps, (34, y + 31), r, 19, INK, bold=i == 3, anchor="lm")
            if i < 2: toggle(ps, BW - 86, y + 13, i == 0)
            else: txt(ps, (BW - 34, y + 31), "›", 26, GRAY, anchor="rm")
            y += 72
        if k["settings"] + 0.3 <= t < k["charge"]: finger(ps, BW / 2, 180 + 3 * 72 + 31)
        return ps
    txt(ps, (24, 84), "‹ バッテリー", 20, BLUE, bold=False, anchor="lm")
    txt(ps, (24, 132), "充電", 34, INK, anchor="lm")
    txt(ps, (30, 176), "充電の上限", 15, GRAY, bold=False, anchor="lm")
    sel = 80 if t >= k["pick"] else 100
    y = 196
    for v in (80, 85, 90, 95, 100):
        hi = v == 80 and t >= k["pick"]
        rr(ps, (16, y, BW - 16, y + 58), 12, (255, 236, 150) if hi else WHITE)
        txt(ps, (34, y + 29), f"{v}%", 20, INK, bold=v == sel, anchor="lm")
        if v == sel: check(ps, BW - 64, y + 17, 22, BLUE, 4)
        y += 66
    if k["pick"] - 0.3 <= t < k["pick"] + 0.3: finger(ps, BW / 2, 196 + 29)
    if t >= k["pick"] + 0.4:
        txt(ps, (30, y + 30), "80%に達すると充電を止めます", 16, GRAY, bold=False, anchor="lm")
    return ps

def screen(t, k):
    return settings_screen(t, k) if t >= k["settings"] else lock_screen(t, k)

def SCREEN(t, T): return screen(t, times(T))

def draw_body(c, t, T):
    big_phone(c, screen(t, times(T)))

def draw_hook_art(ly, t): pass

def sfx(T):
    k = times(T)
    return [("ding", k["full"]), ("pop", T_WARN(k)), ("pop", k["settings"]), ("click", k["charge"]), ("click", k["pick"]), ("ding", k["pick"] + 0.2)]

def stills(T):
    k = times(T)
    return [k["full"] - 0.5, T_WARN(k) + 0.3, k["settings"] + 0.5, k["charge"] + 0.3, k["pick"] + 0.6]
