# iPhone爆速神操作③（11/9週） iPhoneを振って入力を取り消す（シェイクで取り消し）（v3：ショート＋60秒パート）
import math
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="w20261109_first", title="iPhone爆速神操作", spoken="iPhone爆速、かみ操作",
              hook_split=("iPhone", "爆速神操作"), total=5)
NUM, SLUG = 3, "shake_undo"
NEXT = "アイコン長押しで詳細"
SCREEN_CROP = (0, 60, 400, 860)
# 2026-11-09 実験：短縮版（約12秒・エンドカードなし）。20秒版より最後まで見られてループしやすくする
DURATION, END_CARD = 12.0, False
HOOK = "削除キー連打は\n{今すぐやめて}"
HOOK_SPOKEN = "削除キー連打、今すぐやめて！"
TELOPS = [("b1", "打った文字を\n[まとめて消したい]"), ("b2", "iPhoneを\n[軽く振る]だけ"),
          ("b3", "[取り消す]で\n一発で消える！"), ("b4", "設定で\n[オン・オフ]もできる")]
ACTIONS = [("b1", "b2", "削除キーを連打…"), ("b2", "b3", "iPhoneを軽く振る"),
           ("b3", "b4", "「取り消す」をタップ"), ("b4", "cta", "アクセシビリティ→タッチ")]
BODY = [
    ("b1", "打った文字をまとめて消したいとき、", 0.15),
    ("b2", "iPhoneを軽く振って、", 0.15),
    ("b3", "取り消すを押すだけ！", 0.3),
    ("b4", "設定でオフにもできます。", 0.0),
]
BODY_HOLD = 0.8
CTA = dict(lines=[("iPhoneを", WHITE, 100), ("振って取り消し！", YEL, 116)], spoken="保存してね！",
           chip="削除キー連打いらず")

