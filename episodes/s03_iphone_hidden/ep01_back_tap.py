# iPhoneの隠し神機能① 背面タップでスクショ（iPhone 8以降・iOS 14以降）
import math
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="s03_iphone_hidden", title="iPhoneの隠し神機能", spoken="iPhoneの、隠し、かみ機能",
              hook_split=("iPhoneの", "隠し神機能"), total=3)
NUM, SLUG = 1, "back_tap"
NEXT = "スペースキーでカーソル移動"
BODY = [
    ("b1", "iPhoneの背中を、トントンと2回たたくだけで、", 0.3),
    ("b2", "スクリーンショットが撮れます！", 0.3),
    ("b3", "設定の、背面タップから選ぶだけ。", 0.3),
    ("b4", "3回タップにも、別の機能を割り当てられます。", 0.0),
]
BODY_HOLD = 0.9
CTA = dict(lines=[("設定 → アクセシビリティ", WHITE, 84), ("→ タッチ → 背面タップ", YEL, 92)], spoken="保存して試してね！",
           chip="iPhone 8以降・iOS 14以降")

# ---- big centered iPhone (this series is iPhone-only) ----
BW, BH = 400, 860
BX0, BY0 = 340, 560

def big_phone(c, ps, tilt=0.0):
    ly = Image.new("RGBA", (BW + 40, BH + 40), (0, 0, 0, 0))
    rr(ly, (0, 0, BW + 39, BH + 39), 64, (36, 36, 40), outline=(120, 120, 130), width=5)
    m = Image.new("L", (BW, BH), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, BW - 1, BH - 1), 52, fill=255)
    rr(ps, (BW / 2 - 64, 16, BW / 2 + 64, 52), 18, (0, 0, 0))
    ps = ps.copy(); ps.putalpha(Image.fromarray(np.minimum(np.array(ps.getchannel("A")), np.array(m))))
    ly.alpha_composite(ps, (20, 20))
    if tilt: ly = ly.rotate(tilt, resample=Image.BICUBIC, expand=True)
    shadow(c, (BX0 - 20, BY0 - 20, BX0 + BW + 20, BY0 + BH + 20), 64, blur=26, off=18, a=160)
    c.alpha_composite(ly, (int(BX0 + BW / 2 - ly.width / 2), int(BY0 + BH / 2 - ly.height / 2)))

def status(ps, dark=True):
    txt(ps, (56, 36), "9:41", 22, INK if dark else WHITE, anchor="lm")

def times(T):
    return dict(tap1=T.at["b1"] + 1.2, tap2=T.at["b1"] + 1.55, shot=T.at["b2"] + 0.1,
                s_acc=T.at["b3"] + 0.1, s_touch=T.at["b3"] + 0.7, s_back=T.at["b3"] + 1.3,
                triple=T.at["b4"] + 0.3, pick=T.at["b4"] + 1.4,
                done=T.at["b2"] + 0.7, extra=T.at["b4"] + 0.6)

def recipe_screen(t, k):
    ps = Image.new("RGBA", (BW, BH), (255, 255, 255, 255)); status(ps)
    txt(ps, (30, 90), "週末の", 34, INK); txt(ps, (30, 134), "カフェ巡りメモ", 34, INK)
    img = grad(BW - 60, 260, (214, 150, 90), (120, 70, 40))
    ImageDraw.Draw(img).ellipse((120, 70, 220, 170), fill=(250, 245, 235))
    ps.alpha_composite(img, (30, 190))
    for i in range(7):
        rr(ps, (30, 480 + i * 38, BW - 30 - (80 if i % 3 == 2 else 0), 496 + i * 38), 6, (225, 225, 232))
    if k["shot"] <= t < k["s_acc"]:
        fl = clamp(1 - (t - k["shot"]) / 0.25)
        if fl > 0: ps.alpha_composite(Image.new("RGBA", (BW, BH), (255, 255, 255, int(255 * fl))))
        # the screenshot thumbnail shrinks into the lower-left corner
        p = ease_out((t - k["shot"] - 0.15) / 0.5)
        if p > 0:
            w = int(BW - (BW - 120) * p); h = int(BH - (BH - 258) * p)
            th = Image.new("RGBA", (BW, BH), (255, 255, 255, 255))
            th.alpha_composite(img.resize((BW - 60, 260)), (30, 190))
            th = th.resize((max(10, w), max(10, h)))
            x = int(20 * p); y = int((BH - h - 30) * p)
            rr(ps, (x - 4, y - 4, x + th.width + 4, y + th.height + 4), 10, WHITE, outline=(200, 200, 205), width=2)
            ps.alpha_composite(th, (x, y))
    return ps

