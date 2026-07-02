# Hermes 任务:生成 COMEX 贵金属日报并写入 Notion

> 给 Hermes 的标准任务模板。每天换一下 §1 的"目标日期"就能复用。

---

你是 COMEX 贵金属市场首席风控官。今天的任务是基于 **Notion 4 张源表**里已经解析好的结构化数据,生成一份 **2026 年 5 月 28 日**的深度日报,并把结果写回 Notion 分析库。

## §0 严格范围

**只分析三种**:**Gold(GC/OG) / Silver(SI/SO) / Platinum(PL/PO)**。

不要分析 Palladium、Copper、基本金属——即便数据里出现这些也忽略。这是用户明确的范围决策(2026-05-29)。

## §1 目标日期与读取的数据源

**目标业务日期**:`2026-05-28`(若该日数据未齐则向前找最近一个 Parse Status=OK 的日期)。

通过 Notion 连接器读取以下 4 张库的最新可用行,**每条都先看 `Parse Status` 是否为 OK**——非 OK 的数据**绝不采用**(直接在最终输出里明确"X 数据当日解析失败,未采用"):

| 库 | DB ID | 读取字段 |
|---|---|---|
| CME 库存 `Daily auto tracking` | `2e047eb5fd3c80d89d56e2c1ad066138` | Au/Ag/Pt 当日行的:`Total Registered`、`Total Eligible`、`Net Change`、`Reg/Total Ratio`、`Activity Note`(含 `[Stock]` 金库收提 + `[Delivery]` 席位明细) |
| OI `OI` | `2fc47eb5fd3c8035ab22cabf3e6e41bb` | 当日行的:`OI Futures (JSON)`(8 codes,关心 GC/SI/PL/MGC/SIL/QO/QI/SIC)、`OI Options (JSON)`(关心 OG/SO/PO × CALL/PUT) |
| CFTC `CFTC Con H` | `2c747eb5fd3c808186ddd0aeb45d5046` | 最新一行的 `COT (JSON)`(关心 GOLD/SILVER/PLATINUM/MICRO GOLD 的 oi、oi_change、concentration[8]、traders_total) |
| iShares SLV `SLV` | `2ba47eb5fd3c80c6a0c1ce9f47ec5d25` | 当日行 `Ounces In trus`(注意拼写)、`Shares Outstanding`、`Price` |
| **SGE 银库存周报** `极简每日追踪表 Silver` (筛 `市场=SGE`) | `2bc47eb5fd3c80f3a71ad8de149a4943` | 最新 1~2 周行:`SH库存吨`(SGE 银库存,单位吨)+ `Silver日期`(周末日);若想看趋势,拉过去 4~12 周 |
| **SHFE 沪金/沪银周库存** `极简每日追踪表 Gold/Silver` (筛 `市场=SHFE`) | Gold `2bc47eb5fd3c8083966eecfd9f396b44` / Silver(同上) | 同 SGE,目前 SHFE 数据源在恢复中,**没有就标"SHFE 数据本期暂缺",不要 abort 整个报告** |

