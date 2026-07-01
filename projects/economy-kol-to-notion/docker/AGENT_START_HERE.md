# 🚀 AGENT START HERE — Economy-KOL-to-Notion 知识包

> **你（接手的 AI agent）下载了这个 Docker 镜像 = 拿到了这个项目的全部知识。**
> 镜像内是**知识包**：完整代码 + 文档 + 运维机制 + skill + Notion 坐标。
> **不含**真实数据（KOL 言论/Notion 快照）和密钥——你用自己的密钥连真实 Notion 干活。
> 服务对象：Uber Eats Japan GR 运营团队。所有时间 = 东京时区（JST, UTC+9）。

---

## 📖 按这个顺序读（15 分钟看懂全部）

1. **`README.md`** — 项目逻辑：一句话定位、三层 Notion DB 架构、端到端数据流、6 层搜索降级链、**3 条最高优先级铁律**、防脱敏污染架构、最新进展、新 agent checklist。
2. **`ops/RUNBOOK.md`** — 运转机制：每日/每周时序图、6 个 cron 逐一说明、**更新顺序 + 数据流机制**、如何在新环境重建全套 cron、排障。
3. **`notion-locations.md`** — Notion 位置坐标：三层 DB 的 database_id、data_source_id、dashboard URL、By Day 属性结构。
4. **`lessons.md`** — 全部踩坑教训（情绪分析铁律、期限判读、防数据损坏、搜索源选型等）。
5. **`skill/SKILL.md`** — 操作手册（E2E 流程）+ `skill/references/`（分主题深度笔记）。
6. **`scripts/`** — 全部核心可复用脚本（采集/结构化/安全写回/防污染/周报）。

---

## 🎯 这个项目在做什么（历史 + 现状 + 未来）

**做什么**：每天自动监控 ~76 位经济/宏观/贵金属 KOL 的新观点 → LLM 中文逻辑链分析（按标的拆多空腿、判短期/长期）→ 写 Notion 三层 DB → 推 GitHub Pages dashboard（共识度 + 短期/长期雷达图）→ 周报。

**历史里程碑**（详见 README/lessons）：
- 建 registry SSOT（76 KOL）+ 三层 Notion DB + 6 层搜索降级链
- 情绪分析从"浅层匹配"重构为"LLM 读懂语义、按标的拆多空腿"
- 加「期限」维度（短期≤3月/长期>3月）→ 4970 腿 100% 回填 → 短期/长期双雷达图
- 防脱敏污染架构（安全写回 + 写入总闸 + 每日体检 watchdog）
- 全套自动化 cron（采集/dashboard/周报/体检）

**未来工作 / 待办**（详见 `todo.md` + README §10）：
- 日常维护 6 个 cron（见 RUNBOOK），监控 last_status
- 新增 KOL：确认真人 → 加 Notion KOL List → 同步 registry（只增不减）
- registry 个别身份待核对；By Week 部分字段稀疏待补
- 搜索 key 充值/轮换；agent-browser 持久化

---

## ⚡ 快速上手（3 步接手）

```
1. 读上面 6 份文档（README → RUNBOOK → notion-locations → lessons → skill → scripts）
2. 把 config.env.example 复制为项目 config/.env，填入你自己的 NOTION_TOKEN / EXA_API_KEY 等
3. 按 ops/cron-jobs.json 用 cronjob(action='create') 重建 6 个 cron（workdir 改成你的项目根路径）
```

## 🚨 铁律（违反会出事，详见 README §4 + lessons）

1. **情绪/多空绝不浅层匹配** — LLM 读懂语义，一条发言按标的拆多空腿。
2. **期限按 KOL 主观时间预期判**（3 个月内会发生=短期）。
3. **声称成功必须自己读回验证**（重 query Notion / curl 线上），零编造，零遗漏。
4. **防脱敏污染**：agent 绝不肉眼读原文再写回（会把真名覆盖成 ANONYMIZED）；只输出标签数组，脚本自读真字节合并。
5. **密钥只进 .env**，绝不硬编码/进 git/打进公开 image；SearXNG 配置由用户维护勿改。

---

*此镜像由 Generalrule 仓库 `projects/economy-kol-to-notion/` 打包（已脱敏，无 Uber 内部专有名/密钥/数据）。源仓库 main 与 ub-branch 都有同步副本。*
