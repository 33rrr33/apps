"""Find recent hits (for 'follow a hit with a related topic within 1-2 days').
usage: hits.py  -> prints recent shorts with views/hour and a HIT flag, from data/stats.json"""
import json, os, datetime as dt, statistics as S
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    d = json.load(open(os.path.join(ROOT, "data", "stats.json")))
    vs = d.get("videos", d); vs = vs if isinstance(vs, list) else list(vs.values())
    now = dt.datetime.now(dt.timezone.utc)
    pub = []
    for v in vs:
        p = v.get("published") or v.get("publishedAt")
        if not p or (v.get("privacy") or v.get("status")) != "public": continue
        t = dt.datetime.fromisoformat(p.replace("Z", "+00:00"))
        if t > now: continue
        h = max((now - t).total_seconds() / 3600, 0.5)
        pub.append(dict(title=v.get("title"), views=v.get("views", 0), hours=round(h, 1), vph=v.get("views", 0) / h, t=t))
    recent = [p for p in pub if p["hours"] <= 72]
    base = S.median([p["views"] for p in pub if 48 <= p["hours"] <= 24 * 30]) if pub else 0
    out = []
    for p in sorted(recent, key=lambda p: p["t"]):
        proj24 = p["views"] if p["hours"] >= 24 else p["vph"] * 24
        hit = proj24 >= 1000 or (base and proj24 >= 2 * base)
        out.append(dict(title=p["title"], views=p["views"], hours=p["hours"], proj24=int(proj24), hit=bool(hit)))
    print(json.dumps(dict(baseline_median_48h_30d=base, recent=out), ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
