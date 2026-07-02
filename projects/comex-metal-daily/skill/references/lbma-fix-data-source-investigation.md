# LBMA Fix Data Source Investigation (2026-06-11)

## Problem
Need 2026-05-22 ~ 2026-06-10 daily LBMA fix prices (Ag AM Fix, Au PM Fix, Pt AM Fix) for SIFO §8 audit. All free public sources exhausted.

## Sources Tested & Results

### 1. Yahoo Finance spot indices (Priority 1 — User's first choice)
| Symbol | Status | Detail |
|--------|--------|--------|
| XAGUSD=X | ❌ DELISTED | 404 Not Found from Yahoo API |
| XAUUSD=X | ❌ DELISTED | 404 Not Found |
| XPTUSD=X | ❌ DELISTED | 404 Not Found |
- yfinance returns empty DataFrames with "possibly delisted" errors
- These were Yahoo's "continuous spot" indices — all discontinued

### 2. FRED API (Priority 2)
| Series | Name | Status |
|--------|------|--------|
| SLVPRUSD | Silver Fixing Price | ❌ 0 valid obs (2022-05-22~06-10) |
| GOLDPMGBD228NLBM | Gold PM Fix | ❌ 0 valid obs |
| PLATINUMFIXUSD | Platinum Fix | ❌ 0 valid obs |
- LBMA stopped publishing to FRED after ~2025-03-18
- Data before 2025-03-18 is still available via FRED
- Verification code run: `requests.get(f'https://api.stlouisfed.org/fred/series/observations?series_id={id}&api_key={key}&file_type=json')`

### 3. Investing.com (Priority 3 — Website scraping)
| URL | Status | Detail |
|-----|--------|--------|
| `/commodities/silver` | ✅ Page loads | But pairId=8836 is a CFD tracking COMEX SI=F ($62.49), NOT LBMA fix ($68.60). Gap ~10%. |
| `/commodities/silver-historical-data` | ✅ | Also SI=F data |
| Historical data API | ✅ Available | Embedded in page's `__NEXT_DATA__` script tag under `historicalDataStore`. Provides OHLCV for the CFD instrument. |
- PairId 8836 = CME Silver futures derivative (CFD), not LBMA
- Multiple other pairIds found (68, 166, 525, etc.) — none clearly LBMA spot

### 4. Kitco
| URL | Status | Detail |
|-----|--------|--------|
| kitco.com/price/precious-metals | ✅ | Shows live NY spot: Ag=$62.32 (6/10), also COMEX-linked |
| kitco.com/charts/silver | ✅ | Chart UI, HTML extraction impractical |
- "New York Spot Price" tracks COMEX, not LBMA
- "Kitco Morning Fix" box is N/A after market hours
- No free historical LBMA fix data available

### 5. LBMA official website
- `lbma.org.uk/prices-and-data/lbma-silver-price` — informational only, prices NOT rendered on page
- Historical data requires member login or paid ICE subscription
- `lppm.com` — platinum/palladium only, historical CSVs not freely downloadable
- Backend uses Next.js but __NEXT_DATA__ not included on these pages

### 6. ICE Benchmark Administration
- `theice.com/iba/precious-metals` — 404 (ICE restructured)
- LBMA price data administered by IBA, requires paid license for historical access

## Conclusion
**No free public data source provides historical LBMA fix prices for 2026.** For SIFO §8 calculations:
- Use user-provided LBMA fix values when available (authoritative)
- For cron-run daily reports: scrape `lbma.org.uk` for current-day fix (published free), cache it
- For historical audit (5/22~6/10): cannot be done without user-supplied data

## Workflow for future cron runs
1. Daily cron: scrape lbma.org.uk for today's LBMA fix (free, current-day only)
2. Archive scraped values to a local CSV: `~/hermesagent/Comex Metal Daily Issue Report/data/lbma_fix_history.csv`
3. For SIFO calc: read from local archive (yesterday+), fall back to current-day LBMA web scrape, fail loud if both unavailable
