"""
月度三大央行资产负债表抓取（PBoC + BoJ + Fed）。

Workflow 07 的纯数据层。输出 dict 供 caller 写入 Notion B1。

数据源：
- PBoC: 货币当局资产负债表 HTM（GBK 编码静态表格）
- BoJ: FRED JPNASSETS（BoJ Total Assets, 100 Million Yen, 月末值）
- Fed: FRED H.4.1 序列月末值

策略：
- PBoC 本月若未更新 → 沿用上月（从 HTM 表格中取最新非空列）
- BoJ FRED 默认月末，直接取上月
- Fed 取 H.4.1 上月最后一周值
"""
import json
import re
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import FRED_API_KEY, FRED_BASE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
}

# ===== PBoC =====

PBOC_INDEX_URL = "http://www.pbc.gov.cn/diaochatongjisi/116219/116319/2026ntjsj/hbtjgl/index.html"


def fetch_pboc_bs_index() -> Optional[str]:
    """从货币统计概览页面找到最新货币当局资产负债表 HTM 的 URL

    PBoC 页面 GBK 编码导致中文乱码，用英文标签 "Monetary Authority" 或 "Balance Sheet" 匹配。
    父元素 context 中包含英文标签即说明该行是货币当局资产负债表。
    """
    try:
        r = requests.get(PBOC_INDEX_URL, headers=HEADERS, timeout=20)
        r.encoding = "gbk"
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "htm" not in href.lower() or "attachDir" not in href:
                continue
            parent = a.find_parent("tr") or a.find_parent("li") or a.parent
            if parent:
                context = parent.get_text(strip=True)
                if "Monetary Authority" in context or "Balance Sheet" in context:
                    if href.startswith("/"):
                        return "http://www.pbc.gov.cn" + href
                    return href
        return None
    except Exception as e:
        print(f"[PBoC] Error fetching index: {e}", file=sys.stderr)
        return None


