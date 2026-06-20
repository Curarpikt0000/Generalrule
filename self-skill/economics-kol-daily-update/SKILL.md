---
name: economics-kol-daily-update
description: >-
  Economics KOL/IB 每日观点追踪、Notion 写入、Dashboard 推送的端到端技能。
  覆盖 78+ KOL / IB 的观点搜索 → LLM 分析 → Notion 写入 → Dashboard 推送全流程。
  也包含新增 KOL 的 onboarding 流程。
  当用户提到"KOL"、"观点追踪"、"每日更新"、"economics monitor"、"宏观观
  点"、"海淘观点"、"Kol list update"、"dashboard推送"时使用本技能。
  本技能是通用 Agent 技能——不依赖特定 Python 脚本，所有步骤通过 Agent
  自身的工具（web_search, Notion API, GitHub push）完成。
tags: [economics, kol, macro, daily-update, notion, dashboard, opinion-tracking]
---

# Economics KOL Daily Update — E2E Agent Skill

> **通用 Agent 技能：所有步骤通过 Agent 自己的工具执行，不依赖特定 Python 脚本。**
> 你只需要 web_search / web_extract、Notion API 工具、terminal（用于 git）、
> 以及 cronjob 调度。

---

## 一、架构总览

本技能管理 E2E 流程：

```
KOL Register (kol_registry.json)
     │
     ▼  [每日 08:00 JST] ─────────────┐
  E2E_KOL_Daily_Run                   │
     │  搜索 → LLM 分析 → Notion 写入   │
     ▼                                  │
  KOL By Day (Notion DB)               │
     │                                  │
     ▼  [每日 08:30 JST]              │
  Dashboard Push                       │
     │  Generate data → Git push       │
     ▼                                  │
  GitHub Pages (kol-dashboard)         │
     │                                  │
     ▼  [每周一 09:00 JST]            │
  Weekly Summary → KOL By Week DB      │
                                        │
     ▼  [夜间 03:15 JST]              │
  Context Compression → context-log.md  │
                                        │
  (所有 4 个独立 KOL 监控 cron 也
   是同一个 08:00 批次的一部分)  ────────┘
```

### 关键数据：

| 项目 | 详情 |
|---|---|
| **Notion DB IDs** | KOL List: `35947eb5fd3c800db852cef31f9de6a5` |
| | KOL By Day: `32347eb5fd3c8087b9c0f409f95f664e` |
| | KOL By Week: `36b47eb5fd3c80d08d39e30f9e526c45` |
| **GitHub Pages** | `https://curarpikt0000.github.io/kol-dashboard/` |
| **本地 repo 路径** | `~/hermesagent/kol-dashboard/` |
| **数据源路径** | `~/hermesagent/Notion Metal Daily Update/`（读写） |
| **KOL 注册表** | `data/kol_registry.json`（SSOT，80 KOLs） |
| **去重日志** | `data/processed_daily.json`（只追加，永不删除） |
| **JST 时区** | 所有 cron 按 JST (UTC+9) 调度 |

---

## 二、数据引用：Notion DB 的字段结构

### KOL By Day DB（page CRUD 用 database_id）
**Database ID:** `32347eb5fd3c8087b9c0f409f95f664e`

| Notion 字段 | 类型 | 说明 |
|---|---|---|
| `Name` | **title** | 观点标题（含多空方向，如"🟢 GLD 看多，理由..."） |
| `Name of KOL` | **select** | KOL 显示名（新值自动创建） |
| `KOL or IB View` | select | KOL / IB View / AI View / Prophet / Official Data |
| `Date` | date | YYYY-MM-DD（JST） |
| `Sector` | select | Precious Metals / Macro / Energy & Commodities / Crypto / Equities / Government Debt / Alternative |
| `Detail Sector` | select | 根据 KOL 映射（见 kol_registry.json） |
| `Comments` | rich_text | 中文逻辑链，100-200字，用→连接，末尾可附来源 URL |
| `Suggestion` | rich_text | 中文操作建议，绝对不放链接 |
| `多空标的` | rich_text | 如"🟢 GLD, PHYS \| 🔴 TLT"（可选） |

