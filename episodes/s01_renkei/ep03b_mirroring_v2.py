# MacとiPhoneの神連携機能③ iPhoneミラーリング — 作り直し版（20秒・エンドカード付き）
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="s01_renkei", title="MacとiPhoneの神連携機能", spoken="MacとiPhoneの、かみ連携機能",
              hook_split=("MacとiPhoneの", "神連携機能"), total=5)
NUM, SLUG = 3, "mirroring_v2"
NEXT = "インスタントホットスポット"
HOOK_BADGE = "iPhoneをMacで操作！"
BODY = [
    ("b1", "Macで、iPhoneミラーリングを開くと、", 0.3),
    ("b2", "iPhoneの画面が、Macにそのまま出てきます！", 0.3),
    ("b3", "マウスとキーボードで、文字入力もOK。", 0.3),
    ("b4", "iPhoneはロックしたままでOK！", 0.0),
]
BODY_HOLD = 1.0
CTA = dict(lines=[("macOS Sequoia と", WHITE, 90), ("iOS 18以降でOK", YEL, 120)], spoken="保存して試してね！")

APP_COLS = [(10, 132, 255), (52, 199, 89), (255, 159, 10), (255, 59, 48), (175, 82, 222), (90, 200, 250), (255, 204, 0), (88, 86, 214)]
WIN_C = (330, 250)                       # mirrored-iPhone window centre (left of the real iPhone)

def times(T):
    return dict(icon=T.at["b1"] + 0.2, click=T.at["b1"] + 1.4, open=T.at["b1"] + 1.55,
                tap=T.at["b3"] + 0.6, app=T.at["b3"] + 0.8, done=T.at["b2"] + 0.6, extra=T.at["b4"] + 0.5)

def home(img, x0, y0, w, rows=5):
    g = w / 4; s = g * 0.68
    for r in range(rows):
        for q in range(4):
            app_icon(img, x0 + q * g + (g - s) / 2, y0 + r * g * 1.05, s, APP_COLS[(r * 4 + q * 3) % len(APP_COLS)])

def mirror_window(t, k):
    """Phone-shaped window (170x370) showing the home screen, or the opened Notes app."""
    ly = Image.new("RGBA", (180, 380), (0, 0, 0, 0))
    rr(ly, (0, 0, 179, 379), 28, (30, 30, 34))
    if t >= k["app"]:
        scr = Image.new("RGBA", (166, 366), (255, 253, 245, 255))
        txt(scr, (14, 40), "メモ", 20, (200, 150, 0))
        typed = "・パン・卵"[:max(0, int((t - k["app"] - 0.4) / 0.18))]
        for i, s in enumerate(["買い物リスト", "・牛乳", typed]):
            txt(scr, (14, 80 + i * 26), s, 15, INK, bold=i == 0)
        if int(t * 2) % 2 == 0: ImageDraw.Draw(scr).line((70, 132, 70, 150), fill=BLUE, width=2)
    else:
        scr = grad(166, 366, (255, 140, 90), (120, 60, 200))
        home(scr, 8, 50, 150)
    m = Image.new("L", (166, 366), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 165, 365), 24, fill=255)
    scr.putalpha(m)
    ly.alpha_composite(scr, (7, 7))
    rr(ly, (60, 14, 120, 30), 8, (0, 0, 0))
    return ly

def mac(t, k):
    ms = mac_screen_base()
    # Dock (left of centre so the real iPhone never covers it)
    x0 = 330 - (6 * 70 + 12) / 2
    rra(ms, (x0, MH - 82, x0 + 6 * 70 + 12, MH - 10), 22, (255, 255, 255, 90))
    for i in range(6):
        x = x0 + 12 + i * 70
        if i == 5: app_icon(ms, x, MH - 75, 58, (40, 40, 46), "phone")
        else: app_icon(ms, x, MH - 75, 58, APP_COLS[i], "safari" if i == 0 else None)
    icon_c = (x0 + 12 + 5 * 70 + 29, MH - 46)
    if k["icon"] <= t < k["open"]:
        r = 42 + 6 * __import__("math").sin(t * 9)
        ImageDraw.Draw(ms).ellipse((icon_c[0] - r, icon_c[1] - r, icon_c[0] + r, icon_c[1] + r), outline=YEL, width=5)
        fade(ms, e_at(t, k["icon"], 0.3), lambda l: (rr(l, (icon_c[0] - 120, icon_c[1] - 104, icon_c[0] + 120, icon_c[1] - 62), 21, (0, 0, 0, 170)),
                                                    txt(l, (icon_c[0], icon_c[1] - 83), "iPhoneミラーリング", 20, WHITE, anchor="mm")))
        p = ease_out((t - k["icon"]) / max(0.3, k["click"] - k["icon"]))
        cursor(ms, 140 + (icon_c[0] + 4 - 140) * p, 180 + (icon_c[1] - 6 - 180) * p,
               clamp((t - k["click"]) / 0.3) if t >= k["click"] else 0)
    if t >= k["open"]:
        e = back_out(clamp((t - k["open"]) / 0.5), 1.2)
        w, h = int(180 * e), int(380 * e)
        if w > 10:
            win = mirror_window(t, k).resize((w, h), Image.BICUBIC)
            shadow(ms, (WIN_C[0] - w / 2, WIN_C[1] - h / 2, WIN_C[0] + w / 2, WIN_C[1] + h / 2), 24)
            ms.alpha_composite(win, (int(WIN_C[0] - w / 2), int(WIN_C[1] - h / 2)))
        if t >= k["tap"] - 0.8 and t < k["app"] + 0.6:
            # cursor taps the Notes icon (row 0, col 0 of the mirrored home screen)
            tx, ty = WIN_C[0] - 90 + 7 + 8 + 19, WIN_C[1] - 190 + 7 + 50 + 13
            p = ease_out((t - k["tap"] + 0.8) / 0.8)
            cursor(ms, 560 + (tx - 560) * p, 400 + (ty - 400) * p, clamp((t - k["tap"]) / 0.3) if t >= k["tap"] else 0)
    return ms

