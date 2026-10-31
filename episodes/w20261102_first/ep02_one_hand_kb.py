# iPhone爆速神操作② 地球儀（絵文字）キー長押し→片手用キーボードで左右に寄せる（v3：ショート＋60秒パート）
import math
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="w20261102_first", title="iPhone爆速神操作", spoken="iPhone爆速、かみ操作",
              hook_split=("iPhone", "爆速神操作"), total=5)
NUM, SLUG = 2, "one_hand_kb"
NEXT = "画面上タップで一番上へ"
SCREEN_CROP = (0, 420, 400, 860)          # input field + keyboard
HOOK = "9割が知らない\n[片手キーボード]"
HOOK_SPOKEN = "9割が知らない、片手キーボード！"
TELOPS = [("b1", "片手だと\n{指が届かない}…"), ("b2", "[地球儀キー]を\n長押し"),
          ("b3", "片手用の\n[アイコン]をタップ"), ("b4", "キーボードが\n[片側に寄る！]"),
          ("b5", "戻すときは\n[反対側の矢印]")]
ACTIONS = [("b1", "b2", "片手で文字入力"), ("b2", "b3", "地球儀キー長押し"), ("b3", "b4", "片手用アイコンをタップ"),
           ("b4", "b5", "親指だけで楽々入力"), ("b5", "cta", "空いた側の矢印をタップ")]
BODY = [
    ("b1", "片手で打つと、端のキーに指が届かない…", 0.2),
    ("b2", "地球儀のキーを、長押しして、", 0.2),
    ("b3", "片手用のアイコンをタップ。", 0.3),
    ("b4", "キーボードが寄って、親指で楽に打てます！", 0.2),
    ("b5", "戻すときは、反対側の矢印をタップ。", 0.0),
]
BODY_HOLD = 0.6
CTA = dict(lines=[("地球儀キー長押しで", WHITE, 92), ("片手キーボード！", YEL, 120)], spoken="保存して試してね！",
           chip="左にも右にも寄せられる")

PART = dict(
    title="片手キーボード",
    intro="大きいiPhoneを片手で持って文字を打つとき、反対側のキーに指が届かなくて困っていませんか？",
    steps=[
        ("キーボードを出す", "まず、メッセージやメモなど、文字を入力する画面でキーボードを出します。", ("body", "b2")),
        ("地球儀キーを長押し", "キーボードの左下にある、地球儀のキーを長押しします。地球儀がない場合は、絵文字のキーを長押ししてください。", ("b2", "b3")),
        ("片手用アイコンを選ぶ", "メニューの下に、キーボードの形のアイコンが3つ出ます。右手で打つなら右寄せ、左手なら左寄せのアイコンを選びます。", ("b3", "b3+1.3")),
        ("キーボードが片側に寄る", "するとキーボードが片側に寄って小さくなり、親指だけで端のキーまで楽に届きます。", ("b3+1.0", "b5")),
        ("矢印で元に戻す", "元に戻すときは、キーボードの空いた側に出ている矢印をタップするだけです。", ("b5", "cta")),
        ("設定からも選べる", "ちなみに、設定アプリの、一般、キーボードにある、片手用キーボードからも切り替えられます。", ("b4", "b4+1.5")),
    ],
    outro="地球儀キーを長押しして、片手用キーボード。ぜひ試してみてください。",
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

KB_BG, KEY, KEY2 = (208, 211, 218), (255, 255, 255), (172, 177, 187)
KB_Y0, ROW_Y0, ROW_H, ROW_G = 560, 600, 50, 6
SHIFT_W = 70                                    # empty strip width when the keyboard is shifted
MID = [["あ", "か", "さ"], ["た", "な", "は"], ["ま", "や", "ら"], ["小゛゜", "わ", "、。?!"]]
LEFT = ["→", "^_^", "ABC", "EMOJI"]
RIGHT = ["DEL", "空白", "改行", None]
TYPED = "了解、今行くね"

def times(T):
    k = dict(press=T.at["b2"] + 0.3, menu=T.at["b2"] + 0.9, pick=T.at["b3"] + 0.6, shift=T.at["b3"] + 0.75,
             back=T.at["b5"] + 1.2)
    k["types"] = [T.at["b4"] + 0.2 + i * 0.32 for i in range(len(TYPED))]
    return k

def kb_x(t, k):
    """left edge of the keys (0 = full width, SHIFT_W = shifted right)"""
    if t < k["shift"]: return 0.0
    if t < k["back"]: return SHIFT_W * ease_out((t - k["shift"]) / 0.3)
    return SHIFT_W * (1 - ease_out((t - k["back"]) / 0.3))

def key_boxes(x0, x1):
    g = 6; side = (x1 - x0) * 0.17; mid = (x1 - x0 - 2 * side - 6 * g) / 3
    cols = [x0 + g, x0 + g + side + g]
    cols += [cols[1] + mid + g, cols[1] + 2 * (mid + g), cols[1] + 3 * (mid + g)]
    widths = [side, mid, mid, mid, side]
    out = {}
    for r in range(4):
        y = ROW_Y0 + r * (ROW_H + ROW_G)
        for q in range(5):
            if q == 0: lab = LEFT[r]
            elif q == 4: lab = RIGHT[r]
            else: lab = MID[r][q - 1]
            if lab is None: continue
            h = 2 * ROW_H + ROW_G if lab == "改行" else ROW_H
            out[(r, q)] = (lab, (cols[q], y, cols[q] + widths[q], y + h))
    return out

def globe(d, cx, cy, r, col):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col, width=3)
    d.ellipse((cx - r * 0.45, cy - r, cx + r * 0.45, cy + r), outline=col, width=2)
    d.line((cx - r, cy, cx + r, cy), fill=col, width=2)
    d.line((cx, cy - r, cx, cy + r), fill=col, width=2)

