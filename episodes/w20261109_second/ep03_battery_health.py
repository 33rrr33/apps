# iPhone隠し神機能⑧（11/14 06:00） バッテリーの状態で最大容量をチェック（交換の目安は80%）（v3・画面録画風・即効型）
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="w20261109_second", title="iPhone隠し神機能", spoken="iPhone隠し、かみ機能",
              hook_split=("iPhone", "隠し神機能"), total=5, offset=5)
TITLE = "iPhoneユーザーの9割が知らない、バッテリーの寿命チェック #Shorts"
NUM, SLUG = 3, "battery_health"
NEXT = "使わないアプリの更新をオフ"
SCREEN_CROP = (0, 40, 400, 760)
DURATION, END_CARD = 13.5, False
TAGS = {"length": "短縮版", "layout": "画面録画風", "hook_type": "即効型", "title_type": "9割型"}
LAYOUT, FOCUS_Y, CAPTION_Y = "rec", 400, 1260
HOOK = "バッテリーの寿命\n[3秒]でチェック！"
HOOK_SPOKEN = "バッテリーの寿命、3秒でチェック！"
TELOPS = [("b1", "設定 →\n[バッテリー]"), ("b2", "[バッテリーの状態]を\nタップ"),
          ("b3", "[最大容量]が\n電池の元気度"), ("b4", "{80%}を切ったら\n交換の目安")]
ACTIONS = [("b1", "b2", "設定 → バッテリー"), ("b2", "b3", "バッテリーの状態をタップ"),
           ("b3", "b4", "最大容量をチェック"), ("b4", "cta", "80%未満なら交換を検討")]
BODY = [
    ("b1", "設定のバッテリーを開いて、", 0.1),
    ("b2", "バッテリーの状態をタップ。", 0.15),
    ("b3", "この最大容量が、電池の元気度です。", 0.1),
    ("b4", "80%を切ったら、交換の目安！", 0.0),
]
BODY_HOLD = 0.5
CTA = dict(lines=[("最大容量は", WHITE, 110), ("80%が目安！", YEL, 130)], spoken="保存してね！",
           chip="今すぐチェック")

PART = dict(
    title="バッテリーの寿命をチェック",
    intro="最近、電池の減りが早い気がする。そんな時は、バッテリーの状態を見てみましょう。",
    steps=[
        ("設定 → バッテリー", "設定アプリを開いて、バッテリーをタップします。", ("body", "b2")),
        ("バッテリーの状態", "次に、バッテリーの状態を開きます。iPhone 14以前は、バッテリーの状態と充電です。", ("b2", "b3")),
        ("最大容量を確認", "ここにある最大容量が、新品の時と比べて、今どれくらい電池を貯められるかの目安です。", ("b3", "b4")),
        ("80%が交換の目安", "最大容量が80%を下回ってきたら、バッテリー交換を考えるタイミングです。", ("b4", "cta")),
    ],
    outro="数字で見ると、交換のタイミングがわかりやすくなります。一度チェックしてみてください。",
)

BW, BH = 400, 860
ROW_Y0 = 180

def times(T):
    return dict(battery=T.at["b1"] + 0.3, tap=T.at["b2"] + 0.4, health=T.at["b2"] + 0.7,
                count=T.at["b3"], warn=T.at["b4"] + 0.2)

def finger(ps, x, y):
    fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((x - 30, y - 30, x + 30, y + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))

def settings_root(t, k):
    ps = Image.new("RGBA", (BW, BH), (242, 242, 247, 255))
    txt(ps, (56, 36), "9:41", 22, INK, anchor="lm")
    txt(ps, (24, 120), "設定", 34, INK, anchor="lm")
    rows = [("一般", (142, 142, 147)), ("画面表示と明るさ", (10, 132, 255)), ("壁紙", (90, 200, 250)),
            ("バッテリー", (52, 199, 89)), ("プライバシー", (10, 132, 255))]
    y = ROW_Y0
    for i, (r, col) in enumerate(rows):
        hi = i == 3 and t >= k["battery"] - 0.3
        rr(ps, (16, y, BW - 16, y + 58), 12, (255, 236, 150) if hi else WHITE)
        ImageDraw.Draw(ps).rounded_rectangle((30, y + 13, 62, y + 45), 8, fill=col)
        txt(ps, (78, y + 29), r, 19, INK, bold=i == 3, anchor="lm")
        txt(ps, (BW - 34, y + 29), "›", 26, GRAY, anchor="rm")
        y += 64
    if k["battery"] - 0.35 <= t < k["battery"]: finger(ps, BW / 2, ROW_Y0 + 3 * 64 + 29)
    return ps

