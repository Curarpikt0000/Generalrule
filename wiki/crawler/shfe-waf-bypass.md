---
title: SHFE 数据爬取 — WAF 绕过与 Playwright 方案
domain: crawler
keywords: [shfe, waf, playwright, stealth, datacenter-ip, residential-ip, js-challenge]
source: hermes-crawler-lesson-20260620
created: 2026-06-20
last_updated: 2026-06-20
---

# SHFE 数据爬取 — WAF 绕过方案

> 目标：抓取上海期货交易所（SHFE）库存周报数据（黄金 + 白银），写入 Notion。
> 需每周六定时执行。WAF 为长亭 SafeLine（JS challenge 模式），对 datacenter IP 严苛。

## 方案演进（按尝试顺序）

### ❌ 方案 1：curl / requests 直连

```
curl https://www.shfe.com.cn/data/tradedata/future/weeklydata/{date}weeklystock.dat
```

返回 `<!DOCTYPE html>` — WAF JS challenge 页面。需要浏览器执行 PoW SHA-1 哈希计算 + cookie 设置才能放行。纯 HTTP 请求无法跳过。

### ❌ 方案 2：akshare 库

```python
ak.futures_shfe_warehouse_receipt(date='20260619')
```

akshare 内部也是 requests 直连 `www.shfe.com.cn/data/tradedata/future/dailydata/{date}dailystock.dat`，同样被 WAF 拦截。已在 2026-05 验证失败。

金十数据接口 `ak.futures_stock_shfe_js()` 底层走 `datacenter-api.jin10.com`，但该接口 2026-06 起返回空数据（已废弃）。

### ❌ 方案 3：Gemini computer_use（操控本地 Chrome）

```
cron job model: gemini-2.5-flash
工具：computer_use → 操控用户本地 Chrome → 访问 SHFE 页面
```

理论上利用本地 Mac IP（residential）＋ 真实 Chrome 指纹过 WAF。

**失败原因：**
- computer_use 在后台 cron 环境无法正确 capture Chrome 窗口（所有 AX 元素 bounds = [0,0,0,0]）
- Chrome 可能在另一 Space 或 accessibility permissions 不足
- cua-driver 对后台窗口捕获不稳定

### ❌ 方案 4：Hermes 内置 browser 工具（browser_navigate）

browser 工具使用 Browserbase 的 datacenter IP，SHFE WAF 直接拦截（返回 WAF 页面）。

### ✅ 方案 5：Playwright stealth（最终方案）

```python
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
context = await browser.new_context(
    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ... Chrome/120.0.0.0 Safari/537.36',
    locale='zh-CN'
)
page = await context.new_page()
stealth = Stealth()
await stealth.apply_stealth_async(page)
await page.goto('https://www.shfe.com.cn/...')
```

**关键成功因素：**
1. `playwright-stealth` 库（pip install playwright-stealth）提供了完整的反检测指纹伪装
2. 非 headless 模式偶尔成功，但 headless + stealth 更稳定
3. WAF 有频率限制——短时间内多次请求同一 IP 会被标记。需要间隔或 new context
4. 首次加载后等待 3-5s 等 JS challenge 完成

**已验证数据路径（2026-06-20）：**
- SHFE 库存周报 URL：`https://www.shfe.com.cn/reports/tradedata/dailyandweeklydata/`
- 点击 tab `#weeklystock` 后，数据渲染在 `#daily_stock_html` div 内
- 数据以 HTML table 格式嵌入，不含额外 API 请求
- 黄金表是汇总行（3 列：上周库存/本周库存/增减）
- 白银表是明细行 + 总计行（需解析）

## 数据解析要点

### 黄金（Table 21）

```html
<tr><td>110673</td><td>111669</td><td>996</td></tr>
```
黄金没有按地区的明细，只有全国总计行。单位：千克，需 /1000 转为吨。

### 白银（Table 22）

```html
<tr><td>地区</td><td>仓库</td><td>上周期货</td><td>本周期货</td><td>增减</td><td>可用库容量...</td></tr>
<tr><td>上海</td><td>中储吴淞</td><td>75924</td><td>79211</td><td>3287</td><td>...</td></tr>
<tr><td>总计</td><td>898147</td><td>986791</td><td>88644</td><td>...</td></tr>
```
取“总计”行的第 2、3 列（本周期货/上周期货）。单位：千克。

## Cron Job 架构（最终）

```
cron (每周六 09:00 JST)
  └→ no_agent=True (pure script mode, no LLM)
       └→ shfe_weekly_notion_wrapper.sh (load NOTION_API_KEY)
            └→ shfe_weekly_notion.py (orchestrate)
                 └→ shfe_weekly_stock.py (playwright stealth → parse → return JSON)
```

**关键设计决策：**
- `no_agent=True`：跳过 LLM，直接跑 Python 脚本，0 token 消耗
- wrapper 脚本加载 `NOTION_API_KEY` 环境变量后 exec Python
- upsert 逻辑：按 Name 查询 → 存在 PATCH / 不存在 POST

## 踩坑记录

| # | 问题 | 说明 |
|---|------|------|
| 1 | WAF JS challenge 需完整浏览器环境 | 纯 HTTP 库（curl/requests）无法绕过，需 Playwright 等完整浏览器 |
| 2 | Datacenter IP 全拦 | 即使 Playwright headless，datacenter IP 也被拦。stealth 指纹虽有用但非充分 |
| 3 | computer_use 后台不稳定 | 无 GUI 环境的 cron 不可用。仅适合用户在场交互式使用 |
| 4 | SHFE 数据路径非标准 | 库存周报数据不以 JSON/API 加载，而是 Vue 组件直接渲染 HTML 表格 |
| 5 | 频率限制 | 同一 IP 短时间多次请求 SHFE 会被 WAF 标记，需间隔 30s+ |

## 参考文件

- `~/.hermes/scripts/shfe_weekly_stock.py` — 抓取核心
- `~/.hermes/scripts/shfe_weekly_notion.py` — 写入 Notion
- `~/.hermes/scripts/shfe_weekly_notion_wrapper.sh` — cron wrapper
