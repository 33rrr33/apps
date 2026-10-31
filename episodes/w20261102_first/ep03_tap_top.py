# iPhone爆速神操作③ 画面のいちばん上（時計のあたり）をタップして、長いリストの一番上まで一瞬で戻る（v3：ショート＋60秒パート）
import datetime, math
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="w20261102_first", title="iPhone爆速神操作", spoken="iPhone爆速、かみ操作",
              hook_split=("iPhone", "爆速神操作"), total=5)
NUM, SLUG = 3, "tap_top"
NEXT = "タブを一気に閉じる"
SCREEN_CROP = (0, 0, 400, 560)            # status bar (the clock) + the list
HOOK = "スクロール連打は\n{今すぐやめて}"
HOOK_SPOKEN = "スクロール連打、今すぐやめて！"
TELOPS = [("b1", "長いリストを\n[ずっと下まで]…"), ("b2", "戻るのに\n{スクロール連打}？"),
          ("b3", "[時計のあたり]を\nタップ"), ("b4", "一瞬で\n[一番上へ！]"), ("b5", "[多くのアプリ]で\n使える")]
ACTIONS = [("b1", "b2", "下へどんどんスクロール"), ("b2", "b3", "戻るのに何回もスクロール…"),
           ("b3", "b4", "時計の部分をタップ"), ("b4", "b5", "一瞬で一番上へ"), ("b5", "cta", "メールや設定でもOK")]
BODY = [
    ("b1", "長いリストを、ずっと下まで見たあと、", 0.2),
    ("b2", "上に戻るのに、何回もスクロールしていませんか？", 0.2),
    ("b3", "画面のいちばん上、時計のあたりをタップ。", 0.2),
    ("b4", "一瞬で、一番上まで戻ります！", 0.3),
    ("b5", "メールや設定など、多くのアプリで使えます。", 0.0),
]
BODY_HOLD = 0.4
CTA = dict(lines=[("時計のあたりを", WHITE, 96), ("タップで一番上へ！", YEL, 116)], spoken="保存して試してね！",
           chip="スクロール連打はもう不要")