PART = dict(
    title="振って取り消し",
    intro="長い文章を打ち間違えたとき、削除キーを何回も押して消していませんか？",
    steps=[
        ("文字を入力したあと", "例えば、メモに文章を打ったあと、やっぱり今打った分を全部消したくなったとします。", ("body", "b2")),
        ("iPhoneを軽く振る", "そんな時は、iPhoneを持ったまま、軽く振ります。", ("b2", "b3")),
        ("「取り消す」をタップ", "入力を取り消すかどうか聞かれるので、取り消すをタップすると、今打った文字がまとめて消えます。", ("b3", "b4")),
        ("やり直しもできる", "消したあとにもう一度振ると、やり直しも選べます。", ("b3+1.0", "b4")),
        ("設定でオン・オフ", "この機能は、設定アプリの、アクセシビリティ、タッチにある、シェイクで取り消しで、オンとオフを切り替えられます。", ("b4", "cta")),
    ],
    outro="ポケットの中でうっかり反応するのが気になる人は、オフにしておくのもおすすめです。",
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

BASE = ["週末の予定", "土曜：買い物"]
TYPED = "日曜は朝からカフェで作業して、夜は映画を観に行く予定"

def times(T):
    return dict(type0=T.at["b1"] - 1.2, typed=T.at["b1"] + 0.6, press=T.at["b1"] + 1.0, shake=T.at["b2"] + 0.3,
                alert=T.at["b2"] + 1.0, tap=T.at["b3"] + 0.6, gone=T.at["b3"] + 0.8, settings=T.at["b4"] + 0.8)

def wrap_text(s, size, maxw):
    f = font(size, False); out, cur = [], ""
    for ch in s:
        if f.getlength(cur + ch) > maxw: out.append(cur); cur = ch
        else: cur += ch
    return out + ([cur] if cur else [])

def notes_screen(t, k):
    ps = Image.new("RGBA", (BW, BH), (255, 253, 245, 255))
    txt(ps, (56, 36), "9:41", 22, INK, anchor="lm")
    txt(ps, (24, 96), "‹ メモ", 24, (200, 150, 0), bold=False, anchor="lm")
    txt(ps, (26, 160), BASE[0], 34, INK, anchor="lm")
    txt(ps, (26, 214), BASE[1], 28, INK, bold=False, anchor="lm")
    n = int(len(TYPED) * clamp((t - k["type0"]) / (k["typed"] - k["type0"])))
    if k["press"] <= t < k["shake"]:                       # deleting one by one... slowly
        n = max(len(TYPED) - int((t - k["press"]) / 0.18), len(TYPED) - 6)
    if t >= k["gone"]: n = 0
    lines = wrap_text(TYPED[:n], 28, BW - 52)
    y = 266
    for s in lines:
        txt(ps, (26, y), s, 28, INK, bold=False, anchor="lm"); y += 46
    if int(t * 2.5) % 2 == 0:
        last = lines[-1] if lines else ""
        cy = y - 46 if lines else 266
        x = 26 + font(28, False).getlength(last) + 3
        ImageDraw.Draw(ps).line((x, cy - 18, x, cy + 18), fill=(200, 150, 0), width=3)
    if t >= k["gone"] and t < k["gone"] + 1.0:
        rra(ps, (18, 246, 380, 290), 10, (48, 209, 88, 60))
    # keyboard with a flashing delete key while tapping it one by one
    rr(ps, (0, 560, BW, BH), 0, (210, 212, 218))
    for r in range(4):
        for q in range(10 if r < 3 else 5):
            kw = (BW - 20) / 10; w = kw * (1 if r < 3 else 2)
            x = 10 + q * w; y = 576 + r * 66
            rr(ps, (x + 3, y, x + w - 3, y + 56), 8, WHITE)
    dk = (BW - 70, 576 + 2 * 66, BW - 13, 576 + 2 * 66 + 56)
    tapping = k["press"] <= t < k["shake"] - 0.3
    rr(ps, dk, 8, (255, 120, 110) if tapping and int(t * 6) % 2 == 0 else (180, 183, 192))
    txt(ps, ((dk[0] + dk[2]) / 2, (dk[1] + dk[3]) / 2), "削除", 16, INK, anchor="mm")
    if tapping:
        cx, cy = (dk[0] + dk[2]) / 2, (dk[1] + dk[3]) / 2
        fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((cx - 28, cy - 28, cx + 28, cy + 28), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))
    # alert
    if k["alert"] <= t < k["gone"]:
        a = e_at(t, k["alert"], 0.2)
        def alert(l):
            l.alpha_composite(Image.new("RGBA", l.size, (0, 0, 0, 70)))
            box = (60, 300, BW - 60, 470)
            rr(l, box, 18, (245, 245, 247))
            txt(l, (BW / 2, 345), "入力を取り消す", 22, INK, anchor="mm")
            d = ImageDraw.Draw(l)
            d.line((60, 400, BW - 60, 400), fill=(205, 205, 210), width=1)
            d.line((BW / 2, 400, BW / 2, 470), fill=(205, 205, 210), width=1)
            txt(l, ((60 + BW / 2) / 2, 435), "キャンセル", 20, BLUE, bold=False, anchor="mm")
            hi = t >= k["tap"] - 0.15
            if hi: rr(l, (BW / 2 + 2, 402, BW - 62, 468), 12, (225, 230, 240))
            txt(l, ((BW / 2 + BW - 60) / 2, 435), "取り消す", 20, BLUE, anchor="mm")
            if k["tap"] - 0.3 <= t < k["gone"]:
                cx = (BW / 2 + BW - 60) / 2
                ImageDraw.Draw(l).ellipse((cx - 28, 435 - 28, cx + 28, 435 + 28), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3)
        fade(ps, a, alert)
    # shake: jiggle the whole screen and draw motion marks at both edges
    if k["shake"] - 0.2 <= t < k["alert"] + 0.2:
        dx = int(14 * math.sin((t - k["shake"]) * 40)) if t < k["alert"] else 0
        moved = Image.new("RGBA", ps.size, (255, 253, 245, 255)); moved.alpha_composite(ps, (dx, 0)); ps = moved
        d = ImageDraw.Draw(ps)
        for side in (0, 1):
            x = 14 if side == 0 else BW - 14
            for i, y in enumerate((180, 240, 300)):
                w = 14 + 6 * ((int(t * 10) + i) % 2)
                d.line((x - (w if side == 0 else -w) * 0 , y, x + (w if side == 0 else -w), y + 18), fill=(255, 180, 0), width=6)
    return ps

def settings_screen(t, k):
    ps = Image.new("RGBA", (BW, BH), (242, 242, 247, 255))
    txt(ps, (56, 36), "9:41", 22, INK, anchor="lm")
    txt(ps, (24, 84), "‹ アクセシビリティ", 20, BLUE, bold=False, anchor="lm")
    txt(ps, (24, 132), "タッチ", 36, INK, anchor="lm")
    rows = ["AssistiveTouch", "簡易アクセス", "触覚タッチ", "シェイクで取り消し", "背面タップ"]
    y = 180
    for i, r in enumerate(rows):
        hi = i == 3
        rr(ps, (16, y, BW - 16, y + 64), 12, (255, 236, 150) if hi and t >= k["settings"] + 0.6 else WHITE)
        txt(ps, (34, y + 32), r, 20, INK, bold=hi, anchor="lm")
        if i == 3: toggle(ps, BW - 86, y + 14, True)
        else: txt(ps, (BW - 34, y + 32), "›", 26, GRAY, anchor="rm")
        y += 74
    return ps

def screen(t, k):
    return settings_screen(t, k) if t >= k["settings"] else notes_screen(t, k)

def SCREEN(t, T): return screen(t, times(T))

def draw_body(c, t, T):
    big_phone(c, screen(t, times(T)))

def draw_hook_art(ly, t): pass

def sfx(T):
    k = times(T)
    return [("click", k["press"] + i * 0.18) for i in range(5)] + [("whoosh", k["shake"]), ("pop", k["alert"]),
            ("click", k["tap"]), ("ding", k["gone"]), ("pop", k["settings"])]

def stills(T):
    k = times(T)
    return [k["press"] + 0.4, k["shake"] + 0.3, k["alert"] + 0.6, k["gone"] + 0.4, k["settings"] + 1.0]
