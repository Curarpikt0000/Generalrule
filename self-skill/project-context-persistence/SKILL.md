---
name: project-context-persistence
description: Hermes 项目上下文持久化——每日自动采集、蒸馏、更新 docs/context-log.md + AGENTS.md 项目简介
version: 1.0.0
author: Hermes Agent system
platforms: [macos, linux]
category: devops
metadata:
  tags: [context, persistence, cron, state-db, context-log, project-context]
---

# project-context-persistence

## 概述

每个 Hermes 项目必须有一个 `docs/context-log.md` + 每天 02:00 的 cron，用于跨会话上下文持久化。

本 skill 包含：
- 采集脚本 → `scripts/collect_topic_conversation.py`
- 每日 cron prompt 模式
- 多 project 错峰调度配方

## 依赖

- Hermes cron 调度器（`cronjob` 工具）
- `~/.hermes/state.db`（Hermes 会话数据库，SQLite）
- 项目根目录含 `docs/context-log.md`（不存在则自动创建）

## 架构说明

Hermes state.db 对 telegram 会话只记 `source='telegram'`，**不持久化 topic/thread_id**，故无法 100% 精确隔离单个 topic。本方案用「时间窗 + telegram 来源 + 项目关键词过滤 + 排除 delegation 子父」做近似。

**诚实限制**：单 topic 活跃时效果好；多 topic 同时高频活跃时，唯一真隔离是给每个项目开独立 Hermes profile（较重，按需）。

## 首次搭建操作（单项目）

### 步骤 1：确认采集脚本
```bash
ls -la ~/.hermes/scripts/collect_topic_conversation.py
```
不存在则从本 skill 的 `scripts/` 复制。

### 步骤 2：建 docs/context-log.md
在项目根目录创建（可参考下方格式）。

### 步骤 3：确认 AGENTS.md 含指向
在 `AGENTS.md` 末行或「指针」节加：
```markdown
- **上下文日志 → `docs/context-log.md`**（每日 02:00 cron 自动更新）
```

### 步骤 4：设 cron job
用以下 prompt 模板创建 cronjob，注意错开多项目时间（间隔 3-5 分钟）。

### 步骤 5：多项目错峰调度

已有项目采用 23:00 时段，新方案改为 02:00 时段。错峰示例：
| 项目 | 时间 |
|---|---|
| Anything-to-Notion | 02:00 |
| Youtube video | 02:15 |
| COMEX 日报 | 02:30 |
| US Debt | 02:45 |
| Distill | 03:00 |
| KOL 看板 | 03:15 |

## cron prompt 模板

```markdown
# <项目名> 项目上下文压缩 — 每天运行

你的职责是读取当前 Hermes 会话数据库中与 **<项目名>** 项目相关的近期对话，提取关键上下文并压缩到项目快照文件中。

## 步骤

### 1. 搜索近期相关对话
用 session_search 搜索以下关键词：
- "<项目搜索关键词1>" OR "<项目搜索关键词2>"

获取最近 3 天内最多 5 个相关会话。

### 2. 提取关键上下文
从会话中提取：
- **任何纠正**（用户指出错误、否定方案、要求改方向）——这是最重要的
- **项目事实更新**（DB ID、API 端点、核心表、关键配置）
- **决策记录**（用户明确说"按这个方案做"的）
- **进展摘要**（已完成什么，剩什么）
- **待办事项**（未完成的任务）

### 3. 蒸馏更新 docs/context-log.md
用 terminal 读取/写入项目根目录的 `docs/context-log.md`：
1. 先读当前文件确保不重复
2. 添加今天的日期小节（如还不存在）
3. 只写入新的、尚未记录的信息——不要复读已记录过的东西
4. 保持结构：决策 → 事实配置 → 进展 → 待办

### 4. 刷新 AGENTS.md 项目简介
读取 `AGENTS.md`，找到「项目简介」或项目描述行，确保它反映了最新状态。

## 输出规则
- 有新的有效信息 → 报告"已更新 context-log（<日期>），新增 N 条记录"
- 没有新内容 → 输出 `[SILENT]`（抑制消息下发）
- 不要复读老内容
```

## 踩坑记录

| 问题 | 解决 |
|---|---|
| context-log 每天重复写同一段 | 写前先读，用日期节去重 |
| 采集脚本只读 SQLite | 不写 state.db，只读。无副作用 |
| Telegram topic 不精确 | 见上方「架构说明」，用关键词 + 排除 delegation 近似 |
