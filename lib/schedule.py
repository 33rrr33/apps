"""Weekly slot calendar for the v2 pipeline (iPhone-only, two 5-part series a week, 24h-ahead scheduling).

Slots (JST publish times), from config/themes.json start_monday:
    Mon 06:00 前半① / Mon 17:30 前半② / Tue 06:00 前半③ / Tue 17:30 前半④ / Wed 06:00 前半⑤
    Wed 17:30 後半① / Thu 06:00 後半② / Thu 17:30 後半③ / Fri 06:00 後半④ / Fri 17:30 後半⑤
    Sat 17:30 前半まとめ長尺（約5分） / Sun 17:30 後半まとめ長尺（約5分）  ※長尺は必ず17:30（LONG_TIME）
A trigger at 06:00 or 17:30 on day D makes the slot at the same time on D+1 (no slot → skip).
Publish dates before start_monday follow the old state.json "schedule" (legacy).

Usage:
    python3 lib/schedule.py next morning|evening [--date YYYY-MM-DD]   # what this trigger must make (JSON)
    python3 lib/schedule.py slot 2026-11-02T06:00                       # one slot (JSON)
    python3 lib/schedule.py plan [days]                                 # calendar from today
"""
import datetime as dt, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JST = dt.timezone(dt.timedelta(hours=9))
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳"
DAYS = "月火水木金土日"
# Weekend longs are ALWAYS published at 17:30 JST (user rule 2026-10-31; 06:00 is forbidden for longs).
LONG_TIME = "17:30"
# weekday -> [(time, half, num)] ; num 0 = weekend long
WEEK = {
    0: [("06:00", "first", 1), ("17:30", "first", 2)],
    1: [("06:00", "first", 3), ("17:30", "first", 4)],
    2: [("06:00", "first", 5), ("17:30", "second", 1)],
    3: [("06:00", "second", 2), ("17:30", "second", 3)],
    4: [("06:00", "second", 4), ("17:30", "second", 5)],
    5: [(LONG_TIME, "first", 0)],
    6: [(LONG_TIME, "second", 0)],
}
LONG_TITLE = {"first": "【保存版】今すぐ使える！{t}5選まとめ", "second": "【決定版】知らなきゃ損する！{t}5選まとめ"}
HALF_JA = {"first": "前半", "second": "後半"}

def themes(): return json.load(open(os.path.join(ROOT, "config", "themes.json")))

def start_monday(): return dt.date.fromisoformat(themes()["start_monday"])

def week_info(day):
    """Series and topics for the week that contains `day` (dates before start_monday -> None).
    2026-10-31: two fixed iPhone series every week (first = iPhone爆速神操作, second = iPhone隠し神機能),
    topics advance five per week."""
    th = themes(); m0 = start_monday()
    monday = day - dt.timedelta(days=day.weekday())
    if monday < m0: return None
    w = (monday - m0).days // 7
    out = {"monday": monday.isoformat(), "week_index": w}
    for half in ("first", "second"):
        t = th["series"][half]
        topics = t["topics"][w * 5: w * 5 + 5]
        out[half] = dict(theme_id=t["id"], title=t["title"], spoken=t["spoken"], hook_split=t["hook_split"],
                         topics=topics if len(topics) == 5 else None, cycle=w,
                         series_key=f"w{monday.strftime('%Y%m%d')}_{half}",
                         episode_dir=f"episodes/w{monday.strftime('%Y%m%d')}_{half}",
                         storage_dir=f"storage/weekly_{half}_half",
                         long_title=LONG_TITLE[half].format(t=t["title"]))
    return out

# 2026-11-01 (user): the weekend long comes FIRST, so the following week's Shorts can link it as their related video.
# From AHEAD_FROM on, Sat 17:30 = next week's 前半 long, Sun 17:30 = next week's 後半 long (made from the 60s parts of
# next week's episodes, which are therefore written on Fri/Sat; the weekday runs then only render/upload the Shorts).
# The week of 2026-11-09 has no long of its own: its Shorts link the 11/7・11/8 longs.
AHEAD_FROM = dt.date(2026, 11, 14)

def related_long(half, monday):
    """(publish time, title) of the long the Shorts of this half-week should use as their related video:
    the weekend long published just before the week (from the 11/9 week on; the 11/9 week uses 11/7・11/8),
    or, for the 11/2 week, its own weekend long."""
    m = dt.date.fromisoformat(monday) if isinstance(monday, str) else monday
    off = 2 if half == "first" else 1
    day = m - dt.timedelta(days=off) if m >= AHEAD_FROM - dt.timedelta(days=5) else m + dt.timedelta(days=7 - off)
    return f"{day.isoformat()}T{LONG_TIME}", week_info(m)[half]["long_title"]

