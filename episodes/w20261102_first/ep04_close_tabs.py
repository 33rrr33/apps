# iPhone爆速神操作④ Safariのタブボタン長押し→「○個のタブをすべて閉じる」で一気に閉じる（v3：ショート＋60秒パート）
import math
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="w20261102_first", title="iPhone爆速神操作", spoken="iPhone爆速、かみ操作",
              hook_split=("iPhone", "爆速神操作"), total=5)
NUM, SLUG = 4, "close_tabs"
NEXT = "アプリを一瞬で切り替え"
SCREEN_CROP = (0, 300, 400, 860)
HOOK = "タブ溜めてる人\n[今すぐ見て！]"
HOOK_SPOKEN = "タブ溜めてる人、今すぐ見て！"
N_TABS = 48
TELOPS = [("b1", "タブが\n{何十個も}…"), ("b2", "1個ずつ閉じるのは\n{めんどう}"),
          ("b3", "[タブボタン]を\n長押し"), ("b4", "[すべて閉じる]を\nタップ"), ("b5", "一瞬で\n[全部スッキリ！]")]
ACTIONS = [("b1", "b2", "タブがたまりすぎ…"), ("b2", "b3", "×で1個ずつ…"), ("b3", "b4", "タブボタン長押し"),
           ("b4", "b5", "「すべて閉じる」をタップ"), ("b5", "cta", "全部閉じた！")]
BODY = [
    ("b1", "Safariのタブ、何十個もたまっていませんか？", 0.2),
    ("b2", "1個ずつ閉じるのは、大変ですよね。", 0.2),
    ("b3", "右下のタブボタンを長押しして、", 0.2),
    ("b4", "すべて閉じるを選ぶと、", 0.3),
    ("b5", "一瞬で全部閉じられます！", 0.0),
]
BODY_HOLD = 1.5
CTA = dict(lines=[("タブボタン長押しで", WHITE, 92), ("一気に全部閉じる！", YEL, 116)], spoken="保存して試してね！",
           chip="何十個あっても一瞬")

