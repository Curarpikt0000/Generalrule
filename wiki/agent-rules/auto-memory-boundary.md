---
title: Auto Memory 边界规则（仅 Claude Code）
domain: agent-rules
type: rule
keywords: [auto-memory, claude-code, 边界, 共享wiki, 私有笔记, ingest]
tags: [auto-memory, claude-code, boundary, wiki]
source: Claude Code 使用纪律
sources: [conversation-2026-06]
created: 2026-06-07
updated: 2026-06-13
last_updated: 2026-06-13
---

# Auto Memory 边界规则（仅 Claude Code）

> Auto Memory 是 Claude Code 私有的自动笔记，本体系其他 agent（Hermes / Antigravity / Codex / Cursor…）没有它。
> 因此 Auto Memory 只能记"Claude Code 本地琐事"，绝不能记"该被所有 agent 共享的知识"——共享的走 Wiki。

## 可以记（Claude Code 私有）
- 本机操作偏好、Claude Code 专属使用习惯
- 当前项目的临时状态（进行到哪、下一步）
- 纯属本地、不值得全局共享的细节

## 禁止记（这些走共享 Wiki，不进 Auto Memory）
- 值得所有 agent 共享的纠正、规则、方法论 → 走 Wiki ingest（优先 llm-wiki skill）写入共享 Wiki
  （本 repo `wiki/`；各机按本地 clone 路径定位，不写死绝对路径）
- general rule 已有的内容（避免重复）
- 代码结构、文件路径（直接读项目）
- git 历史（git log 更准）
- 调试步骤（修复已在代码里）

## 判断标准（每次要记前自问）
被用户纠正或学到新知识时，先问：**这值得别的 agent 也知道吗？**
- 值得 → 走 Wiki ingest（general rule §6 / [[wiki-ingest-guide]]）
- 仅 Claude Code 本地有用 → 才记进 Auto Memory

## 相关
- [[wiki-ingest-guide]] —— Wiki 写作规范（共享知识的去处）
- general-global-rule.md §6（Lesson 系统）
