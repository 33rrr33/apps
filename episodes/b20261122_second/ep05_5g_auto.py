# 11/26 12:00 13秒1ネタ（電池・plan w2）5Gオン→5Gオートで電池長持ち（画面録画風・損失回避）
# 1フレーム目＝本物そっくりの「音声通話とデータ」画面で「5Gオン」にチェック、電池残量が赤（11/18 スワイプ率ルール）
# 根拠：Apple サポート「iPhoneで5Gを使う」— 5Gオート：5Gの速度がそれほど必要ないときは自動的にLTEに切り替えてバッテリーを節約。
#       5Gオン：利用できる場合は常に5Gを使用（バッテリー消費が増えることがある）。設定→モバイル通信→通信のオプション→音声通話とデータ
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="b20261122_second", title="iPhone隠し神機能", spoken="iPhone隠し、かみ機能",
              hook_split=("iPhone", "隠し神機能"), total=5, offset=10)
TITLE = "5Gを常にオンにしてる人、電池が… #Shorts"
NUM, SLUG = 5, "5g_auto"
NEXT = "次も電池の話"
SCREEN_CROP = (0, 40, 400, 760)
DURATION, END_CARD = 14.0, False
TAGS = {"length": "13秒1ネタ", "layout": "画面録画風", "hook_type": "煽り型", "title_type": "…止め", "topic_kind": "バッテリー",
        "first_frame": "本物の画面＋自分ごと"}
LAYOUT, FOCUS_Y, CAPTION_Y = "rec", 400, 1260
HOOK = "5Gを{常にオン}\nにしてない？"
HOOK_SPOKEN = "5Gを常にオンにしてる人、電池が減りやすいです！"
TELOPS = [("b1", "設定 → モバイル通信 →\n[通信のオプション]"), ("b2", "音声通話とデータを\n[5Gオート]に"),
          ("b3", "必要な時だけ\n{5Gを使う}")]
ACTIONS = [("b1", "b2", "5Gオンのままだと電池を使いやすい"), ("b2", "b3", "5Gオートをタップ"),
           ("b3", "cta", "速さはほぼそのまま")]
BODY = [
    ("b1", "モバイル通信の、通信のオプションで、", 0.1),
    ("b2", "5Gオートを選ぶだけ。", 0.1),
    ("b3", "必要な時だけ5Gを使って、電池を節約します！", 0.0),
]
BODY_HOLD = 0.4
CTA = dict(lines=[("5Gオンだった人は", WHITE, 96), ("コメントで教えて！", YEL, 100)], spoken="オンだった人はコメントで！",
           chip="フォローで毎日1つ")

BW, BH = 400, 860

def finger(ps, x, y):
    fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((x - 30, y - 30, x + 30, y + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))

def pill(ps, text, col):
    rra(ps, (40, 640, BW - 40, 696), 28, col + (235,))
    txt(ps, (BW / 2, 668), text, 17, WHITE, anchor="mm")

def SCREEN(t, T):
    a = T.at
    pick = a["b2"] + 0.6
    auto = t >= pick
    ps = Image.new("RGBA", (BW, BH), (242, 242, 247, 255))
    d = ImageDraw.Draw(ps)
    txt(ps, (56, 84), "9:41", 24, INK, anchor="lm")
    txt(ps, (BW - 132, 84), "5G", 20, INK, anchor="mm")
    pct = 12 if not auto else 12
    d.rounded_rectangle((BW - 100, 72, BW - 56, 96), 6, outline=INK, width=2)
    d.rectangle((BW - 97, 75, BW - 90, 93), fill=(255, 59, 48) if not auto else (52, 199, 89))
    txt(ps, (BW - 28, 84), f"{pct}%", 15, (255, 59, 48) if not auto else INK, anchor="mm")
    txt(ps, (24, 128), "‹ 通信のオプション", 18, BLUE, bold=False, anchor="lm")
    txt(ps, (24, 170), "音声通話とデータ", 26, INK, anchor="lm")
    opts = ["5Gオン", "5Gオート", "4G"]
    sel = 1 if auto else 0
    for i, o in enumerate(opts):
        y = 204 + i * 62
        hi = (i == 0 and not auto and t >= 0.0) or (i == 1 and t >= pick - 0.3)
        rr(ps, (16, y, BW - 16, y + 56), 12, (255, 236, 150) if hi else WHITE)
        txt(ps, (34, y + 28), o, 18, INK, bold=i == sel, anchor="lm")
        if i == sel: check(ps, BW - 60, y + 16, 22, BLUE, 4)
    txt(ps, (24, 410), "5Gオート：5Gの速度が必要ないときは", 13, GRAY, bold=False, anchor="lm")
    txt(ps, (24, 432), "自動でLTEに切り替えてバッテリーを節約", 13, GRAY, bold=False, anchor="lm")
    if pick - 0.35 <= t < pick + 0.1: finger(ps, BW / 2, 204 + 62 + 28)
    if t < a["b1"]: pill(ps, "5Gオンのまま＝電池を使いやすい…", (255, 59, 48))
    elif not auto: pill(ps, "モバイル通信 → 通信のオプション", (10, 132, 255))
    else: pill(ps, "5Gオートで電池を節約！", (52, 199, 89))
    return ps

def draw_body(c, t, T): pass

def draw_hook_art(ly, t): pass

def sfx(T):
    a = T.at
    return [("ding", 0.3), ("pop", a["b1"]), ("click", a["b2"] + 0.6), ("ding", a["b3"])]

def stills(T):
    a = T.at
    return [0.05, 0.8, a["b1"] + 0.5, a["b2"] + 0.9, a["b3"] + 0.5, a["cta"] + 0.6]
