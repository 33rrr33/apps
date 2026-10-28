# iPhoneの隠し神機能③ 写真の被写体を長押しで切り抜き（iOS 16以降・シリーズ最終回）
import math
from PIL import Image, ImageDraw, ImageFilter
from shortlib import *

SERIES = dict(key="s03_iphone_hidden", title="iPhoneの隠し神機能", spoken="iPhoneの、隠し、かみ機能",
              hook_split=("iPhoneの", "隠し神機能"), total=3)
NUM, SLUG = 3, "lift_subject"
NEXT = "Macの神設定"
BODY = [
    ("b1", "写真に写った、ペットや人を長押しすると、", 0.3),
    ("b2", "背景が消えて、切り抜けます！", 0.3),
    ("b3", "そのままコピーして、メッセージに貼り付けOK。", 0.3),
    ("b4", "iOS 17以降なら、ステッカーにもできます。", 0.0),
]
BODY_HOLD = 0.9
CTA = dict(lines=[("写真の被写体を", WHITE, 96), ("長押しするだけ！", YEL, 120)], spoken="保存して試してね！",
           chip="iOS 16以降・アプリ不要")

# ---- big centered iPhone (same layout as ep01/ep02) ----
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

# ---- the photo: a dog in a park. The dog is its own layer so it can be "lifted". ----
PW_, PH_ = BW, 520
PHOTO_Y = 170

def make_bg_photo():
    im = Image.new("RGBA", (PW_, PH_), (0, 0, 0, 255))
    im.alpha_composite(grad(PW_, 330, (120, 190, 250), (200, 230, 255)), (0, 0))
    im.alpha_composite(grad(PW_, PH_ - 300, (110, 190, 90), (60, 140, 60)), (0, 300))
    d = ImageDraw.Draw(im)
    d.rectangle((300, 150, 322, 320), fill=(110, 80, 50))
    d.ellipse((240, 60, 390, 210), fill=(70, 150, 70))
    d.ellipse((20, 40, 120, 90), fill=(255, 255, 255, 230))
    d.ellipse((70, 30, 160, 85), fill=(255, 255, 255, 230))
    for x in range(0, PW_, 26):
        d.line((x, 330, x + 6, 312), fill=(80, 160, 70), width=3)
    return im

def make_dog():
    im = Image.new("RGBA", (PW_, PH_), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    fur, dark = (232, 178, 110), (170, 110, 60)
    d.ellipse((110, 300, 300, 450), fill=fur)                      # body
    d.rounded_rectangle((130, 400, 165, 490), 16, fill=fur)        # legs
    d.rounded_rectangle((245, 400, 280, 490), 16, fill=fur)
    d.ellipse((285, 300, 345, 340), fill=fur)                      # tail
    d.ellipse((100, 190, 250, 330), fill=fur)                      # head
    d.polygon([(105, 220), (120, 150), (160, 205)], fill=dark)     # ears
    d.polygon([(245, 220), (230, 150), (190, 205)], fill=dark)
    d.ellipse((140, 245, 160, 265), fill=INK); d.ellipse((190, 245, 210, 265), fill=INK)
    d.ellipse((152, 275, 198, 320), fill=(250, 235, 215))
    d.ellipse((165, 280, 185, 294), fill=INK)
    return im

BG_PHOTO, DOG = make_bg_photo(), make_dog()
GLOW = DOG.getchannel("A").filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.GaussianBlur(4))

def times(T):
    return dict(finger=T.at["b1"] + 0.5, press=T.at["b1"] + 1.0, glow=T.at["b2"], menu=T.at["b2"] + 0.7,
                copy=T.at["b3"] + 0.2, msgs=T.at["b3"] + 0.6, paste_pop=T.at["b3"] + 1.0, paste=T.at["b3"] + 1.6,
                sticker=T.at["b4"] + 0.4, done=T.at["b2"] + 0.5, extra=T.at["b4"] + 0.9)

