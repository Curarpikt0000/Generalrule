# 项目规则 (Project Rule)

> 本文件是**项目级约束**，在 `/Users/chaojin/Antigravity Projects/Generalrule/antigravity/general-global-rule.md` 的全局规则基础上叠加生效。
> 所有 AI Coding 工具（Antigravity / Claude Code / Cursor / Hermes）均自动识别本文件。
> 创建日期：2026-05-31

---

## §P1 项目基本信息

- **项目名称**：美债收益率和Fed中美日流动性日报
- **项目类型**：数据自动化 + LLM 分析 + Notion 看板
- **主要技术栈**：Python 3.11 + requests + DeepSeek API + FRED API + Notion MCP
- **部署环境**：Hermes（用户本机定时任务）
- **项目根目录**：`/Users/chaojin/hermesagent/US Debt and Fed Liquidity/美债收益率和Fed中美日流动性日报`
- **负责 Agent**（只有两个，不要再以为有第三个模型）：
  - **设计 / 修改 Notion 结构 / 写 workflow**：Claude（Cowork 模式）
  - **每日运行（抓数 + 写 Notion + 自己写分析）**：Hermes（后端 = DeepSeek）
- **架构核心**：Hermes 既是数据搬运工，也是分析师。它在 workflow 03 / 05 / 06 / 07 切换到 `hermes_analysis_prompts/` 里的"首席风控官"角色写报告。**没有外部独立的 DeepSeek 调用，所有 AI 行为都在 Hermes 内部完成。**

---

## §P2 技术栈特有约束

### 核心依赖版本锁定

```
requests>=2.31
python-dotenv>=1.0
beautifulsoup4>=4.12   # 仅 Investing/PBoC 反爬时用
```

### 禁用依赖

- **禁止用 Selenium / Playwright**：PBoC 是静态 HTML，FRED 是 API，不需要浏览器渲染；增加部署复杂度
- **禁止用 pandas**（除非数据量真的大）：30 天小数据用纯 list[dict] 就够
- **禁止用 LangChain / LlamaIndex**：DeepSeek 直接 `requests.post` 调用，3 行代码搞定，不要套框架

### 必须遵守的框架规范

- **所有 Notion 写入走 `notion_writer/client.py`**，不得直接在 workflow 里裸调 MCP
- **所有 FRED 调用走 `scrapers/fred_client.py`**
- **所有 API key 从 `config.py`（即 `.env`）读取**，禁止硬编码
- **所有 DB ID 从 `notion_db_ids.json` 读取**，禁止硬编码 UUID 到代码

---

## §P3 业务领域约束

### 核心业务规则

- **数据归一化**：每个时序 DB 一日一行（B5/B6/B7 资产负债表快照除外，按行月度/10日/周频）。**不得用 Notion markdown 表格代替 DB 行**
- **时区统一为 JST**（Asia/Tokyo）。所有 Date 字段用 ISO 字符串 `YYYY-MM-DD`，表示**JST 当日**（美东收盘日数据对应 JST 次日）
- **AI 短评 ≤ 200 字**，长分析放 page body
- **状态灯严格按 `config.py:THRESHOLDS` 计算**，不许 DeepSeek 自主"感觉应该"

### 数据流向约束

```
FRED/PBoC/BoJ 原始数据
    → scrapers/ 清洗 → list[dict] (JSON-serializable)
        → notion_writer/client.py 写入 Notion DB (A1-A7, B1-B7)
        → fetch 最近数据给 DeepSeek
            → DeepSeek 返回 JSON
                → 写入 A7（短评 + 长分析）
```

**禁止**：跳过 Notion，直接把 scraper 输出喂给 DeepSeek（会丢失历史回溯能力）。

### 已知的业务陷阱（必读）

