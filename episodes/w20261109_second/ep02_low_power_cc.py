# iPhone隠し神機能⑦（11/13 19:00） 低電力モードをコントロールセンターに追加してワンタップ切り替え（v3・画面録画風・疑問型）
import math
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="w20261109_second", title="iPhone隠し神機能", spoken="iPhone隠し、かみ機能",
              hook_split=("iPhone", "隠し神機能"), total=5, offset=5)
TITLE = "iPhoneの低電力モード、毎回設定から探してない？ #Shorts"
NUM, SLUG = 2, "low_power_cc"
NEXT = "バッテリーの状態をチェック"
SCREEN_CROP = (0, 40, 400, 760)
DURATION, END_CARD = 13.5, False
TAGS = {"length": "短縮版", "layout": "画面録画風", "hook_type": "疑問型", "title_type": "疑問型"}
LAYOUT, FOCUS_Y, CAPTION_Y = "rec", 400, 1260
HOOK = "低電力モード\n毎回{設定から}探してない？"
HOOK_SPOKEN = "低電力モード、毎回設定から探してない？"
TELOPS = [("b1", "コントロールセンターに\n[低電力モード]を置く"), ("b2", "[ワンタップ]で\nオン・オフ！"),
          ("b3", "左上の[＋] →\nコントロールを追加"), ("b4", "「低電力」で検索して\n[追加]するだけ")]
ACTIONS = [("b1", "b2", "右上から下にスワイプ"), ("b2", "b3", "電池アイコンをタップ"),
           ("b3", "b4", "＋ → コントロールを追加"), ("b4", "cta", "低電力モードをタップ")]
BODY = [
    ("b1", "低電力モードは、ここに置いておくと、", 0.1),
    ("b2", "ワンタップで切り替えられます！", 0.15),
    ("b3", "プラスから、コントロールを追加。", 0.1),
    ("b4", "低電力で検索して、追加！", 0.0),
]
BODY_HOLD = 0.4
CTA = dict(lines=[("低電力モードは", WHITE, 100), ("ワンタップで！", YEL, 130)], spoken="保存してね！",
           chip="iOS 18以降")

PART = dict(
    title="低電力モードをワンタップで切り替え",
    intro="電池が減ってきたとき、低電力モードにしたくても、毎回設定アプリを開くのは面倒ですよね。",
    steps=[
        ("コントロールセンターに置く", "低電力モードは、コントロールセンターに置いておくと、すぐに切り替えられます。", ("body", "b2")),
        ("ワンタップでオン・オフ", "画面の右上から下にスワイプして、電池のアイコンをタップするだけ。オンにすると、電池のマークが黄色になります。", ("b2", "b3")),
        ("左上の＋をタップ", "追加するには、コントロールセンターを開いて、左上のプラスをタップします。", ("b3", "b3+0.9")),
        ("コントロールを追加", "下に出てくる、コントロールを追加を開きます。", ("b3+0.8", "b4")),
        ("「低電力」で検索", "検索欄に、低電力と入れて、低電力モードをタップすれば追加完了です。", ("b4", "cta")),
    ],
    outro="外出先で電池が心細いときも、すぐに切り替えられます。ぜひ設定してみてください。",
)

BW, BH = 400, 860
LP_X, LP_Y = 288, 300          # low power tile (top-left), 80x80

def times(T):
    return dict(cc=T.at["b1"] + 0.2, tap=T.at["b2"] + 0.3, edit=T.at["b3"], plus=T.at["b3"] + 0.3,
                add=T.at["b3"] + 1.1, gallery=T.at["b4"], type0=T.at["b4"] + 0.3, pick=T.at["b4"] + 1.4,
                added=T.at["b4"] + 1.8)

def finger(ps, x, y):
    fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((x - 30, y - 30, x + 30, y + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))

