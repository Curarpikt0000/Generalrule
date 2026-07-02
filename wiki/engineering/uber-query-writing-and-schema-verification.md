---
title: Uber query 编写 & 表 schema 查证（jpgr-query-writer skill + 踩坑合集）
domain: engineering
type: synthesis
keywords: [query, sql, presto, queryrunner, datasource, show columns, schema, 表名过时, usearch, databook, jpgr, grocery-retail, cerberus, querybuilder, clac, notion-catalog]
tags: [uber, query, presto, queryrunner, schema, jpgr, mcp]
source: hermes-jpgr-query-writer-skill + query对账系列任务
sources: [hermes-jpgr-query-writer-20260702, project-query-explanation, gr-query-tables]
created: 2026-07-02
updated: 2026-07-02
last_updated: 2026-07-02
---

> **本页含 Uber 内部取数链（queryrunner-mcp / aifx / Presto / 内部表名），属 ub-branch，不进 main。**

# Uber query 编写 & 表 schema 查证

写 Uber 内部分析 SQL（尤其日本 GR / Grocery & Retail）时，反复踩的坑与验证过的正确通道的合集。**Uber agent 写 query 必须先调用 skill `jpgr-query-writer`**（它是这套知识的可执行封装：决策树、数据源优先级、WHERE 护栏、~20 张核心表、~130 条 vetted query、schema 查证阶梯）——本页是背后的原理与踩坑，skill 是操作入口。

## 核心规则 / Key Insights

- **写 query 前先走 skill 的数据源优先级**：SSOT 表 → Query Repo（vetted saved query）→ **团队 Notion Table/Query DB 兜底找已验证的表** → 其他库（last-resort，须警告）。别一上来就手写、也别乱抓不常用表。
- **queryrunner-mcp 的正确路由参数是 `datasource:"presto"`**，不是 `data_center`/`cluster_name`。用后者路由到 `secure` 集群，很多 GR 表的 `SHOW COLUMNS` 会直接 `completed_failure`（不是排队、不是权限，是集群路由错）。同一批表：`datasource:presto` 成功，`cluster_name:secure` 失败——这是最隐蔽的坑。
- **`SHOW COLUMNS` 失败 ≠ 表不存在**，先怀疑**表名过时/改名**。用 `usearch-backend usearchbackend_searchv2`（`{"query":"<表名stub> <schema>","page_size":4}`）搜内部 SQL，结果里的真实表名即现役名。真实案例：`kirby_external_data.plan_fx_rates_japan_latest`（skill 旧名）已废，现役是 **`kirby_external_data.plan_fx_rates_2026_v2`**。
- **Databook 通道绕开 Presto 拥堵**：local MCP `query-mcp-server`（用 Databook 拿任意表 schema 再构造 Presto query）和 `query_copilot-mcp-server`（NL→SQL，对 live schema 校验列）从 Databook 取 schema，不受集群拥堵影响。它们是 **local/community MCP**（aifx 网关默认不代理，`mcp call` 会 404），需本地 `aifx mcp add` 配置后用——作为 queryrunner 拥堵或表受限时的备选。
- **`get_execution_results` 破 50 行用 `fetch_rows`**（无硬上限），别用 limit/offset/page_size（被忽略）。详见 [[queryrunner-mcp-fetch-rows-and-queue]]。
- **PII/受限表**（如 `secure_whober.employees`）`SHOW COLUMNS` 可能因 CLAC 加密列 `completed_failure`——预期行为，录入/文档时不展开加密列。
- **QueryBuilder `/r/<id>` 报表反查真 SQL**：Hermes 环境可抽（skill `uber-querybuilder-sql-extract`，cerberus proxy + querybuilder utoken）。**合规铁律：cerberus 仅本地调试，手动起、用完立即 kill，绝禁 cron/常驻/自动化。**

## 正确做法（查证一张表的列，验证过的阶梯）

1. `queryrunner-mcp execute_query` 跑 `SHOW COLUMNS FROM <schema.table>`，参数 `{"query":"...","datasource":"presto"}`；异步 submit → poll `check_execution_status`（`execution_uuids:[...]` 复数）到 `completed_success` → `get_execution_results`（`fetch_rows`）。禁 `SELECT *`。
2. 若 `completed_failure` → usearch 查真实表名 → 用真名重跑第 1 步。
3. 仍不行 → Databook local MCP（query-mcp-server / query_copilot）拿 schema。
4. PII 表 CLAC 失败属正常，按表存在但列不展开处理。

## Notion 编目时（Table/Query DB）

- Table DB 有分字段：`Where (标准过滤)` / `Where Special (场景特定)` / `Comments (注意事项)` / `重要字段说明` / `Rating`（emoji `⭐️⭐️⭐️⭐️⭐️`）。每张表 page 内挂一个「列索引」child DB（列名/类型/Extra/定义）。WHERE 拆两字段、注意事项进 Comments，别一股脑塞 Comments。
- Query DB 评分字段是 `评分(使用度)`，用星号 `★★★★★`（与 Table DB 的 emoji 不同，别混）。
- **只填空不覆盖**：已有人工优质内容的字段（如 dim_storefront 的 Where 已含脏数据清洗谓词）绝不覆盖；幂等按表名/Link 查重。详见 [[notion-dedup-fail-loud]]。

## 来源
hermes-jpgr-query-writer-20260702（skill 落地 + 18 核心表 schema 查证 + 134 query 对账全 5 星）；GR-Query-Tables / Project-Query-explanation 系列对账任务。

## 相关页面
- [[queryrunner-mcp-fetch-rows-and-queue]] —— fetch_rows 破 50 行 + 排队拥堵 watchdog
- [[presto-quark-heavy-join-query]] —— Presto 重 join 查询
- [[notion-dedup-fail-loud]] —— Notion 幂等查重
- [[skill-register]] —— skill 总清单（jpgr-query-writer 登记）