def cutout(scale=1.0, glow=0.0):
    """The lifted dog with a white outline, cropped to its bounding box."""
    ly = Image.new("RGBA", (PW_, PH_), (0, 0, 0, 0))
    if glow > 0:
        g = Image.new("RGBA", (PW_, PH_), (255, 255, 255, 255)); g.putalpha(GLOW.point(lambda v: int(v * glow)))
        ly.alpha_composite(g)
    ly.alpha_composite(DOG)
    ly = ly.crop(ly.getbbox())
    if scale != 1.0: ly = ly.resize((int(ly.width * scale), int(ly.height * scale)), Image.BICUBIC)
    return ly

def photos_screen(t, k):
    ps = Image.new("RGBA", (BW, BH), (0, 0, 0, 255))
    txt(ps, (56, 36), "9:41", 22, WHITE, anchor="lm")
    txt(ps, (24, 96), "‹ 写真", 24, BLUE, bold=False, anchor="lm")
    photo = BG_PHOTO.copy()
    lifted = t >= k["glow"]
    if lifted:
        p = e_at(t, k["glow"], 0.4)
        photo.alpha_composite(Image.new("RGBA", (PW_, PH_), (0, 0, 0, int(150 * p))))
    else:
        photo.alpha_composite(DOG)
    ps.alpha_composite(photo, (0, PHOTO_Y))
    if lifted:
        p = e_at(t, k["glow"], 0.4)
        co = cutout(1 + 0.06 * p, glow=p)
        bx, by, _, _ = DOG.getbbox()
        ox = int(bx - (co.width - (DOG.getbbox()[2] - bx)) / 2); oy = int(PHOTO_Y + by - 14 * p - (co.height - (DOG.getbbox()[3] - by)) / 2)
        # shimmer: a light band sweeps across the subject once
        s = (t - k["glow"]) / 0.7
        if 0 < s < 1:
            band = Image.new("RGBA", co.size, (0, 0, 0, 0)); bd = ImageDraw.Draw(band)
            x = -80 + s * (co.width + 160)
            bd.polygon([(x, 0), (x + 50, 0), (x - 30, co.height), (x - 80, co.height)], fill=(255, 255, 255, 150))
            band.putalpha(Image.fromarray(np.minimum(np.array(band.getchannel("A")), np.array(co.getchannel("A")))))
            co = co.copy(); co.alpha_composite(band)
        ps.alpha_composite(co, (ox, oy))
        if t >= k["menu"]:
            a = e_at(t, k["menu"], 0.25)
            def menu(l):
                y = oy - 70
                shadow(l, (60, y, 340, y + 56), 14, blur=8, off=4)
                rr(l, (60, y, 340, y + 56), 14, (250, 250, 252))
                ImageDraw.Draw(l).line((160, y + 10, 160, y + 46), fill=(200, 200, 205), width=2)
                hi = k["copy"] <= t < k["msgs"]
                if hi: rr(l, (62, y + 2, 158, y + 54), 12, (200, 220, 255))
                txt(l, (110, y + 28), "コピー", 20, INK, bold=False, anchor="mm")
                txt(l, (250, y + 28), "共有…", 20, INK, bold=False, anchor="mm")
            fade(ps, a, menu)
    # thumbnails strip
    for i in range(6):
        rr(ps, (14 + i * 64, BH - 120, 72 + i * 64, BH - 62), 6, (60 + i * 20, 90, 120 - i * 8))
    return ps

