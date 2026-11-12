# 11/15 12:00 60秒3選フォーマットの1本目（format_test）：今すぐ見直したいiPhoneの危険設定3つ（v3・画面録画風・疑問型）
from PIL import Image, ImageDraw
from shortlib import *

SERIES = dict(key="w20261109_second", title="iPhone隠し神機能", spoken="iPhone隠し、かみ機能",
              hook_split=("iPhone", "隠し神機能"), total=5, offset=5)
TITLE = "このiPhoneの設定、オンのままだと危ないかも… #Shorts"
NUM, SLUG = 4, "danger3"
NEXT = "メモで書類スキャン"
SCREEN_CROP = (0, 40, 400, 760)
DURATION, END_CARD = 64.0, False
TAGS = {"length": "60秒3選", "layout": "画面録画風", "hook_type": "疑問型", "title_type": "…止め", "topic_kind": "危険設定"}
LAYOUT, FOCUS_Y, CAPTION_Y = "rec", 400, 1260
HOOK = "この設定\n{オンのまま}だと危ない？"
HOOK_SPOKEN = "このiPhoneの設定、オンのままだと危ないって知ってた？今すぐ3つ見直して！"
TELOPS = [("b1", "1つ目\n[利用頻度の高い場所]"), ("b2", "行った場所が\n{自動で記録}されてる"),
          ("b3", "位置情報サービス →\n[システムサービス]"), ("b4", "2つ目\n[AirDrop]"),
          ("b5", "{すべての人}だと\n知らない人から届く"), ("b6", "一般 → AirDrop →\n[連絡先のみ]"),
          ("b7", "3つ目\n[ロック中の操作]"), ("b8", "盗まれても\n{機内モード}にさせない"),
          ("b9", "Face IDとパスコード →\n[コントロールセンター]")]
ACTIONS = [("b1", "b2", "利用頻度の高い場所"), ("b2", "b3", "行った場所と回数が残る"),
           ("b3", "b4", "プライバシー → 位置情報 → システム"), ("b4", "b5", "AirDropの受信設定"),
           ("b5", "b6", "知らない人から写真が届く"), ("b6", "b7", "連絡先のみをタップ"),
           ("b7", "b8", "ロック中にアクセスを許可"), ("b8", "b9", "ロック画面から機内モード"),
           ("b9", "cta", "コントロールセンターをオフ")]
BODY = [
    ("b1", "1つ目、利用頻度の高い場所。", 0.4),
    ("b2", "よく行く場所と回数が、iPhoneに自動で記録されています。自宅や会社、何回行ったかまで残っています。", 0.5),
    ("b3", "プライバシーとセキュリティ、位置情報サービス、システムサービスから、オフにできます。", 0.7),
    ("b4", "2つ目、エアドロップ。", 0.4),
    ("b5", "すべての人にしていると、電車などで、知らない人から画像が届くことがあります。ニュースにもなった、いたずらです。", 0.5),
    ("b6", "一般の、エアドロップで、連絡先のみにしておきましょう。すべての人は、必要な時だけ、10分間使えます。", 0.7),
    ("b7", "3つ目が一番大事。ロック中のコントロールセンター。", 0.4),
    ("b8", "このままだと、盗まれた時に、ロック画面から機内モードにされてしまいます。そうなると、探すアプリで追いにくくなります。", 0.5),
    ("b9", "フェイスIDとパスコードの、ロック中にアクセスを許可で、コントロールセンターをオフに。これで、ロック中は勝手に操作されません。", 0.0),
]
BODY_HOLD = 0.6
CTA = dict(lines=[("今すぐ", WHITE, 110), ("3つ見直そう！", YEL, 120)], spoken="フォローすると、毎日1つ、iPhoneの設定を紹介するよ！",
           chip="フォローで毎日1つ")

BW, BH = 400, 860

def finger(ps, x, y):
    fade(ps, 1.0, lambda l: ImageDraw.Draw(l).ellipse((x - 30, y - 30, x + 30, y + 30), fill=(255, 255, 255, 150), outline=(80, 80, 90, 200), width=3))

