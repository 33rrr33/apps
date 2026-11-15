"""Competitor channel analysis: for channels found by research.py (JP iPhone tips), pull their last ~50 uploads
and compute cadence, shorts/long mix, median views, views per subscriber, top titles. -> data/channels.json"""
import json, os, sys, re, statistics as S, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
from ytupload import API, http, token, auth
from analytics import iso_dur
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main(maxch=40):
    res = json.load(open(os.path.join(ROOT, "data", "research.json")))
    jp = [v for v in res if re.search(r'[ぁ-んァ-ン]', v["title"])]
    chans = {}
    for v in jp: chans.setdefault(v["channel"], v)
    # prefer small/mid channels (<300k) – the ones whose path we can copy
    cand = sorted([v for v in chans.values() if 500 <= v["subs"] <= 300000], key=lambda v: -v["views"])[:maxch]
    tok = token(); out = []
    _, _, r = http("GET", f"{API}/search?part=snippet&type=video&q=" + "", headers=auth(tok)) if False else (0, 0, 0)
    for c in cand:
        # channel id via one of its videos
        _, _, vr = http("GET", f"{API}/videos?part=snippet&id={c['id']}", headers=auth(tok))
        cid = vr["items"][0]["snippet"]["channelId"]
        _, _, cr = http("GET", f"{API}/channels?part=contentDetails,statistics,snippet&id={cid}", headers=auth(tok))
        ch = cr["items"][0]; up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
        _, _, pr = http("GET", f"{API}/playlistItems?part=contentDetails&maxResults=50&playlistId={up}", headers=auth(tok))
        ids = [i["contentDetails"]["videoId"] for i in pr.get("items", [])]
        if not ids: continue
        _, _, vv = http("GET", f"{API}/videos?part=snippet,statistics,contentDetails&id=" + ",".join(ids), headers=auth(tok))
        vids = [dict(t=x["snippet"]["title"], p=x["snippet"]["publishedAt"], d=iso_dur(x["contentDetails"]["duration"]) or 0,
                     v=int(x["statistics"].get("viewCount", 0))) for x in vv.get("items", [])]
        vids.sort(key=lambda x: x["p"])
        days = max((dt.datetime.fromisoformat(vids[-1]["p"].replace("Z", "+00:00")) - dt.datetime.fromisoformat(vids[0]["p"].replace("Z", "+00:00"))).days, 1)
        shorts = [x for x in vids if x["d"] <= 180]; longs = [x for x in vids if x["d"] > 180]
        subs = int(ch["statistics"].get("subscriberCount", 0) or 0); tv = int(ch["statistics"].get("viewCount", 0) or 0)
        out.append(dict(channel=ch["snippet"]["title"], subs=subs, total_views=tv, videos=int(ch["statistics"].get("videoCount", 0)),
                        created=ch["snippet"]["publishedAt"][:10], subs_per_1k_views=round(subs / max(tv, 1) * 1000, 2),
                        posts_per_day=round(len(vids) / days, 2), shorts_share=round(len(shorts) / len(vids), 2),
                        short_median_views=int(S.median([x["v"] for x in shorts])) if shorts else 0,
                        short_median_sec=int(S.median([x["d"] for x in shorts])) if shorts else 0,
                        long_median_views=int(S.median([x["v"] for x in longs])) if longs else 0, n_longs=len(longs),
                        hit_rate_10k=round(sum(1 for x in shorts if x["v"] >= 10000) / max(len(shorts), 1), 2),
                        top=[(x["v"], x["d"], x["t"][:50]) for x in sorted(vids, key=lambda x: -x["v"])[:5]],
                        desc=ch["snippet"].get("description", "")[:160]))
    json.dump(out, open(os.path.join(ROOT, "data", "channels.json"), "w"), ensure_ascii=False, indent=1)
    print(len(out), "channels")

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 40)
