# 11/23 06:00 13秒1ネタ（日常操作の時短・plan t1）スペースキー長押しでカーソル移動（画面録画風・劇的時短）
# 1フレーム目＝本物そっくりのLINE風入力欄＋キーボード、打ち間違いが赤（11/18 スワイプ率ルール）
# 根拠：iOS キーボードのスペースバーを長押し→トラックパッドモードでカーソルを自由に移動（iOS 12以降）
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="b20261122_second", title="iPhone隠し神機能", spoken="iPhone隠し、かみ機能",
              hook_split=("iPhone", "隠し神機能"), total=5, offset=10)
TITLE = "文字の打ち直し、まだ1文字ずつ消してる人へ… #Shorts"
NUM, SLUG = 2, "cursor_space"
NEXT = "次も時短ワザ"
SCREEN_CROP = (0, 40, 400, 760)
DURATION, END_CARD = 14.0, False
TAGS = {"length": "13秒1ネタ", "layout": "画面録画風", "hook_type": "即効型", "title_type": "…止め", "topic_kind": "時短",
        "first_frame": "本物の画面＋自分ごと"}
LAYOUT, FOCUS_Y, CAPTION_Y = "rec", 400, 1260
HOOK = "文字の打ち直し\n{1文字ずつ}消してない？"
HOOK_SPOKEN = "文字の打ち直し、まだ1文字ずつ消してる人へ！"
TELOPS = [("b1", "[スペースキー]を\n長押し"), ("b2", "キーボードが\n{トラックパッド}に"),
          ("b3", "指を動かして\n[カーソル移動]"), ("b4", "直したい所だけ\n[すぐ直せる]")]
ACTIONS = [("b1", "b2", "スペースを長押し"), ("b2", "b3", "文字が消えたらOK"),
           ("b3", "b4", "そのまま指をスライド"), ("b4", "cta", "全部消さなくていい")]
BODY = [
    ("b1", "スペースキーを長押しすると、", 0.1),
    ("b2", "キーボードがトラックパッドに。", 0.1),
    ("b3", "指を動かせば、カーソルが自由に動いて、", 0.1),
    ("b4", "直したい所だけ直せます！", 0.0),
]
BODY_HOLD = 0.4
CTA = dict(lines=[("知ってた人は", WHITE, 100), ("コメントで教えて！", YEL, 100)], spoken="知ってた人はコメントで！",
           chip="フォローで毎日1つ")

BW, BH = 400, 860
BEFORE, AFTER, WRONG = "明日10時に新宿駅の東口でね", "明日10時に渋谷駅の東口でね", (6, 8)
KEYS = ["あかさ", "たなは", "まやら"]

def finger(ps, x, y):
    fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((x - 30, y - 30, x + 30, y + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))

def pill(ps, text, col):
    rra(ps, (40, 640, BW - 40, 696), 28, col + (235,))
    txt(ps, (BW / 2, 668), text, 17, WHITE, anchor="mm")

def SCREEN(t, T):
    a = T.at
    ps = Image.new("RGBA", (BW, BH), (140, 170, 200, 255))
    d = ImageDraw.Draw(ps)
    txt(ps, (56, 36), "9:41", 22, WHITE, anchor="lm")
    txt(ps, (BW / 2, 84), "けんた", 20, WHITE, anchor="mm")
    rr(ps, (150, 110, BW - 16, 150), 18, (130, 230, 120))
    txt(ps, (BW - 28, 130), "明日どこで待ち合わせる？", 14, INK, bold=False, anchor="rm")
    # input field
    fixed = t >= a["b4"] + 0.3
    text = AFTER if fixed else BEFORE
    rr(ps, (12, 176, BW - 12, 226), 20, WHITE)
    x0 = 28
    # cursor position: end of text until b3, then slides to after the wrong word
    import math
    full = len(text)
    if t < a["b3"]: pos = full
    elif t < a["b3"] + 1.2: pos = int(full - (full - WRONG[1]) * clamp((t - a["b3"]) / 1.2))
    else: pos = WRONG[1]
    if fixed: pos = WRONG[1]
    cw = 14.5
    for i, ch in enumerate(text):
        bad = (not fixed) and WRONG[0] <= i < WRONG[1]
        good = fixed and WRONG[0] <= i < WRONG[1]
        if bad: d.rectangle((x0 + i * cw - 1, 188, x0 + (i + 1) * cw, 214), fill=(255, 210, 205))
        if good: d.rectangle((x0 + i * cw - 1, 188, x0 + (i + 1) * cw, 214), fill=(200, 245, 205))
        txt(ps, (x0 + i * cw + cw / 2, 201), ch, 14, (255, 59, 48) if bad else INK, bold=bad or good, anchor="mm")
    if int(t * 2.5) % 2 == 0 or a["b3"] <= t < a["b4"]:
        cx = x0 + pos * cw
        d.rectangle((cx - 1, 186, cx + 2, 216), fill=BLUE)
    # keyboard
    track = a["b1"] + 0.6 <= t < a["b4"] + 0.2
    d.rectangle((0, 240, BW, 470), fill=(210, 212, 218))
    for r, row in enumerate(KEYS):
        for c, k in enumerate(row):
            x, y = 70 + c * 90, 252 + r * 52
            rr(ps, (x - 40, y, x + 40, y + 44), 8, (225, 227, 232) if track else WHITE)
            if not track: txt(ps, (x + 0, y + 22), k, 20, INK, bold=False, anchor="mm")
    sp = (90, 412, 310, 456)
    rr(ps, sp, 8, (225, 227, 232) if track else (255, 236, 150) if t >= a["b1"] - 0.2 else WHITE)
    if not track: txt(ps, (200, 434), "空白", 16, INK, bold=False, anchor="mm")
    rr(ps, (322, 412, 386, 456), 8, (255, 220, 215) if t < a["b1"] else (172, 176, 186))
    txt(ps, (354, 434), "削除", 14, (255, 59, 48) if t < a["b1"] else INK, anchor="mm")
    # finger
    if a["b1"] - 0.2 <= t < a["b3"]: finger(ps, 200, 434)
    elif a["b3"] <= t < a["b4"] + 0.2:
        fx = 200 - 120 * clamp((t - a["b3"]) / 1.2)
        finger(ps, fx, 380)
    if t < a["b1"]: pill(ps, "1文字ずつ消すと時間がかかる…", (255, 59, 48))
    elif t < a["b3"]: pill(ps, "スペースを長押し", (10, 132, 255))
    elif t < a["b4"]: pill(ps, "指でスーッとカーソル移動", (10, 132, 255))
    else: pill(ps, "直したい所だけ直せた！", (52, 199, 89))
    return ps

def draw_body(c, t, T): pass

def draw_hook_art(ly, t): pass

def sfx(T):
    a = T.at
    return [("pop", a["b1"]), ("click", a["b1"] + 0.6), ("whoosh", a["b3"]), ("ding", a["b4"] + 0.3)]

def stills(T):
    a = T.at
    return [0.05, 0.8, a["b1"] + 0.8, a["b3"] + 0.6, a["b3"] + 1.4, a["b4"] + 0.6, a["cta"] + 0.6]
