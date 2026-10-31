# iPhone隠し神機能② 写真の中の外国語をその場で翻訳（写真を開く→右下のテキスト認識ボタン→「翻訳」・iOS 16以降）（v3）
import math
from PIL import Image, ImageDraw, ImageFilter
from shortlib import *

SERIES = dict(key="w20261102_second", title="iPhone隠し神機能", spoken="iPhone隠し、かみ機能",
              hook_split=("iPhone", "隠し神機能"), total=5)
NUM, SLUG = 2, "live_text_translate"
NEXT = "グリッドと水平器"
SCREEN_CROP = (0, 140, 400, 700)          # the photo with its Live Text / 翻訳 buttons
HOOK = "9割が知らない\n[写真の翻訳ボタン]"
HOOK_SPOKEN = "9割が知らない、写真の翻訳ボタン！"
TELOPS = [("b1", "外国語のメニュー\n{読めない…}"), ("b2", "右下の\n[テキスト認識ボタン]"),
          ("b3", "左下の\n[「翻訳」をタップ]"), ("b4", "写真がそのまま\n[日本語に！]")]
ACTIONS = [("b1", "b2", "写真アプリで開く"), ("b2", "b3", "右下のボタンをタップ"),
           ("b3", "b4", "「翻訳」をタップ"), ("b4", "cta", "写真の上に日本語")]
BODY = [
    ("b1", "外国語のメニューを、写真に撮ったら、", 0.3),
    ("b2", "右下の、テキスト認識ボタンをタップ。", 0.3),
    ("b3", "左下の、翻訳を押すと、", 0.3),
    ("b4", "写真の文字が、そのまま日本語に！", 0.0),
]
BODY_HOLD = 1.6
CTA = dict(lines=[("右下のボタン→", WHITE, 96), ("「翻訳」だけ！", YEL, 120)], spoken="保存して試してね！",
           chip="アプリ不要・旅行で大活躍")

PART = dict(
    title="写真の外国語を翻訳",
    intro="海外旅行のメニューや、外国語の看板。翻訳アプリに打ち込まなくても、写真アプリだけで翻訳できます。",
    steps=[
        ("写真アプリで写真を開く", "まず、外国語が写っている写真を、写真アプリで開きます。その場でカメラで撮った写真でも大丈夫です。", ("body", "b2")),
        ("右下のボタンをタップ", "文字が写っていると、写真の右下に、テキスト認識のボタンが出ます。これをタップします。", ("b2", "b2+1.2")),
        ("文字が認識される", "写真の中の文字が認識されて、選べる状態になります。", ("b2+1.0", "b3")),
        ("左下の「翻訳」をタップ", "外国語の文字なら、左下に、翻訳のボタンが出てくるので、タップします。", ("b3", "b4")),
        ("写真の上に日本語が出る", "すると、写真の文字の上に、日本語の訳がそのまま重なって表示されます。もう一度押すと、元に戻ります。", ("b4", "cta")),
    ],
    outro="海外旅行や、外国語の説明書を読むときに便利です。ぜひ試してみてください。",
)

# ---- big centered iPhone (same layout as the iPhone series) ----
BW, BH = 400, 860
BX0, BY0 = 340, 560

def big_phone(c, ps):
    ly = Image.new("RGBA", (BW + 40, BH + 40), (0, 0, 0, 0))
    rr(ly, (0, 0, BW + 39, BH + 39), 64, (36, 36, 40), outline=(120, 120, 130), width=5)
    m = Image.new("L", (BW, BH), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, BW - 1, BH - 1), 52, fill=255)
    rr(ps, (BW / 2 - 64, 16, BW / 2 + 64, 52), 18, (0, 0, 0))
    ps.putalpha(Image.fromarray(np.minimum(np.array(ps.getchannel("A")), np.array(m))))
    ly.alpha_composite(ps, (20, 20))
    shadow(c, (BX0 - 20, BY0 - 20, BX0 + BW + 20, BY0 + BH + 20), 64, blur=26, off=18, a=160)
    c.alpha_composite(ly, (BX0 - 20, BY0 - 20))