def messages_screen(t, k):
    ps = Image.new("RGBA", (BW, BH), (255, 255, 255, 255))
    txt(ps, (56, 36), "9:41", 22, INK, anchor="lm")
    ImageDraw.Draw(ps).ellipse((BW / 2 - 28, 70, BW / 2 + 28, 126), fill=(170, 175, 185))
    txt(ps, (BW / 2, 140), "ゆうき", 18, INK, bold=False, anchor="mm")
    ImageDraw.Draw(ps).line((0, 165, BW, 165), fill=(225, 225, 230), width=2)
    rr(ps, (20, 196, 270, 250), 22, (233, 233, 235)); txt(ps, (40, 223), "週末なにしてた？", 20, INK, bold=False, anchor="lm")
    # input field + paste popup
    rr(ps, (20, BH - 90, BW - 20, BH - 44), 23, WHITE, outline=(200, 200, 206), width=2)
    if k["paste_pop"] <= t < k["paste"]:
        a = e_at(t, k["paste_pop"], 0.2)
        def pop(l):
            rr(l, (40, BH - 150, 150, BH - 104), 12, (40, 40, 44))
            txt(l, (95, BH - 127), "ペースト", 18, WHITE, anchor="mm")
        fade(ps, a, pop)
    if t >= k["paste"]:
        p = back_out(clamp((t - k["paste"]) / 0.35))
        co = cutout(0.52 * max(0.05, p), glow=1.0)
        ps.alpha_composite(co, (BW - 30 - co.width, 280))
        txt(ps, (BW - 30, 290 + int(co.height) + 14), "既読", 14, GRAY, bold=False, anchor="ra")
    if t >= k["sticker"]:
        # iOS 17+: the same cutout stuck onto the earlier bubble as a sticker
        p = e_at(t, k["sticker"], 0.35)
        st = cutout(0.34, glow=1.0).rotate(-14, resample=Image.BICUBIC, expand=True)
        y = int(120 + 70 * p)
        ps.alpha_composite(st, (190, y))
    return ps

def draw_body(c, t, T):
    k = times(T)
    ps = photos_screen(t, k) if t < k["msgs"] else messages_screen(t, k)
    # finger: long press on the dog, then taps "コピー", then "ペースト"
    fp = None
    if k["finger"] <= t < k["menu"]: fp = (175, PHOTO_Y + 300)
    elif k["menu"] <= t < k["msgs"]: fp = (110, PHOTO_Y + 180 - 40) if t >= k["copy"] - 0.2 else None
    elif k["msgs"] + 0.1 <= t < k["paste"] + 0.1: fp = (95, BH - 127) if t >= k["paste_pop"] + 0.2 else (BW / 2, BH - 67)
    if fp:
        fx, fy = fp
        d = ImageDraw.Draw(ps)
        if k["press"] <= t < k["glow"]:
            ring = clamp((t - k["press"]) / (k["glow"] - k["press"]))
            d.arc((fx - 46, fy - 46, fx + 46, fy + 46), -90, -90 + 360 * ring, fill=YEL, width=7)
        fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((fx - 30, fy - 30, fx + 30, fy + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))
    big_phone(c, ps)
    if t < T.at["b2"]:
        telop(c, t, T.body, [("被写体を長押し", WHITE)], y0=400, size=100)
    elif t < T.at["b3"]:
        telop(c, t, T.at["b2"], [("背景が消えて切り抜き！", YEL)], y0=400, size=96)
    elif t < T.at["b4"]:
        telop(c, t, T.at["b3"], [("コピー → 貼り付けOK", YEL)], y0=400, size=100)
    else:
        telop(c, t, T.at["b4"], [("ステッカーにもできる", YEL)], y0=400, size=100)
    if t < T.at["b4"]:
        badge(c, t, k["done"], "アプリ不要・一瞬で切り抜き", 1505, GREEN, size=42)
    else:
        badge(c, t, k["extra"], "iOS 17以降", 1505, PURPLE, size=44)

def draw_hook_art(ly, t):
    co = cutout(0.55, glow=1.0)
    y = 1180 + int(10 * math.sin(t * 4))
    ly.alpha_composite(co, (int(540 - co.width / 2), y))
    d = ImageDraw.Draw(ly)
    for i in range(3):
        a = (t * 2 + i * 2.1) % (2 * math.pi)
        x, yy = 540 + 150 * math.cos(a), y + 90 + 90 * math.sin(a)
        d.ellipse((x - 8, yy - 8, x + 8, yy + 8), fill=(255, 236, 150))

def sfx(T):
    k = times(T)
    return [("click", k["press"]), ("whoosh", k["glow"]), ("ding", k["glow"] + 0.3), ("pop", k["menu"]),
            ("click", k["copy"]), ("pop", k["paste_pop"]), ("pop", k["paste"]), ("pop", k["sticker"])]

def stills(T):
    k = times(T)
    return [k["press"] + 0.3, k["menu"] + 0.4, k["paste_pop"] + 0.3, k["paste"] + 0.6, k["extra"] + 0.6]
