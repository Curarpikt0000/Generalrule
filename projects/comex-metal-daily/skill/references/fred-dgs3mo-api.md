# FRED DGS3MO (3M T-Bill Rate) — API Reference

> 添加于 2026-07-01，替代之前的硬编码 0.05 占位符

## API 调用

```
GET https://api.stlouisfed.org/fred/series/observations?series_id=DGS3MO&api_key={KEY}&file_type=json&sort_order=desc&limit=3
```

- **API Key**: `2bfd34...3d9b` (存储在 cron prompt 和用户记忆中)
- **系列**: DGS3MO (3-Month Treasury Bill: Secondary Market Rate)
- **参数**: `file_type=json` 强制 JSON 而非默认 HTML；`sort_order=desc&limit=3` 拿到最新 3 个观测值

## Python 示例

```python
import requests
url = f"https://api.stlouisfed.org/fred/series/observations?series_id=DGS3MO&api_key={KEY}&file_type=json&sort_order=desc&limit=3"
r = requests.get(url, headers={"User-Agent": "curl/7.88"}, timeout=15)
data = r.json()
# 取第一个非 '.' 的值（'.' = 数据缺失/非交易日）
for obs in data.get("observations", []):
    if obs["value"] != ".":
        r_val = float(obs["value"]) / 100  # FRED 返回百分比值
        r_date = obs["date"]
        break
```

## 返回值示例

```json
{
  "observations": [
    {"date": "2026-06-29", "value": "3.87"},
    {"date": "2026-06-26", "value": "3.83"},
    {"date": "2026-06-25", "value": "3.84"}
  ]
}
```

最新值 (2026-06-29) = **3.87% → 0.0387 用于 SIFO 公式**

## 注意事项

- **FRED 返回百分比值** (如 3.87)，用于 SIFO 公式时要除以 100 转为小数 (0.0387)
- 非交易日返回 `"."` 作为 value，需要跳过
- 不需要复杂的 auth — API key 直接作为 query parameter
- **不要用 FRED HTML 页面抓取** — 之前 context-log 反复记录"FRED 返回 HTML"就是因为用了 `requests.get` 不加 `file_type=json`
- 之前 context-log 6/25→6/29 反复记录"FRED DGS3MO 应实现真实 API 调用替代硬编码 0.05"，原因就是只有描述没有具体调用代码。**本文件的存在就是为了防止同一个问题继续留存。**
