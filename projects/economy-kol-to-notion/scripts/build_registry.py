#!/usr/bin/env python3
"""Step 1: 从 KOL List raw 生成 kol_registry.json。
规则:
- 删 3 个纯机构: Goldman Sachs / Morgan Stanley / Citi / UBS
- 去重: 同名 KOL 只保留一条(保留编号大的=较新)
- sector 映射 List 中文"领域" -> 7 标准 sector
- 保留原始背景/方向(丰富, 后续 Step3 还会再扩充)
"""
import json, re, unicodedata

raw = json.load(open("data/kol_list_raw.json"))

DROP_INSTITUTIONS = {"Goldman Sachs", "Morgan Stanley", "Citi / UBS"}

# 领域(中文自由文本) -> 标准 sector. 按关键词优先级匹配。
def map_sector(domain, name):
    d = domain or ""
    # 手工修正(Chao 批准): 外汇/宏观为主的归 Macro; 大宗商品专家归 Energy & Commodities
    MANUAL = {
        "Marc Chandler": "Macro",
        "Alex Kuptsikevich": "Macro",
        "Jeff Currie": "Energy & Commodities",
    }
    if name in MANUAL:
        return MANUAL[name]
    if "国债" in d or "债券" in d or "利率" in d:
        return "Government Debt"
    if "贵金属" in d or "商品周期" in d:
        return "Precious Metals"
    if "能源" in d or "资源" in d:
        return "Energy & Commodities"
    if "交易" in d or "微观结构" in d:
        return "Precious Metals"  # 这些多是金银交易员
    if "科技" in d or "未来" in d:
        # 细分: 加密 vs 股权
        if name in ("Michael Saylor", "Raoul Pal"):
            return "Crypto"
        return "Equities"
    if "预测" in d:
        return "Alternative"
    if "股权" in d or "股指" in d or "股票" in d:
        return "Equities"
    if "宏观" in d or "货币" in d or "外汇" in d:
        return "Macro"
    return "Macro"  # 兜底

def make_id(name):
    # 去掉引号/括号/中文别名, snake_case
    n = re.sub(r'["\u201c\u201d]', '', name)
    n = re.sub(r'\([^)]*\)', '', n)          # 去括号内容
    n = re.sub(r'[（）].*', '', n)            # 去中文括号及后
    n = n.split('/')[0].strip()               # Doomberg / Kuppy -> Doomberg
    n = n.strip()
    # 中文名特殊处理
    if re.search(r'[\u4e00-\u9fff]', n):
        ascii_part = re.sub(r'[\u4e00-\u9fff].*', '', n).strip()
        n = ascii_part if ascii_part else "kol_" + str(abs(hash(name)) % 100000)
    n = n.lower()
    n = re.sub(r'[^a-z0-9]+', '_', n).strip('_')
    return n or ("kol_" + str(abs(hash(name)) % 100000))

# 去重: 按显示名归并, 保留编号最大的
seen = {}
for r in raw:
    name = r["KOL"].strip()
    if name in DROP_INSTITUTIONS:
        continue
    try:
        num = int(r["编号"])
    except:
        num = 0
    if name not in seen or num > seen[name]["_num"]:
        seen[name] = {**r, "_num": num}

kols = []
for name, r in sorted(seen.items(), key=lambda x: -x[1]["_num"]):
    display = re.sub(r'\s*\(新\)\s*', '', name).strip()   # 去掉 "(新)" 标记
    sector = map_sector(r["领域"], display)
    kols.append({
        "id": make_id(display),
        "display_name": display,
        "notion_select_name": display,
        "domain": r["领域"],
        "sector": sector,
        "detail_sector": r["领域"],   # 暂用原领域, 后续可细化
        "kol_or_ib": "KOL",
        "institution": r["背景"],
        "x_handle": "",
        "search_terms": [display],     # 起步只放名字, Step2 回溯时扩充
        "active": True,
        "added_date": "2026-06-20",
        "notion_list_page_id": r["page_id"],
        "list_num": r["编号"],
        "bio": r["背景"],
        "focus": r["方向"],
    })

registry = {
    "_comment": "KOL 主注册表 — SSOT, 唯一权威源=Notion KOL List DB. 只增不减.",
    "_last_updated": "2026-06-20",
    "_source": "Notion KOL List DB 35947eb5fd3c800db852cef31f9de6a5",
    "_dropped_institutions": sorted(DROP_INSTITUTIONS),
    "_count": len(kols),
    "kols": kols,
}
json.dump(registry, open("data/kol_registry.json", "w"), ensure_ascii=False, indent=2)

# 报告
from collections import Counter
print(f"原始 {len(raw)} 行 -> 去机构/去重后 {len(kols)} 个 KOL")
print(f"删除机构: {sorted(DROP_INSTITUTIONS)}")
print(f"\nSector 分布:")
for s, c in Counter(k["sector"] for k in kols).most_common():
    print(f"  {s}: {c}")
print(f"\nID 重复检查: ", end="")
ids = [k["id"] for k in kols]
dups = [i for i in set(ids) if ids.count(i) > 1]
print("有重复! " + str(dups) if dups else "无重复 OK")
print(f"\n抽样(前8个):")
for k in kols[:8]:
    print(f"  [{k['list_num']}] {k['display_name']} (id={k['id']}) -> {k['sector']} | {k['domain']}")
