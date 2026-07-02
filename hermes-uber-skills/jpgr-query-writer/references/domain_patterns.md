# JPGR Domain Patterns

The **single source of detail** for the JPGR Query Writer skill: data-source
priority, scoping (default store filter, ward mapping), authoritative metric
formulas, FX rule, cancellation/defect taxonomies, core tables, and the
Japanese⇄English glossary. `SKILL.md` summarizes; this file is authoritative. When a
table or column is uncertain, verify it with Query Copilot or Databook — do not guess.

Metric definitions are transcribed from the **JPGR Merchant Ops Dashboard — Metrics
Definitions** sheet
(`https://docs.google.com/spreadsheets/d/1w3tsFe01Rbny1GGSNi2sO4-LJKSv2t9jNbwFe8znmuo`).
Use the calculation logic verbatim; do not re-derive metrics.

## Platform basics

- **Engine:** Presto SQL over Hive tables (via QueryBuilder / Query Copilot). Pinot
  tables are queried as `pinotadhoc.<schema>.<table>`.
- **Partitioning:** Hive tables are partitioned by `datestr` (a `'YYYY-MM-DD'`
  string). **Always** add a `datestr BETWEEN start_date AND end_date` (or `=`)
  filter. An unpartitioned range scan is a defect and may be blocked for cost.
- **Scope:** JPGR queries are always scoped to Japan grocery. Apply either a
  country/city filter (Japan) or restrict to the JPGR merchant / parent-chain set.
  A global result is almost never what the team wants.
- **Currency:** most money metrics exist in both **JPY and USD**. Default to JPY for
  JP reporting. USD conversions can differ slightly across dashboards due to the
  exchange rate used — match the source dashboard's currency when reproducing a number.
- **FX rate — always use `kirby_external_data.plan_fx_rates_japan_latest`.** For any
  currency conversion (JPY⇄USD), join to this table for the rate. Do **not** use the
  FX rate embedded in the query/source tables — those are inconsistent across
  dashboards and are the known cause of USD discrepancies. Convert JPY→USD (or back)
  with the rate from `plan_fx_rates_japan_latest` so numbers reconcile across reports.
- **Time granularity:** the team parameterizes `month | week | day` and usually
  truncates `datestr` accordingly (e.g. `date_trunc('week', ...)`).

## Data source priority (follow in order)

Pick where to get data in this strict order. Do not jump to obscure tables when a
prioritized source covers the metric.

**1. Prioritized SSOT tables — try these first.**

> ⚠️ **Operational-day vs accounting-date:** these SSOT tracker tables are aggregated
> by **operational day**. Do **not** use them for **financial reporting** — fees,
> NETR, VC (variable contribution), and other finance figures must be aggregated by
> **`accounting_date`**. For those, use finance-oriented queries in `query_repo.md`
> (e.g. the Consolidated Dash / topline finance queries) that aggregate on
> `accounting_date`, not these operational-day trackers.

| Source | Use for | Notes |
|---|---|---|
| `eats_japan.retail_snp_tracker_daily_store` | store-level operational topline / sales / ops / fulfillment (operational-day) | **Always** filter `Fulfillment_Type`: `'All'` for everything, `'DELIVERY'` for MPP-only, `'DELIVERY_OVER_THE_TOP'` for CPP-only. **Not** for finance/accounting reporting. |
| `eats_japan.retail_snp_tracker_daily_promo_ads` | promo & ads metrics (operational-day) | Not for accounting-date finance reporting. |
| `eats_japan.mops_dash_catalog_v2` | catalog / SKU / coverage | |
| `eats_japan.mops_dash_discovery` | search / impressions / discovery | |
| `kirby_external_data.gr_jp_ssot_merchant_information` | **Parent-Chain-level SSOT** — merchant/brand attributes, AM, vertical, grouping | join key `parent_chain_uuid`; see store filter below. |

**2. Fall back to the saved queries** in `query_repo.md` if step 1 can't answer the
question. Adapt the closest one.

**3. Only if steps 1 and 2 both fail**, search other databases (via Query Copilot /
Databook) — and **explicitly warn the user** in the output that the table is not
commonly used and the result should be double-checked.

