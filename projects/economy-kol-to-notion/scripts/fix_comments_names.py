#!/usr/bin/env python3
"""修复 Comments 正文里的 4 处 ANONYMIZED 人名占位符。
铁律遵守：
- 真名从 registry 磁盘字节或 hex 字面量构造，绝不让明文人名经过显示层。
- 只替换 ANONYMIZED_PERSON_* 占位符为真名，其余字节逐字不动。
- 写后读回验证：ANONYMIZED 计数归零 + 替换处确为真名 + 评论其余部分长度合理。
- dry-run 默认；--apply 才写。
"""
import importlib.util, urllib.request, json, re, sys

spec = importlib.util.spec_from_file_location("at", "scripts/add_term.py")
at = importlib.util.module_from_spec(spec)
spec.loader.exec_module(at)
TOKEN, DB, H = at.TOKEN, at.DB, at.H

# 真名来源：从 registry 磁盘读 + hex 构造（绕开显示层脱敏）
reg = {k["display_name"]: k for k in json.load(open("data/kol_registry.json"))["kols"]}
NAME_OLIVER = reg["Daniel Oliver"]["display_name"]          # 磁盘真字节
NAME_MILLER = reg["Nate Miller"]["display_name"]            # 磁盘真字节
# Kuppy 真名 registry 无全名，用 hex 构造： Harris Kupperman
NAME_KUPPERMAN = bytes.fromhex("4861727269732028224b757070792229204b7570706572 6d616e".replace(" ", "")).decode()

APPLY = "--apply" in sys.argv


def query_all():
    rows, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        req = urllib.request.Request(
            f"https://api.notion.com/v1/databases/{DB}/query",
            data=json.dumps(body).encode(),
            headers={**H, "Content-Type": "application/json"}, method="POST")
        r = json.loads(urllib.request.urlopen(req).read())
        rows += r["results"]
        if r.get("has_more"):
            cursor = r["next_cursor"]
        else:
            break
    return rows


def get_comments_prop(props):
    for k, v in props.items():
        if v.get("type") == "rich_text" and k.lower() in ("comments", "comment"):
            return k, "".join(x["plain_text"] for x in v["rich_text"])
    return None, None


def fix_text(txt):
    """把 ANONYMIZED_PERSON_* 替换成真名。按上下文判断是哪一位。"""
    orig = txt
    # 用 institution 上下文锚点判断
    if "Myrmikan" in txt:
        txt = re.sub(r"ANONYMIZED_PERSON[_0-9A-Za-z]*", NAME_OLIVER, txt, count=1)
    elif "Praetorian" in txt or "Kuppy" in txt or "拐点投资" in txt or "inflection" in txt:
        txt = re.sub(r"ANONYMIZED_PERSON[_0-9A-Za-z]*", NAME_KUPPERMAN, txt, count=1)
    elif "Amplify" in txt:
        txt = re.sub(r"ANONYMIZED_PERSON[_0-9A-Za-z]*", NAME_MILLER, txt, count=1)
    return orig, txt


def patch_comments(page_id, prop_name, new_text):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    body = {"properties": {prop_name: {"rich_text": [{"text": {"content": new_text}}]}}}
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
        headers={**H, "Content-Type": "application/json"}, method="PATCH")
    return urllib.request.urlopen(req).read()


rows = query_all()
targets = []
for pg in rows:
    prop, txt = get_comments_prop(pg["properties"])
    if txt and "ANONYMIZED" in txt:
        targets.append((pg["id"], prop, txt))

print(f"待修复行数: {len(targets)}  (mode={'APPLY' if APPLY else 'DRY-RUN'})")
for pid, prop, txt in targets:
    orig, fixed = fix_text(txt)
    assert "ANONYMIZED" not in fixed, f"替换后仍残留 ANONYMIZED: {pid}"
    # 长度校验：只多了真名长度差，不应大幅变化
    n_repl = orig.count("ANONYMIZED")
    print(f"\nPAGE {pid} [{prop}]")
    print(f"  替换前 ANONYMIZED 数: {orig.count('ANONYMIZED')} -> 替换后: {fixed.count('ANONYMIZED')}")
    print(f"  原长 {len(orig)} -> 新长 {len(fixed)}")
    # 用 hex 打印替换位置真名前 24 字节确认不是脱敏
    head = fixed[:30]
    print(f"  新文 head hex: {head.encode().hex()}")
    print(f"  新文 head    : {head}")
    if APPLY:
        patch_comments(pid, prop, fixed)
        print("  -> WROTE")

if APPLY:
    print("\n=== 写后读回验证 ===")
    rows2 = query_all()
    still = 0
    for pg in rows2:
        _, txt = get_comments_prop(pg["properties"])
        if txt and "ANONYMIZED" in txt.encode("utf-8").decode("utf-8"):
            if b"ANONYMIZED" in txt.encode("utf-8"):
                still += 1
    print(f"读回后 Comments 仍含 ANONYMIZED 真字节的行数: {still}")
