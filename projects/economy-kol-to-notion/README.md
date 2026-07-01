# Economy-KOL-to-Notion — 项目逻辑、进展与新 Agent 接手指南

> 服务对象：Uber Eats Japan GR（Grocery & Retail）运营团队（Chao Jin / Sr Operations Manager, Japan Merchandising）。
> 本目录是**通用知识沉淀**（代码 + 文档 + 接手指南），不含 KOL 言论数据、Notion 快照、密钥（IP 红线 + 安全铁律）。
> 实际可运行的工程在 VM `~/Projects/Economy-KOL-to-Notion/`，数据在私人 Notion + 本地 `data/`。
> 最后更新：2026-07-01（JST）。

> 🔧 **运维/自动化如何运转**：见 [`ops/RUNBOOK.md`](ops/RUNBOOK.md) —— 每日时序、6 个 cron 逐一说明、更新顺序、数据流机制、如何在新环境重建。配套 `ops/cron-jobs.json`（可直接重建的 cron 定义）+ `ops/*.sh`。

---

## 0. 一句话定位

**自动监控约 76–86 位经济/宏观/贵金属 KOL 每天的新观点 → LLM 中文逻辑链分析（按标的拆多空腿、判期限）→ 写入 Notion 三层 DB → 推 GitHub Pages dashboard（共识度 + 短期/长期雷达图）→ 周报。**

核心价值：把散落在 Kitco/X/YouTube/财经媒体的 KOL 言论，结构化成"谁、对什么标的、看多还是看空、短期还是长期、逻辑链是什么"，让运营团队一眼看清市场 KOL 共识与分歧的时间结构。

---

## 1. 数据架构（三层 Notion DB）

| DB | database_id | 粒度 | 说明 |
|---|---|---|---|
| **KOL List**（registry 权威源） | `35947eb5fd3c800db852cef31f9de6a5` | 每 KOL 一行 | SSOT；`Name of KOL` 是 **select** 类型；机构不算 KOL |
| **By Day** | `32347eb5fd3c8087b9c0f409f95f664e` | 每 KOL 每天一行 | 核心分析表；含方向明细 JSON |
| **By Week** | `36b47eb5fd3c80d08d39e30f9e526c45` | 每周一行 | 全市场综合周报 |

> data_source_id（用于 select option 读写）：By Day = `32347eb5-fd3c-80d6-b948-000b45caae34`。建 page 用 database_id，改 select options 用 data_source_id。

**By Day 关键属性**：
- `Name of KOL`（**select**，不是 rich_text/title — 读取时易踩坑）
- `Comments`（rich_text）— KOL 当天言论 + 中文逻辑链
- `方向明细` / `direction_detail`（rich_text 存 **JSON 数组**）— 每个 leg 含 `标的`/`板块`/`方向`/`期限`
- `主导方向`（select 6 档：强烈看多/看多/中性/看空/强烈看空/分歧）
- `多空标的`、`Suggestion`、`Sector`、`Detail Sector`

**方向明细 JSON 结构（一条发言按标的拆多个 leg）**：
```json
[
  {"标的":"黄金","板块":"Precious Metals","方向":"看多","期限":"长期"},
  {"标的":"长久期美债","板块":"Macro","方向":"强烈看空","期限":"短期"}
]
```

---

## 2. 数据流（端到端管道）

```
KOL registry (data/kol_registry.json, SSOT 镜像 KOL List DB)
   │
   ▼ scripts/backfill_one.py  (单 KOL 多平台搜索 + 6 层降级链)
   │   L1 Exa → L2 Tavily → L3 SearXNG → L4 ddgs → L5 Google News RSS → L6 playwright/Bing → 报警
   ▼
原始言论 (data/daily/, data/backfill/)
   │
   ▼ 子 agent 逐条读懂语义 → 判方向 + 按标的拆腿 + 判期限
   │
   ▼ scripts/extract_direction.py / add_term.py  (结构化方向 + 期限)
   ▼ scripts/notion_writer.py  (幂等去重 + select 合并 + 建 page + 防污染护栏)
   │
   ▼ Notion By Day
   │
   ├─▼ generate_dashboard_data.py → data.json → push GitHub Pages (短期/长期雷达图)
   └─▼ write_week_report.py → Notion By Week (周报)
```

**Dashboard 线上**：https://curarpikt0000.github.io/kol-dashboard/
（独立 git repo `curarpikt0000/kol-dashboard`，不嵌在本项目 repo 里。）

---

## 3. 搜索栈（6 层降级链，关键工程）

主力 = **SearXNG**（`http://localhost:8888/search?format=json`，用户维护，**严禁改其配置**）。
完整降级链（`scripts/backfill_one.py`）：

1. **Exa**（最强，带日期/质量高，要钱，余额会尽）
2. **Tavily**（已废，超额返 0）
3. **SearXNG**（免费/搜得到人/无结构化日期/偏档案页）
4. **ddgs**（内置 web_search 免费兜底）
5. **Google News RSS**（`news.google.com/rss/search` 纯 HTTP 不反爬，自带 pubDate — 终极独立兜底）
6. **playwright → Bing**（最后手段）