def batt_icon(ps, cx, cy, col, w=34, h=16, lw=2, pct=0.35):
    d = ImageDraw.Draw(ps)
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), 4, outline=col, width=lw)
    d.rectangle((cx + w / 2 + 1, cy - h / 5, cx + w / 2 + 3, cy + h / 5), fill=col)
    d.rounded_rectangle((cx - w / 2 + 3, cy - h / 2 + 3, cx - w / 2 + 3 + (w - 6) * pct, cy + h / 2 - 3), 2, fill=col)

def status(ps, lp, dark=True):
    col = WHITE if dark else INK
    txt(ps, (56, 36), "9:41", 22, col, anchor="lm")
    batt_icon(ps, BW - 60, 36, (255, 214, 10) if lp else col)

def tile(ps, x, y, on=False, glow=0.0, label=None, icon=None):
    def draw(l):
        d = ImageDraw.Draw(l)
        if glow > 0: d.rounded_rectangle((x - 8, y - 8, x + 88, y + 88), 28, outline=(255, 214, 10, int(255 * glow)), width=6)
        d.rounded_rectangle((x, y, x + 80, y + 80), 24, fill=(255, 214, 10, 255) if on else (70, 70, 80, 235))
    fade(ps, 1.0, draw)
    if icon == "batt": batt_icon(ps, x + 40, y + 40, (30, 30, 30) if on else WHITE, w=40, h=20, lw=3)
    elif icon: ImageDraw.Draw(ps).ellipse((x + 28, y + 28, x + 52, y + 52), fill=icon)
    if label: txt(ps, (x + 40, y + 98), label, 13, WHITE, bold=False, anchor="mm")

