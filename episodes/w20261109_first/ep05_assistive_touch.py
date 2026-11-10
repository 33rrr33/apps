# iPhone爆速神操作⑤（11/9週） AssistiveTouch（画面上の丸ボタン）を1回タップでスクショ（v3・短縮版）
import math
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="w20261109_first", title="iPhone爆速神操作", spoken="iPhone爆速、かみ操作",
              hook_split=("iPhone", "爆速神操作"), total=5, offset=5)
NUM, SLUG = 5, "assistive_touch"
NEXT = "次は隠し神機能"
SCREEN_CROP = (0, 40, 400, 860)
# PDCA 実験 short_length：約12〜13秒・エンドカードなし
DURATION, END_CARD = 13.0, False
TAGS = {"length": "短縮版"}
HOOK = "スクショで指が\n{つりそうな人へ}"
HOOK_SPOKEN = "スクショで指がつりそうな人へ！"
TELOPS = [("b1", "画面に\n[丸いボタン]を出す"), ("b2", "[1回タップ]で\nスクショ！"),
          ("b3", "設定 → タッチ →\n[AssistiveTouch]"), ("b4", "ボタンは\n[好きな場所]へ")]
ACTIONS = [("b1", "b2", "画面上の丸ボタン"), ("b2", "b3", "丸ボタンを1回タップ"),
           ("b3", "b4", "シングルタップ＝スクショ"), ("b4", "cta", "ドラッグで移動")]
BODY = [
    ("b1", "画面に、この丸いボタンを出しておくと、", 0.15),
    ("b2", "1回タップでスクショが撮れます！", 0.2),
    ("b3", "設定のタッチから、オンにするだけ。", 0.15),
    ("b4", "ボタンは好きな場所に動かせます。", 0.0),
]
BODY_HOLD = 0.8
CTA = dict(lines=[("丸ボタン", WHITE, 110), ("1タップでスクショ！", YEL, 104)], spoken="保存してね！",
           chip="片手でも撮れる")

PART = dict(
    title="AssistiveTouchでワンタップスクショ",
    intro="スクリーンショットを撮るとき、ボタンを2つ同時に押すのが大変だと感じたことはありませんか？",
    steps=[
        ("丸いボタンを出す", "AssistiveTouchをオンにすると、画面の端に、半透明の丸いボタンが出てきます。", ("body", "b2")),
        ("1回タップでスクショ", "このボタンを1回タップするだけで、スクリーンショットが撮れるように設定できます。", ("b2", "b3")),
        ("設定 → アクセシビリティ → タッチ", "設定は、設定アプリの、アクセシビリティから、タッチ、AssistiveTouchを開いてオンにします。", ("b3", "b3+1.0")),
        ("シングルタップ＝スクリーンショット", "カスタムアクションのシングルタップを、スクリーンショットにすれば準備完了です。", ("b3+0.8", "b4")),
        ("ボタンは好きな場所へ", "ボタンはドラッグして、邪魔にならない場所に動かせます。", ("b4", "cta")),
    ],
    outro="片手で持ったままでも、サッとスクショが撮れます。ぜひ試してみてください。",
)

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

def times(T):
    return dict(tap=T.at["b2"] + 0.2, shot=T.at["b2"] + 0.35, settings=T.at["b3"], custom=T.at["b3"] + 0.9,
                drag=T.at["b4"] + 0.2, dragged=T.at["b4"] + 1.2)

def finger(ps, x, y):
    fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((x - 30, y - 30, x + 30, y + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))

def at_button(ps, cx, cy, glow=0.0):
    def draw(l):
        d = ImageDraw.Draw(l)
        if glow > 0: d.rounded_rectangle((cx - 44, cy - 44, cx + 44, cy + 44), 22, outline=(255, 214, 10, int(255 * glow)), width=6)
        d.rounded_rectangle((cx - 34, cy - 34, cx + 34, cy + 34), 16, fill=(40, 40, 44, 200))
        for r, a in ((24, 70), (17, 120), (10, 255)):
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, a))
    fade(ps, 1.0, draw)

