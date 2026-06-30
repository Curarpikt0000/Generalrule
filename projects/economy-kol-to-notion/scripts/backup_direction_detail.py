"""全量备份 By Day 的 方向明细 原始字节 (rewind 基础)。
输出: scratch/backup_direction_detail_<ts>.json  = {page_id: 原始JSON字符串}
还原用: python3 restore_direction_detail.py <backup_file> [page_id]
"""
import json, urllib.request, sys, time

def load_key(name):
    pre=name+"="
    for l in open("config/.env"):
        if l.startswith(pre): return l[len(pre):].strip()
    return ""

TOKEN=load_key("NOTION_TOKEN")
DB="32347eb5fd3c8087b9c0f409f95f664e"
H={"Authorization":f"Bearer {TOKEN}","Notion-Version":"2022-06-28","Content-Type":"application/json"}

def _txt(p):
    if not p: return ""
    return "".join(x.get("plain_text","") for x in (p.get("rich_text") or []))

rows=[]; cursor=None
while True:
    body={"page_size":100}
    if cursor: body["start_cursor"]=cursor
    req=urllib.request.Request(f"https://api.notion.com/v1/databases/{DB}/query",
        data=json.dumps(body).encode(), headers=H, method="POST")
    d=json.load(urllib.request.urlopen(req,timeout=60))
    rows+=d["results"]
    if not d.get("has_more"): break
    cursor=d["next_cursor"]

backup={}
anon_found=0
for r in rows:
    md=_txt(r["properties"].get("方向明细",{}))
    if md.strip():
        backup[r["id"]]=md
        if "ANONYMIZED" in md: anon_found+=1

ts=time.strftime("%Y%m%d_%H%M%S")
out=f"scratch/backup_direction_detail_{ts}.json"
json.dump(backup, open(out,"w"), ensure_ascii=False, indent=2)
print(f"✅ 备份 {len(backup)} 行方向明细 → {out}")
print(f"   备份前已含 ANONYMIZED 的行: {anon_found} (应为0, 若>0说明历史已有污染)")
