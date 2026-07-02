# Hermes Notion DB 完整参考(2026-05-30)

> Hermes 每次读/写 Notion 前必读这份。**所有 DB ID、data source ID、列名、类型、需共享的 integration 一次性列清**。
> ⚠ 关键概念:**没有"Gold SHFE"或"Silver SHFE"独立 DB**。所有不同市场(CME/SGE/SHFE/LBMA/LME)的数据都写进**同一张金属 DB**,用 `市场` select 字段区分。

---

## 📋 一、Hermes 全部 Notion DB 全景

| # | DB 名称 | DB ID | Data Source ID | Hermes 操作 |
|---|---|---|---|---|
| 1 | **Daily auto tracking**(8 金属 CME 库存+交割,T1) | `2e047eb5fd3c80d89d56e2c1ad066138` | `2e047eb5-fd3c-8034-a672-000be7162cff` | 只读 |
| 2 | **OI** Daily Bulletin(期货+期权 OI,T2) | `2fc47eb5fd3c8035ab22cabf3e6e41bb` | `2fc47eb5-fd3c-8023-85ec-000b59408356` | 只读 |
| 3 | **CFTC Con H** 周报(T3) | `2c747eb5fd3c808186ddd0aeb45d5046` | `2c747eb5-fd3c-808e-ab46-000bfe7673c5` | 只读 |
| 4 | **SLV iShares**(T4) | `2ba47eb5fd3c80c6a0c1ce9f47ec5d25` | `2ba47eb5-fd3c-8026-b549-000b2a02c5c8` | 只读 |
| 5 | **极简每日追踪表 Gold** | `2bc47eb5fd3c8083966eecfd9f396b44` | `2bc47eb5-fd3c-804c-80bf-000bef46167c` | **读+写**(写 SHFE 沪金行) |
| 6 | **极简每日追踪表 Silver** | `2bc47eb5fd3c80f3a71ad8de149a4943` | `2bc47eb5-fd3c-815f-a0e5-000b0c93ad1d` | **读+写**(写 SHFE 沪银行) |
| 7 | **极简每日追踪表 Pt99.95** | `2d647eb5fd3c801a9ce5d5db4d0b961a` | `2d647eb5-fd3c-81ea-990a-000b045a931c` | **读+写**(本任务也写 SHFE 铂金行,如果 SHFE 当周有铂金库存数据) |
| 8 | **SGE Physical Prices**(SIFO 用) | `9bdc19da05a741089ab79e2779d32e89` | `33747d3d-631b-45e8-958f-6a6ea01c0c82` | 只读 |
| 9 | **Delivery Notice & AI Analysis**(日报输出) | `2be47eb5fd3c80bab065f188139834b9` | `2be47eb5-fd3c-81d8-985b-000b6ed57171` | **只写**(daily 22:00 报告) |

---

## 🥇 二、极简每日追踪表 Gold(SHFE 沪金要写这里)

**DB ID**: `2bc47eb5fd3c8083966eecfd9f396b44`
**Data Source**: `collection://2bc47eb5-fd3c-804c-80bf-000bef46167c`

| 列名(精确拼写) | Type | 写 SHFE 沪金时填什么 | 备注 |
|---|---|---|---|
| `Name` | title | `Gold SHFE 2026-MM-DD`(报告周末日) | |
| `Gold日期` | date | 该周五 ISO 日期 | 用 `date:Gold日期:start` 写入 |
| `市场` | select | `SHFE`(已是预埋选项) | 可选: CME / SGE / SGE/SHFE / SHFE / LBMA |
| `库存频率` | select | `每周` | 可选: 每日 / 每周 / 每月 |
| `SH库存吨` | number(整数) | SHFE 沪金当周库存(单位**吨**,= 千克÷1000) | ★ 这是 SHFE/SGE 数据专用字段 |
| `Gold Reg库存` | number(oz) | **留空**(SHFE 不区分 Reg/Elig) | CME 专用,SHFE 不写 |
| `Gold Elig库存` | number(oz) | **留空** | 同上 |
| `Gold结算价` | number($) | 可填(SHFE 当周末沪金主力合约结算价),不强制 | 加分项 |
| `Vol` | number | 可填(成交量),不强制 | 加分项 |
| `Gold总库存` / `Gold总库存吨` | formula(只读) | **不要写**,Notion 自动算 | |
| `URL` | url | `https://www.shfe.com.cn/reports/tradedata/dailyandweeklydata/` | 可追溯 |
| `说明` | text | `SHFE 沪金周库存(computer use 抓取),增减 X 吨` | 简短说明 |

---

## 🪙 三、极简每日追踪表 Silver(SHFE 沪银 + SGE 银 都写这里)

