"""
项目配置中心。所有密钥从 .env 读取（已 gitignore）。
所有 DB ID 从 notion_db_ids.json 读取。
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / ".env")

# ===== 密钥（从环境变量） =====
FRED_API_KEY = os.environ["FRED_API_KEY"]
# 下面两个一般不用——Hermes 自带 DeepSeek + Notion MCP
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
TIMEZONE = os.environ.get("TIMEZONE", "Asia/Tokyo")

# ===== Notion DB IDs（从 JSON） =====
with open(PROJECT_ROOT / "notion_db_ids.json", encoding="utf-8") as f:
    _db_ids = json.load(f)

PAGE_A_ID = _db_ids["page_A_crisis_warning"]["page_id"]
PAGE_B_ID = _db_ids["page_B_cb_balance"]["page_id"]

# 便捷访问（2026-05-31 V2：B 系列重命名对齐 B1-B7）
DB = {
    # Page A
    "A1": _db_ids["page_A_crisis_warning"]["databases"]["A1_UST_Yields_Daily"]["data_source_id"],
    "A2": _db_ids["page_A_crisis_warning"]["databases"]["A2_UST_Basis_SOFR_Daily"]["data_source_id"],
    "A3": _db_ids["page_A_crisis_warning"]["databases"]["A3_JGB_Yields_Daily"]["data_source_id"],
    "A4": _db_ids["page_A_crisis_warning"]["databases"]["A4_JGB_Basis_TONAR_Daily"]["data_source_id"],
    "A5": _db_ids["page_A_crisis_warning"]["databases"]["A5_Fed_Liquidity_Daily"]["data_source_id"],
    "A6": _db_ids["page_A_crisis_warning"]["databases"]["A6_Fed_BalanceSheet_Weekly"]["data_source_id"],
    "A7": _db_ids["page_A_crisis_warning"]["databases"]["A7_Daily_Risk_Report"]["data_source_id"],
    # Page B（B1-B7 与 7 个表严格 1:1 对应）
    "B1": _db_ids["page_B_cb_balance"]["databases"]["B1_CB_BalanceSheet_Monthly"]["data_source_id"],
    "B2": _db_ids["page_B_cb_balance"]["databases"]["B2_PBoC_Liquidity_Daily"]["data_source_id"],
    "B3": _db_ids["page_B_cb_balance"]["databases"]["B3_BoJ_Liquidity_Daily"]["data_source_id"],
    "B4": _db_ids["page_B_cb_balance"]["databases"]["B4_Fed_Liquidity_Daily"]["data_source_id"],
    "B5": _db_ids["page_B_cb_balance"]["databases"]["B5_PBoC_BS_Snapshot"]["data_source_id"],
    "B6": _db_ids["page_B_cb_balance"]["databases"]["B6_BoJ_BS_Snapshot"]["data_source_id"],
    "B7": _db_ids["page_B_cb_balance"]["databases"]["B7_Fed_BS_Snapshot"]["data_source_id"],
}

# ===== 数据源 URL =====
FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
DEEPSEEK_ENDPOINT = "https://api.deepseek.com/v1/chat/completions"

# 用户持仓（DeepSeek 建议时参考）
TICKERS_TO_ADVISE = ["161226", "1542.T", "1164.HK", "8306.T"]

# 风控阈值
THRESHOLDS = {
    "SOFR_SPRD_YELLOW_BP": 7,
    "SOFR_SPRD_RED_BP": 17,
    "RESERVES_YELLOW_T": 3.0,
    "RESERVES_RED_T": 2.8,
    "ON_RRP_YELLOW_B": 200,
    "ON_RRP_RED_B": 50,
    "JGB_10Y_YELLOW": 1.0,
    "JGB_10Y_RED": 1.5,
    "JGB_10Y_CRITICAL": 2.0,
    "BASIS_TOTAL_RED_B": 1500,
}
