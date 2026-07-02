# JPGR Query Reference (enriched)

A per-query lookup so you can reuse the saved reports **without opening each
QueryBuilder link**. For every query: the metric(s) it returns, its grain, its
filters/parameters, currency, and the **likely source table(s)**.

## How to read this file & accuracy caveat

- **Source tables are inferred**, not read from the query SQL. The raw SQL behind
  `querybuilder.uberinternal.com/r/<id>` links is not retrievable in this
  environment, so table/column names are derived from the authoritative **Metrics
  Definitions** sheet, the **priority SSOT tables**, and topic. Tables marked
  **(SSOT)** come from the priority list; **(defn sheet)** are stated in the Metrics
  Definitions sheet; **(infer)** is a best guess — **verify in QueryBuilder before
  relying on the exact table**.
- **Metric calculation logic** is authoritative — it comes from the Metrics
  Definitions sheet (see `domain_patterns.md` for the full formulas). This table
  gives the short form.
- **Prefer the priority order** in `domain_patterns.md`: for most store/merchant
  metrics the SSOT trackers already have the number; use a specific saved query when
  the SSOT tables don't cover it. **Never use the operational-day SSOT trackers for
  finance/accounting reporting (fees, NETR, VC) — those need `accounting_date`.**

## Likely source tables by topic (inference key)

| Topic | Primary table(s) | Notes |
|---|---|---|
| Store operational topline / sales / ops / fulfillment | `eats_japan.retail_snp_tracker_daily_store` (SSOT) | filter `Fulfillment_Type`; operational-day, **not** finance |
| Promo & ads | `eats_japan.retail_snp_tracker_daily_promo_ads` (SSOT) | operational-day |
| Catalog / SKU / coverage | `eats_japan.mops_dash_catalog_v2` (SSOT); `grdw.agg_gr_inca_catalog_metric_snapshot`, `grdw.agg_gr_inca_store_available_item_snapshot` (defn sheet) | |
| Search / impressions / discovery | `eats_japan.mops_dash_discovery` (SSOT); `eats_japan.mops_dash_search` (defn sheet) | |
| Parent-chain / merchant attributes | `kirby_external_data.gr_jp_ssot_merchant_information` (SSOT) | join `parent_chain_uuid` |
| Store/branch dimension & default filter | `grdw.dim_storefront` ⨝ SSOT merchant info; `eds.dim_merchant` | `store_uuid`=parent-chain, `branch_uuid`=store |
| Finance / topline (accounting-date) | Consolidated finance queries (`/r/bmY4WMCSj`, `/r/nCclu4TX9`) | use for fees/NETR/VC |
| Item price / menu snapshot | `dintel_shopping.menu_snapshot_summary`, `dintel_shopping.nv_item_metrics` (defn sheet) | |
| Geo / hex / coverage | `kirby_external_data.jp_hex_geo_v4` (defn sheet) | |
| FX / currency conversion | `kirby_external_data.plan_fx_rates_japan_latest` | **Always** use for JPY⇄USD; never the table-embedded FX rate. |

Standard params (`start_date`, `end_date`, `time_granularity`, `merchant_name`,
`merchant_or_store_level`, `onboarding_status`, `store_uuid`, `merchant_uuid`,
`catalog_uuid`, `GTIN`) are defined once in `query_repo.md`; below, "Params" lists
only what each query takes.

---

## Sales

