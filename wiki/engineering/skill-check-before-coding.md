---
title: 新功能开发前检查现有 Skill
domain: engineering
keywords: [skill, code-reuse, find-skill-first, 复用]
source_lesson: L-2026-05-04-005
created: 2026-05-04
---

# 新功能开发前检查现有 Skill

## 核心规则
开发任何新功能前，必须先搜索现有 Skill 和开源库，确认无现成方案才手写。

## 错误行为
直接开始写代码，没有检查是否已有可复用的 Skill。

## 正确做法
1. `hermes skills search <关键词>`
2. 搜索 PyPI / GitHub
3. 确认无现成方案后才手写

## 适用场景
- 所有新功能开发
- 遇到新的技术需求时
