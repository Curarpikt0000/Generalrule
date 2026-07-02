#!/usr/bin/env python3
"""
Verify SGE (上海黄金交易所) spot prices for COMEX daily report.
Covers Au(T+D), Au99.99, Ag(T+D), Pt99.95.

Usage:
    python3 verify_sge_data.py

Requires: akshare (pip3 install akshare)
"""
import akshare as ak
import json

symbols = {
    "Au(T+D)": {"unit": "CNY/g", "per_oz": True},
    "Au99.99": {"unit": "CNY/g", "per_oz": True},
    "Ag(T+D)": {"unit": "CNY/kg", "per_oz": False},  # needs /1000
    "Pt99.95": {"unit": "CNY/g", "per_oz": True},
}

results = {}
for symbol, info in symbols.items():
    try:
        df = ak.spot_hist_sge(symbol=symbol)
        last = df.iloc[-1]
        results[symbol] = {
            "date": last["date"],
            "open": float(last["open"]),
            "close": float(last["close"]),
            "low": float(last["low"]),
            "high": float(last["high"]),
            "unit": info["unit"],
            "source": "akshare spot_hist_sge()",
        }
    except Exception as e:
        results[symbol] = {"error": str(e)}

print(json.dumps(results, indent=2, ensure_ascii=False))
