#!/usr/bin/env python3
"""打印每个含 ANONYMIZED 的 entry 的完整锚点信息，用于反推真实 KOL。"""
import json, glob

for f in sorted(glob.glob("data/week_backfill/*.json")):
    raw = open(f, "rb").read()
    if b"ANONYMIZED" not in raw:
        continue
    d = json.loads(raw.decode("utf-8"))
    entries = d.get("entries", [])
    for i, e in enumerate(entries):
        blob = json.dumps(e, ensure_ascii=False)
        if "ANONYMIZED" not in blob:
            continue
        print(f"\n{'='*70}")
        print(f"{f}  entries[{i}]")
        for k, v in e.items():
            vs = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
            print(f"  {k}: {vs[:300]}")
