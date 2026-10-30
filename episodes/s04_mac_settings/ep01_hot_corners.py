# Macの神設定① ホットコーナー（システム設定 → デスクトップとDock → ホットコーナー）
import math
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="s04_mac_settings", title="Macの神設定", spoken="Macの、かみ設定",
              hook_split=("Macの", "神設定"), total=3)
NUM, SLUG = 1, "hot_corners"
NEXT = "タップでクリック"
BODY = [
    ("b1", "画面の角に、マウスを持っていくだけで、", 0.3),
    ("b2", "一瞬で、デスクトップが表示されます！", 0.3),
    ("b3", "設定は、デスクトップとドックの、ホットコーナーから。", 0.3),
    ("b4", "画面ロックや、クイックメモも割り当てられます。", 0.0),
]
BODY_HOLD = 0.9
CTA = dict(lines=[("デスクトップとDock →", WHITE, 84), ("ホットコーナー", YEL, 120)], spoken="保存して試してね！",
           chip="マウスを角に寄せるだけ")

def times(T):
    return dict(move=T.at["b1"] + 0.3, arrive=T.at["b1"] + 1.6, show=T.at["b2"] + 0.05, done=T.at["b2"] + 0.7,
                settings=T.at["b3"], btn=T.at["b3"] + 0.8, sheet=T.at["b3"] + 1.5,
                assign=T.at["b4"] + 0.3, assign2=T.at["b4"] + 0.9, extra=T.at["b4"] + 0.6)

def file_icon(ms, x, y, label, col):
    rr(ms, (x, y, x + 56, y + 46), 8, col)
    rr(ms, (x, y - 6, x + 24, y + 4), 4, col)
    txt(ms, (x + 28, y + 62), label, 14, WHITE, anchor="mm")

def lines_in(ms, box, n, col=(225, 225, 232)):
    x0, y0, x1, y1 = box
    for i in range(n):
        rr(ms, (x0 + 20, y0 + 54 + i * 30, x1 - 20 - (60 if i % 3 == 2 else 0), y0 + 66 + i * 30), 6, col)

def desktop(t, k):
    ms = mac_screen_base()
    for i, (lab, col) in enumerate([("書類", (90, 170, 250)), ("写真", (90, 170, 250)), ("請求書", (255, 255, 255))]):
        file_icon(ms, MW - 90, 60 + i * 100, lab, col)
    # windows: pushed off to the edges when the desktop is shown
    p = ease_inout((t - k["show"]) / 0.45) if t > k["show"] else 0
    w1 = (60 - 470 * p, 60, 560 - 470 * p, 400)
    w2 = (280 + 600 * p, 120, 780 + 600 * p, 470)
    window(ms, tuple(int(v) for v in w1), "メモ"); lines_in(ms, w1, 9)
    window(ms, tuple(int(v) for v in w2), "Safari"); lines_in(ms, w2, 10)
    # cursor travels to the bottom-right corner
    q = ease_inout((t - k["move"]) / (k["arrive"] - k["move"])) if t > k["move"] else 0
    cx, cy = 420 + (MW - 24 - 420) * q, 300 + (MH - 34 - 300) * q
    if t >= k["arrive"]:
        ly = Image.new("RGBA", (MW, MH), (0, 0, 0, 0)); d = ImageDraw.Draw(ly)
        for r0 in (0, 0.35):
            s = ((t - k["arrive"]) * 1.2 + r0) % 1
            r = 30 + s * 160
            d.ellipse((MW - r, MH - r, MW + r, MH + r), outline=(255, 214, 10, int(255 * (1 - s))), width=7)
        ms.alpha_composite(ly)
    cursor(ms, cx, cy)
    return ms

SIDEBAR = ["Wi-Fi", "Bluetooth", "一般", "外観", "デスクトップとDock", "ディスプレイ", "壁紙"]