def settings_screen(title, rows, hi=None, checks=(), back=None):
    ps = Image.new("RGBA", (BW, BH), (242, 242, 247, 255)); status(ps)
    if back: txt(ps, (24, 84), "‹ " + back, 22, BLUE, bold=False, anchor="lm")
    txt(ps, (24, 132), title, 38, INK, anchor="lm")
    y = 180
    for i, r in enumerate(rows):
        rr(ps, (16, y, BW - 16, y + 70), 14, WHITE)
        if i == hi:
            rr(ps, (16, y, BW - 16, y + 70), 14, (255, 236, 150))
        txt(ps, (36, y + 35), r, 24, INK, bold=False, anchor="lm")
        if r in checks: check(ps, BW - 70, y + 24, 24, BLUE, 4)
        else: txt(ps, (BW - 40, y + 35), "›", 30, GRAY, anchor="rm")
        y += 82
    return ps

def phone_screen(t, k):
    if t < k["s_acc"]:
        return recipe_screen(t, k)
    if t < k["s_touch"]:
        return settings_screen("アクセシビリティ", ["VoiceOver", "ズーム", "画面表示とテキストサイズ", "動作", "タッチ"], hi=4 if t > k["s_acc"] + 0.6 else None, back="設定")
    if t < k["s_back"]:
        return settings_screen("タッチ", ["AssistiveTouch", "簡易アクセス", "触覚タッチ", "画面をタップしてスリープ解除", "背面タップ"], hi=4 if t > k["s_touch"] + 0.6 else None, back="アクセシビリティ")
    if t < k["triple"]:
        return settings_screen("背面タップ", ["ダブルタップ", "トリプルタップ"], hi=0, back="タッチ") if t < k["s_back"] + 0.5 else \
               settings_screen("ダブルタップ", ["なし", "Appスイッチャー", "コントロールセンター", "スクリーンショット"], hi=3, checks=("スクリーンショット",), back="背面タップ")
    if t < k["pick"]:
        return settings_screen("背面タップ", ["ダブルタップ", "トリプルタップ"], hi=1, back="タッチ")
    return settings_screen("トリプルタップ", ["なし", "Appスイッチャー", "コントロールセンター", "消音"], hi=2, checks=("コントロールセンター",), back="背面タップ")

def tap_fx(c, t, at):
    """'トン！' ripple beside the phone for a back tap at time `at`."""
    if not (at <= t < at + 0.6): return
    p = (t - at) / 0.6
    ly = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ly)
    for r0 in (0, 0.25):
        q = clamp(p - r0)
        r = 40 + q * 160
        d.ellipse((BX0 + BW + 30 - r, 980 - r, BX0 + BW + 30 + r, 980 + r), outline=(255, 214, 10, int(255 * (1 - q))), width=8)
    c.alpha_composite(ly)
    telop(c, t, at, [("トン！", YEL)], y0=900, size=90)

def draw_body(c, t, T):
    k = times(T)
    tilt = 0.0
    for at in (k["tap1"], k["tap2"]):
        if at <= t < at + 0.15: tilt = 3 * math.sin((t - at) / 0.15 * math.pi)
    big_phone(c, phone_screen(t, k), tilt)
    for at in (k["tap1"], k["tap2"]):
        tap_fx(c, t, at)
    if t < T.at["b2"]:
        telop(c, t, T.body, [("背中を2回トントン", WHITE)], y0=400, size=96)
    elif t < T.at["b3"]:
        telop(c, t, T.at["b2"], [("スクショが撮れた！", YEL)], y0=400, size=110)
    elif t < T.at["b4"]:
        telop(c, t, T.at["b3"], [("設定 → 背面タップ", YEL)], y0=400, size=100)
    else:
        telop(c, t, T.at["b4"], [("3回タップにも割り当てOK", YEL)], y0=400, size=86)
    if t < T.at["b4"]:
        badge(c, t, k["done"], "ボタン同時押しいらず", 1505, GREEN, size=44)
    else:
        badge(c, t, k["extra"], "片手でサッと使える", 1505, PURPLE, size=44)

def draw_hook_art(ly, t):
    x0, y0 = 450, 1150
    rr(ly, (x0, y0, x0 + 180, y0 + 360), 30, (36, 36, 40), outline=(120, 120, 130), width=4)
    ly.alpha_composite(grad(164, 344, (255, 140, 90), (120, 60, 200)), (x0 + 8, y0 + 8))
    d = ImageDraw.Draw(ly)
    for k in range(3):
        q = (t * 1.2 + k / 3) % 1; r = 30 + q * 110
        d.ellipse((x0 + 210 - r, y0 + 180 - r, x0 + 210 + r, y0 + 180 + r), outline=(255, 214, 10, int(255 * (1 - q))), width=6)

def sfx(T):
    k = times(T)
    return [("click", k["tap1"]), ("click", k["tap2"]), ("whoosh", k["shot"]), ("ding", k["shot"] + 0.2),
            ("pop", k["s_acc"]), ("pop", k["s_touch"]), ("pop", k["s_back"]), ("pop", k["triple"]), ("pop", k["extra"])]

def stills(T):
    k = times(T)
    return [k["tap1"] + 0.2, k["shot"] + 0.5, k["s_touch"] + 0.5, k["s_back"] + 0.8, k["pick"] + 0.5]
