"""
MoF Japan JGB 收益率 CSV 抓取器。

数据源：https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/jgbcme.csv
- 英文站文件名是 jgbcme.csv（带 e 后缀，注意 L-2026-05-31-004）
- 日文站是 jgbcm.csv
- 每个交易日 15:00 JST 后更新当日收盘
- 文件覆盖当月 + 历史归档（每月一个文件）

CSV 格式示例：
    Interest Rate (May 2026),,,,
    Date,1Y,2Y,3Y,4Y,5Y,6Y,7Y,8Y,9Y,10Y,15Y,20Y,25Y,30Y,40Y
    2026/5/1,1.073,1.385,...
"""
import csv
import io
import requests
from datetime import date, datetime
from typing import Optional

MOF_JGB_URL = "https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/jgbcme.csv"

# 项目需要的期限（A3 / B4 字段）
TARGET_MATURITIES = ["1Y", "2Y", "3Y", "5Y", "10Y", "30Y"]


def fetch_jgb_all() -> list[dict]:
    """
    拉取 MoF 当月全部 JGB 收益率数据。

    Returns:
        [{"date": "2026-05-28", "1Y": 1.12, "2Y": 1.43, ..., "10Y": 2.69, "30Y": 3.99}, ...]
    """
    r = requests.get(MOF_JGB_URL, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    # MoF CSV 是 UTF-8（可能含 BOM）
    text = r.content.decode("utf-8-sig", errors="ignore")

    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    # 找到 header 行（第一列是 "Date"）
    header_idx = next(i for i, row in enumerate(rows) if row and row[0].strip() == "Date")
    header = [c.strip() for c in rows[header_idx]]

    out = []
    for row in rows[header_idx + 1:]:
        if not row or not row[0].strip():
            continue
        date_str = row[0].strip()
        # MoF 用 2026/5/1 格式
        try:
            d = datetime.strptime(date_str, "%Y/%m/%d").date()
        except ValueError:
            continue
        record = {"date": d.isoformat()}
        for col_idx, col_name in enumerate(header):
            if col_name in TARGET_MATURITIES and col_idx < len(row):
                val_str = row[col_idx].strip()
                if val_str:
                    try:
                        record[col_name] = float(val_str)
                    except ValueError:
                        record[col_name] = None
        out.append(record)
    return out


def fetch_jgb_latest() -> Optional[dict]:
    """获取最新一日 JGB 全期限收益率。"""
    all_data = fetch_jgb_all()
    return all_data[-1] if all_data else None


def fetch_10y_history(days: int = 90) -> list[dict]:
    """
    拉取最近 N 天的 10Y JGB（用于 B4_JGB_10Y_3MonthTrend）。

    注意：MoF 单文件只含当月，跨月需多次调用。本函数仅返回当月数据。
    Hermes 可循环调用历史月文件 URL 拼起来：
      https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/historical/jgbcme_YYYYMM.csv
    """
    all_data = fetch_jgb_all()
    return [{"date": r["date"], "10Y_JGB_pct": r.get("10Y")} for r in all_data[-days:]]


if __name__ == "__main__":
    import json
    latest = fetch_jgb_latest()
    print("Latest JGB:")
    print(json.dumps(latest, indent=2, ensure_ascii=False))
