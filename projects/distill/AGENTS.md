# 蒸馏（Distill）— AGENTS.md

## 项目名
蒸馏（Distill）— Hermes Agent 能力蒸馏

## 核心描述
知识蒸馏项目——将 Hermes Agent 的能力、知识、大师人格和最佳实践蒸馏为可复用的技能和 profile 蓝图。

**目标**：通过"议会模式"（四人议会：女娲/大师人格/综合裁决/深度控制），把 Chao 在 Hermes Agent 上积累的架构经验、金融分析能力、通识决策方法论打包进 Hermes profile，让每个 profile 像一位领域专家一样工作。

**已实例化的项目**：

| 项目 | 路径 | 状态 |
|---|---|---|
| Finance Hero | `蒸馏Hermes/finance-hero/` | 11 位投资大师议会 + moomoo 接行情，跑通 |
| General Hero | `蒸馏Hermes/general-hero/` | 10 位伟人议会 + 四件套脚手架，跑通 |
| 蒸馏 Handbook | `蒸馏Hermes/handbook/` | 方法论 + 模板集，用于复刻新 profile |
| Wiki 导出 | `蒸馏Hermes/wiki-output/` | 从蒸馏项目写入真 Wiki 的条目 |

## 目录结构

```
~/hermesagent/Distill/
├── AGENTS.md                      ← 本文件（项目入口）
├── CLAUDE.md → .../CLAUDE.md      ← 符号链接，指向项目 CLAUDE.md
├── tasks/                         ← 当前任务状态
│   └── context-snapshot.md        ← 上下文快照（项目当前状态摘要）
│
└── 蒸馏Hermes/                    ← 所有蒸馏内容的根目录
    ├── finance-hero/              ← Finance Hero 蓝图（11 位投资大师议会）
    ├── general-hero/              ← General Hero 蓝图（10 位伟人议会）
    ├── handbook/                  ← 蒸馏方法论 + 模板集
    │   ├── DISTILLATION-HANDBOOK.md  ← 完整方法论（必读）
    │   ├── QUICK-START.md            ← 急用 checklist
    │   └── templates/                ← 可复制模板
    └── wiki-output/               ← 从蒸馏项目写入真 Wiki 的条目
```

## 🔑 重要指针

| 项目 | 路径 |
|---|---|
| **项目 AGENTS.md** | `~/hermesagent/Distill/AGENTS.md` |
| **上下文快照** | `~/hermesagent/Distill/tasks/context-snapshot.md` |
| 根全局规则 | `~/hermesagent/Hermes General Rule & Protocol/CLAUDE.md` |
| 蒸馏方法论 | `蒸馏Hermes/handbook/DISTILLATION-HANDBOOK.md` |
| 快速开始 | `蒸馏Hermes/handbook/QUICK-START.md` |
| Finance Hero | `蒸馏Hermes/finance-hero/SOUL.md` |
| General Hero | `蒸馏Hermes/general-hero/SOUL.md` |

## ⚠️ 核心规则

1. **Distill 是蓝图目录**——所有蒸馏产物（蓝图、模板、知识）存放在 `蒸馏Hermes/` 下，不与其他项目混淆
2. **复用优先**：复用现有 skill > GitHub 克隆 > 女娲生成 > 手蒸馏 > 凭空编写
3. **profile 隔离**：每个 Hermes profile 有独立的 SOUL.md + skills + config，蓝图只负责描述"如何构建"而非"运行时状态"
4. **议会模式铁律**：任何 profile 必须有冲突源（至少 2-3 对立场相反的大师/人格），否则无辩论价值
5. **去编造纪律**：每个大师的心智模型必须有可追溯的真实来源（著作章节、讲话原文），禁止凭空捏造"决策启发式"

## 📋 历史教训

| 日期 | 问题 | 教训 |
|---|---|---|
| 2026-05-28 | 原"单 Hermes + AGENTS.md 覆盖"方案被推翻 | Hermes 官方 profile 机制自带隔离，应直接用 profile 而非在 channel 内覆盖 |
| 2026-05-28 | finance-hero AGENTS.md 被 SOUL.md 取代 | AGENTS.md 仅用于顶层目录描述，profile 级别的交互细节由 SOUL.md 承载 |

## 📅 下一步

见 `tasks/context-snapshot.md` 获取当前项目状态和待办事项。
