# Hermes 审计令 — 过去 20 天 §8 SIFO q 计算回溯审计 + 修复

> 用户 Claude Chao 在 cowork 发现 6/10 报告 SIFO §8 的 q_fin / q_phy 计算因数据源错误得出反向结论。
> 现在要求**全面审计过去 20 天**所有 daily 报告的 q 计算,识别错误,修复并 PATCH 回原页面。

---

## §1 触发原因(2 个已确认根因 + 1 个符号错)

cowork Claude 在用户 6/10 报告里 spot check,发现:

### 根因 1:F 来源错误 — Yahoo `SI=F` 是**连续期货**,不是 SIN26 specific settle

`SI=F` 是 Yahoo 的 generic front-month 自动滚动 ticker。在月份切换时会跳价。**真实 F 应该是 CME Section 62 Daily Bulletin 里 SIN26(或 Au:AUG26 / Pt:PLN26)的当日 settlement price**,从 Notion `OI` 库 (`2fc47eb5fd3c8035ab22cabf3e6e41bb`) 的 `File` 字段附件 PDF 拿。

### 根因 2:S_fin 来源错误 — Hermes 把 SGE 折算价误用作 S_fin

`S_fin` 应该是 **LBMA 当日定盘价**(Ag: AM Fix,Au: PM Fix,Pt: AM Fix),不是 SGE 折算的 USD/oz。Hermes 6/10 报告里把 SGE Ag(T+D) 15,503 元/千克折算的 $71.18 当成 S_fin,这其实是 **S_phy**。两者搞混导致 q_fin 和 q_phy 都偏。

### 错配 3:ΔS 符号约定不一致

Hermes 在 Au 行用 ΔS = S - F (正号=Backwardation),在 Ag/Pt 行有时翻转。**全局统一**:

```
ΔS     = S_fin - F  (正号 = S>F = Backwardation 短缺信号)
ΔS_phy = S_phy - F  (正号 = SGE 物理 > 西方期货 = 物理紧)
```

---

## §2 审计任务范围

**时间窗:2026-05-22 ~ 2026-06-10**(过去 20 个日历日 = 约 12-14 个交易日报告)

**目标报告**(在 Delivery Notice & AI Analysis DB):
- 5/22 (Fri)、5/26 (Tue)、5/27 (Wed)、5/28 (Thu)、5/29 (Fri)
- 6/1 (Mon)、6/2 (Tue)、6/3 (Wed)、6/4 (Thu)、6/5 (Fri)
- 6/8 (Mon)、6/9 (Tue)、6/10 (Wed)

(周末跳过:5/23-5/25、5/30-5/31、6/6-6/7)

**每份报告审计 6 个 q 值**(Au / Ag / Pt 各 2 个 q):
- q_fin (paper) for Au, Ag, Pt
- q_phy (physical) for Au, Ag, Pt
- = **12 报告 × 6 = 72 个 q 值要核**(Pt q_phy 实际 N/A 部分:SGE Pt 没数据时跳过)

---

## §3 每份报告的 5 步审计流程

### Step 1: 从 Notion 抓原始数据

