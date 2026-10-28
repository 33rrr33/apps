# iPhoneの隠し神機能② スペースキー長押しでカーソル移動
import math
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="s03_iphone_hidden", title="iPhoneの隠し神機能", spoken="iPhoneの、隠し、かみ機能",
              hook_split=("iPhoneの", "隠し神機能"), total=3)
NUM, SLUG = 2, "space_cursor"
NEXT = "写真の被写体を長押しで切り抜き"
BODY = [
    ("b1", "文字を打っていて、カーソルを動かしたいとき、", 0.3),
    ("b2", "スペースキーを長押ししてみてください。", 0.3),
    ("b3", "キーボードがトラックパッドになって、指でスイスイ動かせます！", 0.3),
    ("b4", "細かい修正がすごくラクになります。", 0.0),
]
BODY_HOLD = 0.9
CTA = dict(lines=[("スペースキーを", WHITE, 96), ("長押しするだけ！", YEL, 120)], spoken="保存して試してね！",
           chip="設定いらず・すぐ使える")

# ---- big centered iPhone (same layout as ep01) ----
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

LINES = ["明日の待ち合わせは", "渋谷駅", "ハチ公前に10時"]
FS = 34; LX, LY, LH = 30, 150, 54
KB_Y = 520                                     # keyboard top (screen coords)

def times(T):
    return dict(press=T.at["b2"] + 0.5, track=T.at["b2"] + 1.1, move=T.at["b3"] + 0.3, arrive=T.at["b3"] + 1.8,
                insert=T.at["b4"] + 0.2, done=T.at["b3"] + 0.8, extra=T.at["b4"] + 0.5)

def caret_pos(line, chars):
    f = font(FS, False)
    return LX + f.getlength(LINES[line][:chars] if line < len(LINES) else ""), LY + line * LH

