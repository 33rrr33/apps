# iPhone隠し神機能① 写真に写った文字を長押しでコピー（テキスト認識表示・iOS 15以降）（v3：ショート＋60秒パート）
import math
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="w20261102_second", title="iPhone隠し神機能", spoken="iPhone隠し、かみ機能",
              hook_split=("iPhone", "隠し神機能"), total=5)
NUM, SLUG = 1, "live_text_copy"
NEXT = "写真の外国語を翻訳"
SCREEN_CROP = (0, 140, 400, 700)          # the photo + the edit menu (skip status bar and toolbar)
HOOK = "写真の文字を手打ち？\n{それ時間のムダ}"
HOOK_SPOKEN = "写真の文字、手打ちは時間のムダです！"
TELOPS = [("b1", "Wi-Fiのパスワードを\n[写真に撮った]"), ("b2", "写真の文字を\n[長押し]"),
          ("b3", "文字がそのまま\n[コピーできる！]"), ("b4", "パスワード欄に\n[ペーストでOK]")]
ACTIONS = [("b1", "b2", "写真アプリで開く"), ("b2", "b3", "文字を長押し"),
           ("b3", "b4", "「コピー」をタップ"), ("b4", "cta", "入力欄でペースト")]
BODY = [
    ("b1", "Wi-Fiのパスワードを、写真に撮ったら、", 0.3),
    ("b2", "写真を開いて、文字を長押ししてください。", 0.3),
    ("b3", "写真の文字が、そのままコピーできます！", 0.3),
    ("b4", "あとは、入力欄にペーストするだけ。", 0.0),
]
BODY_HOLD = 1.0
CTA = dict(lines=[("写真の文字を", WHITE, 96), ("長押しでコピー！", YEL, 120)], spoken="保存して試してね！",
           chip="iOS 15以降・アプリ不要")