1. **Hermes 后端不支持多模态**：所有给它的数据必须是 JSON / 纯文本。**不要发 PDF、图片、Notion view 链接**。
2. **FRED 周末/节假日返回 `.`**：fred_client.py 已过滤，但跨天计算 Δ 时要注意"上一个有效观测"。**并发拉多序列会 429**（L-2026-05-31-005）：单次调用后强制 `time.sleep(2)`，已加在 fred_client.py。
3. **PBoC 官网 GBK 编码**：BeautifulSoup 解析时需 `r.encoding = 'gbk'`。
4. **MoF Japan JGB CSV 英文站文件名是 `jgbcme.csv`（不是 jgbcm.csv）**（L-2026-05-31-004）。日文站才是 jgbcm.csv。
5. **Investing.com 反爬激进**：UA 池 + cookie + 5s 间隔不一定够；首选 MoF Japan 官方 API。
6. **Notion MCP 写入 Date 字段需要展开格式**：`"date:Date:start": "2026-05-31", "date:Date:is_datetime": 0`。
7. **Notion MCP 写入 page body 的 rich_text 格式有冗余 type 陷阱**（L-2026-05-31-008）：
   - 正确：`{"paragraph":{"rich_text":[{"text":{"content":"...","type":"text"}}]},"type":"paragraph"}`
   - 不要在外层 paragraph 和内层 text 之间再加多余的 `type` 包裹层，会触发 `validation_error`
8. **Select 字段必须严格匹配枚举**（含 emoji）。状态灯 `"🟢正常"` ≠ `"🟢"` ≠ `"正常"`。
9. **日本节假日 ≠ 中国节假日 ≠ 美国节假日**：跑批前需查 trading calendar。
10. **Hermes 偶尔返回非 JSON**：必须 try/except + 重试一次（temperature 降 0.1）+ 仍失败则 A7 写入"❌失败"。

---

## §P4 目录结构约定

```
美债收益率和Fed中美日流动性日报/
├── AGENTS.md                         # 本文件
├── PROPOSAL.md                       # 设计文档
├── README.md                         # 快速索引
├── config.py                         # 配置（从 .env 读取）
├── .env.example                      # 密钥模板
├── .env                              # 真实密钥（gitignore）
├── .gitignore
├── notion_db_ids.json                # 13 个 Notion DB 的 ID 索引
├── hermes_workflows/                 # Hermes 每日运行 prompt（7 个）
│   ├── 01_morning_us_data.md
│   ├── 02_morning_jgb_data.md
│   ├── 03_morning_ai_analysis.md
│   ├── 04_noon_china_japan.md
│   ├── 05_noon_ai_analysis.md
│   ├── 06_weekly_fed_h41.md
│   └── 07_monthly_cb_balance.md
├── scrapers/                         # 数据抓取
│   ├── fred_client.py                # ✅ FRED API（含 429 速率保护）
│   ├── mof_jgb_client.py             # ✅ MoF Japan JGB CSV（完整实现）
│   ├── pboc_scraper.py               # ✅ PBoC OMO（GBK 解码 + 正则提取）
│   ├── boj_scraper.py                # ✅ BoJ 利率 + JGB 买入 + TONAR + 汇率
│   ├── stock_flow_scraper.py         # ✅ A 股板块（东财）+ 日股个股（Yahoo JP）
│   ├── investing_scraper.py          # 反爬框架（备用，优先用 mof_jgb_client）
│   └── cme_metals.py                 # ⚠️ 待实现：金属期货 q 值计算
├── notion_writer/
│   └── client.py                     # Notion MCP 调用封装 + 13 DB schema
├── hermes_analysis_prompts/          # Hermes 分析阶段套用的角色 prompt
│   ├── crisis_warning.md             # Page A 风控官角色
│   └── china_japan.md                # Page B 中日联动分析师角色
├── tasks/
│   ├── todo.md                       # 任务计划
│   └── lessons.md                    # 经验积累
└── logs/                             # 每日运行日志（gitignore）
```

### 文件放置规则

- **新增数据源** → `scrapers/<source>_client.py`，不要塞 `fred_client.py`
- **新增 Notion DB** → 在 `notion_db_ids.json` 加条目，更新 `config.py:DB`，加 `_FIELDS` 到 `notion_writer/client.py`
- **新增 cron 任务** → `hermes_workflows/<NN>_<desc>.md`，更新 README
- **改 DeepSeek 行为** → 改对应 prompt md，不要改业务代码
- **禁止**：直接在 workflow md 里写抓取/解析逻辑（应该 import scrapers 包）

