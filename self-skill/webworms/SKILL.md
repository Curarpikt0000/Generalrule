---
name: webworms
description: "Python web scraping skill for AI agents. Use when you need to scrape websites for structured data. Supports a 4-tier fallback crawling strategy using requests/BS4, Jina Reader, CamoFox, and Crawl4AI, with built-in robots.txt compliance, rate limiting, and retry logic."
---

# webworms — 网页爬虫标准框架

## 何时使用

需要从网站批量或单页抓取结构化数据时使用本 skill。

## 4层降级回退抓取策略（第一个不行再用第二个，以此类推）

在面临网页抓取任务时，应按照以下工具链层级依次尝试，发生 WAF 封禁、超时或限流时自动回退到下一层：

| 层级 | 工具方案 | 适用场景与优缺点 |
|---|---|---|
| **第一层 (首选/最轻量)** | `requests` + `BeautifulSoup` | 适合可以直接获取源码且无反爬防护的静态页面。性能最高，资源消耗最小。 |
| **第二层 (智能单页/LLM优先)** | `Jina Reader` (`https://r.jina.ai/{url}`) | 适用于动态单页，自动执行 JS 并输出干净的 Markdown，省去 Playwright 依赖。若未授权遇到限流或 403 封锁，自动降级至第三层。 |
| **第三层 (反爬克星/沙盒定制)** | `CamoFox` + `BeautifulSoup` | 适用于高防护、有 WAF 的动态站点，或需要深度模拟用户行为（如滚动、点击）的复杂单页。提供本地指纹级防封。 |
| **第四层 (重度批量/异步并发)** | `Crawl4AI` (`AsyncWebCrawler`) | 适用于需要多并发、异步批量爬取，或全站 BFS/DFS 深度递归爬取，且需要智能 HTML 降噪清洗的场景。 |

---

## 核心架构与各工具使用规范

### 1. 第一层：BaseScraper 基础静态抓取（requests）

所有普通爬虫在编写时应当继承 `BaseScraper`，它内置了：
* **robots.txt 检查**：`self.can_fetch(url)` 自动调用
* **限速请求**：`self.get(url)` 自动进行 2s 以上的延迟限速，并支持 3 次自动重试。

```python
class MyScraper(BaseScraper):
    def fetch(self) -> list[dict]:
        # get() 方法已内置 robots.txt 检查与频率限制
        resp = self.get("https://example.com/events")
        if not resp:
            return []
        soup = BeautifulSoup(resp.text, "lxml")
        # ... 进行 DOM 解析并返回数据
```

### 2. 第二层：Jina Reader 动态 Markdown 转化

对于需要将页面快速转化为 Markdown 输入给 LLM 且不想在本地运行浏览器沙盒的场景：

```python
import requests

def fetch_jina_reader(target_url: str, api_key: str = None) -> str:
    reader_url = f"https://r.jina.ai/{target_url}"
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    response = requests.get(reader_url, headers=headers, timeout=10)
    if response.status_code == 200:
        return response.text  # 返回极简 Markdown 内容
    raise Exception(f"Jina Reader failed: {response.status_code}")
```

### 3. 第三层：CamoFox 浏览器指纹沙盒

当面临 JS 动态渲染或严密反爬，且需要细粒度操控 DOM（如手动点击翻页）时：

```python
from camoufox import Camoufox
from bs4 import BeautifulSoup

def fetch_camoufox(url: str) -> str:
    # 推荐在 headless 模式下运行，非 CI 环境且需要绕过国家区域防爬时可将 geoip 设为 True
    with Camoufox(headless=True, geoip=False) as browser:
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)  # 稳定等待 2s
        return page.content()  # 获取 HTML 源码后用 BeautifulSoup 解析
```

### 4. 第四层：Crawl4AI 异步并发与批量爬虫

对于深度挖掘和多并发抓取，通过 `crawl4ai` 的 `AsyncWebCrawler` 运行：

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def fetch_crawl4ai(url: str) -> str:
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url)
        if result.success:
            return result.markdown  # 自动提取净化后的 Markdown
        return ""
```

---

## 安装依赖

```bash
pip install requests beautifulsoup4 lxml camoufox crawl4ai
python -m camoufox fetch   # 首次使用下载浏览器内核
```

## 📎 站点爬虫备忘录

`references/site-specific-notes.md` — 记录了已测试过的网站的最佳爬虫层级和注意事项（包括 armstrongeconomics.com、微信公众号、中国人行 PBoC、日本央行 BoJ、东方财富等）。新站点测试成功后请追加到该文件。

**Chinese financial data scraping highlights** (see the ref file for full details):
- **PBoC (pbc.gov.cn)** — GBK encoding → mojibake; search garbled "浜垮厓" for amounts; maturity not published in daily OMO announcements
- **BoJ (boj.or.jp)** — Operations data migrated from static HTML to daily XLSX files (requires `openpyxl`)
- **East Money (push2.eastmoney.com)** — `diff` field is a dict (not list); sector codes drift over time

## 必须遵守的规则

* ❌ **严禁高频攻击**：请求间隔不得小于 2 秒。
* ❌ **错误彻底隔离**：单爬虫解析失败时必须进行 try/except 隔离捕获，绝对不能由于局部异常阻断整个采集管道的运行。
* ❌ **禁止使用禁用库**：禁止使用过重的 `scrapy` 或性能较差且易被检测的 `selenium`。
* ✅ **URL 去重清洗**：为保证去重准确性，清洗 URL 时务必剥离不必要的查询参数（如 `url.split("?")[0]`）。
* ✅ **遵守 Robots 合规**：调用除 `Jina Reader` 外的所有自建爬虫前，务必调用 robots.txt 校验逻辑（带 UA 头和 timeout 超时控制）。
* ⚠️ 微信公众号图片（mmbiz.qpic.cn）有防盗链：requests 直接请求可能返回 403/空内容。需要用浏览器打开页面后通过 `browser_console` 提取 `#js_content img[data-src]` 获取真实 URL，并用浏览器 User-Agent 头下载
* ⚠️ EasyOCR 对古籍手抄本（竖排书法）完全无效 — 检测到 OCR 输出置信度 < 0.1 且为乱码时，跳过 OCR，直接保存已有文字信息

## 📦 文件结构

本 skill 的 repo 文件：`self-skill/webworms/`

| 路径 | 内容 |
|------|------|
| `SKILL.md` | 主 skill 文件（本文件） |
| `references/site-specific-notes.md` | 站点爬虫备忘录 |
| `references/base_scraper_impl.md` | BaseScraper 最小实现（各 agent 导入用） |
| `scripts/wechat_scraper.py` | 微信公众号图片批量下载脚本 |

> 安装时直接将 `self-skill/webworms/` 整目录拷到本机 skill 路径即可（如 `~/.claude/skills/`、`~/.hermes/skills/` 或 `~/.gemini/antigravity/skills/`）。
