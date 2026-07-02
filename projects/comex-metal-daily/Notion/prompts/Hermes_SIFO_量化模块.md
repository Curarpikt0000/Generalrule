# §8 SIFO 双轨隐含租赁费率(量化核心模块)

> 给 Hermes 的可执行规范。本模块对 Au / Ag / Pt 三品种,**纸面**与**物理**两个市场,**独立计算**隐含租赁费率 $q$,产出 6 个数字,然后做三步审计闭环。
> 这是 Gemini 范例那篇"风控官报告"最有杀伤力的引擎——逻辑闭环、官方数据驱动、可证伪。

---

## 符号约定（全局统一，不可绕过）

```
ΔS     = S - F           正号 = Backwardation（实物挤压方向，S金融 > F期货）
ΔS_phy = S_phy - F       正号 = SGE 物理 > 西方期货 = 实物溢价
q      = r - (F-S)/(S*t) 正号 = 高 lease rate = 借方付天文租金 = physical squeeze 信号
```

**§8 每次输出必须显示原始 F, S_fin, S_phy 三个绝对值，方便人工复核。**

---

## §8.1 模型定义

**纸面隐含租赁费率**:

$$q_{fin} = r - \frac{F - S_{fin}}{S_{fin} \times t}$$

**物理隐含租赁费率**:

$$q_{phy} = r - \frac{F - S_{phy}}{S_{phy} \times t}$$

**解读**:
- 正常 contango(F > S):公式分子为正,q < r,长头需要支付 carry 才能持有
- 倒挂 backwardation(F < S):公式分子为负,**减去负值变成加正值,q > r,租金费率拉升**
- 极端短缺时 q_phy 可坍塌为负值 → 多头宁可搬走现货也不要纸面利息 → **挤兑警报**

---

## §8.2 数据采集协议(强制权威源,不许算法外推)

### r ─ 无风险基准(3-Month SOFR Term Rate)

- **来源**:纽约联储 https://www.newyorkfed.org/markets/reference-rates/sofr
- **取值**:当日 3M SOFR Term Rate(若当日未发,用最近交易日)
- **备用 fetch**:FRED API `https://api.stlouisfed.org/fred/series/observations?series_id=SOFR&...`(需要 API key)或 search "3-month SOFR term rate today"
- **格式**:百分比小数(如 4.32% → `0.0432`)

### F ─ COMEX 期货活跃合约结算价

#### ⚠ 强制规则：F 只能用 Section62 PDF settle，严禁用 Yahoo 连续期货

**严禁用 Yahoo `SI=F` / `GC=F` / `PL=F` 连续期货！** 这些 ticker 会在合约切换日跳价（如 6/10 SI=F=$64.62 连续期货 vs SIN26 settle=$65.35，差 $0.73/+1.1%）。

| 品种 | 合约规格 | 当前活跃月(2026-06-10 视角) | OI 验证 |
|---|---|---|---|
| Au | COMEX 100 Gold Futures | **AUG26**(JUN26 已进 FND,主力转 AUG) | Notion OI 库 GC.top3 第一名 |
| Ag | COMEX 5000 Silver Futures | **JUL26** | Notion OI 库 SI.top3 第一名 |
| Pt | NYMEX Platinum Futures | **JUL26** | Notion OI 库 PL.top3 第一名 |

- **取值规则**:OI 最大月份的当日 settlement price(不是 last 不是 bid/ask)
- **来源**:CME Group Daily Bulletin Section 62 PDF(Notion `OI` 库的 `File` 字段那个 PDF)
- **结算价的位置**:在我们解析的 JSON 里**没有保存**(parser 只存了 OI 和变化),Hermes 要么:
  - (a) 直接 fetch `Section62_Metals_Futures_2026-05-29.pdf` 自己读结算价(URL 在 Notion `File` 字段里),或者
  - (b) 去 `https://www.cmegroup.com/markets/metals/precious/gold.settlements.html` 查官方结算
