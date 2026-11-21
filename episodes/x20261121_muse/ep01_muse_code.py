# 11/21 12:00 単発（ユーザー依頼）Muse AI：登録後48時間以内に招待コードで10億トークン（PR表示つき・損失回避）
# 事実：Muse（Meta・2026/9提供開始）iPhoneで日本からDL可（ユーザー確認11/21）。招待コード入力で双方に10億トークン・登録後48時間以内・設定→Redeem token
# 招待コード 2202NF は投稿者のもの → 動画内「PR」常時表示・説明欄で明記・有料プロモーション表示
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="x20261121_muse", title="iPhoneで話題のAI", spoken="iPhoneで話題のAI",
              hook_split=("iPhone", "話題のAI"), total=1, offset=0)
TITLE = "Muse始めた人、48時間以内にこれしないと損… #Shorts"
NUM, SLUG = 1, "muse_code"
NEXT = "次も損しない設定"
SCREEN_CROP = (0, 40, 400, 760)
DURATION, END_CARD = 16.0, False
TAGS = {"length": "13秒1ネタ", "layout": "画面録画風", "hook_type": "煽り型", "title_type": "…止め", "topic_kind": "ニュース",
        "first_frame": "本物の画面＋自分ごと", "pr": True}
LAYOUT, FOCUS_Y, CAPTION_Y = "rec", 400, 1260
HOOK = "Muse始めた人\n{48時間以内}に…"
HOOK_SPOKEN = "AIアプリのMuse、始めた人へ！"
TELOPS = [("b1", "登録から\n[48時間以内]に"), ("b2", "招待コードで\n{10億トークン}"),
          ("b3", "設定 →\n[Redeem token]"), ("b4", "コード\n[2202NF]")]
ACTIONS = [("b1", "b2", "過ぎると入力できない"), ("b2", "b3", "入れた人ももらえる"),
           ("b3", "b4", "設定を開く"), ("b4", "cta", "PR：コードは投稿者のもの")]
BODY = [
    ("b1", "登録から48時間以内に、", 0.1),
    ("b2", "招待コードを入れると、10億トークンもらえます。", 0.1),
    ("b3", "設定の、リディームトークンから、", 0.1),
    ("b4", "にー、にー、ぜろ、にー、エヌ、エフ、を入力！", 0.0),
]
BODY_HOLD = 0.4
CTA = dict(lines=[("期限が切れる前に", WHITE, 96), ("今すぐ入力！", YEL, 120)], spoken="48時間を過ぎると入れられないよ！",
           chip="PR・コードは投稿者のもの")

BW, BH = 400, 860
CODE = "2202NF"
DARK, CARD, ACC = (18, 18, 24), (34, 34, 44), (120, 110, 255)

def finger(ps, x, y):
    fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((x - 30, y - 30, x + 30, y + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))

def pill(ps, text, col):
    rra(ps, (40, 640, BW - 40, 696), 28, col + (235,))
    txt(ps, (BW / 2, 668), text, 17, WHITE, anchor="mm")

def base(title):
    ps = Image.new("RGBA", (BW, BH), DARK + (255,))
    txt(ps, (56, 36), "9:41", 22, WHITE, anchor="lm")
    rr(ps, (BW - 70, 62, BW - 16, 92), 8, (255, 59, 48))
    txt(ps, (BW - 43, 77), "PR", 16, WHITE, anchor="mm")
    txt(ps, (24, 120), title, 28, WHITE, anchor="lm")
    return ps

def SCREEN(t, T):
    a = T.at
    if t < a["b3"]:
        ps = base("Muse")
        rr(ps, (16, 160, BW - 16, 400), 18, CARD)
        txt(ps, (BW / 2, 196), "招待コード特典", 18, (200, 200, 215), bold=False, anchor="mm")
        txt(ps, (BW / 2, 250), "10億トークン", 40, (255, 214, 10), anchor="mm")
        left = max(0, 48 * 3600 - 1 - int(t * 37))
        h, m, s = left // 3600, left % 3600 // 60, left % 60
        rr(ps, (60, 300, BW - 60, 360), 14, (255, 59, 48) if t >= a["b1"] else (70, 70, 84))
        txt(ps, (BW / 2, 330), f"入力期限 残り {h}:{m:02d}:{s:02d}", 18, WHITE, anchor="mm")
        if t < a["b1"]: pill(ps, "48時間を過ぎると入力できない…", (255, 59, 48))
        else: pill(ps, "コードを入れた人ももらえる", (120, 110, 255))
        return ps
    ps = base("設定")
    if t < a["b4"]:
        rows = ["アカウント", "Redeem token", "通知", "プライバシー"]
        for i, r in enumerate(rows):
            y = 160 + i * 62
            rr(ps, (16, y, BW - 16, y + 56), 12, (90, 80, 30) if i == 1 and t >= a["b3"] + 0.4 else CARD)
            txt(ps, (34, y + 28), r, 18, WHITE, bold=i == 1, anchor="lm")
            txt(ps, (BW - 34, y + 28), "›", 22, (150, 150, 165), anchor="rm")
        if a["b3"] + 0.5 <= t < a["b3"] + 0.9: finger(ps, BW / 2, 160 + 62 + 28)
        pill(ps, "設定 → Redeem token", (120, 110, 255))
        return ps
    txt(ps, (30, 168), "招待コードを入力", 16, (200, 200, 215), bold=False, anchor="lm")
    rr(ps, (16, 186, BW - 16, 256), 14, CARD)
    n = min(len(CODE), int((t - a["b4"]) / 0.32) + 1)
    txt(ps, (BW / 2, 221), CODE[:n], 34, (255, 214, 10), anchor="mm")
    done = t >= a["b4"] + 2.4
    rr(ps, (60, 282, BW - 60, 336), 16, (52, 199, 89) if done else ACC)
    txt(ps, (BW / 2, 309), "受け取る" if not done else "10億トークン獲得！", 18, WHITE, anchor="mm")
    if a["b4"] + 2.0 <= t < a["b4"] + 2.4: finger(ps, BW / 2, 309)
    pill(ps, "PR：コードは投稿者のものです", (90, 90, 104))
    return ps

def draw_body(c, t, T): pass

def draw_hook_art(ly, t): pass

def sfx(T):
    a = T.at
    return [("ding", a["b1"]), ("pop", a["b2"]), ("click", a["b3"] + 0.7), ("pop", a["b4"]), ("ding", a["b4"] + 2.4)]

def stills(T):
    a = T.at
    return [0.05, 0.8, a["b1"] + 0.5, a["b2"] + 0.6, a["b3"] + 0.7, a["b4"] + 1.0, a["b4"] + 2.6, a["cta"] + 0.6]
