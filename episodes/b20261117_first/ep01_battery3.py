# 11/17 06:00 60秒3選（ヒット系統：バッテリー）電池がすぐ減る人がやりがちな設定3つ（v3・画面録画風・煽り型）
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="b20261117_first", title="iPhone爆速神操作", spoken="iPhone爆速、かみ操作",
              hook_split=("iPhone", "爆速神操作"), total=5, offset=10)
TITLE = "電池がすぐ減る人がやりがちな設定3つ… #Shorts"
NUM, SLUG = 1, "battery3"
NEXT = "次も電池の話"
SCREEN_CROP = (0, 40, 400, 760)
DURATION, END_CARD = 61.5, False
TAGS = {"length": "60秒3選", "layout": "画面録画風", "hook_type": "煽り型", "title_type": "…止め", "topic_kind": "バッテリー"}
LAYOUT, FOCUS_Y, CAPTION_Y = "rec", 400, 1260
HOOK = "電池が減る原因\n{この3つ}かも…"
HOOK_SPOKEN = "電池がすぐ減る人、この3つの設定、やりがちです。今すぐ見直して！"
TELOPS = [("b1", "1つ目\n[明るさの自動調節]"), ("b2", "{オフのまま}だと\nずっと明るい"),
          ("b3", "アクセシビリティ →\n[画面表示とテキストサイズ]"), ("b4", "2つ目\n[位置情報「常に」]"),
          ("b5", "使ってない時も\n{GPSが動く}"), ("b6", "位置情報サービス →\n[使用中のみ]"),
          ("b7", "3つ目\n[ダークモード]"), ("b8", "白い画面は\n{電池を使いやすい}"),
          ("b9", "画面表示と明るさ →\n[ダーク]")]
ACTIONS = [("b1", "b2", "明るさの自動調節"), ("b2", "b3", "明るさ100%のまま…"),
           ("b3", "b4", "明るさの自動調節をオン"), ("b4", "b5", "位置情報が「常に」のアプリ"),
           ("b5", "b6", "裏でずっと位置を取得"), ("b6", "b7", "「使用中のみ」に変更"),
           ("b7", "b8", "ダークモード"), ("b8", "b9", "有機ELのiPhoneで効果あり"),
           ("b9", "cta", "ダークをタップ")]
BODY = [
    ("b1", "1つ目、明るさの自動調節。", 0.4),
    ("b2", "これがオフだと、暗い場所でも画面がずっと明るいまま。電池がどんどん減ります。", 0.5),
    ("b3", "設定のアクセシビリティ、画面表示とテキストサイズの一番下で、オンにできます。夜に眩しい人にもおすすめです。", 0.9),
    ("b4", "2つ目、位置情報が「常に」のアプリ。", 0.4),
    ("b5", "使っていない時も、裏で場所を調べ続けて、電池を使います。地図アプリ以外は、常にしなくて大丈夫。", 0.5),
    ("b6", "プライバシーとセキュリティの、位置情報サービスで、「使用中のみ」に変えましょう。アプリごとに、ひとつずつ選べます。", 0.9),
    ("b7", "3つ目が意外と効く、ダークモード。", 0.4),
    ("b8", "有機ELのiPhoneは、黒い部分の電池の消費が少ないんです。黒が多い画面ほど、省エネになります。", 0.5),
    ("b9", "画面表示と明るさで、ダークを選ぶだけ。夜だけダークにする、自動の設定もあります。", 0.0),
]
BODY_HOLD = 0.6
CTA = dict(lines=[("電池持ち", WHITE, 110), ("3つ見直そう！", YEL, 120)], spoken="フォローすると、毎日1つ、電池が長持ちする設定を紹介するよ！",
           chip="フォローで毎日1つ")

BW, BH = 400, 860

def finger(ps, x, y):
    fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((x - 30, y - 30, x + 30, y + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))

def page(back, title, crumb=None, dark=False):
    bg, ink = ((0, 0, 0, 255), WHITE) if dark else ((242, 242, 247, 255), INK)
    ps = Image.new("RGBA", (BW, BH), bg)
    txt(ps, (56, 36), "9:41", 22, ink, anchor="lm")
    txt(ps, (24, 84), "‹ " + back, 18, BLUE, bold=False, anchor="lm")
    txt(ps, (24, 128), title, 26 if len(title) > 9 else 32, ink, anchor="lm")
    if crumb: txt(ps, (24, 164), crumb, 13, GRAY, bold=False, anchor="lm")
    return ps

def row(ps, y, h, hi, dark=False):
    rr(ps, (16, y, BW - 16, y + h), 12, (255, 236, 150) if hi else ((28, 28, 30) if dark else WHITE))

def ok_pill(ps, text):
    rra(ps, (50, 640, BW - 50, 696), 28, (52, 199, 89, 235))
    txt(ps, (BW / 2, 668), text, 18, WHITE, anchor="mm")

