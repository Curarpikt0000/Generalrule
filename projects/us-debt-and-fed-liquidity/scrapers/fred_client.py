"""
FRED API 客户端。免费、官方、无需反爬。

L-2026-05-31-005：并发拉多序列触发 429，每次调用后 sleep(2) 是安全的速率。
"""
import time
import requests
from datetime import date, timedelta
from typing import Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import FRED_API_KEY, FRED_BASE

# 单次调用后的强制 sleep（避免 FRED 429）
_RATE_LIMIT_SLEEP_SEC = 2.0


def fetch_series(series_id: str, days_back: int = 35) -> list[dict]:
    """
    拉取 FRED 序列最近 N 天数据。

    Args:
        series_id: 如 "DGS10"、"SOFR"、"WALCL"
        days_back: 拉取最近多少天（默认 35，覆盖周末 + 节假日空白）

    Returns:
        [{"date": "2026-05-30", "value": 4.42}, ...]
        无值的日期跳过（FRED 返回 "."）
    """
    end = date.today()
    start = end - timedelta(days=days_back)
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start.isoformat(),
        "observation_end": end.isoformat(),
    }
    r = requests.get(FRED_BASE, params=params, timeout=15)
    # 速率保护：无论成功/失败都 sleep，避免连续打爆
    time.sleep(_RATE_LIMIT_SLEEP_SEC)
    if r.status_code == 429:
        # 一次重试，等长一些
        time.sleep(30)
        r = requests.get(FRED_BASE, params=params, timeout=15)
        time.sleep(_RATE_LIMIT_SLEEP_SEC)
    r.raise_for_status()
    obs = r.json().get("observations", [])
    out = []
    for o in obs:
        if o["value"] == ".":
            continue
        out.append({"date": o["date"], "value": float(o["value"])})
    return out


def latest_value(series_id: str) -> Optional[dict]:
    """获取最新一个有效观测值。"""
    data = fetch_series(series_id, days_back=14)
    return data[-1] if data else None


# 项目常用序列别名
SERIES = {
    # UST yields
    "UST_1Y": "DGS1",
    "UST_2Y": "DGS2",
    "UST_5Y": "DGS5",
    "UST_10Y": "DGS10",
    "UST_30Y": "DGS30",
    # Fed liquidity
    "SOFR": "SOFR",
    "EFFR": "EFFR",
    "IORB": "IORB",
    "ON_RRP": "RRPONTSYD",
    "RRP_AWARD": "RRPONTSYAWARD",
    "TGA": "WTREGEN",
    "RESERVES": "WRESBAL",
    # Fed balance sheet (weekly)
    "TOTAL_ASSETS": "WALCL",
    "TREASURIES": "WSHOTSL",
    "MBS": "WSHOMCB",
    "CURRENCY": "WCURCIR",
}


def fetch_all_morning() -> dict:
    """早间 08:30 一次性拉取所有美债 + Fed 流动性序列。"""
    out = {}
    for alias, sid in SERIES.items():
        try:
            out[alias] = fetch_series(sid, days_back=35)
        except Exception as e:
            out[alias] = {"error": str(e)}
    return out


if __name__ == "__main__":
    import json
    print(json.dumps(fetch_all_morning(), indent=2, ensure_ascii=False))