# ---------------------------------------------------------------------------------------------------------------
# v3 calendar (2026-11-10, PdM redesign): ONE Short a day, every day, at a rotating time (time A/B test),
# hook type A/B-tested on a Latin square, series run back to back (5 parts each, alternating 隠し神機能 / 爆速神操作),
# ONE long a week (Sunday 17:30) compiling the last finished series. Old weekday 2-a-day slots stop on 11/11.
V3_START = dt.date(2026, 11, 12)
V3_TIMES = ["12:00", "19:00", "06:00"]                  # rotation; pdca.py judges the winner, strategy.json can pin one
HOOK_TYPES = ["煽り型", "疑問型", "即効型"]               # 煽り：〇〇な人全員損してます / 疑問：これ知ってた？ / 即効：3秒でできる
LONG_TIME_V3 = "17:30"

def v3_strategy():
    p = os.path.join(ROOT, "config", "strategy.json")
    return json.load(open(p)) if os.path.exists(p) else {}

def v3_time(day):
    pin = v3_strategy().get("slot_pin")                 # set by the weekly Act once a time wins
    if pin: return pin
    return V3_TIMES[(day - V3_START).days % len(V3_TIMES)]

def v3_hook(day):
    pin = v3_strategy().get("hook_pin")
    if pin: return pin
    i = (day - V3_START).days
    return HOOK_TYPES[(i + i // 3) % 3]                   # Latin square: each hook meets each time slot

def v3_block(i):
    """block i of 5 Shorts: (half, topic offset, series_key)."""
    half = "second" if i % 2 == 0 else "first"
    off = 5 * ((i + 1) // 2 + 1)
    start = V3_START + dt.timedelta(days=5 * i)
    key = "w20261109_second" if i == 0 else f"b{start.strftime('%Y%m%d')}_{half}"
    return half, off, key, start

def v3_series(half, off, key):
    th = themes()["series"][half]
    topics = th["topics"][off:off + 5]
    return dict(title=th["title"], spoken=th["spoken"], hook_split=th["hook_split"], topics=topics if len(topics) == 5 else None,
                series_key=key, episode_dir=f"episodes/{key}", storage_dir=f"storage/{key}", long_title=LONG_TITLE[half].format(t=th["title"]))

def v3_latest_long(before):
    """(publish, title, id) of the newest long scheduled before `before` (from state.json)."""
    st = json.load(open(os.path.join(ROOT, "state.json")))
    best = None
    for k, v in st.get("v2", {}).get("slots", {}).items():
        if v.get("kind") == "long" and v.get("id") and k < before.strftime("%Y-%m-%dT%H:%M"):
            if not best or k > best[0]: best = (k, v.get("title"), v.get("id"))
    return best

def v3_slot(publish):
    d = publish.date(); hm = publish.strftime("%H:%M")
    if d.weekday() == 6 and hm == LONG_TIME_V3 and not v3_strategy().get("long_paused"):   # Sunday long (paused 2026-11-10)
        i = (d - V3_START).days // 5 - 1
        while i >= 0 and V3_START + dt.timedelta(days=5 * i + 4) >= d: i -= 1
        if i < 0: return None
        half, off, key, _ = v3_block(i); h = v3_series(half, off, key)
        eps = [f"{h['episode_dir']}/ep{n + 1:02d}_{tp['slug']}.py" for n, tp in enumerate(h["topics"] or [])]
        return dict(kind="long", publish_at=publish.strftime("%Y-%m-%dT%H:%M:00+09:00"), half=half, half_ja=HALF_JA[half],
                    theme=h["title"], theme_spoken=h["spoken"], series_key=key, week=key, ahead=False, notify_subscribers=True,
                    title=h["long_title"], parts=[f"{h['storage_dir']}/part_{n}.mp4" for n in range(1, 6)],
                    episode_dir=h["episode_dir"], episodes=eps, topics=h["topics"])
    if hm != v3_time(d): return None
    i = (d - V3_START).days
    half, off, key, _ = v3_block(i // 5); h = v3_series(half, off, key); num = i % 5 + 1
    tp = h["topics"][num - 1] if h["topics"] else None
    rl = v3_latest_long(publish)
    ft = v3_strategy().get("format_test") or {}
    fmt = None
    if ft and d.isoformat() >= ft.get("since", "9999") and not v3_strategy().get("format_pin"):
        fmt = "60秒3選" if d.day % 2 else "13秒1ネタ"
    elif v3_strategy().get("format_pin"): fmt = v3_strategy()["format_pin"]
    return dict(kind="short", format=fmt, publish_at=publish.strftime("%Y-%m-%dT%H:%M:00+09:00"), half=half, half_ja=HALF_JA[half],
                theme=h["title"], theme_spoken=h["spoken"], series_key=key, week=key, num=num, notify_subscribers=False,
                title=f"{h['title']}{CIRCLED[off + num - 1]} #Shorts", disp_num=off + num, num_offset=off,
                hook_split=h["hook_split"], hook_type=v3_hook(d),
                topic=tp, episode=f"{h['episode_dir']}/ep{num:02d}_{tp['slug']}.py" if tp else None,
                part=f"{h['storage_dir']}/part_{num}.mp4", related_long=[rl[0], rl[1]] if rl else None,
                next_topic=(h["topics"][num]["topic"] if h["topics"] and num < 5 else None))

def upcoming(day, days=2):
    """All v3 slots in the next `days` days after `day` (for the daily production run)."""
    out = []
    for k in range(1, days + 1):
        d = day + dt.timedelta(days=k)
        for hm in sorted(set(V3_TIMES + [LONG_TIME_V3] + ([v3_strategy().get("slot_pin")] if v3_strategy().get("slot_pin") else []))):
            s = slot(dt.datetime.combine(d, dt.time.fromisoformat(hm), JST))
            if s and s.get("kind") in ("short", "long"): out.append(s)
    return out

def slot(publish):
    """publish: aware datetime (JST). Returns the slot description or None."""
    d = publish.date(); hm = publish.strftime("%H:%M")
    if d >= V3_START: return v3_slot(publish)
    if publish.strftime("%Y-%m-%dT%H:%M") in ("2026-11-11T17:30",): return None   # moved to 2026-11-12 12:00 (v3)
    if d < start_monday():
        st = json.load(open(os.path.join(ROOT, "state.json")))
        legacy = st.get("schedule", {}).get(d.isoformat())
        return {"kind": "legacy", "publish_at": publish.isoformat(), "legacy": legacy} if legacy and hm == legacy.get("time", st.get("publish_time", "17:30")) else None
    for t, half, num in WEEK[d.weekday()]:
        if t != hm: continue
        ahead = num == 0 and d >= AHEAD_FROM
        wk = week_info(d + dt.timedelta(days=2) if ahead else d); h = wk[half]
        base = dict(publish_at=publish.strftime("%Y-%m-%dT%H:%M:00+09:00"), half=half, half_ja=HALF_JA[half],
                    week=wk["monday"], theme=h["title"], theme_spoken=h["spoken"], series_key=h["series_key"])
        if num == 0:
            assert t == LONG_TIME, "weekend longs must be published at 17:30"
            eps = [f"{h['episode_dir']}/ep{i + 1:02d}_{tp['slug']}.py" for i, tp in enumerate(h["topics"] or [])]
            return dict(base, kind="long", ahead=ahead, notify_subscribers=True, title=h["long_title"],
                        parts=[f"{h['storage_dir']}/part_{i}.mp4" for i in range(1, 6)], episode_dir=h["episode_dir"],
                        episodes=eps, topics=h["topics"],
                        note=("先出し長尺：来週の①〜⑤のエピソード（ショート＋PART）をここで全部書き、パートから長尺を作る。"
                              "ショートは平日の各実行が、このエピソードを render して予約する。") if ahead else None)
        tp = h["topics"][num - 1] if h["topics"] else None
        return dict(base, kind="short", num=num, notify_subscribers=False,
                    title=f"{h['title']}{CIRCLED[num - 1]} #Shorts", hook_split=h["hook_split"],
                    topic=tp, episode=f"{h['episode_dir']}/ep{num:02d}_{tp['slug']}.py" if tp else None,
                    part=f"{h['storage_dir']}/part_{num}.mp4", related_long=related_long(half, wk["monday"]),
                    next_topic=(h["topics"][num]["topic"] if h["topics"] and num < 5 else None))
    return None

def next_for(trigger, day):
    hm = {"morning": "06:00", "evening": "17:30"}[trigger]
    target = dt.datetime.combine(day + dt.timedelta(days=1), dt.time.fromisoformat(hm), JST)
    s = slot(target)
    return s or {"kind": "skip", "publish_at": target.isoformat(), "reason": "この時間の配信枠なし"}

def today(): return dt.datetime.now(JST).date()

if __name__ == "__main__":
    a = sys.argv[1:] or ["plan"]
    if a[0] == "next":
        day = dt.date.fromisoformat(a[a.index("--date") + 1]) if "--date" in a else today()
        print(json.dumps(next_for(a[1], day), ensure_ascii=False, indent=1))
    elif a[0] == "slot":
        print(json.dumps(slot(dt.datetime.fromisoformat(a[1]).replace(tzinfo=JST)), ensure_ascii=False, indent=1))
    elif a[0] == "upcoming":
        print(json.dumps(upcoming(today(), int(a[1]) if len(a) > 1 else 2), ensure_ascii=False, indent=1))
    elif a[0] == "plan":
        n = int(a[1]) if len(a) > 1 else 21
        for i in range(n):
            d = today() + dt.timedelta(days=i)
            for hm in ("06:00", "12:00", "17:30", "19:00"):
                s = slot(dt.datetime.combine(d, dt.time.fromisoformat(hm), JST))
                if not s: continue
                if s["kind"] == "legacy": label = f"(旧) {s['legacy']}"
                elif s["kind"] == "long": label = s["title"]
                else: label = f"{s['title']}  [{s.get('hook_type', '')}] {s['topic']['topic'][:24] if s['topic'] else '（ネタ未定）'}"
                print(f"{d} ({DAYS[d.weekday()]}) {hm}  {label}")