**DB ID**: `2bc47eb5fd3c80f3a71ad8de149a4943`
**Data Source**: `collection://2bc47eb5-fd3c-815f-a0e5-000b0c93ad1d`

| 列名(精确拼写) | Type | 写 SHFE 沪银时填什么 | 备注 |
|---|---|---|---|
| `Name` | title | `Silver SHFE 2026-MM-DD` | 区别于 `Silver SGE` 和 `Silver YYYY-MM-DD`(CME 命名格式不同) |
| `Silver日期` | date | 该周五 ISO 日期 | 用 `date:Silver日期:start` |
| `市场` | select | `SHFE` | 可选同 Gold DB |
| `库存频率` | select | `每周` | |
| `SH库存吨` | number(整数) | SHFE 沪银当周库存(吨) | |
| `Silver Reg库存` | number(oz) | **留空** | |
| `Silver Elig库存` | number(oz) | **留空** | |
| `Silver结算价` | number($) | 可填(SHFE 沪银主力结算价) | 加分项 |
| `Vol` | number | 可填(成交量) | 加分项 |
| `Silver总库存once` / `SLV总库存吨` | formula(只读) | **不要写** | |
| `URL` | url | `https://www.shfe.com.cn/reports/tradedata/dailyandweeklydata/` | |
| `说明` | text | `SHFE 沪银周库存(computer use 抓取),增减 X 吨` | |
| `Text` | text | 留空 | 历史遗留字段,本任务不用 |

**已写入对照**(给 Hermes 一个去重参考):
- Silver SGE 行:已有 12 行(2026-03-06 ~ 2026-05-22),由 Antigravity backfill 写入
- Silver CME 行:每日,由 GitHub Action 自动写入
- Silver SHFE 行:**还没有,Hermes 本次任务首次写入**

---

## ⚪ 四、极简每日追踪表 Pt99.95(本任务也写,如果 SHFE 当周有 Pt 数据)

**DB ID**: `2d647eb5fd3c801a9ce5d5db4d0b961a`
**Data Source**: `collection://2d647eb5-fd3c-81ea-990a-000b045a931c`

| 列名(精确拼写) | Type | 写 SHFE 铂金时填什么 | 备注 |
|---|---|---|---|
| `Name` | title | `Pt SHFE 2026-MM-DD` | |
| `Pt日期` | date | 该周五 ISO 日期 | 用 `date:Pt日期:start` |
| `市场` | select | `SHFE` | 可选: CME / SGE / SGE/SHFE / SHFE / LME / SGE |
| `库存频率` | select | `每周` | 可选: 每日 / 每周 |
| `SH库存吨` | number(整数) | SHFE 铂金当周库存(吨,= 千克÷1000) | |
| `Pt Reg库存` | number(oz) | **留空** | |
| `Pt Elig库存` | number(oz) | **留空** | |
| `Pt结算价` | number($) | 可填(SHFE 铂金当周末结算价),不强制 | |
| `Vol kg` | number | 可填(成交量,千克) | 加分项 |
| `Vol ounce` | number(整数) | 可填(成交量,盎司) | 加分项 |
| `Pt总库存` | formula(只读) | **不要写** | |
| `URL` | url | `https://www.shfe.com.cn/reports/tradedata/dailyandweeklydata/` | |
| `说明` | text | `SHFE 铂金周库存(computer use 抓取),增减 X 吨` | |

**⚠ 关键不确定性:SHFE 是否实际交易铂金有待 Hermes 现场确认**。
- 如果 SHFE 库存周报页面有铂金品种 → 写入 Pt DB,记录数据
- 如果**没有**(SHFE 历史不交易铂金,以及 2026 是否新增不明)→ **不写 Pt 行**,只在 walkthrough 报告里说一句"SHFE 当周无铂金库存数据,跳过"
- **不要瞎填 0 或 null**(global rule §2.10 Fail Loud)

如果 SGE 未来发铂金库存周报(目前仅银),逻辑同上。

---

## 🚨 五、Integration 权限矩阵(用户必须操作)

Hermes 用 **`Hermes Analysis Issue Report`** integration token(从你给的 NOTION_TOKEN env var 读)。

| DB | 当前是否已共享给 Hermes Analysis Issue Report? | Hermes 需求 | 操作 |
|---|---|---|---|
| Daily auto tracking | ✅ 已共享(daily 报告任务已用过) | 读 | 无需操作 |
| OI | ✅ 已共享 | 读 | 无需操作 |
| CFTC Con H | ✅ 已共享 | 读 | 无需操作 |
| SLV iShares | ✅ 已共享 | 读 | 无需操作 |
| **Gold(极简追踪表)** | ❌ **未共享** | **读+写 SHFE** | **★ 立即添加** |
| **Silver(极简追踪表)** | ❌ **未共享** | **读+写 SHFE+读 SGE** | **★ 立即添加** |
| **Pt(极简追踪表)** | ❌ **未共享** | **读+写 SHFE**(若 SHFE 当周有 Pt 数据) | **★ 立即添加** |
| SGE Physical Prices | ✅ 已共享 | 读 | 无需操作 |
| Delivery Notice & AI Analysis | ✅ 已共享(daily 报告写入) | 写 | 无需操作 |