## Standard JP Retail store filter (default scope)

When the request is for **JP Retail as a whole** and no specific store / brand /
parent chain / merchant is given, scope with this canonical filter. It also
establishes the team's UUID/name mapping conventions — reuse the aliases.

```sql
select
    smi.partner_manager as account_manager
    , coalesce(smi.vertical, ds.store_category) as merchant_category
    , smi.grouped_parent_name as grouped_parent
    , smi.subsidiary_company as merchant_group
    , smi.Grouped_merchant_for_query as unified_merchant
    , store_uuid as merchant_uuid   -- store_uuid in grdw.dim_storefront = parent_chain_uuid in eds.dim_merchant
    , coalesce(grouped_merchant_for_query, lower(ds.store_name_fixed)) as merchant_name
    , branch_uuid as store_uuid     -- branch_uuid in grdw.dim_storefront = uuid in eds.dim_merchant,
                                    --   or store_uuid / restaurant_uuid / storefront_uuid in other tables
    , lower(branch_name) as store_name
from grdw.dim_storefront ds
left join kirby_external_data.gr_jp_ssot_merchant_information smi
    on ds.store_uuid = smi.parent_chain_uuid
    and country_name = 'Japan'
    and is_nv
    and not is_uber_direct
```

**UUID mapping cheat-sheet (critical — these names differ across tables):**
- `grdw.dim_storefront.store_uuid` == parent-chain level == `eds.dim_merchant.parent_chain_uuid`. Alias it as `merchant_uuid`.
- `grdw.dim_storefront.branch_uuid` == store/location level == `eds.dim_merchant.uuid`, and appears elsewhere as `store_uuid` / `restaurant_uuid` / `storefront_uuid`. Alias it as `store_uuid`.
- Join `dim_storefront.store_uuid` → `gr_jp_ssot_merchant_information.parent_chain_uuid` for parent-chain SSOT attributes.
- JP Retail rows require `country_name = 'Japan'`, `is_nv` (new verticals / grocery-retail), and `not is_uber_direct`.

## Ward-level (administrative area) mapping

For **ward-level asks** (Japanese 区/市 administrative wards — region / prefecture /
ward), map each store to its ward by point-in-polygon on the store's lat/long
against the JP ward geofences. Use this exact pattern (`geo_for_gds` CTE joins the
ward dictionary to the admin geofence shapes; then `ST_CONTAINS` locates each store):

```sql
WITH geo_for_gds AS (
    SELECT
        g.*
        , jw.region_eng
        , jw.region_jpn
        , jw.prefecture_eng
        , jw.prefecture_jpn
        , jw.ward_eng
        , jw.ward_jpn
        , jw.prefecture_ward_for_gds
    FROM kirby_external_data.jp_eaterops_jpn_ward jw
    JOIN map_geofences.geofences_mbi_admin g
        ON jw.admincode = g.admincode
        AND g.countrycode = 'JP'
)
SELECT DISTINCT
    dm.uuid AS store_uuid,
    w.ward_eng AS city_kanji
FROM eds.dim_merchant dm
JOIN dwh.dim_city dc ON dc.city_id = dm.city_id
LEFT JOIN geo_for_gds w
    ON ST_CONTAINS(w.simplified_shape, ST_POINT(dm.longitude, dm.latitude))
WHERE dc.country_id = 85                       -- Japan
    AND dm.uber_merchant_type NOT IN ('MERCHANT_TYPE_RESTAURANT', 'MERCHANT_TYPE_UNKNOWN')
```

Notes:
- `eds.dim_merchant.uuid` is the **store-level** UUID (aliased `store_uuid` here) — join
  this to the store metrics you need, then group by the ward columns.
- Ward dictionary `kirby_external_data.jp_eaterops_jpn_ward` provides both English and
  Japanese labels for region / prefecture / ward (`*_eng` / `*_jpn`) plus
  `prefecture_ward_for_gds`; select whichever grain the ask needs.
- `dc.country_id = 85` = Japan; `uber_merchant_type` filter excludes restaurants and
  unknowns (keeps grocery/retail non-food).
- The mapping is geospatial (`ST_CONTAINS` on `simplified_shape`); use it as a CTE and
  join your metric query onto `store_uuid`.

