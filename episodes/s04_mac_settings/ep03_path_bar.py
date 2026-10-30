# Macの神設定③ Finderのパスバー（表示 → パスバーを表示 / ⌥⌘P）・シリーズ最終回
import math
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="s04_mac_settings", title="Macの神設定", spoken="Macの、かみ設定",
              hook_split=("Macの", "神設定"), total=3)
NUM, SLUG = 3, "path_bar"
NEXT = "iPhone爆速神操作"
BODY = [
    ("b1", "Finderで、今どこにいるか迷うこと、ありませんか？", 0.3),
    ("b2", "表示メニューの、パスバーを表示を選ぶと、", 0.3),
    ("b3", "ウィンドウの下に、今いる場所が出ます！", 0.3),
    ("b4", "フォルダ名をダブルクリックで、一瞬で移動できます。", 0.0),
]
BODY_HOLD = 0.9
CTA = dict(lines=[("表示 →", WHITE, 96), ("パスバーを表示", YEL, 116)], spoken="保存して試してね！",
           chip="option＋command＋P でもOK")

PART = dict(
    title="Finderのパスバー",
    intro="Finderでフォルダを何回も開いているうちに、今どこにいるのか、わからなくなること、ありませんか？",
    steps=[
        ("今どこ？と迷う", "フォルダの奥の方に入っていくと、ウィンドウには、今のフォルダ名しか出ていません。", ("body", "b1+1.5")),
        ("メニューバーの「表示」", "そこで、画面の上のメニューバーから、表示、をクリックします。", ("b2", "b2+0.9")),
        ("「パスバーを表示」を選ぶ", "メニューの中にある、パスバーを表示、を選びます。キーボードなら、オプション、コマンド、Pでも同じです。", ("b2+0.6", "b3")),
        ("ウィンドウの下に場所が出る", "すると、ウィンドウの一番下に、今いるフォルダまでの道のりが、横一列で表示されます。", ("b3", "b4")),
        ("ダブルクリックで移動", "途中のフォルダ名をダブルクリックすると、そのフォルダへ一瞬で戻れます。", ("b4", "cta")),
    ],
    outro="一度オンにすれば、ずっと表示されたままです。迷子にならないFinderにしておきましょう。",
)

def times(T):
    return dict(menu=T.at["b2"] + 0.3, hover=T.at["b2"] + 0.9, pick=T.at["b2"] + 1.5, bar=T.at["b3"] + 0.1,
                dbl=T.at["b4"] + 1.0, jump=T.at["b4"] + 1.25, done=T.at["b3"] + 0.6, extra=T.at["b4"] + 1.4)

PATH = ["Macintosh HD", "ユーザ", "mac", "書類", "2026", "請求書"]
WIN = (40, 50, MW - 40, MH - 14)