def home(t, k):
    ps = grad(BW, BH, (90, 170, 250), (175, 82, 222))
    txt(ps, (56, 36), "9:41", 22, WHITE, anchor="lm")
    cols = [(52, 199, 89), (10, 132, 255), (255, 159, 10), (255, 59, 48), (175, 82, 222), (90, 200, 250), (255, 214, 10), (142, 142, 147)]
    names = ["メッセージ", "Safari", "写真", "カメラ", "メモ", "天気", "時計", "設定"]
    for i in range(16):
        x = 26 + (i % 4) * 92; y = 90 + (i // 4) * 110
        rr(ps, (x, y, x + 66, y + 66), 16, cols[i % 8])
        txt(ps, (x + 33, y + 84), names[i % 8], 13, WHITE, bold=False, anchor="mm")
    shot = t >= k["shot"]
    if shot:
        fl = clamp(1 - (t - k["shot"]) / 0.25)
        if fl > 0: ps.alpha_composite(Image.new("RGBA", (BW, BH), (255, 255, 255, int(255 * fl))))
        p = ease_out((t - k["shot"] - 0.1) / 0.5)
        if p > 0:
            w = int(BW - (BW - 110) * p); h = int(BH - (BH - 236) * p)
            th = ps.copy().resize((max(10, w), max(10, h)))
            x = int(20 * p); y = int((BH - h - 40) * p)
            rr(ps, (x - 4, y - 4, x + th.width + 4, y + th.height + 4), 10, WHITE)
            ps.alpha_composite(th, (x, y))
    glow = clamp(1 - abs(t - k["tap"]) / 0.4)
    at_button(ps, BW - 50, 560, glow)
    if k["tap"] - 0.3 <= t < k["tap"] + 0.25: finger(ps, BW - 50, 560)
    return ps

def settings(t, k):
    ps = Image.new("RGBA", (BW, BH), (242, 242, 247, 255))
    txt(ps, (56, 36), "9:41", 22, INK, anchor="lm")
    custom = t >= k["custom"]
    txt(ps, (24, 84), "‹ タッチ", 20, BLUE, bold=False, anchor="lm")
    txt(ps, (24, 132), "AssistiveTouch", 32, INK, anchor="lm")
    rr(ps, (16, 170, BW - 16, 234), 12, WHITE)
    txt(ps, (34, 202), "AssistiveTouch", 20, INK, bold=True, anchor="lm")
    toggle(ps, BW - 86, 186, t >= k["settings"] + 0.4)
    txt(ps, (30, 270), "カスタムアクション", 15, GRAY, bold=False, anchor="lm")
    rows = [("シングルタップ", "スクリーンショット" if custom else "メニューを開く"), ("ダブルタップ", "なし"), ("長押し", "なし")]
    for i, (a, b) in enumerate(rows):
        y = 290 + i * 70
        hi = i == 0 and custom
        rr(ps, (16, y, BW - 16, y + 62), 12, (255, 236, 150) if hi else WHITE)
        txt(ps, (34, y + 31), a, 19, INK, bold=False, anchor="lm")
        txt(ps, (BW - 40, y + 31), b, 16, BLUE if hi else GRAY, bold=hi, anchor="rm")
    at_button(ps, BW - 50, 640)
    return ps

def moving(t, k):
    ps = home(t, dict(k, shot=99, tap=-9))
    # hide the static button and draw the dragged one
    p = ease_inout((t - k["drag"]) / (k["dragged"] - k["drag"])) if t > k["drag"] else 0
    x, y = (BW - 50) + (60 - (BW - 50)) * p, 560 + (720 - 560) * p
    base = grad(BW, BH, (90, 170, 250), (175, 82, 222)).crop((BW - 92, 518, BW - 8, 602))
    ps.alpha_composite(base, (BW - 92, 518))
    at_button(ps, x, y)
    if k["drag"] - 0.2 <= t < k["dragged"] + 0.2: finger(ps, x + 6, y + 6)
    return ps

def screen(t, k):
    if t >= k["drag"] - 0.3: return moving(t, k)
    if t >= k["settings"]: return settings(t, k)
    return home(t, k)

def SCREEN(t, T): return screen(t, times(T))

def draw_body(c, t, T):
    big_phone(c, screen(t, times(T)))

def draw_hook_art(ly, t): pass

def sfx(T):
    k = times(T)
    return [("click", k["tap"]), ("ding", k["shot"]), ("pop", k["settings"]), ("pop", k["custom"]), ("whoosh", k["drag"])]

def stills(T):
    k = times(T)
    return [T.at["b1"] + 0.5, k["shot"] + 0.4, k["settings"] + 0.5, k["custom"] + 0.3, (k["drag"] + k["dragged"]) / 2]
