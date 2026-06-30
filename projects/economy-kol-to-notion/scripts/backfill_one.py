#!/usr/bin/env python3
"""Step2 回溯引擎 — 单 KOL 多源观点检索。
用法: python3 backfill_one.py <kol_id> [start_date] [end_date]
源: Exa (主, 语义+日期过滤) + Tavily (备). 输出原始检索结果到 data/backfill/<id>.json
不直接写 Notion — 先产出原始素材, 由分析层(下一脚本)转结构化观点。
"""
import json, sys, re, urllib.request, urllib.error, time
from datetime import datetime

def load_key(name):
    pre = name + "="
    for l in open("config/.env"):
        if l.startswith(pre):
            return l[len(pre):].strip()
    return ""

EXA = load_key("EXA_API" + "_KEY")
TAV = load_key("TAVILY_API" + "_KEY")

def exa_search(query, start, end, num=10):
    body = {
        "query": query, "type": "auto", "numResults": num,
        "startPublishedDate": start + "T00:00:00.000Z",
        "endPublishedDate": end + "T23:59:59.000Z",
        "contents": {"highlights": True, "text": {"maxCharacters": 2000}},
    }
    req = urllib.request.Request("https://api.exa.ai/search", data=json.dumps(body).encode(),
        headers={"x-api-key": EXA, "Content-Type": "application/json"}, method="POST")
    try:
        d = json.load(urllib.request.urlopen(req, timeout=45))
        return d.get("results", [])
    except urllib.error.HTTPError as e:
        print(f"  Exa ERR {e.code}: {e.read().decode()[:100]}", file=sys.stderr)
        return []

def tavily_search(query, num=8):
    body = {"query": query, "max_results": num, "search_depth": "advanced",
            "include_raw_content": False}
    req = urllib.request.Request("https://api.tavily.com/search", data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + TAV, "Content-Type": "application/json"}, method="POST")
    try:
        d = json.load(urllib.request.urlopen(req, timeout=45))
        return d.get("results", [])
    except urllib.error.HTTPError as e:
        print(f"  Tavily ERR {e.code}: {e.read().decode()[:100]}", file=sys.stderr)
        return []

def ddgs_search(query, num=10):
    """免费兜底源 (DuckDuckGo). 无日期窗 — 时效靠后续分析层按正文判断.
    返回结构归一化为 {title,url,text} 形如 Tavily/Exa 结果, 方便统一处理."""
    try:
        from ddgs import DDGS
    except ImportError:
        print("  ddgs 未安装 (pip install ddgs --break-system-packages)", file=sys.stderr)
        return []
    out = []
    try:
        with DDGS() as d:
            # backend/region 默认; 加 'news' 检索更偏时效
            for x in d.text(query, max_results=num):
                out.append({
                    "title": x.get("title"),
                    "url": x.get("href") or x.get("url"),
                    "content": x.get("body") or "",
                })
    except Exception as e:
        print(f"  ddgs ERR: {str(e)[:120]}", file=sys.stderr)
        return []
    return out

def searxng_search(query, num=12):
    """SearXNG 自托管元搜索 (localhost:8888, 后台默认已配). 免费、不断粮、无 PII 截断、
    可搜真名(不像某些网关会匿名化人名). 返回归一化 [{title,url,content}].
    优先级: 排在 Exa/Tavily 之后、ddgs 之前(质量高于 ddgs 且自托管不限额).
    注: SearXNG 的 publishedDate 常为 None, 时效靠 content 正文里的日期判断."""
    import urllib.parse
    url = "http://localhost:8888/search?" + urllib.parse.urlencode(
        {"q": query, "format": "json"})
    out = []
    try:
        d = json.load(urllib.request.urlopen(url, timeout=30))
    except Exception as e:
        print(f"  SearXNG ERR: {str(e)[:120]}", file=sys.stderr)
        return []
    for x in d.get("results", [])[:num]:
        out.append({
            "title": x.get("title"),
            "url": x.get("url"),
            "content": (x.get("content") or "")[:1500],
            "date": x.get("publishedDate"),
        })
    return out