## Reference queries by metric family

These "canonical logic" queries hold the vetted calculation logic. Open them to
copy joins/columns rather than hand-writing metric math:

- **Topline / finance / eater metrics:** `JP - Grocery & Retail - Consolidated Dash` → `/r/bmY4WMCSj`
- **Fulfillment, C/R, Defect metrics (one query):** `/r/nCclu4TX9` (Replacement Rate logic updated 7/10/25 → `/r/nCclu4TX9/run/63KhB14n1`)
- **Catalog Quality (Canonical GB etc.):** `/r/vNN0N6raL`
- **Discovery / search / impressions:** `/r/h42aTbqVR` (table `eats_japan.mops_dash_search`)

## Metric definitions (authoritative calculation logic)

### Topline / Finance
| Metric | Definition | Calculation |
|---|---|---|
| **GB (JPY / USD)** | Gross Bookings | Food/item sales + fees from **requested** orders |
| **Food Sales (JPY / USD)** | Merchandise value | Food/item sales from **requested** orders (excludes fees) |
| **Organic GB (JPY)** | GB without discounts | items sold without any discounts |
| **% Organic GB** | | Organic GB / GB |
| **Promo GB (JPY)** | GB with discounts | items sold with some discounts |
| **Organic / Promo Food Sales (JPY)** | | Food sales from items sold without / with discounts |
| **Total Promo Spend (JPY)** | | Total promotional investment (merchant + Uber) |
| **Merchant Funded Promo Spend (JPY)** | | Promo investment made by merchants |
| **% Merchant Funded Promo Spend** | | Merchant Funded Promo Spend / Total Promo Spend |
| **Total Promo ROI** | | GB / Total Promo Spend |
| **Add-on GB (JPY)** / **% Add-on GB** | | GB from add-on orders / … ÷ GB |
| **Uber One GB / Food Sales (JPY)** | subscription | GB / Food Sales from Uber One eaters' orders (and % of total) |
| **Ads Revenue (JPY)** | | Advertiser ad revenue from orders within 7 days of an ad click |
| **Ads Spend (JPY)** / **Ads ROI** | | ad investment / Ads Revenue ÷ Ads Spend |
| **# / % Orders from Ads** | | orders within 7 days of an ad click / ÷ # Completed Orders |

### Store / activation & core rates
| Metric | Definition | Calculation |
|---|---|---|
| **# Activated Stores** | | stores with onboarding_status = `'activated'` |
| **# Activated Stores with Orders in L7D** | | stores with ≥1 order in past week |
| **% Activated Stores without Orders** | | (Activated − Activated w/ Orders) / Activated |
| **TpR (Trip per Restaurant)** | | # Completed Orders / # Activated Stores |
| **ABS (JPY)** | Average Basket Size | Food Sales (JPY) / # Completed Orders |
| **SKU per Order** | | # SKUs in Completed Orders / # Completed Orders |
| **ASP (Average Selling Price)** | | Food Sales (JPY) / # Units Fulfilled |

### Store-level eater metrics
Calculated at store level; an eater ordering from multiple locations of the same
merchant is **de-duplicated and counted at one location only**.

| Metric | Calculation |
|---|---|
| **Monthly / Weekly OPE (Store Level)** | # Completed Orders / # Monthly (Weekly) Active Eaters |
| **# Monthly / Weekly Active Eaters** | eaters ordering ≥1 in the month (week) |
| **# Monthly / Weekly Retained Eaters** | active this period **and** order again next period |
| **Monthly / Weekly Retention Rate** | Retained Eaters / Active Eaters |
| **# Monthly / Weekly FT Merchant** | eaters ordering from the merchant for the **first time** in the period |
| **# … FT Merchant Retained** | FT this period and order again next period |
| **… FT Merchant Retention Rate** | FT Merchant Retained / FT Merchant |