PART = dict(
    title="写真の文字をコピー",
    intro="写真に写ったWi-Fiのパスワードや電話番号、見ながら手で打ち込んでいませんか？",
    steps=[
        ("写真アプリで写真を開く", "まず、文字が写っている写真を、写真アプリで開きます。お店のメニューや、Wi-Fiのカードの写真などです。", ("body", "b2")),
        ("文字を長押し", "コピーしたい文字の上を、指で長押しします。", ("b2", "b2+1.3")),
        ("文字が選択される", "すると、普通の文章と同じように、文字が青く選択されます。範囲は、両端の丸をドラッグして調整できます。", ("b2+1.1", "b3")),
        ("「コピー」をタップ", "出てきたメニューの、コピーをタップします。", ("b3", "b4")),
        ("入力欄にペースト", "あとは、パスワードの入力欄などをタップして、ペーストするだけ。打ち間違えの心配もありません。", ("b4", "cta")),
        ("右下のボタンでも", "ちなみに、写真の右下に出る、テキスト認識のボタンを押すと、写真の中の文字をまとめて選べます。", ("b1", "b2")),
    ],
    outro="iOS 15以降のiPhoneなら、アプリなしで使えます。ぜひ試してみてください。",
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

# ---- the photo: a Wi-Fi card on a cafe table ----
PY0, PY1 = 150, 650                      # photo area in screen coords
CARD = (52, 220, 348, 560)
PASS_TXT = "sora2026kumo"
PASS_Y = 500                             # baseline-ish center of the password line
PASS_X = 200

def make_photo():
    im = Image.new("RGBA", (BW, PY1 - PY0), (0, 0, 0, 255))
    im.alpha_composite(grad(BW, PY1 - PY0, (150, 105, 70), (95, 62, 40)), (0, 0))
    d = ImageDraw.Draw(im)
    for y in range(18, PY1 - PY0, 46):                 # wood grain
        d.line((0, y, BW, y + 8), fill=(120, 82, 54), width=2)
    d.ellipse((300, 6, 420, 120), fill=(240, 240, 236)); d.ellipse((322, 28, 398, 98), fill=(120, 75, 45))   # coffee cup
    x0, y0, x1, y1 = CARD[0], CARD[1] - PY0, CARD[2], CARD[3] - PY0
    shadow(im, (x0, y0, x1, y1), 10, blur=8, off=6, a=120)
    rr(im, (x0, y0, x1, y1), 10, (250, 248, 242))
    rr(im, (x0, y0, x1, y0 + 64), 10, (46, 110, 90)); ImageDraw.Draw(im).rectangle((x0, y0 + 40, x1, y0 + 64), fill=(46, 110, 90))
    txt(im, (200, y0 + 33), "FREE Wi-Fi", 28, WHITE, anchor="mm")
    txt(im, (200, y0 + 110), "ネットワーク名", 17, (110, 110, 110), bold=False, anchor="mm")
    txt(im, (200, y0 + 148), "Macun_Cafe", 30, INK, anchor="mm")
    ImageDraw.Draw(im).line((x0 + 30, y0 + 190, x1 - 30, y0 + 190), fill=(220, 215, 205), width=2)
    txt(im, (200, y0 + 226), "パスワード", 17, (110, 110, 110), bold=False, anchor="mm")
    txt(im, (PASS_X, PASS_Y - PY0), PASS_TXT, 34, INK, anchor="mm")
    return im

PHOTO = make_photo()
_pf = font(34)
PASS_BOX = (PASS_X - _pf.getlength(PASS_TXT) / 2 - 4, PASS_Y - 24, PASS_X + _pf.getlength(PASS_TXT) / 2 + 4, PASS_Y + 24)

def times(T):
    return dict(finger=T.at["b2"] + 0.3, press=T.at["b2"] + 0.6, sel=T.at["b2"] + 1.3, menu=T.at["b2"] + 1.5,
                copy=T.at["b3"] + 0.5, sheet=T.at["b4"], tapfield=T.at["b4"] + 0.4, pop=T.at["b4"] + 0.7,
                paste=T.at["b4"] + 1.3, done=T.at["b3"] + 1.0)

def lt_button(ps, x, y, on):
    """The Live Text (テキスト認識表示) button: a rounded square with corner brackets and text lines."""
    rr(ps, (x - 22, y - 22, x + 22, y + 22), 10, (255, 255, 255) if on else (70, 70, 76))
    col = BLUE if on else WHITE
    d = ImageDraw.Draw(ps)
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        cx, cy = x + sx * 12, y + sy * 12
        d.line((cx, cy, cx - sx * 7, cy), fill=col, width=3); d.line((cx, cy, cx, cy - sy * 7), fill=col, width=3)
    for i, w in enumerate((12, 12, 7)):
        d.line((x - 7, y - 5 + i * 5, x - 7 + w, y - 5 + i * 5), fill=col, width=2)

def photos_screen(t, k):
    ps = Image.new("RGBA", (BW, BH), (0, 0, 0, 255))
    txt(ps, (56, 36), "9:41", 22, WHITE, anchor="lm")
    txt(ps, (26, 104), "‹", 40, BLUE, bold=False, anchor="lm")
    txt(ps, (BW / 2, 96), "11月4日", 20, WHITE, anchor="mm")
    txt(ps, (BW / 2, 122), "12:30", 15, GRAY, bold=False, anchor="mm")
    ps.alpha_composite(PHOTO, (0, PY0))
    lt_button(ps, BW - 40, PY1 + 30, False)
    d = ImageDraw.Draw(ps)
    # bottom toolbar: share / heart / info / trash (simple glyphs)
    ty = BH - 92
    d.rounded_rectangle((26, ty - 14, 54, ty + 18), 4, outline=BLUE, width=3); d.line((40, ty - 26, 40, ty + 2), fill=BLUE, width=3)
    d.polygon([(40, ty - 30), (32, ty - 20), (48, ty - 20)], fill=BLUE)
    d.ellipse((128, ty - 14, 146, ty + 4), outline=BLUE, width=3); d.ellipse((140, ty - 14, 158, ty + 4), outline=BLUE, width=3)
    d.ellipse((240, ty - 16, 272, ty + 16), outline=BLUE, width=3); txt(ps, (256, ty), "i", 20, BLUE, anchor="mm")
    d.rectangle((354, ty - 10, 376, ty + 18), outline=BLUE, width=3); d.line((348, ty - 12, 382, ty - 12), fill=BLUE, width=3)
    # selection of the password
    if t >= k["sel"]:
        a = e_at(t, k["sel"], 0.2)
        x0, y0, x1, y1 = PASS_BOX
        fade(ps, a, lambda l: rr(l, (x0, y0, x1, y1), 4, (10, 132, 255, 90)))
        def handles(l):
            dl = ImageDraw.Draw(l)
            dl.line((x0, y0, x0, y1), fill=BLUE, width=3); dl.ellipse((x0 - 7, y0 - 14, x0 + 7, y0), fill=BLUE)
            dl.line((x1, y0, x1, y1), fill=BLUE, width=3); dl.ellipse((x1 - 7, y1, x1 + 7, y1 + 14), fill=BLUE)
        fade(ps, a, handles)
    if k["menu"] <= t < k["copy"] + 0.35:
        a = e_at(t, k["menu"], 0.2)
        def menu(l):
            y = PASS_BOX[1] - 78
            shadow(l, (40, y, 360, y + 54), 12, blur=8, off=4)
            rr(l, (40, y, 360, y + 54), 12, (44, 44, 48))
            hi = k["copy"] - 0.1 <= t
            if hi: rr(l, (42, y + 2, 120, y + 52), 10, (90, 90, 98))
            dl = ImageDraw.Draw(l)
            for xx in (120, 262, 330): dl.line((xx, y + 12, xx, y + 42), fill=(90, 90, 96), width=2)
            txt(l, (81, y + 27), "コピー", 19, WHITE, bold=False, anchor="mm")
            txt(l, (191, y + 27), "すべてを選択", 19, WHITE, bold=False, anchor="mm")
            txt(l, (296, y + 27), "調べる", 19, WHITE, bold=False, anchor="mm")
            txt(l, (345, y + 27), "›", 24, WHITE, bold=False, anchor="mm")
            dl.polygon([(PASS_X - 10, y + 54), (PASS_X + 10, y + 54), (PASS_X, y + 64)], fill=(44, 44, 48))
        fade(ps, a, menu)
    # finger: long press on the password, then taps コピー
    fp = None
    if k["finger"] <= t < k["menu"] + 0.1: fp = (PASS_X + 10, PASS_Y + 6)
    elif k["copy"] - 0.35 <= t < k["copy"] + 0.3: fp = (81, PASS_BOX[1] - 51)
    if fp:
        fx, fy = fp
        if k["press"] <= t < k["sel"]:
            ring = clamp((t - k["press"]) / (k["sel"] - k["press"]))
            ImageDraw.Draw(ps).arc((fx - 44, fy - 44, fx + 44, fy + 44), -90, -90 + 360 * ring, fill=YEL, width=7)
        fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((fx - 30, fy - 30, fx + 30, fy + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))
    return ps

def wifi_screen(t, k):
    """The Wi-Fi password sheet, then paste."""
    ps = Image.new("RGBA", (BW, BH), (242, 242, 247, 255))
    txt(ps, (56, 36), "9:41", 22, INK, anchor="lm")
    txt(ps, (24, 160), "キャンセル", 20, BLUE, bold=False, anchor="lm")
    pasted = t >= k["paste"]
    txt(ps, (BW - 24, 160), "接続", 20, BLUE if pasted else (180, 180, 186), anchor="rm")
    txt(ps, (BW / 2, 198), "“Macun_Cafe”の", 20, INK, bold=False, anchor="mm")
    txt(ps, (BW / 2, 226), "パスワードを入力", 20, INK, bold=False, anchor="mm")
    rr(ps, (16, 310, BW - 16, 370), 12, WHITE)
    txt(ps, (36, 340), "パスワード", 20, INK, bold=False, anchor="lm")
    d = ImageDraw.Draw(ps)
    if pasted:
        p = e_at(t, k["paste"], 0.25)
        n = int(len(PASS_TXT) * p + 0.5)
        for i in range(n): d.ellipse((150 + i * 15, 334, 160 + i * 15, 344), fill=INK)
        if t >= k["paste"] + 0.4:
            fade(ps, e_at(t, k["paste"] + 0.4, 0.3), lambda l: rr(l, (16, 400, BW - 16, 446), 12, (48, 209, 88, 230)))
            if t >= k["paste"] + 0.4: txt(ps, (BW / 2, 423), "打ち間違えゼロ！", 20, WHITE, anchor="mm")
    elif t >= k["tapfield"]:
        if int(t * 2.5) % 2 == 0: d.line((152, 326, 152, 354), fill=BLUE, width=3)
    if k["pop"] <= t < k["paste"]:
        a = e_at(t, k["pop"], 0.2)
        def pop(l):
            rr(l, (130, 248, 250, 292), 12, (44, 44, 48))
            ImageDraw.Draw(l).polygon([(180, 292), (200, 292), (190, 302)], fill=(44, 44, 48))
            txt(l, (190, 270), "ペースト", 19, WHITE, anchor="mm")
        fade(ps, a, pop)
    fp = None
    if k["tapfield"] - 0.25 <= t < k["tapfield"] + 0.2: fp = (230, 340)
    elif k["paste"] - 0.35 <= t < k["paste"] + 0.2: fp = (190, 270)
    if fp:
        fx, fy = fp
        fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((fx - 30, fy - 30, fx + 30, fy + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))
    # keyboard hint at the bottom
    if t >= k["tapfield"]:
        d.rectangle((0, BH - 300, BW, BH), fill=(208, 211, 217))
        for r in range(3):
            for q in range(10 - r):
                x = 6 + r * 18 + q * 39
                rr(ps, (x, BH - 285 + r * 58, x + 33, BH - 237 + r * 58), 6, WHITE)
    return ps

def screen(t, k):
    return photos_screen(t, k) if t < k["sheet"] else wifi_screen(t, k)

def SCREEN(t, T): return screen(t, times(T))

def draw_body(c, t, T):                   # fallback (non-v3 renderers)
    k = times(T)
    big_phone(c, screen(t, k))
    if t < T.at["b2"]:
        telop(c, t, T.body, [("写真の文字を", WHITE)], y0=400, size=96)
    elif t < T.at["b3"]:
        telop(c, t, T.at["b2"], [("文字を長押し", YEL)], y0=400, size=96)
    elif t < T.at["b4"]:
        telop(c, t, T.at["b3"], [("そのままコピー！", YEL)], y0=400, size=96)
    else:
        telop(c, t, T.at["b4"], [("入力欄にペースト", YEL)], y0=400, size=96)
    badge(c, t, k["done"], "iOS 15以降・アプリ不要", 1505, GREEN, size=44)

def draw_hook_art(ly, t):
    x0, y0 = 340, 1170
    rr(ly, (x0, y0, x0 + 400, y0 + 220), 20, (250, 248, 242))
    txt(ly, (x0 + 200, y0 + 70), "パスワード", 30, (110, 110, 110), bold=False, anchor="mm")
    q = (t * 0.7) % 1
    if q > 0.4:
        rra(ly, (x0 + 40, y0 + 110, x0 + 360, y0 + 180), 6, (10, 132, 255, 90))
    txt(ly, (x0 + 200, y0 + 145), PASS_TXT, 46, INK, anchor="mm")

def sfx(T):
    k = times(T)
    return [("click", k["press"]), ("ding", k["sel"]), ("pop", k["menu"]), ("click", k["copy"]),
            ("whoosh", k["sheet"]), ("click", k["tapfield"]), ("pop", k["pop"]), ("click", k["paste"]), ("ding", k["paste"] + 0.4)]

def stills(T):
    k = times(T)
    return [k["press"] + 0.3, k["menu"] + 0.4, k["copy"], k["pop"] + 0.3, k["paste"] + 0.8]
