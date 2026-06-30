#!/usr/bin/env python3
"""每日纯净体检：扫 Notion By Day + 本地 week_backfill 是否有 ANONYMIZED 污染。
watchdog 模式：干净则静默(无输出)，有污染才打印告警(cron 会投递)。"""
import importlib.util, urllib.request, json, glob, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

spec = importlib.util.spec_from_file_location("at", "scripts/add_term.py")
at = importlib.util.module_from_spec(spec)
spec.loader.exec_module(at)
TOKEN, DB, H = at.TOKEN, at.DB, at.H

alerts = []

# 1) 本地数据文件
for f in glob.glob("data/**/*.json", recursive=True):
    n = open(f, "rb").read().count(b"ANONYMIZED")
    if n:
        alerts.append(f"本地 {f}: {n} 处 ANONYMIZED")

# 2) Notion By Day Comments + direction_detail
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

try:
    rows = query_all()
    notion_hits = 0
    for pg in rows:
        blob = json.dumps(pg["properties"], ensure_ascii=False)
        if "ANONYMIZED" in blob:
            notion_hits += 1
    if notion_hits:
        alerts.append(f"Notion By Day: {notion_hits} 行含 ANONYMIZED")
except Exception as e:
    alerts.append(f"Notion 体检失败: {e}")

if alerts:
    print("🔴 KOL 数据脱敏污染告警 (Economy-KOL-to-Notion)")
    for a in alerts:
        print("  -", a)
    print("处理: 见 scripts/fix_weekfiles_names.py / fix_comments_names.py 修复套路")
    sys.exit(0)
# 干净 → 静默(watchdog)
