# 11/27 06:00 13秒1ネタ（電池の犯人さがし・plan w5）位置情報の「システムサービス」で不要な項目をオフ（画面録画風・損失回避）
# 1フレーム目＝本物そっくりの「システムサービス」画面、位置情報を使う項目がずらりとオン＋電池残り15%（11/18 スワイプ率ルール）
# 根拠：設定→プライバシーとセキュリティ→位置情報サービス→システムサービス。「位置情報に基づく提案」「利用頻度の高い場所」
#       「iPhone解析」などは不要ならオフにできる（位置情報の使用が減り電池の節約につながる）。「iPhoneを探す」「緊急SOS」はオンのまま
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="b20261127_first", title="iPhone爆速神操作", spoken="iPhone爆速、かみ操作",
              hook_split=("iPhone", "爆速神操作"), total=5, offset=15)
TITLE = "電池を減らす犯人、ここにも隠れてる… #Shorts"
NUM, SLUG = 1, "system_services"
NEXT = "次も電池の話"
SCREEN_CROP = (0, 40, 400, 760)
DURATION, END_CARD = 15.0, False
TAGS = {"length": "13秒1ネタ", "layout": "画面録画風", "hook_type": "即効型", "title_type": "…止め", "topic_kind": "バッテリー",
        "first_frame": "本物の画面＋自分ごと"}
LAYOUT, FOCUS_Y, CAPTION_Y = "rec", 400, 1260
HOOK = "電池を減らす犯人\n{ここにも}…"
HOOK_SPOKEN = "電池を減らす犯人、ここにも隠れてます！"
TELOPS = [("b1", "位置情報サービス →\n[システムサービス]"), ("b2", "裏で{位置情報を使う}\n項目がずらり"),
          ("b3", "使わないものを\n[オフ]にするだけ"), ("b4", "[iPhoneを探す]は\nオンのまま")]
ACTIONS = [("b1", "b2", "プライバシーとセキュリティの中"), ("b2", "b3", "知らないうちに全部オン"),
           ("b3", "b4", "提案・解析などをオフ"), ("b4", "cta", "大事なものは残す")]
BODY = [
    ("b1", "位置情報サービスの、システムサービスに、", 0.1),
    ("b2", "裏で位置情報を使う項目が並んでます。", 0.1),
    ("b3", "使わないものをオフにするだけ。", 0.1),
    ("b4", "iPhoneを探すは、オンのままで！", 0.0),
]
BODY_HOLD = 0.4
CTA = dict(lines=[("いくつオンだった？", WHITE, 96), ("コメントで教えて！", YEL, 100)], spoken="いくつオンだったか、コメントで！",
           chip="フォローで毎日1つ")

BW, BH = 400, 860
ROWS = [("位置情報に基づく提案", True), ("位置情報に基づく通知", True), ("利用頻度の高い場所", True),
        ("iPhone解析", True), ("iPhoneを探す", False)]

def finger(ps, x, y):
    fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((x - 30, y - 30, x + 30, y + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))

def pill(ps, text, col):
    rra(ps, (40, 640, BW - 40, 696), 28, col + (235,))
    txt(ps, (BW / 2, 668), text, 17, WHITE, anchor="mm")

def SCREEN(t, T):
    a = T.at
    ps = Image.new("RGBA", (BW, BH), (242, 242, 247, 255))
    d = ImageDraw.Draw(ps)
    txt(ps, (56, 84), "9:41", 24, INK, anchor="lm")
    d.rounded_rectangle((BW - 100, 72, BW - 56, 96), 6, outline=INK, width=2)
    d.rectangle((BW - 97, 75, BW - 90, 93), fill=(255, 59, 48))
    txt(ps, (BW - 28, 84), "15%", 15, (255, 59, 48), anchor="mm")
    txt(ps, (24, 124), "‹ 位置情報サービス", 18, BLUE, bold=False, anchor="lm")
    txt(ps, (24, 162), "システムサービス", 26, INK, anchor="lm")
    off_order = [0, 1, 2, 3]
    for i, (lab, can_off) in enumerate(ROWS):
        y = 188 + i * 54
        at = a["b3"] + 0.3 + 0.45 * off_order.index(i) if can_off else None
        on = not (at is not None and t >= at)
        keep = (not can_off) and t >= a["b4"]
        sus = can_off and on and t >= a["b2"]
        rr(ps, (16, y, BW - 16, y + 48), 12, (200, 245, 205) if keep else (255, 225, 220) if sus else WHITE)
        d.polygon([(32, y + 30), (40, y + 14), (48, y + 30)], fill=BLUE if on else (180, 180, 190))
        txt(ps, (58, y + 24), lab, 16, INK, bold=keep, anchor="lm")
        toggle(ps, BW - 86, y + 5, on)
        if at is not None and at - 0.3 <= t < at + 0.1: finger(ps, BW - 60, y + 24)
    if t < a["b2"]: pill(ps, "知らないうちに全部オン…", (255, 59, 48))
    elif t < a["b3"]: pill(ps, "裏でずっと位置情報を使う", (255, 59, 48))
    elif t < a["b4"]: pill(ps, "使わないものはオフ", (10, 132, 255))
    else: pill(ps, "「iPhoneを探す」はオンのまま！", (52, 199, 89))
    return ps

def draw_body(c, t, T): pass

def draw_hook_art(ly, t): pass

def sfx(T):
    a = T.at
    return [("ding", 0.3), ("pop", a["b1"]), ("ding", a["b2"])] + [("click", a["b3"] + 0.3 + 0.45 * k) for k in range(4)] + [("ding", a["b4"])]

def stills(T):
    a = T.at
    return [0.05, 0.8, a["b1"] + 0.5, a["b2"] + 0.5, a["b3"] + 1.2, a["b4"] + 0.5, a["cta"] + 0.6]
