# 11/30 12:00 13秒1ネタ（容量・plan w8）「非使用のAppを取り除く」でデータを残したまま容量を空ける（画面録画風・劇的時短）
# 11/25ルール：指示語なし＋冒頭は主役（残り0.8GB・赤いストレージバー）を超拡大＋赤丸
# 根拠：設定→一般→iPhoneストレージ→推奨事項「非使用のAppを取り除く」。使っていないAppを自動で取り除き、書類とデータは残る（再インストールで元通り）
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="b20261127_first", title="iPhone爆速神操作", spoken="iPhone爆速、かみ操作",
              hook_split=("iPhone", "爆速神操作"), total=5, offset=15)
TITLE = "iPhoneの容量がいっぱいの人、データを消さずに空く… #Shorts"
NUM, SLUG = 4, "offload_apps"
NEXT = "次も容量の話"
SCREEN_CROP = (0, 40, 400, 760)
DURATION, END_CARD = 14.5, False
TAGS = {"length": "13秒1ネタ", "layout": "画面録画風", "hook_type": "煽り型", "title_type": "…止め", "topic_kind": "容量",
        "first_frame": "超拡大＋赤丸"}
LAYOUT, FOCUS_Y, CAPTION_Y = "rec", 400, 1260
HOOK = "{容量いっぱい}の人\nデータ消さないで！"
HOOK_SPOKEN = "iPhoneの容量がいっぱいの人、データは消さないで！"
TELOPS = [("b1", "一般 →\n[iPhoneストレージ]"), ("b2", "[非使用のAppを取り除く]\nを有効に"),
          ("b3", "写真やデータは{そのまま}\nで容量が空く")]
ACTIONS = [("b1", "b2", "設定 → 一般"), ("b2", "b3", "使ってないアプリだけ自動で外す"),
           ("b3", "cta", "アイコンを押せば元通り")]
BODY = [
    ("b1", "一般の、iPhoneストレージを開いて、", 0.1),
    ("b2", "非使用のAppを取り除くを有効にするだけ。", 0.1),
    ("b3", "データは残ったまま、容量が空きます！", 0.0),
]
BODY_HOLD = 0.4
CTA = dict(lines=[("何GB空いたか", WHITE, 100), ("コメントで教えて！", YEL, 100)], spoken="何ギガ空いたか、コメントで！",
           chip="フォローで毎日1つ")

BW, BH = 400, 860
SEGS = [((255, 59, 48), 0.30), ((255, 149, 0), 0.22), ((255, 204, 0), 0.18), ((88, 86, 214), 0.16), ((142, 142, 147), 0.12)]

def finger(ps, x, y):
    fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((x - 30, y - 30, x + 30, y + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))

def pill(ps, text, col):
    rra(ps, (40, 640, BW - 40, 696), 28, col + (235,))
    txt(ps, (BW / 2, 668), text, 17, WHITE, anchor="mm")

def bar(ps, box, free):
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(ps)
    d.rounded_rectangle(box, 8, fill=(229, 229, 234))
    used = 1 - free
    x = x0
    for col, f in SEGS:
        w = (x1 - x0) * used * f / sum(s[1] for s in SEGS)
        d.rectangle((x, y0, x + w, y1), fill=col)
        x += w

def zoom(t, T):
    ps = Image.new("RGBA", (BW, BH), (242, 242, 247, 255))
    d = ImageDraw.Draw(ps)
    txt(ps, (BW / 2, 110), "iPhoneストレージ", 26, INK, anchor="mm")
    bar(ps, (24, 160, BW - 24, 220), 0.006)
    txt(ps, (BW / 2, 290), "残り 0.8GB", 52, (255, 59, 48), anchor="mm")
    d.ellipse((40, 238, BW - 40, 342), outline=(255, 59, 48), width=7)
    rr(ps, (30, 370, BW - 30, 430), 14, (20, 20, 26))
    txt(ps, (BW / 2, 400), "ストレージがほぼいっぱいです", 18, WHITE, anchor="mm")
    pill(ps, "写真を消す前に、これだけやって", (255, 59, 48))
    return ps

def SCREEN(t, T):
    a = T.at
    if t < a["b1"]: return zoom(t, T)
    on_at = a["b2"] + 1.2
    on = t >= on_at
    ps = Image.new("RGBA", (BW, BH), (242, 242, 247, 255))
    d = ImageDraw.Draw(ps)
    txt(ps, (56, 84), "9:41", 24, INK, anchor="lm")
    txt(ps, (24, 124), "‹ 一般", 18, BLUE, bold=False, anchor="lm")
    txt(ps, (24, 162), "iPhoneストレージ", 26, INK, anchor="lm")
    free = 0.006 + (0.12 * clamp((t - on_at) / 1.0) if on else 0)
    rr(ps, (16, 186, BW - 16, 262), 14, WHITE)
    bar(ps, (30, 200, BW - 30, 222), free)
    gb = 0.8 + 15.4 * clamp((t - on_at) / 1.0) if on else 0.8
    txt(ps, (30, 244), f"残り {gb:.1f}GB", 16, (52, 199, 89) if on else (255, 59, 48), anchor="lm")
    rr(ps, (16, 278, BW - 16, 420), 14, (255, 236, 150) if t >= a["b2"] else WHITE)
    txt(ps, (34, 304), "推奨事項", 13, GRAY, bold=False, anchor="lm")
    txt(ps, (34, 334), "非使用のAppを取り除く", 19, INK, anchor="lm")
    txt(ps, (34, 362), "使っていないAppを自動で取り除きます。", 12, GRAY, bold=False, anchor="lm")
    txt(ps, (34, 380), "書類とデータは保持されます。", 12, GRAY, bold=False, anchor="lm")
    rr(ps, (BW - 130, 386, BW - 30, 412), 13, (52, 199, 89) if on else (230, 230, 236))
    txt(ps, (BW - 80, 399), "有効にした" if on else "有効にする", 13, WHITE if on else BLUE, anchor="mm")
    if on_at - 0.35 <= t < on_at + 0.1: finger(ps, BW - 80, 399)
    if t < a["b2"]: pill(ps, "設定 → 一般 → iPhoneストレージ", (10, 132, 255))
    elif not on: pill(ps, "「有効にする」をタップ", (10, 132, 255))
    else: pill(ps, "データはそのまま、容量が空いた！", (52, 199, 89))
    return ps

def draw_body(c, t, T): pass

def draw_hook_art(ly, t): pass

def sfx(T):
    a = T.at
    return [("ding", 0.3), ("pop", a["b1"]), ("click", a["b2"] + 1.2), ("ding", a["b2"] + 2.2)]

def stills(T):
    a = T.at
    return [0.05, 1.0, a["b1"] + 0.6, a["b2"] + 0.6, a["b2"] + 2.4, a["b3"] + 0.8, a["cta"] + 0.6]
