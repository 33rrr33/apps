# MacとiPhoneの神連携機能② ユニバーサルクリップボード
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="s01_renkei", title="MacとiPhoneの神連携機能", spoken="MacとiPhoneの、かみ連携機能",
              hook_split=("MacとiPhoneの", "神連携機能"), total=5)
NUM, SLUG = 2, "clipboard"
BODY = [
    ("b1", "iPhoneでコピーして、", 0.3),
    ("b2", "Macでコマンド、Vを押すだけ！", 0.3),
    ("b3", "そのまま貼り付けられます。写真もOK！", 0.0),
]
BODY_HOLD = 1.4
CTA = dict(lines=[("同じApple IDなら", WHITE, 96), ("すぐ使える！", YEL, 130)], spoken="保存して試してね！",
           chip="Wi-Fi・Bluetooth・Handoff をオン")
NOTE = ["明日 10:00", "渋谷駅 ハチ公前"]

def times(T):
    copy = T.at["b1"] + 0.6                 # text selected + 「コピー」
    fly_t = T.at["b2"] + 0.1                # chip flies iPhone -> Mac
    paste = fly_t + 0.8                     # ⌘V pressed, text appears
    return dict(copy=copy, fly=fly_t, paste=paste, done=T.at["b3"] + 0.1,
                photo=T.at["b3"] + 1.1, photo_in=T.at["b3"] + 1.8)

def photo_img(w, h):
    img = grad(w, h, (255, 170, 90), (220, 80, 120))
    d = ImageDraw.Draw(img)
    d.ellipse((w * .65, h * .15, w * .85, h * .46), fill=(255, 240, 200))
    d.polygon([(0, h), (w * .35, h * .46), (w * .65, h)], fill=(70, 50, 110))
    d.polygon([(w * .4, h), (w * .75, h * .6), (w, h)], fill=(100, 60, 140))
    return img

def phone(t, k):
    ps = phone_screen_base((255, 253, 245, 255))
    txt(ps, (20, 60), "メモ", 30, (200, 150, 0))
    if t >= k["copy"]:
        a = e_at(t, k["copy"], 0.3)
        rra(ps, (14, 124, 242, 196), 8, (10, 132, 255, int(90 * a)))
        def pop(l):
            rr(l, (40, 74, 216, 112), 14, (30, 30, 34))
            txt(l, (88, 93), "コピー", 19, WHITE, anchor="mm")
            ImageDraw.Draw(l).line((136, 82, 136, 104), fill=(90, 90, 96), width=2)
            txt(l, (176, 93), "調べる", 19, WHITE, anchor="mm")
        if t < k["fly"] + 0.3: fade(ps, a, pop)
    for i, s in enumerate(NOTE): txt(ps, (24, 130 + i * 34), s, 24, INK, bold=False)
    ps.alpha_composite(photo_img(200, 130), (24, 220))
    if k["photo"] - 0.4 <= t < k["photo"] + 0.3:
        rra(ps, (18, 214, 230, 356), 10, (10, 132, 255, 90))
    for i in range(3):
        rr(ps, (24, 380 + i * 30, 232 - (60 if i == 2 else 0), 390 + i * 30), 4, (232, 230, 220))
    return ps

def mac(t, k):
    ms = mac_screen_base()
    window(ms, (40, 60, 600, 470), "メモ")
    if t >= k["paste"]:
        fade(ms, e_at(t, k["paste"], 0.3), lambda l: [txt(l, (76, 120 + i * 52), s, 38, INK) for i, s in enumerate(NOTE)])
    if t >= k["photo_in"]:
        fade(ms, e_at(t, k["photo_in"], 0.3), lambda l: l.alpha_composite(photo_img(240, 156), (76, 250)))
    return ms

def draw_body(c, t, T):
    k = times(T)
    stage(c, mac(t, k), phone(t, k))
    if t < T.at["b2"]:
        telop(c, t, T.body, [("① iPhoneでコピー", WHITE)], size=90)
    elif t < T.at["b3"]:
        telop(c, t, T.at["b2"], [("② Macで ⌘V", YEL)], size=110)
    else:
        telop(c, t, T.at["b3"], [("そのまま貼り付け！", YEL)], size=100)
    fly(c, t, k["fly"], 0.75, (PX0 + 128, PY0 + 160), (MX0 + 230, MY0 + 140), "明日 10:00…", BLUE)
    fly(c, t, k["photo"], 0.7, (PX0 + 128, PY0 + 285), (MX0 + 196, MY0 + 328), "写真", ORANGE)
    if k["fly"] + 0.3 <= t < k["done"]:
        keycaps(c, t, k["fly"] + 0.3, [("⌘", "command"), ("V", None)], 1300, press_t=k["paste"] - 0.1, cx=370, scale=0.9)
    badge(c, t, k["done"], "コピペが端末をまたぐ！", 1290, GREEN, size=42, cx=370)
    badge(c, t, k["photo_in"], "写真もOK", 1400, ORANGE, size=42, cx=370)

def sfx(T):
    k = times(T)
    return [("click", k["copy"]), ("whoosh", k["fly"] + 0.2), ("click", k["paste"] - 0.1), ("ding", k["paste"]),
            ("pop", k["done"]), ("whoosh", k["photo"] + 0.2), ("pop", k["photo_in"])]

def stills(T):
    k = times(T)
    return [k["copy"] + 0.4, k["fly"] + 0.4, k["paste"] + 0.3, k["done"] + 0.5, k["photo"] + 0.35, k["photo_in"] + 0.5]
