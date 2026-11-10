# iPhone爆速神操作②（11/9週） メモやメールの一覧を2本指でなぞって、まとめて複数選択（v3：ショート＋60秒パート）
import math
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="w20261109_first", title="iPhone爆速神操作", spoken="iPhone爆速、かみ操作",
              hook_split=("iPhone", "爆速神操作"), total=5, offset=5)
NUM, SLUG = 2, "two_finger_select"
NEXT = "振って取り消し"
SCREEN_CROP = (0, 60, 400, 860)
HOOK = "1個ずつ選ぶ人\n{時間のムダ}です"
HOOK_SPOKEN = "1個ずつ選んでる人、時間のムダです！"
TELOPS = [("b1", "1個ずつ選ぶのは\n{めんどう}…"), ("b2", "[2本指]で\nなぞるだけ"),
          ("b3", "[まとめて選択]\nできる！"), ("b4", "削除も移動も\n[一気に]")]
ACTIONS = [("b1", "b2", "1個ずつタップ…"), ("b2", "b3", "2本指で下になぞる"),
           ("b3", "b4", "なぞった分だけ選択"), ("b4", "cta", "まとめて削除・移動")]
BODY = [
    ("b1", "メモを、1つずつ選んで消していませんか？", 0.3),
    ("b2", "2本指で、一覧を下になぞるだけで、", 0.3),
    ("b3", "まとめて選択できます！", 0.5),
    ("b4", "あとは、削除や移動を一気にできます。", 0.0),
]
BODY_HOLD = 1.2
CTA = dict(lines=[("2本指で", WHITE, 100), ("なぞるだけ！", YEL, 124)], spoken="保存して試してね！",
           chip="メモ・メール・ファイルで使える")

