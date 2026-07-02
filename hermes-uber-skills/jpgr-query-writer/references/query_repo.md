# JPGR Query Repo (Canonical Catalog)

Source of truth: the team's "Query Repo" Google Sheet
(`https://docs.google.com/spreadsheets/d/1nULm0eDPylzTvDSjcUrL-WGp2ADCKn2lrvZbaib5Pu8`).
Companion sheets:
- KPI dashboard: `https://docs.google.com/spreadsheets/d/1IW_1FlGBzvTGzUI5o2qnARIC0itkfywWHITdYXHrhuI`
  (Daily/Weekly/Monthly GB, Trips, ABS breakdowns by vertical / cohort / Uber One / promo).
- **Metrics Definitions** (JPGR Merchant Ops Dashboard):
  `https://docs.google.com/spreadsheets/d/1w3tsFe01Rbny1GGSNi2sO4-LJKSv2t9jNbwFe8znmuo`
  — authoritative calculation logic + source tables; distilled into `domain_patterns.md`.

**Match a user request to a row below first.** Each entry lists the metric(s), the
grain, the standard user inputs, and the QueryBuilder link. Adapt parameters
rather than rewriting SQL. Prefer the most recently updated matching query. Links
ending in `-ea`, `-v1`, `-v2` are older QueryBuilder hosts; the same query often
exists on the current `querybuilder.uberinternal.com` host.

If this catalog drifts, re-fetch the sheet with
`usearchbackend_getdocuments` (via omni-mcp / usearch-backend) using its URL.

## Standard user inputs (used across most queries)

| Input | What it does | Values |
|---|---|---|
| `start_date` / `end_date` | Time-range filter | `'YYYY-MM-DD'` |
| `time_granularity` | Aggregation level | `month`, `week`, `day` |
| `onboarding_status` | Filter stores by status | `activated`, `lead`, `onboarding`, `on hold` |
| `merchant_name` | Filter merchant(s) by official name | merchant name |
| `merchant_or_store_level` | Aggregate at chain vs store | `merchant`, `store` |
| `merchant_names_empty_ok` | Filter by merchant, `''` = all | merchant name or `''` |
| `store_uuid` / `merchant_uuid` / `catalog_uuid` / `GTIN` | Entity lookups | UUID / GTIN |

## Sales

- **[Store Level] GB** — GB by store. Inputs: start_date, end_date, time_granularity. `/r/x5Pv7jAzN`
- **[Merchant or Store & Item-Level] Sales and Quantity Sold** — Item Sales, Quantity Sold. Inputs: start_date, end_date, merchant_name, time_granularity, merchant_or_store_level. `/r/6qHel0y2P`
- **[Merchant or Store & Item-Level] Sales & Quantity Sold | Section | Subsection** — `/r/plH8Atl87`
- **[Merchant or Store & Item Level] Sales | Quantity | Price | Section (lookup by GTIN)** — Avg Selling Price, Quantity Sold, Item Sales. Inputs incl. GTIN. `/r/6vkKuP2NZ`
- **[GTIN Level] JPGR Sales Across All Merchants** — Item Sales, Quantity Sold by GTIN. Inputs: time_granularity, start_date, end_date. `/r/iu3L4roQV`
- **[Merchant or Store & Item Name Level] Sales | Quantity | Sales Loss from OOS | Avg Selling Price | Found Rate | Fulfillment Rate** — the "everything" item query. `/r/F6F5gzD8f`
- **[Merchant or Store & Section Level] Sales | Quantity Sold** — `/r/1HPUW6769`
- **[Vertical & Item-Level] Sales and Quantity Sold | Section | Subsection** — `/r/iT1PzCxZt`
- **[Merchant or Store & Hour & Section Level] Food Sales** — Inputs: start_date, end_date, merchant_name. `/r/do4eobq27`
- **[Country/City/Vertical Level] TpR | Total Food Sales | Food Sales per Store by Store Tenure** — `/r/tQs9TfxDZ`
- **[Country/Vertical/Merchant/Store Level] Avg Hourly Orders Requested/Completed | Food Sales | GB** — `/r/mc3hYRAV5`
- **[Store & UPT Level] Orders Penetrated | Quantity Sold | Food Sales** — `/r/6VIsxTbLl`
- **[Item Level] Sales | Quantity Fulfilled (by Store & Section)** — `/r/ITgct75i3`
- **[Store & Order & Item Level] Order ID | Items Fulfilled | Quantity Fulfilled | Final Food Sales** — `/r/FjRlHgSPp`
- **[Merchant Level] GB from Past X Months with Percentile** — Inputs: start_date, num_months. `/r/zJeQpIk83`
- **[ABS bucket of choice] ABS Distribution** — Inputs: start_date, end_date, merchant_name. `/r/27UWUzeAj`

