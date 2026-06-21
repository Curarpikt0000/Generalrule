# 项目进度与状态

> 最后更新：2026-06-21
> 本文件记录 Hermes 议会模式人格蒸馏项目的完整进度。

---

## 一、项目里程碑

| 日期 | 里程碑 | 状态 |
|---|---|---|
| 2026-05-21 | 单 Hermes + AGENTS.md 覆盖方案（首次架构） | ❌ 已推翻 |
| 2026-05-28 | Hermes Profile 机制发现，架构推翻 | ✅ |
| 2026-05-28 | distil 方法论 handbook v1 完成 | ✅ |
| 2026-05-31 | Finance Hero blueprint 完成 + 部署跑通 | ✅ |
| 2026-05-31 | General Hero blueprint 完成 + 部署跑通 | ✅ |
| 2026-06-13 | 蒸馏方法论定型，模板集完成 | ✅ |
| 2026-06-21 | 上传至 Generalrule 主 repo（本目录） | ✅ |

### 架构推翻记录

**2026-05-21 → 2026-05-28** 的关键发现：

| 旧方案 | 新方案 | 原因 |
|---|---|---|
| 单 Hermes + AGENTS.md 在 channel 内覆盖对话人格 | 每个场景一个独立 Hermes profile | 官方 profile 机制自带隔离，不需要 hack |
| 切人格需要在 channel 内发指令 | 不同 profile 是不同 bot，进不同群自然获得对应人格 | bot 隔离比 prompt 隔离更冷酷可靠 |
| 大师在 memory 里通过 hindsight 持久化 | 大师在 skills/ 里通过 SKILL.md 定义 | memory 是运行时记忆，不是思维定义—混淆了代码和数据的职责 |

---

## 二、已完成资产

### 可运行 Profile（2 个）

| Profile | 大师 | Telegram bot | 状态 |
|---|---|---|---|
| Finance Hero | 11 位投资大师 | 独立 bot，独立 Telegram 群 | ✅ 线上运行 |
| General Hero | 10 位伟人 | 独立 bot，独立 Telegram 群 | ✅ 线上运行 |

### 方法论资产（已定型）

| 文件 | 内容 |
|---|---|
| `handbook/DISTILLATION-HANDBOOK.md` | 5 条铁律 + 全流程 SOP + 4 层议会架构 + 20+ 踩坑教训 |
| `handbook/QUICK-START.md` | 30s 判断当前阶段 → 按 checklist 直接干 |
| `handbook/templates/` | SOUL.template / master-SKILL.template / depth-modes.template / synthesis.template / sync.sh.template / deploy.template / README.template |

### 本地项目资产

| 资产 | 位置 |
|---|---|
| Finance Hero 蓝图 (SSOT) | `~/hermesagent/Distill/蒸馏Hermes/finance-hero/` |
| General Hero 蓝图 (SSOT) | `~/hermesagent/Distill/蒸馏Hermes/general-hero/` |
| 蒸馏 Handbook (SSOT) | `~/hermesagent/Distill/蒸馏Hermes/handbook/` |
| Wiki 导出 | `~/hermesagent/Distill/蒸馏Hermes/wiki-output/` |
| 项目入口 | `~/hermesagent/Distill/AGENTS.md` |
| Finance 运行时 | `~/.hermes/profiles/finance/` |
| General 运行时 | `~/.hermes/profiles/general/` |
| Worker 运行时 | `~/.hermes/`（默认 profile） |

---

## 三、架构决策记录

### 决策 1：Profile 隔离（2026-05-28）

**问题**：单 agent 能否同时服务"金融问答"和"人生通识"两个角色？

**结论**：不能。用 profile 隔离。原因：
- 独立的 bot token（不会在 Telegram 群抢答）
- 独立的 memory（金融分析不会污染人生对话）
- 独立的 skill 库（只加载需要的 skill，减小 context 压力）

### 决策 2：蓝图 ↔ Profile SSOT（2026-05-28）

**问题**：修改后如何部署？直接在 profile 里改还是怎样？

**结论**：蓝图（`Distill/蒸馏Hermes/`）是版本受控源（SSOT）→ `sync.sh` 一键部署到 profile。禁止直接改 profile。

### 决策 3：大师=声部，不独占（2026-05-28）

**问题**：现有 skill 都是"独占人格"模式，如何改为多声部？

**结论**：在 SOUL.md 显式覆盖大师 skill 的 EXIT TRIGGER 规则。大师是声部/分段，主持人保留最后综合权。

### 决策 4：MVP 关 Hindsight（2026-05-31）

**问题**：要不要开跨会话记忆？

**结论**：MVP 关掉。原因：
- Apple Silicon daemon 有已知启动超时 bug（[issue #7135](https://github.com/NousResearch/hermes-agent/issues/7135)）
- 金融问答场景对跨会话记忆需求低（每次问题独立）
- MVP 先跑通核心流程，记忆是锦上添花

### 决策 5：二次验证按需触发（2026-06-04）

**问题**：每次回答都 double-check 会拖慢速度，但完全不 check 又怕数据不准。

**结论**：按需触发模式——用户说"再查一下"等触发词才跑 Google Finance 研究 AI 对账。不污染常规问答。

### 决策 6：数据源回落 web（2026-05-31）

**问题**：moomoo OpenD 未部署完成，行情数据怎么拿？

**结论**：在 moomoo 就绪前使用 web fallback（multpl.com 拿 CAPE/PE，currentmarketvaluation.com 拿估值模型，Yahoo Finance 拿个股财务）。moomoo 就绪后切换。

---

## 四、当前待办

| # | 事项 | 优先级 | 状态 |
|---|---|---|---|
| 1 | General Hero 蒸馏经验沉淀到 Wiki | 中 | 🔲 |
| 2 | 新 profile 蓝图设计（创业/研究/工程师） | 低 | 💡 |
| 3 | 跨 profile 大师复用清单整理 | 低 | 💡 |
| 4 | 议会模式效果跟踪（对比单一 prompt 的胜率） | 低 | 💡 |

---

## 五、已知问题

| 问题 | 严重度 | 说明 |
|---|---|---|
| Apple Silicon Hindsight daemon 超时 | 中 | [issue #7135](https://github.com/NousResearch/hermes-agent/issues/7135)，MVP 关掉规避 |
| moomoo OpenD 未部署 | 低 | 行情数据目前走 web fallback，准确度低于 moomoo API |
| 手蒸馏大师的 references 深度不一 | 低 | 段永平/霍华德马克斯/库恩/福柯等有完整 references，部分大师仅 L1 |
| bot token 泄露风险 | 高 | token 已写入安全位置，但需注意不进任何对话框 |
