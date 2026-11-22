# 11/25 06:00 13秒1ネタ（危険サイン型・plan w1）画面右上の緑/オレンジの点＝カメラ/マイク使用中（画面録画風・損失回避）
# 1フレーム目＝本物そっくりのホーム画面、右上ステータスバーにオレンジの点が光る（危険サイン型：こあら博士『このマークは危険！』21万回）
# 根拠：Apple サポート「iPhoneのステータスバーのオレンジ色や緑色のインジケータ」— オレンジ＝マイク使用中、緑＝カメラ（またはカメラとマイク）使用中。
#       コントロールセンターを開くと、どのAppが使用したか表示される（iOS 14以降）
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="b20261122_second", title="iPhone隠し神機能", spoken="iPhone隠し、かみ機能",
              hook_split=("iPhone", "隠し神機能"), total=5, offset=10)
TITLE = "iPhoneの画面にこの点が出たら注意… #Shorts"
NUM, SLUG = 4, "mic_dot"
NEXT = "次も守る設定"
SCREEN_CROP = (0, 40, 400, 760)
DURATION, END_CARD = 14.5, False
TAGS = {"length": "13秒1ネタ", "layout": "画面録画風", "hook_type": "即効型", "title_type": "…止め", "topic_kind": "危険設定",
        "first_frame": "本物の画面＋自分ごと"}
LAYOUT, FOCUS_Y, CAPTION_Y = "rec", 400, 1260
HOOK = "画面にこの点\n{出てたら注意}…"
HOOK_SPOKEN = "画面の右上に、この点が出てたら注意！"
TELOPS = [("b1", "{オレンジ}＝マイク\n{緑}＝カメラ"), ("b2", "今まさに\n{使われている}サイン"),
          ("b3", "コントロールセンターで\n[どのアプリか]わかる"), ("b4", "心当たりがなければ\n[アクセスをオフ]")]
ACTIONS = [("b1", "b2", "右上の小さな点"), ("b2", "b3", "使ってないのに点いてたら…"),
           ("b3", "b4", "右上から下にスワイプ"), ("b4", "cta", "設定 → プライバシー → マイク")]
BODY = [
    ("b1", "オレンジはマイク、緑はカメラが", 0.1),
    ("b2", "使われているサインです。", 0.1),
    ("b3", "コントロールセンターを開くと、どのアプリか分かります。", 0.1),
    ("b4", "心当たりがなければ、アクセスをオフに！", 0.0),
]
BODY_HOLD = 0.4
CTA = dict(lines=[("点いてた人は", WHITE, 100), ("コメントで教えて！", YEL, 100)], spoken="点いてた人はコメントで！",
           chip="フォローで毎日1つ")

BW, BH = 400, 860
ORANGE, GREEN = (255, 149, 0), (52, 199, 89)
ICONS = [(255, 59, 48), (10, 132, 255), (52, 199, 89), (255, 204, 0), (175, 82, 222), (255, 149, 0),
         (90, 200, 250), (255, 45, 85), (88, 86, 214), (142, 142, 147), (0, 199, 190), (162, 132, 94)]

def finger(ps, x, y):
    fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((x - 30, y - 30, x + 30, y + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))

def pill(ps, text, col):
    rra(ps, (40, 640, BW - 40, 696), 28, col + (235,))
    txt(ps, (BW / 2, 668), text, 17, WHITE, anchor="mm")

def dot(ps, t, col, x=BW - 108, y=84):
    r = 7 + 3 * (0.5 + 0.5 * __import__("math").sin(t * 6))
    d = ImageDraw.Draw(ps)
    d.ellipse((x - r - 6, y - r - 6, x + r + 6, y + r + 6), outline=col, width=3)
    d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=col)

def home(t, T):
    a = T.at
    ps = grad(BW, BH, (40, 70, 140), (140, 80, 160))
    txt(ps, (56, 84), "9:41", 24, WHITE, anchor="lm")
    d = ImageDraw.Draw(ps)
    d.rounded_rectangle((BW - 82, 72, BW - 40, 96), 6, outline=WHITE, width=2)
    d.rectangle((BW - 79, 75, BW - 54, 93), fill=WHITE)
    col = GREEN if a["b1"] + 1.2 <= t < a["b2"] else ORANGE
    dot(ps, t, col)
    for i, c in enumerate(ICONS):
        r, k = divmod(i, 4)
        x, y = 36 + k * 88, 196 + r * 88
        rr(ps, (x, y, x + 64, y + 64), 16, c)
    if t >= a["b1"]:
        d.line((BW - 108, 100, BW - 108, 132), fill=WHITE, width=3)
        lab = "カメラ使用中" if col == GREEN else "マイク使用中"
        rr(ps, (BW - 210, 132, BW - 16, 172), 14, (20, 20, 26))
        txt(ps, (BW - 113, 152), lab, 17, col, anchor="mm")
    return ps

def control(t, T):
    a = T.at
    ps = grad(BW, BH, (30, 30, 40), (20, 20, 30))
    dot(ps, t, ORANGE)
    rr(ps, (16, 120, BW - 16, 200), 18, (60, 60, 70))
    d = ImageDraw.Draw(ps)
    d.ellipse((34, 146, 62, 174), fill=ORANGE)
    txt(ps, (78, 150), "マイク", 14, (200, 200, 210), bold=False, anchor="lm")
    txt(ps, (78, 174), "ショッピングアプリ", 18, WHITE, anchor="lm")
    if t >= a["b3"] + 0.5:
        d.rounded_rectangle((16, 120, BW - 16, 200), 18, outline=(255, 59, 48), width=4)
    for i in range(8):
        r, k = divmod(i, 4)
        x, y = 36 + k * 88, 220 + r * 80
        rr(ps, (x, y, x + 60, y + 60), 16, (70, 70, 82))
    if t >= a["b4"]:
        rr(ps, (16, 394, BW - 16, 450), 14, (242, 242, 247))
        txt(ps, (34, 422), "ショッピングアプリ", 17, INK, anchor="lm")
        toggle(ps, BW - 86, 402, t < a["b4"] + 1.2)
        if a["b4"] + 0.8 <= t < a["b4"] + 1.3: finger(ps, BW - 60, 422)
    return ps

def SCREEN(t, T):
    a = T.at
    ps = control(t, T) if t >= a["b3"] else home(t, T)
    if t < a["b1"]: pill(ps, "右上に点が光ってる…", (255, 59, 48))
    elif t < a["b3"]: pill(ps, "使ってないのに点いてたら要注意", (255, 59, 48))
    elif t < a["b4"]: pill(ps, "どのアプリか一目でわかる", (10, 132, 255))
    else: pill(ps, "設定 → プライバシー → マイクでオフ", (52, 199, 89))
    return ps

def draw_body(c, t, T): pass

def draw_hook_art(ly, t): pass

def sfx(T):
    a = T.at
    return [("ding", 0.3), ("pop", a["b1"]), ("whoosh", a["b3"]), ("click", a["b4"] + 1.0)]

def stills(T):
    a = T.at
    return [0.05, 0.8, a["b1"] + 0.5, a["b1"] + 1.5, a["b3"] + 0.8, a["b4"] + 0.6, a["b4"] + 1.5, a["cta"] + 0.6]
