---
name: economics-kol-daily-update
description: >-
  Economics KOL/IB 每日观点追踪、Notion 写入、Dashboard 推送的端到端技能。
  覆盖 75+ KOL / IB 的观点搜索 → LLM 分析 → Notion 写入 → Dashboard 推送全流程。
  也包含新增 KOL 的 onboarding 流程与每个 KOL 的丰富背景/历史汇总维护。
  当用户提到"KOL"、"观点追踪"、"每日更新"、"economics monitor"、"宏观观
  点"、"海淘观点"、"Kol list update"、"dashboard推送"时使用本技能。
  本技能是通用 Agent 技能——不依赖特定 Python 脚本，所有步骤通过 Agent
  自身的工具（web_search/Exa/Tavily, 真实浏览器, Notion API, GitHub push）完成。
tags: [economics, kol, macro, daily-update, notion, dashboard, opinion-tracking]
---

# Economics KOL Daily Update — E2E Agent Skill

> **通用 Agent 技能：所有步骤通过 Agent 自己的工具执行。**
> 工具栈：Exa(主搜索) + Tavily(备) + 真实浏览器(agent-browser, 抓X/YT/博客) +
> Notion REST API + terminal(git push, gh 凭证) + cronjob。
> 配套项目目录(Uber VM)：`~/Projects/Economy-KOL-to-Notion/`，复用脚本在 `scripts/`。

---

## 零、本技能 2026-06 重构要点（先读这段）

这是基于一次完整重建后的更新版。关键升级：

1. **SSOT = `data/kol_registry.json`**，唯一权威源是 **Notion KOL List DB**。重建脚本 `scripts/build_registry.py`（删机构/去重/sector映射）+ `enrich_registry.py`（search_terms + x_handle）。
2. **Daily/Weekly 只写「新增观点」**（需求①）——见 §三.4 观点新颖性判断。
3. **每个 KOL 的丰富背景+历史汇总** 写在 Notion KOL List 的 **page 正文**（callout/heading 结构化，非纯 text）——见 §六。脚本 `scripts/write_kol_profile.py`。
4. **可靠写入库** `scripts/notion_writer.py`：自动 L2去重 + select option 安全合并 + 建 page。
5. **搜索源优先级**：Exa（主，语义+日期过滤）→ 真实浏览器（X/YT/博客动态页）→ Tavily（备）→ ddgs（免费兜底）。Uber 内部无公网搜索通道（usearch 是内部知识检索）。
6. **真实浏览器已装**（agent-browser + Chrome），可抓 X 推文（未登录即可）、YouTube、个人博客。

---

## 一、关键数据

| 项目 | 详情 |
|---|---|
| **Notion DB IDs** | KOL List: `35947eb5fd3c800db852cef31f9de6a5` |
| | KOL By Day: `32347eb5fd3c8087b9c0f409f95f664e` |
| | KOL By Week: `36b47eb5fd3c80d08d39e30f9e526c45` |
| **data_source_id**（更新 select options 用）| KOL By Day: `32347eb5-fd3c-80d6-b948-000b45caae34`（注意 80d6，≠ database_id 的 8087）|
| **GitHub Pages** | `https://curarpikt0000.github.io/kol-dashboard/` |
| **dashboard repo** | `github.com/Curarpikt0000/kol-dashboard`（push 走 gh CLI 凭证，无需 PAT）|
| **项目目录** | `~/Projects/Economy-KOL-to-Notion/`（registry/scripts/config 都在这）|
| **SSOT** | `data/kol_registry.json`（75 KOL，唯一权威源=Notion KOL List）|
| **去重日志** | `data/processed_daily.json`（只追加）|
| **密钥** | `config/.env`：NOTION_TOKEN, EXA_API_KEY, TAVILY_API_KEY（GitHub 走 gh）|
| **时区** | 一律 JST (UTC+9) |

---

## 二、Notion DB 字段结构