### KOL By Week DB
**Database ID:** `36b47eb5fd3c80d08d39e30f9e526c45`

| 字段 | 类型 | 说明 |
|---|---|---|
| `Key Insight` | title | W号 + 核心结论 |
| `Date` | date | 周一日期 |
| `Week Number` | number | ISO 周数 |
| `Comments` | rich_text | DeepSeek 生成的板块中文周报（150-250字） |
| `Suggestion` | rich_text | 本周综合操作建议（无链接） |
| `Sector` | select | 本周主导板块 |
| `Detail Sector` | select | 本周主导细分板块 |
| `多空标的` | rich_text | 频次最高标的 |

### KOL List DB
**Database ID:** `35947eb5fd3c800db852cef31f9de6a5`

| 字段 | 类型 | 说明 |
|---|---|---|
| `编号` | title | 序号字符串，如"78" |
| `KOL / 机构` | rich_text | KOL 名字 |
| `领域` | rich_text | 领域分类 |
| `核心背景 / 身份` | rich_text | 机构/身份介绍 |
| `主要分析方向 / 监控维度` | rich_text | 分析方向 |

---

## 三、核心流程 1：每日 KOL 追踪（E2E_KOL_Daily_Run）

> **运行时间：每天 08:00 JST（工作日周一~周五）**
> **SKILL 搭配：不需要其他 skill，但不能缺少 web_search 工具**

### 3.1 读取 KOL 注册表

从 `data/kol_registry.json` 读取所有 `active=true`（或未设置 active 字段）的 KOL。
注：不要删除非活跃 KOL，保留在文件中（`active=false` 表示跳过的）。

### 3.2 搜索策略（关键）

对每个活跃 KOL，使用 `web_search` 搜索其 `search_terms` 中的关键词。搜索时：
- **用精确短语搜索**：每位 KOL 的名称必须用引号搜索
- **搜索范围**：最近 2-3 天
- **信源优先级**：
  1. Kitco News（贵金属方向）
  2. FXEmpire（外汇/贵金属）
  3. Reuters / Bloomberg（宏观事件）
  4. X/Twitter（KOL 本人发布）
  5. 各位 KOL 的个人博客/专栏
- **无内容时优雅处理**：搜索后确认真的没有新观点（检查 X、博客首页），然后写"今日无新公开观点"条目到 Notion

### 3.3 LLM 分析层

对搜索结果进行结构化分析，输出 JSON：

```json
{
  "insight_title": "含多空方向的观点标题（中文）",
  "comments": "中文逻辑链，100-200字，用 → 连接关键逻辑节点",
  "suggestion": "中文操作建议（绝对不放任何链接）",
  "bull_bear_tickers": "🟢 GLD, PHYS | 🔴 TLT（可选，没有就留空）"
}
```

**风格要求：**
- `comments`: 逻辑链条式，每步用→连接
- `suggestion`: 简洁的操作建议，不写"仅供参考"，不放链接
- 每次分析需引用搜索到的具体内容（如有），在 comments 末尾附来源名

### 3.4 去重检查（关键）

**L1 本地检查**：`data/processed_daily.json` 中是否有 `{YYYY-MM-DD}::{kol_id}` 的 key。
**L2 Notion 查询**：查询 KOL By Day 数据库中当天+该 KOL 的组合是否有记录。

> **铁律**：同一 KOL 同一天最多只写一条记录。去重 key 写入后立即记录，不等下一步。

### 3.5 Notion 写入

调用 Notion API 创建 page 到 KOL By Day DB。
字段映射见 §2。
关键字段映射：

