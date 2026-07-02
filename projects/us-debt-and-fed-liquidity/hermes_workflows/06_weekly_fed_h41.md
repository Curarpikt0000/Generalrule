# Hermes Workflow 06：周度 Fed H.4.1 抓取

> **触发时间**：每周五 JST 18:00（美东时间周四下午 4:30 PM 公布 H.4.1）
> **目标**：抓取最新 H.4.1 → 写入 A6（一行）+ 触发 DeepSeek 周度综合

---

## §1 抓取（FRED API 优先）

| 序列 ID | 字段 |
|---------|------|
| WALCL | Total_Assets_T |
| WSHOTSL | Treasuries_T |
| WSHOMCB | MBS_T |
| WRESBAL | Reserves_T |
| RRPONTSYD（周末值）| ON_RRP_B |
| WTREGEN | TGA_B |
| WCURCIR | Currency_B |
| H41HSTC18 / H41HRMP | RMP_B（储备管理购买）|
| H41HSRF | SRF_B（常备回购）|

**全部数据均为周三收盘（FRED 周四下午 4:30 EDT 发布）**。

---

## §2 派生

```python
delta_reserves = 本周 - 上周 Reserves_T (单位转 $B)
delta_tga = 本周 - 上周 TGA_B

# QT/QE 趋势
total_delta = 本周 - 上周 Total_Assets_T (单位转 $B)
if total_delta < -30: QT_QE趋势 = "📉QT加速"
elif total_delta < 0: QT_QE趋势 = "📉QT正常"
elif total_delta < 10: QT_QE趋势 = "⏸暂停"
else: QT_QE趋势 = "📈QE"

# 审计判定（关键逻辑）
if delta_reserves > 0 and abs(delta_tga) > 100 and delta_tga < 0:
    审计判定 = "Reserves 上涨为 TGA 季节性放水所致，非主动补氧，警惕下周 TGA 反向"
elif delta_reserves < -50:
    审计判定 = "准备金本周下跌 $50B+，关注是否破 $2.8T 警戒线"
else:
    审计判定 = "本周平稳，无显著异常"
```

---

## §3 写入 A6（一行）+ 调用 DeepSeek 长分析

填入 `AI长分析` 字段（DeepSeek 系统 prompt 见 `../deepseek_prompts/crisis_warning.md` 的 weekly 模式）。
