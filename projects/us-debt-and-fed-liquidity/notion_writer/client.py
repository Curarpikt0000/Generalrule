"""
Notion 写入封装。

Hermes 调用 Notion MCP（已配置），此模块封装常用操作：
- query_today(db_key)：检查今日是否已有行
- create_row(db_key, properties, content=None)：写入一行
- update_row(page_id, properties=None, content=None)

实际调用通过 MCP 工具（Hermes 内部处理）。本文件给出参数对照表。
"""
from typing import Optional
from datetime import date

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB


def make_row_props(db_key: str, **fields) -> dict:
    """
    构造 Notion create_pages 的 properties dict。

    所有字段必须与 schema 名一致（见 notion_db_ids.json + Notion 实际 DB）。
    Date 字段用 ISO 字符串 "2026-05-31"。
    Select 字段用枚举字符串，必须严格匹配（含 emoji）。
    Number 字段用 Python float/int。
    Rich text 字段用 markdown 字符串。
    """
    return fields


# ===== Schema 参考 =====
A1_FIELDS = ["Date", "1Y", "2Y", "5Y", "10Y", "30Y", "2s10s_bps", "AI短评", "数据源"]
A2_FIELDS = ["Date", "总规模_B", "规模_2Y_B", "规模_5Y_B", "规模_10Y_B", "规模_30Y_B",
             "基差_2Y", "基差_5Y", "基差_10Y", "基差_30Y",
             "杠杆倍数", "SOFR_pct", "IORB_pct", "EFFR_pct", "RRP_B",
             "1Y_SOFR_bps", "2Y_SOFR_bps", "5Y_SOFR_bps",
             "10Y_SOFR_bps", "30Y_SOFR_bps",
             "状态灯_基差", "状态灯_SOFR", "风险诊断_基差", "风险诊断_SOFR", "AI短评"]
A3_FIELDS = ["Date", "1M", "3M", "6M", "1Y", "3Y", "5Y", "10Y", "30Y", "关键位突破", "AI短评", "数据源"]
A4_FIELDS = ["Date", "总规模_T_JPY", "规模_10Y_T", "规模_30Y_T",
             "基差_10Y", "基差_30Y", "杠杆倍数", "TONAR_pct",
             "1M_TONAR_bps", "1Y_TONAR_bps", "5Y_TONAR_bps", "10Y_TONAR_bps", "30Y_TONAR_bps",
             "状态灯_基差", "状态灯_TONAR", "YCC退出风险", "风险诊断_基差", "风险诊断_TONAR", "AI短评"]
A5_FIELDS = ["Date", "SOFR_Sprd_bp", "ON_RRP_B", "Reserves_T", "TGA_B",
             "Gold_q", "Silver_q", "Silver_Spread", "SGE_Premium_USD",
             "风控状态", "Risk_Signal", "AI短评", "FRED链接"]
A6_FIELDS = ["Week", "Total_Assets_T", "Treasuries_T", "MBS_T", "RMP_B", "SRF_B",
             "Reserves_T", "ON_RRP_B", "TGA_B", "Currency_B",
             "Delta_Reserves_WoW", "Delta_TGA_WoW", "QT_QE趋势", "审计判定", "AI长分析", "H41源链接"]
A7_FIELDS = ["Date", "风控总分", "AI短评", "美债风险", "日债风险", "Fed流动性风险",
             "基差套利风险", "关键变动", "操作建议", "数据完整度_pct",
             "UST_Yields_Ref", "UST_Basis_Ref", "JGB_Yields_Ref", "JGB_Basis_Ref",
             "Fed_Liquidity_Ref", "Fed_Balance_Ref", "运行状态"]

B1_FIELDS = ["Month", "央行", "总资产_本币", "总资产_USD_T", "对政府债权",
             "对其他存款性公司债权", "国债_JGB持有", "MBS", "基础货币", "准备金_存款",
             "扩缩表方向", "环比_pct", "逻辑解读", "数据源"]
B2_FIELDS = ["Date", "OMO_净投放_亿", "买断式逆回购_亿", "MLF_到期_亿", "MLF_续作_亿",
             "SFISF_规模_亿", "CBS_规模_亿", "A股两融余额_万亿", "DR007_pct",
             "水位状态", "政策信号", "当日信号", "AI短评", "数据源"]
B3_FIELDS = ["Date", "JGB_每日买入_亿日元", "BoJ_政策利率_pct", "加息预期_pct",
             "CNY_JPY", "USD_JPY", "QT_进度", "YCC状态", "当日信号", "AI短评", "数据源"]
B4_FIELDS = ["Date", "10Y_JGB_pct", "日变动_bps", "周变动_bps", "月变动_bps",
             "关键位状态", "金融股冲击", "高PBR科技股冲击", "AI短评", "数据源"]
B5_FIELDS = ["Date_Sector", "市场", "板块名称", "代表股票_代码", "主力净流入_亿",
             "币种", "换手率_pct", "7d趋势", "15d趋势", "配置建议", "逻辑解读"]
B6_FIELDS = ["Date", "中日联动信号", "PBoC动向", "BoJ动向", "AI短评",
             "汇率压力", "核心配置建议", "风险预警",
             "PBoC_Ref", "BoJ_Ref", "JGB10Y_Ref", "SectorFlow_Ref", "CB_Monthly_Ref",
             "运行状态"]


def today_iso() -> str:
    return date.today().isoformat()
