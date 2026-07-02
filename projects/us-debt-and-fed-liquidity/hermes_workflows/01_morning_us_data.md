# Hermes Workflow 01：早间美债 + Fed 流动性抓取

> **触发时间**：每日 JST 08:30（周一-周五，跳过美东节假日）
> **目标**：抓取昨日美东收盘的美债收益率 + Fed 流动性数据，写入 Notion A1 / A2 / A5

---

## §1 数据抓取（FRED API）

调用 `scrapers/fred_client.py`，拉取以下序列**最近 2 天**（避免休市数据缺失）：

| 序列 ID | 含义 | 写入字段 |
|---------|------|----------|
| DGS1 | 1Y UST | A1.1Y |
| DGS2 | 2Y UST | A1.2Y |
| DGS5 | 5Y UST | A1.5Y |
| DGS10 | 10Y UST | A1.10Y |
| DGS30 | 30Y UST | A1.30Y |
| SOFR | SOFR 利率 | A2.SOFR_pct, A5.（用于算 Sprd） |
| EFFR | EFFR 利率 | A5（参考） |
| IORB | 准备金利率 | A5.（SOFR_Sprd_bp = (SOFR-IORB)*100） |
| RRPONTSYD | ON RRP 余额 | A5.ON_RRP_B |
| WTREGEN | TGA 余额 | A5.TGA_B |
| WRESBAL | 准备金余额 | A5.Reserves_T (÷1000) |

**反爬注意**：FRED 公开 API 免费，需 `FRED_API_KEY`（env），单 IP 120 calls/min。

---

## §2 计算 Derived 字段

```python
# A1 派生
A1.2s10s_bps = (A1.10Y - A1.2Y) * 100

# A2 SOFR 利差（基差另由 ICE/CME 期货价格计算，暂留空或 N/A）
A2.1Y_SOFR_bps = (A1.1Y - SOFR) * 100
A2.2Y_SOFR_bps = (A1.2Y - SOFR) * 100
A2.5Y_SOFR_bps = (A1.5Y - SOFR) * 100
A2.10Y_SOFR_bps = (A1.10Y - SOFR) * 100
A2.30Y_SOFR_bps = (A1.30Y - SOFR) * 100

# A2 状态灯规则
if any(spread < 0): 状态灯 = "🔴危险"
elif any(spread < 10): 状态灯 = "🟡紧张"
else: 状态灯 = "🟢正常"

# A5 SOFR Sprd（bps）
A5.SOFR_Sprd_bp = (SOFR - IORB) * 100

# A5 风控状态
if SOFR_Sprd_bp > 17: 状态 = "🔴危险"
elif Reserves_T < 2.8: 状态 = "🚨极危"
elif ON_RRP_B < 200: 状态 = "🟡紧张"
else: 状态 = "🟢正常"
```

---

## §3 贵金属 q 值（白银/黄金）

需要额外抓 COMEX 期货数据（CME 官方 settlement）：
- `scrapers/cme_metals.py`：抓 Silver active month, Gold active month, Platinum active month
- 计算公式：`q = r - (F - S) / (S * t)`
  - r = 3M SOFR (decimal)
  - F = 期货 settle
  - S = LBMA spot
  - t = 到期日 / 360

写入 A5.Gold_q, A5.Silver_q, A5.SGE_Premium_USD（上海金溢价）

---

## §4 写入 Notion

对每个 DB，先 query 今日是否已有行（避免重复）：

```
notion-search(query="2026-MM-DD", data_source_url="collection://<A1_id>")
```

若无，调用 `notion-create-pages` 写入 A1 / A2 / A5 各一行。**Title 字段 Date 用 ISO 格式 `YYYY-MM-DD`**。

**关键 ID**：见 `../notion_db_ids.json` —— 严禁硬编码。

---

## §5 失败处理

- API 调用失败 → 该字段填 `null`，AI 短评填 `"数据缺失，详见 logs/{date}.log"`
- 不得用前一日值伪造（遵循全局规则 §2.10 显式失败）
- 写入失败 → 日志记录 + 在 A7 当日行的 `运行状态` 字段填 `❌失败`

---

## §6 触发下一步

完成后触发 `03_morning_ai_analysis.md`（09:30 启动）。
