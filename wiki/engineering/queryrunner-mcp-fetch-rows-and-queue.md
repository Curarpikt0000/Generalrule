---
title: queryrunner-MCP 取数突破 50 行（fetch_rows）+ 后端排队拥堵应对
domain: engineering
type: lesson
keywords: [queryrunner, mcp, fetch_rows, presto, 50行, row-limit, 全量取数, 排队, started_waiting_to_execute, exeggutor, aifx, uber]
tags: [uber, queryrunner, mcp, data-extraction, presto]
source: hermes-task6-ads-data-extraction-20260629
sources: [hermes-task6-ads-data-extraction-20260629, chao-correction-fetch_rows]
created: 2026-06-29
updated: 2026-06-29
last_updated: 2026-06-29
applies_to: hermes
---

> **本页含 Uber 内部取数链（queryrunner-mcp / aifx / Presto），属 ub-branch。**

# queryrunner-MCP 取数突破 50 行 + 后端排队应对

## 背景

通过 `aifx mcp call queryrunner-mcp`（Presto，异步 submit→poll→fetch）取 Uber 内部数据时，长期误以为 `get_execution_results` 有「50 行硬上限」——以为大结果集必须绕 `queryrunner_client` + cerberus exeggutor（后端极不稳定）才能拿全量。**这是错的（Chao 2026-06 纠正）。**

## 核心：`fetch_rows` 参数突破 50 行

`get_execution_results` 默认只回 ~50 行，但请求参数 **`fetch_rows`** 可调高，**无硬上限，传多少拿多少**：

```bash
aifx mcp call queryrunner-mcp get_execution_results \
  --args '{"execution_uuids":["<uuid>"],"fetch_rows":20000}'
```

- 之前误试的 `limit` / `offset` / `page_size` / `max_rows` / `row_limit` **确实被忽略**——正确的参数名是 **`fetch_rows`**。
- `COUNT(*)` 一直返回真实总数；设了 `fetch_rows` 后行数即与之对齐。
- **结论：常规全量提取（merchant×week、customer-feature、store-level 等）直接走 MCP 即可，不必为了破行数限制而绕 `queryrunner_client` + exeggutor（flaky 后端）。** 只有真正需要 Python client 流式/parquet 超大规模时才用 client。

## 第二条逃生通道：浏览器 scratchpad 下载 CSV

在 querybuilder web scratchpad 里点 **"Download as CSV"**，并**取消勾选 Limit 复选框** → 浏览器直接下载无限制的全量结果集。适合一次性人工导出。

## 后端排队拥堵：`started_waiting_to_execute` 不是慢，是卡

独立于行数问题：即使最轻量的 `LIMIT 5` / dim 表 `GROUP BY` 探查，有时也会在 `check_execution_status` 长时间停在 **`started_waiting_to_execute`**（多分钟不动）。这是 **queryrunner 后端队列拥堵**（环境侧波动），不是你的并发槽问题——把自己所有查询 `cancel_execution` 清空、再重提一个最小查询，仍会卡。

### 应对纪律
1. **不要干等轮询**。
2. 起一个**静默重试 watchdog**（terminal background + notify_on_complete）：周期性重提探查集，成功落地 CSV/JSON，失败保持安静；后端一恢复就自动补全并通知。与 exeggutor watchdog 同模式。
3. **同时把工作 pivot 到不依赖后端的部分**（写 SQL、写文档、写 Sheet 框架）。后端拥堵时把确定性工作做掉，待取数让 watchdog 自动兜。
4. watchdog 里区分确定性失败（列 CLAC 加密：`encrypt`/`does not have`/`CLAC` → 不再重试）vs 排队/duplicate 类（下一轮重提）。

## 相关
- skill `uber-gr-finance-analysis`（已同步纠正旧的「50 行硬上限」段）
- 后端不稳定根因与 cerberus 链：见 `agent-rules/hermes-genai-api-integration.md`
