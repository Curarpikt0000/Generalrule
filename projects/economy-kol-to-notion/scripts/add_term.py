#!/usr/bin/env python3
"""期限(短期/长期)回填 I/O 工具 —— 配合子 agent 判读用。
判读由 agent 做(LLM 真读懂语言意味), 本脚本只管数据进出 Notion, 不内嵌判读逻辑。

用法:
  python3 add_term.py count                          # 统计 leg 期限覆盖率
  python3 add_term.py list <kol_id_or_name> [limit]  # 拉某 KOL 缺期限的腿(出题)
  python3 add_term.py list-kols                       # 列出所有有缺期限腿的 KOL + 缺口数
  python3 add_term.py write <page_id> <legs_json>     # 回写整行的方向明细(已含期限键)
  python3 add_term.py verify <kol_id_or_name>         # 读回验证某 KOL 是否全部补齐

铁律: 只给 leg 加/改 `期限` 键, 其他字段(标的/板块/方向)原样不动; 已有期限的 leg 跳过。
"""
import json, sys, urllib.request, urllib.error

def load_key(name):
    pre = name + "="
    for l in open("config/.env"):
        if l.startswith(pre):
            return l[len(pre):].strip()
    return ""

TOKEN = load_key("NOTION_TOKEN")
DB = "32347eb5fd3c8087b9c0f409f95f664e"  # By Day database_id
H = {"Authorization": f"Bearer {TOKEN}", "Notion-Version": "2022-06-28",
     "Content-Type": "application/json"}

def _txt(p):
    if not p: return ""
    rt = p.get("rich_text") or p.get("title") or []
    return "".join(x.get("plain_text", "") for x in rt)

def _query_all():
    rows = []; cursor = None
    while True:
        body = {"page_size": 100}
        if cursor: body["start_cursor"] = cursor
        req = urllib.request.Request(f"https://api.notion.com/v1/databases/{DB}/query",
            data=json.dumps(body).encode(), headers=H, method="POST")
        d = json.load(urllib.request.urlopen(req, timeout=60))
        rows += d["results"]
        if not d.get("has_more"): break
        cursor = d["next_cursor"]
    return rows

def _kol_of(P):
    p = P.get("Name of KOL", {}) or P.get("KOL", {})
    if p.get("type") == "select" or p.get("select") is not None:
        return (p.get("select") or {}).get("name", "") or ""
    return _txt(p)

def _date_of(P):
    dp = P.get("Date", {})
    return dp.get("date", {}).get("start", "") if dp.get("date") else ""

def _legs_of(P):
    md = _txt(P.get("方向明细", {})).strip()
    if not md: return None
    try:
        legs = json.loads(md)
        return legs if isinstance(legs, list) else None
    except Exception:
        return None

def _need_term(leg):
    return leg.get("期限") not in ("短期", "长期")

def count():
    rows = _query_all()
    total_legs = with_term = 0
    short = long = 0
    for r in rows:
        legs = _legs_of(r["properties"]) or []
        for lg in legs:
            total_legs += 1
            t = lg.get("期限")
            if t in ("短期", "长期"):
                with_term += 1
                if t == "短期": short += 1
                else: long += 1
    print(json.dumps({"total_legs": total_legs, "with_term": with_term,
        "short": short, "long": long, "remaining": total_legs - with_term},
        ensure_ascii=False))

def list_kols():
    rows = _query_all()
    gap = {}
    for r in rows:
        P = r["properties"]
        kol = _kol_of(P)
        legs = _legs_of(P) or []
        n = sum(1 for lg in legs if _need_term(lg))
        if n:
            gap[kol] = gap.get(kol, 0) + n
    for kol, n in sorted(gap.items(), key=lambda x: -x[1]):
        print(f"{n}\t{kol}")
    print(f"# 共 {len(gap)} 个 KOL 有缺期限腿, 合计 {sum(gap.values())} 腿", file=sys.stderr)

def list_legs(kol_q, limit=200):
    rows = _query_all()
    out = []
    for r in rows:
        P = r["properties"]
        kol = _kol_of(P)
        if kol_q.lower() not in kol.lower():
            continue
        legs = _legs_of(P)
        if not legs: continue
        if not any(_need_term(lg) for lg in legs):
            continue  # 该行全部已带期限, 跳过
        out.append({
            "page_id": r["id"],
            "kol": kol,
            "date": _date_of(P),
            "title": _txt(P.get("Name", {})),
            "comments": _txt(P.get("Comments", {})),
            "legs": legs,  # 原样给出, 含已有期限的腿(agent 只补缺的)
        })
        if len(out) >= limit: break
    print(json.dumps(out, ensure_ascii=False, indent=2))

def _read_legs(page_id):
    """脚本自己 urllib 读该行真实 leg(真字节, 不经 agent)。"""
    req = urllib.request.Request(f"https://api.notion.com/v1/pages/{page_id}", headers=H)
    d = json.load(urllib.request.urlopen(req, timeout=60))
    return _legs_of(d["properties"])

