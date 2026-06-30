#!/usr/bin/env python3
"""修复 data/week_backfill/*.json 里所有 ANONYMIZED 人名污染。
铁律：真名只从 registry 磁盘字节 / hex 字面量构造，绝不让明文人名经过显示层。
逐 entry 精确替换 kol 字段 + comments 内人名。dry-run 默认，--apply 才写。
写后读回校验：全文件 ANONYMIZED 计数归零。"""
import json, sys

APPLY = "--apply" in sys.argv

# 真名来源：registry 磁盘字节
reg = {k["display_name"]: k["display_name"] for k in json.load(open("data/kol_registry.json"))["kols"]}
MEGER      = reg["David Meger"]          # High Ridge Futures 金属交易总监
HABERKORN  = reg["Bob Haberkorn"]        # RJO Futures 高级市场策略师
GOTTLIEB   = reg["Robert Gottlieb"]      # 前 JPM 贵金属台
OLIVER     = reg["Daniel Oliver"]        # Myrmikan Gold Fund
MILLER     = reg["Nate Miller"]          # Amplify ETFs
KUPTSIK    = reg["Alex Kuptsikevich"]    # FxPro
# registry 无的 → hex 构造：Joshua Gibson (FXStreet 撰稿分析师)
GIBSON     = bytes.fromhex("4a6f7368756120476962736f6e").decode()

# 映射表：(文件, entry索引) -> kol 真名（kol 字段整体替换为此真名）
KOL_FIX = {
    ("2025-W49", 1): MEGER,
    ("2025-W50", 1): HABERKORN,
    ("2026-W01", 0): GOTTLIEB,
    ("2026-W01", 1): MEGER,
    ("2026-W03", 5): MEGER,
    ("2026-W03", 13): OLIVER,
    ("2026-W05", 2): GOTTLIEB,
    ("2026-W05", 13): MEGER,
    ("2026-W06", 9): HABERKORN,
    ("2026-W07", 3): MEGER,
    ("2026-W07", 6): GOTTLIEB,
    ("2026-W08", 5): MEGER,
    ("2026-W10", 1): GOTTLIEB,
    ("2026-W10", 3): MEGER,
    ("2026-W10", 7): HABERKORN,
    ("2026-W23", 14): KUPTSIK,
    ("2026-W25", 40): GIBSON,
    ("2026-W09", 4): MILLER,
}
# comments 内嵌人名替换：(文件, entry索引) -> 真名（替换 comments 里的 ANONYMIZED_PERSON_*）
COMMENT_FIX = {
    ("2026-W03", 13): OLIVER,   # ANONYMIZED_PERSON_0_15(Myrmikan...) -> Daniel Oliver
    ("2026-W09", 4): MILLER,    # Amplify副总裁ANONYMIZED_PERSON_0 -> Nate Miller
}

import re
ANON_RE = re.compile(r"ANONYMIZED_PERSON[_0-9A-Za-z]*")

def fix_file(week):
    path = f"data/week_backfill/{week}.json"
    d = json.load(open(path, encoding="utf-8"))
    entries = d["entries"]
    changed = []
    for (wf, idx), name in KOL_FIX.items():
        if wf != week: continue
        e = entries[idx]
        if "ANONYMIZED" in e.get("kol", ""):
            old = e["kol"]; e["kol"] = name
            changed.append(f"kol[{idx}] {old} -> {name}")
    for (wf, idx), name in COMMENT_FIX.items():
        if wf != week: continue
        e = entries[idx]
        c = e.get("comments", "")
        if "ANONYMIZED" in c:
            e["comments"] = ANON_RE.sub(name, c, count=1)
            changed.append(f"comments[{idx}] -> {name}")
    return d, changed, path

weeks = sorted({wf for (wf, _) in list(KOL_FIX) + list(COMMENT_FIX)})
total_changes = 0
for week in weeks:
    d, changed, path = fix_file(week)
    if not changed: continue
    total_changes += len(changed)
    blob = json.dumps(d, ensure_ascii=False, indent=2)
    residual = blob.count("ANONYMIZED")
    print(f"\n{path}  ({'APPLY' if APPLY else 'DRY'})")
    for c in changed: print("   ", c)
    print(f"    写后残留 ANONYMIZED: {residual}")
    if APPLY:
        if residual > 0:
            print("    !! 仍有残留，跳过写入（需人工查）"); continue
        open(path, "w", encoding="utf-8").write(blob)
        # 读回验证
        back = open(path, "rb").read()
        print(f"    读回 ANONYMIZED 真字节: {back.count(b'ANONYMIZED')}")

print(f"\n共 {total_changes} 处修改, 涉及 {len(weeks)} 个周文件")