- `Name` (title) → `insight_title`
- `Name of KOL` (select) → 从 kol_registry 读取 `notion_select_name`
- `KOL or IB View` (select) → 从 kol_registry 读取 `kol_or_ib`
- `Date` (date) → 今天日期 YYYY-MM-DD
- `Sector` (select) → 从 kol_registry 读取 `sector`
- `Detail Sector` (select) → 从 kol_registry 读取 `detail_sector`
- `Comments` (rich_text) → LLM 分析的 comments
- `Suggestion` (rich_text) → LLM 分析的 suggestion
- `多空标的` (rich_text) → LLM 分析的 bull_bear_tickers（可选）

### 3.6 记录去重日志

写入 `data/processed_daily.json`：
```json
{
  "YYYY-MM-DD::kol_id": true
}
```

---

## 四、核心流程 2：Dashboard 推送

> **运行时间：每天 08:30 JST（日报跑完后）**  
> **条件：日报必须先跑完**

### 4.1 查询 Notion 获取数据

从 KOL By Day DB 查询最近 N 天（建议 120 天）的所有记录：
- 用 Notion API 查询 database，过滤最近 N 天
- 获取所有字段：Name, Name of KOL, KOL or IB View, Date, Sector, Detail Sector, Comments, Suggestion, 多空标的

### 4.2 生成 data.json

**输出路径**：`~/hermesagent/kol-dashboard/data.json`

```json
{
  "generated_at": "2026-06-18 23:30 JST",
  "raw_entries": [/* 从 Notion 获取的所有原始记录 */],
  "kol_cards": [/* 聚合每个 KOL 的卡片 */],
  "sector_summary": [/* 按 sector 统计多空比例 */],
  "ticker_heatmap": [/* 被提及最多的标的 */],
  "stance_changes": [/* 检测 KOL 情绪反转 */],
  "weekly_reports": [/* 从 KOL By Week DB 读取周报 */]
}
```

**聚合逻辑：**
- `kol_cards`: 每个 KOL 一张卡，包含最近情绪（bull/bear/neutral）、Total entries、Sector 分布
- `sector_summary`: 7 个板块（Precious Metals, Macro, Energy & Commodities, Crypto, Equities, Government Debt, Alternative）的多空比例
- `ticker_heatmap`: 按 ticker 统计出现次数，含看多/看空计数
- `stance_changes`: 检测 KOL 最近 N 天与前 N 天情绪是否反转 (bull→bear 或 bear→bull)

### 4.3 Git Push 到 GitHub

```bash
cd ~/hermesagent/kol-dashboard
git add data.json
git commit -m "KOL dashboard data update $(date +%Y-%m-%d)"
git push origin main
```

---

## 五、核心流程 3：每周汇总（周一 09:00 JST）

### 5.1 查询上一周数据

从 KOL By Day DB 查询上周一 ~ 上周日的数据。
按 Sector 分组，统计各板块的多空比例。

### 5.2 DeepSeek 生成周报

输出 JSON：
```json
{
  "title": "W26 宏观周报 — 贵金属情绪偏多，政府债分歧加大",
  "sector": "Precious Metals",
  "detail_sector": "黄金白银",
  "comments": "150-250字中文周报，分板块总结",
  "suggestion": "本周综合操作建议（无链接）",
  "bull_bear_tickers": "频次最高的标的"
}
```

### 5.3 写入 KOL By Week DB

用 Notion API 在 `KOL By Week DB` 创建 page。

---

## 六、新增 KOL 流程（Onboarding）

当用户要求添加新 KOL 时，执行以下步骤：

### 6.1 收集信息

```
□ 中文显示名（display_name）
□ 英文全名（id 用 snake_case）
□ 所属领域
□ 机构/身份介绍
□ 主要分析方向（2-4 个维度）
□ X handle（如有）
□ 搜索关键词（2-4 个）
```

### 6.2 添加到 KOL List DB

用 Notion API 在 KOL List DB 创建 page：
```json
{
  "编号": { "title": [{ "text": { "content": "79" } }] },
  "KOL / 机构": { "rich_text": [{ "text": { "content": "Full Name" } }] },
  "领域": { "rich_text": [{ "text": { "content": "领域分类" } }] },
  "核心背景 / 身份": { "rich_text": [{ "text": { "content": "机构/身份" } }] },
  "主要分析方向 / 监控维度": { "rich_text": [{ "text": { "content": "方向" } }] }
}
```