## Operational Performance (fulfillment / OOS / cancellations / online rate)

- **[Store Level] Requested Orders | Completed Trips | OOI | Defects | C/R** — `/r/47Wdgy5uz` (OOI Report)
- **[Item Level] List of Out of Stock Items | Replacement Item** — `/r/IZFvZnNyj`
- **[Item Level] List of Out of Stock Items | Sales Loss from OOS** — `/r/aU6RSDdAn`
- **[Store-Level] GB Loss from Unfulfillment** — `/r/5y69VgKof`
- **[Store-Level] % OOI Trips** — `/r/I1BOWuy6z`
- **[Merchant or Store & Item Level] Qty Requested | Qty Found | Found Rate | Times Replaced | Times OOS | Replacement Rate** — `/r/3BloHMSNN`
- **[UPT L2 Level] Sales Loss from OOS | Times Requested | Found Rate | Fulfillment Rate | Replacement Rate** — `/r/IFCEFanVJ`. Found Rate = Item FR / Times Requested; Fulfillment Rate = Item FFR / Times Requested; Replacement Rate = Times to be Replaced / Times Replaced.
- **[UPT Level of choice] Fulfillment Rate | Found Rate | Replacement Rate** — `/r/jnaJs41tl`
- **[Country or Merchant & GTIN Level] Found Rate | Times Requested | Sales Loss From OOS | UPT | Section** — `/r/z9reUu1PZ`
- **[Merchant Level] Replacement Rate by Eater's Fulfillment Method Preference** — `/r/6rPi5lMV5`
- **[Store Level] Daily Online Rate** — `/r/jUfg6cTS7` (Weekly Online Reports)
- **[Merchant or Store Level] Hourly Online Rate | Minutes Store Was Busy Mode** — `/r/3R5fzgdSv`
- **[Month-Store Level] Acceptance Rate and GB** — `/r/rR5SCPftR` ; **[Month-Merchant Level]** — `/r/t9CFRobx1`
- **[Order Level] Cancel Source | Cancel Reason** — `/r/mhXYc50z5` (Weekly Cancel Reports)
- **[Merchant & Order Level] List of Cancelled Orders (from cancel source of choice)** — `/r/r7eGiiNR9`
- **[Merchant or Store Level] # Cancellations | Sales Loss by Cancellation Reason** — `/r/jEogUkrGv` ; all-merchants variant `/r/5pAMzZLUn`
- **[Defect & Bliss Level] List of Defects | Defect Type | Ticket Content** — `/r/dLswjDww3`
- **[Country/Vertical/Merchant/Store Level] JPGR MOps OKR 2025 H1 (with fulfillment-type filter)** — `/r/l2cxQLr3d`

## Catalog (INCA & Menu Maker) / SKU

- **List of menu items and information (INCA and MM)** — Inputs: platform, merchant, gtin, item name. `/r/CnMJupmuX`
- **[Item UUID Level] Product UUID, GTIN, Item Name, Price, Section, UPT of INCA items** — `/r/aYExS58P7`; merchant-item-name variant `/r/htnGx6bM5`
- **[Merchant Level] # SKU | # New SKU | Photo Coverage (first day of each month)** — `/r/oMAYUS65B`
- **[Store-Level] # SKU in Catalog | # Purchasable SKU** — `/r/rq5uM7RLl`
- **[Merchant Level] # of Section and Subsections** — `/r/B9U3vLwgf`
- **[Merchant & Item Level] List of Unique Modifier Groups** — `/r/GX71RfYeb`
- **[Store-Item-Modifier Option Level] Unavailable Items due to Modifier Option Suspension** — `/r/JCfoexgNN`
- **[Store & Item Level] External Store ID | External Product ID | Item UUID | Current OOS (Suspension) Status** — `/r/nkGC2shBZ`
- **[Store & Item Level] List of Items with Suspension (by snapshot date)** — Inputs: merchant_name, date. `/r/7ESVk3zH9`
- **[Catalog UUID & Item UUID] Catalog | Section | Product | Item UUID (by catalog_uuid & section_name)** — `/r/slbr3A76v`
- **GTIN, Photo, Description, UPT Coverage & % Purchasable Items** — `/r/xdD50AvfZ` (MOps OKR Dashboard)
- **JPGR Item Look Up Based on GTIN** — `/r/72Fsjrq4b`
- **UPT List (all UPT)** — `/r/nxU7HJhth`
- **Catalog Change History Log for INCA** — `/r/Ivt592gMH` ; **Menu Change History Log for Menu Maker** — `/r/9Y4v26omt`
- **% INCA GB & % Canonical GB** — `/r/vef83evl1` (MOps OKR Dashboard)
- **JPGR INCA Stores and INCA Transition Date** — `/r/4VskChTPd`

