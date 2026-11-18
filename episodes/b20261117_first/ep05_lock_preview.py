# 11/21 06:00 28秒2ネタ（危険設定・plan s1）ロック画面でLINEの中身が丸見え（画面録画風・損失回避）
# 1フレーム目＝本物そっくりのロック画面にLINEの中身が並ぶ（11/18 スワイプ率ルール）
# 根拠：iOS 設定→通知→プレビューを表示（常に／ロックされていないときのみ／しない）
#       LINE ホーム→設定→通知→「メッセージ内容表示」オフで「新着メッセージがあります。」表示
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="b20261117_first", title="iPhone爆速神操作", spoken="iPhone爆速、かみ操作",
              hook_split=("iPhone", "爆速神操作"), total=5, offset=10)
TITLE = "ロック画面でLINEの中身、丸見えになってない？ #Shorts"
NUM, SLUG = 5, "lock_preview"
NEXT = "次も守る設定"
SCREEN_CROP = (0, 40, 400, 760)
DURATION, END_CARD = 24.0, False
TAGS = {"length": "28秒2ネタ", "layout": "画面録画風", "hook_type": "煽り型", "title_type": "問いかけ", "topic_kind": "危険設定",
        "first_frame": "本物の画面＋自分ごと"}
LAYOUT, FOCUS_Y, CAPTION_Y = "rec", 400, 1260
HOOK = "ロック画面で\n{LINEが丸見え}…"
HOOK_SPOKEN = "ロック画面に、LINEの中身が出てる人へ！"
TELOPS = [("b1", "1つ目\n[通知のプレビュー]"), ("b2", "設定 → 通知 →\n[ロックされていないときのみ]"),
          ("b3", "2つ目\n[LINEの通知設定]"), ("b4", "メッセージ内容表示を\n[オフ]")]
ACTIONS = [("b1", "b2", "通りすがりの人にも見える…"), ("b2", "b3", "プレビューを表示をタップ"),
           ("b3", "b4", "LINE → 設定 → 通知"), ("b4", "cta", "「新着メッセージがあります」だけに")]
BODY = [
    ("b1", "1つ目、iPhoneの通知のプレビュー。通りすがりの人にも、中身が見えてます。", 0.2),
    ("b2", "設定の通知で、プレビューを表示を、ロックされていないときのみに。", 0.3),
    ("b3", "2つ目が大事。LINEの中の通知設定。", 0.15),
    ("b4", "メッセージ内容表示をオフにすると、新着メッセージがあります、だけになります。", 0.0),
]
BODY_HOLD = 0.5
CTA = dict(lines=[("丸見えだった人は", WHITE, 96), ("コメントで教えて！", YEL, 100)], spoken="丸見えだった人は、コメントで教えて！",
           chip="家族のiPhoneにも")

BW, BH = 400, 860
LINE_G = (6, 199, 85)
MSGS = [("田中 さくら", "明日の件、絶対に誰にも言わないでね"), ("母", "暗証番号は前と同じだよ"), ("佐藤 課長", "至急、折り返し電話ください")]

def finger(ps, x, y):
    fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((x - 30, y - 30, x + 30, y + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))

def pill(ps, text, col):
    rra(ps, (40, 640, BW - 40, 696), 28, col + (235,))
    txt(ps, (BW / 2, 668), text, 17, WHITE, anchor="mm")

def line_icon(ps, x, y, s=34):
    rr(ps, (x, y, x + s, y + s), 9, LINE_G)
    txt(ps, (x + s / 2, y + s / 2), "LINE", 9, WHITE, anchor="mm")

def card(ps, y, name, body, hi):
    rra(ps, (14, y, BW - 14, y + 70), 18, (255, 255, 255, 215))
    if hi: ImageDraw.Draw(ps).rounded_rectangle((14, y, BW - 14, y + 70), 18, outline=(255, 59, 48), width=4)
    line_icon(ps, 26, y + 18)
    txt(ps, (72, y + 22), name, 15, INK, anchor="lm")
    txt(ps, (BW - 28, y + 22), "今", 13, GRAY, bold=False, anchor="rm")
    txt(ps, (72, y + 48), body, 14, INK, bold=False, anchor="lm")

