# iPhone爆速神操作① 計算機で打ち間違えた数字を、表示部分のスワイプで1桁だけ消す（v2：ショート＋60秒パート）
import math
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="w20261102_first", title="iPhone爆速神操作", spoken="iPhone爆速、かみ操作",
              hook_split=("iPhone", "爆速神操作"), total=5)
NUM, SLUG = 1, "calc_delete"
NEXT = "片手キーボード"
SCREEN_CROP = (0, 190, 400, 860)          # display + keypad (skip the empty top)
HOOK = "計算機で全部消す人\n[全員損]してます"
HOOK_SPOKEN = "計算機で全部消してる人、全員損してます！"
TELOPS = [("b1", "数字を\n{打ち間違えた}…"), ("b2", "数字の部分を\n[横にスワイプ]"),
          ("b3", "[最後の1桁]だけ\n消えた！"), ("b4", "そのまま\n[続きを打てる]")]
ACTIONS = [("b1", "b2", "数字を入力"), ("b2", "b3", "数字部分を横スワイプ"),
           ("b3", "b4", "1回で1桁消える"), ("b4", "cta", "続きを入力")]
BODY = [
    ("b1", "計算機で、数字を打ち間違えたとき、", 0.3),
    ("b2", "上の数字の部分を、横にスワイプしてみてください。", 0.3),
    ("b3", "最後の1桁だけが、消えます！", 0.3),
    ("b4", "全部消さずに、そのまま続きを打てます。", 0.0),
]
BODY_HOLD = 0.9
CTA = dict(lines=[("数字の部分を", WHITE, 96), ("横にスワイプ！", YEL, 120)], spoken="保存して試してね！",
           chip="1回のスワイプで1桁消える")

