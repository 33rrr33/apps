"""Post the prepared comment on every scheduled video (state.json v2.slots) that is now public and not commented yet.
    python3 lib/comment_new.py      -> prints one line per comment posted (titles), for the 'コメントを付けました、固定してね' notice
"""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ytupload as Y
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
st = json.load(open(os.path.join(ROOT, "state.json")))
todo = [(k, v) for k, v in st.get("v2", {}).get("slots", {}).items() if v.get("id") and v.get("comment") and not v.get("comment_posted")]
if todo:
    tok = Y.token()
    ids = ",".join(v["id"] for _, v in todo)
    _, _, r = Y.http("GET", f"{Y.API}/videos?part=status&id={ids}", headers=Y.auth(tok))
    public = {i["id"] for i in r.get("items", []) if i["status"]["privacyStatus"] == "public"}
    for k, v in todo:
        if v["id"] in public:
            Y.comment(v["id"], v["comment"]); v["comment_posted"] = True
            print("commented:", k, v.get("title"))
    json.dump(st, open(os.path.join(ROOT, "state.json"), "w"), ensure_ascii=False, indent=1)