### Fulfillment metrics (source: `fgo`/`fgod`; query `/r/nCclu4TX9`)
| Metric | Calculation |
|---|---|
| **Products Requested / Fulfilled** | # unique SKUs requested / fulfilled |
| **Items FR** | sum of item-level found rate (input to Found Rate) |
| **Items FFR** | sum of item-level fulfillment rate (input to Fulfillment Rate) |
| **Found Rate** | Items FR / Quantity Requested |
| **Fulfillment Rate** | Items FFR / Quantity Requested |
| **# SKUs Replaced** | requested SKUs replaced (best match or specific item) |
| **# SKUs OOS and Replacement Requested** | requested SKUs that were OOS and eater wanted them replaced |
| **Replacement Rate** | # SKUs Replaced / # SKUs OOS and Replacement Requested (logic updated 7/10/25) |
| **# Units Fulfilled** | units fulfilled |
| **Hours Online / Hours Stated** | hours merchant accepted orders / hours it should per menu hours |
| **Online Rate** | Hours Online / Hours Stated |

### C/R (completion/cancellation rate) metrics
| Metric | Definition | Calculation |
|---|---|---|
| **Orders Requested / Completed** | placed / successfully delivered | — |
| **eC/R** | eater-facing completion rate | Orders Completed / Orders Requested |
| **Orders Offered to / Completed by Merchants** | | — |
| **mC/R** | merchant completion rate | Orders Completed by Merchants / Orders Offered to Merchants |
| **Delivery Trips Requested / Completed** | | — |
| **dC/R** | delivery completion rate | Delivery Trips Completed / Delivery Trips Requested |

Cancellations are bucketed by **responsible party** (Courier / Eater / Merchant /
Uber System / Unknown). See the Cancellation taxonomy below for the full list of
reason codes and their S&P names.

### Defect metrics (source: `fgo, commops`; query `/r/nCclu4TX9`)
| Metric | Calculation |
|---|---|
| **# Defects** | orders with any support ticket filed |
| **Defect Rate** | # Defects / # Completed Orders |
| **# Order Accuracy Defects** | defects about items/orders themselves (÷ Completed = %) |
| **# Missing or Incorrect Item Defects (Merchant Responsible)** | orders reported missing/incorrect item (÷ Completed = %) |
| **# Entirely Wrong Order Defects (Merchant Responsible)** | orders where a different order was delivered (÷ Completed = %) |

Order-accuracy defect subtypes are mapped from `current_contact_type` values to a
responsible party. See the Defect taxonomy sheet
(`docs.google.com/document/d/1sw5QqRKH5Wf18VXoR_fXsPVyuvQW1oUCHeNCSyV62vg`) —
e.g. Courier: *Delivered to Wrong Address*, *Delivered Wrong Order*, *Forgot Part
of Order*; Merchant: *Missed Items*, *Replaced Items Incorrectly*, *Supplied Wrong
Order to DP*, *Did Not Follow Customer Request*.

### Catalog quality metrics
| Metric | Calculation | Source table |
|---|---|---|
| **Canonical GB** / **% Canonical GB** | GB from products linked to Canonical / ÷ GB | `/r/vNN0N6raL` |
| **# Items / # Purchasable Items** | avg items listed / not OOS per store | `grdw.agg_gr_inca_store_available_item_snapshot` |
| **% Purchasable SKU** | # Purchasable Items / # Items | ↑ |
| **# Items Purchased in L30D / L7D** & **L30D/L7D Purchased Rate** | avg items purchased ≥1 in month/week ÷ # Items | `fgod` |
| **# Products / with UPT / with Photo / with GTIN** | catalog product counts | `grdw.agg_gr_inca_catalog_metric_snapshot` |
| **UPT / Photo / GTIN Coverage** | # Products with X / # Products | ↑ |
| **Restricted / Alcohol / OTC Sales (USD)** & their % | | `mmi, fgod` |

### Discovery metrics (source: `eats_japan.mops_dash_search`; query `/r/h42aTbqVR`)
| Metric | Calculation |
|---|---|
| **# In-Store Searches** | times eaters used in-store search |
| **In-Store Search Add to Cart Rate** | In-Store Search to Cart / # In-Store Searches |
| **In-Store Search Conversion Rate** | In-Store Search to Order / # In-Store Searches |
| **Search without Result Rate** | # Zero In-Store Search Results / # In-Store Searches |
| **Average Search Add to Cart Position** | avg position of items added from search results |
| **# Menu Impressions / Menu to Cart / Menu to Order** | impressions on menu pages / that led to cart / order |
| **Menu to Cart Rate / Menu to Order Rate** | Menu to Cart (Order) Impressions / # Menu Impressions |
| **# Any Impressions** | store-name impressions across feed, carousel, search, marketing, reorder (proxy for addressable sessions) |
| **Impressions from Store Cards / Carousel / Reorder / Global Search** | store-name impressions by surface (Store Cards & Carousel defined in the Share of Voice Dashboard, EngWiki NVBI) |
| **Store Cards/Carousel/Reorder/Global Search to Menu** | impressions of that surface that led to a menu tap |

