# 11/19 06:00 60秒3選（危険設定・plan s2）iPhoneを盗まれる前にやっておく設定3つ（予告＋つなぎ・画面録画風・損失回避）
# 根拠：Appleサポート「盗難デバイスの保護」（iOS 17.3以降・設定→Face IDとパスコード）、「探す」ネットワーク／最後の位置情報を送信（設定→ユーザ名→探す→iPhoneを探す）
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="b20261117_first", title="iPhone爆速神操作", spoken="iPhone爆速、かみ操作",
              hook_split=("iPhone", "爆速神操作"), total=5, offset=10)
TITLE = "iPhoneを盗まれる前に、この3つだけはやって… #Shorts"
NUM, SLUG = 3, "theft3"
NEXT = "次も守る設定"
SCREEN_CROP = (0, 40, 400, 760)
DURATION, END_CARD = 39.0, False
TAGS = {"length": "60秒3選", "layout": "画面録画風", "hook_type": "煽り型", "title_type": "…止め", "topic_kind": "危険設定", "structure": "予告＋つなぎ"}
LAYOUT, FOCUS_Y, CAPTION_Y = "rec", 400, 1260
HOOK = "盗まれてからじゃ\n{もう遅い}…"
HOOK_SPOKEN = "iPhoneを盗まれる前に、この3つだけはやって。特に1つ目、知らない人が多いです！"
TELOPS = [("b1", "1つ目\n[盗難デバイスの保護]"), ("b2", "パスコードを見られても\n{勝手に変更できない}"),
          ("b3", "Face IDとパスコード →\n[盗難デバイスの保護]をオン"), ("b4", "2つ目\n[“探す”ネットワーク]"),
          ("b5", "電源が切れても\n[場所を探せる]"), ("b6", "3つ目\n[最後の位置情報を送信]"),
          ("b7", "電池が切れる直前の\n[場所が残る]")]
ACTIONS = [("b1", "b2", "iOS 17.3以降の機能"), ("b2", "b3", "Apple IDの変更などに顔認証が必要"),
           ("b3", "b4", "設定 → Face IDとパスコード"), ("b4", "b5", "設定 → 自分の名前 → 探す"),
           ("b5", "b6", "“探す”ネットワークをオン"), ("b6", "b7", "最後の位置情報を送信をオン"),
           ("b7", "cta", "3つともオンにしておこう")]
BODY = [
    ("b1", "1つ目、盗難デバイスの保護。", 0.2),
    ("b2", "パスコードを盗み見られても、Apple IDの変更などに顔認証が必要になるので、勝手に乗っ取られにくくなります。", 0.2),
    ("b3", "Face IDとパスコードの中で、オンにできます。次の2つは、探すの設定です。", 0.3),
    ("b4", "2つ目、探すネットワーク。", 0.2),
    ("b5", "オンにしておくと、電源が切れていても、近くのApple製品を通して場所を探せます。", 0.3),
    ("b6", "3つ目、最後の位置情報を送信。", 0.2),
    ("b7", "電池が切れる直前の場所が、自動で送られます。", 0.0),
]
BODY_HOLD = 0.5
CTA = dict(lines=[("何個オンだった？", WHITE, 96), ("コメントで教えて！", YEL, 100)], spoken="何個オンだったか、コメントで教えて！",
           chip="家族のiPhoneにも")

BW, BH = 400, 860

def finger(ps, x, y):
    fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((x - 30, y - 30, x + 30, y + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))

def page(back, title):
    ps = Image.new("RGBA", (BW, BH), (242, 242, 247, 255))
    txt(ps, (56, 36), "9:41", 22, INK, anchor="lm")
    txt(ps, (24, 84), "‹ " + back, 18, BLUE, bold=False, anchor="lm")
    txt(ps, (24, 128), title, 26 if len(title) > 9 else 30, INK, anchor="lm")
    return ps

def pill(ps, text, col):
    rra(ps, (40, 640, BW - 40, 696), 28, col + (235,))
    txt(ps, (BW / 2, 668), text, 17, WHITE, anchor="mm")

def toggle_row(ps, y, label, on, hi, bold=True):
    rr(ps, (16, y, BW - 16, y + 56), 12, (255, 236, 150) if hi else WHITE)
    txt(ps, (34, y + 28), label, 17, INK, bold=bold, anchor="lm")
    toggle(ps, BW - 86, y + 10, on)

