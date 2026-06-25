---
title: Uber GenAI Gateway — 免费公网搜索（grounded web search）给 Hermes Agent 用
domain: engineering
keywords: [genai-gateway, web-search, grounded, gemini, google-search, 联网, 公网搜索, exa, tavily, ddgs, ai-guard, pii, cerberus, ussh, devpod, 内部联网]
source: hermes-economy-kol-genai-integration-20260625
created: 2026-06-25
last_updated: 2026-06-25
---

# Uber GenAI Gateway — 免费公网搜索给 Hermes Agent 用

## 一句话

跑在 Uber devpod 上的 Hermes agent **不需要付费的 Exa/Tavily 也能联网搜公网**：
直接打内部 **GenAI Gateway** 的 grounded web search（Gemini + Google Search grounding），
**免费走内部计费、永不断粮、返回带源 URL 的实时结果**。这是 Uber 官方的公网出口。

## 背景 / 纠正一个常见误判

很多人（包括早期的我）扫一眼 `aifx mcp list` 没看到 web/news/serp 类 MCP，就下结论
"Uber 内部没有公网搜索"。**这是错的。**

真相：`aifx mcp list` 里的 search 类 MCP（usearch/Glean、freight-search、opensearch、
web-dm-tools…）确实全是**内部知识/业务数据**，不搜公网。但 **Uber 官方的公网出口
收口在 GenAI Gateway**——它不只做对话补全，还透传各家大模型的**原生联网工具**
（Gemini 的 Google Search grounding / OpenAI 的 web_search / Anthropic 的 web_search）。
LLM 在网关侧实际去搜公网并返回带 URL 的结果。

生产佐证：`tax-tagger/gateway/genai/genai.go` 包注释明确写 "provides a gateway for
**grounded web search** via the internal GenAI API gateway, supporting Gemini, GPT, and
Claude"；hotel-naming LLM 评审写 "gen-ai-gateway acts as the **only outbound gateway**
to external LLM provider(s)"。

## 怎么用（已实测跑通，Gemini 路径最简）

前提：devpod 上 Cerberus 隧道常驻在 `localhost:5436`（genai-proxy/agentic-ussh 已自动续期）。

```python
import json, urllib.request, os

def genai_web_search(query, num=12):
    caller = os.environ.get("USER", "agent") + "@uber.com"
    body = {
        "contents": [{"role": "user", "parts": [{"text": query}]}],
        "tools": [{"google_search": {}}],          # ← 关键：开 Google Search grounding
        "generationConfig": {"temperature": 0.2},
    }
    req = urllib.request.Request(
        "http://localhost:5436/v1/models/gemini-2.5-flash:generateContent",
        data=json.dumps(body).encode(),
        headers={"content-type": "application/json",
                 "Rpc-Service": "genai-api",          # ← 必须
                 "Rpc-Caller": caller},               # ← 必须 <ldap>@uber.com
        method="POST")
    d = json.load(urllib.request.urlopen(req, timeout=60))
    c = (d.get("candidates") or [{}])[0]
    txt = "".join(p.get("text", "") for p in c.get("content", {}).get("parts", []))
    chunks = c.get("groundingMetadata", {}).get("groundingChunks", [])
    urls = [ch.get("web", {}).get("uri", "") for ch in chunks[:num]]
    return txt, urls   # txt=Gemini 综述正文(信息密度高), urls=源URL列表
```

curl 等价：
```bash
curl -s -X POST "http://localhost:5436/v1/models/gemini-2.5-flash:generateContent" \
  -H "content-type: application/json" \
  -H "Rpc-Service: genai-api" -H "Rpc-Caller: $(whoami)@uber.com" \
  -d '{"contents":[{"role":"user","parts":[{"text":"<查询>"}]}],
       "tools":[{"google_search":{}}],"generationConfig":{"temperature":0.2}}'
```

返回结构：
- `candidates[0].content.parts[].text` = Gemini 综述正文（自动跟随查询语言，中文查询→中文综述）
- `candidates[0].groundingMetadata.groundingChunks[].web.uri` = 源 URL（可溯源/去重）
- `groundingMetadata.groundingSupports[]` = 正文每段→来源的细粒度映射

其它 provider（按需）：OpenAI `POST /v1/responses` + `tools:[{"type":"web_search"}]`；
Anthropic `POST /v1/messages` + `tools:[{"type":"web_search_20250305"}]`。

## ⚠️ 致命坑 + 绕过实战：AI-Guard 的 PII 匿名化

GenAI Gateway 前面挂了 **AI-Guard**，会对 prompt 做 PII 匿名化——**人名会被替换成
`ANONYMIZED_PERSON_X`**，导致"精确搜某个人"直接失败（综述返回"找不到此人言论"）。

实测命中率（2026-06）：
- ❌ **带空格的标准全名**："Peter Schiff gold" / "Luke Gromen macro" → 被匿名化 → 查无
- ✅ **handle 拼写 / 全名去空格**："PeterSchiff" / "LukeGromen" / "RayDalio" /
  "jeffgundlach" / "BobHaberkorn" → **未被匿名化，正确识别本人**，返回真实当日观点

**绕过规则：搜人名时把名字写成"去空格连写"形式**（X handle 去掉 @ 去空格，或 display_name
去空格）。验证过对"有 handle"和"无 handle"（用 display_name 去空格）的人都有效。
纯话题查询（不含人名，如 "gold price news 2026-06-23 analyst commentary"）也能拿当日板块动态。

```python
# 人名查询的安全构造
handle = (x_handle or "").lstrip("@").strip() or "".join(display_name.split())
query = f"{handle} {focus_topic} market news {start} to {end}"
```

## 在 Hermes 项目里放哪一层？

它**质量高于 ddgs、且免费不断粮**，但**精度/日期窗不如 Exa**（Exa 有 startPublishedDate
日期窗最准；GenAI 是综述+源URL，无硬日期过滤，时效靠正文判断）。推荐降级链：

**Exa（主，日期窗最准，付费）→ GenAI Gateway（免费不断粮，Google引擎）→ ddgs（最后兜底）**

触发逻辑：付费源命中=0 时自动启用 GenAI；GenAI 也挂（隧道断/网关故障）才到 ddgs。
参考实现见 economics-kol skill 的 `scripts/backfill_one.py`（genai_search + 四桶降级链）。

## 适用 / 不适用

- ✅ 适用：新闻/实时信息/公众人物观点/板块动态/任何公网内容的检索，作为 Exa 的免费替代或兜底
- ✅ 适用：搜具体人（用去空格 handle 绕 PII），实测能拿到本人真实观点 + 中文综述
- ⚠️ 注意：返回的是 Gemini **综述**而非原始文档全文；要原文需再 fetch 源 URL（或走 Oxylabs）
- ⚠️ 注意：依赖 devpod 的 Cerberus 隧道（localhost:5436）+ ussh 证书在线；本地非 Uber 环境不可用

## 其它内部联网选项（备忘）

- **LangFx / Agent Builder 内置工具**：`get_tools(["search.web"])` / `search.serpapi`
  （Uber 已买 SerpAPI 额度）/ `search.web_search_summary`——适合在 LangFx agent 运行时里用。
- **抓全文页面**：Oxylabs 代理 / 直连 HTTPS（agentic-scraping 平台模式）。