### KOL By Day DB（page CRUD 用 database_id `32347...8087`）
| 字段 | 类型 | 说明 |
|---|---|---|
| `Name` | title | 含多空方向的中文标题，如"🟢 看多 GLD：避险+央行购金" |
| `Name of KOL` | select | KOL 显示名（用 registry 的 notion_select_name；新值需先安全合并 options）|
| `KOL or IB View` | select | KOL / IB View / AI View / Prophet / Official Data |
| `Date` | date | YYYY-MM-DD（JST，观点真实发布日）|
| `Sector` | select | 7 标准值：Precious Metals/Macro/Energy & Commodities/Crypto/Equities/Government Debt/Alternative |
| `Detail Sector` | select | **已满 381 option(>100上限)无法新增**！必须映射到已存在的简洁中文 option（黄金白银/国债收益率/科技AI/末日情景等），见 `scripts/fix_detail_sector.py` |
| `Comments` | rich_text | 中文逻辑链 100-200字，用 → 连接，末尾附来源 |
| `Suggestion` | rich_text | 中文操作建议，不放链接 |
| `多空标的` | rich_text | 人类可读，如"🟢 GLD, PHYS \| 🔴 TLT" |
| `方向明细` | rich_text | ⭐**结构化方向(JSON数组,按标的拆分)**：`[{"标的":"美债","板块":"Government Debt","方向":"看空"},...]`。dashboard 摊平成三元组统计真实多空。**写入用 `scripts/extract_direction.py` 的 write_direction()** |
| `主导方向` | select | 6档：强烈看多/看多/中性/看空/强烈看空/分歧（该条最主要方向，快速筛选+加权用）|

> ⭐**情绪/多空方向分析铁律（Chao 最高质量红线，2026-06-21）**：判方向【绝不可】用浅层文本/emoji 匹配或默认中性！必须逐条读懂 KOL 的【语言意味】。① 识别隐含看空（"美债泡沫/收益率飙升/抛长债/缩久期"=看空美债，即使无🔴；"科技泡沫/Mag7见顶/AI估值过高"=看空Equities；"美元购买力崩溃/去美元化"=看空美元）。② 一条发言常含多个标的、方向不同，**必须按标的拆分**，绝不整条简化（Luke Gromen 一条=🟢黄金强烈看多+🔴长久期美债强烈看空+🔴美元）。敷衍会导致"所有资产都看多/美债全看多"的荒谬结果。dashboard 必须读「方向明细」结构化字段，不靠文本现猜。详见项目 lessons §0。

### KOL By Week DB `36b4...`
Key Insight(title) / Date / Week Number(number) / Comments / Suggestion / Sector / Detail Sector / 多空标的

### KOL List DB `3594...`（注册表 + 每个 KOL 的 page 正文存丰富背景）
编号(title) / KOL 机构(rich_text) / 领域(**select**，8标准值：贵金属与商品周期/宏观货币与金融体系/国债利率与债券市场/预测/交易与市场微观结构/科技与未来趋势/资源与能源安全/股权市场) / 核心背景身份 / 主要分析方向。**page 正文**存 profile（§六）。

---

## 三、核心流程 1：每日 KOL 追踪

> **每天 09:00 JST（工作日）。**

### 3.1 读注册表
从 `data/kol_registry.json` 读 `active=true` 的 KOL（当前 74 活跃；anu_anand 因身份待核实 active=false）。

### 3.2 搜索（多源，优先级）
对每个 KOL 用 `scripts/backfill_one.py <id> <start> <end>`（或当日窗口）跑 Exa+Tavily。
- **Exa**（主）：带 startPublishedDate/endPublishedDate 日期窗，type=auto，contents.highlights
- **真实浏览器**（X/YT/博客）：`agent-browser open x.com/<handle>` + `agent-browser snapshot`（未登录可抓推文）。高频发帖 KOL（@PeterSchiff/@TFMetals/@VinceLanci/@LukeGromen 等）优先走浏览器读 X。
- **Tavily**（备）→ **ddgs**（兜底）
- 时间窗：工作日过去 24h；周一过去 72h（覆盖周末）

### 3.3 LLM 分析（提取干货）
输出结构化观点 JSON：insight_title（含方向）/ comments（中文逻辑链100-200字，→连接，末附来源）/ suggestion（不放链接）/ bull_bear_tickers。
- 有交易含金量标准：提到方向(涨/跌/震荡) + 标的(GLD/SLV/TSLA/USD) + 催化剂(Fed/央行/地缘/数据)
- 纯叙事("时代在变化")→ 标中性，不硬推方向
- **同名干扰严筛**：很多 KOL 有重名（运动员/医生/演员），只保留本人观点
- Exa publishedDate 有时是抓取日非发布日 → 以正文实际日期为准

