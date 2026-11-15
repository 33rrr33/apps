# 11/18 12:00（ヒット系統：バッテリー・plan b1）充電しながらゲーム・動画は熱で電池が傷みやすい（28秒2ネタ・画面録画風・損失回避）
# 根拠：Apple公式「バッテリーの性能を最大限に引き出す」— 高温を避ける／充電中に熱くなる場合はケースを外す
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="b20261117_first", title="iPhone爆速神操作", spoken="iPhone爆速、かみ操作",
              hook_split=("iPhone", "爆速神操作"), total=5, offset=10)
TITLE = "充電しながらゲームしてる人、電池が… #Shorts"
NUM, SLUG = 2, "charge_heat"
NEXT = "次も電池の話"
SCREEN_CROP = (0, 40, 400, 760)
DURATION, END_CARD = 27.0, False
TAGS = {"length": "28秒2ネタ", "layout": "画面録画風", "hook_type": "煽り型", "title_type": "…止め", "topic_kind": "バッテリー"}
LAYOUT, FOCUS_Y, CAPTION_Y = "rec", 400, 1260
HOOK = "充電しながら\n{ゲームしてない}？"
HOOK_SPOKEN = "充電しながら、ゲームや動画を見てる人へ！"
TELOPS = [("b1", "1つ目\n{充電中の重いアプリ}"), ("b2", "熱がこもって\n{電池が傷みやすい}"),
          ("b3", "2つ目\n充電中に熱いなら[ケースを外す]"), ("b4", "熱いときは\n[充電してから]遊ぶ")]
ACTIONS = [("b1", "b2", "充電しながらゲーム・動画"), ("b2", "b3", "高温は電池の大敵"),
           ("b3", "b4", "ケースを外して熱を逃がす"), ("b4", "cta", "Appleも高温に注意と案内")]
BODY = [
    ("b1", "毎日やってる人、多いです。1つ目、充電しながらゲームや動画。", 0.2),
    ("b2", "充電の熱とアプリの熱が重なって、電池が傷みやすくなります。Appleも、高温には注意するよう案内しています。", 0.3),
    ("b3", "2つ目、充電中に熱くなるなら、ケースを外して熱を逃がす。", 0.15),
    ("b4", "熱いときは、充電が終わってから遊ぶのがおすすめです。", 0.0),
]
BODY_HOLD = 0.5
CTA = dict(lines=[("やってた人は", WHITE, 100), ("コメントで教えて！", YEL, 100)], spoken="やってた人はコメントで教えて！",
           chip="フォローで毎日1つ")

BW, BH = 400, 860

def finger(ps, x, y):
    fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((x - 30, y - 30, x + 30, y + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))

def pill(ps, text, col):
    rra(ps, (40, 640, BW - 40, 696), 28, col + (235,))
    txt(ps, (BW / 2, 668), text, 18, WHITE, anchor="mm")

def thermo(ps, cx, cy, p):
    d = ImageDraw.Draw(ps)
    d.rounded_rectangle((cx - 14, cy - 110, cx + 14, cy + 40), 14, fill=(235, 235, 240))
    d.ellipse((cx - 30, cy + 20, cx + 30, cy + 80), fill=(255, 59, 48))
    h = 140 * p
    d.rounded_rectangle((cx - 8, cy + 30 - h, cx + 8, cy + 40), 8, fill=(255, 59, 48))

def game(t, T):
    a = T.at
    ps = grad(BW, BH, (20, 120, 90), (10, 50, 40))
    d = ImageDraw.Draw(ps)
    txt(ps, (56, 36), "9:41", 22, WHITE, anchor="lm")
    d.rounded_rectangle((BW - 92, 26, BW - 54, 46), 5, outline=WHITE, width=2)
    d.rectangle((BW - 89, 29, BW - 66, 43), fill=(52, 199, 89))
    txt(ps, (BW - 40, 36), "⚡", 16, (255, 214, 10), anchor="mm")
    for i in range(5):                                        # simple "game" blocks
        x = 40 + i * 66; y = 170 + (i % 2) * 60
        d.rounded_rectangle((x, y, x + 50, y + 50), 10, fill=[(255, 159, 10), (10, 132, 255), (255, 59, 48), (175, 82, 222), (255, 214, 10)][i])
    txt(ps, (BW / 2, 120), "SCORE 12,480", 22, WHITE, anchor="mm")
    p = clamp((t - a["b2"]) / 2.5) if t >= a["b2"] else 0.15
    thermo(ps, BW - 60, 300, p)
    txt(ps, (60, 330), "充電中", 18, (255, 214, 10), anchor="lm")
    d.line((60, 350, 60, 400), fill=WHITE, width=6)          # cable
    if t >= a["b2"] + 0.6:
        rra(ps, (30, 410, BW - 30, 462), 14, (40, 40, 46, 240))
        txt(ps, (BW / 2, 436), "iPhoneが熱くなっています", 16, WHITE, anchor="mm")
        pill(ps, "熱は電池の大敵…", (255, 59, 48))
    return ps

def case_off(t, T):
    a = T.at
    ps = Image.new("RGBA", (BW, BH), (242, 242, 247, 255))
    txt(ps, (56, 36), "9:41", 22, INK, anchor="lm")
    p = ease_inout((t - a["b3"] - 1.2) / 1.0) if t >= a["b3"] + 1.2 else 0
    d = ImageDraw.Draw(ps)
    # phone
    d.rounded_rectangle((140, 110, 260, 400), 28, fill=(30, 30, 34))
    d.rounded_rectangle((150, 120, 250, 390), 22, fill=(60, 60, 70))
    # case sliding off
    off = int(220 * p)
    d.rounded_rectangle((128 + off, 98, 272 + off, 412), 34, outline=(255, 149, 0), width=12)
    if p > 0.6:
        for k in range(3):
            x = 160 + k * 40
            d.arc((x - 12, 60, x + 12, 110), 200, 340, fill=(255, 59, 48), width=4)
        txt(ps, (BW / 2, 452), "熱を逃がす", 22, INK, anchor="mm")
        if t < a["b4"]: pill(ps, "ケースを外して熱を逃がす", (255, 149, 0))
    if a["b3"] + 0.9 <= t < a["b3"] + 1.4: finger(ps, 280, 270)
    if t >= a["b4"]:
        pill(ps, "熱いときは充電が終わってから遊ぶ", (52, 199, 89))
    return ps

def SCREEN(t, T):
    return case_off(t, T) if t >= T.at["b3"] else game(t, T)

def draw_body(c, t, T): pass

def draw_hook_art(ly, t): pass

def sfx(T):
    a = T.at
    return [("pop", a["b1"]), ("ding", a["b2"] + 0.6), ("pop", a["b3"]), ("whoosh", a["b3"] + 1.2), ("ding", a["b4"])]

def stills(T):
    a = T.at
    return [0.8, a["b1"] + 0.5, a["b2"] + 1.5, a["b3"] + 0.5, a["b3"] + 2.4, a["b4"] + 1.0, a["cta"] + 0.8]