def google_news_rss(query, num=10):
    """L5 终极独立兜底(主) —— Google News 官方 RSS 接口。
    完全独立于 SearXNG/Cerberus/付费 API, 纯 HTTP 不用浏览器, Google 官方出口不反爬。
    这就是'直接交给 Google'。带精确 pubDate(弥补 SearXNG 无日期短板)。
    归一化为 [{title,url,content,date}]."""
    import urllib.parse
    import xml.etree.ElementTree as ET
    url = ("https://news.google.com/rss/search?q=" + urllib.parse.quote(query)
           + "&hl=en-US&gl=US&ceid=US:en")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        raw = urllib.request.urlopen(req, timeout=20).read()
        root = ET.fromstring(raw)
    except Exception as e:
        print(f"  GoogleNewsRSS ERR: {str(e)[:100]}", file=sys.stderr)
        return []
    out = []
    for item in root.iter("item"):
        out.append({
            "title": item.findtext("title") or "",
            "url": item.findtext("link") or "",
            "content": (item.findtext("description") or "")[:1500],
            "date": item.findtext("pubDate") or None,
        })
        if len(out) >= num:
            break
    return out

def playwright_google(query, num=10):
    """L6 最后保命兜底 —— Google News RSS 也挂时, 自起 Chromium 抓 Bing News。
    完全独立(自己开浏览器)。Google /search 裸抓会触发反爬验证页, 故改抓 Bing News(对 headless 宽容)。
    归一化为 [{title,url,content,date}]. 需: playwright install chromium"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  playwright 未安装 (pip install playwright --break-system-packages && playwright install chromium)", file=sys.stderr)
        return []
    import urllib.parse
    out = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            page = browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
                locale="en-US",
            ).new_page()
            page.goto("https://www.bing.com/news/search?q=" + urllib.parse.quote(query),
                      timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            items = page.eval_on_selector_all(
                "a.title, a.news-card-title, .news-card a[href]",
                """els => els.slice(0, 20).map(a => ({
                    url: a.href,
                    title: (a.innerText||"").trim(),
                    content: (a.getAttribute("aria-label")||a.innerText||"").slice(0,400)
                }))"""
            )
            browser.close()
            seen = set()
            for it in items:
                u = it.get("url", "")
                if not u or u in seen or "bing.com" in u:
                    continue
                seen.add(u)
                out.append({"title": it.get("title", ""), "url": u,
                            "content": it.get("content", ""), "date": None})
                if len(out) >= num:
                    break
    except Exception as e:
        print(f"  playwright_google(Bing) ERR: {str(e)[:140]}", file=sys.stderr)
        return out
    return out

def main():
    kol_id = sys.argv[1]
    start = sys.argv[2] if len(sys.argv) > 2 else "2025-11-01"
    end = sys.argv[3] if len(sys.argv) > 3 else datetime.now().strftime("%Y-%m-%d")

    reg = json.load(open("data/kol_registry.json"))
    kol = next((k for k in reg["kols"] if k["id"] == kol_id), None)
    if not kol:
        print(f"KOL id '{kol_id}' 未找到"); sys.exit(1)

    print(f"回溯: {kol['display_name']} ({kol['sector']}) | {start} ~ {end}")
    print(f"search_terms: {kol['search_terms']}")

    results = {"kol_id": kol_id, "display_name": kol["display_name"],
               "range": [start, end], "exa": [], "tavily": [], "searxng": [], "ddgs": [], "google": []}

    # Exa: 每个 search_term 跑一次, 带日期窗
    for term in kol["search_terms"]:
        r = exa_search(term, start, end)
        print(f"  Exa '{term}': {len(r)} 条")
        for x in r:
            results["exa"].append({"title": x.get("title"), "url": x.get("url"),
                "date": x.get("publishedDate"), "highlights": x.get("highlights", []),
                "text": (x.get("text") or "")[:1500], "query": term})
        time.sleep(0.5)

    # Tavily: 只用主名字 + 资产词 (备用补充)
    for term in kol["search_terms"][:2]:
        r = tavily_search(term)
        print(f"  Tavily '{term}': {len(r)} 条")
        for x in r:
            results["tavily"].append({"title": x.get("title"), "url": x.get("url"),
                "content": x.get("content", "")[:1500], "score": x.get("score"), "query": term})
        time.sleep(0.5)

    # ───────────────────────────────────────────────────────────────────
    # 自动降级链 (逐层独立判定: 本层 0 命中 = 真没有 OR 被限流/异常, 一律落下层)
    #   L1 Exa → L2 Tavily → L3 SearXNG(全引擎) → L4 ddgs → L5 playwright→Google(终极独立兜底)
    # 触发逻辑: 累计命中仍为 0 时, 才继续往下一层试; 任一层拿到结果即停止下沉.
    # 注: exa_search/tavily_search 已 catch HTTPError(含 429 限流)返回 [],
    #     所以"被限流"会自然表现为该层 0 命中 → 自动触发下沉.
    # L5 用 playwright 自起浏览器抓 Google, 完全独立于 SearXNG/Cerberus, 是真兜底.
    # L1-L5 全挂 = 极端情况, 应报警让人介入(或 computer-use 人工兜底), 不再自欺.
    # ───────────────────────────────────────────────────────────────────
    paid_hits = len(results["exa"]) + len(results["tavily"])

    # L3 SearXNG (付费源全 0 → 限流或无结果, 落自托管元搜索)
    if paid_hits == 0:
        print(f"  ⚠️ L1/L2(Exa+Tavily)无命中(无结果或限流), 降级 L3 SearXNG...")
        for term in kol["search_terms"][:2]:
            r = searxng_search(term)
            print(f"  SearXNG '{term}': {len(r)} 条")
            for x in r:
                results["searxng"].append({"title": x.get("title"), "url": x.get("url"),
                    "content": (x.get("content") or "")[:1500],
                    "date": x.get("date"), "query": term})
            time.sleep(0.4)

        # L4 ddgs (SearXNG 也 0 → 实例挂或限流, 落 ddgs)
        if len(results["searxng"]) == 0:
            print(f"  ⚠️ L3 SearXNG 无命中(挂或限流), 降级 L4 ddgs...")
            for term in kol["search_terms"][:2]:
                r = ddgs_search(term)
                print(f"  ddgs '{term}': {len(r)} 条")
                for x in r:
                    results["ddgs"].append({"title": x.get("title"), "url": x.get("url"),
                        "content": (x.get("content") or "")[:1500], "query": term})
                time.sleep(0.8)

            # L5 Google News RSS 终极独立兜底 (前四层全挂 → 直接交给 Google 官方 RSS, 不反爬/带日期)
            if len(results["ddgs"]) == 0:
                print(f"  🔴 L1-L4 全部无命中, 启用 L5 终极独立兜底: 直接交给 Google News RSS...")
                for term in kol["search_terms"][:2]:
                    r = google_news_rss(term)
                    print(f"  GoogleNewsRSS '{term}': {len(r)} 条")
                    for x in r:
                        results["google"].append({"title": x.get("title"), "url": x.get("url"),
                            "content": (x.get("content") or "")[:1500],
                            "date": x.get("date"), "query": term})
                    time.sleep(0.5)

                # L6 playwright→Bing 最后保命 (连 Google News RSS 都挂 → 自起浏览器)
                if len(results["google"]) == 0:
                    print(f"  🔴 L5 Google News RSS 也无命中, 启用 L6 最后保命: playwright 自起浏览器抓 Bing News...")
                    for term in kol["search_terms"][:2]:
                        r = playwright_google(term)
                        print(f"  playwright→Bing '{term}': {len(r)} 条")
                        for x in r:
                            results["google"].append({"title": x.get("title"), "url": x.get("url"),
                                "content": (x.get("content") or "")[:1500],
                                "date": x.get("date"), "query": term})
                        time.sleep(1.0)

                if len(results["google"]) == 0:
                    print(f"  ⛔ L1-L6 全部失败! 应报警让人介入(或 computer-use 人工兜底).", file=sys.stderr)

    import os
    os.makedirs("data/backfill", exist_ok=True)
    out = f"data/backfill/{kol_id}.json"
    json.dump(results, open(out, "w"), ensure_ascii=False, indent=2)
    print(f"\n原始素材已存: {out}")
    print(f"  Exa {len(results['exa'])} 条, Tavily {len(results['tavily'])} 条, "
          f"SearXNG {len(results['searxng'])} 条, ddgs {len(results['ddgs'])} 条, "
          f"Google {len(results['google'])} 条")



if __name__ == "__main__":
    main()
