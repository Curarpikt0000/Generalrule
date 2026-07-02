# 美债 + Fed + 中美日流动性日报：Hermes 自动化体系设计 V1.1

> 目的：用 **Hermes（后端 DeepSeek） + Notion** 替代 Gemini 定时任务，让数据可查询、可回溯、可建图，并自带 AI 风险分析。
> **架构里只有两个 agent**：Claude（设计） + Hermes（运行，既抓数又写分析）。**没有外部独立模型**。
> 文档地位：本 proposal 经用户批准后方可执行（遵循 §4 PLAN 硬门）。

---

## §1 总体架构

```
┌─────────────────┐     ┌────────────────────────────────────┐
│  数据源 (公开)  │ ──> │  Hermes (后端 = DeepSeek)          │
│  FRED/MoF/PBoC  │     │  ① 抓数据 → ② 写 Notion DB         │
└─────────────────┘     │  ③ 切换"风控官"角色 → ④ 写分析回 DB│
                        └──────────────────┬─────────────────┘
                                           v
                              ┌────────────────────────────┐
                              │  Notion (DB 存储 + 看板)   │
                              │  时序行 + AI 短评列 + 长页 │
                              └────────────────────────────┘
```

**核心理念**：
1. **单 agent 运行**：Hermes 既是数据搬运工，也是分析师。分析阶段它自己换一套 system prompt（`hermes_analysis_prompts/`）。没有"调用外部 DeepSeek"这件事，Hermes 后端本来就是 DeepSeek。
2. **数据归一化**：所有"每日数字"进入时序 DB，每个指标一列，每日一行。**不再用代码块表格**——表格内容直接由 Notion 视图渲染。
3. **AI 双层输出**：DB 每日记录里有 `AI 短评`（一句话，列内可见）；同一行的 page body 存放 Hermes 完整长分析。
4. **模型限制**：DeepSeek 不支持多模态，所以 Hermes 抓取必须输出**结构化 JSON / 纯文本数字**，避免 PDF/图表自己看不懂。

---

## §2 Notion Page 结构

### Page A：🚸 经济危机预警 (`2dc47eb5fd3c803d8c31c4b77bd56154`)

**承担原任务 1（美/日债）+ 原任务 3（Fed 资产负债表）+ 原页面的金属/RRP 双轨监控。**

| # | DB 名称 | 用途 | 行频率 |
|---|---------|------|--------|
| A1 | **UST_Yields_Daily** | 美债收益率（1y/2y/5y/10y/30y） | 每日 |
| A2 | **UST_Basis_SOFR_Daily** | 美债基差套利 + SOFR 倒挂监控 | 每日 |
| A3 | **JGB_Yields_Daily** | 日债收益率（1m/3m/6m/1y/3y/5y/10y/30y） | 每日 |
| A4 | **JGB_Basis_TONAR_Daily** | 日债基差套利 + TONAR 倒挂监控 | 每日 |
| A5 | **Fed_Liquidity_Daily** | SOFR Sprd / ON RRP / Reserves / TGA / Gold q / Silver q / SGE Prem | 每日 |
| A6 | **Fed_BalanceSheet_Weekly** | Total Assets / Treasuries / MBS / Reserves / ON RRP / TGA + Δ 上周/上月 | 每周（H.4.1 后） |
| A7 | **Daily_Risk_Report** | 主索引 DB，每日一条，关联以上 6 DB；列含 `AI 短评`，page body 存长分析 | 每日 |

**Page Layout（自上而下）**：
```
📊 顶部 Callout：今日风控状态灯（🔴/🟡/🟢）+ AI 一句话总结
├── 📌 Pinned：今日 Daily_Risk_Report 链接
├── 🔥 Linked View: Daily_Risk_Report（Table，按日期倒序，仅最近 14 行）
├── 📈 Linked View: UST_Yields_Daily（Line Chart，10y/2y/30y 30天）
├── 📈 Linked View: JGB_Yields_Daily（Line Chart，10y/30y 30天）
├── 🧪 Linked View: Fed_Liquidity_Daily（Table 最近 20 天）
├── 🏦 Linked View: Fed_BalanceSheet_Weekly（Table 最近 12 周）
├── ⚠️ Linked View: UST_Basis_SOFR_Daily + JGB_Basis_TONAR_Daily（基差预警）
└── 📁 Toggle "原 Prompt 备份"（折叠所有原页面内容，不丢失）
```

