"""Rename already-uploaded Shorts to continuous series numbers (e.g. 2nd block of a series = ⑥〜⑩).
usage: renumber.py <video_id> <new_num> [<offset>]   (offset shifts the ①〜⑤ list in the description)"""
import json, re, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from ytupload import API, http, token, auth, CIRCLED

def fix_desc(d, off):
    sh = lambda c: CIRCLED[CIRCLED.index(c) + off]
    d = re.sub(r"^([①-⑤])〜([①-⑤])", lambda m: sh(m.group(1)) + "〜" + sh(m.group(2)), d, flags=re.M)
    d = re.sub(r"^([①-⑤]) ", lambda m: CIRCLED[CIRCLED.index(m.group(1)) + off] + " ", d, flags=re.M)
    d = d.replace("（全5回）", "")
    d = d.replace("Macunでは平日毎日 朝6:00 と 夕方17:30 にiPhoneの便利技を投稿中！", "Macunでは毎日1本、iPhoneの便利技を投稿中！")
    return d

def renumber(vid, num, off=5):
    tok = token()
    _, _, r = http("GET", f"{API}/videos?part=snippet&id={vid}", headers=auth(tok))
    sn = r["items"][0]["snippet"]
    title = re.sub(r"[①-⑳]", CIRCLED[num - 1], sn["title"], count=1)
    body = {"id": vid, "snippet": {"title": title, "description": fix_desc(sn["description"], off),
                                   "categoryId": sn["categoryId"], "tags": sn.get("tags", []),
                                   "defaultLanguage": sn.get("defaultLanguage", "ja")}}
    http("PUT", f"{API}/videos?part=snippet", body=body, headers=auth(tok))
    _, _, r = http("GET", f"{API}/videos?part=snippet&id={vid}", headers=auth(tok))
    print(vid, r["items"][0]["snippet"]["title"])

if __name__ == "__main__":
    renumber(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else 5)
