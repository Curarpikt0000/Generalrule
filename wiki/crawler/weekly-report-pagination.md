---
title: 周报列表爬取中的分页与数据遗漏防范
domain: crawler
type: concept
keywords: [crawler, pagination, weekly-report, sge, backfill]
tags: [crawler, pagination, weekly-report, sge, backfill]
source: L-2026-05-30-001
sources: [conversation-58ba548d-76d0-41b8-adb1-b9b24483e883]
created: 2026-05-30
updated: 2026-05-30
last_updated: 2026-05-30
---

# 周报列表爬取中的分页与数据遗漏防范

在进行按周或按月发布的周报、月报历史数据抓取与回填（Backfill）时，极易因忽略源站列表的“分页（Pagination）”逻辑而只爬取第一页/首屏，从而导致历史回填数据严重遗漏。

## 核心教训 / Key Insights

1. **第一页不等于全量历史**：许多交易数据、行情周报源站的首页（第一页）仅展示固定条数（如 10 条）。直接请求默认 URL 无法获取更早的历史数据。
2. **回填范围驱动的自适应分页**：爬虫获取列表的逻辑不应该硬编码为只请求单页，而应该由“回填目标日期”（如 90 天）动态驱动，逐页向下翻页直到探测到的最早日期超出阈值。
3. **Fail Loud（显式失败）原则**：翻页过程中若未匹配到目标链接或遭遇解析失败，应当及时向上抛出异常，拒绝静默跳过，避免遗漏。

## 正确做法：自适应分页抓取逻辑

以 Python 请求 SGE 行情周报页面为例，编写鲁棒的分页逻辑：

```python
def discover_weekly_reports(start_date, end_date):
    pdf_entries = []
    page = 1
    headers = {"User-Agent": "Mozilla/5.0 ..."}
    
    while True:
        url = f"https://example.com/reports?p={page}"
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, 'html.parser')
        page_entries_found = 0
        has_relevant_dates = False
        
        for a in soup.find_all('a', href=True):
            if a['href'].endswith('.pdf'):
                title = a.get_text(strip=True)
                # 从标题或 URL 提取日期
                m = re.search(r'(\d{8})-(\d{8})周报', title)
                if m:
                    week_end = datetime.strptime(m.group(2), "%Y%m%d").date()
                    page_entries_found += 1
                    
                    if week_end >= start_date:
                        has_relevant_dates = True
                    
                    if start_date <= week_end <= end_date:
                        pdf_entries.append({
                            "title": title,
                            "url": urljoin("https://example.com", a['href']),
                            "week_end": week_end
                        })
        
        # 如果当前页没有找到任何周报，或者当前页包含的所有周报日期都早于我们的 start_date 阈值
        # 则不再继续请求下一页，安全跳出循环
        if page_entries_found == 0 or not has_relevant_dates:
            break
            
        page += 1
        time.sleep(1) # 友好翻页，限速
        
    return pdf_entries
```

## 来源
* **Lesson ID**: L-2026-05-30-001

## 相关页面
- [[crawler-bypass-handbook]]
- [[five-step-pipeline]]