### Page B：🏧 中美日央行资产负债表 (`2de47eb5fd3c80bb9fbff107fa034b2e`)

**承担原任务 2（中日流动性）+ 原页面的月度央行对比。**

| # | DB 名称 | 用途 | 行频率 |
|---|---------|------|--------|
| B1 | **CB_BalanceSheet_Monthly** | PBoC + BoJ + Fed 月度核心项对比（总资产/政府债权/基础货币等） | 每月 |
| B2 | **PBoC_Liquidity_Daily** | OMO 净投放 / SFISF 规模 / 买断式逆回购 / A 股两融余额 / 当日信号 | 每日 |
| B3 | **BoJ_Liquidity_Daily** | JGB 每日买入 / BoJ 利率 / CNY/JPY 汇率 / 当日信号 | 每日 |
| B4 | **JGB_10Y_3MonthTrend** | 10Y JGB 日度收益率 + 关键位突破标记（1.0% / 1.1% / 2.0%） | 每日 |
| B5 | **CN_JP_SectorFlow_Daily** | A 股（电子/有色/金融）+ 日股（金融/电气机器/商社）主力净流入 + 换手 + 7d/15d 趋势 | 每日 |
| B6 | **CN_JP_Daily_Analysis** | 中日联动 AI 分析（短评列 + 长分析页） | 每日 |

**Page Layout**：
```
🏧 顶部 Callout：今日中日货币政策温差 + 配置建议
├── 📌 今日 CN_JP_Daily_Analysis 链接
├── 📊 Linked View: CB_BalanceSheet_Monthly（最近 6 个月）
├── 🇨🇳 Linked View: PBoC_Liquidity_Daily（最近 30 天）
├── 🇯🇵 Linked View: BoJ_Liquidity_Daily（最近 30 天）
├── 📈 Linked View: JGB_10Y_3MonthTrend（90 天 Line Chart）
├── 💰 Linked View: CN_JP_SectorFlow_Daily（最近 15 天）
└── 📁 Toggle "原页面内容备份"（中/美/日 解释 + 操作工具表）
```

---

## §3 DB Schema 详细定义

### A1: UST_Yields_Daily
| 字段 | 类型 | 说明 |
|------|------|------|
| Date | Date (Title) | 主键，倒序 |
| 1Y | Number | % |
| 2Y | Number | % |
| 5Y | Number | % |
| 10Y | Number | % |
| 30Y | Number | % |
| 2s10s | Formula | 10Y - 2Y |
| AI短评 | Rich Text | DeepSeek 一句话 |
| 数据源 | URL | FRED 链接 |

### A2: UST_Basis_SOFR_Daily
| 字段 | 类型 |
|------|------|
| Date | Date (Title) |
| 总规模($B) | Number |
| 2Y基差 | Number |
| 5Y基差 | Number |
| 10Y基差 | Number |
| 30Y基差 | Number |
| 杠杆倍数 | Number |
| 1Y-SOFR(bps) | Number |
| 2Y-SOFR(bps) | Number |
| 5Y-SOFR(bps) | Number |
| 10Y-SOFR(bps) | Number |
| 30Y-SOFR(bps) | Number |
| SOFR(%) | Number |
| 状态灯 | Select (🟢/🟡/🔴) |
| 风险诊断 | Rich Text |

### A3: JGB_Yields_Daily
| 字段 | 类型 |
|------|------|
| Date | Date (Title) |
| 1M / 3M / 6M / 1Y / 3Y / 5Y / 10Y / 30Y | Number |
| AI短评 | Rich Text |

### A4: JGB_Basis_TONAR_Daily（结构同 A2，期限改为 JGB）

### A5: Fed_Liquidity_Daily
| 字段 | 类型 |
|------|------|
| Date | Date (Title) |
| SOFR Sprd(bp) | Number |
| ON RRP($B) | Number |
| Reserves($T) | Number |
| TGA($B) | Number |
| Gold q | Number |
| Silver q | Number |
| Silver Spread | Number |
| SGE Premium | Number |
| 风控状态 | Select (🟢正常/🟡紧张/🔴危险) |
| Risk Signal | Rich Text |

### A6: Fed_BalanceSheet_Weekly
| 字段 | 类型 |
|------|------|
| Week | Date (Title) |
| Total Assets($T) | Number |
| Treasuries($T) | Number |
| MBS($T) | Number |
| RMP($B) | Number |
| SRF($B) | Number |
| Reserves($T) | Number |
| ON RRP($B) | Number |
| TGA($B) | Number |
| Currency($B) | Number |
| Δ 上周 Reserves | Number |
| QT/QE 趋势 | Select |
| 审计判定 | Rich Text |

