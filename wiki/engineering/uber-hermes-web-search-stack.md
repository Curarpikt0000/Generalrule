---
title: Uber Hermes 公网搜索工具栈与兜底层级（SearXNG 主力 / GenAI grounded 仅项目级辅助兜底）
domain: engineering
keywords: [web-search, 搜索工具栈, 兜底层级, searxng, exa, tavily, ddgs, genai-gateway, grounded, gemini, google-search, 联网, 公网搜索, ai-guard, pii, cerberus, ussh, devpod, 内部联网, usearch, keepalive, idle, failed-after-retries]
source: hermes-web-search-stack-20260625
created: 2026-06-25
last_updated: 2026-06-25 (正名为搜索工具栈；GenAI 从"推荐主力"改写为"项目级辅助兜底"，置顶权威层级)
---

# Uber Hermes 公网搜索工具栈与兜底层级

## ⭐ 当前搜索工具层级与兜底方案（权威，先看这个）

> 🔴 **核心事实（Chao 2026-06-25 拍板）**：
> **SearXNG 是公网搜索的主力/默认兜底；GenAI Gateway grounded search 只是【项目级可选辅助兜底】，不是标准搜索步骤之一。**
> GenAI grounded 因 **AI-Guard PII 人名匿名化**（见下文坑）不适合「按人名精确搜索」的场景，
> 因此**不得**把它当成通用/默认的搜索方案来推广或依赖。需要联网搜公网时，标准顺序优先用 SearXNG。

**🔴 铁律：搜索降级链是「项目级」，不是「Hermes 整体级」。**
切换搜索后端 / 调降级顺序，**只动项目自己的搜索代码或 `~/.local/bin/usearch`**，
**绝不能动 `hermes config`、主 model/provider、或 Hermes 基础设置**。
每个项目可以有自己的搜索策略；Hermes 本体的对话链路与 web 工具保持不变。

### 标准搜索层级（推荐给新项目复用）

```
L1  SearXNG       本地自托管 metasearch（localhost:8888，Chao 后台维护）— 主力，免费、不断粮、真实落地页 URL、可搜真名零 PII 截断
L2  ddgs          DuckDuckGo 免费兜底 — 纯链接列表，无日期窗
（可选）GenAI grounded   仅特定项目按需启用的辅助兜底，默认不在标准链里
```

> ⚠️ **SearXNG 后端由 Chao 维护，严禁修改其配置。**

### 两条「正在跑」的真实降级链（按代码现状记录，非理想方案）

1. **`~/.local/bin/usearch`（共享 CLI，所有项目可复用）**：
   `L1 SearXNG → L2 GenAI grounded（辅助兜底）→ L3 ddgs`
   —— GenAI 在这里是**靠后的可选兜底**，不是默认主力（默认就走 SearXNG）。

2. **Economy-KOL 项目 `scripts/backfill_one.py`（项目专属，不外推）**：
   `Exa（付费主力，日期窗最准）→ Tavily（备）→ SearXNG → ddgs`
   —— 该项目**已彻底移除 GenAI 搜索**（AI-Guard 把 KOL 人名匿名化截断，对「按人名精确搜索」致命）。
   这套含付费 Exa 的链是 KOL 监控**项目专属**，不代表 Hermes 通用方案。

---

## GenAI Gateway grounded search —— 辅助方案备忘（非标准步骤）

> ⚠️ **历史/辅助方案，非标准搜索步骤。** 下面记录的是「GenAI Gateway 也能 grounded 搜公网」这一**技术事实**，
> 供个别项目在 SearXNG 不可用、且任务**不涉及精确搜人名**时按需当兜底用。
> **默认不要用它做搜索**——它有 AI-Guard PII 匿名化的致命局限（见下），且属 Uber 内部机制。

### 技术事实：GenAI Gateway 能透传原生联网工具

`aifx mcp list` 里的 search 类 MCP（usearch/Glean、freight-search、opensearch、web-dm-tools…）
全是**内部知识/业务数据**，不搜公网。但 GenAI Gateway 除做对话补全外，也透传各家大模型的
**原生联网工具**（Gemini 的 Google Search grounding / OpenAI 的 web_search / Anthropic 的 web_search），
LLM 在网关侧实际去搜公网并返回带 URL 的结果。

生产佐证：`tax-tagger/gateway/genai/genai.go` 包注释写 "provides a gateway for **grounded web search**
via the internal GenAI API gateway, supporting Gemini, GPT, and Claude"。