**JSON 反转义提醒**:`OI Futures (JSON)` / `OI Options (JSON)` / `COT (JSON)` 通过 notion-fetch 拿回来时,字符串里 `{` `}` `[` `]` 会被 Markdown 渲染层加上 `\` 反斜杠转义。`json.loads()` 前必须先做 `s.replace('\\{','{').replace('\\}','}').replace('\\[','[').replace('\\]',']')`。

## §2 必须涵盖的 6 个分析维度

按这 6 个维度组织分析。每个数字都要可追溯到上面 4 张表的具体字段。

### 1. 实物交割流向:谁在 Issue / 谁在 Stop
- 从 CME 库存 Activity Note 的 `[Delivery]` 段,拆出 Au/Ag/Pt 三个合约当日的关键席位
- 重点标注大行(BofA / JPM / BNP / HSBC / Wells / Citi / Scotia / StoneX 等)的发货 vs 接货方向
- 给出当日 TOTAL 手数,对比 MTD(如果有)

### 2. 库存物理流向:Eligible / Registered 失血 + 东方对照
- 三种金属的 CME 当日 Net Change,推断方向(失血 / 入库 / 横盘)
- Reg/Total Ratio 落在哪个区间(看历史区间判断稀缺度)
- 从 `[Stock]` 段拆出当日有动作的具体金库(Brink's / JPMorgan / Asahi / HSBC / Loomis 等)
- **★ 东方对照(2026-05-30 新增)**:从 Silver DB `市场=SGE` 行拉**最新 1 周 + 过去 4 周**,看 SGE 银库存周环比:
  - 周环比 +5%~+10% 🟡 累库;> +10% 🟠 强累库;> +20% 🔴 暴力累库
  - 周环比 -5%~-10% 🟡 失血;< -10% 🟠 强失血
  - 必须跟 CME 银 Net Change **共振判断**:东方累库 + 西方失血 = "东方虹吸西方"叙事
- **SHFE 沪金/沪银**(如有数据)同样思路;**无数据时只写一句"SHFE 本期数据暂缺"**,不要 abort

### 3. OI 异动:期货
- Au/Ag/Pt 主力合约(看 top3 里 oi 最大的那个月)的 OI 与变化
- 远月有没有异常建仓(看 top3 里 oi_chg 绝对值大的)
- 微型 / E-mini 合约(MGC/SIL/QO/QI/SIC)是否出现机构借小合约调敞口

### 4. OI 异动:期权
- OG_CALL vs OG_PUT、SO_CALL vs SO_PUT、PO_CALL vs PO_PUT 的 OI 与变化
- CALL/PUT 比例反映看涨/看跌结构
- 大幅 chg 可能暗示 dealer gamma 头寸调整

### 5. CFTC 持仓集中度
- GOLD/SILVER/PLATINUM/MICRO GOLD 的:
  - OI 总量 + 周变化
  - 集中度 8 维:`[G4L, G4S, G8L, G8S, N4L, N4S, N8L, N8S]`(Gross/Net × 4/8 largest × Long/Short)
  - 4 大空头集中度 > 50% 通常是逼空信号

### 6. iShares SLV 资金面
- 当日 Ounces 与昨日比的变化(如果能拿到历史行)
- Shares Outstanding 变化反映 ETF 申购赎回
- Price 与 Ounces 走势背离时,暗示套利窗口

## §3 输出要求

### 3.1 写入 Notion 分析库

库:**`Delivery Notice & AI Analysis`**(DB ID `2be47eb5fd3c80bab065f188139834b9`)

- **`Name`** = `日报 2026-05-28`(或对应日期)
- **`Date`** = 2026-05-28
- **`Period`** = `Daily`
- **`Hermes Analysis `** ← **注意列名带尾随空格!写入时必须完全一致**。内容是**短评**,**≤ 300 字中文**,一句话定性 + 3~5 个最关键的数字 + 一句战术建议
- **detail page 正文** ← 完整长文,markdown 格式,按 §2 的 6 个维度分节

### 3.2 短评示例(给个感觉,不要照抄)

> 5/28 黄金交割 BofA 单日发货 1698 手承压,法巴 1319 手强吃;主力 8 月 OI +44,445 手宏观资金加码远月。白银 7 月主力 OI 71,742 手稳守,但 Eligible 失血 121 万盎司,物理脱水加剧。SLV 持仓维持 4.88 亿盎司,SGE 实物溢价高悬利好继续锁多。**战术:核心多头不动,警惕 6 月初纸面横盘消磨期权时间价值。**

### 3.3 长文风格

- 中文简体,风控官口吻(决断、紧凑、不啰嗦)
- 适度用 emoji 强化关键风险点:🚨(警报)🔥(高 risk)💡(洞察)⚔️(战术)
- 章节结构清晰,每节末尾给"风控定性"或"信号读数"小结
- 引用每个数字都要带来源(如"GC AUG26 OI=261,561 (+7,310,来自 5/28 Section62)")
- 末尾给 **3 条战术动作**(对持仓 / 加仓 / 减仓的具体建议)

## §4 数据完整性纪律(强制)

- Parse Status != OK 的源行,**绝不引用其数字**——直接在长文里写"X 库当日解析失败,本期分析不采用"。
- 所有数字必须能追溯到上面 4 张库的具体字段,**严禁基于历史印象编造**。
- 若某个维度数据完全缺失(例如 CFTC 还没出新一期),长文里坦白写"该维度本期无新数据"。

## §5 写入失败的处置

如果 `Hermes Analysis ` 列写入报错"列名不匹配",首先检查列名是不是漏掉了尾随空格(`Hermes Analysis ` 而不是 `Hermes Analysis`)。

如果 Notion 连接器 API 报 timeout,retry 1 次;还失败就把完整分析存到本地 `/tmp/hermes_daily_2026-05-28.md` 让用户手动贴。

## §6 完成确认

任务完成后回报:

1. 引用了哪几张源表的哪个日期的数据
2. 哪些维度因数据缺失或 Parse Status 失败未覆盖
3. 写入分析库的 page URL
4. 短评的具体内容(让用户先看一眼)

---

## §7 外部宏观参考数据(尽力而为,需要 web search 能力)

§1~§6 全部基于 Notion 4 张源表。但要做到 Gemini 范例那种"宏观穿透"深度,**需要补充以下外部公开数据**——这些不在 Notion 里,需要 Hermes 通过 web search 工具(`web_search` / `tavily_search` / `firecrawl` / 等)实时查询。

**前置自检**:开始 §7 前,先告诉用户你**有没有**可用的 web search/fetch 工具。
- 没有:整个 §7 跳过,在长文里写"本期无外部宏观数据,仅基于 Notion 源表"。
- 有:按下面逐项尽力而为。**找不到就坦白说"未获取",绝不臆测**。

### 7.1 上海金交所(SGE)实物溢价(每日必查)

- **目标**:Au9999 / Ag99.99 / Pt99.95 的当日收盘价
- **来源**:`https://www.sge.com.cn/` 或 search "SGE Au9999 closing price YYYY-MM-DD"
- **算法**:SGE 价(人民币计,换算美元/盎司)-COMEX 主力合约结算价 = 实物溢价
- **信号读数**:
  - 黄金溢价 > $10/oz → 东方实物饥渴
  - 白银溢价 > 5% → 强逼空预警
  - 铂金溢价持续 > $5/oz → 工业实物紧