对每个日期 D,从 Notion 抓:
- **F (Au)** = AUG26 settle(D 当天 Section 62 PDF)
- **F (Ag)** = SIN26 settle
- **F (Pt)** = PLN26 settle
- **S_fin (Au)** = LBMA Au PM Fix D 当天 (https://www.lbma.org.uk/prices-and-data/lbma-gold-price 历史)
- **S_fin (Ag)** = LBMA Ag AM Fix D 当天
- **S_fin (Pt)** = LBMA Pt AM Fix D 当天
- **S_phy (Au)** = SGE Au9999 当天午盘 × 31.1035 / USDCNY 中间价
- **S_phy (Ag)** = SGE Ag(T+D) 当天收盘 × 31.1035 / USDCNY 中间价
- **S_phy (Pt)** = SGE Pt99.95 当天收盘 × 31.1035 / USDCNY (有数据时;周库存只到 5/22,中间日期可能空)
- **r** = 3M SOFR Term Rate D 当天 (https://www.newyorkfed.org/markets/reference-rates/sofr 或 FRED `DGS3MO`)
- **t** = (FND - D) / 360

**FND 日期(2026 各合约,核实过 CME 日历)**:
- Au AUG26 FND = 2026-07-31
- Ag SIN26 FND = 2026-06-30(注意!不是 Hermes doc 里写的 6/27,那是周六)
- Pt PLN26 FND = 2026-06-30(同样,不是 6/27)

### Step 2: 用 doc §8.1 公式重算

```
q_fin = r - (F - S_fin) / (S_fin × t)
q_phy = r - (F - S_phy) / (S_phy × t)
```

### Step 3: 按 doc §8.5 阈值判定灯色

| q_phy | 信号 |
|---|---|
| > r (e.g., > 5%) | 物理紧但未挤兑,🟡 |
| 0 ~ r | 物理 backwardation 形成,🟠 |
| 大幅 < 0 (e.g., -2% 以下) | **🔴 物理断裂红色警报**(但当前模型 q_phy 高正值才是 squeeze 信号,跟 doc 阈值方向需要重新校准 — 见 §4) |

**注意**:doc §8.5 阈值是基于"contango 场景 q_phy 接近 0 或正"的预期写的,但实际数据出现 q_phy 极端正值(>100%) = squeeze 信号。**Hermes 必须按以下校正后的阈值判定**:

| q_phy(新阈值) | 信号 |
|---|---|
| > +50% | 🔴 物理极端 squeeze(套利通道堵塞 + SGE 高溢价) |
| +5% ~ +50% | 🟠 物理紧 |
| -2% ~ +5% | 🟢 物理正常 |
| < -2% | 🔴(罕见,物理"过剩",不太可能在贵金属出现) |

### Step 4: 对比新旧值,记录差异

输出格式:

```markdown
### 2026-XX-XX

| 金属 | 旧 q_fin | 新 q_fin | 旧 q_phy | 新 q_phy | 旧灯 | 新灯 | 变化原因 |
|---|---|---|---|---|---|---|---|
| Au | -3.2% | +4.5% | +7.2% | +12% | 🟢 | 🟢 | 数据源切换;判决不变 |
| Ag | +116.8% | +89.5% | +169.8% | +245% | 🟡 | 🔴 | F 用 Yahoo 连续→Section 62 SIN26;S_fin SGE→LBMA;**判决从 🟡 升 🔴** |
| Pt | +140% | -134% | +284.5% | +156% | 🔴 | 🔴 | 符号反过来;判决仍 🔴(物理紧确认) |
```

### Step 5: PATCH 原报告

把每份报告的:
- §0 风控仪表盘 → 更新对应 cell 的灯色(如 Ag 5/29 从 🟡 改 🔴)
- §8 SIFO 三步审计 → 重写 q 数据 + 加符号约定声明 + 用新阈值
- §9 首席风控官结语 → 如果判决变化(如 Ag 从 🟡 升 🔴),"真相缺口"和"脱节判决"段落必须重写
- §0.5 三战术 → 如果 Ag 升 🔴,战术建议也要升级
- `Hermes Analysis ` 短评列 → 反映新判决(用 [audit-2026-06-10] 标签开头)

**PATCH 不删除原内容**,在 §8 段落顶部加一个 callout block:

```markdown
> ⚠ **审计修正 [2026-06-10]**:本节 §8 SIFO 数据于 2026-06-10 经 cowork Claude 审计,发现原数据源错误(F 用 Yahoo 连续期货 / S_fin 误用 SGE 折算价)。已重算 q_fin / q_phy 并修正灯色判决。原版本数据见 §8.audit-trail。
```

并在 §8 末尾加一个 `<details>` 区折叠原始(错误)数据,保留审计追溯。

---

## §4 数据源精确清单(给 Hermes 实操参考)

### F (CME 期货 settle)

**主路径**:Notion `OI` 库 → 当天行 → `File` 字段 → 点开 Section 62 PDF → 找:
- "GOLD - COMEX" section → 找 AUG26 contract → "Settle" 列
- "SILVER - COMEX" section → 找 SIN26 contract → "Settle" 列
- "PLATINUM - NYMEX" section → 找 PLN26 contract → "Settle" 列

**备路径**(如果 PDF 解析失败):
- CME Daily Bulletin 历史归档: https://www.cmegroup.com/market-data/files/daily-bulletin/
- Barchart 历史: https://www.barchart.com/futures/quotes/SI*0/price-history/historical-prices

**绝对禁止**:用 Yahoo `SI=F`, `GC=F`, `PL=F` — 这些是连续期货,**会在合约切换日跳价**。

### S_fin (LBMA fix)

**主路径**:LBMA 历史下载: https://www.lbma.org.uk/prices-and-data/precious-metal-prices → "Download" CSV
- LBMA Gold AM/PM Fix
- LBMA Silver Fix (only one daily fix at 12:00 noon London)
- LBMA Platinum AM/PM Fix
- LBMA Palladium AM/PM Fix

**备路径**(LBMA 拉不到):
- MacroMicro: https://en.macromicro.me/series/4886/lbma-gold-price (Au), https://en.macromicro.me/series/7949/lbma-silver-price (Ag)
- Kitco daily fix archive

### S_phy (SGE 收盘价折 USD)

**SGE Au9999 / Ag(T+D) / Pt99.95**:
- 当天收盘价(元/克)→ 从 Notion 现有的 SGE 行抓(SGE Silver 库已经在 Silver DB `市场=SGE`),或者从 https://www.sge.com.cn/ 历史归档
- 折 USD: `SGE_USD_per_oz = SGE_CNY_per_g × 31.1035 / USDCNY_中间价`
- USDCNY 中间价: 中国外汇交易中心 https://www.chinamoney.com.cn/ 历史

**Pt SGE 注意**:SGE Pt 数据不是每日有,可能要用最近一次有数据的日期(填 N/A 时在表格里注明"S_phy N/A, q_phy 跳过审计")

### r (3M SOFR)

**主路径**:FRED API `https://api.stlouisfed.org/fred/series/observations?series_id=SOFR3M` (需要免费 API key,Hermes 应该已有)

**备路径**:NY Fed https://www.newyorkfed.org/markets/reference-rates/sofr-averages-and-index 历史 90 天平均

---

## §5 验证要求(交付前必做)

### 自检 1:用 6/10 数据再算一遍跟 cowork 对答案

```
F = 65.35  (SIN26 settle - 这个其实你用 Yahoo SI=F 的 mid)
S_fin = 68.60  (LBMA Ag 6/9 fix - 用户给的)
S_phy = 75.46  (LBMA + 10% SGE premium 假设)
r = 0.043  (4.3% SOFR)
t = 20/360 = 0.0556

q_fin = 0.043 - (65.35 - 68.60) / (68.60 × 0.0556)
      = 0.043 - (-3.25 / 3.814)
      = 0.043 + 0.852
      = +0.895 = +89.5%   ← cowork 算的值,你必须跟这个对得上

q_phy = 0.043 - (65.35 - 75.46) / (75.46 × 0.0556)
      = 0.043 - (-10.11 / 4.196)
      = 0.043 + 2.409
      = +2.452 = +245.2%   ← 同上

ΔS = 68.60 - 65.35 = +3.25 → Backwardation(正号)
ΔS_phy = 75.46 - 65.35 = +10.11 → Backwardation
```

**如果你算出的 6/10 数字跟以上对不上(差异 > 1%)**:停下来,贴出你用的 F, S_fin, S_phy 三个原始值给用户,先解决数据源问题再继续审计。

### 自检 2:Pt 6/10 重算

用 doc §8.1 公式:
```
F_Pt(假设) = $1805 (PLN26 settle)
S_fin_Pt = $1690 (LBMA Pt AM Fix - 你抓真实值)
S_phy_Pt = $1944 (= LBMA × 1.15,SGE Pt +15% 假设;实际你抓 SGE Pt99.95)
r = 0.043
t = 20/360 = 0.0556

q_fin_Pt = 0.043 - (1805 - 1690)/(1690 × 0.0556)
         = 0.043 - 115/93.96
         = 0.043 - 1.224
         = -1.181 = -118%   ← 负值,paper 极端 contango
         
q_phy_Pt = 0.043 - (1805 - 1944)/(1944 × 0.0556)
         = 0.043 - (-139)/108.09
         = 0.043 + 1.286
         = +1.329 = +133%   ← 正值,physical 极端 backwardation
```

**Pt 6/10 报告里 q_fin 应该是 -118%(不是 Hermes 写的 +140%),q_phy 应该是 +133%(不是 +284%)**。差异源:Hermes 用的 t 可能不一样,以及 F/S 拉错。

### 自检 3:同期 12 份报告交叉验证

把 12 份报告的新算 q_fin / q_phy 列出来,看是否有合理的时间序列(不应有跳跃式异常 — 如果某天 q 突然从 +5% 跳到 +500% 再回到 +10%,大概率是那天 F 或 S 拉错)。

---

## §6 输出要求

### 6.1 审计报告(单独文件)

把审计结果写到:
```
~/hermesagent/Comex Metal Daily Issue Report/Notion COMEX仓单日报/audit_q_calculations_20260610.md
```

包含:
- 12 份报告每份的对比表(旧 q vs 新 q vs 判决变化)
- 总结:哪些日期判决从 🟡 升 🔴,哪些反过来,哪些不变
- 跟 cowork Claude 6/10 算的 q_fin=+89.5% / q_phy=+245% 对比的 sanity check

### 6.2 PATCH 12 份 Notion 报告

按 §3 Step 5 的规则 PATCH。**不删除原内容**,加 audit callout + 折叠原始数据。

### 6.3 修 SIFO 量化模块文档

在 `Hermes_SIFO_量化模块.md` 里:
- §8.2 数据采集协议:在 F 那段加粗"**严禁用 Yahoo SI=F / GC=F / PL=F 连续期货**,必须用 Section 62 PDF 里的 specific contract settle"
- §8.2 数据采集协议:在 S_fin 那段加粗"**S_fin 是 LBMA 定盘,不是 SGE 折算**"
- §8.2 修 FND 日期:Pt PLN26 FND 改成 2026-06-30(原 6/27 是周六,错的)
- §8.5 阈值表:重写以匹配实际观察到的 q_phy >100% 数量级
- §8.0 开头加"符号约定"声明:ΔS = S - F,正号 = Backwardation;q 正号 = lease rate 高 = 物理 squeeze

### 6.4 在 cowork 简短回报(给用户)

格式:
```
✅ 审计完成
- 审计了 12 份报告(5/22~6/10)
- X 份判决变化:Y 份 🟡 升 🔴,Z 份其他变动
- 审计报告:audit_q_calculations_20260610.md
- PATCH 完成的 Notion page URL 列表(12 个直链)
- SIFO 模块 doc 修复:F/S_fin/FND/阈值/符号约定 5 处

⚠ 关键发现:Ag 这 12 天的 q 计算【全部错】,因为 F 用了 Yahoo SI=F 连续期货。修正后 Ag 在 X 个日期判决从 🟡 升 🔴(paper backwardation 信号)。

如果发现历史数据无法精确还原(如 5/22 LBMA fix 拿不到),在审计报告里明确标注 "数据 N/A,跳过"。
```

---

## §7 不在范围

- **不改 Au/Ag/Pt 任何金属在 Notion 库存库 / OI 库 / SLV 库的数据**(那些是原始数据,审计只重算 q)
- **不动 SHFE backfill / SGE backfill**(数据源没问题,只是被错用)
- **不动 Hermes daily cron 配置**(那是另一条线)
- **不动 watchdog**(独立任务)

---

## §8 用户对你的额外期望(诚实文化)

这次发现 2 个数据源错 + 1 个符号错,是个**质量事故**。用户希望你借这次审计:
1. **诚实展示每份报告的"旧 vs 新"对比**,不要只输出新值,要让用户看到错误的程度
2. **在审计报告末尾加一段 "Lessons" 段**:写清楚 (a) 这次为什么错,(b) 怎么防止再犯,(c) 你计划在 SIFO 模块文档加什么自检机制
3. **如果有任何步骤你做不到**(比如某天的 LBMA 历史拉不到),**显式失败 Fail Loud**(§2.10),不要"近似"或"估算"或"用相近日期凑数"

完成后通知用户,用户会跟 cowork Claude 抽 2-3 个日期 spot check 新 q 数字。