## Cancellation taxonomy (responsible party → reason)

Classified per global 2024 logic. Format: **S&P name — metric name — reason**.

- **Courier:** PRODUCT DAMAGED · DROP-OFF FAILED · ORDER OVERSIZED · COURIER RELATED ISSUES · ROUTE ISSUES · SAFETY CONCERN · TOO FAR AWAY · COURIER UNAVAILABLE · UNRESPONSIVE COURIER · VEHICLE ISSUES
- **Eater:** CONSUMER CANCEL (Cancelled) · CONSUMER ORDERED INCORRECTLY (Cancelled to Modify) · CONSUMER CHANGED MIND · ID VALIDATION ISSUES (Failed ID Validation) · FRAUDULENT ORDERS · DID NOT MEAN TO ORDER (Ordered by Accident) · UNRESPONSIVE CONSUMER
- **Merchant:** CLOSED STORE (Store Closed) · NO STOCK · STORE ISSUES · WRONG ORDER (Supplied Wrong Order) · EXCESSIVE WAIT TIME (Took Too Long) · STORE ACCEPTANCE (Unaccepted)
- **Uber System:** APP ISSUES · ORDER ALREADY PICKED UP · CONSUMER PAYMENT ISSUES (Payment Failure) · PIN FAILURE · STORE CONFIG (Store Config Issue)
- **Unknown:** UNKNOWN

## Vocabulary shorthands

| Term | Meaning |
|---|---|
| **UPT** | Uber Product Taxonomy (hierarchical item category; has levels, e.g. L1/L2). |
| **SKU** | Catalog item; "# Purchasable SKU" = active/orderable items. |
| **INCA** | Integrated catalog pipeline (vs "Menu Maker"/MM manual catalog). |
| **Canonical** | Products linked to Uber's canonicalized catalog. |
| **DP** | Delivery Partner (courier). |
| **FTGR / FT Merchant** | First-Time Grocery Retail user / first-time-at-this-merchant eater. |
| **OOS / OOI** | Out Of Stock / Out Of Inventory item. |
| **Busy Mode** | store throttled/limiting orders. |
| **SAM** | Serviceable Addressable Market. |
| **MAU** | Monthly Active Users. |
| **SoV** | Share of Voice (impression share across surfaces). |
| **LTV** | eater Lifetime Value. |
| **MPP / CPP** | Merchant Pickup Point / Consolidated Pickup Point (courier fulfillment models). |
| **EPUH** | Earnings Per Utilized Hour (courier economics). |
| **Dampening** | courier supply/pay dampening adjustment. |

## Standard parameters (mirror the Query Repo)

```
start_date, end_date            -- 'YYYY-MM-DD'
time_granularity                -- month | week | day
onboarding_status               -- activated | lead | onboarding | on hold
merchant_name / merchant_uuid   -- brand filter (name or UUID)
store_uuid / catalog_uuid       -- location / catalog filter
merchant_or_store_level         -- merchant | store  (controls GROUP BY grain)
GTIN / item name / section      -- item filters
UPT_level, UPT                  -- taxonomy level + value
country_or_city / vertical      -- geo / vertical rollups
```

When a user gives a merchant/store **name**, map it to its UUID first (see the
"Stores by parent chain name" / "Store External ID Search" queries in
`query_repo.md`), then filter on the UUID for reliability.

## Core data sources

Authoritative table names (from the Metrics Definitions sheet); always confirm exact
columns by opening the linked query or Databook:

