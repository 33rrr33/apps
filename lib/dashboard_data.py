"""data/stats.json (from analytics.py fetch) -> data/dash_videos.json + data/dash_channel.json for the dashboard."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(ROOT, "data", "stats.json")))
rows = []
for r in d["videos"]:
    if r["privacy"] != "public" and not r.get("slot"): continue          # unlisted/cancelled privates are left out
    slot = "朝6:00" if r["hhmm"] == "06:00" else ("夕方17:30" if r["hhmm"] == "17:30" else "その他の時間")
    if r["kind"] == "long": length = "長尺"
    elif r["published"][:10] >= "2026-11-10" and r["seconds"] <= 15: length = "短縮版"     # experiment from 11/10
    else: length = "11〜16秒" if r["seconds"] <= 17 else "20秒"
    rows.append(dict(id=r["id"], published=r["published"][:16], date=r["published"][:10], weekday=r["weekday"], slot=slot,
                     title=r["title"].replace("#Shorts", "").replace("⁠", "").strip(), kind="長尺" if r["kind"] == "long" else "ショート",
                     seconds=r["seconds"], length=length, status="公開中" if r["privacy"] == "public" else "予約中",
                     views=r["views"], likes=r["likes"], comments=r["comments"], age_hours=r["age_hours"],
                     judged=bool(r["age_hours"] >= 48 and r["privacy"] == "public")))
json.dump(rows, open(os.path.join(ROOT, "data", "dash_videos.json"), "w"), ensure_ascii=False, indent=1)
json.dump([dict(fetched=d["fetched"][:16], **d["channel"])], open(os.path.join(ROOT, "data", "dash_channel.json"), "w"), ensure_ascii=False)
print(len(rows), "rows")