| Query (link) | Metric(s) | Grain | Params / Filters | Calc (short) | Likely table(s) |
|---|---|---|---|---|---|
| [Store Level] GB `/r/x5Pv7jAzN` | GB | store | start/end, time_granularity | Food/item sales + fees, requested orders | `retail_snp_tracker_daily_store` (infer) |
| [Merch/Store & Item] Sales & Qty `/r/6qHel0y2P` | Item Sales, Qty Sold | store/merchant × item | start/end, merchant_name, time_granularity, merchant_or_store_level | Food sales; units fulfilled | tracker/store-item (infer) |
| …+ Section/Subsection `/r/plH8Atl87` | Item Sales, Qty Sold | + section | start/end, merchant_name, time_granularity | as above by section | (infer) |
| Sales/Qty/Price by GTIN `/r/6vkKuP2NZ` | ASP, Qty Sold, Item Sales | store × item | start/end, time_granularity, merchant_name, merchant_or_store_level, GTIN | ASP = Food Sales / Units Fulfilled | catalog + tracker (infer) |
| [GTIN] Sales Across All Merchants `/r/iu3L4roQV` | Item Sales, Qty Sold | GTIN | time_granularity, start/end | sum across merchants by GTIN | (infer) |
| "Everything" item query `/r/F6F5gzD8f` | Item Sales, Qty Sold, Sales Loss from OOS, ASP, Found Rate, Fulfillment Rate | store/merchant × item name | time_granularity, start/end, onboarding_status, merchant_or_store_level | see fulfillment formulas | tracker + fgo/fgod (infer) |
| [Merch/Store & Section] Sales `/r/1HPUW6769` | Qty Sold, Item Sales | store/merchant × section | start/end, merchant_uuid/name, store_uuid, merchant_or_store_level | food sales by section | (infer) |
| [Vertical & Item] Sales `/r/iT1PzCxZt` | Item Sales, Qty Sold | vertical × item + section | start/end, time_granularity | food sales by vertical | (infer) |
| [Merch/Store × Hour × Section] Food Sales `/r/do4eobq27` | Item Sales | hour × section | start/end, merchant_name | food sales | tracker (infer) |
| [Country/City/Vertical] TpR / Food Sales / per-store by tenure `/r/tQs9TfxDZ` | # Requested Trips, Item Sales | country/city/vertical × tenure | start/end, country_or_city | TpR = Completed Orders / Activated Stores | tracker (infer) |
| [Country/Vertical/Merch/Store] Hourly Orders / Food Sales / GB `/r/mc3hYRAV5` | GB, Requested, Completed | geo/merchant × hour | start/end, merchant_or_store_level, country_or_vertical_or_merchant, merchant_name | avg hourly | tracker (infer) |
| [Store × UPT] Orders Penetrated / Qty / Food Sales `/r/6VIsxTbLl` | Qty Sold, Item Sales | store × UPT | UPT_level, UPT, start/end | by UPT | catalog + tracker (infer) |
| [Item] Sales / Qty Fulfilled by store+section `/r/ITgct75i3` | Item Sales, Qty Sold | item | start/end, store_uuid | qty fulfilled | (infer) |
| [Store×Order×Item] Order ID / Fulfilled / Final Food Sales `/r/FjRlHgSPp` | Item Sales, Qty Sold | order × item | start/end, merchant_name, store_uuid | final food sales | order-level (infer) |
| [Merchant] GB past X months w/ percentile `/r/zJeQpIk83` | Item Sales | parent chain | start_date, num_months | GB + percentile | tracker (infer) |
| ABS Distribution `/r/27UWUzeAj` | ABS | bucket | start/end, merchant_name | ABS = Food Sales / Completed Orders | tracker (infer) |
| sales by UPT/brand/category `/r/8jHNdXSPd` | Item Sales | UPT/brand/category | — | by taxonomy | catalog (infer) |

## Operational Performance (fulfillment / OOS / cancels / online)

Fulfillment/C/R/Defect canonical logic query: **`/r/nCclu4TX9`** (source `fgo`/`fgod`/`commops`).

