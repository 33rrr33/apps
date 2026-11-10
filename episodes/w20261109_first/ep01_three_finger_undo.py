# iPhone爆速神操作①（11/9週） 3本指で左スワイプ＝取り消し、右スワイプ＝やり直し（v3：ショート＋60秒パート）
import math
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="w20261109_first", title="iPhone爆速神操作", spoken="iPhone爆速、かみ操作",
              hook_split=("iPhone", "爆速神操作"), total=5, offset=5)
NUM, SLUG = 1, "three_finger_undo"
NEXT = "2本指でまとめて選択"
SCREEN_CROP = (0, 60, 400, 560)            # banner + note text
HOOK = "消しすぎて打ち直す人\n{全員損}してます"
HOOK_SPOKEN = "消しすぎて打ち直してる人、全員損してます！"
TELOPS = [("b1", "文字を\n{消しすぎた}…"), ("b2", "[3本指]で\n左にスワイプ"),
          ("b3", "[取り消し]で\n元に戻る！"), ("b4", "右にスワイプで\n[やり直し]")]
ACTIONS = [("b1", "b2", "うっかり消しすぎ"), ("b2", "b3", "3本指で左スワイプ"),
           ("b3", "b4", "消した文字が復活"), ("b4", "cta", "3本指で右スワイプ")]
BODY = [
    ("b1", "文字を消しすぎてしまったとき、", 0.3),
    ("b2", "3本指で、画面を左にスワイプすると、", 0.3),
    ("b3", "取り消しで、元に戻ります！", 0.5),
    ("b4", "右にスワイプすれば、やり直しもできます。", 0.0),
]
BODY_HOLD = 1.3
CTA = dict(lines=[("3本指で", WHITE, 100), ("左スワイプ！", YEL, 124)], spoken="保存して試してね！",
           chip="メモ・メール・LINEで使える")

PART = dict(
    title="3本指で取り消し・やり直し",
    intro="文字を消しすぎたとき、もう一度打ち直していませんか？",
    steps=[
        ("文字を消しすぎた", "例えば、メモに書いた買い物リストを、うっかり消しすぎてしまったとします。", ("body", "b2")),
        ("3本指で左にスワイプ", "そんな時は、指を3本そろえて、画面を左にスワイプします。", ("b2", "b2+1.4")),
        ("取り消しで元どおり", "画面の上に取り消すと表示されて、消した文字が元に戻ります。", ("b3", "b4")),
        ("右スワイプでやり直し", "反対に、3本指で右にスワイプすると、やり直しになります。", ("b4", "cta")),
        ("ダブルタップでもOK", "ちなみに、3本指で画面をトントンと2回タップしても、取り消しができます。", ("b3", "b3+1.0")),
    ],
    outro="メモ、メール、LINEなど、文字を打つアプリならどこでも使えます。ぜひ試してみてください。",
)

# ---- big centered iPhone (fallback layout) ----
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

FULL = ["買い物リスト", "・牛乳", "・卵 10個", "・食パン", "・バナナ", "・トマト"]
KEEP = 2                                   # lines left after the over-deletion

def times(T):
    k = dict(delete=T.at["b1"] + 0.4, swipeL=T.at["b2"] + 0.6, undone=T.at["b2"] + 1.4,
             swipeR=T.at["b4"] + 0.3, redone=T.at["b4"] + 1.1)
    return k

def visible_lines(t, k):
    n = len(FULL)
    if t >= k["delete"]:
        p = clamp((t - k["delete"]) / 1.2)
        n = len(FULL) - int(round((len(FULL) - KEEP) * p))
    if t >= k["undone"]: n = len(FULL)
    if t >= k["redone"]: n = KEEP
    return n

def banner(ps, label, t, at):
    if not (at <= t < at + 1.4): return
    a = clamp(min((t - at) / 0.15, (at + 1.4 - t) / 0.25))
    def draw(l):
        w = 170; x0 = BW / 2 - w / 2
        rr(l, (x0, 66, x0 + w, 108), 21, (60, 60, 66))
        txt(l, (BW / 2, 87), label, 20, WHITE, anchor="mm")
    fade(ps, a, draw)