def lockscreen(t, T, hidden=False):
    a = T.at
    ps = grad(BW, BH, (40, 60, 110), (120, 70, 140))
    txt(ps, (BW / 2, 58), "11月21日 金曜日", 16, WHITE, bold=False, anchor="mm")
    txt(ps, (BW / 2, 112), "6:00", 64, WHITE, anchor="mm")
    for i, (nm, body) in enumerate(MSGS):
        y = 180 + i * 82
        if hidden: card(ps, y, "LINE", "新着メッセージがあります。", False)
        else: card(ps, y, nm, body, t >= a["b1"] - 0.4)
    if not hidden and t >= a["b1"] - 0.4:
        pill(ps, "ロック中でも中身が丸見え…", (255, 59, 48))
    return ps

def preview(t, T):
    a = T.at
    tap, pick = a["b2"] + 0.5, a["b2"] + 1.8
    if t < tap + 0.3:
        ps = page_("設定", "通知")
        rows = [("プレビューを表示", "常に"), ("画面共有", "オフ"), ("Siriからの提案", "")]
        for i, (k, v) in enumerate(rows):
            y = 170 + i * 62
            rr(ps, (16, y, BW - 16, y + 56), 12, (255, 236, 150) if i == 0 and t >= a["b2"] else WHITE)
            txt(ps, (34, y + 28), k, 17, INK, bold=i == 0, anchor="lm")
            txt(ps, (BW - 34, y + 28), v + "  ›", 15, (255, 59, 48) if i == 0 else GRAY, bold=i == 0, anchor="rm")
        if tap - 0.35 <= t < tap + 0.1: finger(ps, BW / 2, 198)
        return ps
    ps = page_("通知", "プレビューを表示")
    opts = ["常に", "ロックされていないときのみ", "しない"]
    sel = 1 if t >= pick else 0
    for i, o in enumerate(opts):
        y = 170 + i * 62
        rr(ps, (16, y, BW - 16, y + 56), 12, (255, 236, 150) if i == 1 and t >= pick - 0.3 else WHITE)
        txt(ps, (34, y + 28), o, 17, INK, bold=i == sel, anchor="lm")
        if i == sel: check(ps, BW - 60, y + 16, 22, BLUE, 4)
    if pick - 0.35 <= t < pick + 0.1: finger(ps, BW / 2, 170 + 62 + 28)
    if t >= pick + 0.3: pill(ps, "ロック中は中身が隠れる", (52, 199, 89))
    return ps

def page_(back, title):
    ps = Image.new("RGBA", (BW, BH), (242, 242, 247, 255))
    txt(ps, (56, 36), "9:41", 22, INK, anchor="lm")
    txt(ps, (24, 84), "‹ " + back, 18, BLUE, bold=False, anchor="lm")
    txt(ps, (24, 128), title, 26, INK, anchor="lm")
    return ps

def line_settings(t, T):
    a = T.at
    off_at, show_at = a["b4"] + 1.6, a["b4"] + 3.0
    if t >= show_at:
        ps = lockscreen(t, T, hidden=True)
        pill(ps, "名前も中身も出ない！", (52, 199, 89))
        return ps
    ps = page_("設定", "通知")
    line_icon(ps, BW - 60, 108, 30)
    rows = [("通知", True), ("メッセージ内容表示", t < off_at), ("サムネイル表示", True)]
    for i, (k, on) in enumerate(rows):
        y = 170 + i * 62
        rr(ps, (16, y, BW - 16, y + 56), 12, (255, 236, 150) if i == 1 and t >= a["b4"] else WHITE)
        txt(ps, (34, y + 28), k, 17, INK, bold=i == 1, anchor="lm")
        toggle(ps, BW - 86, y + 8, on)
    if off_at - 0.35 <= t < off_at + 0.1: finger(ps, BW - 60, 170 + 62 + 28)
    return ps

def SCREEN(t, T):
    a = T.at
    if t >= a["b3"]: return line_settings(t, T)
    if t >= a["b2"]: return preview(t, T)
    return lockscreen(t, T)

def draw_body(c, t, T): pass

def draw_hook_art(ly, t): pass

def sfx(T):
    a = T.at
    return [("ding", a["b1"] - 0.4), ("pop", a["b2"]), ("click", a["b2"] + 0.5), ("click", a["b2"] + 1.8), ("pop", a["b3"]),
            ("click", a["b4"] + 1.6), ("ding", a["b4"] + 3.0)]

def stills(T):
    a = T.at
    return [0.05, 0.8, a["b1"] + 0.5, a["b2"] + 1.0, a["b2"] + 2.4, a["b3"] + 0.8, a["b4"] + 2.0, a["b4"] + 3.4, a["cta"] + 0.8]