---

## §P5 环境变量清单

```bash
# 必填
FRED_API_KEY=        # FRED 官方 API key，免费申请：https://fred.stlouisfed.org/docs/api/api_key.html
DEEPSEEK_API_KEY=    # DeepSeek 平台 key：https://platform.deepseek.com/api_keys
NOTION_TOKEN=        # Notion Integration token（Hermes MCP 已配则可空）

# 可选（有默认值）
DEEPSEEK_MODEL=deepseek-chat   # 或 deepseek-reasoner
LOG_LEVEL=INFO
TIMEZONE=Asia/Tokyo
```

**注意**：`.env` 文件已 gitignore，Agent 不得将密钥写入任何被 Git 追踪的文件。

---

## §P6 LLM 调用专项约束

### 使用的 LLM 平台

- **唯一模型**：Hermes 的后端 DeepSeek（用户的 Hermes 自带，不需要单独 API key）
- **分析任务的角色 prompt**：`hermes_analysis_prompts/*.md`。Hermes 在执行 workflow 03/05/06/07 时把对应文件作为 system prompt 套上自己。
- **不许引入第二个模型**（除非用户明确要求）

### Fallback 策略

- DeepSeek 失败一次 → 重试 1 次（temperature 降 0.1）
- 再失败 → A7/B6 写入"❌失败" + 不修改任何其他 DB（其他 DB 的数据由 scrapers 已写入，是真实数据）
- **严禁伪造 AI 分析**

### 禁止行为

- 禁止让 Hermes 处理图片 / PDF / Notion 视图截图（DeepSeek 不支持多模态）
- 禁止 Hermes 自主决定 select 字段值（select 由 `config.py:THRESHOLDS` 规则计算后写入，Hermes 角色分析时只读不改）
- 禁止 prompt 注入用户原始输入到 system prompt（system 是固定模板，user 部分才是数据）

---

## §P7 测试与验证约定

### 当前测试状态

- [ ] 有 `tests/` 目录和测试代码
- [x] 暂无测试（依赖每日运行 + 人工 review A7/B6）

### 手动验证的关键场景

1. **首次跑批后**：人工 review 一次每个 DB 第一行，确认字段对齐 + 状态灯逻辑正确
2. **DeepSeek prompt 改动后**：用同一天数据跑一次 → 对比新旧短评是否合理
3. **数据源切换**（如 Investing → MoF）：跑一周观察是否值与历史 DB 中已有的对应日吻合
4. **Notion schema 改动后**（加字段、改 select 选项）：先在 `notion_db_ids.json` 记录变更日期 + 更新 `notion_writer/client.py:_FIELDS`

---

## §P8 本项目专属 Lessons 入口

- **经验库路径**：`tasks/lessons.md`
- **TODO 路径**：`tasks/todo.md`
- **格式规范**：见 `general-global-rule.md §6`

---

## §P9 更新记录

| 日期 | 变更 | 原因 |
|---|---|---|
| 2026-05-31 | 初版建立 | Claude 设计完成；建 13 个 Notion DB + 7 个 Hermes workflow；待用户首次部署运行 |
| 2026-06-11 | V7 重建 A2/A4 DB | A2/A4 DB 误入 trash 不可恢复，重建 schema 升级（加规模/状态灯等新字段）|
| 2026-06-11 | B5/B6/B7 写入 | 资产负债表快照 DB 首次写入成功（PBoC Apr/BoJ May-31/Fed Jun-03）|
| 2026-06-24 | 上下文压缩 + 小修复 | 创建 docs/context-log.md；修正 AGENTS.md 中 B5/B6 过时描述；补录 6/16 BoJ MPM 未加息经验 |

---

> **给 Agent 的提示**：本文件是项目级约束的**唯一来源**。如发现本文件与全局规则有冲突，**项目级约束优先**。如发现本文件有遗漏或需要更新（如 Hermes 实际运行后发现的坑），请在任务完成后提示用户更新本文件。