踩坑（见 lessons.md §10）：
- Google `/search` 裸抓必弹反爬验证页 → 用 News RSS 代替。
- 假 L5（经 SearXNG 的 Google）= L3 同源非独立，已删。
- X/YouTube 游客可抓（无需登录，避免封号），但实质依赖 google 引擎（限流单点风险）。
- Uber 网关不透传 Claude Code WebSearch；aifx MCP 下无公网搜索工具 → 没有现成"内部独立兜底"。

---

## 4. ⭐ 三条最高优先级铁律（违反会被 Chao 反驳）

### 铁律 1：情绪/多空方向**绝不浅层文本匹配**
- 必须 LLM **读懂语言意味**，**一条发言按标的拆多空腿**（同条可"看多金银 + 看空美债"）。
- 识别隐含看空：美债泡沫/收益率飙升/抛长债=看空美债；科技泡沫/Mag7 见顶=看空 Equities；美元购买力崩溃=看空美元。
- dashboard 读结构化字段而非现猜文本。（背景：早期浅层匹配导致"所有人都看多"被一眼识破，见 lessons §0）

### 铁律 2：期限按 **KOL 主观时间预期**判
- 短期 = KOL 认为 **3 个月内**会发生；长期 = >3 个月。锚点是他的主观预期，**非客观日历、非资产类别**。
- 同类资产短长可并存；信号词可重叠；靠 LLM 读懂不靠词表。

### 铁律 3：声称成功必须**自己读回验证**
- 子 agent 自报不算证据。写 Notion 后必须重新 query 确认真落地。
- 零编造：查不到标注"(推断)"+依据，不假装查过。
- 零遗漏：多源/多 DB 项目每个源、每个 DB 单独核对覆盖率（By Day 补了≠By Week 补了）。

---

## 5. ⚠️ 防脱敏污染架构（安全核心，务必理解）

**问题根源**：Uber redactor 在"工具输出展示给 agent"层把人名脱敏成 `ANONYMIZED_PERSON_X`，但**磁盘真实字节是正确人名**。若 agent 肉眼读原文再写回 → 把真名覆盖成占位符 → **永久损坏数据**。

**三条防线**：

1. **安全写回架构**（`add_term.py apply_terms`）：agent **只输出标签数组**（如 `["短期","长期"]`），**绝不经手原文**。脚本自己 urllib 重读真字节合并写回，多重校验（leg 数一致 + 标的/方向逐字段不变 + 无 ANONYMIZED）+ 写后读回。

2. **写入总闸**（`notion_writer.py`）：写 Notion 前 `json.dumps(props)` 全字段扫 ANONYMIZED，命中直接 `REJECTED_ANONYMIZED` 拒写。这是污染入口的拦截。

3. **每日体检 watchdog**（`purity_watchdog.py` + cron `econ-kol-purity-watchdog` JST 09:15）：扫 Notion + 本地，干净静默/污染告警。

**修复污染的正确姿势**（2026-06-30 清理过 Notion 4 处 + 本地 19 处）：
- 真名**只从 registry 磁盘字节读 或 hex 构造**（`bytes.fromhex(...).decode()`），绝不让明文人名经过 agent 输出（否则又被脱敏）。
- 锚点不足以确定真名 → delegate_task 子 agent 联网核实（只输出"占位符→真名+依据URL"映射，不改文件）。
- dry-run → apply → 读回 ANONYMIZED 真字节归零。
- 验证磁盘真字节：`python3 -c "print(open('f','rb').read().count(b'ANONYMIZED'))"`，**不要信工具显示层**。

> 已核实的固定发言人（机构→真名）：High Ridge Futures=David Meger / RJO Futures=Bob Haberkorn / Myrmikan=Daniel Oliver / Amplify ETFs=Nate Miller / 前JPM贵金属台=Robert Gottlieb / FxPro=Alex Kuptsikevich / FXStreet=Joshua Gibson。

**rewind 安全网**：开工前 `backup_direction_detail.py` 全量备份原始字节；出问题 `restore_direction_detail.py <backup> [page_id|--check]` 还原。

---

## 6. 核心脚本速查（scripts/）

| 脚本 | 用途 |
|---|---|
| `backfill_one.py` | 单 KOL 多平台搜索（6 层降级链） |
| `daily_search.py` | 每日增量搜索 |
| `notion_writer.py` | 写 By Day（幂等去重 + select 合并 + **防污染护栏**） |
| `extract_direction.py` | 方向明细结构化（list/next/count/write_direction） |
| `add_term.py` | 期限补全 I/O（list-kols/list/apply 安全写回/count/verify）；`_kol_of` 已支持 select |
| `backup_direction_detail.py` / `restore_direction_detail.py` | 全量备份 / rewind 还原 |
| `check_source_purity.py` | 体检 Notion 源（Comments + direction_detail 真字节扫描） |
| `purity_watchdog.py` | 每日污染体检 watchdog（干净静默/污染告警） |
| `fix_comments_names.py` / `fix_weekfiles_names.py` | 脱敏污染修复（Notion / 本地） |
| `audit_anon_entries.py` / `audit_anon_all.py` | 列出所有 ANONYMIZED 污染处 + 锚点 |
| `build_registry.py` / `enrich_registry.py` / `pull_kol_list.py` | registry 维护 |
| `export_week_entries.py` / `write_week_report.py` | By Week 周报回溯 + 写入 |
| `write_kol_profile.py` | KOL 画像写入 |
| `check_coverage.py` | 覆盖率核对 |