def finder(t, k):
    ms = mac_screen_base()
    d = ImageDraw.Draw(ms)
    menus = ["Finder", "ファイル", "編集", "表示", "移動", "ウインドウ"]
    x = 48
    pos = {}
    for m in menus:
        w = font(15, m == "Finder").getlength(m)
        if m == "表示" and k["menu"] <= t < k["pick"] + 0.1: rr(ms, (x - 8, 2, x + w + 8, 24), 5, BLUE)
        txt(ms, (x, 13), m, 15, WHITE, bold=m == "Finder", anchor="lm"); pos[m] = x; x += w + 24
    jumped = t >= k["jump"]
    title = "書類" if jumped else "請求書"
    window(ms, WIN, title)
    x0, y0, x1, y1 = WIN
    rr(ms, (x0, y0 + 34, x0 + 170, y1), 0, (236, 236, 240))
    for i, s in enumerate(["AirDrop", "最近の項目", "アプリケーション", "デスクトップ", "書類", "ダウンロード"]):
        sel = (s == "書類" and jumped)
        if sel: rr(ms, (x0 + 8, y0 + 50 + i * 36, x0 + 162, y0 + 80 + i * 36), 7, (210, 210, 218))
        txt(ms, (x0 + 22, y0 + 65 + i * 36), s, 14, INK, bold=False, anchor="lm")
    files = ["2026", "2025", "企画書.pages", "見積もり.pdf", "メモ.txt"] if jumped else ["10月分.pdf", "9月分.pdf", "8月分.pdf", "7月分.pdf"]
    for i, f in enumerate(files):
        fx = x0 + 210 + (i % 4) * 150; fy = y0 + 70 + (i // 4) * 130
        folder = "." not in f
        col = (90, 170, 250) if folder else WHITE
        rr(ms, (fx, fy, fx + 70, fy + 56), 8, col, outline=None if folder else (200, 200, 206), width=1)
        if folder: rr(ms, (fx, fy - 7, fx + 30, fy + 5), 4, col)
        else: txt(ms, (fx + 35, fy + 28), "PDF" if f.endswith("pdf") else "", 13, (220, 60, 60), anchor="mm")
        txt(ms, (fx + 35, fy + 76), f, 13, INK, bold=False, anchor="mm")
    # path bar
    if t >= k["bar"]:
        a = e_at(t, k["bar"], 0.3)
        def bar(l):
            by = y1 - 40
            rr(l, (x0 + 170, by, x1, y1), 0, (244, 244, 247))
            ImageDraw.Draw(l).line((x0 + 170, by, x1, by), fill=(210, 210, 216), width=1)
            px = x0 + 186
            path = PATH[:4] if jumped else PATH
            for j, s in enumerate(path):
                hi = s == "書類" and k["dbl"] - 0.3 <= t < k["jump"] + 0.6
                w = font(13, False).getlength(s) + 26
                if hi: rr(l, (px - 4, by + 7, px + w, by + 33), 6, (255, 236, 150))
                rr(l, (px, by + 13, px + 14, by + 26), 2, (90, 170, 250))
                txt(l, (px + 20, by + 20), s, 13, INK, bold=False, anchor="lm")
                px += w + 4
                if j < len(path) - 1:
                    txt(l, (px, by + 20), "›", 15, GRAY, anchor="lm"); px += 14
            if t < k["bar"] + 1.6:
                pz = (math.sin(t * 8) + 1) / 2
                ImageDraw.Draw(l).rectangle((x0 + 172, by + 2, x1 - 2, y1 - 2), outline=(255, 190, 0, int(255 * pz)), width=3)
        fade(ms, a, bar)
    # View menu
    if k["menu"] <= t < k["pick"] + 0.1:
        mx, my = pos["表示"] - 8, 26
        items = ["アイコン", "リスト", "カラム", "ギャラリー", "-", "タブバーを表示", "パスバーを表示", "ステータスバーを表示", "サイドバーを隠す"]
        h = sum(10 if s == "-" else 30 for s in items) + 12
        shadow(ms, (mx, my, mx + 260, my + h), 10, blur=10, off=5)
        rr(ms, (mx, my, mx + 260, my + h), 10, (246, 246, 248))
        y = my + 6
        for s in items:
            if s == "-":
                ImageDraw.Draw(ms).line((mx + 10, y + 5, mx + 250, y + 5), fill=(210, 210, 214), width=1); y += 10; continue
            hi = s == "パスバーを表示" and t >= k["hover"]
            if hi: rr(ms, (mx + 6, y, mx + 254, y + 28), 6, BLUE)
            txt(ms, (mx + 20, y + 14), s, 15, WHITE if hi else INK, bold=False, anchor="lm")
            if s == "パスバーを表示": hy = y + 14
            y += 30
        if t >= k["hover"] - 0.4:
            q = ease_out((t - k["hover"] + 0.4) / 0.4)
            cursor(ms, mx + 40 + 80 * q, 120 + (hy - 120) * q, clamp((t - k["pick"] + 0.3) / 0.3) if t >= k["pick"] - 0.3 else 0)
    elif t < k["menu"]:
        cursor(ms, 420, 260)
    elif t >= k["bar"]:
        # cursor moves to "書類" in the path bar and double-clicks
        px = x0 + 186
        for s in PATH[:3]: px += font(13, False).getlength(s) + 26 + 4 + 14
        tx, ty = px + 30, y1 - 18
        q = ease_out((t - k["bar"] - 1.2) / 0.8) if t > k["bar"] + 1.2 else 0
        clk = 0
        for at in (k["dbl"], k["dbl"] + 0.15):
            if at <= t < at + 0.25: clk = (t - at) / 0.25
        cursor(ms, 560 + (tx - 560) * q, 300 + (ty - 300) * q, clk)
    return ms

def draw_body(c, t, T):
    k = times(T)
    stage(c, finder(t, k), None)
    if t < T.at["b2"]:
        telop(c, t, T.body, [("今どこのフォルダ…？", WHITE)], size=96)
    elif t < T.at["b3"]:
        telop(c, t, T.at["b2"], [("表示 → パスバーを表示", YEL)], size=92)
    elif t < T.at["b4"]:
        telop(c, t, T.at["b3"], [("今いる場所が一目でわかる", YEL)], size=86)
    else:
        telop(c, t, T.at["b4"], [("ダブルクリックで移動！", YEL)], size=96)
    badge(c, t, k["done"], "一度オンにすればずっと表示", 1290, GREEN, size=42)
    badge(c, t, k["extra"], "途中のフォルダへ一瞬で戻れる", 1410, PURPLE, size=42)

def draw_hook_art(ly, t):
    x0, y0, x1, y1 = 300, 1170, 780, 1440
    rr(ly, (x0, y0, x1, y1), 18, (246, 246, 248), outline=(90, 90, 100), width=3)
    d = ImageDraw.Draw(ly)
    for i in range(3):
        rr(ly, (x0 + 40 + i * 140, y0 + 50, x0 + 130 + i * 140, y0 + 120), 10, (90, 170, 250))
    rr(ly, (x0, y1 - 60, x1, y1), 0, (234, 234, 240))
    q = (t * 0.6) % 1
    s = "HD › ユーザ › 書類 › 請求書"
    n = int(len(s) * min(1, q * 1.8))
    txt(ly, (x0 + 24, y1 - 30), s[:n], 30, INK, anchor="lm")

def sfx(T):
    k = times(T)
    return [("click", k["menu"]), ("pop", k["hover"]), ("click", k["pick"]), ("whoosh", k["bar"]), ("ding", k["bar"] + 0.3),
            ("click", k["dbl"]), ("click", k["dbl"] + 0.15), ("pop", k["jump"]), ("pop", k["extra"])]

def stills(T):
    k = times(T)
    return [T.at["b1"] + 1.0, k["hover"] + 0.3, k["bar"] + 0.6, k["dbl"] + 0.1, k["jump"] + 0.5]
