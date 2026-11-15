# 11/16 19:00 ニュース系（plan n1）：iOS 27.2でSiri AIが日本語に。アップデートだけでは使えない（28秒2ネタ・画面録画風・損失回避）
# 出典：Yahoo!ニュース/CNET Japan（iOS 27.2 Siri AI日本語対応）、スーログ（設定手順・対応機種）— 2026-11-15確認
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="news_202611", title="iPhoneニュース", spoken="iPhoneニュース",
              hook_split=("iPhone", "ニュース"), total=5, offset=0)
TITLE = "iOS 27.2にしたのにSiri AIが使えない人へ… #Shorts"
NUM, SLUG = 1, "siri_ai"
NEXT = "次もiOS 27.2"
SCREEN_CROP = (0, 40, 400, 760)
DURATION, END_CARD = 28.0, False
TAGS = {"length": "28秒2ネタ", "layout": "画面録画風", "hook_type": "煽り型", "title_type": "…止め", "topic_kind": "ニュース"}
LAYOUT, FOCUS_Y, CAPTION_Y = "rec", 400, 1260
HOOK = "iOS 27.2にしたのに\n{Siri AIが使えない}？"
HOOK_SPOKEN = "iOS 27.2にしたのに、Siri AIが使えない人へ！"
TELOPS = [("b1", "1つ目\n[Siriの言語を日本語に]"), ("b2", "設定 → Siri →\n[言語：日本語]"),
          ("b3", "2つ目\n[Apple Intelligence]をオン"), ("b4", "Wi-Fi＋充電で\n[ダウンロード待ち]")]
ACTIONS = [("b1", "b2", "アップデートだけでは使えない"), ("b2", "b3", "言語をタップ → 日本語"),
           ("b3", "b4", "オン → 順番待ちに参加"), ("b4", "cta", "対応：iPhone 15 Pro以降")]
BODY = [
    ("b1", "実はアップデートしただけでは、まだ使えません。1つ目、Siriの言語を日本語にする。", 0.2),
    ("b2", "設定のSiriで、言語を日本語に。", 0.25),
    ("b3", "2つ目、Apple Intelligenceをオンにして、日本語ベータの順番待ちに参加。", 0.2),
    ("b4", "Wi-Fiと充電をつないで、ダウンロードが終われば使えます！対応はiPhone 15 Pro以降です。", 0.0),
]
BODY_HOLD = 0.5
CTA = dict(lines=[("使えた人は", WHITE, 100), ("コメントで教えて！", YEL, 100)], spoken="使えた人はコメントで教えて！",
           chip="iPhone 15 Pro以降")

BW, BH = 400, 860

def finger(ps, x, y):
    fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((x - 30, y - 30, x + 30, y + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))

def page(back, title):
    ps = Image.new("RGBA", (BW, BH), (242, 242, 247, 255))
    txt(ps, (56, 36), "9:41", 22, INK, anchor="lm")
    txt(ps, (24, 84), "‹ " + back, 18, BLUE, bold=False, anchor="lm")
    txt(ps, (24, 128), title, 26, INK, anchor="lm")
    return ps

def row(ps, y, hi):
    rr(ps, (16, y, BW - 16, y + 56), 12, (255, 236, 150) if hi else WHITE)

def pill(ps, text, col):
    rra(ps, (50, 640, BW - 50, 696), 28, col + (235,))
    txt(ps, (BW / 2, 668), text, 18, WHITE, anchor="mm")

def language(t, T):
    a = T.at
    tap, pick = a["b2"] + 0.6, a["b2"] + 1.7
    if t < pick - 0.6:
        ps = page("設定", "Siri")
        rows = [("Siriに話しかける", "“Siri”"), ("言語", "English"), ("Siriの声", "声1"), ("Siriの応答", "")]
        for i, (k, v) in enumerate(rows):
            y = 170 + i * 62
            row(ps, y, i == 1 and t >= a["b1"])
            txt(ps, (34, y + 28), k, 18, INK, bold=i == 1, anchor="lm")
            txt(ps, (BW - 40, y + 28), v + "  ›", 16, (255, 59, 48) if i == 1 else GRAY, bold=i == 1, anchor="rm")
        if tap - 0.35 <= t < tap + 0.1: finger(ps, BW / 2, 170 + 62 + 28)
        if t < a["b1"]:
            pill(ps, "アップデートしたのに使えない…", (255, 59, 48))
        return ps
    ps = page("Siri", "言語")
    langs = ["English (US)", "日本語", "Español", "Français"]
    sel = 1 if t >= pick else 0
    for i, l in enumerate(langs):
        y = 170 + i * 62
        row(ps, y, i == 1 and t >= pick - 0.3)
        txt(ps, (34, y + 28), l, 18, INK, bold=i == sel, anchor="lm")
        if i == sel: check(ps, BW - 64, y + 16, 22, BLUE, 4)
    if pick - 0.35 <= t < pick + 0.1: finger(ps, BW / 2, 170 + 62 + 28)
    if t >= pick + 0.3: pill(ps, "Siriの言語を日本語にした！", (52, 199, 89))
    return ps

def intelligence(t, T):
    a = T.at
    on_at, join_at, dl0 = a["b3"] + 1.6, a["b3"] + 2.6, a["b4"]
    ps = page("設定", "Apple IntelligenceとSiri")
    row(ps, 170, t >= on_at - 0.3)
    txt(ps, (34, 198), "Apple Intelligence", 18, INK, bold=True, anchor="lm")
    toggle(ps, BW - 86, 180, t >= on_at)
    if on_at - 0.35 <= t < on_at + 0.1: finger(ps, BW - 60, 198)
    if t >= on_at + 0.2:
        hi = t >= join_at - 0.3
        rr(ps, (16, 250, BW - 16, 306), 12, (255, 236, 150) if hi else WHITE)
        txt(ps, (BW / 2, 278), "Siri AI（ベータ）の順番待ちに参加", 16, BLUE, bold=True, anchor="mm")
        if join_at - 0.35 <= t < join_at + 0.1: finger(ps, BW / 2, 278)
    if t >= dl0:
        p = clamp((t - dl0) / 3.5)
        rr(ps, (16, 330, BW - 16, 450), 12, WHITE)
        txt(ps, (34, 360), "モデルをダウンロード中…", 17, INK, anchor="lm")
        d = ImageDraw.Draw(ps)
        d.rounded_rectangle((34, 384, BW - 34, 400), 8, fill=(225, 225, 232))
        d.rounded_rectangle((34, 384, 34 + (BW - 68) * p, 400), 8, fill=BLUE)
        txt(ps, (34, 428), "Wi-Fiと電源に接続してください", 14, GRAY, bold=False, anchor="lm")
        if p >= 1: pill(ps, "これでSiri AIが使える！", (52, 199, 89))
    return ps

def SCREEN(t, T):
    return intelligence(t, T) if t >= T.at["b3"] else language(t, T)

def draw_body(c, t, T): pass

def draw_hook_art(ly, t): pass

def sfx(T):
    a = T.at
    return [("pop", a["b1"]), ("click", a["b2"] + 0.6), ("click", a["b2"] + 1.7), ("pop", a["b3"]), ("click", a["b3"] + 1.6),
            ("click", a["b3"] + 2.6), ("ding", a["b4"] + 3.5)]

def stills(T):
    a = T.at
    return [0.8, a["b1"] + 0.6, a["b2"] + 2.2, a["b3"] + 2.0, a["b4"] + 1.5, a["b4"] + 3.8, a["cta"] + 0.8]