def del_icon(d, cx, cy, col):
    d.polygon([(cx - 16, cy), (cx - 7, cy - 10), (cx + 14, cy - 10), (cx + 14, cy + 10), (cx - 7, cy + 10)], outline=col, width=2)
    d.line((cx - 2, cy - 5, cx + 8, cy + 5), fill=col, width=2); d.line((cx - 2, cy + 5, cx + 8, cy - 5), fill=col, width=2)

def smile(d, cx, cy, r, col):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col, width=2)
    d.ellipse((cx - 6, cy - 5, cx - 2, cy - 1), fill=col); d.ellipse((cx + 2, cy - 5, cx + 6, cy - 1), fill=col)
    d.arc((cx - 7, cy - 4, cx + 7, cy + 8), 20, 160, fill=col, width=2)

def kb_icon(d, cx, cy, mode, col):
    """the 3 one-handed keyboard icons: mode -1 left, 0 full, 1 right"""
    w, h = 44, 30
    if mode == 0: x0, x1 = cx - w / 2, cx + w / 2
    elif mode < 0: x0, x1 = cx - w / 2, cx + w / 2 - 12
    else: x0, x1 = cx - w / 2 + 12, cx + w / 2
    d.rounded_rectangle((x0, cy - h / 2, x1, cy + h / 2), 5, outline=col, width=3)
    for i in range(3):
        for j in range(2):
            px = x0 + 7 + i * (x1 - x0 - 14) / 2; py = cy - 6 + j * 10
            d.rectangle((px - 2, py - 2, px + 2, py + 2), fill=col)
    if mode != 0:
        ax = cx - w / 2 + 3 if mode > 0 else cx + w / 2 - 3
        d.line((ax, cy - 6, ax, cy + 6), fill=col, width=2)

def finger(ps, x, y):
    fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((x - 30, y - 30, x + 30, y + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))