def page(back, title, crumb=None):
    ps = Image.new("RGBA", (BW, BH), (242, 242, 247, 255))
    txt(ps, (56, 36), "9:41", 22, INK, anchor="lm")
    txt(ps, (24, 84), "‹ " + back, 18, BLUE, bold=False, anchor="lm")
    txt(ps, (24, 128), title, 28 if len(title) > 8 else 32, INK, anchor="lm")
    if crumb: txt(ps, (24, 164), crumb, 13, GRAY, bold=False, anchor="lm")
    return ps

def hi_row(ps, y, h, on):
    rr(ps, (16, y, BW - 16, y + h), 12, (255, 236, 150) if on else WHITE)

# ---------------------------------------------------------------- 1) significant locations
def locations(t, T):
    off_at = T.at["b3"] + 2.6
    off = t >= off_at
    ps = page("システムサービス", "利用頻度の高い場所", "プライバシーとセキュリティ › 位置情報サービス › システムサービス")
    hi_row(ps, 186, 62, T.at["b3"] + 1.8 <= t)
    txt(ps, (34, 217), "利用頻度の高い場所", 19, INK, bold=True, anchor="lm")
    toggle(ps, BW - 86, 200, not off)
    if off_at - 0.35 <= t < off_at + 0.15: finger(ps, BW - 60, 217)
    txt(ps, (30, 272), "履歴", 15, GRAY, bold=False, anchor="lm")
    places = [("自宅", "128回"), ("会社", "96回"), ("駅前カフェ", "23回"), ("ジム", "11回")]
    for i, (nm, n) in enumerate(places):
        y = 290 + i * 66
        rr(ps, (16, y, BW - 16, y + 58), 12, WHITE)
        d = ImageDraw.Draw(ps)
        d.ellipse((32, y + 17, 56, y + 41), fill=(200, 200, 205) if off else (255, 59, 48))
        txt(ps, (70, y + 29), nm, 18, GRAY if off else INK, bold=False, anchor="lm")
        txt(ps, (BW - 34, y + 29), "—" if off else n, 16, GRAY, bold=False, anchor="rm")
    if T.at["b2"] <= t < T.at["b3"]:
        p = clamp((t - T.at["b2"]) / 0.4)
        rra(ps, (28, 284, BW - 28, 556), 16, (255, 59, 48, 0), outline=(255, 59, 48, int(255 * p)), width=5)
    if off:
        rra(ps, (60, 640, BW - 60, 696), 28, (52, 199, 89, 235))
        txt(ps, (BW / 2, 668), "記録をオフにした！", 18, WHITE, anchor="mm")
    return ps

# ---------------------------------------------------------------- 2) AirDrop
def airdrop(t, T):
    pick = T.at["b6"] + 2.2
    ps = page("一般", "AirDrop")
    opts = ["受信しない", "連絡先のみ", "すべての人（10分間）"]
    sel = 1 if t >= pick else 2
    for i, o in enumerate(opts):
        y = 186 + i * 66
        hi_row(ps, y, 58, (i == 1 and t >= pick - 0.3) or (i == 2 and T.at["b5"] <= t < T.at["b6"]))
        txt(ps, (34, y + 29), o, 19, INK, bold=i == sel, anchor="lm")
        if i == sel: check(ps, BW - 64, y + 17, 22, BLUE, 4)
    if pick - 0.35 <= t < pick + 0.15: finger(ps, BW / 2, 186 + 66 + 29)
    if T.at["b5"] + 0.4 <= t < T.at["b6"]:
        p = ease_out((t - T.at["b5"] - 0.4) / 0.35)
        y0 = int(210 - 30 * (1 - p))
        rra(ps, (24, y0, BW - 24, y0 + 150), 22, (40, 40, 46, int(252 * p)))
        if p > 0.5:
            txt(ps, (BW / 2, y0 + 34), "AirDrop", 18, WHITE, anchor="mm")
            txt(ps, (BW / 2, y0 + 70), "知らない人が写真を", 16, (220, 220, 225), bold=False, anchor="mm")
            txt(ps, (BW / 2, y0 + 96), "共有しようとしています", 16, (220, 220, 225), bold=False, anchor="mm")
            txt(ps, (BW / 2 - 70, y0 + 128), "辞退", 16, BLUE, anchor="mm"); txt(ps, (BW / 2 + 70, y0 + 128), "受け入れる", 16, BLUE, anchor="mm")
    if t >= pick + 0.2:
        rra(ps, (60, 640, BW - 60, 696), 28, (52, 199, 89, 235))
        txt(ps, (BW / 2, 668), "連絡先のみ にした！", 18, WHITE, anchor="mm")
    return ps

