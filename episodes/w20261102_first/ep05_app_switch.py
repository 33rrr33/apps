# iPhone爆速神操作⑤ 画面下のホームバーを左右にスワイプして、直前のアプリと一瞬で行き来する（Face ID機種）（v3：ショート＋60秒パート）
import math
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="w20261102_first", title="iPhone爆速神操作", spoken="iPhone爆速、かみ操作",
              hook_split=("iPhone", "爆速神操作"), total=5)
NUM, SLUG = 5, "app_switch"
NEXT = "まとめは土曜の朝6時"
SCREEN_CROP = (0, 200, 400, 860)          # lower part of the screen, with the home bar
HOOK = "知らないと損\n[アプリ爆速切替]"
HOOK_SPOKEN = "知らないと損、アプリの爆速切り替え！"
TELOPS = [("b1", "毎回ホームに\n{戻ってない？}"), ("b2", "下のバーを\n[右にスワイプ]"), ("b3", "[直前のアプリ]に\n一瞬で切替！"),
          ("b4", "左にスワイプで\n[元のアプリへ]")]
ACTIONS = [("b1", "b2", "ホームに戻って探す…"), ("b2", "b3", "ホームバーを右へスワイプ"), ("b3", "b4", "直前のアプリに切替"),
           ("b4", "cta", "ホームバーを左へスワイプ")]
BODY = [
    ("b1", "アプリを切り替えるとき、毎回ホームに戻っていませんか？", 0.3),
    ("b2", "画面の一番下のバーを、右にスワイプすると、", 0.2),
    ("b3", "直前のアプリに、一瞬で切り替わります！", 0.3),
    ("b4", "左にスワイプすれば、元のアプリに戻ります。", 0.0),
]
BODY_HOLD = 0.7
CTA = dict(lines=[("下のバーを", WHITE, 100), ("横にスワイプ！", YEL, 124)], spoken="保存して試してね！",
           chip="Face IDのiPhoneで使える")