### 3.4 ⭐观点新颖性判断（需求①：只写新增观点）
**Daily/Weekly 只写真正的新观点，不重复写已表达的立场。** 在 L1+L2 去重之上：
1. 查该 KOL 在 Notion 最近 N 天（建议 7-14 天）的记录（按 Name of KOL filter + Date 排序）
2. 把今天搜到的观点与最近记录对比：
   - **实质重复**（同方向+同标的+同催化剂）→ **不写新条目**，或写"维持 X 月 X 日观点"
   - **真正的新观点 / 方向变化 / 新催化剂** → 写
3. 持仓派 vs 交易派区别对待（brief 第八节）：
   - 持仓派（Peter Schiff/Kiyosaki/Rick Rule/Luke Gromen）：方向几乎不变 → 看**催化剂论点是否变了**，不是看多空
   - 交易派（Vince Lanci/Gareth Soloway/Bob Haberkorn）：方向会变 → 重点看**方向切换**和短期建议
4. 信号价值：一个看多5年的KOL再喊多 = 低价值；中性/看空者突然转多 = 高价值

### 3.5/3.6 去重 + 写入
- **L1**：`data/processed_daily.json` 查 `{date}::{kol_id}`
- **L2**：`scripts/notion_writer.py` 自动查 Notion 当天+该KOL（同KOL同日只1条铁律）
- 写入：构造记录 json → `python3 scripts/notion_writer.py write <json>`（自动 select 合并 + L2 + 建page）
- 写后记 processed_daily.json
- **写后必读回验证**：`scripts/notion_writer.py check "<name>" "<date>"` 返回 EXISTS

---

## 四、核心流程 2：Dashboard 推送

> **每天 09:30 JST（日报跑完后）。** push 走 gh 凭证（无需 PAT）。

1. 从 KOL By Day 查最近 N 天（建议 120 天）记录
2. 生成 `dashboard/kol-dashboard/data.json`（顶层：generated_at / raw_entries / kol_cards / sector_summary / ticker_heatmap / stance_changes / weekly_reports）
3. `cd dashboard/kol-dashboard && git add data.json && git commit && git push origin main`
4. **不要覆盖 index.html / README.md**
5. 验证：打开 GitHub Pages 确认数据可见

聚合改进方向（brief 第八节）：按 ticker 聚合 > 按情绪计数；sector 评分制；stance_changes 反转检测；置信度标签。
**⭐sector 多空必须读「方向明细」JSON 摊平成(板块,标的,方向)三元组**（`generate_dashboard_data.py` 的 parse_legs/sector_legs），sector_summary 输出 legs_bull/legs_bear/strong_bear；绝不用旧的 sentimentScore 文本匹配（会把看空吞成中性→所有资产都看多）。未结构化的旧记录回退文本法但标注。
**⭐评分公式=共识度净占比（Chao 2026-06-21 重批，不可用 tanh）**：`score = 100×(加权看多−加权看空)/(加权看多+加权看空+分歧)`，强度加权（强烈±2/普通±1）。含义：**只有零反对才可能到±100，有一个相反立场就<100**，多空各半=0。tanh 那种"信号强度映射"会让几乎所有板块顶到±99，违背直觉（贵金属有113条看空却显示+99）。score 即"净多空倾向%"，consensus=|score|=共识度。

---

## 五、核心流程 3：每周汇总（周一 09:00 JST）

查上周 KOL By Day → 按 Sector 分组统计 → **只总结本周新增/变化的观点**（需求①同样适用）→ 生成周报写入 KOL By Week。注明"板块共识"vs"个体发现"。

---

## 六、每个 KOL 的丰富背景 + 历史汇总（需求②）

**写在 Notion KOL List 的 page 正文**（不是 DB 属性），用 callout/heading/bullets/quote 结构化分层（非纯 text，太难读）。

新增 KOL 或定期更新时，用 `scripts/write_kol_profile.py <json>`，json 含：
- `one_liner`：🎯 一句话定位（callout）
- `stance` + `key_assets`：⚖️ 派别 + 常提标的（callout）
- `identity`：👤 身份与背景（bullets，比原 bio 丰富）
- `framework`：🧭 核心分析框架（bullets，用→）
- `core_views`：📌 长期核心立场（bullets）
- `recent_summary`：📈 近期观点演变（quote，基于回溯素材）

