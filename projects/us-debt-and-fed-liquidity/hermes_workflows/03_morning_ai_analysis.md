# Hermes Workflow 03：早间风险分析（Hermes 自己跑）

> **触发时间**：每日 JST 09:30（在 01 + 02 完成后）
> **目标**：Hermes 切换到"首席风控官"角色，读 A1-A6 最近 30 天 + 今日数据，写入 A7（短评 + 长分析）
>
> **说明**：这一步不调用外部模型。Hermes（= DeepSeek）把自己的 system prompt 临时换成 `../hermes_analysis_prompts/crisis_warning.md`，然后自己生成分析。

---

## §1 拉取上下文（Notion → JSON）

调用 `notion-fetch` 或 query data source，拉取以下 DB 最近 N 行：

| DB | 最近 N 行 | 必带字段 |
|----|-----------|----------|
| A1 UST_Yields_Daily | 30 | Date, 1Y, 2Y, 5Y, 10Y, 30Y, 2s10s_bps |
| A2 UST_Basis_SOFR_Daily | 30 | Date, 5种基差, 5种 SOFR_bps, 状态灯 |
| A3 JGB_Yields_Daily | 30 | Date, 全期限 |
| A4 JGB_Basis_TONAR_Daily | 30 | Date, 基差, TONAR_bps, YCC退出风险 |
| A5 Fed_Liquidity_Daily | 30 | Date, SOFR_Sprd_bp, ON_RRP_B, Reserves_T, TGA_B, Gold_q, Silver_q, SGE_Premium_USD |
| A6 Fed_BalanceSheet_Weekly | 12 | Week, Total_Assets, Treasuries, MBS, Reserves, ON_RRP, TGA, Delta_Reserves_WoW |

拼成统一 JSON：
```json
{
  "report_date": "2026-MM-DD",
  "timezone": "Asia/Tokyo",
  "ust_yields": [{ "date": "...", "10Y": 4.42, ... }, ...],
  "ust_basis_sofr": [ ... ],
  "jgb_yields": [ ... ],
  "jgb_basis_tonar": [ ... ],
  "fed_liquidity": [ ... ],
  "fed_balance_sheet": [ ... ],
  "tickers_to_advise": ["161226", "1542.T", "1164.HK", "8306.T"]
}
```

---

## §2 Hermes 切换角色生成分析

- **不是外部 API 调用**。Hermes 自己读 `../hermes_analysis_prompts/crisis_warning.md` 内容作为 system 角色，把 §1 拼好的 JSON 作为 user 消息，自己生成 JSON 输出。
- temperature：尽量低（≤0.3），减少漂移
- 输入限制：DeepSeek 不支持多模态，所以 §1 拼数据时必须纯文本/JSON，不能塞 Notion 视图截图

---

## §3 解析返回 + 写入 Notion

Hermes 在该角色下严格返回 JSON：
```json
{
  "score": "🔴危险",
  "tldr": "...≤200字...",
  "us_bond_risk": "🔴",
  "jgb_risk": "🔴",
  "fed_liquidity_risk": "🟡",
  "basis_arb_risk": "🔴",
  "key_changes": ["...", "..."],
  "trades": [
    {"ticker": "161226", "action": "持有", "rationale": "..."},
    {"ticker": "1542.T", "action": "减仓", "rationale": "..."}
  ],
  "long_analysis_md": "## 逻辑链条\n...\n## 操作建议\n..."
}
```

写入 A7：
- properties: Date, 风控总分=score, AI短评=tldr, 美债风险, 日债风险, Fed流动性风险, 基差套利风险, 关键变动=key_changes joined, 操作建议=trades formatted, 数据完整度_pct, 运行状态=✅成功, 各 Ref 字段关联到当日 A1-A6 page
- **page content** = long_analysis_md

同时给 A1 / A2 / A5 当日行的 `AI短评` 列各填一段子短评（从 `long_analysis_md` 提取或单独要 DeepSeek 输出 sub-comments）。

---

## §4 重写经济危机预警 Page 顶部 "Today's Brief" 区域

**这是 dashboard 层，每天都要彻底覆盖（不是 append）。**

调用 `notion-update-page` 的 `update_content` 命令：
- page_id = `2dc47eb5fd3c803d8c31c4b77bd56154`
- 找到上次的 Today's Brief 区域（以 `# 📊 Today's Brief` 开头到 `> 以下是 13 个原始数据库视图` 结束）
- 整段替换为今天的新版本

Today's Brief 必须按这个模板（照样板，不要发挥）：

```markdown
# 📊 Today's Brief — YYYY-MM-DD (美东收盘)

> 本区每日 JST 09:30 由 Hermes 重写。

> [!CALLOUT|{color}]
> ## {emoji} 综合状态：{label}
> **一句话**：{≤80字概况}

## 🇺🇸 表 1：美债收益率快照（前一日 → 今日）
{markdown 表：1Y/2Y/5Y/10Y/30Y/2s10s + Δ bps + 状态灯}

## 🏦 表 2：Fed 流动性快照
{markdown 表：SOFR Sprd / ON RRP / Reserves / TGA / Gold q / Silver q}

## 🇯🇵 表 3：日债快照
{markdown 表：1Y/5Y/10Y/30Y + 关键位}

## 🔍 综合诊断
**关键变动 (Top 3)**
1. ...
2. ...
3. ...

## 💡 仓位建议
{markdown 表：161226 / 1542.T / 1164.HK / 8306.T + 动作 + 逻辑}

## 📈 明日重点
- ...
- ...
- ...

---

> 以下是 13 个原始数据库视图，drill-down 查历史/趋势图表用。
```

**color/emoji 规则**：
- 🟢 normal=`green`, 🟡 紧张=`yellow`, 🔴 危险=`red`, 🚨 极危=`pink`
- 与 A7 当日 `风控总分` 字段保持完全一致

## §5 同步写 A7 一行

完成 §4 后，再写 A7 一行（含同样的内容但结构化到字段）：
- properties: Date, 风控总分, AI短评(=Brief 里的"一句话"), 各风险灯, 关键变动, 操作建议, 数据完整度_pct, 运行状态, 各 Ref
- page body: 完整长分析（比 Brief 更深，800-1500 字）

## §6 失败处理

返回非 JSON / 解析失败：
1. Hermes 自己重试 1 次（temperature 降 0.1）
2. 仍失败 → A7 写入：风控总分=`🟡紧张`, AI短评=`"AI 分析失败，详见 logs/"`, 运行状态=`❌失败`，**且不要清空 Today's Brief 顶部区**（保留昨天的，比清空好）
3. 不得编造分析（遵循全局规则 §2.10）