def phone(t, k):
    ps = Image.new("RGBA", (PW, PH), (0, 0, 0, 255))
    ps.alpha_composite(grad(PW, PH, (20, 30, 60), (60, 30, 80)))
    lock_c = (PW / 2, 78)
    d = ImageDraw.Draw(ps)
    d.arc((lock_c[0] - 9, lock_c[1] - 12, lock_c[0] + 9, lock_c[1] + 4), 180, 360, fill=WHITE, width=3)
    rr(ps, (lock_c[0] - 12, lock_c[1] - 4, lock_c[0] + 12, lock_c[1] + 14), 4, WHITE)
    txt(ps, (PW / 2, 150), "9:41", 70, WHITE, anchor="mm")
    txt(ps, (PW / 2, 200), "10月25日 日曜日", 17, WHITE, bold=False, anchor="mm")
    if t >= k["open"]:
        fade(ps, e_at(t, k["open"], 0.4), lambda l: (rr(l, (40, 470, PW - 40, 512), 21, (255, 255, 255, 60)),
                                                    txt(l, (PW / 2, 491), "Macで使用中", 17, WHITE, anchor="mm")))
    return ps

def draw_body(c, t, T):
    k = times(T)
    stage(c, mac(t, k), phone(t, k))
    if t < T.at["b2"]:
        telop(c, t, T.body, [("①「iPhoneミラーリング」を開く", WHITE)], size=80)
    elif t < T.at["b3"]:
        telop(c, t, T.at["b2"], [("iPhoneがMacの中に！", YEL)], size=100)
    elif t < T.at["b4"]:
        telop(c, t, T.at["b3"], [("マウスとキーボードで操作", YEL)], size=92)
    else:
        telop(c, t, T.at["b4"], [("iPhoneはロックのままOK", YEL)], size=92)
    badge(c, t, k["done"], "アプリもそのまま使える", 1290, GREEN, size=42, cx=370)
    if k["app"] <= t < k["extra"]:
        badge(c, t, k["app"] + 0.2, "キーボードで文字入力", 1410, WHITE, tc=INK, size=42, cx=370)
    badge(c, t, k["extra"], "iPhoneはカバンの中でOK", 1410, PURPLE, size=42, cx=370)

def draw_hook_art(ly, t):
    """Opening art: an iPhone shown inside the Mac, the real iPhone locked beside it."""
    rr(ly, (230, 1150, 740, 1450), 18, (22, 22, 26), outline=(90, 90, 100), width=3)
    ly.alpha_composite(grad(480, 270, (64, 92, 200), (150, 70, 170)), (245, 1165))
    ImageDraw.Draw(ly).polygon([(200, 1450), (770, 1450), (750, 1474), (220, 1474)], fill=(196, 198, 204))
    rr(ly, (430, 1180, 540, 1420), 18, (30, 30, 34))
    scr = grad(98, 228, (255, 140, 90), (120, 60, 200)); home(scr, 4, 30, 90, rows=4)
    ly.alpha_composite(scr, (436, 1186))
    rr(ly, (790, 1240, 900, 1480), 22, (36, 36, 40), outline=(120, 120, 130), width=3)
    ly.alpha_composite(grad(94, 224, (20, 30, 60), (60, 30, 80)), (798, 1248))
    d = ImageDraw.Draw(ly)
    d.arc((836, 1290, 854, 1306), 180, 360, fill=WHITE, width=3); rr(ly, (833, 1298, 857, 1316), 4, WHITE)
    for k in range(3):                                   # signal from the real iPhone to the Mac
        q = (t * 0.9 + k / 3) % 1; r = 30 + q * 120
        d.arc((790 - r, 1360 - r, 790 + r, 1360 + r), 160, 200, fill=(255, 214, 10, int(255 * (1 - q))), width=7)

def sfx(T):
    k = times(T)
    return [("pop", k["icon"]), ("click", k["click"]), ("whoosh", k["open"] + 0.2), ("ding", k["done"]),
            ("click", k["tap"]), ("pop", k["app"] + 0.2), ("pop", k["extra"])]

def stills(T):
    k = times(T)
    return [k["icon"] + 0.7, k["open"] + 0.6, k["done"] + 0.5, k["app"] + 1.0, k["extra"] + 0.6]