def settings(t, k):
    ms = mac_screen_base()
    box = (40, 40, MW - 40, MH - 20)
    window(ms, box, None)
    x0, y0, x1, y1 = box
    rr(ms, (x0, y0 + 34, x0 + 230, y1), 0, (238, 238, 242))
    for i, s in enumerate(SIDEBAR):
        y = y0 + 50 + i * 44
        if i == 4: rr(ms, (x0 + 10, y, x0 + 220, y + 36), 8, BLUE)
        txt(ms, (x0 + 24, y + 18), s, 16, WHITE if i == 4 else INK, bold=i == 4, anchor="lm")
    txt(ms, (x0 + 260, y0 + 66), "デスクトップとDock", 22, INK, anchor="lm")
    for i, s in enumerate(["サイズ", "拡大", "画面上の位置", "Dockを自動的に表示/非表示"]):
        y = y0 + 100 + i * 46
        rr(ms, (x0 + 250, y, x1 - 20, y + 38), 8, WHITE)
        txt(ms, (x0 + 266, y + 19), s, 15, INK, bold=False, anchor="lm")
        if i == 3: toggle(ms, x1 - 76, y + 6, False)
    bx = (x1 - 190, y1 - 60, x1 - 24, y1 - 22)
    hi = t >= k["btn"]
    rr(ms, bx, 8, (255, 236, 150) if hi else WHITE, outline=(200, 200, 206), width=1)
    txt(ms, ((bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2), "ホットコーナー…", 15, INK, anchor="mm")
    if hi:
        pz = (math.sin(t * 8) + 1) / 2
        ImageDraw.Draw(ms).rounded_rectangle(bx, 8, outline=(255, 190, 0, int(255 * pz)), width=3)
        if t < k["sheet"]:
            cursor(ms, bx[0] + 90, bx[1] + 22, clamp((t - k["btn"]) / 0.3))
    if t >= k["sheet"]:
        a = e_at(t, k["sheet"], 0.3)
        def sheet(l):
            sb = (150, 90, MW - 150, MH - 50)
            shadow(l, sb, 14)
            rr(l, sb, 14, (250, 250, 252))
            txt(l, (MW / 2, sb[1] + 30), "ホットコーナー", 18, INK, anchor="mm")
            mini = (MW / 2 - 110, 190, MW / 2 + 110, 330)
            l.alpha_composite(grad(220, 140, (64, 92, 200), (150, 70, 170)), (int(mini[0]), int(mini[1])))
            labels = {"tl": "−", "tr": "−", "bl": "−", "br": "デスクトップ"}
            if t >= k["assign"]: labels["bl"] = "画面をロック"
            if t >= k["assign2"]: labels["tr"] = "クイックメモ"
            pos = {"tl": (175, 150), "tr": (MW - 345, 150), "bl": (175, 330), "br": (MW - 345, 330)}
            for key, (x, y) in pos.items():
                new = (key == "bl" and k["assign"] <= t < k["assign"] + 1.2) or (key == "tr" and k["assign2"] <= t < k["assign2"] + 1.2)
                on = labels[key] != "−"
                rr(l, (x, y, x + 170, y + 40), 8, (255, 236, 150) if new else (WHITE if not on else (220, 235, 255)),
                   outline=(200, 200, 206), width=1)
                txt(l, (x + 12, y + 20), labels[key], 15, INK, bold=on, anchor="lm")
                txt(l, (x + 156, y + 20), "⌄", 15, GRAY, anchor="mm")
            rr(l, (MW / 2 + 140, sb[3] - 54, MW / 2 + 230, sb[3] - 18), 8, BLUE)
            txt(l, (MW / 2 + 185, sb[3] - 36), "完了", 15, WHITE, anchor="mm")
        fade(ms, a, sheet)
    return ms

def draw_body(c, t, T):
    k = times(T)
    stage(c, desktop(t, k) if t < k["settings"] else settings(t, k), None)
    if t < T.at["b2"]:
        telop(c, t, T.body, [("画面の角にマウスを寄せる", WHITE)], size=88)
    elif t < T.at["b3"]:
        telop(c, t, T.at["b2"], [("デスクトップが一瞬で！", YEL)], size=100)
    elif t < T.at["b4"]:
        telop(c, t, T.at["b3"], [("Dock設定 → ホットコーナー", YEL)], size=88)
    else:
        telop(c, t, T.at["b4"], [("ロックやメモも割り当てOK", YEL)], size=88)
    badge(c, t, k["done"], "ウィンドウを閉じなくてOK", 1290, GREEN, size=44)
    badge(c, t, k["extra"], "4つの角に1つずつ設定できる", 1410, PURPLE, size=44)

def draw_hook_art(ly, t):
    x0, y0, x1, y1 = 300, 1170, 780, 1440
    rr(ly, (x0, y0, x1, y1), 18, (22, 22, 26), outline=(90, 90, 100), width=3)
    ly.alpha_composite(grad(450, 240, (64, 92, 200), (150, 70, 170)), (x0 + 15, y0 + 15))
    ImageDraw.Draw(ly).polygon([(x0 - 30, y1), (x1 + 30, y1), (x1 + 12, y1 + 22), (x0 - 12, y1 + 22)], fill=(196, 198, 204))
    q = (t * 0.7) % 1
    p = ease_inout(min(1, q * 1.6))
    cx, cy = 480 + (x1 - 40 - 480) * p, 1280 + (y1 - 50 - 1280) * p
    d = ImageDraw.Draw(ly)
    if q > 0.62:
        s = (q - 0.62) / 0.38; r = 20 + s * 90
        d.ellipse((x1 - 15 - r, y1 - 15 - r, x1 - 15 + r, y1 - 15 + r), outline=(255, 214, 10, int(255 * (1 - s))), width=6)
    cursor(ly, cx, cy)

def sfx(T):
    k = times(T)
    return [("whoosh", k["move"]), ("ding", k["arrive"]), ("whoosh", k["show"]), ("pop", k["settings"]),
            ("click", k["btn"]), ("pop", k["sheet"]), ("pop", k["assign"]), ("pop", k["assign2"])]

def stills(T):
    k = times(T)
    return [k["move"] + 0.6, k["show"] + 0.6, k["btn"] + 0.3, k["sheet"] + 0.5, k["assign2"] + 0.4]

PART = dict(
    title="ホットコーナー",
    intro="ウィンドウがたくさん開いていて、デスクトップのファイルが見えない。そんな時、いちいちウィンドウを閉じていませんか？",
    steps=[
        ("ポインタを画面の角へ", "ホットコーナーを設定すると、マウスのポインタを、画面の角に持っていくだけで、", ("body", "b2")),
        ("デスクトップが一瞬で表示", "ウィンドウが端に寄って、デスクトップが一瞬で表示されます。", ("b2", "b3")),
        ("システム設定 → デスクトップとDock", "設定は、システム設定の、デスクトップとドックを開いて、", ("b3", "b3+0.8")),
        ("「ホットコーナー」ボタン", "一番下にある、ホットコーナーのボタンをクリックします。", ("b3+0.7", "b3+1.6")),
        ("角ごとに機能を選ぶ", "4つの角それぞれに、デスクトップや、画面ロック、クイックメモなどを選んで、完了を押せば設定完了です。", ("b3+1.5", "cta")),
    ],
    outro="よく使う機能を角に置いておけば、マウスを動かすだけで呼び出せます。",
)
