---
description: "Python web scraping skill. Use when you need to scrape websites for structured data. Supports a 4-tier fallback crawling strategy using requests/BS4, Jina Reader, CamoFox, and Crawl4AI, with built-in robots.txt compliance, rate limiting, and retry logic."
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
*   **robots.txt 检查**：`self.can_fetch(url)` 自动调用
*   **限速请求**：`self.get(url)` 自动进行 2s 以上的延迟限速，并支持 3 次自动重试。

```python
class MyScraper(BaseScraper):
    def fetch(self) -> list[dict]:
        resp = self.get("https://example.com/events")
        if not resp:
            return []
        soup = BeautifulSoup(resp.text, "lxml")
        # ... 进行 DOM 解析并返回数据
```

### 2. 第二层：Jina Reader 动态 Markdown 转化

```python
import requests

def fetch_jina_reader(target_url: str, api_key: str = None) -> str:
    reader_url = f"https://r.jina.ai/{target_url}"
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    response = requests.get(reader_url, headers=headers, timeout=10)
    if response.status_code == 200:
        return response.text
    raise Exception(f"Jina Reader failed: {response.status_code}")
```

### 3. 第三层：CamoFox 浏览器指纹沙盒

```python
from camoufox import Camoufox
from bs4 import BeautifulSoup

def fetch_camoufox(url: str) -> str:
    with Camoufox(headless=True, geoip=False) as browser:
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        return page.content()
```

### 4. 第四层：Crawl4AI 异步并发与批量爬虫

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def fetch_crawl4ai(url: str) -> str:
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url)
        if result.success:
            return result.markdown
        return ""
```

---

## 必须遵守的规则

*   ❌ **严禁高频攻击**：请求间隔不得小于 2 秒。
*   ❌ **错误彻底隔离**：单爬虫解析失败时必须进行 try/except 隔离捕获。
*   ❌ **禁止使用禁用库**：禁止使用过重的 `scrapy` 或 `selenium`。
*   ✅ **URL 去重清洗**：清洗 URL 时务必剥离不必要的查询参数（`url.split("?")[0]`）。
*   ✅ **遵守 Robots 合规**：调用除 Jina Reader 外的所有爬虫前，务必调用 robots.txt 校验逻辑。

## 示例代码位置

BaseScraper 基类和 JS+图片抓取示例见 `~/.hermes/skills/webworms/examples/`
