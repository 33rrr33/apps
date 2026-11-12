"""Benchmark: top Japanese iPhone-tip Shorts (last N days) via YouTube Data API -> data/research.json
usage: research.py [days=90]"""
import json, os, sys, re, datetime as dt, urllib.parse
sys.path.insert(0, os.path.dirname(__file__))
from ytupload import API, http, token, auth
from analytics import iso_dur

QUERIES = ["iPhone 便利機能", "iPhone 裏技", "iPhone 設定 知らない", "iPhone 隠し機能", "iPhone 使い方 ショート", "iOS 便利 設定"]

def main(days=90):
    tok = token(); since = (dt.datetime.utcnow() - dt.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    ids = {}
    for q in QUERIES:
        p = dict(part="snippet", q=q, type="video", videoDuration="short", regionCode="JP", relevanceLanguage="ja",
                 order="viewCount", publishedAfter=since, maxResults=50)
        _, _, r = http("GET", f"{API}/search?" + urllib.parse.urlencode(p), headers=auth(tok))
        for it in r.get("items", []): ids.setdefault(it["id"]["videoId"], q)
    vids, ids_l = [], list(ids)
    for i in range(0, len(ids_l), 50):
        _, _, r = http("GET", f"{API}/videos?part=snippet,statistics,contentDetails&id=" + ",".join(ids_l[i:i + 50]), headers=auth(tok))
        vids += r.get("items", [])
    chans = {}
    cids = list({v["snippet"]["channelId"] for v in vids})
    for i in range(0, len(cids), 50):
        _, _, r = http("GET", f"{API}/channels?part=statistics,snippet&id=" + ",".join(cids[i:i + 50]), headers=auth(tok))
        for c in r.get("items", []): chans[c["id"]] = c
    out = []
    for v in vids:
        s, st, c = v["snippet"], v.get("statistics", {}), chans.get(v["snippet"]["channelId"], {})
        cs = c.get("statistics", {})
        out.append(dict(id=v["id"], title=s["title"], channel=s["channelTitle"], published=s["publishedAt"],
                        dur=iso_dur(v["contentDetails"]["duration"]), views=int(st.get("viewCount", 0)),
                        likes=int(st.get("likeCount", 0)), comments=int(st.get("commentCount", 0)),
                        subs=int(cs.get("subscriberCount", 0) or 0), ch_videos=int(cs.get("videoCount", 0) or 0),
                        ch_views=int(cs.get("viewCount", 0) or 0), query=ids[v["id"]], desc=s.get("description", "")[:300]))
    out.sort(key=lambda x: -x["views"])
    json.dump(out, open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "research.json"), "w"), ensure_ascii=False, indent=1)
    print(len(out), "videos,", len(chans), "channels")

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 90)
