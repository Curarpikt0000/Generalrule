import json, os, urllib.request

prefix = "NOTION_" + "TOKEN="
tok = ""
for l in open("config/.env"):
    if l.startswith(prefix):
        tok = l[len(prefix):].strip()
H = {"Authorization": f"Bearer {tok}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}
DB_LIST = "35947eb5fd3c800db852cef31f9de6a5"

def query_all(db):
    rows, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor: body["start_cursor"] = cursor
        req = urllib.request.Request(f"https://api.notion.com/v1/databases/{db}/query",
                                     data=json.dumps(body).encode(), headers=H, method="POST")
        r = json.load(urllib.request.urlopen(req, timeout=30))
        rows += r["results"]
        if not r.get("has_more"): break
        cursor = r["next_cursor"]
    return rows

def txt(prop):
    if prop is None: return ""
    t = prop.get("type")
    if t in ("rich_text", "title"):
        return "".join(x.get("plain_text", "") for x in prop[t])
    if t == "select":
        return prop["select"]["name"] if prop["select"] else ""
    return ""

rows = query_all(DB_LIST)
out = []
for row in rows:
    p = row["properties"]
    out.append({
        "编号": txt(p.get("编号")),
        "KOL": txt(p.get("KOL / 机构")),
        "领域": txt(p.get("领域")),
        "背景": txt(p.get("核心背景 / 身份")),
        "方向": txt(p.get("主要分析方向 / 监控维度")),
        "page_id": row["id"],
    })
json.dump(out, open("data/kol_list_raw.json", "w"), ensure_ascii=False, indent=2)
print(f"拉取 {len(out)} 行 KOL List，已存 data/kol_list_raw.json")
print("\n字段完整性抽查(前3行):")
for r in out[:3]:
    print(f"  [{r['编号']}] {r['KOL']}")
    print(f"      领域={r['领域']}")
    print(f"      背景={r['背景'][:80]}")
    print(f"      方向={r['方向'][:80]}")
