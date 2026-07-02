# COMEX 贵金属日报 — 项目 Docker

> 生成 COMEX 贵金属日报的核心知识包。每天 08:00 JST 自动运行。
> 本目录是 SSOT（单一真实来源），comit 到 Generalrule 后，新 agent 启动时 git pull 即可开工。

---

## 快速启动（新 agent）

1. `git pull` 本仓库（Generalrule）
2. `cd projects/comex-metal-daily/`
3. 读 `AGENTS.md` → `HANDBOOK.md` → `skill/SKILL.md`
4. 检查 cron 是否注册（参照 `cron/` 目录下的配置）
5. 开工

## 目录结构

```
projects/comex-metal-daily/
├── README.md              ← 本文件（项目简介+启动指南）
├── AGENTS.md              ← 项目 AGENTS.md（知识包索引+核心指针）
├── HANDBOOK.md            ← 踩坑大全（所有关键教训合集）
├── context-log.md         ← 最近上下文快照（每晚自动更新）
│
├── Notion/                ← Notion DB/DS ID 参考 + 所有 prompt 文档
│   ├── DB_REFERENCE.md    ← 所有 DB/DS ID 快速参考（一张表）
│   └── prompts/           ← 所有 Hermes_*.md prompt 文档（原始规格）
│
├── skill/                 ← comex-daily-report skill 本体
│   ├── SKILL.md           ← 核心 skill（数据源、分析逻辑、输出规范）
│   └── references/        ← 所有 reference 文档（SIFO、Section62、SGE 等）
│
├── scripts/               ← 关键脚本
│   ├── sifo_calculator.py       ← SIFO 双轨租赁费率计算
│   ├── query_cme_inventory.py   ← CME 库存查询
│   ├── verify_sge_data.py       ← SGE 数据验证
│   ├── test_sifo_calc.py        ← SIFO 计算单元测试
│   └── comex_watchdog.py        ← 独立看门狗（检测日报是否产出）
│
└── cron/                  ← cron 配置快照
    ├── daily-report.json
    ├── context-compression.json
    └── shfe-weekly.json
```

## 核心调度

| 时间 (JST) | 任务 | cron job ID |
|---|---|---|
| 08:00 每日 | COMEX 贵金属日报 | `6dc5b547934e` |
| 02:30 每日 | COMEX 上下文快照压缩 | `c0151adeb107` |
| 09:00 周六 | SHFE 库存周报 | `7c5135047775` |
| 22:30 每日 | 独立看门狗（launchd） | `com.chaojin.comex-watchdog` |

## 数据源全景

**4 张西方源表（Notion inline data_source）：**

| 表 | DS ID | DB ID（回退） | 关键字段 |
|---|---|---|---|
| CME 库存 | `2e047eb5-fd3c-8034-a672-000be7162cff` | `2e047eb5-fd3c-80d8-9d56-e2c1ad066138` | Metal Type, Registered, Eligible, Net Change |
| OI | `2fc47eb5-fd3c-8023-85ec-000b59408356` | `2fc47eb5-fd3c-8035-ab22-cabf3e6e41bb` | OI Futures (JSON), OI Options (JSON) |
| CFTC | `2c747eb5-fd3c-808e-ab46-000bfe7673c5` | `2c747eb5-fd3c-8081-86dd-d0aeb45d5046` | COT (JSON) |
| SLV | `2ba47eb5-fd3c-8026-b549-000b2a02c5c8` | `2ba47eb5-fd3c-80c6-a0c1-ce9f47ec5d25` | Ounces In Trust, Shares Outstanding |

**2 张东方源表（普通 Notion database）：**

| 表 | DB ID | 说明 |
|---|---|---|
| SHFE Au 周库存 | `2bc47eb5-fd3c-8083-966e-ecfd9f396b44` | 排序用 `Gold日期` |
| SHFE/SGE Ag 周库存 | `2bc47eb5-fd3c-80f3-a71a-d8de149a4943` | 排序用 `Silver日期` |

**写入库：** `Delivery Notice & AI Analysis` — DB ID: `2be47eb5-fd3c-80ba-b065-f188139834b9`

## Token

- Notion: `YOUR_NOTION_TOKEN`（Hermes Analysis Issue Report 集成）
- FRED: `YOUR_FRED_API_KEY`（DGS3MO 3M T-Bill）
- 首次部署：先在 `.hermes/.env` 确认这两个 token 存在

## 关键教训（除非你读过 HANDBOOK.md，否则一定会踩的坑）

1. **DS API 返回 0 行是已知故障** — 必须回退到 databases/query + `Notion-Version: 2022-06-28`
2. **SGE Excel 下载 403** — 从 2026-06-18 起持续至今，用 akshare 或 web_extract 替代
3. **F 值只能用 Section62 PDF** — 严禁用 Yahoo `GC=F` 连续期货
4. **q 公式方向陷阱** — `q = r - (F-S)/(S*t)`，不是 `r - ΔS/(S*t)`
5. **Au 先判 ΔS 方向** — ΔS<0（Contango）时 q_phy 无论数值都不是挤兑
6. **东方库存排序用 `Gold日期` 不是 `Date`** — 否则 400 错误
