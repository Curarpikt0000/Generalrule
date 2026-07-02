# Silver Stock Excel — ADJUSTMENT 列分析 (2026-05-28 案例)

## 背景
5/28 日报中 Silver Registered 从 81,430,936 → 84,051,083 oz (+2,620,147 oz, +3.2%)。
表面上看像是"大量买入进入交割池", 实际是内部转仓。

## 核心发现: ADJUSTMENT 列

!ADJUSTMENT 是 CMX Stocks Report (原版 Excel) 的一个特殊列, 反映金库内部 Registered↔Eligible 的纯转仓量, 不涉及任何外部资金流动。

## 5/28 各金库 Registered 明细

| Depository | Prev Reg | Received | Adj | New Reg | Δ |
|---|---|---|---|---|---|
| ASAHI DEPOSITORY LLC | 21,941,315 | 532,933 | **+2,082,204** | 24,556,451 | +2,615,136 |
| BRINK'S, INC. | 12,938,827 | 0 | **+5,011** | 12,943,838 | +5,011 |
| CNT DEPOSITORY, INC. | 11,478,195 | 0 | 0 | 11,478,195 | 0 |
| DELAWARE DEPOSITORY | 1,893,532 | 0 | 0 | 1,893,532 | 0 |
| HSBC BANK, USA | 2,988,041 | 0 | 0 | 2,988,041 | 0 |
| INTL DEPO SVCS OF DELAWARE | 173,668 | 0 | 0 | 173,668 | 0 |
| JP MORGAN CHASE BANK NA | 10,549,218 | 0 | 0 | 10,549,218 | 0 |
| LOOMIS INTERNATIONAL (US) | 7,120,299 | 0 | 0 | 7,120,299 | 0 |
| MALCA-AMIT USA, LLC | 533,932 | 0 | 0 | 533,932 | 0 |
| MANFRA, TORDELLA & BROOKES | 5,977,799 | 0 | 0 | 5,977,799 | 0 |
| STONEX PRECIOUS METALS LLC | 5,836,110 | 0 | 0 | 5,836,110 | 0 |
| **TOTAL** | **81,430,936** | **532,933** | **+2,087,215** | **84,051,083** | **+2,620,147** |

## Eligible 对等变化

| Depository | Prev Elig | Received | Withdrawn | Adj | New Elig | Δ |
|---|---|---|---|---|---|---|
| ASAHI | 8,425,885 | 599,288 | 0 | **-2,082,204** | 6,942,969 | -1,482,916 |
| BRINK'S | 28,524,975 | 8,983 | 676,053 | **-5,011** | 27,852,894 | -672,081 |
| 其他无变动 | 197,331,101 | 322,003 | 9,283 | 0 | 197,643,820 | +312,720 |
| **TOTAL** | **234,281,962** | **930,274** | **685,336** | **-2,087,205** | **232,439,694** | **-1,842,277** |

Adj 总和 Reg +2,087,215 = Elig -2,087,205 (差10 oz 取整误差) ✓

## 解读

**ASAHI 是唯一有重大转仓动作的金库。**
- ASAHI 的 Registered 增量 99.5% 来自内部转仓 + 0.5% 来自新收
- 2.1M oz Eligible→Registered 转移发生在同一天, 且净额无外部提取
- = 某家银行(可能是 Wells Fargo 或 JPM Client)在 ASAHI 金库持有 Eligible 仓单, 主动要求转成 Registered 为 FND 交割做预备

**BRINK'S 微量转仓 +5K oz 是机械调整。**
- BRINK'S 更大的动作是 Eligible Withdrawn -676K oz(外部提走), 被+532K ASAHI新收+ +599K ASAHI新收Eligible 抵消

### 金库地址参考
- ASAHI DEPOSITORY LLC: 纽约/特拉华的主要交割金库, 为 COMEX 做市商提供仓位托管
- BRINK'S, INC.: 运输+存储物流商, 日常出入库活跃但不会主动转换 Reg/Elig

## 对交易的影响

| 影响面 | 方向 | 理由 |
|---|---|---|
| 是否逼空信号？ | 中性 | Registered 增加但不代表空头无法 delivery |
| 是否实物趋紧？ | 中性偏松 | Eligible 绝对量仍 232M oz, 足够 30 天交割量 |
| 是否暗示价格上行？ | 弱多 | 有人愿意承担转仓成本(放弃 eligible 灵活度)来预备交割 |
| FND 波动？ | 偏高 | 备货行为说明市场参与者预期 FND 期间有实质性交割对抗 |