| Query (link) | Metric(s) | Grain | Params | Calc (short) | Likely table(s) |
|---|---|---|---|---|---|
| [Store] Requested/Completed/OOI/Defects/CR `/r/47Wdgy5uz` | Completed Trips, eC/R, OOI, Defects | store | start/end, time_granularity | eC/R = Completed/Requested; Defect Rate = Defects/Completed | tracker + fgo (infer) |
| [Item] OOS list + Replacement `/r/IZFvZnNyj` | — (list) | item | start/end | OOS items + replacements | fgod (infer) |
| [Item] OOS list + Sales Loss `/r/aU6RSDdAn` | Sales Loss from OOS | item | start/end | GB lost to OOS | fgod (infer) |
| [Store] GB Loss from Unfulfillment `/r/5y69VgKof` | Sales Loss | store | — | unfulfilled GB | fgod (infer) |
| [Store] % OOI Trips `/r/I1BOWuy6z` | % OOI | store | — | OOI trips / trips | tracker (infer) |
| [Merch/Store × Item] Found/Replacement etc. `/r/3BloHMSNN` | Found Rate, Replacement Rate | store/merchant × item | start/end, time_granularity, merchant_or_store_level | Found = Items FR / Qty Requested; Repl = SKUs Replaced / SKUs OOS&ReplReq | fgo/fgod (infer) |
| [UPT L2] Sales Loss / Found / Fulfillment / Replacement `/r/IFCEFanVJ` | Item Sales, Found/Fulfillment/Replacement Rate, Sales Loss | parent chain × UPT | time_granularity, start/end | see fulfillment formulas | fgo/fgod + catalog (infer) |
| [UPT of choice] Fulfillment/Found/Replacement `/r/jnaJs41tl` | Found/Fulfillment/Replacement Rate | UPT/country/vertical/chain | start/end, time_granularity, country_or_vertical_or_merchant, UPT_level | as above | fgo/fgod (infer) |
| [Country/Merchant × GTIN] Found/Requested/OOS Loss/UPT/Section `/r/z9reUu1PZ` | Found Rate, Sales Loss from OOS | chain × GTIN | start/end, time_granularity, country_or_merchant | as above | fgo/fgod + catalog (infer) |
| [Merchant] Replacement Rate by fulfillment pref `/r/6rPi5lMV5` | Replacement Rate | parent chain | start/end, merchant_name, time_granularity | Repl rate by eater pref | fgod (infer) |
| [Store] Daily Online Rate `/r/jUfg6cTS7` | Online Rate | store | start/end, merchant_name | Hours Online / Hours Stated | `rs`/tracker (infer) |
| [Merch/Store] Hourly Online Rate / Busy-mode mins `/r/3R5fzgdSv` | Online Rate, Busy-mode minutes | hour | start/end, merchant_name, merchant_or_store_level | as above | `rs` (infer) |
| [Month-Store] Acceptance Rate & GB `/r/rR5SCPftR`; [Month-Merchant] `/r/t9CFRobx1` | Acceptance Rate, GB | store / merchant × month | — | accepted / offered | tracker (infer) |
| [Order] Cancel Source / Reason `/r/mhXYc50z5` | eC/R | order | start/end, merchant_name | cancellation taxonomy | fgo (infer) |
| [Merch×Order] Cancelled Orders by source `/r/r7eGiiNR9` | — (list) | parent chain | start/end | by cancel source | fgo (infer) |
| [Merch/Store] # Cancellations / Sales Loss by reason `/r/jEogUkrGv`; all-merchants `/r/5pAMzZLUn` | Sales Loss | store / chain | start/end, time_granularity, merchant_or_store_level | loss by cancel reason | fgo (infer) |
| [Defect & Bliss] Defect list / type / ticket `/r/dLswjDww3` | — (list) | chain × defect | start/end, merchant_name | defect taxonomy | commops (infer) |
| JPGR MOps OKR 2025 H1 `/r/l2cxQLr3d` | mixed ops/finance/catalog | country/vertical/merchant/store | start/end, time_granularity, merchant_or_store_level, fulfillment_types | OKR bundle (incl. CPP) | tracker + catalog (infer) |
| Online Courier MPP `/r/uYSYo4YtF`; CPP `/r/ECI4b67RJ` | online couriers | courier | — | MPP vs CPP model | courier econ (infer) |
| Dampening `/r/yTdP5UoTt` | dampening | courier/supply | — | supply/pay dampening | courier econ (infer) |
| Delivery Time Related `/r/tDaeuXF0P` | delivery time | trip | — | delivery-time metrics | trips (infer) |
| Courier pay & Batch-discounted Hours (EPUH) `/r/rquvyKWo7` | courier pay, batch hours | courier | — | inputs for EPUH | courier econ (infer) |

## Catalog (INCA & Menu Maker) / SKU

Catalog canonical logic: **`/r/vNN0N6raL`** (Canonical GB). Coverage tables:
`grdw.agg_gr_inca_catalog_metric_snapshot`, `grdw.agg_gr_inca_store_available_item_snapshot`.