def apply_terms(page_id, terms_json):
    """安全写回 —— 防脱敏污染的核心。
    terms_json = agent 判读输出, 形如 ["短期","长期",...] 或 [{"i":0,"期限":"短期"},...]
      仅是【期限标签】, 不含任何原文(标的/板块/方向/人名)。
    脚本自己重读该行真实 leg(真字节), 把期限合并进去再写。agent 永不经手原文。
    多重校验: leg 数一致 + 标的/板块/方向逐字段不变 + 无 ANONYMIZED, 否则拒写。"""
    terms = json.loads(terms_json) if isinstance(terms_json, str) else terms_json
    # 归一化为按索引的期限列表
    if terms and isinstance(terms[0], dict):
        term_by_i = {t["i"]: t["期限"] for t in terms}
    else:
        term_by_i = {i: t for i, t in enumerate(terms)}

    real = _read_legs(page_id)
    if real is None:
        print(f"SKIP {page_id[:8]}: 无方向明细", file=sys.stderr); return False

    new_legs = []
    for i, leg in enumerate(real):
        nl = dict(leg)  # 复制真 leg(真字节)
        if nl.get("期限") not in ("短期", "长期"):  # 已有期限的不动
            t = term_by_i.get(i)
            if t in ("短期", "长期"):
                nl["期限"] = t
        new_legs.append(nl)

    # ── 多重校验 ──
    if len(new_legs) != len(real):
        print(f"REJECT {page_id[:8]}: leg 数变化 {len(real)}→{len(new_legs)}", file=sys.stderr); return False
    for a, b in zip(real, new_legs):
        for k in ("标的", "板块", "方向"):
            if a.get(k) != b.get(k):
                print(f"REJECT {page_id[:8]}: 字段[{k}]被改 {a.get(k)!r}→{b.get(k)!r}", file=sys.stderr); return False
    detail = json.dumps(new_legs, ensure_ascii=False)
    if "ANONYMIZED" in detail:
        print(f"REJECT {page_id[:8]}: 含 ANONYMIZED, 拒写(防污染)", file=sys.stderr); return False

    body = {"properties": {"方向明细": {"rich_text": [{"type": "text",
        "text": {"content": detail[:1990]}}]}}}
    req = urllib.request.Request(f"https://api.notion.com/v1/pages/{page_id}",
        data=json.dumps(body).encode(), headers=H, method="PATCH")
    urllib.request.urlopen(req, timeout=60)

    # ── 写后读回验证 ──
    back = _read_legs(page_id)
    if back is None or len(back) != len(real):
        print(f"WARN {page_id[:8]}: 读回 leg 数异常", file=sys.stderr); return False
    if "ANONYMIZED" in json.dumps(back, ensure_ascii=False):
        print(f"DANGER {page_id[:8]}: 读回含 ANONYMIZED! 应 rewind", file=sys.stderr); return False
    termed = sum(1 for lg in back if lg.get("期限") in ("短期", "长期"))
    print(f"OK {page_id[:8]} {termed}/{len(back)} 腿带期限")
    return True

def write_row(page_id, legs_json):
    """[旧/危险] 整行覆盖写回。保留供兼容, 但大批量请用 apply_terms(只传标签)。"""
    legs = json.loads(legs_json) if isinstance(legs_json, str) else legs_json
    detail = json.dumps(legs, ensure_ascii=False)
    if "ANONYMIZED" in detail:
        print(f"REJECT {page_id[:8]}: 含 ANONYMIZED, 拒写", file=sys.stderr); return False
    body = {"properties": {"方向明细": {"rich_text": [{"type": "text",
        "text": {"content": detail[:1990]}}]}}}
    req = urllib.request.Request(f"https://api.notion.com/v1/pages/{page_id}",
        data=json.dumps(body).encode(), headers=H, method="PATCH")
    urllib.request.urlopen(req, timeout=60)
    print(f"OK {page_id[:8]} {len(legs)} legs")

def verify(kol_q):
    rows = _query_all()
    rem = 0; rows_n = 0
    for r in rows:
        P = r["properties"]
        if kol_q.lower() not in _kol_of(P).lower(): continue
        legs = _legs_of(P)
        if not legs: continue
        rows_n += 1
        rem += sum(1 for lg in legs if _need_term(lg))
    print(json.dumps({"kol": kol_q, "rows": rows_n, "remaining_legs": rem},
        ensure_ascii=False))

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "count"
    if cmd == "count": count()
    elif cmd == "list-kols": list_kols()
    elif cmd == "list": list_legs(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 200)
    elif cmd == "write": write_row(sys.argv[2], sys.argv[3])
    elif cmd == "apply": apply_terms(sys.argv[2], sys.argv[3])
    elif cmd == "verify": verify(sys.argv[2])
    else: print("unknown cmd", file=sys.stderr); sys.exit(1)