### 调用方式（已实测，Gemini 路径最简）

前提：devpod 上 Cerberus 隧道常驻在 `localhost:5436`（genai-proxy/agentic-ussh 已自动续期）。

```python
import json, urllib.request, os

def genai_web_search(query, num=12):
    caller = os.environ.get("USER", "agent") + "@uber.com"
    body = {
        "contents": [{"role": "user", "parts": [{"text": query}]}],
        "tools": [{"google_search": {}}],          # ← 开 Google Search grounding
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
    return txt, urls   # txt=Gemini 综述正文, urls=源URL列表
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
- `candidates[0].content.parts[].text` = Gemini 综述正文（跟随查询语言）
- `candidates[0].groundingMetadata.groundingChunks[].web.uri` = 源 URL（可溯源/去重）

其它 provider（按需）：OpenAI `POST /v1/responses` + `tools:[{"type":"web_search"}]`；
Anthropic `POST /v1/messages` + `tools:[{"type":"web_search_20250305"}]`。

### ⚠️ 致命坑：AI-Guard 的 PII 匿名化（这正是它不能当标准搜索的原因）

GenAI Gateway 前面挂了 **AI-Guard**，会对 prompt 做 PII 匿名化——**人名会被替换成
`ANONYMIZED_PERSON_X`**，导致「精确搜某个人」直接失败（综述返回"找不到此人言论"）。

实测（2026-06）：
- ❌ **带空格的标准全名**（"Peter Schiff" / "Luke Gromen macro"）→ 被匿名化 → 查无
- ⚠️ **handle/全名去空格**（"PeterSchiff" / "LukeGromen"）→ **大多**能绕过被正确识别，
  但**不稳定**：76 KOL 抽测仍有人（如 Daniel Ghali / DanielGhali）被截断、9 人综述未直呼全名。

**结论：去空格只是缓解非根治；GenAI grounded 不适合「按人名精确搜索」**，这是它从标准搜索层级里
被降为「项目级辅助兜底」的根本原因。需要搜人名时一律走 SearXNG（可搜真名零截断）。

### 适用 / 不适用

- ✅ 仅适用：SearXNG 不可用时，且任务**不涉及精确搜人名**的纯话题/新闻/板块动态检索
- ❌ 不适用：按人名精确搜索（AI-Guard 截断）；任何「默认/标准」搜索步骤
- ⚠️ 返回的是 Gemini **综述**而非原文全文；要原文需再 fetch 源 URL
- ⚠️ 依赖 devpod 的 Cerberus 隧道（localhost:5436）+ ussh 证书在线；本地非 Uber 环境不可用

### 其它内部联网选项（备忘）

- **LangFx / Agent Builder 内置工具**：`get_tools(["search.web"])` / `search.serpapi` / `search.web_search_summary`——适合在 LangFx agent 运行时里用。
- **抓全文页面**：Oxylabs 代理 / 直连 HTTPS（agentic-scraping 平台模式）。

## 复用 CLI 封装：`usearch`（逐级 backup 搜索）

把搜索降级链封装成开箱即用的 CLI，**所有 Hermes 项目直接复用**，不用各自重写降级逻辑。

**位置**：`~/.local/bin/usearch`（已 chmod +x；`~/.local/bin` 需在 PATH）

> 🔴 **铁律：websearch 降级链是「项目级」，不是「整体级」**（Chao 2026-06-25 明确）。
> `usearch` 是一个独立的项目级 CLI，与 **Hermes Agent 的主对话模型 / provider / 网关配置完全无关**。
> 要换搜索后端 / 调降级顺序，**只改这个文件**，**绝不能去动 `hermes config`、主 model/provider、或 Hermes 基础设置**。

**降级链**（前级失败/无结果才落下级，stderr 实时打印用了哪一级）：
- **L1** **SearXNG**（本地 metasearch，`http://localhost:8888`，Chao 维护的默认主力）：多引擎聚合，**直接返回真实落地页 URL**（无需 resolve），免费、快、可搜真名。
- **L2** GenAI Gateway grounded（`gemini` + `google_search`，端口 5436）：**仅作 SearXNG 挂掉时的辅助兜底**，带 AI 综述 + 源URL；**有 PII 匿名化局限，搜人名不可靠**。纯调用，不改 Hermes 任何设置。
- **L3** `ddgs` 兜底（前两级都挂时），纯链接列表。