### A7: Daily_Risk_Report (主索引)
| 字段 | 类型 |
|------|------|
| Date | Date (Title) |
| 风控总分 | Select (🟢/🟡/🔴) |
| AI 短评 | Rich Text (≤200 字) |
| 美债风险 | Select |
| 日债风险 | Select |
| Fed流动性风险 | Select |
| 关键变动 | Rich Text |
| → UST_Yields 链接 | Relation |
| → Fed_Liquidity 链接 | Relation |
| → JGB_Yields 链接 | Relation |
| 数据完整度 | Number (0–100%) |

**Page body** = DeepSeek 完整长分析（含逻辑链条、操作建议、对 161226/1542.T/8306.T/1164.HK 的建议）。

### B1–B6 schema 同理（略，建库时按 §3 思路类比展开）

---

## §4 Hermes 每日 Workflow（关键交付物）

### Cron 时间表（所有时间为 Asia/Shanghai）

| 时间 | 任务 | 数据源 | 写入 DB |
|------|------|--------|---------|
| **08:30** | 抓取美债 + Fed 流动性日数据（昨日收盘） | FRED API: DGS1, DGS2, DGS5, DGS10, DGS30, SOFR, EFFR, IORB, RRPONTSYD, WALCL, WSC | A1, A2, A5 |
| **09:00** | 抓取日债（JGB）+ TONAR | Investing.com / TradingEconomics（反爬：headless + user-agent rotation） | A3, A4 |
| **09:30** | 调用 DeepSeek，传入 A1–A5 最近 30 天数据 + 今日值 | DeepSeek API | 写 A7 (Daily_Risk_Report) 短评 + 长分析 |
| **12:01** | 抓取 PBoC OMO + 日央行最新数据 + 中日股市资金 | PBoC 官网 / Wind 替代源 / 财联社 / 东方财富 API | B2, B3, B4, B5 |
| **12:30** | DeepSeek 中日联动分析 | DeepSeek | B6 |
| **每周五 18:00** | Fed H.4.1 周报数据更新 | FRED: WALCL, WTREGEN, WRESBAL, RRPONTSYD | A6 |
| **每月 10 号** | PBoC/BoJ/Fed 月度资产负债表 | PBoC + BoJ 官网 + Fed H.4.1 月末值 | B1 |

### Hermes Workflow 文件结构（在项目目录下）
```
美债收益率和Fed中美日流动性日报/
├── AGENTS.md                          # 项目规则（已存在）
├── PROPOSAL.md                        # 本文件
├── README.md                          # 给未来 Agent 的快速索引
├── config.py                          # 配置（API keys 从 .env 读取）
├── .env.example                       # 密钥模板（FRED_API_KEY / NOTION_TOKEN / DEEPSEEK_API_KEY）
├── notion_db_ids.json                 # 13 个 DB 的 data_source_id 缓存
├── hermes_workflows/
│   ├── 01_morning_us_data.md          # 08:30 prompt
│   ├── 02_morning_jgb_data.md         # 09:00 prompt
│   ├── 03_morning_ai_analysis.md      # 09:30 prompt（DeepSeek）
│   ├── 04_noon_china_japan.md         # 12:01 prompt
│   ├── 05_noon_ai_analysis.md         # 12:30 prompt
│   ├── 06_weekly_fed_h41.md           # 周五 18:00
│   └── 07_monthly_cb_balance.md       # 每月 10 号
├── scrapers/
│   ├── fred_client.py                 # FRED API 封装
│   ├── investing_scraper.py           # 反爬：日债/TONAR
│   ├── pboc_scraper.py                # PBoC OMO 抓取
│   ├── boj_scraper.py                 # BoJ 官网
│   └── stock_flow_scraper.py          # A 股/日股资金流
├── notion_writer/
│   ├── client.py                      # Notion MCP 封装
│   └── schemas.py                     # 13 个 DB schema 定义（写入时校验）
├── deepseek_prompts/
│   ├── crisis_warning.md              # Page A 长分析 prompt
│   └── china_japan.md                 # Page B 长分析 prompt
├── tasks/
│   ├── todo.md
│   └── lessons.md
└── logs/                              # 每日运行日志（gitignore）
```

