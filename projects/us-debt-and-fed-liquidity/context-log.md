# 美债收益率和Fed中美日流动性日报 — 上下文快照
> 每晚 23:00 自动更新

## 项目信息

- **路径**: `~/hermesagent/US Debt and Fed Liquidity/美债收益率和Fed中美日流动性日报/`
- **AGENTS.md**: 已存在（含完整项目规则，2026-05-31 初版）
- **核心架构**: Hermes 7 workflow（01-07）每日运行
- **Notion DB**: 13 个 DB，见 `notion_db_ids.json`
- **数据源**: FRED / PBoC / BoJ / MoF Japan

## 关键指针

- AGENTS.md 在项目根目录
- context-snapshot: `tasks/context-snapshot.md`
- 所有 cron 已注册（8个定时任务）

## 核心规则（不可遗忘）

1. Hermes 既是数据搬运工也是分析师
2. 所有 Notion 写入走 `notion_writer/client.py`
3. 所有 FRED 调用走 `scrapers/fred_client.py`（含 429 保护）
4. 所有 DB ID 从 `notion_db_ids.json` 读取，禁止硬编码
5. 时区统一 JST（Asia/Tokyo）

## 已知的 DB 状态变化（来自日志）

- **B5 CN_JP_SectorFlow_Daily**: 已归档（_OLD_CN_JP_SectorFlow_Daily）。当前 B5 DB 实际为 `B5_PBoC_BS_Snapshot`（月度）。workflow 05 中日分析跳过板块资金流。
- **B6**: 原 B6_CN_JP_Daily_Analysis 已归档，替代 DB 为 B6_BoJ_BS_Snapshot
- **A6 Fed_BalanceSheet_Weekly**: DB 在回收站中（404 不可读）。H.4.1 周报数据通过 B7_Fed_BS_Snapshot 维护
- **stock_flow_scraper.py**: 板块代码更新为 BK1039/BK0478/BK0475/BK1202，加 pagination 循环；JP Yahoo Finance 加 429 retry（3s/5s/7s + Referer header）
- **DR007**: pboc_scraper.fetch_dr007() 返回 None，需手动估算补充
- **cme_metals.py**: 仍未实现（Gold_q/Silver_q/SGE_Premium 字段为 null）

## 未修复的已知问题

- **B4_FIELDS 与 DB 指向不一致**：`notion_writer/client.py` 中 B4_FIELDS 仍描述旧 B4_JGB_10Y_3MonthTrend schema，但 `config.py:DB["B4"]` 实际指向 B4_Fed_Liquidity_Daily。写 A4 数据时不会触发此问题，但维护需注意。
- **DR007**: pboc_scraper.fetch_dr007() 返回 None，需手动估算补充
- **cme_metals.py**: 仍未实现（Gold_q/Silver_q/SGE_Premium 字段为 null）

## 6 月关键事件

- **6/16**: BoJ MPM 加息决议（市场定价加息至 1.0% 概率 ~85%）。BoJ 维持 0.75%，未如预期加息（6/16 最新数据确认）
- **6/17~18**: 美联储 FOMC 会议（点阵图 & SEP 前瞻）
- **跨季**: PBoC 加大 OMO 投放（6/16 净投放 4495亿为 6月最大单日）
- **JGB 10Y**: 6/12 最新 2.643%（突破2.5%关键位），TONAR 稳定 0.727%