def cc_base(t, k, lp, dim=0.0):
    ps = grad(BW, BH, (40, 44, 70), (18, 18, 30))
    status(ps, lp)
    rra(ps, (16, 110, 188, 282), 36, (60, 60, 72, 235))
    for i, c in enumerate([(255, 159, 10), (52, 199, 89), (10, 132, 255), (10, 132, 255)]):
        cx, cy = 58 + (i % 2) * 88, 152 + (i // 2) * 88
        ImageDraw.Draw(ps).ellipse((cx - 28, cy - 28, cx + 28, cy + 28), fill=c)
    rra(ps, (204, 110, 384, 282), 36, (60, 60, 72, 235))
    txt(ps, (294, 196), "再生停止中", 16, (200, 200, 210), bold=False, anchor="mm")
    rra(ps, (16, 430, 100, 514), 24, (70, 70, 80, 235)); rra(ps, (104, 430, 188, 514), 24, (70, 70, 80, 235))
    for x0 in (204, 296):
        rra(ps, (x0, 430, x0 + 88, 610), 30, (70, 70, 80, 235))
        rra(ps, (x0, 530, x0 + 88, 610), 0, (235, 235, 240, 255))
    tile(ps, 16, LP_Y, icon=(255, 255, 255), label="ライト")
    tile(ps, 112, LP_Y, icon=(255, 159, 10), label="タイマー")
    tile(ps, 200, LP_Y, icon=(142, 142, 147), label="計算機")
    return ps

def cc_screen(t, k):
    lp = t >= k["tap"]
    ps = cc_base(t, k, lp)
    glow = clamp(1 - abs(t - k["tap"]) / 0.5) if t >= k["cc"] else 0
    tile(ps, LP_X, LP_Y, on=lp, glow=glow, label="低電力モード", icon="batt")
    if k["tap"] - 0.35 <= t < k["tap"] + 0.25: finger(ps, LP_X + 40, LP_Y + 40)
    if lp:
        rra(ps, (60, 680, BW - 60, 736), 28, (255, 214, 10, 235))
        txt(ps, (BW / 2, 708), "低電力モード：オン", 20, INK, anchor="mm")
    return ps

def edit_screen(t, k):
    ps = cc_base(t, k, True)
    tile(ps, LP_X, LP_Y, on=True, label="低電力モード", icon="batt")
    ps.alpha_composite(Image.new("RGBA", (BW, BH), (0, 0, 0, 90)))
    hi = t >= k["plus"]
    d = ImageDraw.Draw(ps)
    if hi: d.ellipse((14, 72, 74, 132), outline=YEL, width=5)
    d.ellipse((22, 80, 66, 124), fill=(90, 90, 100))
    txt(ps, (44, 101), "＋", 26, WHITE, anchor="mm")
    if t >= k["plus"] + 0.3:
        hb = t >= k["add"] - 0.3
        rra(ps, (70, 656, BW - 70, 716), 30, (255, 236, 150, 255) if hb else (235, 235, 240, 240))
        txt(ps, (BW / 2, 686), "コントロールを追加", 20, INK, anchor="mm")
        if k["add"] - 0.35 <= t < k["add"]: finger(ps, BW / 2, 686)
    elif k["plus"] - 0.3 <= t < k["plus"] + 0.2: finger(ps, 44, 102)
    return ps

def gallery(t, k):
    ps = grad(BW, BH, (40, 44, 70), (18, 18, 30))
    status(ps, True)
    rra(ps, (0, 90, BW, BH), 34, (242, 242, 247, 255))
    rra(ps, (20, 116, BW - 20, 166), 14, (225, 225, 232, 255))
    q = "低電力"[:max(0, min(3, int((t - k["type0"]) / 0.25) + 1))] if t >= k["type0"] else ""
    txt(ps, (44, 141), q if q else "コントロールを検索", 19, INK if q else GRAY, bold=False, anchor="lm")
    if len(q) == 3:
        txt(ps, (30, 200), "検索結果", 15, GRAY, bold=False, anchor="lm")
        hi = t >= k["pick"] - 0.3
        rr(ps, (16, 220, BW - 16, 300), 16, (255, 236, 150) if hi else WHITE)
        ImageDraw.Draw(ps).rounded_rectangle((32, 236, 80, 284), 12, fill=(255, 214, 10))
        batt_icon(ps, 56, 260, (30, 30, 30), w=28, h=14, lw=2)
        txt(ps, (96, 260), "低電力モード", 20, INK, anchor="lm")
        if k["pick"] - 0.35 <= t < k["pick"] + 0.1: finger(ps, BW / 2, 260)
    else:
        for i, nm in enumerate(["アラーム", "カメラ", "計算機", "ダークモード"]):
            y = 200 + i * 74
            rr(ps, (16, y, BW - 16, y + 62), 14, WHITE)
            txt(ps, (34, y + 31), nm, 18, INK, bold=False, anchor="lm")
    return ps

def added(t, k):
    ps = cc_base(t, k, True)
    glow = clamp(1 - (t - k["added"]) / 0.8)
    tile(ps, LP_X, LP_Y, on=True, glow=max(glow, 0.35), label="低電力モード", icon="batt")
    rra(ps, (60, 680, BW - 60, 736), 28, (52, 199, 89, 235))
    txt(ps, (BW / 2, 708), "追加できた！", 20, WHITE, anchor="mm")
    return ps

def screen(t, k):
    if t >= k["added"]: return added(t, k)
    if t >= k["gallery"]: return gallery(t, k)
    if t >= k["edit"]: return edit_screen(t, k)
    return cc_screen(t, k)

def SCREEN(t, T): return screen(t, times(T))

def draw_body(c, t, T): pass

def draw_hook_art(ly, t): pass

def sfx(T):
    k = times(T)
    return [("whoosh", k["cc"]), ("click", k["tap"]), ("ding", k["tap"] + 0.15), ("pop", k["edit"]), ("click", k["plus"]),
            ("click", k["add"]), ("pop", k["gallery"]), ("click", k["pick"]), ("ding", k["added"])]

def stills(T):
    k = times(T)
    return [T.at["b1"] + 0.5, k["tap"] + 0.4, k["plus"] + 0.5, k["add"] - 0.2, k["type0"] + 0.9, k["added"] + 0.3]
