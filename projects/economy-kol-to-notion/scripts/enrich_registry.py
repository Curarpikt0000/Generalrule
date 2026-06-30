#!/usr/bin/env python3
"""Step1.5: 富化 registry — 生成 search_terms + 已知 x_handle 映射。
search_terms 策略: [全名] + [全名+核心资产关键词] + [机构/产品名]
不联网, 基于已有 bio/focus 智能生成。x_handle 用人工已知映射(高频KOL)。
"""
import json, re

reg = json.load(open("data/kol_registry.json"))

# 已知 X handle (高频 KOL, 人工确认的). 其余留空, Step2 回溯时按需补。
KNOWN_X = {
    "Luke Gromen": "@LukeGromen", "Peter Schiff": "@PeterSchiff",
    "Craig Hemke": "@TFMetals", "Vince Lanci": "@VlanciPictures",
    "Ray Dalio": "@RayDalio", "Robert Kiyosaki": "@theRealKiyosaki",
    "Michael Saylor": "@saylor", "Cathie Wood": "@CathieDWood",
    "Raoul Pal": "@RaoulGMI", "Jim Rogers": "@JimRogers1942",
    "Gareth Soloway": "@GarethSoloway", "Keith Neumeyer": "@FirstMajestic",
    "Lawrence Lepard": "@LawrenceLepard", "Lyn Alden": "@LynAldenContact",
    "Jeffrey Gundlach": "@TruthGundlach", "Kyle Bass": "@Jkylebass",
    "Dan Ives": "@DivesTech", "Michael Hartnett": "",
    "Rick Rule": "@RealRickRule", "Jay Martin": "@JayMartinBC",
    "Matthew Piepenburg": "@gold_matterhorn", "Alasdair Macleod": "@MacleodFinance",
    "Larry McDonald": "@Convertbond", "Daniel Ghali": "@DanielGhali",
    "Steve Penny": "@SilverPenny__", "Andy Schectman": "@MilesFranklinCo",
    "Marc Chandler": "@marcmakingsense", "Bob Haberkorn": "",
    "David Hunter": "@DaveHcontrarian", "Dan Loeb": "@DanielSLoeb",
    "David Icke": "@davidicke", "Ronny Stoeferle": "@RonStoeferle",
}

# 资产关键词(按 sector 给搜索词加 context)
SECTOR_KW = {
    "Precious Metals": "gold silver",
    "Macro": "macro dollar fed",
    "Government Debt": "bonds treasury yields",
    "Energy & Commodities": "oil commodities energy",
    "Equities": "stocks equities market",
    "Crypto": "bitcoin crypto",
    "Alternative": "forecast prediction",
}

def institution_keyword(bio):
    # 提取机构/产品名作为第二搜索词 (取 bio 里第一个英文专有名/书名)
    m = re.search(r'([A-Z][A-Za-z0-9&\.\' ]{2,40}?)(?:\s*(?:创始|CEO|合伙|主席|总裁|首席|创办|管理|董事|主编|作者|founder|创始人))', bio)
    if m:
        return m.group(1).strip()
    m = re.search(r'《([^》]+)》', bio)
    if m:
        return m.group(1).strip()
    m = re.search(r'([A-Z][A-Za-z0-9&\.\']{2,}(?:\s+[A-Z][A-Za-z0-9&\.\']{1,}){0,3})', bio)
    return m.group(1).strip() if m else ""

for k in reg["kols"]:
    name = k["display_name"]
    k["x_handle"] = KNOWN_X.get(name, "")
    terms = [name]
    kw = SECTOR_KW.get(k["sector"], "market")
    terms.append(f"{name} {kw}")
    inst = institution_keyword(k.get("bio", ""))
    if inst and inst.lower() not in name.lower():
        terms.append(f"{name} {inst}")
    # 去重保序
    seen = set(); uniq = []
    for t in terms:
        if t not in seen:
            seen.add(t); uniq.append(t)
    k["search_terms"] = uniq

reg["_last_updated"] = "2026-06-20"
json.dump(reg, open("data/kol_registry.json", "w"), ensure_ascii=False, indent=2)

n_x = sum(1 for k in reg["kols"] if k["x_handle"])
print(f"富化完成: {len(reg['kols'])} KOL, 其中 {n_x} 个有已知 x_handle")
print("\n抽样 search_terms:")
for k in reg["kols"][:6]:
    print(f"  {k['display_name']} (x={k['x_handle'] or '-'})")
    for t in k["search_terms"]:
        print(f"      - {t}")