PART = dict(
    title="2本指でまとめて選択",
    intro="メモやメールを整理するとき、1つずつタップして選ぶの、面倒じゃないですか？",
    steps=[
        ("一覧を開く", "まず、メモアプリやメールアプリで、項目がずらっと並んだ一覧を開きます。", ("body", "b2")),
        ("2本指で一覧をなぞる", "指を2本そろえて、選びたい項目の上を、下に向かってなぞります。", ("b2", "b2+1.6")),
        ("なぞった分だけ選択", "すると自動で選択モードになって、なぞった項目にまとめてチェックが入ります。", ("b3", "b4")),
        ("削除や移動を一気に", "あとは、下に出てくる削除や移動を押せば、選んだ項目をまとめて処理できます。", ("b4", "cta")),
        ("ほかのアプリでも", "この2本指でなぞる選択は、メモやメールのほか、ファイルアプリなどでも使えます。", ("b2+0.4", "b3")),
    ],
    outro="1つずつ選ぶ必要はありません。2本指でなぞって、まとめて選択。ぜひ試してみてください。",
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

NOTES = [("買い物リスト", "牛乳、卵、食パン"), ("会議メモ", "来週までに資料"), ("旅行の持ち物", "充電器、パスポート"),
         ("読みたい本", "3冊目から"), ("Wi-Fiのパスワード", "ルーターの裏に記載"), ("ジムのメニュー", "スクワット30回"),
         ("観たい映画", "週末に観る"), ("レシピ", "玉ねぎ2個")]
ROW0, RH = 200, 80
SEL_FROM, SEL_TO = 1, 5                      # rows swept with two fingers (inclusive)

def times(T):
    return dict(tap1=T.at["b1"] + 0.6, tap2=T.at["b1"] + 1.4, drag=T.at["b2"] + 0.6, dragged=T.at["b2"] + 2.0,
                bar=T.at["b3"], delete=T.at["b4"] + 1.2)

def selected_rows(t, k):
    rows = set()
    if k["tap1"] <= t < k["drag"]:
        rows.add(0)
        if t >= k["tap2"]: rows.add(1)
    if t >= k["drag"]:
        p = clamp((t - k["drag"]) / (k["dragged"] - k["drag"]))
        last = SEL_FROM + int((SEL_TO - SEL_FROM + 1) * p - 1e-6)
        rows |= set(range(SEL_FROM, min(SEL_TO, last) + 1)) if p > 0 else set()
    return rows

def screen(t, k):
    ps = Image.new("RGBA", (BW, BH), (242, 242, 247, 255))
    txt(ps, (56, 36), "9:41", 22, INK, anchor="lm")
    txt(ps, (24, 84), "‹ フォルダ", 22, (200, 150, 0), bold=False, anchor="lm")
    sel_mode = t >= k["tap1"] - 0.3
    txt(ps, (BW - 24, 84), "完了" if sel_mode else "選択", 22, (200, 150, 0), bold=sel_mode, anchor="rm")
    txt(ps, (24, 140), "メモ", 40, INK, anchor="lm")
    deleted = t >= k["delete"]
    sel = selected_rows(t, k)
    rows = [n for i, n in enumerate(NOTES) if not (deleted and SEL_FROM <= i <= SEL_TO)]
    rr(ps, (14, ROW0 - 8, BW - 14, ROW0 + RH * min(len(rows), 7)), 14, WHITE)
    for j, (title, sub) in enumerate(rows[:7]):
        i = NOTES.index((title, sub))
        y = ROW0 + j * RH
        x = 30
        if sel_mode and not deleted:
            on = i in sel
            d = ImageDraw.Draw(ps)
            if on: d.ellipse((24, y + 24, 52, y + 52), fill=(255, 180, 0))
            else: d.ellipse((24, y + 24, 52, y + 52), outline=(190, 190, 196), width=2)
            if on: check(ps, 30, y + 30, 16, WHITE, 3)
            x = 66
        txt(ps, (x, y + 26), title, 22, INK, anchor="lm")
        txt(ps, (x, y + 52), sub, 16, GRAY, bold=False, anchor="lm")
        if j < 6: ImageDraw.Draw(ps).line((x, y + RH - 2, BW - 14, y + RH - 2), fill=(225, 225, 230), width=1)
    if deleted and t < k["delete"] + 1.0:
        txt(ps, (BW / 2, ROW0 + RH * len(rows) + 40), "5件のメモを削除しました", 18, GRAY, bold=False, anchor="mm")
    # bottom toolbar in select mode
    if sel_mode and not deleted:
        rr(ps, (0, BH - 90, BW, BH), 0, (248, 248, 250))
        n = len(sel)
        hi = t >= k["bar"]
        txt(ps, (40, BH - 50), "移動", 22, (200, 150, 0) if n else GRAY, anchor="lm")
        txt(ps, (BW - 40, BH - 50), "削除", 22, (255, 59, 48) if n else GRAY, bold=hi, anchor="rm")
        if hi:
            txt(ps, (BW / 2, BH - 50), f"{n}件を選択", 18, INK, bold=False, anchor="mm")
    # fingers
    ly = Image.new("RGBA", ps.size, (0, 0, 0, 0)); dd = ImageDraw.Draw(ly)
    for at in (k["tap1"], k["tap2"]):
        if at - 0.15 <= t < at + 0.25:
            r = 0 if at == k["tap1"] else 1
            y = ROW0 + r * RH + RH / 2
            dd.ellipse((24 - 6, y - 26, 52 + 6, y + 26), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3)
    if k["drag"] - 0.3 <= t < k["dragged"] + 0.3:
        p = clamp((t - k["drag"]) / (k["dragged"] - k["drag"]))
        y = ROW0 + SEL_FROM * RH + RH / 2 + (SEL_TO - SEL_FROM) * RH * p
        y0 = ROW0 + SEL_FROM * RH + RH / 2
        if p > 0: dd.line((150, y0, 150, y), fill=(255, 214, 10, 255), width=6)
        for dx in (-28, 28):
            dd.ellipse((150 + dx - 26, y - 26, 150 + dx + 26, y + 26), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3)
    if k["delete"] - 0.3 <= t < k["delete"] + 0.1:
        dd.ellipse((BW - 70, BH - 76, BW - 18, BH - 24), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3)
    ps.alpha_composite(ly)
    return ps

def SCREEN(t, T): return screen(t, times(T))

def draw_body(c, t, T):
    big_phone(c, screen(t, times(T)))

def draw_hook_art(ly, t): pass

def sfx(T):
    k = times(T)
    return [("click", k["tap1"]), ("click", k["tap2"]), ("whoosh", k["drag"])] + \
           [("pop", k["drag"] + i * (k["dragged"] - k["drag"]) / 5) for i in range(1, 6)] + [("click", k["delete"]), ("ding", k["delete"] + 0.2)]

def stills(T):
    k = times(T)
    return [k["tap2"] + 0.2, (k["drag"] + k["dragged"]) / 2, k["bar"] + 0.4, k["delete"] - 0.4, k["delete"] + 0.5]
