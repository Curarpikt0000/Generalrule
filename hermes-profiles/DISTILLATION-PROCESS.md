# 人格蒸馏流程：从公开资料到 Hermes Skill

> **目标**：把一个真实的思想家/投资人/伟人，"蒸馏"成一个可被 AI 调用的镜片（SKILL.md + references/），保留其核心思维方式和表达风格，但不编造其未表达过的观点。
> 
> **适用读者**：想自己蒸馏新大师的 Hermes Agent 或其他 AI agent。
>
> **📌 统一方法论 SSOT**：通用蒸馏 skill 在 `../self-skill/persona-distillation/`（女娲方法论改造，所有 agent 可取用）。本文件是它在「Hermes profile 议会模式」场景的落地说明——两者共享同一条第一铁律（§5 防编造）。蒸馏新人格前，**先读 `self-skill/persona-distillation/SKILL.md`** 拿完整六维度流程 + Agentic Protocol + 质量自检脚本，再回本文件看 profile 落地细节。

---

## 1. 蒸馏的本质

不是"复制人格"，而是 **提取思维镜片 + 约束回答范围 + 建立引用溯源**。

```
公开资料（著作、访谈、股东会）
    │
    ▼
蒸馏提取：核心思维（镜片） + 表达风格（DNA） + 局限性
    │
    ▼
SKILL.md（定义镜片 + 适用场景 + 引用来源）
    +
references/（可回溯的原始材料）
```

**关键心态**：大师在其擅长领域内是专家，在其不擅长的领域，一个诚实的大师会说"这不在我的镜片里"。

---

## 2. 蒸馏级别

根据资源/时间不同，有三种蒸馏级别：

### Level 1：引用源蒸馏（基础，～2 小时）

**适用**：已有成熟开源技能库（如 nuwa-skill、investment-master-mindset）

步骤：
1. 从现有 skill 库拉取 SKILL.md
2. 检查 references/ 是否存在真实来源（著作章节、访谈原文片段）
3. 补议会模式声明（身份声部覆盖）
4. 补数据源映射（如有）
5. 烟雾测试 — 问一个该大师典型问题，验证输出是否匹配

### Level 2：开源增强蒸馏（推荐，～4 小时）

**适用**：有开源 skill 但需要增强/适配

步骤：
1. 取现有 skill 为基础
2. 扩展 references/ 到 3–5 层（思想体系 → 表达DNA → 决策记录 → 外部批评 → 时间线）
3. 与议会模式的 constraints 合并
4. 补局限性声明（大师不擅长的领域）
5. 补适用场景映射表
6. 多问题烟雾测试

### Level 3：手蒸馏（完整，～6–8 小时）

**适用**：完全无现成 skill 的新大师