### 用户必做的 3 步:

打开下面 3 个 DB,右上角 ··· → **Add connections** → 找 `Hermes Analysis Issue Report` → 添加:

1. **Gold 极简追踪表**: https://www.notion.so/2bc47eb5fd3c8083966eecfd9f396b44
2. **Silver 极简追踪表**: https://www.notion.so/2bc47eb5fd3c80f3a71ad8de149a4943
3. **Pt 极简追踪表**: https://www.notion.so/2d647eb5fd3c801a9ce5d5db4d0b961a

(注:之前你给 `goldptsilverupdate` integration 加过这 2 个 DB,Antigravity 的 GitHub job 用那个 token。**Hermes 是另一个 integration,要单独加**——一个 DB 可以同时有多个 integration 都能写,不冲突。)

---

## 📝 六、上下文澄清:为什么没有 "Gold SHFE" 独立 DB

**正确架构**:
```
Gold DB (1 张)
├─ Row 1: 市场=CME,    Gold日期=2026-05-28, Gold Reg=...   ← CME 每日,由 Antigravity 写
├─ Row 2: 市场=CME,    Gold日期=2026-05-29, Gold Reg=...   ← 同上
├─ Row 3: 市场=SHFE,   Gold日期=2026-05-22, SH库存吨=...  ← SHFE 每周,本任务由 Hermes 写
├─ Row 4: 市场=SHFE,   Gold日期=2026-05-15, SH库存吨=...  ← 同上
└─ ... 等

Silver DB (1 张,结构类似)
├─ Row: 市场=CME,  ...
├─ Row: 市场=SGE,  Silver日期=2026-05-22, SH库存吨=834.855  ← SGE 周报,由 Antigravity 已 backfill
├─ Row: 市场=SHFE, Silver日期=2026-05-22, SH库存吨=986.791 ← 本任务由 Hermes 写
└─ ...
```

**每张金属 DB 一个总表,用 `市场` 字段区分数据源**。这套设计的好处:
- 同一金属跨市场对比一目了然(同周 Silver CME / SGE / SHFE 并排看)
- Hermes 分析时一次 query 拿到所有市场数据
- 用户 Notion UI 上 filter `市场=SGE` 就能只看东方现货

如果 Hermes 想"读最新 SHFE 沪银",query 是:
```python
notion_client.databases.query(
    database_id="2bc47eb5fd3c80f3a71ad8de149a4943",  # Silver DB
    filter={
        "and": [
            {"property": "市场", "select": {"equals": "SHFE"}},
            {"property": "库存频率", "select": {"equals": "每周"}}
        ]
    },
    sorts=[{"property": "Silver日期", "direction": "descending"}],
    page_size=1
)
```

---

## 🎯 七、Hermes 本次 SHFE 任务核对清单

执行前对照:
- [ ] 用户已把 `Hermes Analysis Issue Report` 加进 Gold DB connections
- [ ] 用户已把 `Hermes Analysis Issue Report` 加进 Silver DB connections
- [ ] 用户已把 `Hermes Analysis Issue Report` 加进 Pt DB connections
- [ ] Hermes 知道:**不要建新 DB**,写进已有的 Gold/Silver/Pt DB
- [ ] Hermes 知道:`市场` 填 `SHFE`,`库存频率` 填 `每周`,`SH库存吨` = kg ÷ 1000
- [ ] Hermes 知道:Reg/Elig 库存字段**留空**(SHFE 不区分)
- [ ] Hermes 知道:upsert 去重 key 是 (Date + 市场 + 频率) 三联,避免重复写
- [ ] Hermes 知道:**Pt 是 best-effort**——SHFE 当周有 Pt 数据就写,没有就跳过并在 walkthrough 报告里说明,**不要瞎填 0**

执行后回报:
- [ ] 13 周 × 2~3 金属 = **26~39 行** Notion page URL(Pt 视 SHFE 实际有无数据而定)
- [ ] 5/22 SHFE 沪银 总计 = ? 吨(参考截图应为 986.79 吨)
- [ ] 5/22 SHFE 沪金 总计 = ? 吨(截图未含,Hermes 自己抓)
- [ ] 5/22 SHFE 铂金 总计 = ? 吨,**或**"SHFE 当周/历史无铂金品种"
- [ ] 失败明细(如有)