def screen(t, k):
    ps = Image.new("RGBA", (BW, BH), (255, 255, 255, 255))
    d = ImageDraw.Draw(ps)
    txt(ps, (56, 36), "9:41", 22, INK, anchor="lm")
    # Messages header
    d.ellipse((BW / 2 - 30, 70, BW / 2 + 30, 130), fill=(160, 166, 180))
    txt(ps, (BW / 2, 100), "ゆ", 30, WHITE, anchor="mm")
    txt(ps, (BW / 2, 150), "ゆうき", 18, INK, bold=False, anchor="mm")
    txt(ps, (24, 100), "‹", 50, BLUE, bold=False, anchor="lm")
    d.line((0, 176, BW, 176), fill=(225, 225, 230), width=1)
    # bubbles
    def bub(s, right, y):
        f = font(22, False); w = f.getlength(s) + 36
        x0 = BW - 16 - w if right else 16
        rr(ps, (x0, y, x0 + w, y + 50), 25, BLUE if right else (233, 233, 235))
        txt(ps, (x0 + w / 2, y + 25), s, 22, WHITE if right else INK, bold=False, anchor="mm")
    bub("いまどこ？", False, 220)
    bub("駅についたよ！", False, 284)
    bub("迎えに行こうか？", False, 348)
    # input field
    n = sum(1 for a in k["types"] if t >= a)
    s = TYPED[:n]
    rr(ps, (14, 500, 54, 540), 20, (233, 233, 235)); txt(ps, (34, 519), "+", 30, (120, 120, 128), bold=False, anchor="mm")
    rr(ps, (64, 496, BW - 14, 544), 24, WHITE, outline=(205, 205, 210), width=2)
    if s: txt(ps, (84, 520), s, 22, INK, bold=False, anchor="lm")
    else: txt(ps, (84, 520), "iMessage", 22, (170, 170, 176), bold=False, anchor="lm")
    if s and int(t * 2) % 2 == 0:
        cx = 84 + font(22, False).getlength(s) + 2; d.line((cx, 506, cx, 534), fill=BLUE, width=3)
    # keyboard
    d.rectangle((0, KB_Y0, BW, BH), fill=KB_BG)
    xs = kb_x(t, k)
    boxes = key_boxes(xs, BW - 0)
    pressed = None
    for i, a in enumerate(k["types"]):
        if a <= t < a + 0.16: pressed = [(0, 1), (1, 2), (2, 2), (0, 2), (1, 1), (2, 3), (3, 2)][i % 7]
    for (r, q), (lab, b) in boxes.items():
        col = KEY if 1 <= q <= 3 else KEY2
        if (r, q) == pressed: col = (190, 196, 206)
        if lab == "改行": col = KEY2
        rr(ps, (b[0], b[1] + 2, b[2], b[3] + 2), 7, (140, 144, 152))
        rr(ps, b, 7, col)
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        if lab == "DEL": del_icon(d, cx, cy, INK)
        elif lab == "EMOJI": smile(d, cx, cy, 13, INK)
        else:
            sz = 26 if len(lab) == 1 else (20 if len(lab) <= 3 else 16)
            txt(ps, (cx, cy), lab, sz, INK, bold=False, anchor="mm")
    # empty side + arrow (one-handed mode)
    if xs > 8:
        a = clamp(xs / SHIFT_W)
        ax, ay = xs / 2, ROW_Y0 + 2 * (ROW_H + ROW_G) - 3
        hl = k["back"] - 0.15 <= t < k["back"] + 0.1
        d.line([(ax + 7, ay - 16), (ax - 7, ay), (ax + 7, ay + 16)], fill=(BLUE if hl else (90, 90, 100)) if a > 0.5 else KB_BG, width=5, joint="curve")
    # bottom strip: globe + mic
    globe(d, 40, 832, 15, (70, 70, 80))
    d.rounded_rectangle((BW - 46, 818, BW - 34, 838), 6, outline=(70, 70, 80), width=3)
    d.arc((BW - 52, 822, BW - 28, 846), 0, 180, fill=(70, 70, 80), width=3)
    d.line((BW - 40, 846, BW - 40, 852), fill=(70, 70, 80), width=3)
    # long-press menu
    if k["menu"] <= t < k["shift"]:
        p = ease_out((t - k["menu"]) / 0.18)
        mx0, my0, mx1, my1 = 16, 586, 276, 806
        ly = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
        shadow(ly, (mx0, my0, mx1, my1), 16, blur=10, off=4, a=90)
        rr(ly, (mx0, my0, mx1, my1), 16, (250, 250, 252))
        items = ["日本語 - かな", "English (Japan)", "絵文字"]
        for i, s2 in enumerate(items):
            y = my0 + 30 + i * 46
            txt(ly, (mx0 + 46, y), s2, 20, INK, bold=False, anchor="lm")
            if i == 0: check(ly, mx0 + 14, y - 8, 16, BLUE, 3)
            ImageDraw.Draw(ly).line((mx0 + 14, y + 23, mx1 - 14, y + 23), fill=(220, 220, 226), width=1)
        iy = my1 - 42
        dl = ImageDraw.Draw(ly)
        sel = 1 if t >= k["pick"] - 0.35 else 0
        for j, mode in enumerate([-1, 0, 1]):
            cx = mx0 + 50 + j * 80
            if mode == sel:
                rr(ly, (cx - 34, iy - 26, cx + 34, iy + 26), 10, (220, 225, 235))
            kb_icon(dl, cx, iy, mode, BLUE if mode == sel else (60, 60, 70))
        if p < 1: ly.putalpha(ly.getchannel("A").point(lambda v: int(v * p)))
        ps.alpha_composite(ly)
    # finger
    fp = None
    if k["press"] - 0.15 <= t < k["pick"] - 0.5: fp = (40, 832)
    elif k["pick"] - 0.5 <= t < k["pick"] + 0.15:
        q = ease_inout((t - (k["pick"] - 0.5)) / 0.4)
        fp = (40 + (226 - 40) * q, 832 + (764 - 832) * q)
    for i, a in enumerate(k["types"]):
        if a - 0.12 <= t < a + 0.16:
            r, q = [(0, 1), (1, 2), (2, 2), (0, 2), (1, 1), (2, 3), (3, 2)][i % 7]
            b = boxes[(r, q)][1]; fp = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
    if k["back"] - 0.4 <= t < k["back"] + 0.2: fp = (SHIFT_W / 2, ROW_Y0 + 2 * (ROW_H + ROW_G) - 3)
    if fp:
        # long-press ring on the globe
        if k["press"] <= t < k["menu"]:
            pr = (t - k["press"]) / (k["menu"] - k["press"])
            d2 = ImageDraw.Draw(ps); d2.arc((fp[0] - 40, fp[1] - 40, fp[0] + 40, fp[1] + 40), -90, -90 + 360 * pr, fill=(255, 159, 10), width=6)
        finger(ps, *fp)
    return ps