# ---- the photo: an English chalkboard menu outside a cafe ----
PY0, PY1 = 150, 650
BOARD = (40, 30, 360, 420)                 # in photo coords
ROWS = [("MENU", "メニュー", 78, 40), ("Iced Latte", "アイスラテ", 155, 28), ("Croissant", "クロワッサン", 212, 28),
        ("Tomato Soup", "トマトスープ", 269, 28), ("Lemon Cake", "レモンケーキ", 326, 28), ("Open 8am-6pm", "営業 8時〜18時", 385, 22)]
CHALK = (232, 236, 228)
BOARD_COL = (38, 62, 50)

def make_photo():
    im = Image.new("RGBA", (BW, PY1 - PY0), (0, 0, 0, 255))
    im.alpha_composite(grad(BW, PY1 - PY0, (196, 186, 170), (150, 140, 128)), (0, 0))
    d = ImageDraw.Draw(im)
    for x in range(0, BW, 40): d.line((x, 0, x, PY1 - PY0), fill=(178, 168, 152), width=2)   # wall planks
    x0, y0, x1, y1 = BOARD
    shadow(im, BOARD, 8, blur=8, off=6, a=130)
    rr(im, (x0 - 10, y0 - 10, x1 + 10, y1 + 10), 8, (120, 82, 50))
    rr(im, BOARD, 4, BOARD_COL)
    for en, _, y, s in ROWS:
        txt(im, (200, y), en, s, CHALK, anchor="mm")
    d.line((110, 112, 290, 112), fill=CHALK, width=2)
    return im.filter(ImageFilter.GaussianBlur(0.4))

PHOTO = make_photo()

def make_translated():
    im = PHOTO.copy()
    for en, ja, y, s in ROWS:
        w = font(s).getlength(en)
        box = (200 - w / 2 - 8, y - s * 0.75, 200 + w / 2 + 8, y + s * 0.75)
        rr(im, box, 6, (48, 74, 61))
        js = s
        while font(js).getlength(ja) > max(w + 24, 120) and js > 14: js -= 1
        txt(im, (200, y), ja, js, WHITE, anchor="mm")
    return im

PHOTO_JA = make_translated()

def times(T):
    return dict(finger=T.at["b2"] + 0.5, lt=T.at["b2"] + 1.1, quick=T.at["b2"] + 1.6,
                tap=T.at["b3"] + 0.9, ja=T.at["b3"] + 1.1, done=T.at["b4"] + 0.6)

def lt_button(ps, x, y, on):
    """The Live Text (テキスト認識表示) button: corner brackets with text lines."""
    fade(ps, 1.0, lambda l: rr(l, (x - 24, y - 24, x + 24, y + 24), 12, (10, 132, 255, 255) if on else (40, 40, 46, 200)))
    d = ImageDraw.Draw(ps)
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        cx, cy = x + sx * 12, y + sy * 12
        d.line((cx, cy, cx - sx * 7, cy), fill=WHITE, width=3); d.line((cx, cy, cx, cy - sy * 7), fill=WHITE, width=3)
    for i, w in enumerate((12, 12, 7)):
        d.line((x - 7, y - 5 + i * 5, x - 7 + w, y - 5 + i * 5), fill=WHITE, width=2)

def translate_pill(ps, x, y, on, a):
    def f(l):
        w = 116
        rr(l, (x, y - 24, x + w, y + 24), 24, (10, 132, 255, 255) if on else (40, 40, 46, 215))
        dl = ImageDraw.Draw(l)
        # small "translate" glyph: two overlapping speech squares
        rr(l, (x + 14, y - 12, x + 32, y + 6), 4, None, outline=WHITE, width=2)
        rr(l, (x + 22, y - 4, x + 40, y + 14), 4, (10, 132, 255, 255) if on else (40, 40, 46, 255), outline=WHITE, width=2)
        txt(l, (x + 48, y), "翻訳", 20, WHITE, anchor="lm")
    fade(ps, a, f)

