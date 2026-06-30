#!/usr/bin/env python3
"""每日批量搜索 — 对所有 active KOL 跑当日窗口多源检索(Exa+Tavily)。
用法: python3 scripts/daily_search.py <start> <end>
输出: data/daily/<date>_raw.json (所有 KOL 原始素材汇总), 并打印每个 KOL 命中数。
"""
import json, sys, urllib.request, urllib.error, time, os
from datetime import datetime

def load_key(name):
    pre = name + "="
    for l in open("config/.env"):
        if l.startswith(pre): return l[len(pre):].strip()
    return ""

EXA = load_key("EXA_API" + "_KEY")
TAV = load_key("TAVILY_API" + "_KEY")

def exa_search(query, start, end, num=6):
    body = {"query": query, "type": "auto", "numResults": num,
        "startPublishedDate": start + "T00:00:00.000Z",
        "endPublishedDate": end + "T23:59:59.000Z",
        "contents": {"highlights": True, "text": {"maxCharacters": 1500}}}
    req = urllib.request.Request("https://api.exa.ai/search", data=json.dumps(body).encode(),
        headers={"x-api-key": EXA, "Content-Type": "application/json"}, method="POST")
    try:
        d = json.load(urllib.request.urlopen(req, timeout=45))
        return d.get("results", [])
    except Exception as e:
        print(f"    Exa ERR: {str(e)[:80]}", file=sys.stderr); return []

def tavily_search(query, num=5):
    body = {"query": query, "max_results": num, "search_depth": "advanced",
            "include_raw_content": False, "topic": "news", "days": 4}
    req = urllib.request.Request("https://api.tavily.com/search", data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + TAV, "Content-Type": "application/json"}, method="POST")
    try:
        d = json.load(urllib.request.urlopen(req, timeout=45))
        return d.get("results", [])
    except Exception as e:
        print(f"    Tavily ERR: {str(e)[:80]}", file=sys.stderr); return []

def main():
    start = sys.argv[1]; end = sys.argv[2]
    reg = json.load(open("data/kol_registry.json"))
    kols = [k for k in reg["kols"] if k.get("active")]
    print(f"窗口 {start} ~ {end} | {len(kols)} active KOL", flush=True)
    out = {"window": [start, end], "generated": datetime.now().isoformat(), "kols": {}}
    for i, kol in enumerate(kols):
        kid = kol["id"]; terms = kol.get("search_terms") or [kol["display_name"]]
        rec = {"display_name": kol["display_name"], "sector": kol.get("sector"),
               "exa": [], "tavily": []}
        for term in terms[:3]:
            for x in exa_search(term, start, end):
                rec["exa"].append({"title": x.get("title"), "url": x.get("url"),
                    "date": x.get("publishedDate"),
                    "highlights": x.get("highlights", []),
                    "text": (x.get("text") or "")[:1200], "q": term})
            time.sleep(0.3)
        for term in terms[:2]:
            for x in tavily_search(term):
                rec["tavily"].append({"title": x.get("title"), "url": x.get("url"),
                    "content": x.get("content", "")[:1200],
                    "date": x.get("published_date"), "score": x.get("score"), "q": term})
            time.sleep(0.3)
        ne, nt = len(rec["exa"]), len(rec["tavily"])
        out["kols"][kid] = rec
        print(f"[{i+1}/{len(kols)}] {kid}: Exa {ne}, Tav {nt}", flush=True)
    os.makedirs("data/daily", exist_ok=True)
    fn = f"data/daily/{end}_raw.json"
    json.dump(out, open(fn, "w"), ensure_ascii=False, indent=2)
    print(f"\n已存 {fn}", flush=True)

if __name__ == "__main__":
    main()