# ---------------------------------------------------------------- 3) lock screen access
def lock_cc(t, T):
    ps = grad(BW, BH, (20, 24, 60), (60, 30, 90))
    txt(ps, (BW / 2, 140), "9:41", 72, WHITE, anchor="mm")
    p = ease_out((t - T.at["b8"] - 0.3) / 0.5)
    if p > 0:
        rra(ps, (24, 220 - int(40 * (1 - p)), BW - 24, 420), 30, (50, 50, 60, int(230 * p)))
        on = t >= T.at["b8"] + 1.6
        cx, cy = 90, 300
        ImageDraw.Draw(ps).ellipse((cx - 40, cy - 40, cx + 40, cy + 40), fill=(255, 159, 10) if on else (90, 90, 100))
        txt(ps, (cx, cy), "機内", 22, WHITE, anchor="mm")
        for i, c in enumerate([(52, 199, 89), (10, 132, 255), (10, 132, 255)]):
            x = 190 + i * 70; ImageDraw.Draw(ps).ellipse((x - 26, 274, x + 26, 326), fill=(90, 90, 100) if on else c)
        if T.at["b8"] + 1.25 <= t < T.at["b8"] + 1.7: finger(ps, cx, cy)
        if on:
            rra(ps, (40, 640, BW - 40, 696), 28, (255, 59, 48, 235))
            txt(ps, (BW / 2, 668), "ロックしたまま機内モードに…", 18, WHITE, anchor="mm")
    return ps

def faceid(t, T):
    off_at = T.at["b9"] + 3.0
    ps = page("設定", "Face IDとパスコード")
    txt(ps, (30, 172), "ロック中にアクセスを許可", 15, GRAY, bold=False, anchor="lm")
    rows = ["今日の表示と検索", "通知センター", "コントロールセンター", "Siri", "USBアクセサリ"]
    for i, r in enumerate(rows):
        y = 190 + i * 60
        hi_row(ps, y, 54, i == 2 and t >= T.at["b9"] + 1.5)
        txt(ps, (34, y + 27), r, 18, INK, bold=i == 2, anchor="lm")
        toggle(ps, BW - 86, y + 9, not (i == 2 and t >= off_at) and i != 4)
    if off_at - 0.35 <= t < off_at + 0.15: finger(ps, BW - 60, 190 + 2 * 60 + 27)
    if t >= off_at + 0.2:
        rra(ps, (60, 640, BW - 60, 696), 28, (52, 199, 89, 235))
        txt(ps, (BW / 2, 668), "ロック中は開けない！", 18, WHITE, anchor="mm")
    return ps

def SCREEN(t, T):
    if t >= T.at["b9"]: return faceid(t, T)
    if t >= T.at["b7"]: return lock_cc(t, T)
    if t >= T.at["b4"]: return airdrop(t, T)
    return locations(t, T)

def draw_body(c, t, T): pass

def draw_hook_art(ly, t): pass

def sfx(T):
    a = T.at
    return [("pop", a["b1"]), ("ding", a["b2"]), ("click", a["b3"] + 2.6), ("pop", a["b4"]), ("ding", a["b5"] + 0.4),
            ("click", a["b6"] + 2.2), ("pop", a["b7"]), ("click", a["b8"] + 1.6), ("click", a["b9"] + 3.0)]

def stills(T):
    a = T.at
    return [1.0, a["b2"] + 0.8, a["b3"] + 3.0, a["b5"] + 1.2, a["b6"] + 2.6, a["b8"] + 2.0, a["b9"] + 3.3, a["cta"] + 1.0]
