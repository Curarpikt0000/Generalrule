"""Check absolute latest data from FRED for all series"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from scrapers.fred_client import fetch_series, SERIES

check_series = {
    "DGS10": "UST_10Y",
    "DGS2": "UST_2Y",
    "DGS1": "UST_1Y",
    "SOFR": "SOFR",
    "RRPONTSYD": "ON_RRP",
}

for sid, alias in check_series.items():
    data = fetch_series(sid, days_back=5)
    if data and not isinstance(data, dict):
        print(f"{alias} ({sid}): latest={data[-1]['date']} val={data[-1]['value']}")
    else:
        print(f"{alias} ({sid}): error or no data")
