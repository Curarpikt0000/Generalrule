#!/usr/bin/env python3
"""可复用 Notion KOL By Day 写入库。
关键: select option 安全合并(永不覆盖); L2 去重(同KOL同日只一条)。
供 backfill 子 agent 与 daily cron 调用。

CLI:
  python3 notion_writer.py check <kol_name> <date>        # L2 去重检查, 输出 EXISTS/NEW
  python3 notion_writer.py ensure_option <field> <value>  # 安全加 select option
  python3 notion_writer.py write <json_file>              # 写一条记录(json 见下)
write 的 json:
  {"name_title","name_of_kol","kol_or_ib","date","sector","detail_sector",
   "comments","suggestion","bull_bear"}
"""
import json, sys, urllib.request, urllib.error, time

def load_key(name):
    pre = name + "="
    for l in open("config/.env"):
        if l.startswith(pre): return l[len(pre):].strip()
    return ""

TOK = load_key("NOTION_" + "TOKEN")
H = {"Authorization": f"Bearer {TOK}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}
DB = "32347eb5fd3c8087b9c0f409f95f664e"

def api(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=H, method=method)
    for attempt in range(3):
        try:
            return json.load(urllib.request.urlopen(req, timeout=45))
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:200]
            if e.code == 429 and attempt < 2:
                time.sleep(2 * (attempt + 1)); continue
            raise RuntimeError(f"HTTP {e.code}: {msg}")
    raise RuntimeError("retries exhausted")

def get_db():
    return api("GET", f"https://api.notion.com/v1/databases/{DB}")

def ensure_option(field, value):
    """确保 select field 含 value option, 合并式 update(不覆盖)。返回 True 若新增。"""
    db = get_db()
    prop = db["properties"].get(field)
    if not prop or prop["type"] != "select":
        raise RuntimeError(f"{field} 不是 select")
    opts = prop["select"]["options"]
    if any(o["name"] == value for o in opts):
        return False  # 已存在
    new_opts = [{"name": o["name"]} for o in opts] + [{"name": value}]
    api("PATCH", f"https://api.notion.com/v1/databases/{DB}",
        {"properties": {field: {"select": {"options": new_opts}}}})
    return True

def check_dup(kol_name, date):
    """L2: 同 KOL 同日是否已有记录。返回 page_id 或 None。"""
    body = {"filter": {"and": [
        {"property": "Name of KOL", "select": {"equals": kol_name}},
        {"property": "Date", "date": {"equals": date}},
    ]}, "page_size": 1}
    r = api("POST", f"https://api.notion.com/v1/databases/{DB}/query", body)
    res = r.get("results", [])
    return res[0]["id"] if res else None

def write_record(rec):
    """写一条 KOL By Day。自动确保 select options 存在 + L2 去重。"""
    name = rec["name_of_kol"]
    date = rec["date"]
    dup = check_dup(name, date)
    if dup:
        return {"status": "SKIP_DUP", "page_id": dup}
    # 确保 select options
    ensure_option("Name of KOL", name)
    if rec.get("kol_or_ib"):
        ensure_option("KOL or IB View", rec["kol_or_ib"])
    if rec.get("sector"):
        ensure_option("Sector", rec["sector"])
    if rec.get("detail_sector"):
        ensure_option("Detail Sector", rec["detail_sector"])
    props = {
        "Name": {"title": [{"text": {"content": rec["name_title"][:200]}}]},
        "Name of KOL": {"select": {"name": name}},
        "Date": {"date": {"start": date}},
    }
    if rec.get("kol_or_ib"): props["KOL or IB View"] = {"select": {"name": rec["kol_or_ib"]}}
    if rec.get("sector"): props["Sector"] = {"select": {"name": rec["sector"]}}
    if rec.get("detail_sector"): props["Detail Sector"] = {"select": {"name": rec["detail_sector"]}}
    if rec.get("comments"): props["Comments"] = {"rich_text": [{"text": {"content": rec["comments"][:2000]}}]}
    if rec.get("suggestion"): props["Suggestion"] = {"rich_text": [{"text": {"content": rec["suggestion"][:2000]}}]}
    if rec.get("bull_bear"): props["多空标的"] = {"rich_text": [{"text": {"content": rec["bull_bear"][:2000]}}]}
    if rec.get("direction_detail"): props["方向明细"] = {"rich_text": [{"text": {"content": rec["direction_detail"][:2000]}}]}
    if rec.get("main_direction"):
        ensure_option("主导方向", rec["main_direction"])
        props["主导方向"] = {"select": {"name": rec["main_direction"]}}
    # === 防脱敏污染护栏 ===
    # 采集子 agent 经手原文时, redactor 会把人名脱敏成 ANONYMIZED_PERSON_X(显示层),
    # 若把脱敏占位符当真名写进 Notion 就是永久污染。写入前全字段拦截, 含 ANONYMIZED 拒写。
    _blob = json.dumps(props, ensure_ascii=False)
    if "ANONYMIZED" in _blob:
        import sys as _sys
        print(f"REJECT: 待写记录含 ANONYMIZED 脱敏占位符, 拒写防污染。"
              f"name={name!r} date={date!r}", file=_sys.stderr)
        return {"status": "REJECTED_ANONYMIZED", "name": name, "date": date}
    r = api("POST", "https://api.notion.com/v1/pages",
            {"parent": {"database_id": DB}, "properties": props})
    return {"status": "CREATED", "page_id": r["id"]}

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "check":
        print("EXISTS" if check_dup(sys.argv[2], sys.argv[3]) else "NEW")
    elif cmd == "ensure_option":
        print("ADDED" if ensure_option(sys.argv[2], sys.argv[3]) else "EXISTS")
    elif cmd == "write":
        rec = json.load(open(sys.argv[2]))
        print(json.dumps(write_record(rec), ensure_ascii=False))
    else:
        print("unknown cmd"); sys.exit(1)
