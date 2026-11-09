"""PDCA for the channel (run after analytics.py fetch).

    python3 lib/pdca.py check   # Do→Check: record each public Short's 48h result once, with its experiment tags
    python3 lib/pdca.py judge   # Check→Act: judge config/strategy.json running_experiment by config/experiments.json rule
    python3 lib/pdca.py insights  # rewrite data/insights.json (what we learned / what we do / what's next) from the numbers

data/results.json keeps one row per Short: views at ~48h (first fetch at or after 48h), tags, and the experiment it belonged to.
Tags come from the episode file (DURATION/END_CARD, HOOK, CTA spoken, TAGS = {...} if the episode sets them) and the slot.
"""
import datetime as dt, json, os, re, statistics as S, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
load = lambda p, d=None: json.load(open(p)) if os.path.exists(p) else d

def tags_for(v, slot_meta):
    t = {"length": "短縮版" if v["seconds"] <= 15 and v["published"][:10] >= "2026-11-10" else ("11〜16秒" if v["seconds"] <= 17 else "20秒"),
         "slot": {"06:00": "朝6:00", "17:30": "夕方17:30"}.get(v["hhmm"], "その他"),
         "title_style": "中身入り" if "｜" in v["title"] else "シリーズ名だけ"}
    ep = (slot_meta or {}).get("episode")
    if ep and os.path.exists(P(ep)):
        src = open(P(ep)).read()
        h = re.search(r'^HOOK = "(.*)"', src, re.M)
        if h:
            hook = h.group(1)
            t["hook"] = hook.replace("\\n", " ")
            t["hook_type"] = "問いかけ型" if re.search(r"[？?]", hook) and "損" not in hook else "損失型"
        c = re.search(r'spoken="([^"]*)"', src.split("CTA = dict", 1)[-1])
        if c: t["cta"] = "フォロー" if "フォロー" in c.group(1) else "保存"
        m = re.search(r"^TAGS = (\{.*\})", src, re.M)
        if m:
            try: t.update(json.loads(m.group(1)))
            except Exception: pass
    return t

def check():
    stats = load(P("data", "stats.json")); st = load(P("state.json"))
    slots = {v["id"]: v for v in st.get("v2", {}).get("slots", {}).values() if v.get("id")}
    res = load(P("data", "results.json"), {})
    exp = load(P("config", "strategy.json"), {}).get("running_experiment", {})
    added = 0
    for v in stats["videos"]:
        if v["privacy"] != "public" or v["kind"] != "short" or v["age_hours"] < 48: continue
        if v["id"] in res: continue
        res[v["id"]] = dict(title=v["title"], published=v["published"][:16], age_at_record=v["age_hours"],
                            views48=v["views"], likes=v["likes"], comments=v["comments"],
                            late=v["age_hours"] > 72, tags=tags_for(v, slots.get(v["id"])),
                            experiment=exp.get("id") if v["published"][:10] >= exp.get("started", "9999") else None)
        added += 1
    json.dump(res, open(P("data", "results.json"), "w"), ensure_ascii=False, indent=1)
    print(f"recorded {added} new results ({len(res)} total)")

def groups(res, field, rows=None):
    out = {}
    for r in (rows or res.values()):
        k = r["tags"].get(field)
        if k: out.setdefault(k, []).append(r["views48"])
    return {k: dict(n=len(v), median=S.median(v), hit=sum(x >= 1000 for x in v) / len(v)) for k, v in out.items()}

def judge():
    res = load(P("data", "results.json"), {}); strat = load(P("config", "strategy.json")); exps = load(P("config", "experiments.json"))
    run = strat.get("running_experiment") or {}
    spec = next((e for e in exps["backlog"] if e["id"] == run.get("id")), None)
    if not spec: print("no running experiment"); return None
    g = groups(res, spec["tag_field"])
    test = g.get(run.get("test_tag") or spec["test"]) or g.get(run.get("test_tag", "短縮版"))
    base = g.get(run.get("baseline_tag") or "20秒")
    verdict = dict(id=spec["id"], test=test, baseline=base, decision="継続（本数が足りない）")
    if test and base and test["n"] >= exps["rule"]["min_videos"]:
        better = test["median"] >= 1.5 * base["median"] or test["hit"] - base["hit"] >= 0.2
        if better: verdict["decision"] = "採用"
        elif test["n"] >= 6: verdict["decision"] = "見送り"
    print(json.dumps(verdict, ensure_ascii=False))
    return verdict

def insights():
    res = load(P("data", "results.json"), {}); strat = load(P("config", "strategy.json"))
    rows = list(res.values()); n = len(rows)
    if not n: return
    med = S.median(r["views48"] for r in rows); hit = sum(r["views48"] >= 1000 for r in rows)
    out = [dict(kind="finding", id="overall", title=f"48時間で1,000回を超えたのは{n}本中{hit}本",
                body=f"公開48時間の再生回数の中央値は{int(med):,}回。目標は「毎回1,000回以上」。",
                evidence="data/results.json（各ショートの48時間時点の再生回数）")]
    for field, title in (("length", "長さ別"), ("slot", "時間帯別"), ("hook_type", "フックの型別")):
        g = groups(res, field)
        if len(g) >= 2:
            best = max(g.items(), key=lambda kv: kv[1]["median"])
            body = "、".join(f"{k}：中央値{int(v['median']):,}回（{v['n']}本・達成{round(v['hit']*100)}%）" for k, v in sorted(g.items(), key=lambda kv: -kv[1]["median"]))
            out.append(dict(kind="finding", id=field, title=f"{title}では「{best[0]}」が一番伸びている", body=body, evidence="公開48時間の再生回数"))
    run = strat.get("running_experiment") or {}
    v = judge() if run else None
    if run:
        out.append(dict(kind="action", id="running", title=f"実験中：{run.get('change')}", body=f"判定：{v['decision'] if v else '—'}。{run.get('judge_on','')}に判定。",
                        evidence=f"比べる相手：{run.get('compare_with','')}"))
    for i, h in enumerate(strat.get("history", [])[-3:]):
        out.append(dict(kind="action", id=f"h{i}", title=f"{h['date']}に変えたこと：{h['change']}", body=h["why"], evidence="config/strategy.json"))
    nxt = strat.get("next_experiment")
    if nxt: out.append(dict(kind="next", id="next", title=f"次に試すこと：{nxt.get('test')}", body=nxt.get("why", ""), evidence=f"変える点：{nxt.get('variable')}"))
    json.dump(out, open(P("data", "insights.json"), "w"), ensure_ascii=False, indent=1)
    print(f"{len(out)} insight rows")

if __name__ == "__main__":
    {"check": check, "judge": judge, "insights": insights}[sys.argv[1]]()
