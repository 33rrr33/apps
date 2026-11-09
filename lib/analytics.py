"""Channel performance snapshot (YouTube Data API v3 public statistics) -> data/stats.json.

    python3 lib/analytics.py fetch     # all uploads: views/likes/comments, publish time, length, our metadata
    python3 lib/analytics.py report    # quick text summary by group

Joins each video with what we know about it from state.json (slot, series, layout version, hook) so the
loop can compare groups: publish slot (06:00 / 17:30 / other), weekday, theme, Mac vs iPhone, v3 layout or not,
Shorts vs long. Views are also normalised per day since publish (first 7 days capped) to compare young and old videos.
YouTube Analytics (impressions, CTR, retention, traffic source) needs the yt-analytics.readonly scope, which the
current token does not have; only public counters are used here.
"""
import datetime as dt, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ytupload as Y

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JST = dt.timezone(dt.timedelta(hours=9))

def iso_dur(s):
    m = re.fullmatch(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?", s or "PT0S")
    if not m: return 0                                   # e.g. a video still processing
    d, h, mi, se = (int(x) if x else 0 for x in m.groups()); return d * 86400 + h * 3600 + mi * 60 + se

def our_meta():
    st = json.load(open(os.path.join(ROOT, "state.json")))
    meta = {}
    for k, v in st.get("v2", {}).get("slots", {}).items():
        if v.get("id"): meta[v["id"]] = dict(slot=k, series_key=v.get("series_key"), theme=v.get("theme"), kind=v.get("kind"),
                                             num=v.get("num"), layout="v3" if v.get("kind") == "short" else "long", episode=v.get("episode"))
    return meta

def hook_of(episode):
    if not episode: return None
    p = os.path.join(ROOT, episode)
    if not os.path.exists(p): return None
    m = re.search(r'^HOOK = "(.*)"', open(p).read(), re.M)
    return m.group(1).replace("\\n", " / ") if m else None

def fetch():
    tok = Y.token(); A = Y.auth(tok)
    _, _, r = Y.http("GET", f"{Y.API}/channels?part=contentDetails,statistics,snippet&mine=true", headers=A)
    ch = r["items"][0]; up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, page = [], ""
    while True:
        _, _, r = Y.http("GET", f"{Y.API}/playlistItems?part=contentDetails&maxResults=50&playlistId={up}{page}", headers=A)
        ids += [i["contentDetails"]["videoId"] for i in r.get("items", [])]
        if not r.get("nextPageToken"): break
        page = "&pageToken=" + r["nextPageToken"]
    vids = []
    for i in range(0, len(ids), 50):
        _, _, r = Y.http("GET", f"{Y.API}/videos?part=snippet,statistics,contentDetails,status&id={','.join(ids[i:i+50])}", headers=A)
        vids += r.get("items", [])
    meta = our_meta(); now = dt.datetime.now(JST); rows = []
    for v in vids:
        st, sn = v["status"], v["snippet"]
        pub = st.get("publishAt") if st["privacyStatus"] != "public" else sn["publishedAt"]
        pub = dt.datetime.fromisoformat((pub or sn["publishedAt"]).replace("Z", "+00:00")).astimezone(JST)
        m = meta.get(v["id"], {})
        title = sn["title"]; secs = iso_dur(v["contentDetails"].get("duration"))
        age_h = max(0.0, (now - pub).total_seconds() / 3600)
        views = int(v["statistics"].get("viewCount", 0))
        rows.append(dict(
            id=v["id"], title=title, privacy=st["privacyStatus"], published=pub.isoformat(), weekday="月火水木金土日"[pub.weekday()],
            hhmm=pub.strftime("%H:%M"), seconds=secs, kind=("long" if secs > 70 else "short"),
            views=views, likes=int(v["statistics"].get("likeCount", 0)), comments=int(v["statistics"].get("commentCount", 0)),
            age_hours=round(age_h, 1), views_per_day=round(views / max(1.0, min(age_h, 24 * 7) / 24), 1),
            topic_device=("Mac" if ("Mac" in title and "iPhone" not in title) or "Macの" in title else "iPhone"),
            series=m.get("theme") or re.sub(r"[①-⑩].*$", "", title.replace("#Shorts", "")).strip(),
            layout=m.get("layout") or ("legacy"), hook=hook_of(m.get("episode")), slot=m.get("slot")))
    rows.sort(key=lambda x: x["published"])
    add_analytics(tok, rows, now)
    out = dict(fetched=now.isoformat(), channel=dict(title=ch["snippet"]["title"], subscribers=int(ch["statistics"].get("subscriberCount", 0)),
                                                    views=int(ch["statistics"].get("viewCount", 0)), videos=int(ch["statistics"].get("videoCount", 0))),
               videos=rows)
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    json.dump(out, open(os.path.join(ROOT, "data", "stats.json"), "w"), ensure_ascii=False, indent=1)
    # history of snapshots (for growth curves)
    hp = os.path.join(ROOT, "data", "history.jsonl")
    with open(hp, "a") as f:
        f.write(json.dumps(dict(t=now.isoformat(), ch=out["channel"], v={r["id"]: r["views"] for r in rows if r["privacy"] == "public"})) + "\n")
    print(f"{len(rows)} videos, {out['channel']}")
    return out

def add_analytics(tok, rows, now):
    """YouTube Analytics (needs yt-analytics.readonly on the token). Adds retention etc. per video; skipped quietly if not allowed."""
    pub = [r for r in rows if r["privacy"] == "public"]
    if not pub: return
    start = min(r["published"][:10] for r in pub); end = now.strftime("%Y-%m-%d")
    metrics = "views,averageViewDuration,averageViewPercentage,likes,subscribersGained,shares"
    for i in range(0, len(pub), 40):
        ids = ",".join(r["id"] for r in pub[i:i + 40])
        url = (f"https://youtubeanalytics.googleapis.com/v2/reports?ids=channel==MINE&startDate={start}&endDate={end}"
               f"&metrics={metrics}&dimensions=video&filters=video=={ids}&maxResults=200")
        try:
            _, _, r = Y.http("GET", url, headers=Y.auth(tok))
        except SystemExit as e:
            print("analytics skipped:", str(e)[:120]); return
        cols = [c["name"] for c in r.get("columnHeaders", [])]
        for row in r.get("rows", []):
            d = dict(zip(cols, row)); v = next((x for x in pub if x["id"] == d["video"]), None)
            if v: v.update(avg_view_pct=d.get("averageViewPercentage"), avg_view_sec=d.get("averageViewDuration"),
                           subs_gained=d.get("subscribersGained"), shares=d.get("shares"))
    print("analytics added")

def report():
    d = json.load(open(os.path.join(ROOT, "data", "stats.json")))
    pub = [r for r in d["videos"] if r["privacy"] == "public"]
    for r in pub:
        print(f"{r['published'][:16]} {r['weekday']} {r['kind']:5} {r['views']:6} views  {r['likes']:3}♥ {r['comments']:2}💬  {r['layout']:6}  {r['title'][:40]}")

if __name__ == "__main__":
    {"fetch": fetch, "report": report}[sys.argv[1] if len(sys.argv) > 1 else "fetch"]()