步骤：
1. **WebSearch 收集原始材料** — 搜索"<大师名> 核心思想"、"<大师名> 采访"、"<大师名> 著名案例"
2. **提取核心镜片** — 哪些问题是他擅长回答的？他对什么感兴趣？他的核心方法是什么？
3. **提取表达DNA** — 语气特点（犀利/耐心/反讽/数据驱动）、常用类比、标志性语言模式
4. **识别局限** — 他在什么领域会是"锤子看什么都像钉子"？他承认自己不懂什么？
5. **整理 references/** — 按六层结构组织：
   - `01-writings.md` — 核心著作摘录
   - `02-conversations.md` — 访谈/语录
   - `03-expression-dna.md` — 表达风格分析
   - `04-external-views.md` — 外部评价/批评
   - `05-decisions.md` — 著名决策案例
   - `06-timeline.md` — 生平时间线（什么阶段形成什么观点）
6. **编写 SKILL.md** — 按标准模板
7. **烟雾测试** — 问 5–10 个典型问题，验证不编造、不越界

---

## 3. SKILL.md 模板

```yaml
---
name: 大师名
description: 一句话定位
---

## 身份声部声明
在本 profile 中，我是大师声部，不独占接管对话。

## 核心镜片（不超过 5 条）
- [最核心的思维方法]
- [第二个]
- [第三个]

## 适用场景
- [场景1]
- [场景2]

## 边界（这不在我的镜片里）
- [大师不擅长的领域]

## 回答风格
- [语气特点]
- [语言习惯]

## 关键数据来源（如有）
| 需求 | 来源 | URL |
|---|---|---|
| [数据1] | [来源名] | [URL] |
| [数据2] | [来源名] | [URL] |

## references/
- 01-writings: 关键著作摘录
- 02-conversations: 访谈/语录
- 03-qa: 常见问题
```

---

## 4. Finance Hero 蒸馏实例

### 来源清单

| 大师 | 蒸馏级别 | 原始技能来源 |
|---|---|---|
| 巴菲特 | L1 | [investment-master-mindset](https://github.com/Cat-Geek/investment-master-mindset) + 补 references |
| 格雷厄姆 | L1 | 同上 |
| 利弗莫尔 | L2 | 同上 + 补深度调研 references |
| 索罗斯 | L2 | 同上 + 补反身性 references |
| 彼得·林奇 | L1 | 同上 |
| 西蒙斯 | L2 | 同上 + 补量化 references |
| 德曼 | L2 | 同上 + 补"好像"模型 references |
| 塔勒布 | L3 | [alchaincyf/taleb-skill](https://github.com/alchaincyf/taleb-skill) + 6 层 references 调研 |
| 芒格 | L3 | [alchaincyf/munger-skill](https://github.com/alchaincyf/munger-skill) + 25 biases 调研 |
| 段永平 | L3 | 手蒸馏（雪球语录 + 网易博客 + 决策记录）|
| 霍华德马克斯 | L3 | 手蒸馏（周期理论 + 投资备忘录）|

### 数据源映射

每个需要行情数据的大师，在 SKILL.md 中注明了数据来源：

| 需求 | 来源 | URL |
|---|---|---|
| CAPE/Shiller PE | multpl.com | https://www.multpl.com/ |
| 历史估值模型 | currentmarketvaluation.com | https://www.currentmarketvaluation.com/ |
| 股票基本面 | Yahoo Finance | https://finance.yahoo.com/ |
| 个股K线/期权 | moomoo OpenAPI | （需本地部署 OpenD） |
| 实时市场验证 | Google Finance AI | https://www.google.com/finance/ |

---

## 5. 防编造纪律 ⛔（第一铁律，所有 Level 强制）

> **任何蒸馏项目，必须用真实联网检索获取一手资料，绝对禁止仅凭训练知识/记忆编造。**
> 这条对 **Level 1/2/3 全部强制**，不分级别、不分人物/主题、不分自动/手工。所有 Hermes 实例在所有蒸馏项目中遵守同一条铁律。
> **统一权威**：本条与通用蒸馏 skill `self-skill/persona-distillation/`（女娲方法论改造）的「第一铁律」是同一条规则。两边内容一致，以 persona-distillation/SKILL.md 为方法论 SSOT，本文件为 profile-蒸馏场景的落地说明。

**这是蒸馏项目踩过最深的坑**：

1. **必须真实发起检索调用** — 不能只靠训练记忆，会编造"听起来对但不存在的语录/数据/近况"。每个调研维度都要有实际 web 检索/抓取动作。
2. **references/ 是关键约束** — 没有引用来源的 skill 会越界编造。每条核心论断标注来源 URL。
3. **逐字引语必须来自真实抓取的页面** — 凭记忆复述的标 `[paraphrase]`，无 URL 的论断标 `[INFERRED-未验证]`，**绝不伪造引号原文**。
4. **派 subagent 调研必须在 context 写死这条铁律**，收回结果时**核对 tool_trace 是否真有检索调用** — 没有 = 没做（哪怕它声称做了），打回重来或主 agent 自己补检索。
5. **每次烟雾测试验证来源** — 问"你这句话是哪里看的？"看 SKILL.md 能否回查。
6. **大师不擅长的领域必须写进 SKILL.md** — 不让大师跨界讲话。
7. **做不到就如实说"检索失败/信息不足"** — 宁可残缺也不编造（general rule §2.10）。

**本环境实测可用的检索通道**（无需特殊权限）：
- `curl` 直连维基 REST API / SEC EDGAR / 官方 IR 页
- `curl "https://html.duckduckgo.com/html/?q=<query>"`（拿真实结果列表）
- `curl "https://r.jina.ai/<URL>"`（读任意页面全文，有 CAPTCHA 的站换源）
- `web_search` / `browser` toolset / `webworms` skill

**反例教训**（真实踩坑，两次）：
- **2026-05-28**：某手蒸馏 skill 记住了"该大师说过 XX"，但该大师从未公开表达过——因无 references/ 约束，bot 连续 3 次编了相同假语录。修复：重写 SKILL.md 加 references/，每段核心论断标来源章节。
- **2026-06-21**：3 个调研 subagent 明明配了 web 工具，却不调用、凭训练知识编内容，其中一个还谎称"无联网权限"（实测环境网络完全正常）。修复：把"必须真实联网"升级为全局第一铁律 + tool_trace 验收硬门，写进本文件与 persona-distillation。

---

## 6. 烟雾测试 checklist

新蒸馏完一个大师，必须过以下测试：

- [ ] "你是谁？" → 正确的身份描述，不越界
- [ ] 一个该大师擅长的问题 → 输出符合其思维框架
- [ ] 一个该大师不擅长的问题 → 诚实说"这不在我的镜片里"
- [ ] 角色扮演问题（"帮忙写邮件/写诗"） → 不跳出金融场景
- [ ] 编造检查（"你关于XXX的看法是什么？"） → 如果有 referenced source 则答，无则说"无公开记录"
- [ ] 数据源检查（"现在PE是多少？"） → 如果有数据源则取数，无则说"未取到"

---

## 7. 框架层面的复用

**可复用**（一个大师出现在多个 profile 中）：
- 芒格（finance + general 都出现，各自的 SKILL.md 有所侧重）
- 塔勒布（同上，finance 侧重风险镜片，general 侧重反脆弱哲学）

**不复用**（同一 skill 跨 profile 拷贝）：
- 直接拷贝物理文件，不共用 symlink —— 每个 profile 独立部署简单重要过"省磁盘"

---

## 8. General Hero 的额外步骤

General Hero 的蒸馏多一个"四件套脚手架"整合：

1. 每个大师的 SKILL.md 要额外标注该大师与四个脚手架的交集
   - 费曼翻译层：该大师的表达适合翻译什么？
   - 证伪自检：该大师最知名的错误判断是什么？
   - 横纵分析：该大师是历时还是共时视角？
   - 演化同类：该大师的"竞争对手/同类"是谁？
2. 综合裁决层要挂接四个脚手架的输出
3. 篇幅限制放宽（≤ 700 字 vs 500 字）