PART = dict(
    title="Safariのタブを一気に閉じる",
    intro="Safariのタブ、気づいたら何十個もたまっていませんか？",
    steps=[
        ("タブがたまっている", "Safariでいろいろなページを開いていると、タブがどんどん増えていきます。", ("body", "b2")),
        ("1個ずつ閉じるのは大変", "タブの一覧で、バツを押して1個ずつ閉じることもできますが、数が多いと大変です。", ("b2", "b3")),
        ("タブボタンを長押し", "そこで、画面右下の、四角が2つ重なったタブボタンを、長押しします。", ("b3", "b3+1.5")),
        ("すべて閉じるを選ぶ", "メニューが出たら、赤い文字の、何個のタブをすべて閉じる、を選びます。確認が出た場合は、もう一度選んで確定します。", ("b3+1.2", "b4+1.0")),
        ("一瞬で全部閉じる", "これで、たまっていたタブが、一瞬で全部閉じます。", ("b4+0.6", "cta")),
        ("1個だけ閉じることも", "ちなみに、同じメニューの、このタブを閉じる、を選べば、今見ているタブだけを閉じられます。", ("b3+1.0", "b3+1.6")),
    ],
    outro="タブがたまったら、右下のタブボタンを長押しするだけ。何十個あっても一瞬なので、ぜひ試してみてください。",
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

TAB_BTN = (362, 790)
CARD_W, CARD_H = 170, 200
CARDS = [("カフェ特集", (214, 150, 90)), ("天気予報", (90, 160, 230)), ("レシピ検索", (240, 120, 100)), ("乗換案内", (80, 190, 140)),
         ("ニュース", (150, 150, 170)), ("通販サイト", (250, 180, 60)), ("地図", (120, 200, 120)), ("映画情報", (170, 100, 200))]
MENU = [("CLOSE_ALL", RED), ("このタブを閉じる", INK), ("新規タブ", INK)]

def times(T):
    k = dict(grid_x=T.at["b2"] + 0.5, page=T.at["b3"] - 0.1, press=T.at["b3"] + 0.5, menu=T.at["b3"] + 1.1,
             pick=T.at["b4"] + 0.9)
    k["gone"] = k["pick"] + 0.2
    return k

def card_xy(i, scroll=0):
    return 20 + (i % 2) * 190, 320 + (i // 2) * 240 - scroll

def tabs_icon(d, cx, cy, col):
    d.rounded_rectangle((cx - 12, cy - 8, cx + 6, cy + 10), 4, outline=col, width=3)
    d.line((cx - 6, cy - 14, cx + 10, cy - 14), fill=col, width=3)
    d.line((cx + 12, cy - 12, cx + 12, cy + 4), fill=col, width=3)

def toolbar(ps, d, blank=False):
    d.rectangle((0, 674, BW, BH), fill=(246, 246, 248))
    d.line((0, 674, BW, 674), fill=(215, 215, 220), width=1)
    rr(ps, (16, 690, BW - 16, 738), 14, (229, 229, 234))
    if blank:
        d.ellipse((32, 704, 46, 718), outline=(142, 142, 147), width=2); d.line((44, 716, 50, 722), fill=(142, 142, 147), width=2)
    else:
        txt(ps, (BW / 2, 714), "cafe-guide.jp", 20, INK, bold=False, anchor="mm")
        txt(ps, (34, 714), "ぁあ", 16, INK, bold=False, anchor="lm")
    col = BLUE
    txt(ps, (38, 790), "‹", 52, col if not blank else (190, 190, 196), bold=False, anchor="mm")
    txt(ps, (112, 790), "›", 52, (190, 190, 196), bold=False, anchor="mm")
    d.rounded_rectangle((186, 784, 214, 808), 4, outline=col, width=3)
    d.rectangle((194, 780, 206, 790), fill=(246, 246, 248))
    d.line((200, 770, 200, 794), fill=col, width=3); d.line((192, 778, 200, 770), fill=col, width=3); d.line((208, 778, 200, 770), fill=col, width=3)
    d.arc((268, 776, 292, 806), 90, 270, fill=col, width=3); d.arc((282, 776, 306, 806), 270, 90, fill=col, width=3)
    tabs_icon(d, *TAB_BTN, col)
    rr(ps, (BW / 2 - 70, 840, BW / 2 + 70, 846), 3, INK)

def page(ps, d):
    ps.alpha_composite(grad(BW - 32, 200, (214, 150, 90), (120, 70, 40)), (16, 130))
    d.ellipse((150, 170, 250, 290), fill=(250, 245, 235))
    txt(ps, (20, 80), "cafe-guide.jp", 16, (120, 120, 126), bold=False, anchor="lm")
    txt(ps, (20, 350), "週末行きたい", 30, INK)
    txt(ps, (20, 392), "おしゃれカフェ10選", 30, INK)
    for i in range(7):
        rr(ps, (20, 452 + i * 30, BW - 20 - (90 if i == 6 else 0), 466 + i * 30), 6, (222, 222, 228))

def grid(ps, d, t, k):
    ps.paste((236, 236, 241, 255), (0, 0, BW, BH))
    closing = clamp((t - k["grid_x"]) / 0.35)
    for i in range(-2, 8):
        x, y = card_xy(i)
        idx = i
        if i == 0 and closing > 0:
            a = 1 - closing
            if a <= 0: continue
            x -= 120 * closing
        if i > 0 and closing > 0:
            pass
        title, col = CARDS[idx % len(CARDS)]
        ly = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
        shadow(ly, (x, y, x + CARD_W, y + CARD_H), 16, blur=6, off=3, a=60)
        rr(ly, (x, y, x + CARD_W, y + CARD_H), 16, WHITE)
        ly.alpha_composite(grad(CARD_W - 16, 110, col, tuple(int(v * 0.6) for v in col)), (int(x + 8), int(y + 28)))
        for j in range(3): rr(ly, (x + 10, y + 150 + j * 14, x + CARD_W - 10 - j * 30, y + 158 + j * 14), 4, (222, 222, 228))
        dl = ImageDraw.Draw(ly)
        dl.ellipse((x + CARD_W - 26, y + 6, x + CARD_W - 8, y + 24), fill=(200, 200, 206))
        dl.line((x + CARD_W - 21, y + 11, x + CARD_W - 13, y + 19), fill=WHITE, width=2)
        dl.line((x + CARD_W - 13, y + 11, x + CARD_W - 21, y + 19), fill=WHITE, width=2)
        txt(ly, (x + CARD_W / 2, y + CARD_H + 18), title, 17, INK, bold=False, anchor="mm")
        if i == 0 and closing > 0: ly.putalpha(ly.getchannel("A").point(lambda v: int(v * (1 - closing))))
        ps.alpha_composite(ly)
    d.rectangle((0, 760, BW, BH), fill=(236, 236, 241))
    txt(ps, (40, 800), "+", 44, BLUE, bold=False, anchor="mm")
    n = N_TABS - (1 if t >= k["grid_x"] else 0)
    txt(ps, (BW / 2, 800), f"{n}個のタブ", 20, INK, anchor="mm")
    txt(ps, (BW - 40, 800), "完了", 22, BLUE, anchor="mm")

def screen(t, k):
    ps = Image.new("RGBA", (BW, BH), (255, 255, 255, 255))
    d = ImageDraw.Draw(ps)
    n = N_TABS - (1 if t >= k["grid_x"] else 0)
    if t < k["page"]:
        grid(ps, d, t, k)
    elif t < k["gone"]:
        page(ps, d); toolbar(ps, d)
    else:
        toolbar(ps, d, blank=True)
        p = clamp((t - k["gone"]) / 0.4)
        # the old page collapses away
        if p < 1:
            ly = Image.new("RGBA", (BW, BH), (0, 0, 0, 0)); page(ly, ImageDraw.Draw(ly))
            s = 1 - 0.7 * ease_out(p)
            ly = ly.crop((0, 60, BW, 674)).resize((max(1, int(BW * s)), max(1, int(614 * s))))
            ly.putalpha(ly.getchannel("A").point(lambda v: int(v * (1 - p))))
            ps.alpha_composite(ly, (int(TAB_BTN[0] - ly.width * ease_out(p) - (BW - ly.width) * (1 - ease_out(p)) / 2 * 0), int(60 + (TAB_BTN[1] - 60) * ease_out(p) * 0.6)))
        else:
            for i in range(6):
                d.rounded_rectangle((34 + (i % 3) * 116, 200 + (i // 3) * 120, 34 + (i % 3) * 116 + 84, 200 + (i // 3) * 120 + 84), 18, fill=(229, 229, 234))
    txt(ps, (56, 36), "9:41", 22, INK, anchor="lm")
    # context menu
    if k["menu"] <= t < k["gone"]:
        p = ease_out((t - k["menu"]) / 0.2)
        ly = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
        x0, x1, y1 = 70, 390, 756; y0 = y1 - 56 * len(MENU)
        shadow(ly, (x0, y0, x1, y1), 16, blur=14, off=6, a=100)
        rr(ly, (x0, y0, x1, y1), 16, (248, 248, 250))
        dl = ImageDraw.Draw(ly)
        for i, (lab, col) in enumerate(MENU):
            y = y0 + i * 56
            if lab == "CLOSE_ALL":
                if k["pick"] - 0.1 <= t: rr(ly, (x0, y, x1, y + 56), 16, (228, 228, 234)); dl.rectangle((x0, y + 30, x1, y + 56), fill=(228, 228, 234))
                lab = f"{n}個のタブをすべて閉じる"
                dl.line((x1 - 36, y + 20, x1 - 20, y + 36), fill=col, width=3); dl.line((x1 - 20, y + 20, x1 - 36, y + 36), fill=col, width=3)
            elif lab == "このタブを閉じる":
                dl.line((x1 - 36, y + 20, x1 - 20, y + 36), fill=col, width=3); dl.line((x1 - 20, y + 20, x1 - 36, y + 36), fill=col, width=3)
            else:
                dl.rounded_rectangle((x1 - 40, y + 16, x1 - 16, y + 40), 5, outline=col, width=2)
                dl.line((x1 - 28, y + 22, x1 - 28, y + 34), fill=col, width=2); dl.line((x1 - 34, y + 28, x1 - 22, y + 28), fill=col, width=2)
            txt(ly, (x0 + 20, y + 28), lab, 21, col, bold=False, anchor="lm")
            if i < len(MENU) - 1: dl.line((x0, y + 56, x1, y + 56), fill=(215, 215, 220), width=1)
        if p < 1:
            ly = ly.resize((BW, BH)); ly.putalpha(ly.getchannel("A").point(lambda v: int(v * p)))
        ps.alpha_composite(ly)
        k["_menu_y0"] = y0
    # finger
    fp = None
    cx0, cy0 = card_xy(0)
    if k["grid_x"] - 0.4 <= t < k["grid_x"] + 0.2: fp = (cx0 + CARD_W - 17, cy0 + 15)
    if k["page"] - 0.35 <= t < k["page"] + 0.1: fp = (290, 420)
    if k["press"] - 0.2 <= t < k["pick"] - 0.5: fp = TAB_BTN
    if k["pick"] - 0.5 <= t < k["pick"] + 0.15:
        q = ease_inout((t - (k["pick"] - 0.5)) / 0.4)
        ty = 756 - 56 * len(MENU) + 28
        fp = (TAB_BTN[0] + (230 - TAB_BTN[0]) * q, TAB_BTN[1] + (ty - TAB_BTN[1]) * q)
    if fp:
        fx, fy = fp
        if k["press"] <= t < k["menu"]:
            pr = (t - k["press"]) / (k["menu"] - k["press"])
            d.arc((fx - 40, fy - 40, fx + 40, fy + 40), -90, -90 + 360 * pr, fill=(255, 159, 10), width=6)
        fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((fx - 30, fy - 30, fx + 30, fy + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))
    return ps

def SCREEN(t, T): return screen(t, times(T))

def draw_body(c, t, T):
    k = times(T)
    big_phone(c, screen(t, k))
    if t < T.at["b3"]:
        telop(c, t, T.body, [("タブがたまりすぎ…", WHITE)], y0=400, size=96)
    elif t < T.at["b5"]:
        telop(c, t, T.at["b3"], [("タブボタンを長押し", YEL)], y0=400, size=90)
    else:
        telop(c, t, T.at["b5"], [("一瞬で全部閉じた！", YEL)], y0=400, size=96)

def draw_hook_art(ly, t):
    x0, y0 = 380, 1180
    q = (t * 0.7) % 1
    for i in range(4):
        p = clamp((q - 0.4 - i * 0.08) / 0.2)
        x, y = x0 + (i % 2) * 170, y0 + (i // 2) * 150
        if p < 1: rr(ly, (x + 60 * p, y, x + 150 + 60 * p, y + 130), 16, (245, 245, 248))

def sfx(T):
    k = times(T)
    return [("click", k["grid_x"]), ("pop", k["page"]), ("click", k["press"]), ("pop", k["menu"]), ("click", k["pick"]),
            ("whoosh", k["gone"]), ("ding", k["gone"] + 0.45)]

def stills(T):
    k = times(T)
    return [k["grid_x"] - 0.1, k["press"] + 0.3, k["menu"] + 0.5, k["pick"], k["gone"] + 0.8]
