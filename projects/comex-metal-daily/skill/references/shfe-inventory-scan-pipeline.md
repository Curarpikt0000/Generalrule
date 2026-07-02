# SHFE 库存周报扫描（companion pipeline for COMEX daily report）

> ⚠ **2026-06-20 更新**: 改用 Playwright stealth 方案替代旧版 REST API + cookie 方案。
> 旧版 cookies 会过期且 WAF 无法绕过。新方案见 `data-science/chinese-exchange-scraping` skill。
>
> SHFE 周库存数据流入 `comex-daily-report` 的 §0 仪表盘（东方列）和 §2 东方对照小节。
> 部署使用 Hermes cron（每周六 09:00 JST），替代旧版 macOS launchd。

## 核心文件

- Scraper 脚本: `~/hermesagent/shfe_weekly_inventory/shfe_weekly_stock.py` (Playwright stealth)
- Notion 写入: `~/hermesagent/shfe_weekly_inventory/shfe_weekly_notion.py`
- Cron wrapper: `~/.hermes/scripts/shfe_weekly_notion_wrapper.sh`
- Cron: job_id `7c5135047775`, `no_agent=True`, 每周六 09:00 JST
- 执行计划: `~/hermesagent/Comex Metal Daily Issue Report/Notion COMEX仓单日报/Hermes_周任务_SHFE库存扫描.md`

## 架构：没有独立 SHFE DB

所有市场写进同一张金属追踪表，用 `市场` select 字段区分：

```
Gold DB (2bc47eb5-fd3c-8083-966e-ecfd9f396b44)
├─ Row: 市场=CME,  Gold日期=2026-05-29, Gold Reg=...   ← CME 每日
├─ Row: 市场=SHFE, Gold日期=2026-05-22, SH库存吨=...   ← SHFE 每周（Hermes 写）
```

同理 Silver DB (2bc47eb5-fd3c-80f3-a71a-d8de149a4943) 和 Pt DB (2d647eb5-fd3c-801a-9ce5-d5db4d0b961a)。

## REST API 直抓（主方案）

### API Endpoint

```
URL: https://www.shfe.com.cn/data/tradedata/future/stockdata/weeklystock_{YYYYMMDD}/ZH/all.html?params={timestamp_ms}
```

### 必需 Headers

```
User-Agent: Mozilla/5.0 ...
Referer: https://www.shfe.com.cn/reports/tradedata/dailyandweeklydata/
X-Requested-With: XMLHttpRequest
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: same-origin
sec-ch-ua: "Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"
```

### 必需 Cookies（会过期，需更新）

```
TrsAccessMonitor=TrsAccessMonitor-{timestamp}-{random}
safeline_bot_token=AGq07wE...
sl_xxx_fig=...
```

### 数据解析

```python
tables = pd.read_html(StringIO(resp.text))
# 黄金表：形状 (2, 3)，行1是数据。注意 MultiIndex columns 需展平。
# 白银表：形状 (7, 8)，最后行是「总计 总计」。找 row_text.count("总计") >= 2 的行。
# 铂金：**不存在于 SHFE**，跳过。
```

### 404 处理

```python
if resp.status_code == 404:
    print(f"⚠ {date}: 404 Not Found (假期无数据)")
    return {}
```

## Notion 写入（databases/query）

必须用 `Notion-Version: 2022-06-28`（`2025-09-03` 对 query endpoint 返回 400）。

### Upsert 逻辑

Query (Date == friday_date, 市场 == SHFE) → 存在则 PATCH，不存在则 POST。

**Gold DB** (2bc47eb5-fd3c-8083-966e-ecfd9f396b44):
- Name: `Gold SHFE {friday_date}`
- Gold日期: friday_date (date)
- 市场: `SHFE` (select)
- 库存频率: `每周` (select)
- SH库存吨: kg/1000 (number — 单位是吨)

**Silver DB** (2bc47eb5-fd3c-80f3-a71a-d8de149a4943):
- 同上，Name=`Silver SHFE {date}`, Silver日期 property

**Pt DB** (2d647eb5-fd3c-801a-9ce5-d5db4d0b961a) — SHFE 无铂金，不可写。

## 部署：Mac launchd（不要用 Hermes cron）

```xml
<!-- ~/Library/LaunchAgents/com.chaojin.shfe-weekly.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.chaojin.shfe-weekly</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/chaojin/Antigravity Projects/Daily_GoldSilvPT-inv_Notion/sync_shfe.py</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>NOTION_TOKEN</key>
        <string>YOUR_NOTION_TOKEN</string>
    </dict>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key><integer>9</integer>
        <key>Minute</key><integer>0</integer>
        <key>Weekday</key><integer>6</integer>
    </dict>
    <key>StandardOutPath</key><string>/tmp/shfe_weekly.log</string>
    <key>StandardErrorPath</key><string>/tmp/shfe_weekly.err</string>
    <key>RunAtLoad</key><false/>
</dict>
</plist>
```

## 失败处理

| 失败 | 处置 |
|------|------|
| cookies 过期（403/401） | 通知用户重新从 Chrome copy cURL |
| 单周 404 | 跳过（假日无数据） |
| Notion API 401 | 检查 NOTION_TOKEN |
| 所有周都 404 | WAF 可能封了 IP |

## 与 daily report 的协调

- 周扫描只写 Notion 不分析，完成后退出
- daily report 只读 Notion 不写 SHFE 源
- 周扫描失败 → daily report 写「SHFE 本周数据暂缺」