PART = dict(
    title="画面上タップで一番上へ",
    intro="長いページを下まで見たあと、一番上に戻るのに、何回もスクロールしていませんか？",
    steps=[
        ("長いリストを下まで見る", "メモやメール、ウェブページなど、長いリストやページを、ずっと下まで見ていったとします。", ("body", "b2")),
        ("戻るのが大変", "一番上に戻りたいとき、指で何回もスクロールするのは、けっこう面倒ですよね。", ("b2", "b3")),
        ("時計のあたりをタップ", "そんな時は、画面のいちばん上、時計が表示されているあたりを、1回だけタップします。", ("b3", "b3+1.9")),
        ("一瞬で一番上へ", "すると自動でスクロールして、一瞬で一番上まで戻ります。", ("b3+1.5", "b5")),
        ("多くのアプリで使える", "メモ、メール、設定、Safariなど、縦に長い画面なら、多くのアプリで同じように使えます。", ("b5", "cta")),
        ("場所はどのアプリも同じ", "ちなみに、ステータスバーと呼ばれる、この一番上の部分は、どのアプリでも同じ場所なので、すぐに覚えられます。", ("b3", "b4")),
    ],
    outro="一番上に戻りたいときは、時計のあたりをタップ。ぜひ試してみてください。",
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

BG_G = (242, 242, 247)
ROW_H, LIST_Y = 86, 262
NOTES = ["買い物リスト", "旅行の持ち物", "会議メモ", "カレーのレシピ", "読みたい本", "Wi-Fiのパスワード", "誕生日プレゼント案",
         "ジムのメニュー", "観たい映画", "引っ越しのTODO", "家計簿メモ", "ゴミの日", "英単語", "名言メモ", "子どもの予定"]
PREV = ["牛乳、卵、パン", "充電器、パスポート", "来週までに資料", "玉ねぎ2個、にんじん", "3冊目から", "ルーターの裏に記載",
        "予算5000円", "スクワット30回", "週末に観る", "電気・水道の連絡", "今月の支出", "燃えるゴミは火・金", "毎日10個",
        "あとで見返す", "水曜は習い事"]
N_ROWS = 160
DEEP = 4200

def note_date(i):
    d = datetime.date(2026, 10, 31) - datetime.timedelta(days=i * 3)
    return "8:15" if i == 0 else f"{d.year}/{d.month:02d}/{d.day:02d}"

def times(T):
    k = dict(tap=T.end["b3"] - 0.25)
    k["ups"] = [T.at["b1"] + 0.2 + i * 0.7 for i in range(3)]          # scroll further down (finger drags up)
    k["downs"] = [T.at["b2"] + 0.2 + i * 0.55 for i in range(4)]       # trying to go back by dragging down
    k["jump"] = k["tap"] + 0.12
    return k

def offset(t, k):
    off = DEEP
    for a in k["ups"]: off += 700 * ease_out((t - a) / 0.6) if t > a else 0
    for a in k["downs"]: off -= 160 * ease_out((t - a) / 0.45) if t > a else 0
    if t > k["jump"]: off *= 1 - ease_inout((t - k["jump"]) / 0.45)
    return off

def status_bar(ps, d, hl):
    if hl > 0:
        fade(ps, hl, lambda l: rr(l, (22, 16, 112, 56), 20, (255, 214, 10, 200)))
    txt(ps, (66, 36), "9:41", 24, INK, anchor="mm")
    rr(ps, (BW / 2 - 64, 16, BW / 2 + 64, 52), 18, (0, 0, 0))
    for i in range(4):
        h = 6 + i * 3; d.rectangle((292 + i * 7, 44 - h, 296 + i * 7, 44), fill=INK)
    d.rounded_rectangle((328, 28, 364, 44), 5, outline=INK, width=2)
    d.rounded_rectangle((331, 31, 356, 41), 3, fill=INK)
    d.rectangle((365, 33, 368, 39), fill=INK)

def screen(t, k):
    ps = Image.new("RGBA", (BW, BH), BG_G + (255,))
    d = ImageDraw.Draw(ps)
    off = offset(t, k)
    y0 = -off
    # large title + search (content space)
    if y0 + 230 > 0:
        txt(ps, (22, y0 + 150), "メモ", 46, INK, anchor="ls")
        rr(ps, (18, y0 + 176, BW - 18, y0 + 218), 12, (227, 227, 232))
        txt(ps, (58, y0 + 197), "検索", 21, (142, 142, 147), bold=False, anchor="lm")
        d.ellipse((30, y0 + 188, 44, y0 + 202), outline=(142, 142, 147), width=2)
        d.line((42, y0 + 200, 48, y0 + 206), fill=(142, 142, 147), width=2)
        txt(ps, (22, y0 + 248), "今日", 22, INK, anchor="ls")
    # rows
    first = max(0, int((off - LIST_Y) // ROW_H) - 1)
    for i in range(first, min(N_ROWS, first + 12)):
        y = y0 + LIST_Y + i * ROW_H
        if y > BH or y + ROW_H < 0: continue
        d.rectangle((14, y, BW - 14, y + ROW_H), fill=WHITE)
        if i == 0: rr(ps, (14, y, BW - 14, y + 30), 12, WHITE)
        txt(ps, (34, y + 30), NOTES[i % len(NOTES)], 22, INK, anchor="lm")
        txt(ps, (34, y + 60), note_date(i), 17, (120, 120, 126), bold=False, anchor="lm")
        txt(ps, (34 + font(17, False).getlength(note_date(i)) + 12, y + 60), PREV[i % len(PREV)], 17, (142, 142, 147), bold=False, anchor="lm")
        if i < N_ROWS - 1: d.line((34, y + ROW_H - 1, BW - 14, y + ROW_H - 1), fill=(222, 222, 226), width=1)
    # compact nav bar once scrolled
    if off > 120:
        a = clamp((off - 120) / 60)
        fade(ps, a, lambda l: ImageDraw.Draw(l).rectangle((0, 0, BW, 118), fill=(248, 248, 250, 245)))
        fade(ps, a, lambda l: (txt(l, (BW / 2, 92), "メモ", 22, INK, anchor="mm"),
                               txt(l, (16, 92), "‹ フォルダ", 21, (227, 160, 8), bold=False, anchor="lm"),
                               ImageDraw.Draw(l).line((0, 118, BW, 118), fill=(210, 210, 216), width=1)))
    # scroll indicator
    moving = any(a <= t < a + 1.0 for a in k["ups"] + k["downs"]) or k["jump"] <= t < k["jump"] + 0.9
    if moving:
        total = LIST_Y + N_ROWS * ROW_H - BH
        p = clamp(off / total); h = 50
        rra(ps, (BW - 9, 120 + p * (BH - 160 - h), BW - 4, 120 + p * (BH - 160 - h) + h), 3, (0, 0, 0, 110))
    # status bar (+ highlight around the clock when tapped)
    hl = 0.0
    if k["tap"] - 0.6 <= t < k["jump"] + 0.7: hl = clamp(1 - abs(t - k["tap"]) / 0.7) * 0.6 + 0.4
    status_bar(ps, ImageDraw.Draw(ps), hl if k["tap"] - 0.6 <= t < k["jump"] + 0.7 else 0)
    # finger
    fp = None
    for a in k["ups"]:
        if a - 0.1 <= t < a + 0.45:
            q = ease_out((t - a) / 0.4); fp = (250, 560 - 300 * q)
    for a in k["downs"]:
        if a - 0.1 <= t < a + 0.4:
            q = ease_out((t - a) / 0.35); fp = (250, 300 + 200 * q)
    if k["tap"] - 0.45 <= t < k["tap"] + 0.3:
        q = ease_out((t - (k["tap"] - 0.45)) / 0.4); fp = (250 + (66 - 250) * q, 420 + (38 - 420) * q)
    if fp:
        fx, fy = fp
        if abs(t - k["tap"]) < 0.3:
            r = 30 + 60 * clamp((t - k["tap"]) / 0.3)
            fade(ps, 1 - clamp((t - k["tap"]) / 0.3), lambda l: ImageDraw.Draw(l).ellipse((fx - r, fy - r, fx + r, fy + r), outline=(255, 159, 10, 255), width=5))
        fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((fx - 30, fy - 30, fx + 30, fy + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))
    return ps

def SCREEN(t, T): return screen(t, times(T))

def draw_body(c, t, T):
    k = times(T)
    big_phone(c, screen(t, k))
    if t < T.at["b3"]:
        telop(c, t, T.body, [("戻るのにスクロール連打…", WHITE)], y0=400, size=84)
    elif t < T.at["b4"]:
        telop(c, t, T.at["b3"], [("時計のあたりをタップ", YEL)], y0=400, size=90)
    else:
        telop(c, t, T.at["b4"], [("一瞬で一番上へ！", YEL)], y0=400, size=96)

def draw_hook_art(ly, t):
    x0, y0 = 420, 1150
    rr(ly, (x0, y0, x0 + 240, y0 + 300), 28, (245, 245, 248), outline=(90, 90, 100), width=3)
    q = (t * 0.8) % 1
    d = ImageDraw.Draw(ly)
    for i in range(5):
        y = y0 + 40 + ((i * 56 + 280 * (1 - ease_inout(q))) % 260)
        d.rounded_rectangle((x0 + 20, y, x0 + 220, y + 36), 8, fill=(220, 220, 228))

def sfx(T):
    k = times(T)
    return [("whoosh", a) for a in k["ups"]] + [("click", a) for a in k["downs"]] + [("click", k["tap"]), ("whoosh", k["jump"]),
                                                                                       ("ding", k["jump"] + 0.45)]

def stills(T):
    k = times(T)
    return [k["ups"][-1] + 0.3, k["downs"][2] + 0.2, k["tap"], k["jump"] + 0.2, k["jump"] + 1.0]
