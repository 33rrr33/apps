# 11/16 19:00（ヒット後の関連ネタ：バッテリー系）Appのバックグラウンド更新を、使わないアプリだけオフ（v3・画面録画風・13秒・即効型）
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="w20261109_second", title="iPhone隠し神機能", spoken="iPhone隠し、かみ機能",
              hook_split=("iPhone", "隠し神機能"), total=5, offset=5)
TITLE = "電池がすぐ減る人、この設定オンのままかも… #Shorts"
NUM, SLUG = 5, "bg_refresh"
NEXT = "次もバッテリーの話"
SCREEN_CROP = (0, 40, 400, 760)
DURATION, END_CARD = 13.5, False
TAGS = {"length": "13秒1ネタ", "layout": "画面録画風", "hook_type": "即効型", "title_type": "…止め", "topic_kind": "バッテリー"}
LAYOUT, FOCUS_Y, CAPTION_Y = "rec", 400, 1260
HOOK = "電池が{すぐ減る}人\nこれオフにして"
HOOK_SPOKEN = "電池がすぐ減る人、これオフにして！"
TELOPS = [("b1", "見てない間も\n{裏で電池を使う}"), ("b2", "設定 → 一般 →\n[バックグラウンド更新]"),
          ("b3", "使わないアプリを\n[オフ]にするだけ"), ("b4", "よく使うアプリは\n[オンのまま]でOK")]
ACTIONS = [("b1", "b2", "アプリが裏で動いている"), ("b2", "b3", "一般 → Appのバックグラウンド更新"),
           ("b3", "b4", "使わないアプリをオフ"), ("b4", "cta", "よく使うアプリはそのまま")]
BODY = [
    ("b1", "アプリが裏で、電池を使ってます。", 0.1),
    ("b2", "一般の、バックグラウンド更新で、", 0.1),
    ("b3", "使わないアプリをオフ。", 0.1),
    ("b4", "よく使うアプリは、そのままでOK！", 0.0),
]
BODY_HOLD = 0.4
CTA = dict(lines=[("使わないアプリは", WHITE, 100), ("オフにしよう！", YEL, 120)], spoken="フォローで毎日1つ紹介！",
           chip="フォローで毎日1つ")

PART = dict(
    title="Appのバックグラウンド更新を見直す",
    intro="電池の減りが早いと感じたら、アプリが裏で動いていないかチェックしましょう。",
    steps=[
        ("裏で動くアプリ", "アプリは、使っていない間も、裏で新しい情報を読み込んで電池を使うことがあります。", ("body", "b2")),
        ("設定 → 一般", "設定アプリの一般から、Appのバックグラウンド更新を開きます。", ("b2", "b3")),
        ("使わないアプリをオフ", "あまり使わないアプリのスイッチをオフにします。", ("b3", "b4")),
        ("よく使うアプリはそのまま", "よく使うアプリは、オンのままにしておけば、開いた時にすぐ最新になります。", ("b4", "cta")),
    ],
    outro="使わないアプリだけオフにして、電池を長持ちさせましょう。",
)

BW, BH = 400, 860
APPS = [("ゲーム", (255, 59, 48)), ("ショッピング", (255, 149, 0)), ("ニュース", (88, 86, 214)),
        ("LINE", (52, 199, 89)), ("天気", (10, 132, 255))]
OFF = (0, 1, 2)                       # the apps we switch off

def times(T):
    return dict(drain=T.at["b1"] + 0.2, general=T.at["b2"], tap=T.at["b2"] + 1.0, page=T.at["b2"] + 1.3,
                off0=T.at["b3"] + 0.2, keep=T.at["b4"] + 0.2)

def finger(ps, x, y):
    fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((x - 30, y - 30, x + 30, y + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))

def icon(ps, x, y, col, s=34):
    ImageDraw.Draw(ps).rounded_rectangle((x, y, x + s, y + s), 9, fill=col)