def SCREEN(t, T): return screen(t, times(T))

def draw_body(c, t, T):
    k = times(T)
    big_phone(c, screen(t, k))
    if t < T.at["b2"]:
        telop(c, t, T.body, [("指が届かない…", WHITE)], y0=400, size=96)
    elif t < T.at["b3"]:
        telop(c, t, T.at["b2"], [("地球儀キーを長押し", YEL)], y0=400, size=90)
    elif t < T.at["b5"]:
        telop(c, t, T.at["b3"], [("片手用キーボード！", YEL)], y0=400, size=96)
    else:
        telop(c, t, T.at["b5"], [("戻すのは反対側の矢印", YEL)], y0=400, size=84)

def draw_hook_art(ly, t):
    x0, y0 = 340, 1170
    rr(ly, (x0, y0, x0 + 400, y0 + 220), 24, KB_BG)
    q = (t * 0.7) % 1
    sh = 70 * ease_inout(clamp((q - 0.3) / 0.3))
    for r in range(3):
        for j in range(4):
            bx = x0 + 10 + sh + j * (380 - sh) / 4
            rr(ly, (bx + 4, y0 + 14 + r * 68, bx + (380 - sh) / 4 - 4, y0 + 70 + r * 68), 8, WHITE)

def sfx(T):
    k = times(T)
    return [("click", k["press"]), ("pop", k["menu"]), ("click", k["pick"]), ("whoosh", k["shift"])] + \
           [("click", a) for a in k["types"]] + [("click", k["back"]), ("whoosh", k["back"] + 0.05)]

def stills(T):
    k = times(T)
    return [k["press"] + 0.3, k["menu"] + 0.4, k["shift"] + 0.6, k["types"][-1] + 0.2, k["back"] + 0.5]