def battery_page(t, k):
    ps = Image.new("RGBA", (BW, BH), (242, 242, 247, 255))
    txt(ps, (56, 36), "9:41", 22, INK, anchor="lm")
    txt(ps, (24, 84), "‹ 設定", 20, BLUE, bold=False, anchor="lm")
    txt(ps, (24, 132), "バッテリー", 34, INK, anchor="lm")
    rows = ["バッテリー残量（%）", "低電力モード", "バッテリーの状態", "充電"]
    y = ROW_Y0
    for i, r in enumerate(rows):
        hi = i == 2 and t >= k["tap"] - 0.3
        rr(ps, (16, y, BW - 16, y + 62), 12, (255, 236, 150) if hi else WHITE)
        txt(ps, (34, y + 31), r, 19, INK, bold=i == 2, anchor="lm")
        if i < 2: toggle(ps, BW - 86, y + 13, i == 0)
        else: txt(ps, (BW - 34, y + 31), "›", 26, GRAY, anchor="rm")
        y += 72
    if k["tap"] - 0.35 <= t < k["tap"] + 0.1: finger(ps, BW / 2, ROW_Y0 + 2 * 72 + 31)
    return ps

def health_page(t, k):
    ps = Image.new("RGBA", (BW, BH), (242, 242, 247, 255))
    txt(ps, (56, 36), "9:41", 22, INK, anchor="lm")
    txt(ps, (24, 84), "‹ バッテリー", 20, BLUE, bold=False, anchor="lm")
    txt(ps, (24, 132), "バッテリーの状態", 30, INK, anchor="lm")
    rr(ps, (16, 168, BW - 16, 300), 14, (255, 236, 150) if t >= k["count"] else WHITE)
    txt(ps, (34, 196), "最大容量", 18, INK, anchor="lm")
    p = clamp((t - k["count"]) / 0.6) if t >= k["count"] else 1.0
    val = int(100 - 13 * p) if t >= k["count"] else 87
    col = (255, 59, 48) if val < 80 else INK
    txt(ps, (34, 252), f"{val}%", 56, col, anchor="lm")
    txt(ps, (BW - 34, 252), "サイクル 412回", 15, GRAY, bold=False, anchor="rm")
    # gauge with an 80% line
    gx0, gx1, gy = 34, BW - 34, 336
    d = ImageDraw.Draw(ps)
    d.rounded_rectangle((gx0, gy, gx1, gy + 26), 13, fill=(225, 225, 232))
    d.rounded_rectangle((gx0, gy, gx0 + (gx1 - gx0) * val / 100, gy + 26), 13, fill=(52, 199, 89))
    x80 = gx0 + (gx1 - gx0) * 0.8
    warn = t >= k["warn"]
    d.line((x80, gy - 12, x80, gy + 38), fill=(255, 59, 48) if warn else (120, 120, 130), width=5 if warn else 3)
    txt(ps, (x80, gy + 56), "80%", 18, (255, 59, 48) if warn else GRAY, anchor="mm")
    txt(ps, (gx0, gy + 56), "交換の目安 →", 15, (255, 59, 48) if warn else GRAY, bold=False, anchor="lm")
    rr(ps, (16, 620, BW - 16, 720), 14, WHITE)
    txt(ps, (34, 652), "iPhone 14以前は", 16, INK, anchor="lm")
    txt(ps, (34, 688), "「バッテリーの状態と充電」", 16, GRAY, bold=False, anchor="lm")
    return ps

def screen(t, k):
    if t >= k["health"]: return health_page(t, k)
    if t >= k["battery"]: return battery_page(t, k)
    return settings_root(t, k)

def SCREEN(t, T): return screen(t, times(T))

def draw_body(c, t, T): pass

def draw_hook_art(ly, t): pass

def sfx(T):
    k = times(T)
    return [("click", k["battery"]), ("click", k["tap"]), ("pop", k["health"]), ("ding", k["count"] + 0.6), ("pop", k["warn"])]

def stills(T):
    k = times(T)
    return [T.at["b1"] + 0.1, k["battery"] + 0.3, k["tap"] - 0.1, k["count"] + 0.8, k["warn"] + 0.3]
