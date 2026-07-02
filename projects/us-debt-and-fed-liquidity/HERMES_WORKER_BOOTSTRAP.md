# Hermes Worker 启动 Prompt

> **使用方法**：打开一个新的 Hermes worker 对话，把下面分隔线之间的所有内容**完整复制粘贴**发送给它。
> Hermes 会读懂项目结构 + 注册 7 个定时任务 + 跑首日数据 + 报告状态。

---

```
你好 Hermes，我要你接管一个长期的金融风控自动化项目。下面是完整指令，请逐条执行，不要漏，遇到问题立刻反馈我。

# 项目根目录

/Users/chaojin/hermesagent/US Debt and Fed Liquidity/美债收益率和Fed中美日流动性日报

# 第一步：理解项目（必读）

请按顺序读以下文件，理解你的角色和任务：

1. AGENTS.md — 项目级规则（最重要）
2. README.md — 快速索引
3. PROPOSAL.md — 整体架构
4. notion_db_ids.json — 13 个 Notion DB 的 ID
5. hermes_workflows/ 下全部 7 个 md — 你每天要做的具体事
6. hermes_analysis_prompts/ 下 2 个 md — 你做 AI 分析时切换的角色 prompt
7. config.py + scrapers/fred_client.py — 已写好的工具代码

# 第二步：核心认知（不要弄错）

- 我（用户）已经把 13 个 Notion 数据库建好了，你只负责往里写行
- 你不是"调用 DeepSeek"——你自己就是 DeepSeek，做分析就是切换你的 system prompt 到 hermes_analysis_prompts/ 里那两个文件
- 数据流：FRED/PBoC/BoJ 原始数据 → 你的 scrapers → 你写入 Notion DB → 你切角色 → 你读 30 天 DB → 你写 AI 分析回 Notion
- 全程没有第三方模型
- 时区一律 JST (Asia/Tokyo)
- 所有金额/利率字段严格按字段名（含 emoji）写入，select 字段值不可发明
- THRESHOLDS 在 config.py 里，状态灯按规则计算后写入，分析角色只读不改

# 第三步：环境检查

1. 确认 .env 文件存在，FRED_API_KEY 已填（python -c "from config import FRED_API_KEY; print(bool(FRED_API_KEY))")
2. 确认你能访问 Notion MCP：试着 fetch https://www.notion.so/2dc47eb5fd3c803d8c31c4b77bd56154，看是否能读到 "🚸 经济危机预警"
3. 确认你能访问 FRED API：用 scrapers/fred_client.py 拉一次 DGS10 最近 5 天

如果有任何一项不通，停下报告我，不要继续。

# 第四步：首日全量跑批（一次性，用于初始化数据）

按这个顺序，串行执行 5 个 workflow（首日不跑周度/月度，等到时间触发）：

1. 读 hermes_workflows/01_morning_us_data.md，照做（抓 UST + Fed 流动性 → 写 A1/A2/A5 今日一行）
2. 读 hermes_workflows/02_morning_jgb_data.md，照做（抓 JGB + TONAR → 写 A3/A4/B4 今日一行）
3. 读 hermes_workflows/03_morning_ai_analysis.md，照做（切风控官角色 → 写 A7 今日一行 + 长分析）
4. 读 hermes_workflows/04_noon_china_japan.md，照做（抓 PBoC + BoJ + 板块资金 → 写 B2/B3/B5）
5. 读 hermes_workflows/05_noon_ai_analysis.md，照做（切中日联动分析师角色 → 写 B6）

每一步完成后告诉我"完成 N，写入了 X 行"。失败就停下报告，不要硬继续。

# 第五步：注册 7 个定时任务

以 Asia/Tokyo 时区为基准，注册以下 cron 任务。每个任务的"内容"就是去读对应 md 文件并执行：

| 任务名 | Cron (JST) | 执行的 md |
|--------|-----------|-----------|
| daily_us_data       | 30 8 * * 1-5    | hermes_workflows/01_morning_us_data.md |
| daily_jgb_data      | 0  9 * * 1-5    | hermes_workflows/02_morning_jgb_data.md |
| daily_morning_ai    | 30 9 * * 1-5    | hermes_workflows/03_morning_ai_analysis.md |
| daily_china_japan   | 1 12 * * 1-5    | hermes_workflows/04_noon_china_japan.md |
| daily_noon_ai       | 30 12 * * 1-5   | hermes_workflows/05_noon_ai_analysis.md |
| weekly_fed_h41      | 0 18 * * 5      | hermes_workflows/06_weekly_fed_h41.md |
| monthly_cb_balance  | 0 12 10 * *     | hermes_workflows/07_monthly_cb_balance.md |

跳过日本节假日（你自己用 jpholiday 或类似工具判断；中国/美国节假日按对应数据源是否开市自动跳过即可）。

# 第六步：报告

全部完成后给我一份回执：

- 7 个 cron 是否注册成功
- 首日 5 个 workflow 每个写了多少行 Notion，是否有失败
- A7 + B6 今天的 AI 短评内容（让我直观看到分析质量）
- 任何你发现的、和文档不一致的坑（比如某个字段名 typo、某个 select 选项写错）

# 长期约定

- 每日跑批失败超过 2 天，主动找我
- 数据源失效（如 FRED 返回 503 持续 1 小时+），主动切备用源并告诉我
- 任何 Notion schema 变更需求，先提案再执行，不要私自改
- 把每次跑批的失败原因 append 到 tasks/lessons.md

开始吧。先做第一、第二、第三步，做完汇报给我，再继续。
```

---

## 备注（不需要发给 Hermes）

如果你的 Hermes 实例和默认配置不同（比如 cron 语法不一样、Notion MCP 没配），你可能要微调上面的内容。常见调整：

- **没有 cron 工具**：让 Hermes 用 launchd / crontab 自己挂任务
- **想跳过首日跑批**：删掉"第四步"那段
- **节假日判断 Hermes 不会做**：让它在 workflow 开头加 `if today.weekday() >= 5: exit()`（周末跳过）

跑通一周后，你可以让 Hermes 把这份 BOOTSTRAP 自身的内容存到 Notion 一个"运维 SOP"page，未来换 worker 直接调用即可。
