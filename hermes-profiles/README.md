# Hermes Profile 议会模式人格蒸馏

> 这个目录记录了我们将 Hermes Agent 的 profile 机制与"议会模式人格蒸馏"结合的完整实践——从架构设计、人格蒸馏流程，到两个已上线的实例（Finance Hero、General Hero）。

---

## 这是什么

**一句话**：让一个 AI 装多颗"镜片"（多位大师的人格/思维框架），为同一个问题从不同角度回答，最后收敛成一个有立场的综合判断。

**痛点解决**：
- 单一 AI prompt 无法同时做到"懂价值投资"+"懂量化"+"懂周期"
- 用 prompt 切人格，仍然在同一个 memory/skill 池里，互相污染
- 现成的 AI 人格 skill 都是"独占模式"——激活后变成一个人，不能同台辩论

**答案**：
- **Hermes Profile 隔离机制** → 每个场景一个独立 bot
- **议会模式+声部架构** → 多位大师同台+主持人综合裁决
- **蓝图↔profile SSOT同步** → 改代码 → 一键部署

---

## 目录结构

```
hermes-profiles/
├── README.md                       ← 本文件
├── ARCHITECTURE.md                 ← Hermes profile/SOUL 匹配机制
├── MECHANISM-DESIGN.md             ← 议会模式对话机制与人格设计
├── DISTILLATION-PROCESS.md         ← 人格蒸馏流程（从资料到 skill）
├── PROJECT-PROGRESS.md             ← 项目进度与架构决策记录
├── COPY-GUIDE.md                   ← 给其他 Hermes 的复刻指南
│
├── finance-hero/                   ← Finance Hero 完整蓝图（11 位投资大师）
│   ├── SOUL.md
│   ├── README.md
│   ├── deploy.md
│   ├── sync.sh
│   ├── skills/ (11 大师)
│   ├── references/ (synthesis/depth-modes/moomoo-setup)
│   └── tools/
│
├── general-hero/                   ← General Hero (10 位伟人，由另一 profile 上传)
│   └── README.md
│
└── handbook/                       ← 蒸馏方法论（可复用）
    ├── DISTILLATION-HANDBOOK.md
    ├── QUICK-START.md
    └── templates/
```

---

## 两个实例一览

### Finance Hero（金融大师）
- **定位**：投资决策辅助
- **大师**：11 位（巴菲特、格雷厄姆、彼得·林奇、段永平、利弗莫尔、索罗斯、西蒙斯、德曼、塔勒布、芒格、霍华德·马克斯）
- **回复形状**：主持人开场 → 2–4 位大师声部 → 综合裁决（四问）→ 反例自检 → 免責
- **特殊机制**：行情数据接入、Google Finance 二次验证
- **快答档** ≤ 500 字

### General Hero（人生大师）
- **定位**：人生/通识/困境答疑
- **大师**：10 位（毛泽东、费曼、芒格、塔勒布、库恩、老子、福柯、波特、阿克洛夫、乔布斯）
- **回复形状**：同 finance + 四件套脚手架（费曼翻译/证伪自检/横纵/演化同类）
- **快答档** ≤ 700 字
- *蓝图由另一 Hermes profile 管理*

---

## 快速开始

```bash
# 1. 随便挑一个实例看看
cat finance-hero/SOUL.md

# 2. 想自己建个议会？看
cat COPY-GUIDE.md

# 3. 想懂底层逻辑？看
cat ARCHITECTURE.md

# 4. 想蒸馏新大师？看
cat DISTILLATION-PROCESS.md

# 5. 想部署 Finance Hero？看
cat finance-hero/deploy.md
```

---

## 上游规范

本目录服从 `../antigravity/general-global-rule.md`：
- §2.10 显式失败优先于编造
- 研究先行原则
- 认知纪律

---

## 维护

本目录由两个 Hermes profile 分别维护：
- **Finance Hero** — 当前 profile（`finance` profile）
- **General Hero** — 另一 profile（`general` profile）

冲突解决：两方各自管理自己目录下的文件。顶层文档（如本 README、ARCHITECTURE.md）由最近更新的 profile 负责同步最新状态。
