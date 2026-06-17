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

> 本领域沉淀：所有 agent（Claude Code / Hermes / Antigravity / Codex / Cursor 等）的工作流、代码规范、本体系自身的规则与项目模板。
> 新页面写完后在此登记一行（手动维护）。

---

## 工作流 · 项目模板（体系骨架）

- [[wiki-ingest-guide]] —— Wiki 读写操作宪法：何时写 / 写哪 / 怎么写 / 怎么读 / 怎么体检；三层索引规范、frontmatter 方案 Z
- [[five-step-pipeline]] —— 五步链路（信息检索优先级）+ 五阶段 workflow（任务生命周期 Explore→Plan→Execute→Verify→Learn）完整 SOP，含 TDD 强制规则与 PLAN 硬门
- [[project-template]] —— 新项目 / 新 Telegram channel 标准目录结构（src/tasks/tests/docs/scratch 等）+ 初始化步骤
- [[AGENTS-template]] —— `AGENTS.md` 项目入口模板（多 agent 通用，CLAUDE.md 走符号链接）
- [[skill-register]] —— skill/MCP 总清单（对账 A/B/C 三类 + 各环境全量明细 + Self-Skill 区）
- [[agent-config-matrix]] —— 各 agent 配置自述矩阵（入口/人格/记忆/workflow/技能/与 repo 关系）；配新实例照抄
- [[soul-authoring-guide]] —— SOUL 写作指南 + SOUL.md 模板（仅 Hermes；其余 agent 无 SOUL 层）

## Claude Code 私有机制（Hermes / Antigravity 无）

- [[auto-memory-boundary]] —— Auto Memory 边界：哪些进私有笔记、哪些必须进共享 Wiki
- [[auto-memory-setup]] —— Auto Memory 配置：三层开关、存储与 MEMORY.md 索引、frontmatter 字段、写入/召回/更新/删除触发

## 代码与运行规范

- [[python-coding]] —— Python 代码规范：PEP 8、文件头注释、docstring、模块化原则、Test-First / TDD 执行顺序
- [[llm-orchestration]] —— LLM 调度准则：禁止硬编码模型 ID、动态发现、级联回退（主→同平台备→跨平台兜底）、串行不并行
- [[frontend-rendering]] —— 前端富文本渲染管道：禁裸露 Markdown、必经 marked.js 解析、剪贴板 `Clipboard API (text/html) + Blob` 加纯文本降级
- [[rtk-usage]] —— RTK 终端 token 优化代理（v0.40.0）完整命令表 + 各 agent 用法差异（Claude Code 有 hook 透明，Hermes/Antigravity 需主动用）

## 项目案例（蒸馏经验沉淀）

- [[finance-hero-distillation]] —— Hermes profile 多人格架构 + 投资大师议会模式 + 11 位大师名册（2026-05-28）
- [[google-finance-research-integration]] —— Google Finance Beta「研究 AI」二次验证集成；Playwright + Chrome profile + 7 大网页自动化踩坑（2026-05-29）
- [[moomoo-opend-integration]] —— moomoo OpenD + futu-api 接入；同 Mac 多 Hermes profile 共用一个 OpenD 实例；凭证安全纪律（2026-05-31）
- [[hermes-profile-filesystem-discipline]] —— 任何 Hermes profile 写文件的纪律：~/hermesagent/<profile>/ 专属工作区 + 禁止染指 Documents/Desktop 等用户文件夹（2026-05-31）
- [[hermes-genai-api-integration]] —— Hermes 接 Uber 内部 GenAI API（Claude Opus 4 / GPT-5.5）；Cerberus 隧道 + proxy v2（429 重试）+ dinit/crontab 24/7 持久化；SSH_AUTH_SOCK 踩坑；隧道 watchdog（系统 cron · 认证失败 Telegram 提醒）+ idle 掉线/端口漂移 `502 [Errno 99]` 踩坑（2026-06-12，更新 2026-06-17）
- [[hermes-gateway-watchdog]] —— 【仅 Hermes】Gateway 24/7 cron watchdog 自动拉起；核心踩坑：必须同时匹配 run/restart 两种 cmdline，否则 false-DOWN 死循环（2026-06-15）

---

## 相关领域

- `wiki/engineering/` —— 工程实践、bug 修复、架构、部署
- `wiki/llm/` —— LLM 具体踩坑（fallback 设计模式见 `wiki/design-patterns/cascade-fallback`）
- `wiki/design-patterns/` —— 可复用架构模式（级联回退、议会综合等）

## 顶层入口

回到 [[index]] 顶层总览。