### 单次 Workflow 示例（`03_morning_ai_analysis.md`）
```markdown
# Hermes 任务：早间美债+Fed AI 风险分析

## 输入
1. 从 Notion 拉取 A1 (UST_Yields_Daily) 最近 30 行
2. 从 Notion 拉取 A2 (UST_Basis_SOFR_Daily) 最近 30 行
3. 从 Notion 拉取 A5 (Fed_Liquidity_Daily) 最近 30 行
4. 从 Notion 拉取 A6 (Fed_BalanceSheet_Weekly) 最近 12 行

## 处理
1. 拼接 JSON 给 DeepSeek（不发图，纯结构化）
2. DeepSeek prompt 模板 = deepseek_prompts/crisis_warning.md
3. 解析返回：{短评(≤200字), 风控总分, 长分析(MD)}

## 输出
- notion-create-pages 写入 A7 一行：
  - Date = 今天
  - 风控总分 = <DeepSeek 返回>
  - AI 短评 = <短评>
  - page content = <长分析 MD>
- 同时给 A1/A5 今日行的 `AI短评` 列填短评
```

---

## §5 数据源映射 + 反爬策略

| 数据 | 主源 | 备用源 | 反爬要点 |
|------|------|--------|----------|
| 美债收益率 | FRED API (DGS1/2/5/10/30) | Treasury.gov XML | 官方 API 无需反爬 |
| SOFR / EFFR / IORB | FRED API (SOFR/EFFR/IORB) | NY Fed | 同上 |
| ON RRP / TGA | FRED API (RRPONTSYD/WTREGEN) | NY Fed 操作页 | 同上 |
| Fed 总资产 / Treasuries / MBS | FRED API (WALCL/WSHOTSL/WSHOMCB) | H.4.1 PDF | 同上 |
| 日债 (JGB) | MoF Japan API / Investing.com | TradingEconomics | Investing 需 user-agent + cookie；优先 MoF |
| TONAR | BoJ 官网每日公布 | Reuters | 官方源 |
| PBoC OMO | PBoC 官网 + WeChat 公告 | 财联社 | 官方源静态页 |
| 买断式逆回购 / SFISF | PBoC 货政司新闻稿 | 中国货币网 | 官方源 |
| A 股两融 | 沪深交易所每日数据 | 东方财富 | 官方源 |
| 日股资金流 | Nikkei / Bloomberg | 雅虎财经日本 | 公开 API |
| 黄金/白银期货 | CME 官方 | Investing.com | 优先 CME |

**重要**：所有外部 API 调用必须 `try/except` + 失败时该行 `AI 短评` 填 "数据缺失，详见 logs/"，**不得用上一日值伪造**（遵循全局规则 §2.10 显式失败）。

---

## §6 DeepSeek Prompt 设计要点

- **角色固定**：`首席宏观风控官 (CRO)`
- **输入格式**：JSON 数组（30 天历史 + 今日）
- **输出格式严格 JSON**：
  ```json
  {
    "score": "🔴|🟡|🟢",
    "tldr": "≤200 字一句话",
    "long_analysis_md": "完整 Markdown 长分析",
    "key_changes": ["变动1", "变动2"],
    "trades": [
      {"ticker": "161226", "action": "持有/加仓/减仓", "rationale": "..."}
    ]
  }
  ```
- **三个 prompt**：crisis_warning（美/日债 + Fed） / china_japan（中日流动性） / weekly_synthesis（周五综合）

---

## §7 与原 Gemini 任务的映射对照

| 原 Gemini 任务 | 替代方案 |
|----------------|---------|
| 任务 1（美/日债 6 表，每日 9 点） | Hermes 08:30 + 09:00 抓取 → A1/A2/A3/A4 → 09:30 AI 分析进 A7 |
| 任务 2（中日流动性，每日 12:01） | Hermes 12:01 抓取 → B2/B3/B4/B5 → 12:30 AI 分析进 B6 |
| 任务 3（Fed 资负表 20日 + 6月） | 每日 08:30 抓 A5；周五 18:00 抓 A6 |

**优势**：
1. 不再每次重发 prompt 让 Gemini "回忆"30 天数据——Notion 直接存
2. 数据可被前端、ETF 操作工具、其他 Notion view 复用
3. 可对历史做回测（找 SOFR Spread > 17bp 的天，看后续金属表现）
4. AI 短评在 DB 列里可一眼扫，详细长分析点开看

---

## §8 待用户确认的 3 个关键决策

见后续 AskUserQuestion。