def screen(t, k):
    ps = Image.new("RGBA", (BW, BH), (255, 253, 245, 255))
    txt(ps, (56, 36), "9:41", 22, INK, anchor="lm")
    txt(ps, (24, 96), "メモ", 30, (200, 150, 0))
    inserted = t >= k["insert"]
    lines = list(LINES)
    if inserted:
        n = min(2, int((t - k["insert"]) / 0.2) + 1)
        lines[1] = "渋谷駅" + "東口"[:n]
    for i, s in enumerate(lines):
        txt(ps, (LX, LY + i * LH), s, FS, INK, bold=False)
    if inserted:
        f = font(FS, False)
        x0 = LX + f.getlength("渋谷駅")
        rra(ps, (x0 - 2, LY + LH - 4, x0 + f.getlength(lines[1][3:]) + 2, LY + LH + 44), 6, (48, 209, 88, 70))
    # caret: end of the last line → after 渋谷駅 (line 2)
    p = ease_inout((t - k["move"]) / (k["arrive"] - k["move"])) if t > k["move"] else 0
    ex, ey = caret_pos(2, len(LINES[2]))
    tx, ty = caret_pos(1, 3)
    if inserted: tx += font(FS, False).getlength(lines[1][3:])
    if p < 0.5:
        cx, cy = ex + (LX + 260 - ex) * (p * 2), ey
    else:
        q = (p - 0.5) * 2
        cx, cy = LX + 260 + (tx - LX - 260) * q, ty
    if t < k["track"] or int(t * 2.5) % 2 == 0 or (k["move"] < t < k["arrive"]):
        ImageDraw.Draw(ps).line((cx, cy + 2, cx, cy + 42), fill=BLUE, width=4)
    # keyboard
    rr(ps, (0, KB_Y, BW, BH), 0, (210, 212, 218))
    track = k["track"] <= t < k["insert"]
    rows = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
    for r, row in enumerate(rows):
        kw = (BW - 20) / 10
        x0 = 10 + (10 - len(row)) * kw / 2
        for i, ch in enumerate(row):
            x = x0 + i * kw; y = KB_Y + 20 + r * 66
            rr(ps, (x + 3, y, x + kw - 3, y + 56), 8, (232, 233, 237) if track else WHITE)
            if not track: txt(ps, (x + kw / 2, y + 28), ch, 22, INK, bold=False, anchor="mm")
    sy = KB_Y + 20 + 3 * 66
    sp = (100, sy, 300, sy + 56)
    pressed = k["press"] <= t < k["insert"]
    rr(ps, sp, 8, (255, 236, 150) if pressed and not track else ((232, 233, 237) if track else WHITE))
    if not track: txt(ps, ((sp[0] + sp[2]) / 2, sy + 28), "space", 20, INK, bold=False, anchor="mm")
    for xx, lab in ((14, "123"), (310, "改行")):
        rr(ps, (xx, sy, xx + 76, sy + 56), 8, (232, 233, 237) if track else (180, 183, 192))
        if not track: txt(ps, (xx + 38, sy + 28), lab, 18, INK, bold=False, anchor="mm")
    # finger: presses space, then slides left/up while in trackpad mode
    if k["press"] - 0.4 <= t < k["insert"]:
        fx, fy = (sp[0] + sp[2]) / 2, sy + 28
        if t > k["move"]:
            q = ease_inout((t - k["move"]) / (k["arrive"] - k["move"]))
            fx -= 120 * q; fy -= 90 * math.sin(q * math.pi / 2)
        a = clamp((t - k["press"] + 0.4) / 0.3)
        d = ImageDraw.Draw(ps)
        if k["press"] <= t < k["track"]:
            ring = clamp((t - k["press"]) / (k["track"] - k["press"]))
            d.arc((fx - 46, fy - 46, fx + 46, fy + 46), -90, -90 + 360 * ring, fill=YEL, width=7)
        fade(ps, a, lambda l: ImageDraw.Draw(l).ellipse((fx - 30, fy - 30, fx + 30, fy + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))
    return ps

def draw_body(c, t, T):
    k = times(T)
    big_phone(c, screen(t, k))
    if t < T.at["b2"]:
        telop(c, t, T.body, [("カーソルを動かしたい…", WHITE)], y0=400, size=96)
    elif t < T.at["b3"]:
        telop(c, t, T.at["b2"], [("スペースキーを長押し！", YEL)], y0=400, size=100)
    elif t < T.at["b4"]:
        telop(c, t, T.at["b3"], [("指でスイスイ動かせる", YEL)], y0=400, size=100)
    else:
        telop(c, t, T.at["b4"], [("細かい修正がラクに！", YEL)], y0=400, size=100)
    if t < T.at["b4"]:
        badge(c, t, k["done"], "キーボードがトラックパッドに", 1505, GREEN, size=42)
    else:
        badge(c, t, k["extra"], "どのアプリでも使える", 1505, PURPLE, size=44)

def draw_hook_art(ly, t):
    x0, y0 = 360, 1180
    rr(ly, (x0, y0, x0 + 360, y0 + 200), 24, (210, 212, 218))
    for i in range(10):
        rr(ly, (x0 + 10 + i * 34, y0 + 20, x0 + 38 + i * 34, y0 + 60), 6, WHITE)
    rr(ly, (x0 + 90, y0 + 120, x0 + 270, y0 + 170), 8, (255, 236, 150))
    txt(ly, (x0 + 180, y0 + 145), "space", 24, INK, bold=False, anchor="mm")
    q = (t * 0.8) % 1
    ImageDraw.Draw(ly).arc((x0 + 140, y0 + 105, x0 + 220, y0 + 185), -90, -90 + 360 * q, fill=YEL, width=7)

def sfx(T):
    k = times(T)
    return [("click", k["press"]), ("pop", k["track"]), ("whoosh", k["move"] + 0.3), ("ding", k["arrive"]),
            ("pop", k["insert"]), ("pop", k["extra"])]

def stills(T):
    k = times(T)
    return [T.at["b1"] + 0.8, k["press"] + 0.4, (k["move"] + k["arrive"]) / 2, k["insert"] + 0.6, k["extra"] + 0.6]