### 6.3 写入本地注册表

追加到 `data/kol_registry.json` 的 `kols` 数组：
```json
{
  "id": "snake_case_id",
  "display_name": "Full Name",
  "notion_select_name": "Full Name",
  "domain": "贵金属",
  "sector": "Precious Metals",
  "detail_sector": "黄金走势",
  "kol_or_ib": "KOL",
  "institution": "机构名",
  "x_handle": "@handle",
  "search_terms": ["Full Name", "keyword2", "keyword3"],
  "active": true,
  "added_date": "2026-06-20",
  "sequence": 79
}
```

> **注意**：`kol_registry.json` 的顶层有几个元字段（`_comment`, `_last_updated`, `_sectors`），不要覆盖它们。KOL 列表在 `kols` 键下（数组格式）。

> **注意**：KOL 的 `sector` 必须是 7 个标准值之一：Precious Metals / Macro / Energy & Commodities / Crypto / Equities / Government Debt / Alternative。  
> `detail_sector` 使用已有的细分（可从注册表参考），不要随意新建。

### 6.4 NOTION 的 Name of KOL 字段

当在 notion KOL By Day 的 `Name of KOL` select 选项中选择了某个 KOL 名字，如果不存在该选项，则需要在 Notion 的数据源（Data Source Definition）中添加新的 select option。

请使用 Notion API 的 `retrieve_a_data_source` 来获取当前的 options 列表（data_source_id 是 `32347eb5-fd3c-80d6-b948-000b45caae34` — 注意这是 data_source_id 格式，不是 database_id），获取现有的 options 列表后，用 `update_a_data_source` 发送完整的新 options 列表（旧选项+新选项），否则旧选项会被覆盖。

**但注意**: data_source_id 和 database_id 不同。database_id（用于创建 page）是 `32347eb5-fd3c-8087-b9c0-f409f95f664e`，data_source_id（用于查询/更新 options）是 `32347eb5-fd3c-80d6-b948-000b45caae34`。

---

## 七、配置需求（首次部署）

### 7.1 环境变量

| 变量 | 说明 |
|---|---|
| `NOTION_TOKEN` | Notion Integration Token（需有读写 KOL 三个 DB 的权限） |
| `TAVILY_API_KEY` | Tavily Search API Key（主搜索源） |

### 7.2 项目结构（必须存在）

```
~/hermesagent/Notion Metal Daily Update/
├── config/
│   ├── .env                   ← NOTION_TOKEN, TAVILY_API_KEY
│   └── notion_ids.json        ← DB IDs（SSOT）
├── data/
│   ├── kol_registry.json      ← KOL 主注册表
│   └── processed_daily.json   ← 去重记录（空 {} 初始化）
├── scripts/                   ← （可选，本 skill 不依赖）
└── dashboard/                 ← （生成 data.json 的源目录）

~/hermesagent/kol-dashboard/
├── data.json                  ← Dashboard 数据文件
├── index.html                 ← Dashboard 前端（不要覆盖）
├── .git/                      ← GitHub Pages repo
└── README.md                  ← 项目简介
```

### 7.3 GitHub Pages 配置

Dashboard 部署在 GitHub Pages 上：
- **Repo**: `https://github.com/Curarpikt0000/kol-dashboard`
- **Branch**: main
- **本地 clone 到**: `~/hermesagent/kol-dashboard/`
- 需要具有 push 权限的 GitHub token 或 SSH key

首次设置：
```bash
cd ~/hermesagent/kol-dashboard
git remote -v  # 确认指向正确 repo
```

---

## 八、Cron 调度模板（首次部署用）

创建以下 cron jobs：

### 8.1 Daily KOL Tracker（工作日 08:00 JST）

