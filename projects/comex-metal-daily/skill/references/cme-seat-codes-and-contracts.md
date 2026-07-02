# 席位代码对照表 (CME 9大 + 常用)

| 代码 | 名称 | H/C | 备注 |
|---|---|---|---|
| 099 | DEUTSCHE BANK AG | H | 自营, 大额接收方 |
| 118 | MACQUARIE FUTURES | C | 白银发货常客 |
| 363 | WELLS FARGO SECURITIES | H | 白银接货主导 |
| 555 | BNP PARIBAS SEC CORP | C | 黄金接货 |
| 624 | BOFA SECURITIES | H | 黄金发货 |
| 661 | JP MORGAN SECURITIES | C | 多品种活跃 |
| 686 | STONEX FINANCIAL | H/C | 两者都有 |
| 880 | CITIGROUP | H | 多品种 |
| 905 | ADM | C | 小型交割 |
| 077 | Standard Chartered | H | 黄金发货大王 |
| 991 | JP Morgan | H | 自营 |
| 005 | Barclays | C | 黄金发货 |
| 660 | Morgan Stanley | C | 黄金发货 |
| 877 | RBC | C | 黄金发货 |
| 178 | BMO | C | 黄金接货 |
| 435 | Scotia Capital | H | 多品种 |
| 323 | HSBC | C | 多品种 |
| 191 | Dorman | C | 铂金发货 |
| 030 | CME | C | 少量 |

# 金库代码映射

| 代码 | 全称 |
|---|---|
| MANFRA | Manfra, Tordella & Brookes, LLC |
| BRINK'S | Brink's, Inc. |
| ASAHI | Asahi Depository LLC |
| CNT | CNT Depository, Inc. |
| DELAWARE | Delaware Depository |
| JPMORGAN | JPMorgan Chase |
| LOOMIS | Loomis International |
| HSBC | HSBC Bank |

# CME Contract FND Dates
- Au: 交割月前一个月最后一个交易日 (AUG26 FND≈2026-07-31)
- Ag: 同上 (JUL26 FND≈2026-06-30)
- Pt: 同上 (JUL26 FND≈2026-06-27 Friday)

# SGE Contract Reference
| SGE Code | Metal | Unit | COMEX Analog |
|---|---|---|---|
| Au99.99 | Gold 99.99% | CNY/g | GC |
| Au(T+D) | Gold Deferred | CNY/g | GC (same) |
| Ag(T+D) | Silver Deferred | CNY/kg ÷ 1000 = CNY/g | SI |
| Pt99.95 | Platinum 99.95% | CNY/g | PL |

# Section62 PDF Column Layout (COMEX GOLD section)
MONTH VOLUME CHG OPEN HIGH LOW OI OI_CHG SETTLE_PRICE [PT_CHGE]

For settlement extraction by metal:
- GC AUG26 line ~Line 16 after "1 OUNCE GOLD FUTURES" heading
- SI JUL26 line ~Line 2 after "SI FUT COMEX SILVER FUTURES" heading
- PL JUL26 line ~Line 1 after "PL FUT NYMEX PLATINUM FUTURES" heading

Settlement value is the number after OI_CHG column (7th data column in layout mode).
