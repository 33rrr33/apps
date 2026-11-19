# 11/22 12:00 13秒1ネタ（ヒット系統：バッテリー）電池を食っている犯人アプリは「設定→バッテリー」で分かる
# 1フレーム目＝本物そっくりの「バッテリー」画面（残り18%＋アプリ別の使用率）— 11/18 スワイプ率ルール
# 根拠：iOS 設定→バッテリー「Appごとのバッテリー使用状況」（過去24時間／10日間、バックグラウンドの表示あり）
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="b20261122_second", title="iPhone隠し神機能", spoken="iPhone隠し、かみ機能",
              hook_split=("iPhone", "隠し神機能"), total=5, offset=10)
TITLE = "電池がすぐ減る人、犯人はこのアプリかも… #Shorts"
NUM, SLUG = 1, "battery_culprit"
NEXT = "次も電池の話"
SCREEN_CROP = (0, 40, 400, 760)
DURATION, END_CARD = 14.5, False
TAGS = {"length": "13秒1ネタ", "layout": "画面録画風", "hook_type": "疑問型", "title_type": "…止め", "topic_kind": "バッテリー",
        "first_frame": "本物の画面＋自分ごと"}
LAYOUT, FOCUS_Y, CAPTION_Y = "rec", 400, 1260
HOOK = "電池が減る犯人\n{このアプリ}かも…"
HOOK_SPOKEN = "電池がすぐ減る人、犯人はこのアプリかも！"
TELOPS = [("b1", "設定 →\n[バッテリー]"), ("b2", "電池を使った順に\n{アプリが並ぶ}"),
          ("b3", "使ってないのに\n{上位}のアプリは…"), ("b4", "[削除]か\n[バックグラウンド更新オフ]")]
ACTIONS = [("b1", "b2", "設定 → バッテリー"), ("b2", "b3", "Appごとの使用状況"),
           ("b3", "b4", "「バックグラウンド」と出たら要注意"), ("b4", "cta", "使わないアプリは削除")]
BODY = [
    ("b1", "設定のバッテリーを開くと、", 0.1),
    ("b2", "電池を使った順に、アプリが並びます。", 0.1),
    ("b3", "使ってないのに上にいるアプリは、", 0.1),
    ("b4", "削除するか、バックグラウンド更新をオフ！", 0.0),
]
BODY_HOLD = 0.4
CTA = dict(lines=[("1位のアプリ", WHITE, 100), ("コメントで教えて！", YEL, 100)], spoken="1位をコメントで教えて！",
           chip="フォローで毎日1つ")

BW, BH = 400, 860
APPS = [("ショッピング", (255, 149, 0), 31, True), ("SNS", (175, 82, 222), 24, False), ("ゲーム", (255, 59, 48), 17, True),
        ("LINE", (52, 199, 89), 11, False), ("天気", (10, 132, 255), 6, False)]

def finger(ps, x, y):
    fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((x - 30, y - 30, x + 30, y + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))

def pill(ps, text, col):
    rra(ps, (40, 640, BW - 40, 696), 28, col + (235,))
    txt(ps, (BW / 2, 668), text, 17, WHITE, anchor="mm")

def SCREEN(t, T):
    a = T.at
    ps = Image.new("RGBA", (BW, BH), (242, 242, 247, 255))
    d = ImageDraw.Draw(ps)
    txt(ps, (56, 36), "9:41", 22, INK, anchor="lm")
    d.rounded_rectangle((BW - 92, 26, BW - 54, 46), 5, outline=INK, width=2)
    d.rectangle((BW - 89, 29, BW - 84, 43), fill=(255, 59, 48))
    txt(ps, (24, 84), "‹ 設定", 18, BLUE, bold=False, anchor="lm")
    txt(ps, (24, 124), "バッテリー", 30, INK, anchor="lm")
    txt(ps, (BW - 24, 124), "残り 18%", 22, (255, 59, 48), anchor="rm")
    txt(ps, (30, 168), "Appごとのバッテリー使用状況", 14, GRAY, bold=False, anchor="lm")
    for i, (nm, col, pct, bg) in enumerate(APPS):
        y = 184 + i * 56
        suspect = bg and t >= a["b3"]
        rr(ps, (16, y, BW - 16, y + 50), 12, (255, 220, 215) if suspect else WHITE)
        d.rounded_rectangle((28, y + 9, 60, y + 41), 8, fill=col)
        txt(ps, (72, y + (17 if bg else 25)), nm, 16, INK, bold=False, anchor="lm")
        if bg: txt(ps, (72, y + 36), "バックグラウンドのアクティビティ", 11, (255, 59, 48) if suspect else GRAY, bold=False, anchor="lm")
        txt(ps, (BW - 30, y + 25), f"{pct}%", 18, (255, 59, 48) if suspect else INK, anchor="rm")
    if a["b1"] <= t < a["b2"]: finger(ps, BW / 2, 168)
    if a["b3"] + 0.3 <= t < a["b3"] + 0.8: finger(ps, BW / 2, 184 + 25)
    if a["b2"] <= t < a["b3"]: pill(ps, "電池を使った順に並ぶ", (10, 132, 255))
    if a["b3"] <= t < a["b4"]: pill(ps, "使ってないのに裏で電池を使う…", (255, 59, 48))
    if t >= a["b4"]: pill(ps, "削除かバックグラウンド更新オフ！", (52, 199, 89))
    return ps

def draw_body(c, t, T): pass

def draw_hook_art(ly, t): pass

def sfx(T):
    a = T.at
    return [("pop", a["b1"]), ("pop", a["b2"]), ("ding", a["b3"]), ("click", a["b3"] + 0.5), ("ding", a["b4"])]

def stills(T):
    a = T.at
    return [0.05, 0.8, a["b1"] + 0.3, a["b2"] + 0.5, a["b3"] + 0.6, a["b4"] + 0.5, a["cta"] + 0.6]
