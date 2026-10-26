# MacとiPhoneの神連携機能⑤ 認証コードの自動入力（シリーズ最終回）
import math
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="s01_renkei", title="MacとiPhoneの神連携機能", spoken="MacとiPhoneの、かみ連携機能",
              hook_split=("MacとiPhoneの", "神連携機能"), total=5)
NUM, SLUG = 5, "code"
NEXT = "Mac神ショートカット⑥"
BODY = [
    ("b1", "iPhoneのSMSに届いた認証コード、", 0.3),
    ("b2", "MacのSafariなら、入力欄に候補として出てきます！", 0.3),
    ("b3", "クリックするだけで入力完了。", 0.3),
    ("b4", "テキストメッセージ転送をオンにしておけばOK！", 0.0),
]
BODY_HOLD = 0.85
CTA = dict(lines=[("設定 → メッセージ →", WHITE, 84), ("テキストメッセージ転送", YEL, 100)], spoken="保存して試してね！",
           chip="Macをオンにするだけ")
CODE = "482913"

def times(T):
    return dict(sms=T.at["b1"] + 0.4, suggest=T.at["b2"] + 0.4, click=T.at["b3"] + 0.5, filled=T.at["b3"] + 0.65,
                done=T.at["b3"] + 1.0, settings=T.at["b4"] + 0.2, extra=T.at["b4"] + 0.6)

def mac(t, k):
    ms = mac_screen_base()
    window(ms, (30, 50, 610, 470), None)
    rr(ms, (180, 60, 460, 82), 11, (236, 236, 240)); txt(ms, (320, 71), "mybank.example.jp", 13, (90, 90, 96), bold=False, anchor="mm")
    rr(ms, (130, 110, 510, 450), 16, (246, 247, 250), outline=(225, 225, 232))
    txt(ms, (320, 150), "ログイン", 28, INK, anchor="mm")
    txt(ms, (320, 190), "SMSに届いた認証コードを入力", 15, GRAY, bold=False, anchor="mm")
    filled = t >= k["filled"]
    focus = t >= k["sms"]
    rr(ms, (170, 222, 470, 276), 10, WHITE, outline=BLUE if focus else (200, 200, 206), width=3 if focus else 1)
    if filled:
        n = min(len(CODE), int((t - k["filled"]) / 0.03) + 1)
        txt(ms, (320, 249), " ".join(CODE[:n]), 28, INK, anchor="mm")
    elif focus and int(t * 2) % 2 == 0:
        ImageDraw.Draw(ms).line((188, 235, 188, 263), fill=BLUE, width=2)
    done = t >= k["done"]
    rr(ms, (170, 380, 470, 428), 10, GREEN if done else BLUE)
    if done:
        check(ms, 262, 392, 22, WHITE, 4); txt(ms, (334, 404), "ログイン完了", 19, WHITE, anchor="mm")
    else:
        txt(ms, (320, 404), "ログイン", 19, WHITE, anchor="mm")
    if k["suggest"] <= t < k["filled"] + 0.1:
        a = e_at(t, k["suggest"], 0.3)
        pulse = (math.sin(t * 7) + 1) / 2
        def drop(l):
            shadow(l, (170, 282, 470, 362), 10)
            rr(l, (170, 282, 470, 362), 10, WHITE, outline=(210, 210, 215))
            app_icon(l, 186, 298, 46, GREEN, "bubble")
            txt(l, (246, 308), "メッセージから", 14, GRAY, bold=False, anchor="lm")
            txt(l, (246, 338), CODE, 24, INK, anchor="lm")
            ImageDraw.Draw(l).rounded_rectangle((170, 282, 470, 362), 10, outline=(255, 190, 0, int(255 * pulse)), width=4)
        fade(ms, a, drop)
        if t >= k["suggest"] + 0.4:
            p = ease_out((t - k["suggest"] - 0.4) / max(0.3, k["click"] - k["suggest"] - 0.4))
            cursor(ms, 560 + (380 - 560) * p, 440 + (325 - 440) * p, clamp((t - k["click"]) / 0.3) if t >= k["click"] else 0)
    return ms

def phone(t, k):
    if t >= k["settings"]:
        ps = phone_screen_base((242, 242, 247, 255))
        txt(ps, (16, 64), "メッセージ", 26, INK)
        rr(ps, (10, 104, PW - 10, 172), 12, WHITE)
        txt(ps, (22, 125), "テキストメッセージ", 15, INK, anchor="lm"); txt(ps, (22, 150), "転送", 15, INK, anchor="lm")
        txt(ps, (PW - 22, 138), "›", 24, GRAY, anchor="rm")
        rr(ps, (10, 190, PW - 10, 250), 12, WHITE)
        txt(ps, (22, 220), "MacBook", 16, INK, anchor="lm")
        toggle(ps, PW - 72, 206, t >= k["settings"] + 0.5)
        if k["settings"] + 0.2 <= t:
            p = (math.sin(t * 7) + 1) / 2
            ImageDraw.Draw(ps).rounded_rectangle((10, 190, PW - 10, 250), 12, outline=(255, 190, 0, int(255 * p)), width=3)
        return ps
    ps = phone_screen_base((0, 0, 0, 255), dark_text=False)
    ps.alpha_composite(grad(PW, PH, (255, 140, 90), (120, 60, 200)))
    txt(ps, (38, 25), "9:41", 17, WHITE, anchor="lm")
    g = PW / 4; s = g * 0.68
    cols = [(10, 132, 255), (52, 199, 89), (255, 159, 10), (255, 59, 48), (175, 82, 222), (90, 200, 250)]
    for r in range(5):
        for q in range(4):
            app_icon(ps, q * g + (g - s) / 2, 70 + r * g * 1.1, s, cols[(r * 4 + q) % len(cols)])
    if t >= k["sms"]:
        e = e_at(t, k["sms"], 0.4)
        def ban(l):
            y = 50 - (1 - e) * 60
            shadow(l, (8, y, PW - 8, y + 100), 16, blur=8, off=4)
            rr(l, (8, y, PW - 8, y + 100), 18, (246, 246, 248, 250))
            app_icon(l, 18, y + 14, 34, GREEN, "bubble")
            txt(l, (60, y + 31), "SMS", 15, INK, anchor="lm")
            txt(l, (18, y + 72), f"認証コード：{CODE}", 16, INK, anchor="lm")
        fade(ps, e, ban)
    return ps

def draw_body(c, t, T):
    k = times(T)
    stage(c, mac(t, k), phone(t, k))
    if t < T.at["b2"]:
        telop(c, t, T.body, [("iPhoneにSMSでコードが届く", WHITE)], size=84)
    elif t < T.at["b3"]:
        telop(c, t, T.at["b2"], [("Macの入力欄に候補が出る！", YEL)], size=84)
    elif t < T.at["b4"]:
        telop(c, t, T.at["b3"], [("クリックで入力完了！", YEL)], size=100)
    else:
        telop(c, t, T.at["b4"], [("テキストメッセージ転送をON", YEL)], size=84)
    badge(c, t, k["done"], "スマホを見なくてOK", 1290, GREEN, size=42, cx=370)
    badge(c, t, k["extra"], "設定は1回だけ", 1410, PURPLE, size=42, cx=370)

def sfx(T):
    k = times(T)
    return [("pop", k["sms"]), ("pop", k["suggest"]), ("click", k["click"]), ("ding", k["done"]), ("pop", k["extra"])]

def stills(T):
    k = times(T)
    return [k["sms"] + 0.5, k["suggest"] + 0.6, k["filled"] + 0.3, k["done"] + 0.5, k["extra"] + 0.6]