def lock_drain(t, k):
    ps = grad(BW, BH, (20, 24, 60), (60, 30, 90))
    txt(ps, (BW / 2, 120), "0:24", 64, WHITE, anchor="mm")
    p = clamp((t - k["drain"]) / 1.2)
    pct = int(80 - 30 * p)
    d = ImageDraw.Draw(ps)
    d.rounded_rectangle((BW / 2 - 90, 190, BW / 2 + 90, 270), 18, outline=WHITE, width=5)
    d.rounded_rectangle((BW / 2 + 92, 216, BW / 2 + 102, 244), 3, fill=WHITE)
    d.rounded_rectangle((BW / 2 - 80, 200, BW / 2 - 80 + 160 * pct / 100, 260), 10, fill=(255, 59, 48) if pct < 60 else (48, 209, 88))
    txt(ps, (BW / 2, 300), f"{pct}%", 30, WHITE, anchor="mm")
    for i, (nm, col) in enumerate(APPS[:3]):
        y = 318 + i * 46
        a = clamp((t - k["drain"] - 0.25 * i) / 0.3)
        if a > 0:
            rra(ps, (40, y, BW - 40, y + 42), 14, (255, 255, 255, int(40 * a)))
            icon(ps, 52, y + 5, col, 32)
            txt(ps, (96, y + 21), f"{nm}  裏で更新中…", 16, (230, 230, 235), bold=False, anchor="lm")
    return ps

def general(t, k):
    ps = Image.new("RGBA", (BW, BH), (242, 242, 247, 255))
    txt(ps, (56, 36), "9:41", 22, INK, anchor="lm")
    txt(ps, (24, 84), "‹ 設定", 20, BLUE, bold=False, anchor="lm")
    txt(ps, (24, 132), "一般", 34, INK, anchor="lm")
    rows = ["情報", "ソフトウェアアップデート", "AirDrop", "Appのバックグラウンド更新", "日付と時刻"]
    for i, r in enumerate(rows):
        y = 176 + i * 62
        hi = i == 3 and t >= k["tap"] - 0.35
        rr(ps, (16, y, BW - 16, y + 56), 12, (255, 236, 150) if hi else WHITE)
        txt(ps, (34, y + 28), r, 18, INK, bold=i == 3, anchor="lm")
        txt(ps, (BW - 34, y + 28), "›", 24, GRAY, anchor="rm")
    if k["tap"] - 0.35 <= t < k["tap"] + 0.1: finger(ps, BW / 2, 176 + 3 * 62 + 28)
    return ps

def refresh(t, k):
    ps = Image.new("RGBA", (BW, BH), (242, 242, 247, 255))
    txt(ps, (56, 36), "9:41", 22, INK, anchor="lm")
    txt(ps, (24, 84), "‹ 一般", 20, BLUE, bold=False, anchor="lm")
    txt(ps, (24, 128), "Appのバックグラウンド更新", 24, INK, anchor="lm")
    for i, (nm, col) in enumerate(APPS):
        y = 166 + i * 60
        at = k["off0"] + 0.4 * OFF.index(i) if i in OFF else None
        off = at is not None and t >= at
        keep = i not in OFF and t >= k["keep"]
        rr(ps, (16, y, BW - 16, y + 54), 12, (255, 236, 150) if (off or keep) else WHITE)
        icon(ps, 30, y + 10, col)
        txt(ps, (78, y + 27), nm, 18, INK, bold=False, anchor="lm")
        toggle(ps, BW - 86, y + 8, not off)
        if at is not None and at - 0.3 <= t < at + 0.1: finger(ps, BW - 60, y + 27)
    if t >= k["keep"]:
        rra(ps, (40, 640, BW - 40, 696), 28, (52, 199, 89, 235))
        txt(ps, (BW / 2, 668), "使わないアプリだけオフ！", 18, WHITE, anchor="mm")
    return ps

def screen(t, k):
    if t >= k["page"]: return refresh(t, k)
    if t >= k["general"]: return general(t, k)
    return lock_drain(t, k)

def SCREEN(t, T): return screen(t, times(T))

def draw_body(c, t, T): pass

def draw_hook_art(ly, t): pass

def sfx(T):
    k = times(T)
    return [("pop", k["drain"]), ("click", k["tap"]), ("pop", k["page"]), ("click", k["off0"]), ("click", k["off0"] + 0.55),
            ("click", k["off0"] + 1.1), ("ding", k["keep"])]

def stills(T):
    k = times(T)
    return [0.8, k["drain"] + 1.0, k["tap"] - 0.1, k["off0"] + 1.3, k["keep"] + 0.4]