| Query (link) | Metric(s) | Grain | Params | Calc (short) | Likely table(s) |
|---|---|---|---|---|---|
| Menu items info (INCA & MM) `/r/CnMJupmuX` | — (attributes) | item | platform, merchant, gtin, item name | catalog listing | `mops_dash_catalog_v2` (infer) |
| INCA item attributes `/r/aYExS58P7`; merchant-item variant `/r/htnGx6bM5` | Product/GTIN/Price/Section/UPT | item | store_uuid / parent chain | catalog attrs | catalog (infer) |
| # SKU / New SKU / Photo Coverage (monthly) `/r/oMAYUS65B` | # SKU, # New SKU | parent chain | start/end, onboarding_status, merchant_name | Photo Coverage = Products w/ Photo / Products | `agg_gr_inca_catalog_metric_snapshot` (defn) |
| [Store] # SKU / # Purchasable SKU `/r/rq5uM7RLl` | # SKU | store | merchant_name | % Purchasable = Purchasable / Items | `agg_gr_inca_store_available_item_snapshot` (defn) |
| # Section & Subsections `/r/B9U3vLwgf` | # Sections | parent chain | — | count | catalog (infer) |
| Unique Modifier Groups `/r/GX71RfYeb` | Modifier Group | chain × item | merchant_name | distinct modifier groups | catalog (infer) |
| Unavailable Items — Modifier Suspension `/r/JCfoexgNN` | — (list) | store-item-modifier | — | suspended modifiers | catalog (infer) |
| External IDs + OOS Suspension status `/r/nkGC2shBZ` | — | store × item | store_uuid | current suspension | catalog (infer) |
| Items w/ Suspension by snapshot date `/r/7ESVk3zH9` | — | store × item | merchant_name, date | suspension @ date | catalog snapshot (infer) |
| Catalog/Section/Product/Item UUID lookup `/r/slbr3A76v` | — | catalog × item | catalog_uuid, section_name | id resolution | catalog (infer) |
| GTIN/Photo/Desc/UPT & % Purchasable `/r/xdD50AvfZ` | Coverage %, % Purchasable | daily × store | — | coverage ratios | `agg_gr_inca_catalog_metric_snapshot` (defn) |
| JPGR Item Lookup by GTIN `/r/72Fsjrq4b` | — | item | merchant, section, upt, item name | GTIN lookup | catalog (infer) |
| UPT List `/r/nxU7HJhth` | UPT | — | — | all UPT | catalog (infer) |
| Catalog Change Log INCA `/r/Ivt592gMH`; MM `/r/9Y4v26omt` | — (log) | change | — | change history | catalog log (infer) |
| % INCA GB & % Canonical GB `/r/vef83evl1` | % INCA GB, % Canonical GB | daily × store | — | Canonical GB / GB | `/r/vNN0N6raL` logic; kirby (defn) |
| INCA Stores & Transition Date `/r/4VskChTPd` | — | store | — | INCA transition | catalog (infer) |
| brand-level UPT & # products `/r/6wc5NQm2X` | UPT, # Products | brand | — | UPT Coverage = w/UPT / Products | `agg_gr_inca_catalog_metric_snapshot` (infer) |

## Store Information

Default JP Retail scope: `grdw.dim_storefront` ⨝ `kirby_external_data.gr_jp_ssot_merchant_information`.

