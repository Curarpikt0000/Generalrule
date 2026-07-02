# SGE Daily Report via Web Scraping

> Verified 2026-06-11: extracts Au(T+D), Ag(T+D), Pt99.95 Close prices without akshare, JavaScript, or login.

## URL
```
https://en.sge.com.cn/data/data_daily_international_new?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
```

## Method
Use `web_extract(urls=[URL])` or direct `requests.get(url, headers={'User-Agent': '...'})`.

## Table format (HTML)
The page returns an HTML table with these columns:
| Date | Contract | Open | Highest | Lowest | Close | Up/Down (yuan) | Up/Down (%) | Weighted Avg Price | Volume (Kg) | Amount (yuan) | Open Interest (Lot) | Direction | Delivery Volume (Lot) |

## Key contracts
| Symbol | Contract | Close unit | Conversion to USD/oz |
|--------|----------|-----------|---------------------|
| Au(T+D) | Gold deferred | 元/克 | `close * 31.1035 / USDCNY` |
| Ag(T+D) | Silver deferred | 元/千克 | `(close / 1000) * 31.1035 / USDCNY` |
| Pt99.95 | Platinum spot | 元/克 | `close * 31.1035 / USDCNY` |

## Verified data (2026-06-11)
- Au(T+D) Close = 895.82 元/克 → $4,111/oz at USDCNY=6.7774
- Ag(T+D) Close = 15,433 元/千克 → $70.83/oz at USDCNY=6.7774
- Pt99.95 Close = 418.64 元/克 → $1,921/oz at USDCNY=6.7774

## Note on availability
- English SGE site works via web_extract (no render blocking)
- Chinese SGE site (sge.com.cn/sjzx/mrhj) requires JavaScript — avoid
- Historical data available by changing start_date/end_date params
- Data is trade-date aligned (Chinese market closes 15:30 CST, 07:30 UTC)
