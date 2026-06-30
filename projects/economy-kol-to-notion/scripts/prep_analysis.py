#!/usr/bin/env python3
"""把 backfill 原始素材过滤到窗口内, 输出精简供 LLM 分析。
只保留 publishedDate 在 [start,end] 内的 Exa 条目 + 有效 Tavily。
用法: python3 prep_analysis.py <start> <end>
输出: data/analysis_input.json  (每 KOL: id/name/items[])
"""
import json, sys, os
from datetime import datetime

def in_window(dstr, start, end):
    if not dstr: return False
    try:
        d = dstr[:10]
        return start <= d <= end
    except: return False

def main():
    start, end = sys.argv[1], sys.argv[2]
    reg = json.load(open("data/kol_registry.json"))
    name_map = {k["id"]: k for k in reg["kols"]}
    out = {}
    bdir = "data/backfill"
    for fn in os.listdir(bdir):
        if not fn.endswith(".json"): continue
        kid = fn[:-5]
        if kid not in name_map: continue
        kol = name_map[kid]
        if not kol.get("active"): continue
        d = json.load(open(os.path.join(bdir, fn)))
        items = []
        seen_urls = set()
        for x in d.get("exa", []):
            if not in_window(x.get("date"), start, end): continue
            u = x.get("url")
            if u in seen_urls: continue
            seen_urls.add(u)
            txt = " ".join(x.get("highlights") or []) or x.get("text","")
            items.append({"date": (x.get("date") or "")[:10], "title": x.get("title"),
                          "url": u, "snippet": txt[:600]})
        # Tavily 无日期, 仅当 Exa 窗口内为空时补少量(标记需正文核验)
        out[kid] = {"id": kid, "name": kol["display_name"],
                    "notion_select": kol.get("notion_select_name", kol["display_name"]),
                    "sector": kol.get("sector"), "kol_or_ib": kol.get("kol_or_ib","KOL"),
                    "n_in_window": len(items), "items": items[:8]}
    json.dump(out, open("data/analysis_input.json","w"), ensure_ascii=False, indent=2)
    # summary
    withdata = {k:v for k,v in out.items() if v["n_in_window"]>0}
    print(f"KOL total: {len(out)} | 窗口内有素材: {len(withdata)}")
    for k,v in sorted(withdata.items(), key=lambda x:-x[1]["n_in_window"]):
        print(f"  {v['n_in_window']:2d}  {k} ({v['name']})")

if __name__ == "__main__":
    main()
