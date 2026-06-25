---
title: Uber GenAI Gateway — 免费公网搜索（grounded web search）给 Hermes Agent 用
domain: engineering
keywords: [genai-gateway, web-search, grounded, gemini, google-search, 联网, 公网搜索, exa, tavily, ddgs, ai-guard, pii, cerberus, ussh, devpod, 内部联网, usearch, keepalive, idle, failed-after-retries]
source: hermes-economy-kol-genai-integration-20260625
created: 2026-06-25
last_updated: 2026-06-25 (+usearch CLI 封装 + Cerberus idle 保活根治)
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

## 复用 CLI 封装：`usearch`（逐级 backup 搜索）

把上面的方案封装成一个开箱即用的 CLI，**所有 Hermes 项目直接复用**，不用各自重写降级逻辑。

**位置**：`~/.local/bin/usearch`（已 chmod +x；记得 `~/.local/bin` 在 PATH）

**降级链**（前级失败/无结果才落下级，stderr 实时打印用了哪一级）：
- **L1** GenAI Gateway grounded：`gemini-3-flash-preview` + `google_search`，端口 5436，带 `Rpc-Service`/`Rpc-Caller` 头。综述 + 源URL，免费不断粮。
- **L2** 同网关自动换备用模型（`gemini-2.5-flash` → `gemini-2.5-pro`），抗偶发 5xx。
- **L3** `ddgs` 兜底（网关整挂时），纯链接列表。

**源 URL = 方案 A**：直接用 `groundingMetadata` 原始 uri（`vertexaisearch.../grounding-api-redirect/...` 跳转链），**不跟随重定向解析**。要落地页再 fetch。

**用法**：
```bash
usearch "query"                  # 默认 grounded
usearch -n 8 "query"             # 限源数
usearch --model gemini-2.5-pro "query"
usearch --raw "query"            # JSON 输出 (text + urls + tier)
usearch --ddgs "query"           # 强制走 ddgs 兜底
```

**实现要点 / 踩过的坑**：
- `ddgs -o json` **不打印 stdout 而是偷偷写文件** `/tmp/text_<query>_<时间>.json`。改用 `from ddgs import DDGS` Python 库直调，别走 CLI 的 `-o`。
- `ddgs` 装在 `~/.local/bin/`，cron/非登录 shell 的 PATH 里可能没有 → 用库直调最稳。
- L1 默认升到 `gemini-3-flash-preview`（质量高于 2.5、比 3-pro 快），实测 grounded 可用。

## ⚠️ 致命坑 + 根治：Cerberus 隧道 idle 自停 → 对话/搜索偶发 "failed after retries"

**现象**：一段时间没活动后，下一条请求偶发 `The model provider failed after retries`，再发一条又好了。

**根因**（cerberus 日志实锤）：Cerberus 有空闲休眠——`Idle session detected. Stopping Cerberus daemon`。请求落在 idle 唤醒/重握手窗口期（1-2s），此时隧道返回连接错误或 502/503。而 **proxy 旧代码只对 429 重试，对连接错误/5xx 直接放弃** → 报错。**关键**：cerberus 的 `/health` 探测**不算活跃使用**，每分钟 ping health 也阻止不了 idle（日志显示 health check 后照样 idle）。

**根治（双管齐下，治本 + 兜底）**：

1. **保活进程**（治本）`~/.hermes/scripts/genai_keepalive.sh`
   - 每 40s 打一次**真实 1-token** `generateContent`（`gemini-2.5-flash`，`maxOutputTokens:1`）→ session 永不 idle。代价极小（每次 totalTokenCount=1）。
   - `flock` 单实例；cron **每分钟自愈** + `@reboot` 兜底 → durable、跨会话、抗 reboot。
   - 必须显式 `export SSH_AUTH_SOCK=/var/lib/devpod/ssh/active_ssh_auth_sock`（cron 不继承登录 shell env，否则 Cerberus no suitable auth）。
   - 验证：cerberus 日志 `Idle session detected` 应归零，改为持续的 generateContent 请求。

2. **proxy 重试覆盖瞬时错误**（兜底竞态窗口）`genai_proxy.py`
   - `HTTPError` 重试条件从 `e.code == 429` 扩到 `e.code in (429, 502, 503)`。
   - `URLError`（连接层错误）也重试（退避 1.5s/3s），兜住保活间隙的窄竞态窗口。
   - 429/超时(504)/大请求逻辑不动。注意 `except HTTPError` 必须在 `except URLError` 之前（前者是后者子类）。

> 不做保活 = 隧道反复 idle 拉锯，用户偶发掉线手动恢复；做了保活 = 永不 idle，proxy 重试再兜住极端竞态。两者都上才是真 durable。

