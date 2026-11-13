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
         "slot": {"06:00": "朝6:00", "12:00": "昼12:00", "17:30": "夕方17:30", "19:00": "夜19:00"}.get(v["hhmm"], "その他"),
         "layout": "旧デザイン",
         "title_style": "中身入り" if "｜" in v["title"] else "シリーズ名だけ",
         "title_type": "番号型" if re.search(r"[①-⑳]", v["title"]) else "内容型"}
    ep = (slot_meta or {}).get("episode")
    if ep and os.path.exists(P(ep)):
        src = open(P(ep)).read()
        t["layout"] = "画面録画風" if re.search(r'LAYOUT[^=\n]*= *"rec"', src) else "黒帯＋端末"
        h = re.search(r'^HOOK = "(.*)"', src, re.M)
        if h:
            hook = h.group(1)
            t["hook"] = hook.replace("\\n", " ")
            t["hook_type"] = ("即効型" if re.search(r"\d+秒|一瞬|すぐ", hook) else
                              "疑問型" if re.search(r"[？?]", hook) and "損" not in hook else "煽り型")
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

def perf_log():
    """data/performance_log.json: per Short, snapshots at >=24h and >=48h (views, likes, comments, retention if available)."""
    stats = load(P("data", "stats.json")); log = load(P("data", "performance_log.json"), {})
    for v in stats["videos"]:
        if v["privacy"] != "public" or v["kind"] != "short": continue
        e = log.setdefault(v["id"], dict(title=v["title"], published=v["published"][:16]))
        snap = dict(at_hours=v["age_hours"], views=v["views"], likes=v["likes"], comments=v["comments"],
                    avg_view_pct=v.get("avg_view_pct"), subs_gained=v.get("subs_gained"))
        if v["age_hours"] >= 24 and "h24" not in e: e["h24"] = snap
        if v["age_hours"] >= 48 and "h48" not in e: e["h48"] = snap
        e["latest"] = snap
    json.dump(log, open(P("data", "performance_log.json"), "w"), ensure_ascii=False, indent=1)

FEATURES = ("hook_type", "slot", "layout", "length", "topic_kind", "title_type")

def patterns():
    """Score each feature value by its 48h median vs the overall median -> config/patterns.json (winners >=600, losers <200)."""
    res = load(P("data", "results.json"), {}); rows = list(res.values())
    if not rows: return {}
    overall = S.median(r["views48"] for r in rows)
    out = dict(updated=dt.datetime.now().isoformat(timespec="minutes"), overall_median=overall, features={},
               winners=[r["tags"].get("hook") for r in rows if r["views48"] >= 600 and r["tags"].get("hook")],
               losers=[r["tags"].get("hook") for r in rows if r["views48"] < 200 and r["tags"].get("hook")])
    for f in FEATURES:
        g = groups(res, f)
        out["features"][f] = {k: dict(v, score=round(v["median"] / overall, 2) if overall else None) for k, v in g.items()}
    json.dump(out, open(P("config", "patterns.json"), "w"), ensure_ascii=False, indent=1)
    return out

def act():
    """Weekly Act (Friday): pin a winning time / hook once it clearly wins (user allowed automatic time/title changes)."""
    pat = patterns(); strat = load(P("config", "strategy.json")); changes = []
    since = strat.get("v3_since", "2026-11-12")
    res = {k: v for k, v in load(P("data", "results.json"), {}).items() if v["published"][:10] >= since}
    for f, key in (("slot", "slot_pin"), ("hook_type", "hook_pin")):
        g = groups(res, f)
        if len(g) < 2 or strat.get(key): continue
        best, rest = max(g.items(), key=lambda kv: kv[1]["median"]), [v for k, v in g.items()]
        others = [v for k, v in g.items() if k != best[0]]
        if best[1]["n"] >= 3 and all(o["n"] >= 2 for o in others) and best[1]["median"] >= 1.5 * max(o["median"] for o in others):
            val = {"朝6:00": "06:00", "昼12:00": "12:00", "夜19:00": "19:00"}.get(best[0], best[0]) if f == "slot" else best[0]
            strat[key] = val; changes.append(f"{f} を「{best[0]}」に固定（中央値 {int(best[1]['median'])}回）")
    if changes:
        strat.setdefault("history", []).append(dict(date=dt.date.today().isoformat(), change="、".join(changes), why="A/Bテストで1.5倍以上の差"))
        json.dump(strat, open(P("config", "strategy.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(dict(changes=changes or ["変更なし（差がまだ小さい／本数不足）"]), ensure_ascii=False))

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
    for field, title in (("length", "長さ別"), ("slot", "時間帯別"), ("hook_type", "フックの型別"), ("layout", "見た目別")):
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
    {"check": lambda: (check(), perf_log(), patterns()), "judge": judge, "insights": insights, "act": act,
     "patterns": patterns}[sys.argv[1]]()
