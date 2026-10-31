"""Upload a rendered video to the Macun YouTube channel (YouTube Data API v3, stdlib only).

Credentials come from environment variables set in the cloud environment's settings (never from chat):
    YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
    publish_at in meta.json is sent as a scheduled publish time (status.publishAt). Check the printed
    "publish_at": if YouTube dropped it (unverified API project), the user schedules it in Studio instead.

Usage:
    python3 lib/ytupload.py check                       # verify credentials, print the channel name
    python3 lib/ytupload.py upload <video.mp4> <meta.json>
    python3 lib/ytupload.py comment <video_id> <text>   # once the video is public
    python3 lib/ytupload.py recent                      # latest uploads (id + title)
    python3 lib/ytupload.py playlist <video_id> <playlist title>
meta.json: {"title", "description", "tags": [...], "playlist": "<series title>", "publish_at": "2026-10-26T17:30:00+09:00",
            "comment": "...", "notify_subscribers": false}
Prints one JSON line with the result.
"""
import json, os, ssl, sys, urllib.error, urllib.parse, urllib.request

API = "https://www.googleapis.com/youtube/v3"
UPLOAD = "https://www.googleapis.com/upload/youtube/v3/videos"
CA = "/root/.ccr/ca-bundle.crt"
CTX = ssl.create_default_context(cafile=CA) if os.path.exists(CA) else ssl.create_default_context()

def env(name):
    v = os.environ.get(name)
    if not v:
        raise SystemExit(f"missing environment variable {name} (add it in the cloud environment settings)")
    return v

def http(method, url, body=None, headers=None, raw=None):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    h = {"Content-Type": "application/json"} if body is not None else {}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=600) as r:
            txt = r.read().decode() or "{}"
            return r.status, dict(r.headers), json.loads(txt)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{method} {url.split('?')[0]} -> HTTP {e.code}: {e.read().decode()[:600]}")

def token():
    data = urllib.parse.urlencode(dict(client_id=env("YT_CLIENT_ID"), client_secret=env("YT_CLIENT_SECRET"),
                                       refresh_token=env("YT_REFRESH_TOKEN"), grant_type="refresh_token")).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, method="POST")
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=60) as r:
            return json.loads(r.read())["access_token"]
    except urllib.error.HTTPError as e:
        raise SystemExit(f"token refresh failed: HTTP {e.code}: {e.read().decode()[:300]}")

def auth(tok): return {"Authorization": f"Bearer {tok}"}

def check():
    tok = token()
    _, _, r = http("GET", f"{API}/channels?part=snippet&mine=true", headers=auth(tok))
    items = r.get("items", [])
    print(json.dumps({"ok": True, "channels": [i["snippet"]["title"] for i in items]}, ensure_ascii=False))

def playlist_id(tok, title):
    page = ""
    while True:
        _, _, r = http("GET", f"{API}/playlists?part=snippet&mine=true&maxResults=50{page}", headers=auth(tok))
        for p in r.get("items", []):
            if p["snippet"]["title"] == title: return p["id"]
        if not r.get("nextPageToken"): break
        page = "&pageToken=" + r["nextPageToken"]
    _, _, p = http("POST", f"{API}/playlists?part=snippet,status",
                   {"snippet": {"title": title, "defaultLanguage": "ja"}, "status": {"privacyStatus": "public"}}, auth(tok))
    return p["id"]

def taken_slots():
    """Publish times already used (YYYY-MM-DDTHH:MM, JST) according to state.json."""
    st = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "state.json")))
    out = {}
    for u in st.get("uploads", []):
        if u.get("scheduled") and u.get("date"): out[f"{u['date']}T{u['scheduled']}"] = u.get("title")
    for k, u in st.get("v2", {}).get("slots", {}).items():
        if u.get("id"): out[k] = u.get("title")
    return out

CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩"
LONG_TIME = "17:30"            # weekend longs: always 17:30 JST (user rule 2026-10-31)