def screen(t, k):
    ps = Image.new("RGBA", (BW, BH), (0, 0, 0, 255))
    txt(ps, (56, 36), "9:41", 22, WHITE, anchor="lm")
    txt(ps, (26, 104), "‹", 40, BLUE, bold=False, anchor="lm")
    txt(ps, (BW / 2, 96), "11月5日", 20, WHITE, anchor="mm")
    txt(ps, (BW / 2, 122), "10:12", 15, GRAY, bold=False, anchor="mm")
    if t >= k["ja"]:
        a = e_at(t, k["ja"], 0.35)
        ph = Image.blend(PHOTO, PHOTO_JA, a)
    else:
        ph = PHOTO.copy()
        if t >= k["lt"]:                                     # Live Text on: the photo dims, the text is lifted out
            a = e_at(t, k["lt"], 0.3)
            dim = Image.new("RGBA", ph.size, (0, 0, 0, int(80 * a)))
            ph.alpha_composite(dim)
            for en, _, y, s in ROWS:
                w = font(s).getlength(en)
                fade(ph, a, lambda l, w=w, y=y, s=s: rr(l, (200 - w / 2 - 6, y - s * 0.7, 200 + w / 2 + 6, y + s * 0.7), 5, (255, 255, 255, 40)))
                txt(ph, (200, y), en, s, CHALK, anchor="mm")
    ps.alpha_composite(ph, (0, PY0))
    by = PY1 - 34
    lt_button(ps, BW - 40, by, t >= k["lt"])
    if t >= k["quick"]:
        translate_pill(ps, 16, by, t >= k["tap"], e_at(t, k["quick"], 0.25))
    d = ImageDraw.Draw(ps)
    ty = BH - 92                                             # bottom toolbar: share / heart / info / trash
    d.rounded_rectangle((26, ty - 14, 54, ty + 18), 4, outline=BLUE, width=3); d.line((40, ty - 26, 40, ty + 2), fill=BLUE, width=3)
    d.polygon([(40, ty - 30), (32, ty - 20), (48, ty - 20)], fill=BLUE)
    d.ellipse((128, ty - 14, 146, ty + 4), outline=BLUE, width=3); d.ellipse((140, ty - 14, 158, ty + 4), outline=BLUE, width=3)
    d.ellipse((240, ty - 16, 272, ty + 16), outline=BLUE, width=3); txt(ps, (256, ty), "i", 20, BLUE, anchor="mm")
    d.rectangle((354, ty - 10, 376, ty + 18), outline=BLUE, width=3); d.line((348, ty - 12, 382, ty - 12), fill=BLUE, width=3)
    # finger: taps the Live Text button, then 翻訳
    fp = None
    if k["finger"] <= t < k["lt"] + 0.25: fp = (BW - 40, by)
    elif k["tap"] - 0.4 <= t < k["tap"] + 0.25: fp = (74, by)
    if fp:
        fx, fy = fp
        fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((fx - 30, fy - 30, fx + 30, fy + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))
    return ps

def SCREEN(t, T): return screen(t, times(T))

def draw_body(c, t, T):                   # fallback (non-v3 renderers)
    k = times(T)
    big_phone(c, screen(t, k))
    if t < T.at["b2"]:
        telop(c, t, T.body, [("外国語のメニュー", WHITE)], y0=400, size=96)
    elif t < T.at["b3"]:
        telop(c, t, T.at["b2"], [("右下のボタンをタップ", YEL)], y0=400, size=88)
    elif t < T.at["b4"]:
        telop(c, t, T.at["b3"], [("「翻訳」をタップ", YEL)], y0=400, size=96)
    else:
        telop(c, t, T.at["b4"], [("そのまま日本語に！", YEL)], y0=400, size=96)
    badge(c, t, k["done"], "アプリ不要・写真アプリだけ", 1505, GREEN, size=44)

def draw_hook_art(ly, t):
    x0, y0 = 340, 1170
    rr(ly, (x0, y0, x0 + 400, y0 + 220), 12, BOARD_COL)
    q = (t * 0.7) % 1
    txt(ly, (x0 + 200, y0 + 110), "メニュー" if q > 0.5 else "MENU", 70, CHALK, anchor="mm")

def sfx(T):
    k = times(T)
    return [("click", k["lt"]), ("pop", k["quick"]), ("click", k["tap"]), ("whoosh", k["ja"]), ("ding", k["ja"] + 0.4)]

def stills(T):
    k = times(T)
    return [k["lt"] - 0.1, k["quick"] + 0.5, k["tap"], k["ja"] + 0.8, k["done"] + 0.8]