PART = dict(
    title="計算機で1桁だけ消す",
    intro="計算機で打ち間違えたとき、全部消して、最初から打ち直していませんか？",
    steps=[
        ("計算機で数字を入力", "まず、計算機アプリを開いて、いつも通り数字を入力します。", ("body", "b1+1.4")),
        ("打ち間違えに気づく", "ここで、最後の数字を打ち間違えてしまいました。普通は、全部消すボタンを押して、最初からやり直しがちですよね。", ("b1+1.2", "b2")),
        ("数字の部分を横にスワイプ", "そんな時は、上の、数字が表示されている部分を、指で左か右にスワイプします。", ("b2", "b2+1.6")),
        ("最後の1桁だけ消える", "すると、最後の1桁だけが消えます。2回スワイプすれば、2桁消せます。", ("b2+1.4", "b4")),
        ("続きを入力", "あとは、正しい数字を打ち直すだけ。最初から打ち直す必要はありません。", ("b4", "b4+1.2")),
        ("計算の途中でもOK", "ちなみに、足し算や掛け算の途中で入力している数字でも、同じように1桁ずつ消せます。", ("b4+1.0", "cta")),
    ],
    outro="打ち間違えたら、数字の部分を横にスワイプ。ぜひ試してみてください。",
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

KEYS = [["AC", "±", "%", "÷"], ["7", "8", "9", "×"], ["4", "5", "6", "−"], ["1", "2", "3", "+"], ["0", "", ".", "="]]
KD, KG, KX0, KY0 = 80, 14, 19, 372
TYPED = "12348"                       # the last "8" is the mistake

def key_xy(ch):
    for r, row in enumerate(KEYS):
        if ch in row:
            q = row.index(ch); return KX0 + q * (KD + KG) + KD / 2, KY0 + r * (KD + KG) + KD / 2
    return None

def times(T):
    k = dict(swipe=T.at["b2"] + 0.9, swiped=T.at["b2"] + 1.5, fix=T.at["b4"] + 0.5,
             done=T.at["b3"] + 0.3, extra=T.at["b4"] + 0.9)
    k["types"] = [T.at["b1"] + 0.1 + i * 0.28 for i in range(len(TYPED))]
    return k

def fmt(s): return f"{int(s):,}" if s else "0"

def screen(t, k):
    ps = Image.new("RGBA", (BW, BH), (0, 0, 0, 255))
    txt(ps, (56, 36), "9:41", 22, WHITE, anchor="lm")
    n = sum(1 for a in k["types"] if t >= a)
    s = TYPED[:n]
    if t >= k["swiped"]: s = TYPED[:4]
    if t >= k["fix"]: s = "12345"
    disp = fmt(s)
    col = (255, 214, 10) if (s == TYPED and k["types"][-1] + 0.1 <= t < k["swiped"]) else WHITE
    if s == TYPED and k["types"][-1] <= t:
        f = font(84, False)
        txt(ps, (BW - 28 - f.getlength(disp[-1]), 300), disp[:-1], 84, WHITE, bold=False, anchor="rs")
        txt(ps, (BW - 28, 300), disp[-1], 84, (255, 120, 110), bold=False, anchor="rs")
    else:
        txt(ps, (BW - 28, 300), disp, 84, (120, 255, 150) if t >= k["fix"] else col, bold=False, anchor="rs")
    # the deleted "8" flies off to the right
    if k["swiped"] <= t < k["swiped"] + 0.5:
        p = (t - k["swiped"]) / 0.5
        ly = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
        txt(ly, (BW - 28 + 120 * p, 300), "8", 84, (255, 120, 110, int(255 * (1 - p))), bold=False, anchor="rs")
        ps.alpha_composite(ly)
    pressed = None
    for i, a in enumerate(k["types"]):
        if a <= t < a + 0.18: pressed = TYPED[i]
    if k["fix"] <= t < k["fix"] + 0.18: pressed = "5"
    d = ImageDraw.Draw(ps)
    for r, row in enumerate(KEYS):
        for q, ch in enumerate(row):
            if ch == "": continue
            x = KX0 + q * (KD + KG); y = KY0 + r * (KD + KG)
            wide = ch == "0"
            box = (x, y, x + (2 * KD + KG if wide else KD), y + KD)
            col = (255, 159, 10) if q == 3 else ((165, 165, 165) if r == 0 else (51, 51, 51))
            if ch == pressed: col = tuple(min(255, v + 70) for v in col)
            d.rounded_rectangle(box, KD // 2, fill=col)
            tc = INK if r == 0 else WHITE
            if wide: txt(ps, (x + KD / 2, y + KD / 2), ch, 34, tc, bold=False, anchor="mm")
            else: txt(ps, (x + KD / 2, y + KD / 2), ch, 30 if r == 0 else 36, tc, bold=False, anchor="mm")
    # finger: taps the keys, then swipes across the display
    fp = None
    for i, a in enumerate(k["types"]):
        if a - 0.12 <= t < a + 0.16: fp = key_xy(TYPED[i])
    if k["swipe"] - 0.3 <= t < k["swiped"] + 0.2:
        q = ease_inout((t - k["swipe"]) / (k["swiped"] - k["swipe"]))
        fp = (90 + 230 * q, 318)
        if t >= k["swipe"]:
            d.line((90, 334, fp[0], 334), fill=(255, 214, 10), width=6)
            d.polygon([(fp[0] + 24, 334), (fp[0] + 6, 322), (fp[0] + 6, 346)], fill=(255, 214, 10))
    if k["fix"] - 0.12 <= t < k["fix"] + 0.2: fp = key_xy("5")
    if fp:
        fx, fy = fp
        fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((fx - 30, fy - 30, fx + 30, fy + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))
    return ps

def SCREEN(t, T): return screen(t, times(T))

def draw_body(c, t, T):
    k = times(T)
    big_phone(c, screen(t, k))
    if t < T.at["b2"]:
        telop(c, t, T.body, [("数字を打ち間違えた…", WHITE)], y0=400, size=96)
    elif t < T.at["b3"]:
        telop(c, t, T.at["b2"], [("数字の部分を横にスワイプ", YEL)], y0=400, size=88)
    elif t < T.at["b4"]:
        telop(c, t, T.at["b3"], [("最後の1桁だけ消えた！", YEL)], y0=400, size=96)
    else:
        telop(c, t, T.at["b4"], [("そのまま続きを打てる", YEL)], y0=400, size=96)
    if t < T.at["b4"]:
        badge(c, t, k["done"], "ACで全部消さなくてOK", 1505, GREEN, size=44)
    else:
        badge(c, t, k["extra"], "2回スワイプで2桁消える", 1505, PURPLE, size=44)

def draw_hook_art(ly, t):
    x0, y0 = 360, 1170
    rr(ly, (x0, y0, x0 + 360, y0 + 230), 30, (0, 0, 0), outline=(90, 90, 100), width=3)
    q = (t * 0.8) % 1
    txt(ly, (x0 + 330, y0 + 110), ("12,348" if q < 0.55 else "1,234"), 70, WHITE, bold=False, anchor="rs")
    d = ImageDraw.Draw(ly)
    p = ease_inout(clamp((q - 0.1) / 0.45))
    d.line((x0 + 60, y0 + 170, x0 + 60 + 220 * p, y0 + 170), fill=(255, 214, 10), width=8)
    d.ellipse((x0 + 30 + 220 * p, y0 + 140, x0 + 90 + 220 * p, y0 + 200), fill=(255, 255, 255, 170), outline=(80, 80, 90), width=3)

def sfx(T):
    k = times(T)
    return [("click", a) for a in k["types"]] + [("whoosh", k["swipe"] + 0.3), ("pop", k["swiped"]), ("ding", k["done"]),
                                                  ("click", k["fix"]), ("pop", k["extra"])]

def stills(T):
    k = times(T)
    return [k["types"][-1] + 0.3, (k["swipe"] + k["swiped"]) / 2, k["swiped"] + 0.6, k["fix"] + 0.4, k["extra"] + 0.5]