def validate(meta, video):
    """Fix up metadata before any API call: Shorts titles must be '<series><number> #Shorts'; longs publish at 17:30."""
    import re
    is_long = meta.get("kind") == "long" or meta.get("notify_subscribers") is True
    title = (meta.get("title") or "").strip()
    if not is_long:
        body = re.sub(r"#shorts", "", title, flags=re.I).strip()
        if not body:                                 # empty or only '#Shorts' -> rebuild from series + number
            series = meta.get("series") or meta.get("playlist")
            num = meta.get("num")
            if not num:
                m = re.search(r"_(\d{2})_", os.path.basename(video))
                num = int(m.group(1)) if m else None
            if not (series and num): raise SystemExit(f"refused: title is empty/only #Shorts and series/number are unknown ({video})")
            meta["title"] = f"{series}{CIRCLED[int(num) - 1]} #Shorts"
            print(f"title completed -> {meta['title']}", file=sys.stderr)
        elif "#shorts" not in title.lower():
            meta["title"] = f"{title} #Shorts"
    elif meta.get("publish_at") and meta["publish_at"][11:16] != LONG_TIME:
        fixed = meta["publish_at"][:11] + LONG_TIME + ":00+09:00"
        print(f"long publish time {meta['publish_at']} -> {fixed} (longs are always 17:30)", file=sys.stderr)
        meta["publish_at"] = fixed
    if not meta.get("title", "").strip(): raise SystemExit("refused: empty title")
    return meta

def upload(video, meta_path):
    meta = validate(json.load(open(meta_path)), video)
    # rule (user, 2026-10-31): never publish two videos at the same time, Short or long alike
    if meta.get("publish_at") and not meta.get("allow_same_time"):
        key = meta["publish_at"][:16]
        clash = taken_slots().get(key)
        if clash and clash != meta.get("title"):
            raise SystemExit(f"refused: {key} is already used by '{clash}'. Same-time publishing is not allowed; pick another slot.")
    tok = token()
    status = {"privacyStatus": "private", "selfDeclaredMadeForKids": False}
    if meta.get("publish_at") and (os.environ.get("YT_AUDITED") == "1" or meta.get("schedule", True)):
        status["publishAt"] = meta["publish_at"]          # stays private until then, then goes public
    body = {"snippet": {"title": meta["title"], "description": meta["description"], "tags": meta.get("tags", []),
                        "categoryId": "28", "defaultLanguage": "ja", "defaultAudioLanguage": "ja"}, "status": status}
    size = os.path.getsize(video)
    notify = "true" if meta.get("notify_subscribers", True) else "false"   # Shorts: false / weekend longs: true
    _, h, _ = http("POST", f"{UPLOAD}?uploadType=resumable&part=snippet,status&notifySubscribers={notify}", body,
                   {**auth(tok), "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)})
    loc = h.get("Location") or h.get("location")
    _, _, v = http("PUT", loc, raw=open(video, "rb").read(), headers={**auth(tok), "Content-Type": "video/mp4"})
    vid = v["id"]
    out = {"ok": True, "id": vid, "url": f"https://youtube.com/shorts/{vid}", "privacy": v["status"]["privacyStatus"],
           "publish_at": v["status"].get("publishAt"), "notify_subscribers": notify == "true"}
    if meta.get("playlist"):
        try:
            add_to_playlist(tok, vid, meta["playlist"]); out["playlist"] = meta["playlist"]
        except SystemExit as e:                    # the video is up; a playlist hiccup must not hide its id
            out["playlist_error"] = str(e)[:200]
    print(json.dumps(out, ensure_ascii=False))

def add_to_playlist(tok, vid, title):
    import time
    for i in range(4):
        try:
            pid = playlist_id(tok, title)
            return http("POST", f"{API}/playlistItems?part=snippet",
                        {"snippet": {"playlistId": pid, "resourceId": {"kind": "youtube#video", "videoId": vid}}}, auth(tok))
        except SystemExit:
            if i == 3: raise
            time.sleep(3 * (i + 1))

def recent(n=5):
    tok = token()
    _, _, r = http("GET", f"{API}/channels?part=contentDetails&mine=true", headers=auth(tok))
    up = r["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    _, _, r = http("GET", f"{API}/playlistItems?part=snippet,status&maxResults={n}&playlistId={up}", headers=auth(tok))
    for i in r.get("items", []):
        print(i["snippet"]["resourceId"]["videoId"], i["snippet"]["title"])

def comment(vid, text):
    tok = token()
    _, _, r = http("POST", f"{API}/commentThreads?part=snippet",
                   {"snippet": {"videoId": vid, "topLevelComment": {"snippet": {"textOriginal": text}}}}, auth(tok))
    print(json.dumps({"ok": True, "comment_id": r["id"]}))

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "check": check()
    elif cmd == "upload": upload(sys.argv[2], sys.argv[3])
    elif cmd == "comment": comment(sys.argv[2], sys.argv[3])
    elif cmd == "recent": recent()
    elif cmd == "playlist": add_to_playlist(token(), sys.argv[2], sys.argv[3]); print(json.dumps({"ok": True}))
    else: raise SystemExit(__doc__)