## Store Information

- **[Store Level] Store Information and Last Month GB** — `/r/acPKEAF6p` (feeds "JPGR Store List", updated 6am daily)
- **[Store-level] Onboarding and Visibility Status** — `/r/9dj7hPisf`
- **[Store Level] Stores Not Visible** — Input: merchant segment. `/r/pRs6Ootp5`
- **[Store-level] Stores with No Sales in Past 3 Months** — `/r/Be31K3vJt`
- **[Store Level] New Locations** — Inputs: start_date, end_date. `/r/hhkjYSXVd`
- **[Store Level] Store Open & Close Time** — `/r/81xvcHMmj`
- **[Store & Section Level] Catalog UUID | Section UUID | Section Name | Current Menu Hours** — `/r/jOBlocCzf`; with section-name filter `/r/FwB23qET1`; subsection variant `/r/pOxdysVdZ`
- **Stores by parent chain name** — `/r/mWVTvJEjn`; **by parent chain uuid** — `/r/APexoPOpx`
- **Store External ID Search** — Inputs: merchant_uuid, store_uuid. `/r/nD62eEN3h`
- **[Merchant-Level] List of JPGR Merchants | Subsidiary Group | Link to Top GB Store** — `/r/pyVukhXIv`
- **List of POS-integrated merchants/locations** — `/r/3fumKK3DJ`
- **JPGR Category and Searchable Tag** — `/r/n7Svs54DB`
- **[Change Log] Catalog Manager Store Hour Change Log** — Inputs: start_date, end_date, catalog_uuid. `/r/sey1bw8f9`
- **[UEO User] Store | UEO User Email** — `/r/yOombdsHt`; **JPGR UEM User Email and Role** — `/r/mxF4JYNkr`; **email search by keyword** — `/r/s9TycSC1p`

## Eater Metrics / Retention / Cohort

- **[Merchant Level] Distribution of Eaters by Trip Rank (N-th Order)** — `/r/bGIHJXlBh`
- **[Merchant Level] User churn / users who churned or moved to other merchants** — `/r/wQzrYM5cb`
- **Store-level retention rate** (14D / 1M / 2M / 3M return) — `/r/s87EVzKml`
- **[Store-section level] Category sales by customer cohort (retained vs one-time)** — `/r/1AS0IdQO5`
- Growth Ops set (separate tab): FTGR `/r/34NyPba95`; Retention 28D backward global `/r/k8wjlK8IV`; 28D forward global `/r/24aB6imBF`; 28D forward JP `/r/IqTl5KuaD`; Global GR Cohort `/r/ljV7UvI2L`; 28D forward JP by Cohort `/r/zJO0lwBTZ`.

## Search / Impressions / Basket / Marketplace / Promo

- **[Search Query Level] Times Searched in Japan | Add to Cart Rate | Zero Results Rate** — `/r/8vRJkTtQ3`
- **[Country/Vertical/Merchant/Store & Search Term] Times Searched | Searches without Results | Search to Cart** — `/r/fpGOVLZ43`
- **[Merchant & Item Level] Item Impressions | Add-to-Cart Rate** — `/r/6MgbjCYX`
- **[Merchant or Store & Hour Level] Menu Impressions** — `/r/fnpQMR3lB`
- **[Merchant & Section Level] Section Add to Cart Rate** — `/r/yHV31ZtC3`
- **[Merchant Level] Items Bought Together** — `/r/BIH6AmrB`; **Sections Bought Together** — `/r/FdpnriyUP`; **Add to Cart Order Distribution** — `/r/8fsxhvEGv`
- **JPGR # of Units in Basket Distribution** — `/r/iTPD9BTw7`
- **[Merchant Level] # of Orders with Multiple DPs** — `/r/37dmaR2ev`
- **[Coordinate Level] Nearby Stores from Point A (by coordinates)** — `/r/gCgoMpgj9`
- **Competitors within the Delivery Radius** — `/r/BpkElkKUL`
- **Offer Performance by Parent Chain** — Inputs: start_date, end_date, parent chain uuid. `/r/5cba8Djqd`

