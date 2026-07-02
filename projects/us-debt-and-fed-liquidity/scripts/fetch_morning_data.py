"""早间美债 + Fed 流动性数据抓取脚本"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scrapers.fred_client import fetch_series, SERIES
from config import FRED_API_KEY

# 需要拉取的序列
MORNING_SERIES = [
    ("UST_1Y", "DGS1"),
    ("UST_2Y", "DGS2"),
    ("UST_5Y", "DGS5"),
    ("UST_10Y", "DGS10"),
    ("UST_30Y", "DGS30"),
    ("SOFR", "SOFR"),
    ("EFFR", "EFFR"),
    ("IORB", "IORB"),
    ("ON_RRP", "RRPONTSYD"),
    ("TGA", "WTREGEN"),
    ("RESERVES", "WRESBAL"),
]

results = {}
for alias, sid in MORNING_SERIES:
    try:
        data = fetch_series(sid, days_back=35)
        results[alias] = data
        print(f"OK {alias} ({sid}): {len(data)} obs", file=sys.stderr)
    except Exception as e:
        results[alias] = {"error": str(e)}
        print(f"ERR {alias} ({sid}): {e}", file=sys.stderr)

print(json.dumps(results, indent=2, ensure_ascii=False))
