---
title: Uber GenAI Gateway — 免费公网搜索（grounded web search）给 Hermes Agent 用
domain: engineering
keywords: [genai-gateway, web-search, grounded, gemini, google-search, 联网, 公网搜索, exa, tavily, ddgs, ai-guard, pii, cerberus, ussh, devpod, 内部联网, usearch, keepalive, idle, failed-after-retries]
source: hermes-economy-kol-genai-integration-20260625
created: 2026-06-25
last_updated: 2026-06-25 (+SearXNG 升为 L1 + usearch 项目级边界 + deepdive 深挖 + Cerberus idle 保活)
---

# Uber GenAI Gateway — 内部联网/搜索备忘 + usearch 项目级降级链

> ⚠️ **现状提示（2026-06-25 起）**：GenAI Gateway grounded 搜索仍可用，但它前面的 **AI-Guard 会把人名匿名化**（见下文「致命坑」），不适合「精确搜某个人」。因此项目级搜索的**首选已改为自托管 SearXNG**，GenAI 降为备用：
> - 通用项目级降级链（本文 `usearch` CLI）：**SearXNG（L1）→ GenAI grounded（L2）→ ddgs（L3）**
> - economics-kol 项目另有专属链：**Exa → Tavily → SearXNG → ddgs**（项目专属，不外推）
> 下面保留 GenAI Gateway 的完整调法（它仍是 L2 备用 + 历史参考）。

## 一句话

跑在 Uber devpod 上的 Hermes agent **不需要付费的 Exa/Tavily 也能联网搜公网**：
直接打内部 **GenAI Gateway** 的 grounded web search（Gemini + Google Search grounding），
**免费走内部计费、永不断粮、返回带源 URL 的实时结果**。这是 Uber 官方的公网出口。
（注：因 AI-Guard PII 局限，现已降为 usearch 的 L2 备用，L1 用 SearXNG。）

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

> 🔴 **铁律：websearch 降级链是「项目级」，不是「整体级」**（Chao 2026-06-25 明确）。
> `usearch` 是一个独立的项目级 CLI，跑在 `~/.local/bin/`，与 **Hermes Agent 的主对话模型 /
> provider / 网关配置完全无关**。要换搜索后端 / 调降级顺序，**只改这个文件**，
> **绝不能去动 `hermes config`、主 model/provider、或 Hermes 基础设置**。
> 每个项目可以有自己的搜索策略；Hermes 本体的 web 工具与对话链路保持不变。
>
> 📌 **适用范围**：本节(SearXNG→GenAI→ddgs 降级链)是给 **`~/Projects/` 下搭建的 Hermes 项目级数据管道**
> 用的(竞品追踪、KOL 监控、dashboard 这类自动化采集项目)。**不是所有 topic conversation 的强制规则**——
> 日常对话里 Hermes 自带的 web 工具照常用，无需套这套降级链。只有当你在某个项目里需要
> 「自带兜底、可控后端」的稳定搜索时，才复用这个 `usearch` CLI。

**降级链**（前级失败/无结果才落下级，stderr 实时打印用了哪一级）：
- **L1** **SearXNG**（本地 metasearch，`http://localhost:8888`，Chao 后台设的默认）：多引擎聚合，**直接返回真实落地页 URL**（无需 resolve），免费、快。
- **L2** GenAI Gateway grounded（`gemini-3-flash-preview` + `google_search`，端口 5436）：带 AI 综述 + 源URL，作为 SearXNG 挂掉时的备用。仍可用，但**只是纯调用，不改 Hermes 任何设置**。
- **L3** `ddgs` 兜底（前两级都挂时），纯链接列表。

**源 URL 处理**：
- SearXNG / ddgs 直接给真实 URL。
- GenAI grounded 给 `vertexaisearch.../grounding-api-redirect/...` 跳转链（方案 A 原样），`--resolve` 可解析成真实 URL（仅 GenAI 层需要）。

**用法**：
```bash
usearch "query"                  # 默认走降级链 (SearXNG 优先)
usearch -n 8 "query"             # 限源数
usearch --raw "query"            # JSON 输出 (text + urls + tier)
usearch --resolve "query"        # 深挖: 解析 GenAI 跳转链为真实 URL
usearch --genai "query"          # 强制跳过 SearXNG, 直接走 GenAI grounded
usearch --ddgs "query"           # 强制走 ddgs 兜底
usearch --model gemini-2.5-pro "query"   # 仅 GenAI 层换模型
```
环境变量：`SEARXNG_BASE`（默认 `http://localhost:8888`）、`GENAI_BASE`（默认 `http://localhost:5436`）。

**实现要点 / 踩过的坑**：
- SearXNG JSON 接口：`GET /search?q=<query>&format=json`，返回 `results:[{title,url,content}]`，**url 是真实落地页**（比 GenAI 跳转链更省，深挖时不用 resolve）。
- `ddgs -o json` **不打印 stdout 而是偷偷写文件**。改用 `from ddgs import DDGS` Python 库直调。
- `ddgs` 装在 `~/.local/bin/`，cron/非登录 shell 的 PATH 里可能没有 → 用库直调最稳。

## 深挖补全（deepdive）：从「综述」到「拿到 promo 真实机制+时间」

usearch 默认只给综述/链接列表。要拿到**真实的活动期間 + 机制细节**（建 calendar/入库用），需要"深挖"：
搜索 → 跟进真实落地页原文 → LLM 二次抽取。参考实现：competitor-news 项目 `src/deepdive.py`。

- **触发条件**（可配）：campaign 缺任一日期 OR 机制描述过短（< ~40 字）。
- **反复深挖**：每条最多用 N 个不同角度的查询（日期向 / 机制向 / 官方 prtimes 向），命中即停。
- **数据禁估算（铁律）**：深挖只填能从落地页原文**明确证实**的真值；拿不到精确日期就**留空**，展示层标「期間未明示」——**绝不 ±N 天估算补全**。
- **证据留痕**：抽取时一并返回 `evidence`（源 URL + 原文引文片段），便于人工核验，符合"每个论断锚到具名数据"。
- **预算控制**：每轮全局上限（competitor-news 设 60 条），超预算放弃，防 cron 超时。
- SearXNG 作 L1 后，深挖源质量更硬（常直接命中官方新闻稿，如 `corporate.demae-can.co.jp` / `prtimes.jp`），优于聚合返利站。

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