# ---------------------------------------------------------------- 1) auto-brightness
def brightness(t, T):
    a = T.at
    if t < a["b3"]:                      # control-centre style: brightness stuck at 100%
        ps = grad(BW, BH, (40, 44, 70), (18, 18, 30))
        txt(ps, (BW / 2, 120), "画面の明るさ", 22, WHITE, anchor="mm")
        rra(ps, (150, 150, 250, 380), 40, (245, 245, 250, 255))
        txt(ps, (200, 220), "☀", 40, (255, 204, 0), anchor="mm")
        txt(ps, (BW / 2, 425), "明るさ 100%", 30, WHITE, anchor="mm")
        if t >= a["b2"]:
            p = clamp((t - a["b2"]) / 0.4)
            rra(ps, (50, 640, BW - 50, 696), 28, (255, 59, 48, int(235 * p)))
            if p > 0.5: txt(ps, (BW / 2, 668), "暗い所でもずっと明るい…", 18, WHITE, anchor="mm")
        return ps
    on_at = a["b3"] + 3.2
    on = t >= on_at
    ps = page("アクセシビリティ", "画面表示とテキストサイズ")
    rows = ["文字を太くする", "さらに大きな文字", "コントラストを上げる", "明るさの自動調節"]
    for i, r in enumerate(rows):
        y = 180 + i * 64
        row(ps, y, 56, i == 3 and t >= a["b3"] + 2.4)
        txt(ps, (34, y + 28), r, 18, INK, bold=i == 3, anchor="lm")
        toggle(ps, BW - 86, y + 10, on if i == 3 else False)
    if on_at - 0.35 <= t < on_at + 0.15: finger(ps, BW - 60, 180 + 3 * 64 + 28)
    if on: ok_pill(ps, "明るさが自動で下がる！")
    return ps

# ---------------------------------------------------------------- 2) location "always"
APPS = [("ショッピング", (255, 149, 0)), ("天気", (10, 132, 255)), ("SNS", (175, 82, 222)), ("地図", (52, 199, 89))]
ALWAYS = (0, 2)

def location(t, T):
    a = T.at
    ps = page("プライバシーとセキュリティ", "位置情報サービス")
    for i, (nm, col) in enumerate(APPS):
        y = 180 + i * 64
        fix_at = a["b6"] + 2.6 + 0.8 * ALWAYS.index(i) if i in ALWAYS else None
        fixed = fix_at is not None and t >= fix_at
        bad = i in ALWAYS and not fixed and t >= a["b5"]
        row(ps, y, 56, fixed or bad)
        ImageDraw.Draw(ps).rounded_rectangle((30, y + 11, 64, y + 45), 9, fill=col)
        txt(ps, (80, y + 28), nm, 18, INK, bold=False, anchor="lm")
        val = "使用中のみ" if (fixed or i not in ALWAYS) else "常に"
        txt(ps, (BW - 34, y + 28), val, 16, (255, 59, 48) if val == "常に" else BLUE, bold=val == "常に", anchor="rm")
        if fix_at is not None and fix_at - 0.35 <= t < fix_at + 0.1: finger(ps, BW - 90, y + 28)
    if a["b5"] <= t < a["b6"]:
        p = clamp((t - a["b5"]) / 0.4)
        rra(ps, (50, 640, BW - 50, 696), 28, (255, 59, 48, int(235 * p)))
        if p > 0.5: txt(ps, (BW / 2, 668), "使ってない時もGPSが動く…", 18, WHITE, anchor="mm")
    if t >= a["b6"] + 4.2: ok_pill(ps, "「使用中のみ」にした！")
    return ps

# ---------------------------------------------------------------- 3) dark mode
def darkmode(t, T):
    a = T.at
    pick = a["b9"] + 2.4
    dark = t >= pick
    ps = page("設定", "画面表示と明るさ", dark=dark)
    txt(ps, (30, 172), "外観モード", 15, GRAY, bold=False, anchor="lm")
    rr(ps, (16, 190, BW - 16, 450), 14, (28, 28, 30) if dark else WHITE)
    for j, (lab, scr, ink) in enumerate((("ライト", (250, 250, 252), INK), ("ダーク", (20, 20, 22), WHITE))):
        cx = 120 + j * 160
        d = ImageDraw.Draw(ps)
        d.rounded_rectangle((cx - 48, 214, cx + 48, 384), 14, fill=scr, outline=(120, 120, 130), width=3)
        for k in range(4): d.rounded_rectangle((cx - 34, 236 + k * 28, cx + 34, 252 + k * 28), 5, fill=(200, 200, 205) if j == 0 else (70, 70, 75))
        sel = (j == 1) == dark
        txt(ps, (cx, 410), lab, 17, WHITE if dark else INK, anchor="mm")
        d.ellipse((cx - 13, 422, cx + 13, 448), outline=(150, 150, 160), width=3, fill=BLUE if sel else None)
    if pick - 0.35 <= t < pick + 0.15: finger(ps, 280, 300)
    if a["b8"] <= t < a["b9"]:
        p = clamp((t - a["b8"]) / 0.4)
        rra(ps, (50, 640, BW - 50, 696), 28, (255, 159, 10, int(235 * p)))
        if p > 0.5: txt(ps, (BW / 2, 668), "黒い部分は電池の消費が少ない", 17, WHITE, anchor="mm")
    if dark and t >= pick + 0.3: ok_pill(ps, "ダークモードにした！")
    return ps

def SCREEN(t, T):
    if t >= T.at["b7"]: return darkmode(t, T)
    if t >= T.at["b4"]: return location(t, T)
    return brightness(t, T)

def draw_body(c, t, T): pass

def draw_hook_art(ly, t): pass

def sfx(T):
    a = T.at
    return [("pop", a["b1"]), ("ding", a["b2"]), ("click", a["b3"] + 3.2), ("pop", a["b4"]), ("ding", a["b5"]),
            ("click", a["b6"] + 2.6), ("click", a["b6"] + 3.4), ("pop", a["b7"]), ("click", a["b9"] + 2.4)]

def stills(T):
    a = T.at
    return [1.0, a["b2"] + 1.0, a["b3"] + 3.5, a["b5"] + 1.0, a["b6"] + 4.4, a["b8"] + 1.0, a["b9"] + 2.8, a["cta"] + 1.0]