### 7.2 瑞士联邦海关贵金属出口(月度,有 4~6 周滞后)

- **目标**:瑞士 → 中国/印度/香港 的 Au/Ag/Pt 出口吨数
- **来源**:`https://www.gate.ezv.admin.ch/swissimpex/` 或 search "Swiss federal customs gold export <month>"
- **关注口径**:最近月度 vs 上月环比、vs 去年同月同比
- **信号读数**:
  - 月环比 +30% 以上视为强信号(实物东移加速)
  - 单月对华出口 > 100 吨黄金 = 历史级峰值

### 7.3 CME EFP / EFR 成交比

- **目标**:Gold / Silver / Platinum 的 EFP(Exchange For Physical)与期货成交比
- **来源**:CME 每日 "Statistical Reports" 的 Block Trade / EFP 部分,或 search "CME gold silver EFP volume daily"
- **信号读数**:
  - EFP / 期货成交比 > 30% → 场外暗盘活跃,纸面定价被绕过
  - 白银 EFP > 35% → 逼空预警(做市商正私下结算化解多头)

### 7.4 主要分析师当周观点(可选,加分项)

- **目标**:大行金属研究员的当周观点
- 名单:TD Securities **Daniel Ghali** / RBC **Christopher Louney** / BofA / JPM Global Metals / Goldman Sachs Metals
- **来源**:他们的 X/Twitter post、Kitco 转载、Reuters 转载
- **引用规范**:必须标"按 X/Kitco/Reuters 报道,YYYY-MM-DD",不能编造、不能改写
- 找不到当日的就说"未获取"

### 7.5 数据完整性(延续 §4 纪律)

- 找不到 → 写"未获取"
- 数据日期与目标日期不一致(SGE 当日 / 瑞士月度 / EFP T-1)→ 必须标明实际数据日期
- 引用必须可追溯到具体 URL 或来源
- 重点:**Gemini 范例那篇的"瑞士对华白银出口 +120%"是月度数据,不是当日**——别把月数据冒充日数据