> 排除未 push 的脚本：`test_keys.py`/`write_keys.py`/`write_pat.py`（含密钥）、各种一次性 inspect/test 探查脚本。

---

## 7. Cron 作业（VM 上运行，本目录不含脚本本体）

| cron 名 | 调度（JST） | 作用 |
|---|---|---|
| Economics KOL Daily Track | 工作日 09:00 | 全量 KOL 采集 → 写 By Day |
| KOL Dashboard Push | 工作日 09:30 | 重生 data.json → push GitHub Pages |
| kol-dashboard-hourly-radar | 每小时整点 | 重生短期/长期雷达图（no_agent 纯脚本） |
| KOL Weekly Summary | 周一 09:00 | 生成周报 → By Week |
| econ-kol-purity-watchdog | 每日 09:15 | 脱敏污染体检（no_agent，干净静默） |
| Economy-KOL context-distill | 每日 | 上下文压缩归档 |

> 脚本本体在 `~/.hermes/scripts/`（kol_dashboard_hourly.sh, econ_purity_watchdog.sh 等）。
> 注意：`kol-dashboard-hourly-radar`/cron 调度按系统时区（VM 已设 Asia/Tokyo）。

---

## 8. 最新进展（截至 2026-06-30 JST）

**期限回填项目 100% 完成 + 数据纯净化 + 永久护栏：**
- By Day **2037 行 / 4970 多空腿全部有期限**（短 1843 / 长 3127），remaining=0，逐 KOL 核对零缺口。
- 短期/长期雷达图已揭示核心洞察：**股市短期 -40（看空）vs 长期 +36（看多）** — KOL 群体短期避险、长期看好的时间结构分化。
- **脱敏污染全清理 + 防复发**：发现并修复 Notion Comments 4 处 + 本地 week_backfill 19 处 ANONYMIZED 污染（采集阶段遗留，非回填造成；direction_detail 核心字段零污染）。加了写入总闸 + 每日体检 watchdog。

**期限判读分布合理性已抽查**（按 KOL 画像精准区分）：技术派偏短（Gareth Soloway 短75/长17）、体系论偏长（James Rickards 短21/长70）、外汇策略师偏短（Marc Chandler 短87/长14）。

---

## 9. 新 Agent 接手 Checklist（按顺序）

**开工前：**
1. `git pull` Generalrule（对账规则/Wiki/技能）。
2. 读本 README + `lessons.md`（全部踩坑）+ `AGENTS.original.md`（项目特有规则）。
3. 确认 `~/Projects/Economy-KOL-to-Notion/config/.env` 有有效密钥（NOTION_TOKEN 复用 Project-Competitor-News/.env；EXA_API_KEY/TAVILY 可能需轮换/充值）。
4. 健康检查：`python3 scripts/add_term.py count`（看 remaining）、`python3 scripts/purity_watchdog.py`（应静默）。

**日常维护：**
- 监控本项目 6 个 cron 的 last_status；error 要查（雷达图 cron 曾因 git noise 误判 error，已加固去 set -e）。
- 新增 KOL：先确认是真人非机构 → 加 Notion KOL List → 同步 `data/kol_registry.json`（只增不减）。
- 任何写 Notion 操作：走安全脚本（add_term/notion_writer），**绝不肉眼读原文再写回**。
- 充值/换 Exa key、Tavily key 写进 `config/.env`（绝不经聊天传、绝不进 git）。

**铁律红线（重复强调）：**
- Uber 数据/密钥**绝不进个人 repo**；本目录只放脱离 Uber 也成立的通用知识。
- 破坏性操作（删除/覆盖/push/重启/付费 API/发消息）**先停下确认**。
- 声称成功**必须自己读回验证**；零编造；零遗漏。
- 时间一律东京时间（JST, UTC+9）。

---

## 10. 已知待办 / 数据小瑕疵（见 lessons.md 详情）

- registry 个别身份待核对：郑博建→郑博见（拼写）；部分 KOL 空白期是真实数据分布非遗漏。
- By Week W11/W13「多空标的」字段稀疏（按零编造未强行机器拼凑，留待子 agent 真读补）。
- `kol-term-backfill-auto` cron 使命已完成（remaining=0），应清理避免空跑。
- agent-browser/Chrome 不持久化（devpod 重启会丢），需持久化方案。

---

*本指南随项目演进更新。踩坑沉淀见 `lessons.md`；满 30 条或稳定后升级到 Generalrule `wiki/`。*
