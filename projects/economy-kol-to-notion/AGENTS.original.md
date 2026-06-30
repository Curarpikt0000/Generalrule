# Economy-KOL-to-Notion

> 本项目遵守全局规则：见 Generalrule 仓库 `antigravity/general-global-rule.md`（本机 clone：`~/uberhermes/Generalrule/`）。
> 通用规范与踩坑教训见 Generalrule 仓库 `wiki/`。
> 本文件只写本项目特有的内容。五阶段 workflow、认知纪律、安全铁律在全局规则里，这里不重复。

## 项目简介

（待补充）将 Economy 相关 KOL（关键意见领袖）信息采集 / 整理 → 写入 Notion DB。

服务 Uber Eats Japan GR（Grocery & Retail）运营团队。

## 你的使命

（待 Chao 补充具体需求后细化）

## 数据源 / 目标

### Notion DB
- URL:（待填）
- database_id:（待填）
- token 复用 `~/Projects/Project-Competitor-News/.env` 的 `NOTION_TOKEN`，Notion-Version `2022-06-28`
- GOTCHA：每个 Notion page/DB 必须在 Notion 里把该 integration 加为连接，否则 API 404

## 技术栈 / 工具

- Hermes Agent on Uber VM（无 Notion MCP、无通用 web-fetch MCP）。
- Notion 读写：REST API v1（无 MCP）。token 见上。
- 复用脚本放 `src/`，一次性脚本放 `scratch/`。

## 目录约定

- `src/` 源码（可复用库、读写逻辑）
- `scratch/` 临时脚本、调试输出、一次性产物（不进 git）
- `tasks/todo.md` 任务清单 ｜ `tasks/lessons.md` 踩坑
- `docs/` 文档 + `docs/context-log.md`（cron 每日上下文归档）
- 密钥只进 `.env`，绝不硬编码、绝不进 git

## 工作规则（本项目特有）

- **写后必读回验证**：Notion 重新 query 确认行/属性真落地，再向用户报告"完成"。API 的"OK"自报不算证据。
- **绝不编造**：查不到的信息标注 `(推断)` 并写依据，不假装查过。
- **时间一律东京时间**（JST, UTC+9）。
- IP 红线：Uber 专有数据只留本地 `~/Projects/`，绝不 push 个人 repo。

## 验收标准

（待补充）

## 项目 Wiki

本项目经验沉淀见 `tasks/lessons.md`，满 30 条或稳定后升级到全局 Wiki。

> 关联全局 skill：`notion`、`uber-aifx-mcp`、`monitoring-pipeline`（如做采集管道）。
