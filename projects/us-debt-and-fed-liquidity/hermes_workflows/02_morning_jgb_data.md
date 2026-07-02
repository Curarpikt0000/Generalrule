# Hermes Workflow 02：日债 + TONAR 抓取

> **触发时间**：每日 JST 09:00（周一-周五，跳过日本节假日）
> **目标**：抓取 JGB 全期限收益率 + TONAR + 10Y 关键位状态，写入 A3 / A4 / B4

---

## §1 数据抓取

### 优先源：MoF Japan 官方（已实现 → 用 `scrapers/mof_jgb_client.py`）
```
URL: https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/jgbcme.csv
                                                                       ^^^^^^^^
注意：英文站文件名是 jgbcme.csv（带 e），不是 jgbcm.csv (L-2026-05-31-004)。
格式：CSV 每日 15:00 JST 后更新
覆盖期限：1y, 2y, 3y, 4y, 5y, 6y, 7y, 8y, 9y, 10y, 15y, 20y, 25y, 30y, 40y

调用：
  from scrapers.mof_jgb_client import fetch_jgb_latest
  rec = fetch_jgb_latest()
  # → {"date": "2026-05-28", "1Y": 1.12, "2Y": 1.43, ..., "10Y": 2.69, "30Y": 3.99}
```

### 备用源：Investing.com（反爬）
- `scrapers/investing_scraper.py`
- Headers: `User-Agent` 轮换（5 个 UA 池），`Cookie` 缓存
- 间隔：每条 5 秒
- URL 模板：`https://www.investing.com/rates-bonds/japan-{N}-year-bond-yield-historical-data`

### TONAR
- BoJ 官网每日公布：https://www3.boj.or.jp/market/en/menu_m.htm
- 字段：TONAR 利率（%）

### 1M / 3M / 6M JGB
- MoF Japan Treasury Discount Bill 数据

---

## §2 派生字段

```python
# A4 SOFR/TONAR 利差
A4.1M_TONAR_bps = (JGB_1M - TONAR) * 100
A4.1Y_TONAR_bps = (JGB_1Y - TONAR) * 100
A4.5Y_TONAR_bps = (JGB_5Y - TONAR) * 100
A4.10Y_TONAR_bps = (JGB_10Y - TONAR) * 100
A4.30Y_TONAR_bps = (JGB_30Y - TONAR) * 100

# A4 YCC 退出风险
if JGB_10Y >= 2.0: YCC退出风险 = "高"
elif JGB_10Y >= 1.1: YCC退出风险 = "中"
else: YCC退出风险 = "低"

# B4 10Y 关键位
levels = [(1.0, "逼近1.0%"), (1.1, "突破1.0%"), (1.5, "突破1.1%"), (2.0, "突破2.0%"), (2.5, "突破2.5%")]
B4.关键位状态 = max(level for limit, level in levels if JGB_10Y >= limit, default="安全")

# B4 日变动
B4.日变动_bps = (今日JGB_10Y - 昨日JGB_10Y) * 100
B4.周变动_bps = (今日 - 7日前) * 100
B4.月变动_bps = (今日 - 30日前) * 100

# B4 金融股冲击规则
if JGB_10Y >= 1.0 and 周变动_bps > 5: 金融股冲击 = "利好"  # NIM 扩张逻辑
elif 周变动_bps < -10: 金融股冲击 = "利空"
else: 金融股冲击 = "中性"

# B4 科技股冲击（分母效应）
if JGB_10Y >= 2.0: 高PBR科技股冲击 = "利空"
elif JGB_10Y >= 1.1 and 月变动_bps > 20: 高PBR科技股冲击 = "利空"
else: 高PBR科技股冲击 = "中性"
```

---

## §3 写入 Notion

调用 `notion-create-pages` 写入 A3 / A4 / B4 各一行。

---

## §4 失败处理 & 触发下一步

同 `01_morning_us_data.md` §5 / §6。完成后触发 `03_morning_ai_analysis.md`。
