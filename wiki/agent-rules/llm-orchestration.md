---
title: LLM 调度与模型 Fallback 准则
domain: agent-rules
keywords: [llm, 模型调度, fallback, 级联回退, 配额, 429, model-discovery, 跨平台兜底]
source: 原 general-global-rule.md §3（2026-05-24 迁移至 Wiki）
created: 2026-05-24
last_updated: 2026-05-24
---

# LLM 调度与模型 Fallback 准则

> 本页是写「调用 LLM 的代码」时的规范。任何涉及模型调用、fallback、配额处理的开发都应先读本页。
> 不涉及 LLM 调用的任务可跳过。

---

## 核心原则

本项目核心是 LLM 应用，所有 LLM 调用必须遵守以下四条。

## 1. 禁止硬编码模型 ID

- 禁止在代码中写死 `gemini-1.5-pro`、`claude-opus-4` 等具体模型代号
- 所有模型 ID 必须从 `config.py` 或动态发现结果中读取

*因为模型代号会随服务商更新而废弃，硬编码会导致代码突然失效。*

## 2. 动态发现（Model Discovery）

- 应用启动或首次调用前，必须通过 `list_models` 接口获取当前 API Key 真实可用的最新 Pro 级 and Flash 级模型 ID
- 发现结果缓存，避免每次调用都发请求

## 3. 级联回退（Cascading Fallback）

这是一个**通用模式，不绑定任何特定服务商**。下面的 Vertex / AI Studio 只是举例，实际可以是 OpenRouter、DeepSeek、Anthropic、Gemini 或任意组合——关键是分层 + 自动降级的**结构**，不是具体哪家。

- **第一优先级（主模型）**：动态发现的最顶级稳定版模型。
- **第二优先级（同平台降级）**：主模型报错（429 配额 / 500 异常）时，自动捕获并尝试同平台的次级模型（如 Pro 降 Flash）。
- **跨平台兜底**：当前平台整体不可用时，平滑切换到另一家服务商。

> 举例（仅示意一种可能配置）：Vertex Pro → Vertex Flash → AI Studio。
> 你的项目可按实际接入的服务商替换，比如：OpenRouter 某模型 → DeepSeek → Anthropic。
> 核心是「主 → 同平台备 → 跨平台兜底」这个三层结构，而非具体服务商。

## 4. 容错回馈

- 所有候选链路都失败后才抛最终异常
- 异常信息必须包含"所有候选链路已尝试"的完整诊断路径

---

## 重要纪律：串行，不要并行抢占

LLM 长文本生成与图像生成等重资源任务**严禁并行抢占**，必须严格串行执行（例：生成文章 → 抽取视觉 Prompt → 渲染图片）。
遇到 429 配额报错，必须走上面第 3 条的级联熔断机制（Pro 降级至 Flash），**绝对禁止**脱离熔断机制的自我无限重试。

（来源：L-2026-04-24-001，原 general rule §4.7）

---

## 相关页面

- [[cascade-fallback]] —— 级联回退设计模式（design-patterns 领域）
- general-global-rule.md §2.5 显式暴露冲突、§2.10 显式失败
