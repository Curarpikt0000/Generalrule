#!/usr/bin/env python3
"""一次性核查：Notion By Day 的 Comments 源字节是否被 ANONYMIZED 污染。
复用 add_term 的连接常量，不写 DB id 字面量（避 redactor 损坏）。"""
import importlib.util, urllib.request, json

spec = importlib.util.spec_from_file_location("at", "scripts/add_term.py")
at = importlib.util.module_from_spec(spec)
spec.loader.exec_module(at)

TOKEN, DB, H = at.TOKEN, at.DB, at.H


def query_all():
    rows = []
    cursor = None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        req = urllib.request.Request(
            f"https://api.notion.com/v1/databases/{DB}/query",
            data=json.dumps(body).encode(),
            headers={**H, "Content-Type": "application/json"},
            method="POST",
        )
        r = json.loads(urllib.request.urlopen(req).read())
        rows += r["results"]
        if r.get("has_more"):
            cursor = r["next_cursor"]
        else:
            break
    return rows


def comments_bytes(props):
    for k, v in props.items():
        if v.get("type") == "rich_text" and k.lower() in ("comments", "comment"):
            txt = "".join(x["plain_text"] for x in v["rich_text"])
            return txt
    # fallback: any rich_text containing meaningful text
    return None


rows = query_all()
print(f"Notion By Day 总行数: {len(rows)}")
poisoned = []
for pg in rows:
    txt = comments_bytes(pg["properties"])
    if txt and "ANONYMIZED" in txt:
        # 用真字节确认（不是显示层）
        b = txt.encode("utf-8")
        if b"ANONYMIZED" in b:
            kol = at._kol_of(pg["properties"])
            poisoned.append((kol, txt.count("ANONYMIZED"), txt[:120]))

print(f"Comments 源被 ANONYMIZED 污染的行数: {len(poisoned)}")
for kol, n, sample in poisoned:
    print(f"  [{kol}] x{n}: {sample!r}")

# 同时核查 direction_detail（标的/方向）是否被污染——这是更严重的
print("\n=== direction_detail 污染核查（更严重）===")
dd_poison = 0
for pg in rows:
    legs = at._legs_of(pg["properties"])
    blob = json.dumps(legs, ensure_ascii=False)
    if "ANONYMIZED" in blob:
        dd_poison += 1
        print(f"  [{at._kol_of(pg['properties'])}] direction_detail 含 ANONYMIZED")
print(f"direction_detail 被污染行数: {dd_poison}")