PART = dict(
    title="アプリを一瞬で切り替え",
    intro="別のアプリに切り替えるとき、毎回ホーム画面に戻って、アイコンを探していませんか？",
    steps=[
        ("いつもの切り替え方", "ふつうは、ホーム画面に戻ってから、使いたいアプリのアイコンを探してタップしますよね。", ("body", "b2")),
        ("画面下のバーに指を置く", "そこで、画面の一番下にある、横長のバーに指を置きます。これはホームボタンのない、Face IDのiPhoneにある部分です。", ("b2", "b2+0.9")),
        ("右にスワイプ", "そのまま、バーに沿って、指を右にスワイプします。", ("b2+0.6", "b3")),
        ("直前のアプリに切り替わる", "すると、さっきまで使っていたアプリに、一瞬で切り替わります。", ("b3", "b4")),
        ("左にスワイプで戻る", "元のアプリに戻りたいときは、続けてバーを左にスワイプします。", ("b4", "b4+1.6")),
        ("何度でも行き来できる", "地図とメッセージを見比べるときなど、2つのアプリを何度も行き来するときにとても便利です。", ("b2+0.6", "b4+1.6")),
    ],
    outro="アプリの切り替えは、画面下のバーを横にスワイプ。ぜひ試してみてください。",
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

BAR_Y = 846
_cache = {}

def app_maps():
    if "maps" in _cache: return _cache["maps"]
    ps = Image.new("RGBA", (BW, BH), (242, 239, 230, 255))
    d = ImageDraw.Draw(ps)
    d.polygon([(0, 300), (140, 260), (210, 330), (120, 420), (0, 400)], fill=(196, 226, 176))
    d.polygon([(260, 520), (400, 470), (400, 640), (300, 650)], fill=(196, 226, 176))
    d.line([(0, 560), (120, 520), (230, 560), (400, 420)], fill=(160, 205, 245), width=28)
    for x in (70, 190, 320): d.line((x, 0, x - 30, BH), fill=WHITE, width=12)
    for y in (180, 380, 600): d.line((0, y, BW, y + 40), fill=WHITE, width=12)
    d.line((0, 470, BW, 300), fill=(255, 220, 120), width=16)
    # pin
    d.ellipse((182, 300, 222, 340), fill=RED); d.polygon([(188, 330), (216, 330), (202, 356)], fill=RED)
    d.ellipse((194, 312, 210, 328), fill=WHITE)
    rr(ps, (150, 364, 254, 392), 10, WHITE); txt(ps, (202, 378), "駅前カフェ", 16, INK, anchor="mm")
    # bottom sheet with search
    rr(ps, (0, 690, BW, BH + 30), 26, (250, 250, 252))
    rr(ps, (BW / 2 - 24, 700, BW / 2 + 24, 706), 3, (200, 200, 206))
    rr(ps, (18, 722, BW - 18, 770), 12, (232, 232, 236))
    d.ellipse((34, 736, 50, 752), outline=(142, 142, 147), width=2); d.line((48, 750, 54, 756), fill=(142, 142, 147), width=2)
    txt(ps, (64, 746), "マップで検索", 20, (142, 142, 147), bold=False, anchor="lm")
    txt(ps, (56, 36), "9:41", 22, INK, anchor="lm")
    _cache["maps"] = ps
    return ps

def app_messages():
    if "msg" in _cache: return _cache["msg"]
    ps = Image.new("RGBA", (BW, BH), (255, 255, 255, 255))
    d = ImageDraw.Draw(ps)
    txt(ps, (56, 36), "9:41", 22, INK, anchor="lm")
    d.ellipse((BW / 2 - 30, 70, BW / 2 + 30, 130), fill=(160, 166, 180))
    txt(ps, (BW / 2, 100), "ゆ", 30, WHITE, anchor="mm")
    txt(ps, (BW / 2, 150), "ゆうき", 18, INK, bold=False, anchor="mm")
    txt(ps, (24, 100), "‹", 50, BLUE, bold=False, anchor="lm")
    d.line((0, 176, BW, 176), fill=(225, 225, 230), width=1)
    def bub(s, right, y):
        f = font(22, False); w = f.getlength(s) + 36
        x0 = BW - 16 - w if right else 16
        rr(ps, (x0, y, x0 + w, y + 50), 25, BLUE if right else (233, 233, 235))
        txt(ps, (x0 + w / 2, y + 25), s, 22, WHITE if right else INK, bold=False, anchor="mm")
    bub("駅前のカフェにいるよ", False, 300)
    bub("場所わかる？", False, 364)
    bub("地図で見てみる！", True, 440)
    bub("北口から3分くらい", False, 516)
    bub("了解、すぐ行くね", True, 592)
    rr(ps, (14, 742, 54, 782), 20, (233, 233, 235)); txt(ps, (34, 761), "+", 30, (120, 120, 128), bold=False, anchor="mm")
    rr(ps, (64, 738, BW - 14, 786), 24, WHITE, outline=(205, 205, 210), width=2)
    txt(ps, (84, 762), "iMessage", 22, (170, 170, 176), bold=False, anchor="lm")
    _cache["msg"] = ps
    return ps

ICONS = [("メッセージ", GREEN), ("マップ", (90, 180, 120)), ("写真", (250, 190, 60)), ("カメラ", (120, 120, 130)),
         ("カレンダー", (240, 90, 80)), ("時計", (40, 40, 44)), ("Safari", BLUE), ("設定", (142, 142, 147)),
         ("メモ", (250, 200, 50)), ("天気", (80, 150, 230)), ("ミュージック", (250, 60, 90)), ("ファイル", (60, 130, 240))]

def home():
    if "home" in _cache: return _cache["home"]
    ps = grad(BW, BH, (60, 90, 190), (170, 80, 160))
    for i, (name, col) in enumerate(ICONS):
        x = 26 + (i % 4) * 92; y = 250 + (i // 4) * 116
        rr(ps, (x, y, x + 70, y + 70), 17, col)
        if name == "マップ":
            d = ImageDraw.Draw(ps); d.line((x + 10, y + 50, x + 60, y + 20), fill=WHITE, width=6)
            d.ellipse((x + 26, y + 18, x + 44, y + 36), fill=RED)
        if name == "メッセージ":
            ImageDraw.Draw(ps).ellipse((x + 14, y + 16, x + 56, y + 50), fill=WHITE)
        txt(ps, (x + 35, y + 86), name, 14, WHITE, bold=False, anchor="mm")
    rra(ps, (14, 700, BW - 14, 812), 34, (255, 255, 255, 70))
    for i, col in enumerate([GREEN, BLUE, (250, 190, 60), (250, 60, 90)]):
        x = 34 + i * 88; rr(ps, (x, 720, x + 70, 790), 17, col)
    txt(ps, (56, 36), "9:41", 22, WHITE, anchor="lm")
    _cache["home"] = ps
    return ps

def times(T):
    return dict(up=T.at["b1"] + 1.0, open=T.at["b1"] + 2.4, sw1=T.at["b2"] + 1.0, sw2=T.at["b4"] + 1.0)

def card(img, s):
    """the app as a rounded card scaled by s (during transitions)"""
    w, h = int(BW * s), int(BH * s)
    im = img.resize((w, h), Image.LANCZOS)
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), 40, fill=255)
    im.putalpha(m)
    return im

def slide(ps, cur, prev, p, direction):
    """cur slides out to the right (direction=1) and prev comes in from the left; direction=-1 the other way."""
    ps.paste((20, 20, 24, 255), (0, 0, BW, BH))
    e = ease_inout(p); s = 1 - 0.08 * math.sin(math.pi * p)
    a, b = card(cur, s), card(prev, s)
    gap = 24
    yo = int((BH - a.height) / 2)
    xo = int((BW - a.width) / 2)
    ps.alpha_composite(a, (int(xo + direction * (BW + gap) * e), yo))
    ps.alpha_composite(b, (int(xo - direction * (BW + gap) * (1 - e)), yo))