## Other / Lookups

- **User (internal/eater/driver/rider) lookup by email** — `/r/J9SXS70Of`; **by user_uuid** — `/r/CYiNUugMh`
- **List of order IDs** — `/r/HXYLnHF9n`; **[workflow uuid] courier fare lookup** — `/r/wgj9ZFZ0X`
- **Consumer feedback / customer comments** — Inputs: start_date, end_date. `/r/E3ZpNTJhJ`
- **Country comparison of DR / Courier DR / Eater DR / Merchant DR** — `/r/fc6bKnZxN`
- **JPGR | Payout Calculator (approximate)** — Inputs: start_date, end_date, store_uuid. `/r/kZBQp3679`

## Market Sizing / S&P (geo, coverage, inflation)

- **Trips by hex** — trips aggregated to hex geo. `/r/oPBK8W7sn`
- **Area coverage by %** — coverage of area by %. `/r/nYxMpf92z`
- **Japan geofences** — JP geofence definitions (alt table: `kirby_external_data.jp_hex_geo_v4`). `/r/8eBNQ6b9n`
- **SAM** — Serviceable Addressable Market. `/r/vdiTW6cUR`
- **MAU by coverage** — Monthly Active Users by coverage. `/r/pTs3none3`
- **Intentful sessions** — sessions showing purchase intent. `/r/6fYWELm5J`
- **Price Inflation YoY** — year-over-year price inflation. `/r/6uRsSHstt` and variant `/r/tvZKY6moX`

## Growth / Eater Analytics (segments, retention, LTV, sessions, subscription)

- **Conversion rates by user segments** — conversion by user segment. `/r/HhojUOIyn`
- **User segment @ merchant** — user-segment mix at a merchant. `/r/logudgZkj`
- **Eater** — eater base metrics. `/r/E7tc5lzBR`
- **Eater retention** — `/r/u3qB9BkiH` (see also global/JP retention set in the Eater Metrics section)
- **Retention** — retention analysis. `/r/AjGqWsF6T`
- **LTV** — eater lifetime value. `/r/44iZ8gV7d`
- **Uber One Members** — Uber One membership base/metrics. `/r/oS9b2yKuj`
- **Sessions** — app/web sessions. `/r/ck9GpWtX1`
- **SoV and Funnel** — Share of Voice and conversion funnel. `/r/zVX23Vm11`

## Catalog / Sales by taxonomy (UPT / brand / category)

- **sales by UPT/brand/category** — sales broken down by UPT, brand, category. `/r/8jHNdXSPd`
- **brand level UPT & number of products** — UPT + product counts at brand level. `/r/6wc5NQm2X`

## Promo & Ads

- **Promo Spend (tax included)** — promo spend inclusive of tax. `/r/koqiwLiA7`
- **ads finance data** — ads finance figures. `/r/ny5ZDygsd` (`-ea` host)
- **Ads Performance by House Ads and Merchant Funded** — ads performance split by house vs merchant-funded. `/r/BTeG05zIP`

## Courier / Delivery Economics

- **Online Courier MPP** — online couriers, Merchant Pickup Point (MPP) model. `/r/uYSYo4YtF`
- **Online Courier CPP** — online couriers, Consolidated Pickup Point (CPP) model. `/r/ECI4b67RJ`
- **Dampening** — courier supply/pay dampening. `/r/yTdP5UoTt`
- **Delivery Time Related** — delivery-time metrics. `/r/tDaeuXF0P`
- **Courier payment and Batch-discounted Hours (for EPUH calc)** — courier pay + batch-discounted hours, used to compute EPUH (Earnings Per Utilized Hour). `/r/rquvyKWo7` (`-web` host)
