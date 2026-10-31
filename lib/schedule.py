"""Weekly slot calendar for the v2 pipeline (iPhone-only, two 5-part series a week, 24h-ahead scheduling).

Slots (JST publish times), from config/themes.json start_monday:
    Mon 06:00 前半① / Mon 17:30 前半② / Tue 06:00 前半③ / Tue 17:30 前半④ / Wed 06:00 前半⑤
    Wed 17:30 後半① / Thu 06:00 後半② / Thu 17:30 後半③ / Fri 06:00 後半④ / Fri 17:30 後半⑤
    Sat 06:00 前半まとめ長尺（約5分） / Sun 06:00 後半まとめ長尺（約5分）  ※2026-10-30 ユーザー指定で土日は朝6時
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
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩"
DAYS = "月火水木金土日"
# weekday -> [(time, half, num)] ; num 0 = weekend long
WEEK = {
    0: [("06:00", "first", 1), ("17:30", "first", 2)],
    1: [("06:00", "first", 3), ("17:30", "first", 4)],
    2: [("06:00", "first", 5), ("17:30", "second", 1)],
    3: [("06:00", "second", 2), ("17:30", "second", 3)],
    4: [("06:00", "second", 4), ("17:30", "second", 5)],
    5: [("06:00", "first", 0)],
    6: [("06:00", "second", 0)],
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

def slot(publish):
    """publish: aware datetime (JST). Returns the slot description or None."""
    d = publish.date(); hm = publish.strftime("%H:%M")
    if d < start_monday():
        st = json.load(open(os.path.join(ROOT, "state.json")))
        legacy = st.get("schedule", {}).get(d.isoformat())
        return {"kind": "legacy", "publish_at": publish.isoformat(), "legacy": legacy} if legacy and hm == legacy.get("time", st.get("publish_time", "17:30")) else None
    for t, half, num in WEEK[d.weekday()]:
        if t != hm: continue
        wk = week_info(d); h = wk[half]
        base = dict(publish_at=publish.strftime("%Y-%m-%dT%H:%M:00+09:00"), half=half, half_ja=HALF_JA[half],
                    week=wk["monday"], theme=h["title"], theme_spoken=h["spoken"], series_key=h["series_key"])
        if num == 0:
            return dict(base, kind="long", notify_subscribers=True, title=h["long_title"],
                        parts=[f"{h['storage_dir']}/part_{i}.mp4" for i in range(1, 6)], episode_dir=h["episode_dir"])
        tp = h["topics"][num - 1] if h["topics"] else None
        return dict(base, kind="short", num=num, notify_subscribers=False,
                    title=f"{h['title']}{CIRCLED[num - 1]} #Shorts", hook_split=h["hook_split"],
                    topic=tp, episode=f"{h['episode_dir']}/ep{num:02d}_{tp['slug']}.py" if tp else None,
                    part=f"{h['storage_dir']}/part_{num}.mp4",
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
    elif a[0] == "plan":
        n = int(a[1]) if len(a) > 1 else 21
        for i in range(n):
            d = today() + dt.timedelta(days=i)
            for hm in ("06:00", "17:30"):
                s = slot(dt.datetime.combine(d, dt.time.fromisoformat(hm), JST))
                if not s: continue
                if s["kind"] == "legacy": label = f"(旧) {s['legacy']}"
                elif s["kind"] == "long": label = s["title"]
                else: label = f"{s['title']}  {s['topic']['topic'][:28] if s['topic'] else '（ネタ未定）'}"
                print(f"{d} ({DAYS[d.weekday()]}) {hm}  {label}")
