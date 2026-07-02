# COMEX 贵金属日报 — AGENTS.md

> 项目: COMEX 贵金属日报（Comex Metal Daily Issue Report）
> 用途: 自动化生成 COMEX 贵金属日报，覆盖黄金(Au)、白银(Ag)、铂金(Pt)
> 最后更新: 2026-07-02

---

## 项目描述

自动化生成 COMEX 贵金属日报，每天 22:00 JST 自动运行。核心能力包括：

- **交割数据分析**：从 CME 库存表读取当日交割数据，拆解 Ag/Au/Pt 三个合约的席位流向
- **库存物理流向分析**：西方(CME Eligible/Registered) + 东方(SGE/SHFE) 双市场库存共振判断
- **SIFO 双轨隐含租赁费率量化**：独立计算纸面(q_fin)与物理(q_phy)隐含租赁费率，3 步审计闭环
- **OI 期货/期权异动监测**：主力合约 OI 变化 + 期权 C/P 比例 + 微型合约机构行为
- **CFTC 持仓集中度分析**：4 大/8 大空头、多头集中度，逼空信号识别
- **SLV iShares ETF 资金面分析**：Ounces/Shares/Price 三要素背离检测
- **东方库存数据**：SGE 白银 + SHFE 黄金/白银 每周库存趋势（13 周历史数据）

## 核心文件

> 本 Docker 包的文件路径从本项目根目录（`projects/comex-metal-daily/`）开始。

### Notion/ 目录（所有 Hermes prompt 文档）

| 文件 | 用途 | 优先级 |
|------|------|--------|
| `Hermes_定时任务_每日22pm报告.md` | 每日 22:00 主调度规范（含前置检查、数据采集、分析流程） | ★★★★★ |
| `Hermes_COMEX_取数器规格与解析代码.md` | 数据采集 & 解析规则（xls/PDF/JSON） | ★★★★ |
| `Hermes_SIFO_量化模块.md` | §8 SIFO 双轨隐含租赁费率量化核心模型 | ★★★★ |
| `Hermes_分析层任务_Prompt.md` | 分析层标准任务模板（6 维度分析、Notion 写入） | ★★★★ |
| `Hermes_格式改造单_v3_红绿灯.md` | v3 红绿灯输出格式（风控仪表盘 + 信号分级篇幅分配） | ★★★★ |
| `Hermes_LBMA数据源获取_5层降级方案.md` | LBMA 数据获取降级方案（MacroMicro/Kitco/FRED） | ★★★ |
| `Hermes_Notion_DB_完整参考.md` | Notion DB ID、列名、类型完整参考 | ★★★ |
| `Hermes_通知_SGE+SHFE东方库存上线.md` | SGE/SHFE 东方库存数据接入通知（2026-05-31） | ★★ |
| `Hermes_整改令_文件系统纪律.md` | 文件系统纪律 | ★★ |
| `Hermes_审计令_过去20天SIFO_q重算.md` | SIFO 历史重算审计 | ★ |
| `Hermes_周任务_SHFE库存扫描.md` | 周级别 SHFE 库存任务 | ★ |
| `general-global-rule.md` | 通用全局规则（认知纪律 + 任务执行五步链路） | ★★★ |
| `Antigravity_T_重组_COMEX-Metal-Daily父目录.md` | 项目结构重组记录 | ★ |
| `Antigravity_T5_SGE7日趋势.md` | SGE 7 日趋势任务 | ★ |
| `Antigravity_T6_SHFE+SGE_库存扩展.md` | SHFE+SGE 库存扩展任务 | ★ |
| `Antigravity_T7_SHFE抢救.md` | SHFE 数据抢救任务 | ★ |

### scripts/ 目录

| 文件 | 用途 |
|------|------|
| `sifo_calculator.py` | SIFO 隐含租赁费率计算模块（Au/Ag/Pt 三品种，纸面+物理双轨） |
| `comex_watchdog.py` | 看门狗脚本 |
| `test_sifo_calc.py` | SIFO 计算测试 |

## 重要指针

> **→ 上下文日志**: [docs/context-log.md](./docs/context-log.md)
>
> 包含: Notion DB 全景、定时任务配置、关键依赖文件列表、当前项目状态

## 核心规则

### 1. 定时调度

- **运行时间**: 每日 08:00 JST (UTC 23:00) — **cron `6dc5b547934e`（deepseek-chat）于 2026-06-30 重建，时间从旧 22:00 改到 08:00**
- **前置检查**: 必须验证 5 张源库当日 Parse Status = OK，任一失败则 abort
- **跳过原则**: 不写新 page、记日志、不通知骚扰
- **cron 注册位置**: `~/.hermes/config.yaml`
- **状态**: ✅ 新 cron `6dc5b547934e`（deepseek-chat）已注册并运行成功（7/1 首次运行）

### 2. 数据来源纪律

- **F（期货结算价）**: 只能用 CME Section 62 PDF settle，**严禁** Yahoo 连续期货
- **S_fin（金融现货）**: 只能用 LBMA 定盘价，**严禁** SGE 折算
- **S_phy（物理现货）**: SGE 当日收盘价 × 31.1035 ÷ USDCNY
- **r（无风险基准）**: 3M SOFR Term Rate（FRED `DGS3MO` 备用）

### 3. JSON 反转义提醒

通过 notion-fetch 获取的 `OI Futures (JSON)` / `OI Options (JSON)` / `COT (JSON)` 在返回时会被 Markdown 层加上 `\\` 转义。`json.loads()` 前必须先做：

```python
s.replace('\\\\{','{').replace('\\\\}','}').replace('\\\\[','[').replace('\\\\]',']')
```

### 4. 输出规范

- **格式**: v3 红绿灯仪表盘（§0 顶部 18 灯表 + §0.5 三条战术 + §1~§7 各节 + §8 SIFO 三步审计 + §9 首席风控官结语）
- **灯色逻辑**: 红(必行动) > 橙(密切监控) > 黄(可观察) > 绿(可跳过)
- **写入库**: `Delivery Notice & AI Analysis` (DB ID `2be47eb5fd3c80bab065f188139834b9`)
- **Name 格式**: `日报 YYYY-MM-DD`

### 5. 分析范围限制

- **只分析三种金属**: Gold(GC/OG) / Silver(SI/SO) / Platinum(PL/PO)
- **严禁分析**: Palladium、Copper、基本金属（即便数据出现也忽略）

### 6. 东方库存判定规则

- **Ag**: 取 SGE 和 SHFE 两源中更严重的灯色
  - SGE 12 周累计 > +100% 且持续 4 周以上 = 🔴
  - SHFE 周环比 |ΔV| > 5% = 🟠, > 10% = 🔴
- **Au**: 只看 SHFE（SGE 永久 N/A）
  - 周环比 |ΔV| > 5% = 🟠, > 10% = 🔴
- **Pt**: 永久 N/A（双源缺失）

## 历史里程碑

| 日期 | 事件 |
|------|------|
| 2026-05-28 | Au 回归模型偏差修正（q_phy 骤降） |
| 2026-05-29 | 分析范围严格限定 Au/Ag/Pt |
| 2026-05-31 | SGE 银 + SHFE 金/银 东方库存上线 |
| 2026-05-31 | 项目从 Notion Metal Daily Update 更名为 Comex Metal Daily Issue Report |
| 2026-06-06 | Au 修正问题最终解决 |
| 2026-06-29 | 旧 cron 因 Notion 401 被删除，日报自动生产暂停 |
