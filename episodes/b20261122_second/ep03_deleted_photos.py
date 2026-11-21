# 11/24 12:00 13秒1ネタ（守り・プライバシー系：ロック画面LINEの関連）消した写真は「最近削除した項目」に30日残る（画面録画風・損失回避）
# 1フレーム目＝本物そっくりの写真アプリ「最近削除した項目」（残り日数つきのサムネイル）— 11/18 スワイプ率ルール
# 根拠：iOS 写真アプリ — 削除した写真・ビデオは「最近削除した項目」に30日間保存、選択→すべて削除で完全に削除
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="b20261122_second", title="iPhone隠し神機能", spoken="iPhone隠し、かみ機能",
              hook_split=("iPhone", "隠し神機能"), total=5, offset=10)
TITLE = "消したはずの写真、まだiPhoneに残ってる人へ… #Shorts"
NUM, SLUG = 3, "deleted_photos"
NEXT = "次も守る設定"
SCREEN_CROP = (0, 40, 400, 760)
DURATION, END_CARD = 14.0, False
TAGS = {"length": "13秒1ネタ", "layout": "画面録画風", "hook_type": "疑問型", "title_type": "…止め", "topic_kind": "危険設定",
        "first_frame": "本物の画面＋自分ごと"}
LAYOUT, FOCUS_Y, CAPTION_Y = "rec", 400, 1260
HOOK = "消した写真\n{まだ残ってる}…"
HOOK_SPOKEN = "写真を消したつもりの人へ！"
TELOPS = [("b1", "削除した写真は\n{30日間残る}"), ("b2", "アルバム →\n[最近削除した項目]"),
          ("b3", "[選択] →\n[すべて削除]"), ("b4", "これで\n[完全に消える]")]
ACTIONS = [("b1", "b2", "消したつもりでも残ってる"), ("b2", "b3", "アルバムのいちばん下"),
           ("b3", "b4", "右上の「選択」から"), ("b4", "cta", "人に見られる前に")]
BODY = [
    ("b1", "削除した写真は、30日間残ってます。", 0.1),
    ("b2", "アルバムの、最近削除した項目を開いて、", 0.1),
    ("b3", "選択から、すべて削除。", 0.1),
    ("b4", "これで完全に消えます！", 0.0),
]
BODY_HOLD = 0.4
CTA = dict(lines=[("残ってた人は", WHITE, 100), ("コメントで教えて！", YEL, 100)], spoken="残ってた人はコメントで！",
           chip="フォローで毎日1つ")

BW, BH = 400, 860
COLS = [(255, 159, 10), (90, 160, 255), (255, 100, 130), (120, 200, 120), (180, 120, 230), (250, 210, 80),
        (100, 200, 220), (240, 120, 80), (150, 150, 170), (255, 180, 200), (80, 140, 120), (200, 160, 110)]
DAYS = [29, 29, 28, 27, 27, 25, 22, 21, 18, 14, 9, 3]

def finger(ps, x, y):
    fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((x - 30, y - 30, x + 30, y + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))

def pill(ps, text, col):
    rra(ps, (40, 640, BW - 40, 696), 28, col + (235,))
    txt(ps, (BW / 2, 668), text, 17, WHITE, anchor="mm")

def SCREEN(t, T):
    a = T.at
    ps = Image.new("RGBA", (BW, BH), (255, 255, 255, 255))
    d = ImageDraw.Draw(ps)
    txt(ps, (56, 36), "9:41", 22, INK, anchor="lm")
    txt(ps, (24, 84), "‹ アルバム", 18, BLUE, bold=False, anchor="lm")
    sel_mode = t >= a["b3"] + 0.3
    rr(ps, (BW - 86, 70, BW - 16, 98), 14, (255, 236, 150) if a["b3"] <= t < a["b3"] + 0.6 else (230, 230, 236))
    txt(ps, (BW - 51, 84), "キャンセル" if sel_mode else "選択", 13 if sel_mode else 15, BLUE, anchor="mm")
    txt(ps, (24, 124), "最近削除した項目", 26, INK, anchor="lm")
    gone = t >= a["b4"] + 0.2
    if not gone:
        for i, (col, dd) in enumerate(zip(COLS, DAYS)):
            r, c = divmod(i, 3)
            x, y = 16 + c * 124, 150 + r * 64
            d.rectangle((x, y, x + 120, y + 60), fill=col)
            for k in range(3): d.ellipse((x + 20 + k * 30, y + 16, x + 40 + k * 30, y + 36), fill=(255, 255, 255, 120))
            rr(ps, (x + 64, y + 38, x + 116, y + 57), 8, (0, 0, 0))
            txt(ps, (x + 90, y + 47), f"{dd}日", 12, (255, 90, 80) if t >= a["b1"] else WHITE, anchor="mm")
        if not sel_mode: txt(ps, (BW / 2, 424), "残り日数がたつと完全に削除されます", 13, GRAY, bold=False, anchor="mm")
    else:
        txt(ps, (BW / 2, 300), "写真またはビデオはありません", 18, GRAY, anchor="mm")
    if sel_mode and not gone:
        rr(ps, (BW - 150, 412, BW - 16, 450), 12, (255, 236, 150) if t >= a["b3"] + 0.9 else (245, 245, 248))
        txt(ps, (BW - 83, 431), "すべて削除", 15, (255, 59, 48), anchor="mm")
    if a["b3"] + 0.2 <= t < a["b3"] + 0.5: finger(ps, BW - 51, 84)
    if a["b3"] + 1.0 <= t < a["b3"] + 1.4: finger(ps, BW - 83, 431)
    if a["b4"] - 0.3 <= t < a["b4"] + 0.2:
        rra(ps, (40, 220, BW - 40, 360), 18, (250, 250, 252, 245))
        txt(ps, (BW / 2, 260), "12項目を削除しますか？", 17, INK, anchor="mm")
        txt(ps, (BW / 2, 322), "削除", 18, (255, 59, 48), anchor="mm")
        finger(ps, BW / 2, 322)
    if t < a["b2"]: pill(ps, "消したつもりが30日残ってる…", (255, 59, 48))
    elif t < a["b4"]: pill(ps, "選択 → すべて削除", (10, 132, 255))
    else: pill(ps, "完全に消えた！", (52, 199, 89))
    return ps

def draw_body(c, t, T): pass

def draw_hook_art(ly, t): pass

def sfx(T):
    a = T.at
    return [("ding", a["b1"]), ("pop", a["b2"]), ("click", a["b3"] + 0.3), ("click", a["b3"] + 1.2), ("whoosh", a["b4"] + 0.2)]

def stills(T):
    a = T.at
    return [0.05, 0.8, a["b1"] + 0.5, a["b2"] + 0.5, a["b3"] + 1.2, a["b4"], a["b4"] + 0.6, a["cta"] + 0.6]
