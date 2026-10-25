# MacとiPhoneの神連携機能④ インスタントホットスポット
import math
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="s01_renkei", title="MacとiPhoneの神連携機能", spoken="MacとiPhoneの、かみ連携機能",
              hook_split=("MacとiPhoneの", "神連携機能"), total=5)
NUM, SLUG = 4, "hotspot"
NEXT = "認証コードの自動入力"
BODY = [
    ("b1", "外でWiFiがないとき、MacのWiFiメニューを開くと、", 0.3),
    ("b2", "iPhoneの名前が出てきます！", 0.3),
    ("b3", "クリックするだけで、すぐネットにつながります。", 0.3),
    ("b4", "iPhoneのテザリング画面を開く必要もなし！", 0.0),
]
BODY_HOLD = 1.0
CTA = dict(lines=[("テザリングできる", WHITE, 96), ("契約ならすぐ使える！", YEL, 110)], spoken="保存して試してね！",
           chip="同じApple ID・Wi-Fi・Bluetooth をオン")

WIFI_X = 590                         # Wi-Fi icon in the menu bar (left of the real iPhone)
PANEL = (300, 32, 620, 330)          # Wi-Fi menu (Mac-screen coords)

def times(T):
    return dict(menu_click=T.at["b1"] + 1.6, menu=T.at["b1"] + 1.75, row=T.at["b2"] + 0.1,
                click=T.at["b3"] + 0.7, connected=T.at["b3"] + 0.9, close=T.at["b3"] + 1.9,
                done=T.at["b3"] + 1.0, extra=T.at["b4"] + 0.4)

def wifi_icon(img, x, y, s, col):
    d = ImageDraw.Draw(img)
    for r in (s, s * .66, s * .33):
        d.arc((x - r, y - r, x + r, y + r), 225, 315, fill=col, width=max(2, int(s * .16)))
    d.ellipse((x - s * .12, y - s * .12, x + s * .12, y + s * .12), fill=col)

def link_icon(img, x, y, s, col, w=3):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((x - s, y - s * .35, x, y + s * .35), int(s * .35), outline=col, width=w)
    d.rounded_rectangle((x - s * .2, y - s * .35, x + s * .8, y + s * .35), int(s * .35), outline=col, width=w)

def mac(t, k):
    ms = mac_screen_base()
    on = t >= k["connected"]
    if on: link_icon(ms, WIFI_X + 4, 13, 10, WHITE, 2)
    else: wifi_icon(ms, WIFI_X, 19, 12, WHITE)
    # Safari: offline → connected
    window(ms, (30, 60, 280, 420), "Safari")
    if on:
        fade(ms, e_at(t, k["connected"], 0.3), lambda l: (check(l, 130, 180, 46, GREEN, 7), txt(l, (155, 270), "接続しました", 24, INK, anchor="mm")))
    else:
        txt(ms, (155, 220), "インターネットに", 20, GRAY, anchor="mm")
        txt(ms, (155, 250), "接続されていません", 20, GRAY, anchor="mm")
    # cursor to the Wi-Fi icon, then to the iPhone row
    if k["menu_click"] - 1.0 <= t < k["menu"] + 0.2:
        p = ease_out((t - k["menu_click"] + 1.0) / 0.9)
        cursor(ms, 200 + (WIFI_X - 200) * p, 300 + (12 - 300) * p, clamp((t - k["menu_click"]) / 0.3) if t >= k["menu_click"] else 0)
    if k["menu"] <= t < k["close"]:
        a = e_at(t, k["menu"], 0.25) * (1 - clamp((t - k["close"] + 0.25) / 0.25))
        def panel(l):
            x0, y0, x1, y1 = PANEL
            shadow(l, PANEL, 14)
            rr(l, PANEL, 14, (246, 246, 248, 255))
            txt(l, (x0 + 18, y0 + 28), "Wi-Fi", 22, INK, anchor="lm"); toggle(l, x1 - 64, y0 + 14, True)
            txt(l, (x0 + 18, y0 + 74), "パーソナルホットスポット", 15, GRAY, anchor="lm")
            if t >= k["row"]:
                sel = t >= k["click"] + 0.1
                pulse = 0 if sel else (math.sin(t * 7) + 1) / 2
                rr(l, (x0 + 8, y0 + 92, x1 - 8, y0 + 150), 10, BLUE if sel else (225, 230, 245))
                if not sel: ImageDraw.Draw(l).rounded_rectangle((x0 + 8, y0 + 92, x1 - 8, y0 + 150), 10, outline=(255, 190, 0, int(255 * pulse)), width=4)
                ImageDraw.Draw(l).ellipse((x0 + 18, y0 + 102, x0 + 56, y0 + 140), fill=WHITE if sel else BLUE)
                link_icon(l, x0 + 39, y0 + 121, 10, BLUE if sel else WHITE)
                txt(l, (x0 + 68, y0 + 121), "あなたのiPhone", 19, WHITE if sel else INK, anchor="lm")
                txt(l, (x1 - 22, y0 + 121), "5G", 16, WHITE if sel else GRAY, anchor="rm")
            else:
                txt(l, (x0 + 18, y0 + 118), "検索中…", 17, GRAY, bold=False, anchor="lm")
            txt(l, (x0 + 18, y0 + 190), "その他のネットワーク", 15, GRAY, anchor="lm")
            txt(l, (x0 + 18, y0 + 226), "見つかりません", 17, (170, 170, 175), bold=False, anchor="lm")
        fade(ms, a, panel)
        if k["row"] + 0.3 <= t < k["close"]:
            tx, ty = PANEL[0] + 220, PANEL[1] + 118
            p = ease_out((t - k["row"] - 0.3) / max(0.3, k["click"] - k["row"] - 0.3))
            cursor(ms, WIFI_X + (tx - WIFI_X) * p, 14 + (ty - 14) * p, clamp((t - k["click"]) / 0.3) if t >= k["click"] else 0)
    return ms

