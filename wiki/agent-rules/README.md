---
title: agent-rules 领域知识总览
domain: agent-rules
type: concept
keywords: [agent-rules, 总览, 索引, workflow, 五步链路, 项目模板, skill, python, llm, rtk, frontend]
tags: [agent-rules, index, overview]
source: 三层索引第 2 层 · 领域分总览（wiki-ingest-guide §二·五）
sources: [conversation-2026-05-28]
created: 2026-05-28
updated: 2026-05-28
last_updated: 2026-05-28
---

# agent-rules 领域知识

> 本领域沉淀：三 Agent（Claude Code / Hermes / Antigravity / Gemini CLI）的工作流、代码规范、本体系自身的规则与项目模板。
> 由 promote-lessons Workflow 自动维护；新页面写完后在此登记一行。

---

## 工作流 · 项目模板（体系骨架）

- [[wiki-ingest-guide]] —— Wiki 读写操作宪法：何时写 / 写哪 / 怎么写 / 怎么读 / 怎么体检；三层索引规范、frontmatter 方案 Z
- [[five-step-pipeline]] —— 五步链路（信息检索优先级）+ 五阶段 workflow（任务生命周期 Explore→Plan→Execute→Verify→Learn）完整 SOP，含 TDD 强制规则与 PLAN 硬门
- [[project-template]] —— 新项目 / 新 Telegram channel 标准目录结构（src/tasks/tests/docs/scratch 等）+ 初始化步骤
- [[AGENTS-template]] —— `AGENTS.md` 项目入口模板（三 Agent 通用，CLAUDE.md 走符号链接）
- [[skill-registry]] —— 三 Agent skill 安装清单 + 统一管理三类（A 必须三处统一 / B 系统级共享 / C 单 Agent 专用）

## 代码与运行规范

- [[python-coding]] —— Python 代码规范：PEP 8、文件头注释、docstring、模块化原则、Test-First / TDD 执行顺序
- [[llm-orchestration]] —— LLM 调度准则：禁止硬编码模型 ID、动态发现、级联回退（主→同平台备→跨平台兜底）、串行不并行
- [[frontend-rendering]] —— 前端富文本渲染管道：禁裸露 Markdown、必经 marked.js 解析、剪贴板 `Clipboard API (text/html) + Blob` 加纯文本降级
- [[rtk-usage]] —— RTK 终端 token 优化代理（v0.40.0）完整命令表 + 三 Agent 用法差异（Claude Code 有 hook 透明，Hermes/Antigravity 需主动用）

## 项目案例（蒸馏经验沉淀）

- [[finance-hero-distillation]] —— Hermes profile 多人格架构 + 投资大师议会模式 + 11 位大师名册（2026-05-28）
- [[google-finance-research-integration]] —— Google Finance Beta「研究 AI」二次验证集成；Playwright + Chrome profile + 7 大网页自动化踩坑（2026-05-29）

---

## 相关领域

- `wiki/engineering/` —— 工程实践、bug 修复、架构、部署
- `wiki/llm/` —— LLM 具体踩坑（fallback 设计模式见 `wiki/design-patterns/cascade-fallback`）
- `wiki/design-patterns/` —— 可复用架构模式（级联回退、议会综合等）

## 顶层入口

回到 [[index]] 顶层总览。