| Query (link) | Returns | Grain | Params | Likely table(s) |
|---|---|---|---|---|
| Store Info + Last Month GB `/r/acPKEAF6p` | store attrs + GB | store | — | dim_storefront + tracker (infer) |
| Onboarding & Visibility Status `/r/9dj7hPisf` | onboarding/visibility | store | — | dim_storefront + SSOT (infer) |
| Stores Not Visible `/r/pRs6Ootp5` | not-visible list | store | merchant segment | storefront (infer) |
| Stores w/ No Sales in 3M `/r/Be31K3vJt` | store list | store | — | tracker + storefront (infer) |
| New Locations `/r/hhkjYSXVd` | new stores | store | start/end | dim_storefront (infer) |
| Store Open & Close Time `/r/81xvcHMmj` | hours | store | — | `rs`/storefront (infer) |
| Catalog/Section UUID + Menu Hours `/r/jOBlocCzf`; +section filter `/r/FwB23qET1`; subsection `/r/pOxdysVdZ` | menu hours | store × section | merchant_uuid, section_name | catalog (infer) |
| Stores by parent chain name `/r/mWVTvJEjn` / uuid `/r/APexoPOpx` | store list | store | parent chain name/uuid | dim_storefront + SSOT (infer) |
| Store External ID Search `/r/nD62eEN3h` | external IDs | store | merchant_uuid, store_uuid | dim_storefront (infer) |
| List of JPGR Merchants + Subsidiary + Top GB Store `/r/pyVukhXIv` | merchant list | merchant | — | `gr_jp_ssot_merchant_information` (SSOT) |
| POS-integrated merchants/locations `/r/3fumKK3DJ` | POS list | store | — | SSOT/storefront (infer) |
| JPGR Category & Searchable Tag `/r/n7Svs54DB` | category, tag | store | — | catalog/SSOT (infer) |
| Store Hour Change Log `/r/sey1bw8f9` | change log | change | start/end, catalog_uuid | catalog log (infer) |
| UEO/UEM user email & role `/r/yOombdsHt`, `/r/mxF4JYNkr`, `/r/s9TycSC1p` | user email/role | store/user | merchant_name / email | user/access (infer) |

## Eater / Growth Analytics

| Query (link) | Metric(s) | Grain | Params | Calc (short) | Likely table(s) |
|---|---|---|---|---|---|
| Distribution of Eaters by Trip Rank `/r/bGIHJXlBh` | Eaters | parent chain | start/end, merchant_name | Nth-order distribution | eater/order (infer) |
| User churn / moved merchants `/r/wQzrYM5cb` | churn | parent chain | — | churn counts | eater (infer) |
| Store-level retention rate `/r/s87EVzKml` | Retention (14D/1M/2M/3M) | store | — | Retained / Active | eater (infer) |
| Category sales by cohort `/r/1AS0IdQO5` | cohort sales | store × section | — | retained vs one-time | eater + tracker (infer) |
| Conversion rates by user segments `/r/HhojUOIyn` | conversion | user segment | — | conv by segment | funnel (infer) |
| User segment @ merchant `/r/logudgZkj` | segment mix | merchant | — | segment share | funnel (infer) |
| Eater `/r/E7tc5lzBR` | eater base | eater | — | base metrics | eater (infer) |
| Eater retention `/r/u3qB9BkiH` | retention | eater | — | Retained / Active | eater (infer) |
| Retention `/r/AjGqWsF6T` | retention | — | month/country | 28D fwd/bwd | eater (infer) |
| LTV `/r/44iZ8gV7d` | LTV | eater | — | lifetime value | eater (infer) |
| Uber One Members `/r/oS9b2yKuj` | Uber One base | member | — | membership | subsc (infer) |
| Sessions `/r/ck9GpWtX1` | sessions | session | — | app/web sessions | sessions (infer) |
| SoV and Funnel `/r/zVX23Vm11` | SoV, funnel | surface | — | impression share + funnel | discovery (infer) |
| Growth Ops set: FTGR `/r/34NyPba95`; Retention 28D global/JP `/r/k8wjlK8IV`,`/r/24aB6imBF`,`/r/IqTl5KuaD`; Global GR Cohort `/r/ljV7UvI2L`; 28D fwd JP by Cohort `/r/zJO0lwBTZ` | FTGR, Retention, Cohort | month/country/cohort | month, country, cohort | see domain_patterns | eater (infer) |

## Search / Impressions / Basket / Marketplace

Discovery canonical: **`/r/h42aTbqVR`** (table `eats_japan.mops_dash_search`).