def phone(t, k):
    ps = phone_screen_base((0, 0, 0, 255), dark_text=False)
    ps.alpha_composite(grad(PW, PH, (255, 140, 90), (120, 60, 200)))
    txt(ps, (38, 25), "9:41", 17, WHITE, anchor="lm")
    g = PW / 4; s = g * 0.68
    cols = [(10, 132, 255), (52, 199, 89), (255, 159, 10), (255, 59, 48), (175, 82, 222), (90, 200, 250)]
    for r in range(5):
        for q in range(4):
            app_icon(ps, q * g + (g - s) / 2, 70 + r * g * 1.1, s, cols[(r * 4 + q) % len(cols)])
    if t >= k["connected"]:
        rr(ps, (PW / 2 - 60, 10, PW / 2 + 60, 40), 15, GREEN)
        link_icon(ps, PW / 2 - 4, 25, 9, WHITE)
        fade(ps, e_at(t, k["connected"] + 0.2, 0.3), lambda l: (rr(l, (12, 380, PW - 12, 470), 18, (255, 255, 255, 235)),
             txt(l, (PW / 2, 410), "インターネット共有", 17, INK, anchor="mm"), txt(l, (PW / 2, 442), "1台接続中", 16, GREEN, anchor="mm")))
    return ps

def draw_body(c, t, T):
    k = times(T)
    stage(c, mac(t, k), phone(t, k))
    if t < T.at["b2"]:
        telop(c, t, T.body, [("① Wi-Fiメニューを開く", WHITE)], size=90)
    elif t < T.at["b3"]:
        telop(c, t, T.at["b2"], [("② iPhoneの名前が出る！", YEL)], size=92)
    elif t < T.at["b4"]:
        telop(c, t, T.at["b3"], [("クリックで即つながる！", YEL)], size=96)
    else:
        telop(c, t, T.at["b4"], [("iPhoneは触らなくてOK", YEL)], size=96)
    badge(c, t, k["done"], "パスワード入力も不要", 1290, GREEN, size=42, cx=370)
    badge(c, t, k["extra"], "iPhoneはポケットのままでOK", 1410, PURPLE, size=40, cx=370)

def sfx(T):
    k = times(T)
    return [("click", k["menu_click"]), ("pop", k["row"]), ("click", k["click"]), ("ding", k["connected"]), ("pop", k["extra"])]

def stills(T):
    k = times(T)
    return [k["menu"] + 0.5, k["row"] + 0.6, k["click"] + 0.15, k["connected"] + 0.8, k["extra"] + 0.6]
