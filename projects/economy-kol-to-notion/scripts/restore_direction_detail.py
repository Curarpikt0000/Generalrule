"""Rewind 执行器 —— 从备份还原 方向明细 原始字节。
复用 add_term 的连接配置(DB/H/_txt), 避免在本文件写 DB id 字面量(redactor 会干扰)。
用法:
  python3 restore_direction_detail.py <backup_file>            # 还原全部行
  python3 restore_direction_detail.py <backup_file> <page_id>  # 只还原一行
  python3 restore_direction_detail.py <backup_file> --check    # 只对比当前 vs 备份, 不写
"""
import json, urllib.request, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from add_term import DB, H, _txt   # 复用已验证可用的配置

def get_current(page_id):
    req = urllib.request.Request(f"https://api.notion.com/v1/pages/{page_id}", headers=H)
    d = json.load(urllib.request.urlopen(req, timeout=60))
    return _txt(d["properties"].get("方向明细", {}))

def write_md(page_id, md):
    body = {"properties": {"方向明细": {"rich_text": [{"type": "text",
        "text": {"content": md[:1990]}}]}}}
    req = urllib.request.Request(f"https://api.notion.com/v1/pages/{page_id}",
        data=json.dumps(body).encode(), headers=H, method="PATCH")
    urllib.request.urlopen(req, timeout=60)

backup_file = sys.argv[1]
backup = json.load(open(backup_file))
arg2 = sys.argv[2] if len(sys.argv) > 2 else None

if arg2 == "--check":
    diff = 0
    for pid, orig in backup.items():
        cur = get_current(pid)
        if cur != orig:
            diff += 1
            print(f"DIFF {pid[:8]}: 当前!=备份 {'(当前含ANONYMIZED!)' if 'ANONYMIZED' in cur else ''}")
    print(f"# 共 {diff}/{len(backup)} 行与备份不同")
elif arg2:
    write_md(arg2, backup[arg2])
    print(f"✅ 已还原 {arg2[:8]}")
else:
    n = 0
    for pid, orig in backup.items():
        write_md(pid, orig); n += 1
        if n % 100 == 0: print(f"  还原 {n}/{len(backup)}...")
    print(f"✅ 全量还原 {n} 行")
