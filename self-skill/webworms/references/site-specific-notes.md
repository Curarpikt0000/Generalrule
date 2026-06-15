# Site-Specific Scraping Notes

## en.macromicro.me (MacroMicro)
- **Tier to use**: Tier 1 (requests + regex, no session needed)
- **Data embedding**: Chart data is base64-encoded JSON embedded in an inline `<script>` tag, called via `atob("BASE64...")`. Extract with `re.finditer(r'atob\("([A-Za-z0-9+/=]+)"\)', html)` → `base64.b64decode()` → `json.loads()`
- **Data format**: List of `[timestamp_ms, value]` pairs. The chart frequency varies by series (LBMA silver is monthly, not daily)
- **Limitations**:
  - Cloudflare Turnstile blocks headless browsers (Playwright/CamoFox) — plain `requests` works for initial HTML
  - `/charts/data/{series_id}` endpoint exists but returns `error #1158 #1170` without proper CSRF/auth (POST + `ignoredCharts`/`limitedCharts` body required)
  - Series data embedded in HTML is pre-rendered and may be lower frequency than the interactive chart
- **Rate limit**: Can get ~3 pages before hitting 429; `sleep(15)` between requests
- **No auth**: Public pages work without login

## armstrongeconomics.com (Martin Armstrong)
- **Tier to use**: Tier 2 (Jina Reader via `r.jina.ai`)
- **Why**: WordPress site, no aggressive WAF. Jina Reader fetches full content cleanly.
- **Available content**: Full blog posts including Market Talk, Economics, War, Precious Metals sections
- **No auth needed**: Public blog posts are freely readable. Private blog content behind $4.99/mo paywall won't be accessible.
- **Rate limit**: Standard Jina Reader limits apply. No custom rate limiting needed.

## weixin.qq.com (微信公众号)
- **Tier to use**: Browser-based (CamoFox or browser tool) for the initial page load
- **Image anti-leech**: mmbiz.qpic.cn images require Referer header. Use browser User-Agent + Referer when downloading via requests.

## fxempire.com (FX Empire)
- **Tier to use**: Browser (JS-rendered content, article pages are SPA-like)
- **Note**: Author pages (`/author/ag-thorson` etc.) and slug-only article URLs return 404 after the 2026 site redesign. Latest article URLs include numeric IDs (e.g. `-1528359` suffix). Google News RSS is the most reliable way to discover FX Empire articles.
- **Search article list**: Google News RSS `?q=site:fxempire.com+{author}+gold` works well.

## 中国人民银行 PBoC (pbc.gov.cn)
- **Tier to use**: Tier 1 (requests + BeautifulSoup, GBK encoding)
- **Encoding**: The entire site uses GBK encoding. Set `r.encoding = 'gbk'` before parsing. After conversion, Chinese characters are garbled to mojibake (e.g. "亿元" → "浜垮厓", "开展" → garbled). Numbers survive intact.
- **OMO trading announcements** (公开市场业务交易公告): List page at `/zhengcehuobisi/125207/125213/125431/125475/index.html`. Detailed pages use URL pattern `/125475/20260602xxxxxxxx/index.html`.
- **What PBoC publishes**: Only the injection amount (投放_亿) and interest rate. **Maturity amounts are NOT stated** in the daily OMO announcement — they must be inferred from 7-day-prior operations.
- **Rate format**: In table cells, rate appears as e.g. "1.40%" (decimal survives encoding). In GBK-garbled text, search for `(\d+\.\d+)\s*%`.
- **Amount extraction**: Due to mojibake, use `r"(\d+)\s*浜垮厓"` (garbled "亿元") to find injection amounts.
- **Date extraction**: Date is in `<meta name="createDate" content="2026-06-02 09:20:39">` — search raw HTML for `content="(\d{4}-\d{2}-\d{2})`.
- **Rate limit**: PBoC has no aggressive rate limiting; 2s interval is sufficient.

## 日本銀行 BoJ (boj.or.jp)
- **Tier to use**: Tier 1 (requests + openpyxl for xlsx)
- **Operations data**: The old page at `https://www3.boj.or.jp/market/en/menu_o.htm` stopped updating on 2025-10-06. New daily operations data is published as XLSX at `https://www.boj.or.jp/en/statistics/boj/fm/ope/index.htm` — files named `opeYYYYMMDD.xlsx`.
- **XLSX structure** (sheet name: "オペ"): Row 18+ contain operation details. Column A = Instrument type, column F = loan rate, column G/H = bid/successful amounts. **JGB outright purchases** are listed as a specific Instrument row; if absent, JGB buying = 0 for that day.
- **TONAR data**: Old page at `https://www3.boj.or.jp/market/en/menu_m.htm` also stopped updating. New page: `https://www.boj.or.jp/en/statistics/market/short/mutan/index.htm`. Provisional data: `mpYYYYMMDD.xlsx`, final: `mdYYYYMMDD.xlsx`. Average value in column C (index 2), label in column B (index 1).
- **Policy rate**: Not easily extractable from a single page. Known to be 0.75% (last hike). Monthly summary xlsx files at `https://www.boj.or.jp/en/statistics/boj/fm/ope/m_release/` can confirm.
- **Dependencies**: Requires `openpyxl` for xlsx parsing.
- **Rate limit**: No aggressive limits on boj.or.jp. Standard 2s interval.

## 东方财富 East Money (push2.eastmoney.com)
- **Tier to use**: Tier 1 (requests, JSON API)
- **API endpoint**: `https://push2.eastmoney.com/api/qt/clist/get`
- **Sector board query**: `fs=m:90+t:2` for industry sectors, `fs=m:90+t:3` for concept sectors.
- **Key fields**: `f12`=sector code, `f14`=sector name, `f62`=主力净流入 (yuan), `f8`=换手率 (%), `f184`=主力净占比.
- **CRITICAL**: The `diff` field in the response is a **dict with string keys** (e.g. `{"0": {...}, "1": {...}}`), NOT a list. Use `diff.values()` to iterate, NOT `for item in diff:` (which iterates over string keys).
- **Sector code drift**: Old sector codes like BK0473(电子), BK0478(有色金属), BK0451(房地产) have been deprecated from the API. Current equivalents: BK1287(工业金属), BK1037(消费电子), BK0475(银行). Always verify sector codes before reuse.
- **Headers**: Set `Referer: https://data.eastmoney.com/` or the API returns empty data. Standard `Mozilla/5.0` User-Agent works.
- **Rate limit**: Very generous. Can query every 1s.
- **No auth**: Public API, no API key needed.