def protection(t, T):
    a = T.at
    if t < a["b3"]:                                   # danger visual: someone watching the passcode
        ps = grad(BW, BH, (30, 30, 50), (12, 12, 20))
        txt(ps, (BW / 2, 120), "パスコードを入力", 22, WHITE, anchor="mm")
        for i in range(6):
            x = BW / 2 - 100 + i * 40
            ImageDraw.Draw(ps).ellipse((x - 9, 196, x + 9, 214), fill=WHITE if i < 4 else None, outline=WHITE, width=2)
        for r in range(3):
            for c in range(3):
                x, y = 110 + c * 90, 270 + r * 72
                ImageDraw.Draw(ps).ellipse((x - 32, y - 32, x + 32, y + 32), fill=(70, 70, 80))
                txt(ps, (x, y), str(r * 3 + c + 1), 26, WHITE, anchor="mm")
        if t >= a["b1"] + 0.3:
            txt(ps, (BW / 2, 500), "👀", 40, WHITE, anchor="mm") if False else None
            rra(ps, (40, 140, BW - 40, 178), 14, (255, 59, 48, 220))
            txt(ps, (BW / 2, 159), "後ろから見られている…", 16, WHITE, anchor="mm")
        if t >= a["b2"]:
            pill(ps, "顔認証がないと変更できない", (52, 199, 89))
        return ps
    on_at = a["b3"] + 2.2
    ps = page("設定", "Face IDとパスコード")
    txt(ps, (30, 172), "盗難デバイスの保護", 15, GRAY, bold=False, anchor="lm")
    toggle_row(ps, 190, "盗難デバイスの保護", t >= on_at, t >= on_at - 0.4)
    if on_at - 0.35 <= t < on_at + 0.1: finger(ps, BW - 60, 218)
    txt(ps, (30, 272), "パスコードを知られても、大事な変更には", 14, GRAY, bold=False, anchor="lm")
    txt(ps, (30, 294), "Face IDなどの生体認証が必要になります", 14, GRAY, bold=False, anchor="lm")
    if t >= on_at + 0.3: pill(ps, "盗難デバイスの保護：オン", (52, 199, 89))
    return ps

def findmy(t, T):
    a = T.at
    net_at, last_at = a["b5"] + 1.6, a["b7"] + 0.6
    ps = page("探す", "iPhoneを探す")
    toggle_row(ps, 170, "iPhoneを探す", True, False)
    toggle_row(ps, 236, "“探す”ネットワーク", t >= net_at, a["b4"] <= t < a["b6"])
    toggle_row(ps, 302, "最後の位置情報を送信", t >= last_at, t >= a["b6"])
    if net_at - 0.35 <= t < net_at + 0.1: finger(ps, BW - 60, 264)
    if last_at - 0.35 <= t < last_at + 0.1: finger(ps, BW - 60, 330)
    if a["b5"] <= t < a["b6"]:
        d = ImageDraw.Draw(ps)
        d.ellipse((BW / 2 - 40, 370, BW / 2 + 40, 450), outline=(10, 132, 255), width=4)
        d.ellipse((BW / 2 - 10, 400, BW / 2 + 10, 420), fill=(10, 132, 255))
        if t >= net_at + 0.2: pill(ps, "電源オフでも探せる", (10, 132, 255))
    if t >= last_at + 0.2: pill(ps, "電池切れ直前の場所が残る", (52, 199, 89))
    return ps

def SCREEN(t, T):
    return findmy(t, T) if t >= T.at["b4"] else protection(t, T)

def draw_body(c, t, T): pass

def draw_hook_art(ly, t): pass

def sfx(T):
    a = T.at
    return [("pop", a["b1"]), ("ding", a["b2"]), ("click", a["b3"] + 2.2), ("pop", a["b4"]), ("click", a["b5"] + 1.6),
            ("pop", a["b6"]), ("click", a["b7"] + 0.6)]

def stills(T):
    a = T.at
    return [1.0, a["b1"] + 1.0, a["b2"] + 1.5, a["b3"] + 2.6, a["b5"] + 2.0, a["b7"] + 1.0, a["cta"] + 0.8]
