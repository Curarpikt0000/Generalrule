# Distill — Hermes Agent 能力蒸馏知识包

## 项目简介

**Distill（蒸馏）** 是一个知识蒸馏项目，将 Hermes Agent 的能力、知识、大师人格和最佳实践蒸馏为可复用的 Hermes profile 蓝图。每个 profile 像一位领域专家一样工作，无需真实 API token 即可离线部署和运行。

## 核心方法

采用 **议会模式（四人议会）** 架构：

| 角色 | 职责 |
|------|------|
| 🏛️ 女娲 | 统筹、总结、蓝图规划 |
| 🧠 大师人格 | 领域专家，提供多元视角 |
| ⚖️ 综合裁决 | 整合分歧，输出共识 |
| 🎛️ 深度控制 | 把控输出质量与一致性 |

议会模式的铁律：每个 profile 必须有冲突源（至少 2-3 对立场相反的大师/人格），否则无辩论价值。

## 已产出的 Profile

### Finance Hero（11 位投资大师）
- 路径：`蒸馏Hermes/finance-hero/`
- 11 位投资大师议会 + moomoo 接行情，已跑通

### General Hero（10 位伟人）
- 路径：`蒸馏Hermes/general-hero/`
- 10 位伟人议会 + 四件套脚手架，已跑通

## 目录结构

```
/tmp/distill-docker/
├── AGENTS.md                  ← 项目入口文档
├── README.md                  ← 本文件
├── context-log.md             ← 上下文日志
├── tasks/
│   ├── lessons.md             ← 历史教训
│   └── todo.md                ← 待办事项
└── cron/
    └── context-compression.json  ← 上下文压缩调度配置
```

## 最终部署位置

此知识包为 Docker 封装版本（不含真实 token），完整蓝图的最终部署位置为：

- **GitHub:** `github.com/Generalrule/hermes-profiles/`
- **本地开发:** `~/hermesagent/Distill/`

## 重要纪律

- 此包不包含任何真实 API token 或密钥
- 所有大师心智模型必须有可追溯的真实来源（著作章节、讲话原文）
- 每个 profile 隔离运行，蓝图只描述"如何构建"，不包含运行时状态
