#!/usr/bin/env python3
"""全面排查 data/week_backfill/*.json 里所有 ANONYMIZED 污染处，
打印每处的：文件、JSON 路径(字段)、所在条目的 kol/其他锚点字段、周边文本。
只读不改——先看清全貌。"""
import json, glob, os

def walk(obj, path=""):
    """yield (path, value) for every str leaf containing ANONYMIZED"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{path}[{i}]")
    elif isinstance(obj, str) and "ANONYMIZED" in obj:
        yield path, obj

for f in sorted(glob.glob("data/week_backfill/*.json")):
    raw = open(f, "rb").read()
    if b"ANONYMIZED" not in raw:
        continue
    d = json.loads(raw.decode("utf-8"))
    print(f"\n{'='*70}\nFILE: {f}")
    for path, val in walk(d):
        # 找同一条目的 kol 字段做锚点
        print(f"  PATH {path}")
        print(f"    VALUE: {val[:160]}")