```
cronjob(action='create',
  name='Economics KOL Daily Track',
  schedule='0 8 * * 1-5',
  prompt='运行 E2E KOL 每日追踪流程：读取 kol_registry.json 的活跃 KOL，搜索、分析、去重、写入 Notion KOL By Day DB。用 web_search 工具搜索每个 KOL 的最新观点。输出结果到 origin。',
  skills=['economics-kol-daily-update'],
  provider='<your_provider>',
  model='<your_model>')
```

### 8.2 Dashboard Push（工作日 08:30 JST）

```
cronjob(action='create',
  name='KOL Dashboard Push',
  schedule='30 8 * * 1-5',
  prompt='运行 KOL Dashboard 推送：从 Notion KOL By Day DB 查询数据 → 生成 data.json → git push 到 GitHub Pages repo。用 Notion API 读取数据。用 terminal 处理 git。',
  skills=['economics-kol-daily-update'],
  provider='<your_provider>',
  model='<your_model>')
```

### 8.3 Weekly Summary（周一 09:00 JST）

```
cronjob(action='create',
  name='KOL Weekly Summary',
  schedule='0 9 * * 1',
  prompt='运行 KOL 每周汇总：从 KOL By Day DB 查询上周数据 → 按 Sector 分组统计多空比例 → 生成周报 → 写入 KOL By Week DB。',
  skills=['economics-kol-daily-update'],
  provider='<your_provider>',
  model='<your_model>')
```

### 8.4 夜间上下文压缩（每天 03:15 JST）

```
cronjob(action='create',
  name='KOL Dashboard Nightly Context',
  schedule='15 3 * * *',
  prompt='运行 KOL 看板项目上下文压缩：用 session_search 搜索 KOL 相关会话 → 更新 docs/context-log.md 和 AGENTS.md 项目简介。',
  skills=['economics-kol-daily-update'],
  workdir='~/hermesagent/kol-dashboard',
  deliver='local')
```

---

## 九、致新 Agent：对接说明

### 9.1 你需要做的（首次部署）

1. **git clone** 本 repo（含 kol_registry.json 的完整副本）
2. 确认 `config/.env` 中有正确的 `NOTION_TOKEN` 和 `TAVILY_API_KEY`
3. **确认 Notion Integration 有权限**访问 3 个 DB（KOL By Day, KOL By Week, KOL List）
4. **创建 4 个 cron jobs**（参考 §8 模板）
5. **确认 GitHub Pages 有 push 权限**（SSH key 或 token）

### 9.2 搜索质量保障

- 主搜索源：Tavily（付费，quality 更高，费率限制更低）
- 降级方案：如果你没有 Tavily，使用其他 web_search
- 每位 KOL 至少搜 2 个关键词组合（含精确的人名搜索）
- 不要跳过「无新内容」的 KOL——写"今日无新公开观点"保持追踪连续性

### 9.3 常见陷阱

| 陷阱 | 解决方案 |
|---|---|
| Notion data_source_id ≠ database_id | 更新 select options 用 80d6 variant，创建 page 用 8087 variant |
| 同一 KOL 同一天写多次 | L1 检查 processed_daily.json → L2 查询 Notion 当天记录 |
| 搜索 API 限速 | 间隔 sleep，降级 web_search |
| Select options 覆盖 | 先 retrieve 所有现有 options，再 update 合并 |
| 新 KOL 的 notion_select_name 不存在于 KOL By Day 的 select 中 | 必须先 update data source 添加选项 |
| JST vs UTC 混淆 | 所有时间按 JST (UTC+9) |
| GitHub push 失败 | 检查 SSH key / token 是否有效 |

---

## 十、参考链接

- **KOL Dashboard**: https://curarpikt0000.github.io/kol-dashboard/
- **Notion Integration 管理**: https://www.notion.com/my-integrations
- **GitHub Repo**: https://github.com/Curarpikt0000/kol-dashboard

---

*文档创建：2026-06-20，基于原 Hermes KOL 追踪流水线重构为通用 Agent Skill*
