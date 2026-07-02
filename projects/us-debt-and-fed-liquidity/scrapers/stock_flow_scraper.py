"""
中日板块资金流抓取（_OLD_CN_JP_SectorFlow_Daily）。

A 股板块：东方财富免费 API（https://push2.eastmoney.com）
- 板块行情：fs=m:90+t:2（行业板块）
- 主力净流入：字段 f62
- 换手率：字段 f8

注意：2026-06-02 更新：东方财富 API 的 diff 字段是 dict 类型（key=str），
不支持旧版 for item in diff 迭代。已修复。

注意：板块代码 BK0473(电子)等旧代码已不在 API 返回中，
已替换为新的分类代码。
"""
import requests
import time
from datetime import date, datetime
from typing import Optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Referer": "https://data.eastmoney.com/",
}

EASTMONEY_BASE = "https://push2.eastmoney.com/api/qt/clist/get"

# Updated sector codes (2026-06-11: verified from live API)
A_SHARE_SECTORS = {
    # 电子 proxy: 电子化学品Ⅱ
    "BK1039": "电子(电子化学品Ⅱ)",
    # 有色金属
    "BK0478": "有色金属",
    # 银行
    "BK0475": "银行",
    # 房地产
    "BK1202": "房地产",
}


def fetch_a_share_sector_flow() -> list[dict]:
    """
    抓取 A 股行业板块当日资金流。
    diff 字段为 dict（key=string index），不是 list。
    银行板块净流出时排在很后面，需遍历多页。
    """
    today = date.today().isoformat()
    out = []
    seen = set()

    for page in range(1, 7):  # 最多 6 页 × 100 = 600 够覆盖 496 板块
        params = {
            "pn": page,
            "pz": 100,
            "fid": "f12",
            "po": 1,
            "fs": "m:90+t:2",
            "fields": "f12,f14,f62,f8,f184",
        }
        try:
            r = requests.get(EASTMONEY_BASE, params=params, headers=HEADERS, timeout=15)
            r.raise_for_status()
            data = r.json().get("data", {}) or {}
            diff = data.get("diff", {}) or {}
        except Exception:
            break
        for item in diff.values():
            code = item.get("f12")
            if code not in A_SHARE_SECTORS or code in seen:
                continue
            seen.add(code)
            net_yuan = item.get("f62") or 0
            out.append({
                "date": today,
                "市场": "A股",
                "板块名称": A_SHARE_SECTORS[code],
                "代表股票_代码": code,
                "主力净流入_亿": round(net_yuan / 1e8, 2),
                "换手率_pct": item.get("f8"),
                "币种": "CNY",
            })
        if len(seen) >= len(A_SHARE_SECTORS):
            break
    return out


# 日股板块（Yahoo Finance Japan）
JP_SECTORS_YAHOO = {
    "8306.T": "三菱日联（金融）",
    "8316.T": "三井住友（金融）",
    "6857.T": "Advantest（半导体）",
    "8058.T": "三菱商事（商社）",
    "6920.T": "Lasertec（半导体）",
}


def fetch_jp_stock_flow() -> list[dict]:
    """抓取日股个股当日数据。Yahoo Finance 429 限制激进，需 retry + 间隔。"""
    out = []
    today = date.today().isoformat()
    for ticker, name in JP_SECTORS_YAHOO.items():
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=2d"
        for attempt in range(3):
            try:
                time.sleep(3 + attempt * 2)  # 3s, 5s, 7s
                hdrs = dict(HEADERS)
                hdrs["Referer"] = "https://finance.yahoo.com/"
                r = requests.get(url, headers=hdrs, timeout=10)
                if r.status_code == 429:
                    time.sleep(10)
                    continue
                r.raise_for_status()
                chart = r.json().get("chart", {}).get("result", [{}])[0]
                quote = chart.get("indicators", {}).get("quote", [{}])[0]
                volumes = quote.get("volume", [])
                closes = quote.get("close", [])
                if not volumes or not closes:
                    continue
                turnover_jpy = (volumes[-1] or 0) * (closes[-1] or 0)
                out.append({
                    "date": today,
                    "市场": "日股",
                    "板块名称": name,
                    "代表股票_代码": ticker,
                    "主力净流入_亿": None,
                    "换手率_pct": None,
                    "币种": "JPY",
                    "成交额_亿日元": round(turnover_jpy / 1e8, 2),
                })
                break  # success → next ticker
            except Exception:
                if attempt == 2:
                    continue  # last attempt, skip
                time.sleep(5)
    return out


def fetch_all_sectors() -> list[dict]:
    """汇总 A 股 + 日股板块资金流。"""
    return fetch_a_share_sector_flow() + fetch_jp_stock_flow()


if __name__ == "__main__":
    import json
    print(json.dumps(fetch_all_sectors(), indent=2, ensure_ascii=False))
