# 11/29 06:00 13秒1ネタ（プライバシー・plan w6）写真を送る時「オプション→位置情報」をオフ（画面録画風・損失回避）
# 11/25ルール：指示語なし（『家の場所』と具体的に）＋冒頭は主役（写真の撮影場所＝自宅のピン）を超拡大＋赤丸
# 根拠：iOS 写真 → 共有 → 上部「オプション」→「位置情報」をオフにすると撮影場所の情報を含めずに送れる（iOS 13以降）
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="b20261127_first", title="iPhone爆速神操作", spoken="iPhone爆速、かみ操作",
              hook_split=("iPhone", "爆速神操作"), total=5, offset=15)
TITLE = "写真を送ると家の場所がバレる人へ… #Shorts"
NUM, SLUG = 3, "photo_location"
NEXT = "次も守る設定"
SCREEN_CROP = (0, 40, 400, 760)
DURATION, END_CARD = 14.5, False
TAGS = {"length": "13秒1ネタ", "layout": "画面録画風", "hook_type": "疑問型", "title_type": "…止め", "topic_kind": "危険設定",
        "first_frame": "超拡大＋赤丸"}
LAYOUT, FOCUS_Y, CAPTION_Y = "rec", 400, 1260
HOOK = "写真を送ると\n{家の場所}がバレる？"
HOOK_SPOKEN = "写真を送ると、家の場所がバレてるかもしれません！"
TELOPS = [("b1", "写真には\n{撮った場所}が入ってる"), ("b2", "共有 →\n上の[オプション]"),
          ("b3", "[位置情報]を\nオフにして送る")]
ACTIONS = [("b1", "b2", "写真の情報に地図が出る"), ("b2", "b3", "共有ボタン → オプション"),
           ("b3", "cta", "これで場所は送られない")]
BODY = [
    ("b1", "写真には、撮った場所が記録されてます。", 0.1),
    ("b2", "送る時は、共有の、オプションを開いて、", 0.1),
    ("b3", "位置情報をオフにするだけ！", 0.0),
]
BODY_HOLD = 0.4
CTA = dict(lines=[("知らなかった人は", WHITE, 96), ("コメントで教えて！", YEL, 100)], spoken="知らなかった人はコメントで！",
           chip="家族のiPhoneにも")

BW, BH = 400, 860

def finger(ps, x, y):
    fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((x - 30, y - 30, x + 30, y + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))

def pill(ps, text, col):
    rra(ps, (40, 640, BW - 40, 696), 28, col + (235,))
    txt(ps, (BW / 2, 668), text, 17, WHITE, anchor="mm")

def mapcard(ps, box, big):
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(ps)
    d.rounded_rectangle(box, 16, fill=(214, 232, 214))
    for k in range(5):
        d.line((x0, y0 + 20 + k * (y1 - y0) / 5, x1, y0 + 10 + k * (y1 - y0) / 5), fill=(250, 250, 250), width=6 if big else 3)
    d.line((x0 + (x1 - x0) * 0.6, y0, x0 + (x1 - x0) * 0.4, y1), fill=(250, 250, 250), width=8 if big else 4)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    r = 26 if big else 12
    d.ellipse((cx - r, cy - r * 2.2, cx + r, cy - r * 0.2), fill=(255, 59, 48))
    d.polygon([(cx - r * 0.7, cy - r * 0.8), (cx + r * 0.7, cy - r * 0.8), (cx, cy + r * 0.6)], fill=(255, 59, 48))
    d.ellipse((cx - r * 0.4, cy - r * 1.6, cx + r * 0.4, cy - r * 0.8), fill=WHITE)
    return cx, cy

def zoom(t, T):
    ps = Image.new("RGBA", (BW, BH), (242, 242, 247, 255))
    d = ImageDraw.Draw(ps)
    d.rounded_rectangle((20, 70, BW - 20, 190), 16, fill=(255, 190, 120))
    txt(ps, (BW / 2, 130), "📷 送った写真", 22, WHITE, anchor="mm") if False else txt(ps, (BW / 2, 130), "送った写真", 26, WHITE, anchor="mm")
    cx, cy = mapcard(ps, (20, 206, BW - 20, 420), True)
    d.ellipse((cx - 70, cy - 100, cx + 70, cy + 40), outline=(255, 59, 48), width=7)
    rr(ps, (BW / 2 - 110, cy + 50, BW / 2 + 110, cy + 92), 14, (20, 20, 26))
    txt(ps, (BW / 2, cy + 71), "撮影場所：自宅付近", 18, WHITE, anchor="mm")
    pill(ps, "撮った場所まで一緒に送られてる…", (255, 59, 48))
    return ps

def SCREEN(t, T):
    a = T.at
    if t < a["b1"]: return zoom(t, T)
    ps = Image.new("RGBA", (BW, BH), (242, 242, 247, 255))
    d = ImageDraw.Draw(ps)
    txt(ps, (56, 84), "9:41", 24, INK, anchor="lm")
    if t < a["b2"]:
        d.rounded_rectangle((16, 110, BW - 16, 260), 16, fill=(255, 190, 120))
        txt(ps, (BW / 2, 185), "写真", 22, WHITE, anchor="mm")
        mapcard(ps, (16, 276, BW - 16, 420), False)
        txt(ps, (24, 440), "撮影場所：自宅付近", 15, (255, 59, 48), anchor="lm")
        pill(ps, "写真の情報に撮った場所が出る", (255, 59, 48))
        return ps
    # share sheet
    off_at = a["b3"] + 0.8
    rr(ps, (16, 110, BW - 16, 200), 18, WHITE)
    txt(ps, (34, 140), "1枚の写真を選択中", 17, INK, anchor="lm")
    opt_hi = t >= a["b2"] + 0.3
    rr(ps, (34, 160, 160, 190), 15, (255, 236, 150) if opt_hi else (230, 230, 236))
    txt(ps, (97, 175), "オプション ›", 14, BLUE, anchor="mm")
    if a["b2"] + 0.4 <= t < a["b2"] + 0.8: finger(ps, 97, 175)
    if t >= a["b2"] + 0.9:
        rr(ps, (16, 220, BW - 16, 330), 18, WHITE)
        txt(ps, (34, 248), "含める", 14, GRAY, bold=False, anchor="lm")
        txt(ps, (34, 296), "位置情報", 20, INK, anchor="lm")
        on = t < off_at
        d.ellipse((BW - 110, 266, BW - 10, 326), outline=(255, 59, 48), width=5) if on else None
        toggle(ps, BW - 86, 280, on)
        if off_at - 0.35 <= t < off_at + 0.1: finger(ps, BW - 60, 296)
    if t < a["b3"]: pill(ps, "共有 → 上の「オプション」", (10, 132, 255))
    elif t < off_at: pill(ps, "位置情報をオフに", (10, 132, 255))
    else: pill(ps, "これで撮った場所は送られない！", (52, 199, 89))
    return ps

def draw_body(c, t, T): pass

def draw_hook_art(ly, t): pass

def sfx(T):
    a = T.at
    return [("ding", 0.3), ("pop", a["b1"]), ("click", a["b2"] + 0.6), ("click", a["b3"] + 0.8), ("ding", a["b3"] + 1.0)]

def stills(T):
    a = T.at
    return [0.05, 1.0, a["b1"] + 0.6, a["b2"] + 1.2, a["b3"] + 0.4, a["b3"] + 1.2, a["cta"] + 0.6]
