---
name: jpgr-query-writer
description: >-
  Write Presto/Hive SQL for the Japan Retail / JP Grocery Retail (JPGR) team,
  sourcing from the team's SSOT tables and vetted Query Repo first. Use when
  someone asks to "write a JPGR query", "Japan Retail SQL", "JP grocery query",
  or wants grocery-retail metrics — GB, food sales, quantity sold, ABS/ASP,
  found/fulfillment/replacement rate, out-of-stock (OOS/OOI) loss, cancellations
  and C/R, defects, UPT, catalog/SKU/photo/GTIN coverage, acceptance rate,
  online rate, retention/LTV/Uber One, basket analysis, impressions, search,
  promo & ads, courier economics (MPP/CPP/EPUH), market sizing (SAM/MAU),
  price inflation, or ward/prefecture geo breakdowns. Also use when the user
  gives a merchant/store/parent-chain name or UUID (or a Japanese term) and
  wants sales, catalog, financial, or operational data for it. Produces
  validated SQL plus the closest matching existing QueryBuilder link.
metadata:
  hermes:
    tags: [uber-gr, jpgr, japan-retail, sql, presto, querybuilder, ssot, data-query, mandatory]
    related_skills: [uber-querybuilder-sql-extract, query-corpus-to-notion, uber-gr-finance-analysis, uber-internal-mcp]
argument-hint: '<natural-language data question, optionally with merchant/store name or UUID>'
---

> **Hermes 环境适配说明（本节由 Chao 团队适配，非原版）**
> 本 skill 原为 Claude-Code / omni-mcp 格式，已改造为 Hermes on Uber VM 原生。关键差异：
> - MCP 调用走 aifx 网关包装器：`~/.hermes/scripts/ax.sh mcp call <server> <tool> --args '{...}'`（"omni-mcp" = aifx MCP 网关本身，不是独立服务）。
> - 查表结构/列：用 `queryrunner-mcp execute_query`（异步：submit → `check_execution_status` 用 `execution_uuids:[...]` → `get_execution_results`）跑 `SHOW COLUMNS FROM <schema.table>`（禁 `SELECT *`，加密列会 CLAC PERMISSION_DENIED）。
> - 抽 querybuilder `/r/<id>` 的真实 SQL：本环境**可以**，用 skill `uber-querybuilder-sql-extract`（cerberus proxy，用完即 kill——合规铁律，绝禁 cron/常驻）。原版说"SQL 不可取"在 Hermes 不成立。
> - 内部知识检索：`usearch-backend usearchbackend_searchv2`（**必带 page_size**）/ `usearchbackend_getdocuments`。
> - 本 skill 的 table + sample query 已录入团队 Notion（Table DB `37f47eb5fd3c80d998ebfc245119def3` / Query DB `38347eb5-fd3c-80f1-8005-fb50b3b07af8`，全 5 星），可直接查。

# JPGR Query Writer

Write correct, runnable Presto SQL for the **Japan Retail / JP Grocery Retail
(JPGR)** team. Reuse the team's SSOT tables and vetted queries first; hand-write SQL
only when nothing covers the ask. Output SQL — do not run it unless the user asks
(then hand off to `execute-query`).

## Quick decision tree

Route the request before writing anything:

- **Financial / accounting report** (fees, NETR, VC, anything needing accounting alignment)?
  → **Do NOT use the SSOT trackers** (they aggregate by operational day). Use an
  `accounting_date`-aggregated finance query (`query_repo.md` → finance/topline).
- **Ward / prefecture / region breakdown?** → use the **ward-mapping CTE** in `domain_patterns.md`.
- **Whole JP Retail, no merchant/store specified?** → apply the **default store filter** in `domain_patterns.md`.
- **Hex / coverage / geofence?** → `kirby_external_data.jp_hex_geo_v4`.
- **Otherwise** → follow the **data-source priority**: SSOT tables → Query Repo → (last resort) other DBs with a warning.

Any currency conversion → FX rate from `kirby_external_data.plan_fx_rates_japan_latest`, never a table-embedded rate.

## Reference map — open what you need

| Need | Open |
|---|---|
| Data-source priority, store filter, ward CTE, metric formulas, FX rule, cancellation/defect taxonomy, Japanese glossary | `references/domain_patterns.md` |
| Short index of ~150 saved queries by topic (title + QueryBuilder link) | `references/query_repo.md` |
| Per-query enriched lookup (metric, grain, filters, calc, likely tables) — reuse a report without opening its link | `references/query_reference.md` |
| Which MCP backends to call and how | `references/server_details.md` |

## Workflow

1. **Understand the ask.** Identify metric(s), grain (store / merchant / parent-chain / item / GTIN / UPT / ward / country), time range + granularity, and any entity filter (name or UUID). Translate Japanese terms via the glossary in `domain_patterns.md` first.

