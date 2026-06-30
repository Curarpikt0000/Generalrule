# 多源搜索降级链（KOL 搜索抗断粮设计）

> 2026-06-25 实战：付费 Exa/Tavily 会断粮（Tavily 实测超额返回 0、Exa 余额将尽），
> 付费源断粮那天 cron 观点全丢 = KOL 监控最怕的事。解法 = 多源降级链 + 免费兜底。
> 本文是 `backfill_one.py` 的搜索源工程笔记 + 选型踩坑（含 grounded-search 网关弃用教训）。

## 当前降级链（精度递减，backfill_one.py 内置）

**Exa（主，带日期窗最准）→ Tavily（备）→ SearXNG（自托管，免费不断粮、可搜真名零截断）→ ddgs（最后兜底）**

- 触发：付费源(Exa+Tavily)命中=0 → 上 SearXNG；SearXNG 也挂 → 才 ddgs。
- 输出 json **四桶** `exa`/`tavily`/`searxng`/`ddgs`。**下游分析/cron prompt 必须四桶都读**，漏读=断粮当天丢观点。
- searxng/ddgs 无可靠 date 字段 → 时效靠 content 正文里的实际日期判断（只保留当日窗口）。
- ⚠️ **此降级链是 Economy-KOL 项目专属，不外推到其他 Hermes 项目。SearXNG backend 设置由 Chao 维护，禁止修改。**

## SearXNG（当前正式兜底源）

自托管元搜索，Chao 已配为后台默认（`config.yaml` 里 `search_backend: searxng`）。

```python
import json, urllib.request, urllib.parse
def searxng_search(query, num=12):
    url = "http://localhost:8888/search?" + urllib.parse.urlencode({"q": query, "format": "json"})
    out = []
    try:
        d = json.load(urllib.request.urlopen(url, timeout=30))
    except Exception as e:
        print(f"  SearXNG ERR: {str(e)[:120]}"); return []
    for x in d.get("results", [])[:num]:
        out.append({"title": x.get("title"), "url": x.get("url"),
                    "content": (x.get("content") or "")[:1500], "date": x.get("publishedDate")})
    return out
```

**为什么 SearXNG 适合 KOL 任务（关键优势）**：
- **可搜真名、零 PII 截断**——直接 `"Peter Schiff gold"` 带空格全名就返回 31 条真实结果，无需任何绕过技巧。
- 免费、自托管、不断粮、不限额。
- `publishedDate` 常为 None（SearXNG 不总给日期），但 content 正文里常带日期（"June 23, 2026"）→ 时效靠正文。

## ⚠️ 带 PII 匿名化的 LLM grounded-search 网关 — 试过但弃用（重要教训，别再走回头路）

曾把一个 LLM grounded-search（LLM + google_search 综述式）网关集成为首选兜底，
**后因致命局限弃用，换 SearXNG**。记录在此避免未来重蹈：

**致命局限：该网关对 prompt 做人名 PII 匿名化** → 按人名精确搜索不稳定，正是 KOL 任务的命门。

全量实测（76 KOL）：
- 大部分人 OK（综述认出本人）、少数 NO_NAME（有综述+源URL但未直呼全名）、**个别高频人名被匿名化截断**、0 EMPTY。
- "去空格连写"绕过（`PeterSchiff`/`LukeGromen`/handle去@/display_name去空格）能缓解大部分，但 **高频名去空格后仍被匿名化** → 缓解非根治。
- 结论：**带 PII 匿名化的 grounded search 不适合"按人名精确搜索"的 KOL 监控**。SearXNG 没这个问题（直接搜真名）。

**grounded-search 网关 vs Exa 素材形态差异（选型参考）**：
- Exa = 原始文档列表，每条带**精确发布日期**+标题+正文片段（颗粒细、日期准、但有噪音页要自己筛）。
- grounded 网关 = 1 篇 LLM **综述**（信息密度高、已归纳好）+ 源URL，但**无精确到条的日期**、是二手转述。
- → Exa 当主源（日期准利于"当日新观点"判断）是对的；兜底要"可搜真名"则 SearXNG > grounded 综述。
> （通用版联网知识由其他 Hermes 实例维护）。但**此项目已不用该 grounded-search 网关**。

## 验证降级链（不动 .env 模拟断粮）

```python
import importlib.util, sys
spec = importlib.util.spec_from_file_location('bf','scripts/backfill_one.py')
bf = importlib.util.module_from_spec(spec); spec.loader.exec_module(bf)
bf.EXA=''; bf.TAV=''                       # 模拟两个付费源断粮
sys.argv=['x','<kol_id>','2026-06-22','2026-06-23']
bf.main()                                  # 应看到"降级 SearXNG"+searxng 桶有料、ddgs=0
```
正常场景（Exa 有结果）跑真实 key，确认 searxng/ddgs=0（不触发不浪费）。
测人名截断用一个之前被 grounded-search 网关匿名化截断的高频名：SearXNG 应正常返回（验证零截断）。

## ddgs 安装

`pip install ddgs --break-system-packages`（VM 系统 python 无 venv，cron 用 /usr/bin/python3）。
新包名 `ddgs`（旧 `duckduckgo_search` 的后继），`from ddgs import DDGS`。