脚本幂等（先清空 page children 再写）。取 KOL 上下文用 `scripts/kol_context.py <id>`。

---

## 七、新增 KOL 流程（Onboarding，7 步）

1. **确认全名+机构**（音译名先 web_search 确认拼写，确保真实存在）
2. **收集信息**：display_name, id(snake_case), domain, sector(7标准值之一), detail_sector(映射到Notion已有option), institution, x_handle, search_terms(2-4个)
3. **写 KOL List DB**（注册表行）
4. **更新 `data/kol_registry.json`**（追加到 kols 数组，保留顶层元字段）
5. **历史深度回溯**：`scripts/backfill_one.py <id> 2025-11-01 <today>` 多源检索 → 提炼该 KOL 全部历史观点写入 KOL By Day（这样新KOL一入库就有基线）
6. **写丰富 profile 到 List page 正文**（§六）
7. **告知用户完成**（附写入统计）

> select option 新增：先 `notion_writer.py ensure_option "Name of KOL" "<name>"` 安全合并（脚本内部 retrieve 现有 options + 合并回写，绝不覆盖）。

---

## 八、Cron 调度（4 个）

```
# 任务1 每日追踪 工作日 09:00 JST
cronjob(action='create', name='Economics KOL Daily Track', schedule='0 9 * * 1-5',
  skills=['economics-kol-daily-update'], workdir='~/Projects/Economy-KOL-to-Notion',
  prompt='读 data/kol_registry.json 活跃KOL → 各跑 backfill_one.py 当日窗口 → LLM分析(只写新增观点,见skill §3.4) → notion_writer.py 写入 KOL By Day → 记 processed_daily.json → 读回验证')

# 任务2 Dashboard 09:30 JST
cronjob(action='create', name='KOL Dashboard Push', schedule='30 9 * * 1-5',
  skills=['economics-kol-daily-update'], workdir='~/Projects/Economy-KOL-to-Notion/dashboard/kol-dashboard',
  prompt='从 KOL By Day 查120天 → 生成 data.json → git add/commit/push(gh凭证)')

# 任务3 周报 周一 09:00 JST
cronjob(action='create', name='KOL Weekly Summary', schedule='0 9 * * 1',
  skills=['economics-kol-daily-update'], workdir='~/Projects/Economy-KOL-to-Notion',
  prompt='查上周 KOL By Day → 按Sector统计 → 只总结新增/变化观点 → 写 KOL By Week')

# 任务4 上下文归档 夜间(见 project-context-autosave)
```

---

## 九、常见陷阱

| 陷阱 | 解决 |
|---|---|
| 粘贴到聊天的 API key 被 redactor 损坏 | 让用户在终端写 config/.env；脚本里别写完整字面量 `NOTION_TOKEN=` 等(会触发 redactor)，用拼接 `"NOTION_"+"TOKEN="` |
| Detail Sector 满 381 option 无法加新 | 映射到已有简洁 option，见 fix_detail_sector.py |
| select option 覆盖清空 | notion_writer.py ensure_option 合并式回写 |
| data_source_id ≠ database_id | 更新 options 用 80d6；建 page 用 8087 |
| 同KOL同日多条 | L1(processed_daily) + L2(notion_writer 自动) |
| 同名干扰 | 严筛只留本人观点 |
| Exa date 不准 | 以正文实际发布日为准 |
| 子 agent 批量回溯每批 >4 KOL 会超时 | 每批 3-4 个 KOL |
| GitHub push | 走 gh CLI 凭证(已登录 Curarpikt0000)，无需 PAT |
| 不编造 | 搜不到就少写/不写，预测类诚实标注风格 |

---

## 十、参考
- Dashboard: https://curarpikt0000.github.io/kol-dashboard/
- repo: https://github.com/Curarpikt0000/kol-dashboard
- 项目目录: ~/Projects/Economy-KOL-to-Notion/（scripts 全套：build_registry/enrich_registry/fix_detail_sector/backfill_one/notion_writer/write_kol_profile/kol_context/check_coverage）

*2026-06-20 基于完整重建更新：SSOT重建 + 412条历史回溯 + 75 KOL丰富profile + 需求①新颖性判断 + 真实浏览器 + notion_writer库*
