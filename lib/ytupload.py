"""Upload a rendered video to the Macun YouTube channel (YouTube Data API v3, stdlib only).

Credentials come from environment variables set in the cloud environment's settings (never from chat):
    YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
    publish_at in meta.json is sent as a scheduled publish time (status.publishAt). Check the printed
    "publish_at": if YouTube dropped it (unverified API project), the user schedules it in Studio instead.

Usage:
    python3 lib/ytupload.py check                       # verify credentials, print the channel name
    python3 lib/ytupload.py upload <video.mp4> <meta.json>
    python3 lib/ytupload.py comment <video_id> <text>   # e.g. the next day, once the video is public
meta.json: {"title", "description", "tags": [...], "playlist": "<series title>", "publish_at": "2026-10-26T17:30:00+09:00",
            "comment": "..."}
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

def upload(video, meta_path):
    meta = json.load(open(meta_path))
    tok = token()
    status = {"privacyStatus": "private", "selfDeclaredMadeForKids": False}
    if meta.get("publish_at") and (os.environ.get("YT_AUDITED") == "1" or meta.get("schedule", True)):
        status["publishAt"] = meta["publish_at"]          # stays private until then, then goes public
    body = {"snippet": {"title": meta["title"], "description": meta["description"], "tags": meta.get("tags", []),
                        "categoryId": "28", "defaultLanguage": "ja", "defaultAudioLanguage": "ja"}, "status": status}
    size = os.path.getsize(video)
    _, h, _ = http("POST", f"{UPLOAD}?uploadType=resumable&part=snippet,status", body,
                   {**auth(tok), "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)})
    loc = h.get("Location") or h.get("location")
    _, _, v = http("PUT", loc, raw=open(video, "rb").read(), headers={**auth(tok), "Content-Type": "video/mp4"})
    vid = v["id"]
    out = {"ok": True, "id": vid, "url": f"https://youtube.com/shorts/{vid}", "privacy": v["status"]["privacyStatus"],
           "publish_at": v["status"].get("publishAt")}
    if meta.get("playlist"):
        pid = playlist_id(tok, meta["playlist"])
        http("POST", f"{API}/playlistItems?part=snippet",
             {"snippet": {"playlistId": pid, "resourceId": {"kind": "youtube#video", "videoId": vid}}}, auth(tok))
        out["playlist"] = meta["playlist"]
    print(json.dumps(out, ensure_ascii=False))

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
    else: raise SystemExit(__doc__)