2. **Route via the decision tree above**, then pick the source by the **data-source priority** (`domain_patterns.md` → "Data source priority"): SSOT tables → saved queries (`query_repo.md`, enriched in `query_reference.md`) → other DBs (last resort, with a double-check warning).

3. **Scope correctly.** Whole-JP asks → default store filter. Ward asks → ward CTE. Reuse the file's UUID/name aliases (mind `store_uuid` = parent-chain vs `branch_uuid` = store — names differ across tables).

4. **Compute metrics from the authoritative logic** in `domain_patterns.md` verbatim — never re-derive formulas. Set `Fulfillment_Type` on `retail_snp_tracker_daily_store`. Filter on `datestr`.

5. **No lead in this skill? Fall back to Notion, not to the wild.** If the tables/sample queries here and in `references/*` give no lead, **traverse the team's Notion Table DB (`37f47eb5fd3c80d998ebfc245119def3`) and Query DB (`38347eb5-fd3c-80f1-8005-fb50b3b07af8`) first** to find a table the team already vetted. Prefer a table that belongs to this catalog; only use a table outside it if absolutely unavoidable, and flag it as a last-resort choice needing verification.

6. **When still nothing fits, adapt author history.** Regular authors: `ryan.chan@uber.com`, `piotrk@uber.com`, `fay.xu@uber.com`, `zhww@uber.com`, `soichiro.miyawaki@uber.com`. Pull their recent (~6 mo) queries as table/column signal; resolve identity via `secure_whober.employees` (see `domain_patterns.md`).

7. **Generate/validate net-new SQL via Query Copilot** — delegate to the `query-generation` skill with a JPGR-scoped prompt naming the target tables (SSOT first). It validates columns against live schema.

8. **Validate & return.** Run the output checklist at the end of `domain_patterns.md`. Return: the QueryBuilder link (if reused), the SQL in a code block, the parameters to set, and any last-resort double-check warning.

## Worked example — GB by ward, whole JP Retail (composes the core rules)

Shows: default-scope intent + ward CTE + `datestr` filter + `Fulfillment_Type` + a
metric from a saved query. Adapt tables/columns after verifying in QueryBuilder.

```sql
WITH geo_for_gds AS (
    SELECT g.*, jw.prefecture_eng, jw.ward_eng
    FROM kirby_external_data.jp_eaterops_jpn_ward jw
    JOIN map_geofences.geofences_mbi_admin g
        ON jw.admincode = g.admincode AND g.countrycode = 'JP'
),
store_ward AS (                        -- map each JP grocery store to its ward
    SELECT dm.uuid AS store_uuid, w.prefecture_eng, w.ward_eng
    FROM eds.dim_merchant dm
    JOIN dwh.dim_city dc ON dc.city_id = dm.city_id
    LEFT JOIN geo_for_gds w ON ST_CONTAINS(w.simplified_shape, ST_POINT(dm.longitude, dm.latitude))
    WHERE dc.country_id = 85            -- Japan
      AND dm.uber_merchant_type NOT IN ('MERCHANT_TYPE_RESTAURANT', 'MERCHANT_TYPE_UNKNOWN')
)
SELECT sw.prefecture_eng, sw.ward_eng, SUM(t.gb) AS gb            -- GB = food/item sales + fees (requested)
FROM eats_japan.retail_snp_tracker_daily_store t                 -- operational-day; NOT for finance reporting
JOIN store_ward sw ON sw.store_uuid = t.store_uuid
WHERE t.datestr BETWEEN DATE '2025-06-01' AND DATE '2025-06-30'   -- always filter the datestr partition
  AND t.Fulfillment_Type = 'All'                                  -- 'DELIVERY'=MPP, 'DELIVERY_OVER_THE_TOP'=CPP
GROUP BY 1, 2
ORDER BY gb DESC
```

## MCP Access via aifx gateway (Hermes)

All internal MCP servers are reached through the aifx gateway wrapper. Call any tool with:
```
~/.hermes/scripts/ax.sh mcp call <server> <tool> --args '{...json...}'
```
Discover/inspect when unsure:
- `~/.hermes/scripts/ax.sh mcp search "<keyword>"` — find tools across servers.
- `~/.hermes/scripts/ax.sh mcp call <server> <tool> --args '{...}'` — invoke.

### Backend servers this skill uses

