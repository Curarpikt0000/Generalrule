# Hermes Workflow 04：中日央行 + 中日股市资金流抓取

> **触发时间**：每日 JST 12:01（中国大陆 11:01 CST，A 股午盘休市时段）
> **目标**：抓取 PBoC OMO + BoJ 政策 + 中日板块资金流，写入 B2 / B3 / B5

---

## §1 PBoC 数据抓取（B2）

### 主要源
1. **PBoC 官网公开市场操作日报**：
   `http://www.pbc.gov.cn/zhengcehuobisi/125207/index.html`
2. **PBoC 货政司公告**（买断式逆回购）：
   `http://www.pbc.gov.cn/goutongjiaoliu/113456/113469/index.html`
3. **中国货币网（央行直属）**：CFETS 数据
4. **DR007**：上海银行间同业拆放利率页面
5. **A 股两融余额**：上交所 + 深交所每日数据合并

### 字段映射
| Notion 字段 | 数据来源 |
|-------------|----------|
| OMO_净投放_亿 | PBoC 当日 OMO 净投放（投放 - 到期） |
| 买断式逆回购_亿 | PBoC 公告 |
| MLF_到期_亿 | 当日到期 |
| MLF_续作_亿 | 续作量 |
| SFISF_规模_亿 | 累计余额（季度更新） |
| CBS_规模_亿 | 累计余额 |
| A股两融余额_万亿 | 沪深两市合计 |
| DR007_pct | 上海银行间利率 |

### 派生
```python
# 水位状态
if OMO_净投放 < -2000 or DR007 > 3.0: 水位 = "🔴紧张"
elif OMO_净投放 > 2000 and DR007 < 2.0: 水位 = "🟢宽松"
else: 水位 = "🟡平衡"

# 政策信号（综合）
if 买断式逆回购_亿 > 5000 or OMO_净投放_亿 > 5000: 政策信号 = "宽松"
elif OMO_净投放_亿 < -3000: 政策信号 = "紧缩"
else: 政策信号 = "中性"
```

---

## §2 BoJ 数据抓取（B3）

### 源
1. **BoJ 官网每日操作**：https://www3.boj.or.jp/market/en/menu_o.htm
2. **BoJ 政策利率页面**
3. **CNY/JPY、USD/JPY**：Investing.com / 雅虎财经

### 字段
| Notion 字段 | 源 |
|-------------|---|
| JGB_每日买入_亿日元 | BoJ Market Operations 当日实施额 |
| BoJ_政策利率_pct | BoJ 官网 |
| 加息预期_pct | OIS market priced probability（Bloomberg 替代 → Reuters） |
| CNY_JPY | 实时汇率 |
| USD_JPY | 实时汇率 |

### 派生
```python
# QT 进度
if JGB_每日买入 < 1000: QT_进度 = "显著缩减"  # 历史正常 4000+
elif JGB_每日买入 < 2500: QT_进度 = "正常"
else: QT_进度 = "增加"

# YCC 状态：人工 / 看 BoJ 最近公告（DeepSeek 在 12:30 时填）
```

---

## §3 中日板块资金流（B5）

每日一组板块（A 股 4 个 + 日股 4 个 + 港股 2 个 ≈ 10 行）。

### A 股板块（数据源：东方财富 Choice API / 同花顺 iFinD / Wind 替代）
- 电子/科技（代表：300750 宁德、000063 中兴）
- 有色（代表：601899 紫金）
- 金融（红利）（代表：601988 中行、601398 工商）
- 房地产（代表：000002 万科）

### 港股
- 有色（代表：1164.HK 中州矿业 / 0257.HK 中国光大水务 / 0763.HK 中兴 等，按用户持仓）
- 红利（代表：3988.HK 中行）

### 日股
- 金融（代表：8306.T 三菱日联、8316.T 三井住友）
- 电气机器（代表：6857.T Advantest、6526.T 索喜）
- 商社（代表：8058.T 三菱商事）
- 半导体（代表：6920.T Lasertec）

### 字段
| Notion 字段 | 源 |
|-------------|---|
| 主力净流入_亿 | 东财大单净额（A股）/ Nikkei 主力买盘（日股） |
| 换手率_pct | 当日换手 |
| 7d / 15d 趋势 | 计算最近 7/15 天净流入累计 → 映射到枚举 |

### 派生
```python
# 7d 趋势
total_7d = sum(net_inflow[-7:])
if total_7d > 200 and today > 50: 7d = "↑↑↑暴力抢筹"
elif total_7d > 50: 7d = "↑买入"
elif total_7d < -200 and today < -50: 7d = "↓↓↓卖压极重"
elif total_7d < -50: 7d = "↓卖出"
else: 7d = "→震荡"
```

---

## §4 写入 Notion

调用 `notion-create-pages`：
- B2 一行（PBoC）
- B3 一行（BoJ）
- B5 ~10 行（每个板块一行）

---

## §5 触发下一步

完成后触发 `05_noon_ai_analysis.md`（12:30）。