- `grdw.agg_gr_inca_store_available_item_snapshot` — store-level catalog availability (# Items, # Purchasable).
- `grdw.agg_gr_inca_catalog_metric_snapshot` — catalog product metrics (# Products, UPT/Photo/GTIN coverage).
- `eats_japan.mops_dash_search` — in-store search / discovery metrics.
- `dintel_shopping.menu_snapshot_summary` — item price / menu snapshot.
- `dintel_shopping.nv_item_metrics` — item checkout metrics.
- `kirby_external_data.jp_hex_geo_v4` — Japan hex geofences (geo/coverage).
- `kirby_external_data.plan_fx_rates_japan_latest` — **canonical FX rates for JPY⇄USD conversion**; always use this instead of any FX rate embedded in query/source tables.
- `secure_whober.employees` — employee directory (restricted; used only to resolve author identities, see below).

Source-system shorthands seen in the sheet: `fgo`/`fgod` (fulfillment order data),
`fet` (fleet/trips), `rs` (restaurant/store status), `mmi` (merchant menu items),
`kirby` (catalog/canonical), `commops` (support/defects), `subsc` (subscription),
`ads` (advertising), `finance`.

For anything else, resolve the exact table via Query Copilot (it validates against
live schema) or Databook (`https://databook.uberinternal.com/datasets/hive/<schema>.<table>/definition`).

## Generating net-new SQL (delegate to Query Copilot)

When no Query Repo entry and no author-history query matches, do not hand-write
schema from memory. Instead:

1. Draft the intent + the candidate tables (from this file / the repo).
2. Invoke the `query-generation` skill (Query Copilot) with a JPGR-scoped prompt:
   name the metric, grain, date range, Japan scope, and any known tables. Query
   Copilot is tuned for Retail delivery metrics and validates columns against the
   live schema.
3. Take the returned SQL, re-apply the JPGR guardrails (datestr filter, Japan
   scope, JPY) and the exact metric logic above, and return it.

## Resolving authors & pulling history

Regular JPGR query authors:
`ryan.chan@uber.com`, `piotrk@uber.com`, `fay.xu@uber.com`, `zhww@uber.com`,
`soichiro.miyawaki@uber.com`.

Their past ~6 months of queries are the best signal when the catalog falls short —
they show which tables/joins the team actually uses.

- **Resolve identity:** `secure_whober.employees` maps work email → employee /
  user identity (columns such as `email`, `user_uuid`/`employee_uuid`, org, team).
  This is a **secure** table: use it only to resolve these five people for history
  lookup, and never surface their personal data in output. Confirm the exact
  column names via Databook before relying on them.
- **Find their queries:** open a recent query each author owns in the Query Repo
  (the sheet lists owners), or ask the user to share a QueryBuilder/Query Copilot
  link from one of them. Adapt the closest one. If a query-history dataset is
  available in your environment, filter it to these emails and
  `datestr >= date_add('month', -6, current_date)`.

## Japanese ⇄ English glossary

The team works bilingually; requests and merchant/section names often arrive in
Japanese. Map Japanese terms to the metric/entity names above.

### Metrics & finance
| 日本語 | English |
|---|---|
| 総取引額 / GB | GB (Gross Bookings) |
| 売上 | Food Sales / Item Sales |
| オーガニック売上 | Organic GB / Organic Food Sales |
| プロモ売上 | Promo GB / Promo Food Sales |
| プロモ費用 | Promo Spend |
| 店舗負担プロモ | Merchant Funded Promo Spend |
| 注文単価 | ABS (Average Basket Size) |
| 平均販売価格 | ASP (Average Selling Price) |
| 広告売上 / 広告費用 | Ads Revenue / Ads Spend |
| Uber One 売上 | Uber One GB / Food Sales |
| 注文数 | # Orders |
| 完了注文 / 完了トリップ | Completed Orders / Completed Trips |
| リクエスト注文 | Requested Orders |

### Stores / eaters / operations
| 日本語 | English |
|---|---|
| マーチャント | Merchant |
| 店舗 / ストア | Store |
| ブランド | Parent Chain |
| 地域 / リージョン | Region (ward mapping) |
| 都道府県 | Prefecture |
| 区 / 市区 / ワード | Ward |
| アクティブ店舗 | Activated / Active Stores |
| オンボーディング状況 | onboarding_status |
| オンライン率 | Online Rate |
| 受注率 / アクセプタンス率 | Acceptance Rate |
| 実営業時間 | Hours Online |
| 登録営業時間 | Hours Stated (menu hours) |
| 混雑モード | Busy Mode |
| ユーザー | Eater / Consumer |
| 新規利用者 | First-Time user (FTGR / FT Merchant) |
| リテンション / 継続率 | Retention Rate |
| アクティブ利用者 | Active Eaters |
| 注文頻度 (OPE) | OPE (orders per eater) |

### Fulfillment / cancellation / defect
| 日本語 | English |
|---|---|
| 在庫切れ / 欠品 | Out of Stock (OOS/OOI) |
| 発見率 | Found Rate |
| 商品充足＋代替率 | Fulfillment Rate |
| 代替率 / 置き換え率 | Replacement Rate |
| 代替品 / 置き換え | Replacement item |
| 充足数量 | # Units Fulfilled |
| キャンセル / キャンセル率 | Cancellation / C/R (eC/R, mC/R, dC/R) |
| キャンセル理由 | Cancellation Reason |
| 責任者 (配達員/イーター/加盟店/システム) | Responsible Party (Courier / Eater / Merchant / Uber System) |
| 欠陥 / ディフェクト | Defect |
| 欠陥率 | Defect Rate |
| 注文精度 | Order Accuracy |
| 商品欠落 / 誤配 | Missing / Wrong Item |
| 配達員 / クーリエ | Courier / Delivery Partner (DP) |

### Catalog / discovery
| 日本語 | English |
|---|---|
| カタログ | Catalog |
| 商品 / アイテム | Product / Item |
| SKU / 品目数 | SKU / # Items |
| 購入可能商品 | Purchasable Items |
| 商品分類 / カテゴリ | UPT / Section / Subsection |
| セクション / サブセクション | Section / Subsection |
| 写真カバレッジ | Photo Coverage |
| GTIN / JANコード | GTIN |
| カノニカル | Canonical |
| 検索 / 店内検索 | Search / In-Store Search |
| カート追加率 | Add to Cart Rate |
| インプレッション / 表示回数 | Impressions |
| メニュー表示 | Menu Impressions |
| 制限商品 / 酒類 / 医薬品(OTC) | Restricted / Alcohol / OTC items |

### Time / filters
| 日本語 | English |
|---|---|
| 日次 / 週次 / 月次 | day / week / month (time_granularity) |
| 開始日 / 終了日 | start_date / end_date |
| 過去7日 (L7D) / 過去30日 (L30D) | Last 7 / 30 Days |
| 前週比 (WoW) / 前月比 (MoM) | Week-over-Week / Month-over-Month |

## Output checklist

Before returning SQL, confirm:
- [ ] Data source chosen by priority order (SSOT tables → saved queries → warned fallback).
- [ ] Not a finance/accounting report using operational-day trackers — financial figures (fees, NETR, VC, etc.) use `accounting_date`-aggregated finance queries, not the SSOT trackers.
- [ ] `Fulfillment_Type` set when using `retail_snp_tracker_daily_store` (`'All'` / `'DELIVERY'` MPP / `'DELIVERY_OVER_THE_TOP'` CPP).
- [ ] Default JP Retail store filter applied when no entity is specified (`country_name='Japan'`, `is_nv`, `not is_uber_direct`); correct `store_uuid` vs `branch_uuid` aliasing.
- [ ] Filters on `datestr` within the requested range.
- [ ] Scoped to Japan grocery (country/city or JPGR merchant set).
- [ ] Grain matches the ask (`merchant_or_store_level` correct).
- [ ] Metric matches the authoritative calculation logic above (esp. GB vs Food Sales; Found vs Fulfillment vs Replacement Rate; the four C/R variants).
- [ ] Every table/column verified (Query Copilot / Databook), none fabricated.
- [ ] Currency correct (JPY vs USD) and noted; any FX conversion uses `kirby_external_data.plan_fx_rates_japan_latest` (not table-embedded FX).
- [ ] Japanese terms in the request mapped via the glossary.
- [ ] Closest existing QueryBuilder link included when one exists.