def screen(t, k):
    ps = Image.new("RGBA", (BW, BH), (0, 0, 0, 255))
    maps, msg = app_maps(), app_messages()
    if t < k["up"]:
        ps.alpha_composite(maps)
    elif t < k["up"] + 0.4:                                   # swipe up to home (the slow way)
        p = ease_out((t - k["up"]) / 0.4)
        ps.alpha_composite(home())
        cimg = card(maps, 1 - 0.75 * p)
        ps.alpha_composite(cimg, (int((BW - cimg.width) / 2), int((BH - cimg.height) / 2 - 200 * p)))
    elif t < k["open"]:
        ps.alpha_composite(home())
    elif t < k["open"] + 0.35:                                # open Maps from its icon
        p = ease_out((t - k["open"]) / 0.35)
        ps.alpha_composite(home())
        cimg = card(maps, 0.18 + 0.82 * p)
        cx, cy = 26 + 92 + 35, 250 + 35
        ps.alpha_composite(cimg, (int(cx + (BW / 2 - cx) * p - cimg.width / 2), int(cy + (BH / 2 - cy) * p - cimg.height / 2)))
    elif t < k["sw1"]:
        ps.alpha_composite(maps)
    elif t < k["sw1"] + 0.45:
        slide(ps, maps, msg, (t - k["sw1"]) / 0.45, 1)
    elif t < k["sw2"]:
        ps.alpha_composite(msg)
    elif t < k["sw2"] + 0.45:
        slide(ps, msg, maps, (t - k["sw2"]) / 0.45, -1)
    else:
        ps.alpha_composite(maps)
    # home bar (highlighted while it is swiped)
    d = ImageDraw.Draw(ps)
    hl = any(s - 0.5 <= t < s + 0.5 for s in (k["sw1"], k["sw2"], k["up"]))
    if hl:
        fade(ps, 1.0, lambda l: rr(l, (BW / 2 - 90, BAR_Y - 12, BW / 2 + 90, BAR_Y + 12), 12, (255, 214, 10, 150)))
    rr(ps, (BW / 2 - 70, BAR_Y - 3, BW / 2 + 70, BAR_Y + 3), 3, INK)
    # finger
    fp = None
    if k["up"] - 0.4 <= t < k["up"] + 0.35:
        q = ease_inout((t - (k["up"] - 0.4)) / 0.7); fp = (BW / 2, BAR_Y - 6 - 300 * clamp((q - 0.4) / 0.6))
    if k["open"] - 0.35 <= t < k["open"] + 0.1: fp = (26 + 92 + 35, 250 + 35)
    for s, dirn in ((k["sw1"], 1), (k["sw2"], -1)):
        if s - 0.4 <= t < s + 0.5:
            q = ease_inout((t - (s - 0.25)) / 0.6)
            x0 = 110 if dirn > 0 else 290
            fp = (x0 + dirn * 180 * q, BAR_Y - 8 - 20 * math.sin(math.pi * q))
            if t >= s - 0.25:
                d = ImageDraw.Draw(ps)
                d.line((x0, BAR_Y - 30, fp[0], BAR_Y - 30), fill=(255, 214, 10), width=6)
                tip = fp[0] + dirn * 18
                d.polygon([(tip, BAR_Y - 30), (fp[0], BAR_Y - 42), (fp[0], BAR_Y - 18)], fill=(255, 214, 10))
    if fp:
        fx, fy = fp
        fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((fx - 30, fy - 30, fx + 30, fy + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))
    return ps

def SCREEN(t, T): return screen(t, times(T))

def draw_body(c, t, T):
    k = times(T)
    big_phone(c, screen(t, k))
    if t < T.at["b2"]:
        telop(c, t, T.body, [("毎回ホームに戻ってない？", WHITE)], y0=400, size=84)
    elif t < T.at["b4"]:
        telop(c, t, T.at["b2"], [("下のバーを右にスワイプ", YEL)], y0=400, size=88)
    else:
        telop(c, t, T.at["b4"], [("左にスワイプで元に戻る", YEL)], y0=400, size=86)

def draw_hook_art(ly, t):
    x0, y0 = 300, 1180
    q = (t * 0.7) % 1
    e = ease_inout(clamp((q - 0.3) / 0.4))
    for i, col in enumerate([(90, 180, 120), (10, 132, 255)]):
        x = x0 + (i - 1 + e) * 260 + 140
        if -10 < x < 1090: rr(ly, (x - 110, y0, x + 110, y0 + 260), 28, col)
    rr(ly, (440, y0 + 290, 640, y0 + 302), 6, WHITE)

def sfx(T):
    k = times(T)
    return [("whoosh", k["up"]), ("click", k["open"]), ("whoosh", k["sw1"]), ("pop", k["sw1"] + 0.45),
            ("whoosh", k["sw2"]), ("pop", k["sw2"] + 0.45)]

def stills(T):
    k = times(T)
    return [k["open"] - 0.3, k["sw1"] + 0.2, k["sw1"] + 1.0, k["sw2"] + 0.2, k["sw2"] + 1.0]