**源 URL 处理**：
- SearXNG / ddgs 直接给真实 URL。
- GenAI grounded 给 `vertexaisearch.../grounding-api-redirect/...` 跳转链，`--resolve` 可解析成真实 URL（仅 GenAI 层需要）。

**用法**：
```bash
usearch "query"                  # 默认走降级链 (SearXNG 优先)
usearch -n 8 "query"             # 限源数
usearch --raw "query"            # JSON 输出 (text + urls + tier)
usearch --resolve "query"        # 深挖: 解析 GenAI 跳转链为真实 URL
usearch --genai "query"          # 强制跳过 SearXNG, 直接走 GenAI grounded（辅助层，慎用）
usearch --ddgs "query"           # 强制走 ddgs 兜底
```
环境变量：`SEARXNG_BASE`（默认 `http://localhost:8888`）、`GENAI_BASE`（默认 `http://localhost:5436`）。

**实现要点 / 踩过的坑**：
- SearXNG JSON 接口：`GET /search?q=<query>&format=json`，返回 `results:[{title,url,content}]`，**url 是真实落地页**。
- `ddgs -o json` **不打印 stdout 而是偷偷写文件**。改用 `from ddgs import DDGS` Python 库直调。
- `ddgs` 装在 `~/.local/bin/`，cron/非登录 shell 的 PATH 里可能没有 → 用库直调最稳。

## 深挖补全（deepdive）：从「综述」到「拿到真实机制+时间」

usearch 默认只给综述/链接列表。要拿到**真实的活动期間 + 机制细节**（建 calendar/入库用），需要"深挖"：
搜索 → 跟进真实落地页原文 → LLM 二次抽取。参考实现：competitor-news 项目 `src/deepdive.py`。

- **触发条件**（可配）：campaign 缺任一日期 OR 机制描述过短（< ~40 字）。
- **反复深挖**：每条最多用 N 个不同角度的查询（日期向 / 机制向 / 官方 prtimes 向），命中即停。
- **数据禁估算（铁律）**：深挖只填能从落地页原文**明确证实**的真值；拿不到精确日期就**留空**，标「期間未明示」——**绝不 ±N 天估算补全**。
- **证据留痕**：抽取时一并返回 `evidence`（源 URL + 原文引文片段），便于人工核验。
- **预算控制**：每轮全局上限（competitor-news 设 60 条），超预算放弃，防 cron 超时。
- SearXNG 作 L1 后，深挖源质量更硬（常直接命中官方新闻稿，如 `prtimes.jp`），优于聚合返利站。

## ⚠️ 致命坑 + 根治：Cerberus 隧道 idle 自停 → 对话/搜索偶发 "failed after retries"

**现象**：一段时间没活动后，下一条请求偶发 `The model provider failed after retries`，再发一条又好了。

**根因**（cerberus 日志实锤）：Cerberus 有空闲休眠——`Idle session detected`。请求落在 idle 唤醒/重握手窗口期（1-2s），此时隧道返回连接错误或 502/503。而 **proxy 旧代码只对 429 重试，对连接错误/5xx 直接放弃** → 报错。**关键**：cerberus 的 `/health` 探测**不算活跃使用**，每分钟 ping health 也阻止不了 idle。

**根治（双管齐下，治本 + 兜底）**：

1. **保活进程**（治本）`~/.hermes/scripts/genai_keepalive.sh`
   - 每 40s 打一次**真实 1-token** `generateContent`（`gemini-2.5-flash`，`maxOutputTokens:1`）→ session 永不 idle。
   - `flock` 单实例；cron **每分钟自愈** + `@reboot` 兜底 → durable、跨会话、抗 reboot。
   - 必须显式 `export SSH_AUTH_SOCK=/var/lib/devpod/ssh/active_ssh_auth_sock`（cron 不继承登录 shell env，否则 Cerberus no suitable auth）。

2. **proxy 重试覆盖瞬时错误**（兜底竞态窗口）`genai_proxy.py`
   - `HTTPError` 重试条件从 `e.code == 429` 扩到 `e.code in (429, 502, 503)`。
   - `URLError`（连接层错误）也重试（退避 1.5s/3s）。
   - 注意 `except HTTPError` 必须在 `except URLError` 之前（前者是后者子类）。

> 不做保活 = 隧道反复 idle 拉锯，用户偶发掉线手动恢复；做了保活 = 永不 idle，proxy 重试再兜住极端竞态。两者都上才是真 durable。
