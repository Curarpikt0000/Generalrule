# Hermes Workflow 05：中日联动分析（Hermes 自己跑）

> **触发时间**：每日 JST 12:30（在 04 完成后）
> **目标**：Hermes 切换到"中日联动分析师"角色，分析中日联动信号 + 配置建议，写入 B6
>
> **说明**：不调用外部模型，Hermes 自己换 system prompt 完成分析。

---

## §1 拉取上下文

| DB | 最近 N 行 |
|----|-----------|
| B1 CB_BalanceSheet_Monthly | 6 个月 |
| B2 PBoC_Liquidity_Daily | 30 |
| B3 BoJ_Liquidity_Daily | 30 |
| B4 JGB_10Y_3MonthTrend | 90 |
| B5 CN_JP_SectorFlow_Daily | 15（按 Date_Sector group by Date） |
| A5 Fed_Liquidity_Daily | 7（提供美元流动性背景） |
| A6 Fed_BalanceSheet_Weekly | 4 |

拼成统一 JSON，调用 DeepSeek。

---

## §2 角色 Prompt

Hermes 读取 `../hermes_analysis_prompts/china_japan.md` 内容作为 system prompt，临时切换角色。

---

## §3 返回格式

```json
{
  "linkage_signal": "🟡背离开始",
  "pboc_stance": "宽松加码",
  "boj_stance": "鹰派",
  "fx_pressure": "🟡波动",
  "tldr": "...≤200字...",
  "core_allocation": "...",
  "risk_warning": "...",
  "long_analysis_md": "..."
}
```

## §3 写入 B6 + 重写中美日资产负债表 Page 顶部 7 表快照（V2 大改 2026-05-31）

**§3a：B6 数据库一行** — properties + 完整长分析作为 page body

**§3b：Page B 顶部 7 表快照重写**（每天彻底覆盖，不 append）

调用 `notion-update-page` 的 `update_content` 命令：
- page_id = `2de47eb5fd3c80bb9fbff107fa034b2e`
- 找到上次的 "# 📊 今日快照 — 中美日三央行资产负债表" 区域
- 整段替换为今天版本，照下面模板（共 7 个表）：

```markdown
# 📊 今日快照 — 中美日三央行资产负债表

> 本区每日 JST 12:30 由 Hermes 重写。

> [!CALLOUT|{color}]
> ## 🏦 三大央行政策温差监控
> **更新时间**：YYYY-MM-DD HH:MM JST | **数据完整度**：{0-100}%
> **一句话**：{≤120字综合诊断}

## 表 0：三大央行核心项对比（最新）
| 核心指标 | 🇨🇳 PBoC | 🇯🇵 BoJ | 🇺🇸 Fed | 逻辑解读 |
{4 行：总资产规模 / 对政府债权 / 基础货币 / 环比方向}

## 表 1：🇨🇳 PBoC 流动性流入流出（最近 7 天 + 30 天精选）
| 日期 | OMO净投放 | 买断式 | MLF续作 | SFISF | 两融 | DR007 | 当日信号 |
{8-10 行}

## 表 2：🇯🇵 BoJ 流动性流入流出
| 日期 | JGB买入 | BoJ利率 | 加息预期 | USD/JPY | CNY/JPY | 当日信号 |
{6-8 行}

## 表 3：🇺🇸 Fed 流动性流入流出
| 日期 | SOFR-IORB | ON RRP | Reserves | TGA | QT/QE | 当日信号 |
{6-8 行}

## 表 4：🇨🇳 PBoC 资产负债表全景（最新月）
{Assets 左 6 行 | Liabilities 右 7 行 markdown 表，左右并列}

## 表 5：🇯🇵 BoJ 资产负债表全景（最新 10 日）
{Assets 左 8 行 | Liabilities 右 4 行}

## 表 6：🇺🇸 Fed 资产负债表全景（最新周）
{Assets 左 5 行 | Liabilities 右 5 行 + 审计判定}

# 🔍 综合诊断
**关键变动 (Top 3)**：1/2/3
**💡 核心配置建议**：针对 1164.HK / 8306.T / 161226 / 高 PBR 科技
**📈 明日重点**：3 个观察点
```

**color/emoji**：🟢 联动顺畅=green, 🟡 背离开始=yellow, 🟠 明显背离=orange, 🔴 政策对冲=red

## §3c：填写底层 DB（重要 — 7 表不能只渲染，得留档）

- **B1 CB_BalanceSheet_Monthly**：若是新月份，写 3 行（PBoC + BoJ + Fed）
- **B2 PBoC_Liquidity_Daily**：今日一行（OMO/买断式/MLF/SFISF/两融/DR007）
- **B3 BoJ_Liquidity_Daily**：今日一行
- **B7 PBoC_BS_Snapshot**（NEW）：若 PBoC 当月发布了新资产负债表（每月 15-20 号），写一行
- **B8 BoJ_BS_Snapshot**（NEW）：若 BoJ 当 10 日周期发布了新表，写一行
- **A5/A6** 已由 Page A workflow 写入，跨页 query 即可

**数据源 ID 全部在 `../notion_db_ids.json`，禁止硬编码。**