- **不能凑数**:不能用 Investing.com 的"latest price",必须是 CME 官方 settlement

### S_fin ─ 金融现货(LBMA 国际定盘)

#### ⚠ 强制规则：S_fin 是 LBMA 定盘价，不是 SGE 折算

**S_fin ≠ S_phy！** 6/10 报告原来的错误就是把 SGE Ag(T+D) 15,503 元/千克折算的 $71.18 当成 S_fin（实际 S_fin 应该是 LBMA 6/9 fix=$68.60）。两个变量在代码中彻底分清。

| 品种 | 符号 | 取值规则 |
|---|---|---|
| Au | XAUUSD | LBMA PM Fix(伦敦下午定盘) |
| Ag | XAGUSD | LBMA AM Fix |
| Pt | XPTUSD | LBMA AM Fix |

- **来源**:https://www.lbma.org.uk/prices-and-data
- **备用**:Kitco / Investing.com 当日 LBMA fixing 转载
- **单位**:USD/oz

### S_phy ─ 物理现货(优先境内 SGE)

| 品种 | SGE 品种 | 取值 |
|---|---|---|
| Au | Au9999(99.99% 金) | 当日午盘定盘价 元/克 |
| Ag | Ag(T+D) | 当日收盘价 元/克 |
| Pt | Pt99.95 | 当日收盘价 元/克 |

- **来源**:https://www.sge.com.cn/ 当日行情(Hermes 已经在抓了)
- **单位换算**:`S_phy_USD = SGE_CNY_per_g × 31.1035 / USDCNY_rate`
  - 31.1035 g/oz 是金衡盎司换算
  - USD/CNY 来源:**中国外汇交易中心(CFETS)当日中间价** https://www.chinamoney.com.cn/(取离岸 CNH 也可)
- **示例(Hermes 已经拿到的 Au 数据)**:
  - SGE Au9999 5/28 午盘 985.98 元/克
  - 假设 USDCNY 5/28 中间价 7.20
  - S_phy_Au = 985.98 × 31.1035 / 7.20 = **$4,258.6/oz**

### t ─ 到期变量精度

$$t = \frac{\text{Active Contract FND} - \text{Today}}{360}$$

**COMEX 各品种 FND 规则**:
- Au:交割月前一个月的最后一个交易日(如 AUG26 FND ≈ 2026-07-31)
- Ag:同上(JUL26 FND ≈ **2026-06-30**)
- Pt:同上(JUL26 FND ≈ **2026-06-30**)

**示例(2026-06-10 视角)**:
- t(Au AUG26)= (2026-07-31 - 2026-06-10) / 360 = 51 / 360 ≈ **0.1417**
- t(Ag JUL26)= (2026-06-30 - 2026-06-10) / 360 = 20 / 360 ≈ **0.0556**
- t(Pt JUL26)= (2026-06-30 - 2026-06-10) / 360 = 20 / 360 ≈ **0.0556**

**⚠ FND 修正历史**: Hermes 文档原来写 Pt JUL26 FND=6/27（周六），Ag JUL26 FND=6/27（周五）。实际 CME 官方 Last Trade Day / First Notice Day 为 6/30（Au AUG26 7/31，Ag/Pt JUL26 6/29 是 Last Trade，6/30 是 FND）。见 Section62 PDF 最后 "METALS CONTRACTS LAST TRADE DATES" 表 SI FUT 行。Confirmed 2026-06-10 by coco。**勿再用 6/27。**

**FND 备查**:https://www.cmegroup.com/tools-information/holiday-calendar.html → 选 Metals → 看具体合约 First Notice Day。

---

## §8.3 三步审计闭环(强制执行)

### 第 1 步:基准比对

- 抓的 SOFR 与 NY Fed 官方一致吗?抓的 F 与 CME 官方 Section 62 settlement 一致吗?
- 任何一项偏差 > 0.5%,**强制重抓**,不能算下去。

### 第 2 步:Reality Gap 测算