| Query (link) | Metric(s) | Grain | Params | Calc (short) | Likely table(s) |
|---|---|---|---|---|---|
| Times Searched / ATC / Zero-Result `/r/8vRJkTtQ3` | # Searched, Search-to-ATC | search query | start/end, time_granularity | ATC / Searches; Zero-Result / Searches | `mops_dash_search` / `mops_dash_discovery` (defn/SSOT) |
| Search term by geo/merchant `/r/fpGOVLZ43` | # Searched, Search-to-ATC | chain/country/vertical/store × term | start/end, merchant_or_store_level, country_or_vertical_or_merchant | as above | discovery (infer) |
| Item Impressions / ATC Rate `/r/6MgbjCYX` | ATC Rate | item | start/end, time_granularity | ATC Impr / Impr | discovery (infer) |
| Menu Impressions `/r/fnpQMR3lB` | Menu Impressions | store/merchant × hour | merchant_name, merchant_or_store_level, time_granularity, start/end | # menu impressions | discovery (infer) |
| Section ATC Rate `/r/yHV31ZtC3` | ATC Rate | parent chain × section | start/end, merchant_name, time_granularity | ATC / impr | discovery (infer) |
| Items Bought Together `/r/BIH6AmrB`; Sections `/r/FdpnriyUP`; ATC Order Dist `/r/8fsxhvEGv` | basket assoc | parent chain / item / section | start/end, merchant_name | co-occurrence | order (infer) |
| # Units in Basket Distribution `/r/iTPD9BTw7` | basket size dist | merchant | — | units/order dist | order (infer) |
| # Orders with Multiple DPs `/r/37dmaR2ev` | # DP/Order | parent chain | start/end, merchant_name | multi-DP orders | order (infer) |
| Nearby Stores from coordinates `/r/gCgoMpgj9` | store list | coordinate | — | geo radius | `jp_hex_geo_v4` (infer) |
| Competitors within Delivery Radius `/r/BpkElkKUL` | competitor list | store | — | geo radius | geo (infer) |
| Offer Performance by Parent Chain `/r/5cba8Djqd` | offer perf | parent chain | start/end, parent_chain_uuid | promo perf | `retail_snp_tracker_daily_promo_ads` (infer) |
| Intentful sessions `/r/6fYWELm5J` | intentful sessions | session | — | intent sessions | sessions/discovery (infer) |

## Market Sizing / S&P

| Query (link) | Metric(s) | Grain | Likely table(s) |
|---|---|---|---|
| Trips by hex `/r/oPBK8W7sn` | trips | hex | trips + `jp_hex_geo_v4` (infer) |
| Area coverage by % `/r/nYxMpf92z` | coverage % | area/hex | geo (infer) |
| Japan geofences `/r/8eBNQ6b9n` | geofences | hex | `jp_hex_geo_v4` (defn) |
| SAM `/r/vdiTW6cUR` | SAM | market | market-sizing (infer) |
| MAU by coverage `/r/pTs3none3` | MAU | coverage | eater + geo (infer) |
| Price Inflation YoY `/r/6uRsSHstt`, `/r/tvZKY6moX` | YoY inflation | item/category | `menu_snapshot_summary` (infer) |

## Promo & Ads

| Query (link) | Metric(s) | Grain | Calc (short) | Likely table(s) |
|---|---|---|---|---|
| Promo Spend (tax incl.) `/r/koqiwLiA7` | Promo Spend | — | spend incl. tax | `retail_snp_tracker_daily_promo_ads` (infer) |
| ads finance data `/r/ny5ZDygsd` | ads finance | — | ad revenue/spend | promo_ads (infer) |
| Ads Perf by House vs Merchant-Funded `/r/BTeG05zIP` | ads perf | ad type | Ads ROI = Revenue/Spend | promo_ads (infer) |

## Other / Lookups (no metric math)

| Query (link) | Returns | Params | Likely table(s) |
|---|---|---|---|
| User lookup by email `/r/J9SXS70Of` / by uuid `/r/CYiNUugMh` | user identity | email / user_uuid | user/identity (infer) |
| List of order IDs `/r/HXYLnHF9n` | order IDs | order | order (infer) |
| Courier fare by workflow uuid `/r/wgj9ZFZ0X` | courier fare | workflow | trips (infer) |
| Consumer feedback / comments `/r/E3ZpNTJhJ` | feedback | start/end | commops (infer) |
| Country DR comparison `/r/fc6bKnZxN` | DR / Courier/Eater/Merchant DR | month/country | Defect Rate variants | commops (infer) |
| Payout Calculator (approx) `/r/kZBQp3679` | Payout | start/end, store_uuid | approximate | finance (infer) |

---

## To upgrade any row to exact tables/filters

Open the QueryBuilder link and read its SQL (FROM/JOINs/WHERE), or paste the SQL here
and I'll replace the inferred table(s) and add exact filters + metric expressions.
For finance rows, confirm aggregation is on `accounting_date` (not operational day).