def fingers(ps, t, k):
    for start, end, d in ((k["swipeL"] - 0.25, k["undone"], -1), (k["swipeR"] - 0.25, k["redone"], 1)):
        if start <= t < end + 0.15:
            q = ease_inout((t - start - 0.25) / (end - start - 0.25)) if t > start + 0.25 else 0
            cx = BW / 2 + d * (-90 + 180 * q)
            ly = Image.new("RGBA", ps.size, (0, 0, 0, 0)); dd = ImageDraw.Draw(ly)
            for i, dy in enumerate((-70, 0, 70)):
                x, y = cx + (i - 1) * 10, 330 + dy
                dd.ellipse((x - 28, y - 28, x + 28, y + 28), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3)
            if q > 0:
                y = 470
                dd.line((BW / 2 - d * 90, y, cx, y), fill=(255, 214, 10, 255), width=6)
                dd.polygon([(cx + d * 18, y), (cx, y - 12), (cx, y + 12)], fill=(255, 214, 10, 255))
            ps.alpha_composite(ly)

def screen(t, k):
    ps = Image.new("RGBA", (BW, BH), (255, 253, 245, 255))
    txt(ps, (56, 36), "9:41", 22, INK, anchor="lm")
    txt(ps, (24, 96), "‹ メモ", 24, (200, 150, 0), bold=False, anchor="lm")
    n = visible_lines(t, k)
    for i, s in enumerate(FULL[:n]):
        restored = k["undone"] <= t < k["redone"] and i >= KEEP
        if restored and t < k["undone"] + 1.2:
            rra(ps, (18, 142 + i * 56, 300, 186 + i * 56), 8, (48, 209, 88, 70))
        txt(ps, (26, 164 + i * 56), s, 34 if i == 0 else 30, INK, bold=i == 0, anchor="lm")
    y = 164 + n * 56 - 56
    if int(t * 2.5) % 2 == 0:
        x = 26 + font(30, False).getlength(FULL[n - 1]) + 4
        ImageDraw.Draw(ps).line((x, y - 20, x, y + 20), fill=(200, 150, 0), width=3)
    banner(ps, "取り消す", t, k["undone"])
    banner(ps, "やり直す", t, k["redone"])
    # keyboard (bottom) with the delete key flashing while deleting
    rr(ps, (0, 560, BW, BH), 0, (210, 212, 218))
    for r in range(4):
        for q in range(10 if r < 3 else 5):
            kw = (BW - 20) / 10
            x = 10 + q * kw * (1 if r < 3 else 2); y = 576 + r * 66
            rr(ps, (x + 3, y, x + kw * (1 if r < 3 else 2) - 3, y + 56), 8, WHITE)
    dk = (BW - 70, 576 + 2 * 66, BW - 13, 576 + 2 * 66 + 56)
    deleting = k["delete"] <= t < k["delete"] + 1.2
    rr(ps, dk, 8, (255, 120, 110) if deleting and int(t * 8) % 2 == 0 else (180, 183, 192))
    txt(ps, ((dk[0] + dk[2]) / 2, (dk[1] + dk[3]) / 2), "削除", 16, INK, anchor="mm")
    fingers(ps, t, k)
    return ps

def SCREEN(t, T): return screen(t, times(T))

def draw_body(c, t, T):
    big_phone(c, screen(t, times(T)))

def draw_hook_art(ly, t): pass

def sfx(T):
    k = times(T)
    return [("click", k["delete"] + i * 0.25) for i in range(4)] + [("whoosh", k["swipeL"]), ("ding", k["undone"]),
            ("whoosh", k["swipeR"]), ("pop", k["redone"])]

def stills(T):
    k = times(T)
    return [k["delete"] + 1.3, (k["swipeL"] + k["undone"]) / 2, k["undone"] + 0.5, (k["swipeR"] + k["redone"]) / 2, k["redone"] + 0.5]