$$\Delta S = S_{phy} - S_{fin}$$

- 算出三个金属的 ΔS(USD/oz)
- 阈值表:

| ΔS / S_fin | 含义 | 风控读数 |
|---|---|---|
| < 1% | 正常,套利通道顺畅 | 🟢 |
| 1% ~ 5% | 物理偏紧,东方需求 | 🟡 |
| 5% ~ 10% | 实物虹吸明显 | 🟠 |
| **> 10%** | **东方实物正强行解构西方票据定价权** | 🔴 |

### 第 3 步:金库失血交叉验证

把算出的 **q_phy 负值幅度** 与 CME 库存的物理流动做共振:

- **q_phy < 0%** + 当日 **Eligible Withdrawn > 100 万盎司**(看 Notion CME 库存库 `Activity Note` 的 `[Stock]` 段)→ 物理断裂确认
- **q_phy < -1.5%** + 清算所自营盘(席位 **991 H CME CLEARING**)越界出现在 Stop 方(看 `[Delivery]` 段)→ **🔴 红色警报**,清算所亲自下场截货说明后台拆解兑付出现摩擦

---

## §8.4 输出格式(写进长文 §8 节)

每个金属一个表 + 一句风控读数。建议这样:

```markdown
### Gold (Au) — JUN26 已 FND,主力 AUG26

| | 纸面(Paper) | 物理(Physical) |
|---|---|---|
| F (CME settle) | $4,500.40 | $4,500.40 |
| S | XAUUSD $4,495.20 | SGE Au9999 $4,258.60 |
| t | 0.175 | 0.175 |
| **q** | **6.18%** | **-3.21%** ⚠️ |

- **ΔS** = $4,258.60 - $4,495.20 = **-$236.60/oz**(-5.3%,SGE 折价)
- **风控读数**:与 5/24 Gemini 范例的 SGE 溢价 +$16.85 反向,提示当前 5/28 SGE 黄金转入相对折价区间——可能东方近期已完成阶段性吸货,需进一步确认 USDCNY 中间价是否被低估了换算。
```

(上面只是格式范例,**真实数字 Hermes 必须自己拿数据算**,不能照抄)

---

## §8.5 信号阈值速查（2026-06-10 校正版）

### 方向优先（不可绕过）

先判 ΔS 方向，再解读 q_phy 幅度：

| ΔS 方向 | 物理含义 | 解读规则 |
|:--------:|:---------|:---------|
| **ΔS > 0** (Backwardation) | 现货升水，物理紧张 | q_phy 正值为 squeeze 信号生效 |
| **ΔS < 0** (Contango) | 期货升水，物理宽松 | 反向解读，q_phy 无论数值都不是挤兑 |
| **ΔS ≈ 0** | 平水 | 无信号 |

### q_phy 阈值（校正版，反映 >100% 的观察现实）

| q_phy | 方向 | 信号 |
|:----:|:----:|:----:|
| > +50% | ΔS>0 (Backwardation) | 🔴 物理极端 squeeze：套利通道堵塞+SGE高溢价+COT空头集中 |
| > +5% ~ +50% | ΔS>0 | 🟠 物理偏紧 |
| -2% ~ +5% | ΔS>0 | 🟢 物理正常 |
| < -2% | ΔS>0 | 🔴 物理过剩（贵金属罕见） |
| 任意正值 | ΔS<0 (Contango) | 🟡 物理宽松+paper过升（反向解读） |
| <0 | ΔS<0 | 🟢 正常 Contango 区间 |

---

## §8.6 写入位置

把 §8 整段插在长文 §6(SLV)之后、§7(SGE/瑞士外部数据)之前。或者直接合并:**§7 + §8 合成一个"宏观穿透与量化温差"大节**——这是风控官报告的杀手锏所在。

短评里若 q_phy < -1.5%,必须在 `Hermes Analysis ` 列加一句 `⚠️ <金属> 物理断裂预警 q_phy=-X.XX%`。
