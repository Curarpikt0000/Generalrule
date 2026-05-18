---
title: 模型选择规则
domain: llm
keywords: [deepseek, v4-pro, v4-flash, 模型切换, 任务分级]
source: L-2026-05-18-003
created: 2026-05-18
last_updated: 2026-05-18
---

# 模型选择规则

AI Agent 根据任务复杂度自动选择 DeepSeek 模型，无需手动切换。

## 可用模型

| 模型 ID | 类型 | 速度 | 质量 |
|---------|------|------|------|
| `deepseek-v4-flash` | Flash | 快 | 日常可用 |
| `deepseek-v4-pro` | Pro | 较慢 | 更高质量 |

## 触发使用 Pro 的场景

以下情况强制自动切换到 `deepseek-v4-pro`：

1. **复杂 debug / 报错分析** — 涉及多步骤根因排查
2. **代码审查、架构设计** — 需要深度推理和权衡
3. **涉及 5+ 文件的大规模修改** — 上下文复杂度高
4. **用户明确要求高质量输出** — 用户说"用pro"或类似表述

## 切换方式

通过 `/model deepseek-v4-pro` 或 `/model deepseek-v4-flash` 临时切换，无需重启会话。

## 来源

- general-global-rule.md §11 模型选择规则
- L-2026-05-18-003