def parse_pboc_htm(url: str) -> Optional[dict]:
    """
    解析货币当局资产负债表 HTML 表格，提取最新月度数据。

    表格 HTML 结构（已通过实际测试确认）：
    Row 5: Item | 2026.01 | 2026.02 | ... | 2026.12
    Row 7: Foreign Assets | 226843.32 | ...
    Row 11: Claims on Government | ...
    Row 13: Claims on Other Depository Corporations | ...
    Row 17: Total Assets | ...
    Row 18: Reserve Money | ...
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.encoding = "gbk"
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        table = soup.find("table")
        if not table:
            print("[PBoC] No table found", file=sys.stderr)
            return None

        rows = table.find_all("tr")
        if len(rows) < 20:
            print(f"[PBoC] Too few rows: {len(rows)}", file=sys.stderr)
            return None

        month_labels = None
        for row in rows:
            cols = row.find_all(["td", "th"])
            for c in cols:
                text = c.get_text(strip=True)
                if re.match(r"2026\.\d{2}", text):
                    if month_labels is None:
                        month_labels = []
                    month_labels.append(text)
            if month_labels is not None:
                break

        if not month_labels:
            print("[PBoC] No month columns found", file=sys.stderr)
            return None

        # Map row English label → data position in the table
        # Based on actual HTML: Row 17 = Total Assets, Row 18 = Reserve Money,
        # Row 11 = Claims on Government, Row 13 = Claims on Other Depository Corps
        row_map = {
            "Total Assets": 17,
            "Reserve Money": 18,
            "Claims on Government": 11,
            "Claims on Other Depository Corporations": 13,
        }

        def get_row_values(row_idx: int) -> list[str]:
            if row_idx >= len(rows):
                return []
            row = rows[row_idx]
            cells = row.find_all(["td", "th"])
            values = []
            for c in cells:
                text = c.get_text(strip=True)
                if re.match(r"[\d,]+\.?\d*$", text):
                    values.append(text.replace(",", ""))
            return values

        # Extract data for each field
        data = {}
        for label_key, field_name in [
            ("total assets", "total_assets"),
            ("reserve money", "reserve_money"),
            ("claims on government", "claims_on_government"),
            ("other depository corporations", "claims_on_depository"),
        ]:
            # Find the row by iterating and matching label (case-insensitive, handle \\r\\n)
            found_values = None
            for i, row in enumerate(rows):
                # Use normalized text (remove \\r\\n, collapse whitespace)
                raw_text = row.get_text(" ", strip=True)
                normalized = " ".join(raw_text.split())  # normalize all whitespace
                if label_key in normalized.lower():
                    # Exclude false positives for Reserve Money
                    if label_key == "reserve money" and "excluded" in normalized.lower():
                        continue
                    cells = row.find_all(["td", "th"])
                    values = []
                    for c in cells:
                        text = c.get_text(strip=True)
                        if re.match(r"^[\d,]+\.?\d*$", text):
                            values.append(text.replace(",", ""))
                    if values:
                        found_values = values
                        break

            if found_values:
                data[field_name] = found_values

        if not data:
            print("[PBoC] No data rows found", file=sys.stderr)
            return None

        # Find latest non-empty column index across all data rows
        latest_col = -1
        for field, vals in data.items():
            for i, v in enumerate(vals):
                if v and float(v) > 0:
                    if i > latest_col:
                        latest_col = i

        if latest_col < 0 or latest_col >= len(month_labels):
            print("[PBoC] No non-empty data found", file=sys.stderr)
            return None

        latest_month_label = month_labels[latest_col]
        month_iso = latest_month_label.replace(".", "-")

        result = {
            "央行": "PBoC",
            "month": month_iso,
            "total_assets": round(float(data.get("total_assets", ["0"])[latest_col]), 2),
            "reserve_money": round(float(data.get("reserve_money", ["0"])[latest_col]), 2),
            "claims_on_government": round(float(data.get("claims_on_government", ["0"])[latest_col]), 2),
            "claims_on_depository": round(float(data.get("claims_on_depository", ["0"])[latest_col]), 2),
            "data_source_url": url,
        }

        return result

    except Exception as e:
        print(f"[PBoC] Parse error: {e}", file=sys.stderr)
        return None


# ===== BoJ (via FRED JPNASSETS) =====

BOJ_ASSETS_SERIES = "JPNASSETS"  # Bank of Japan: Total Assets for Japan, 100 Million Yen


def fetch_boj_monthly() -> Optional[dict]:
    """
    从 FRED 获取 BoJ 总资产月末值。
    JPNASSETS: 100 Million Yen, Monthly, End of Period.

    2026-05: 6,643,630 (100M Yen) = 664.363 兆 JPY
    USD value = 664.363 / USDJPY 兆 USD
    """
    today = date.today()
    prev_month_end = today.replace(day=1) - timedelta(days=1)
    prev_month = prev_month_end.strftime("%Y-%m")

    start = (today - timedelta(days=400)).isoformat()
    params = {
        "series_id": BOJ_ASSETS_SERIES,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start,
        "observation_end": today.isoformat(),
        "sort_order": "desc",
        "limit": 60,
    }
    try:
        r = requests.get(FRED_BASE, params=params, timeout=15)
        time.sleep(2.0)
        if r.status_code == 429:
            time.sleep(30)
            r = requests.get(FRED_BASE, params=params, timeout=15)
            time.sleep(2.0)
        r.raise_for_status()

        obs = r.json().get("observations", [])
        monthly = {}
        for o in obs:
            if o["value"] == ".":
                continue
            d = o["date"]
            month_key = d[:7]
            # JPNASSETS is monthly end-of-period, values are month-first-day-indexed
            # e.g. 2026-05-01 = May 2026
            monthly[month_key] = float(o["value"])

        if prev_month in monthly:
            return {
                "央行": "BoJ",
                "month": prev_month,
                "total_assets_100m_jpy": monthly[prev_month],
                "data_source_url": "https://fred.stlouisfed.org/series/JPNASSETS",
            }
        # Fallback: try earlier months
        for m in sorted(monthly.keys(), reverse=True):
            if m < prev_month:
                return {
                    "央行": "BoJ",
                    "month": m,
                    "total_assets_100m_jpy": monthly[m],
                    "data_source_url": "https://fred.stlouisfed.org/series/JPNASSETS",
                }

        print("[BoJ] No data found", file=sys.stderr)
        return None

    except Exception as e:
        print(f"[BoJ] Error: {e}", file=sys.stderr)
        return None


# ===== Fed (month-end via FRED) =====

FRED_FED_SERIES = {
    "WALCL": "Total_Assets",
    "WSHOTSL": "Treasuries",
    "WSHOMCB": "MBS",
    "WRESBAL": "Reserve_Balances",
    "RRPONTSYD": "ON_RRP",
    "WTREGEN": "TGA",
    "WCURCIR": "Currency",
}


def fetch_fed_monthly_end() -> Optional[dict]:
    """取 Fed 资产负债表上一个月的最后观测值。"""
    today = date.today()
    prev_month_end = today.replace(day=1) - timedelta(days=1)
    prev_month = prev_month_end.strftime("%Y-%m")

    start = (today - timedelta(days=120)).isoformat()
    result = {
        "央行": "Fed",
        "month": prev_month,
        "data_source_url": "https://fred.stlouisfed.org/releases/title?rid=32",
    }

    for series_id, label in FRED_FED_SERIES.items():
        params = {
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "observation_start": start,
            "observation_end": today.isoformat(),
            "sort_order": "desc",
            "limit": 30,
        }
        try:
            r = requests.get(FRED_BASE, params=params, timeout=15)
            time.sleep(2.0)
            if r.status_code == 429:
                time.sleep(30)
                r = requests.get(FRED_BASE, params=params, timeout=15)
                time.sleep(2.0)
            r.raise_for_status()

            obs = r.json().get("observations", [])
            # Group by month, take last value of each month
            monthly = {}
            for o in obs:
                if o["value"] == ".":
                    continue
                d = o["date"]
                month_key = d[:7]
                monthly[month_key] = float(o["value"])

            # Find the requested month
            if prev_month in monthly:
                result[label] = monthly[prev_month]
            else:
                # Try the month before
                fallback = (prev_month_end - timedelta(days=35)).strftime("%Y-%m")
                result[label] = monthly.get(fallback, None)
        except Exception as e:
            print(f"[Fed] {series_id}: {e}", file=sys.stderr)
            result[label] = None

    return result


# ===== FX Rates =====


def fetch_fx_rates() -> tuple:
    """获取 USD/JPY 和 USD/CNY 汇率。"""
    usd_jpy = None
    usd_cny = None

    for sid, name in [("DEXJPUS", "USD/JPY"), ("DEXCHUS", "USD/CNY")]:
        params = {
            "series_id": sid,
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 3,
        }
        try:
            r = requests.get(FRED_BASE, params=params, timeout=15)
            time.sleep(2.0)
            if r.status_code == 200:
                obs = r.json().get("observations", [])
                for o in obs:
                    if o["value"] != ".":
                        val = float(o["value"])
                        if name == "USD/JPY":
                            usd_jpy = val
                        else:
                            usd_cny = val
                        break
        except Exception:
            pass

    return usd_jpy or 144.0, usd_cny or 7.25


# ===== Main =====


def cny_100m_to_usd_t(cny_100m: float, usd_cny: float = 7.25) -> float:
    """亿元 → 万亿美元。1 亿 = 100M, 1 万亿 USD = 10^12, 汇率 CNY/USD"""
    # cny_100m is in 亿元 (100M CNY)
    # 1 亿元 = 1e8 CNY
    # USD = CNY_100m * 1e8 / USD_CNY
    # Trillions = (CNY_100m * 1e8) / (USD_CNY * 1e12) = CNY_100m / (USD_CNY * 10000)
    return round(cny_100m / (usd_cny * 10000), 2)


def jpy_100m_to_usd_t(jpy_100m: float, usd_jpy: float = 144.0) -> float:
    """100 Million Yen → 万亿美元"""
    # jpy_100m: value in 100 Million Yen
    # USD = jpy_100m * 100M / USDJPY
    # Trillions = jpy_100m * 1e8 / (USDJPY * 1e12) = jpy_100m / (USDJPY * 10000)
    return round(jpy_100m / (usd_jpy * 10000), 2)


def fed_to_usd_t(value: float) -> float:
    """FRED Fed series values are in Millions USD. Convert to Trillions USD."""
    # WALCL=6709505 means $6,709,505 million = $6.71 trillion
    return round(value / 1_000_000, 2)


def main() -> dict:
    """主函数：返回三大央行数据 dict。"""
    results = {}
    usd_jpy, usd_cny = fetch_fx_rates()
    print(f"[FX] USD/JPY={usd_jpy}, USD/CNY={usd_cny}", file=sys.stderr)

    # 1. PBoC
    print("=== Fetching PBoC ===", file=sys.stderr)
    pboc_url = fetch_pboc_bs_index()
    if pboc_url:
        print(f"[PBoC] HTM: {pboc_url}", file=sys.stderr)
        pboc_data = parse_pboc_htm(pboc_url)
        if pboc_data:
            pboc_data["total_assets_usd_t"] = cny_100m_to_usd_t(pboc_data["total_assets"], usd_cny)
            results["PBoC"] = pboc_data
            print(f"[PBoC] Month={pboc_data['month']}, Assets={pboc_data['total_assets']}亿CNY / {pboc_data['total_assets_usd_t']}T USD", file=sys.stderr)
        else:
            print("[PBoC] Failed to parse", file=sys.stderr)
    else:
        print("[PBoC] No HTM found", file=sys.stderr)

    # 2. BoJ
    print("=== Fetching BoJ ===", file=sys.stderr)
    boj_data = fetch_boj_monthly()
    if boj_data:
        boj_data["total_assets_usd_t"] = jpy_100m_to_usd_t(boj_data["total_assets_100m_jpy"], usd_jpy)
        # JPNASSETS: 6,643,630 (100M Yen)
        # In 兆 (trillion JPY): 6,643,630 * 100M / 1e12 = 6,643,630 / 10000 = 664.363 兆
        boj_data["total_assets_trillion_jpy"] = round(boj_data["total_assets_100m_jpy"] / 10000, 2)
        results["BoJ"] = boj_data
        print(f"[BoJ] Month={boj_data['month']}, Assets={boj_data['total_assets_trillion_jpy']}兆JPY / {boj_data['total_assets_usd_t']}T USD", file=sys.stderr)
    else:
        print("[BoJ] Failed", file=sys.stderr)

    # 3. Fed
    print("=== Fetching Fed ===", file=sys.stderr)
    fed_data = fetch_fed_monthly_end()
    if fed_data:
        # Convert millions to trillions
        for label in ["Total_Assets", "Treasuries", "MBS", "Reserve_Balances"]:
            if label in fed_data and fed_data[label] is not None:
                fed_data[f"{label}_T"] = fed_to_usd_t(fed_data[label])
        for label in ["ON_RRP", "TGA"]:
            if label in fed_data and fed_data[label] is not None:
                fed_data[f"{label}_B"] = round(fed_data[label] / 1000, 2)  # Millions → Billions
        if "Currency" in fed_data and fed_data["Currency"] is not None:
            fed_data["Currency_B"] = round(fed_data["Currency"] / 1000, 2)

        results["Fed"] = fed_data
        total_t = fed_to_usd_t(fed_data.get("Total_Assets", 0))
        print(f"[Fed] Month={fed_data['month']}, Total Assets={total_t}T USD", file=sys.stderr)

    return results


if __name__ == "__main__":
    result = main()
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