- **usearch-backend** — search/fetch internal knowledge (Databook table definitions, EngWiki QueryBuilder/Query Copilot guides, the JPGR Query Repo and related Google Sheets) to confirm a table schema or find a documented pattern. `usearchbackend_searchv2` **requires `page_size`**; `usearchbackend_getdocuments` honors only the first doc spec per call.
- **queryrunner-mcp** — run Presto SQL (incl. `SHOW COLUMNS FROM <schema.table>` to verify fields). **Pass `{"query": "...", "datasource": "presto"}`** — the correct routing param is `datasource:presto`, NOT `data_center`/`cluster_name` (those route to a `secure` cluster where many GR tables return `completed_failure` for SHOW COLUMNS). Async: `execute_query` → poll `check_execution_status` (arg is `execution_uuids:[...]`, plural list) until `completed_success` → `get_execution_results` (`fetch_rows`). Never `SELECT *` (CLAC on encrypted columns).
- **google-mcp** — read the Query Repo / Metrics Definitions / KPI Google Sheets (`sheets` tool, `{resource,method:"get",params:{spreadsheetId,range|ranges,includeGridData}}`).

### Verifying a table's schema / columns (proven ladder)

To confirm a table's real columns (e.g. before writing SQL, or when cataloging), use this order — learned the hard way (2026-07):

1. **`queryrunner-mcp` `SHOW COLUMNS FROM <schema.table>` with `datasource:"presto"`** — the primary channel. Returns Column/Type/Extra/Comment. (Do NOT use `data_center`/`cluster_name`: the `secure` cluster returns `completed_failure` for SHOW COLUMNS on many GR tables.)
2. **If it returns `completed_failure`, the table name is probably stale/renamed** — resolve the real name via **`usearch-backend` `usearchbackend_searchv2`** (`{"query":"<table stub> <schema>", "page_size":4}`). Real internal SQL in the results reveals the current name. Real example: `kirby_external_data.plan_fx_rates_japan_latest` is stale → the live table is **`kirby_external_data.plan_fx_rates_2026_v2`**. Re-run SHOW COLUMNS on the resolved name.
3. **Databook-backed schema (no Presto dependency):** the local MCPs **`query-mcp-server`** ("uses Databook to get the schema of any table then constructs a Presto query") and **`query_copilot-mcp-server`** ("construct SQL from natural-language context; validates columns against live schema") pull schema from Databook, so they're unaffected by Presto cluster congestion. They are **local/community MCPs** (not proxied by the aifx gateway by default) — configure/run them locally (`aifx mcp add …`) before calling; use as a fallback when queryrunner is congested or a table is restricted.
4. **PII/restricted tables** (e.g. `secure_whober.employees`) may `completed_failure` on SHOW COLUMNS due to CLAC — that's expected; document the table without expanding encrypted columns.

### Getting the real SQL behind a `/r/<id>` report

Unlike the original (Claude-Code) version, in Hermes the QueryBuilder SQL **is** retrievable — use skill `uber-querybuilder-sql-extract` (cerberus proxy + querybuilder utoken, fetch ladder `/v4/report/<id>/published` → draft `/v4/report/<id>` → `/v4/run/<id>`). **Compliance rule: cerberus is local-debug-only — start it manually, kill it immediately after; never in cron / long-running / automation.**

## Related skills

- `query-generation` (Query Copilot) — schema-validated SQL generator. Delegate for net-new SQL; this skill supplies the JPGR grounding.
- `execute-query` — run the SQL and return results, only when the user asks.

## Non-negotiable guardrails

Full rationale lives in `references/domain_patterns.md`; these must always hold:

- **Source order:** SSOT tables → Query Repo → **Notion Table/Query DB** → other DBs (last resort + warning). Don't reach for an uncommon table when a prioritized source covers it.
- **Notion fallback before going outside:** if neither this skill's tables/sample queries nor `references/*` give a lead, **first traverse the team's Notion Table DB (`37f47eb5fd3c80d998ebfc245119def3`) and Query DB (`38347eb5-fd3c-80f1-8005-fb50b3b07af8`)** to find a table already vetted by the team. **Prefer a table that belongs to this catalog; do NOT reach for a table outside it unless absolutely unavoidable** — and if you must, flag it as a last-resort choice needing verification.
- **Finance ≠ operational:** never use the operational-day SSOT trackers for financial/accounting figures (fees, NETR, VC) — use `accounting_date` finance queries.
- **`Fulfillment_Type` is mandatory** on `retail_snp_tracker_daily_store` (`'All'` / `'DELIVERY'` MPP / `'DELIVERY_OVER_THE_TOP'` CPP) — omitting it double-counts.
- **`datestr` filter is mandatory** — an unpartitioned scan is a bug.
- **Japan scope always** — default store filter or an explicit merchant/store filter; never global.
- **FX** — convert only via `kirby_external_data.plan_fx_rates_japan_latest`.
- **Metrics verbatim** from `domain_patterns.md` — never re-derive formulas.
- **No fabricated tables/columns** — verify via Query Copilot or Databook when unsure.
- **`secure_whober.employees` is restricted** — use only to resolve the listed authors for history lookup; never expose PII.
