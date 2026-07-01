# Economy-KOL-to-Notion — 运维手册 RUNBOOK

> 本文件让新 agent（读 main 或 ub-branch 都行）**马上看清整个自动化如何运转、按什么顺序、靠什么机制**，无需在 cron 数据库里翻。
> 配套：`ops/cron-jobs.json`（6 个 cron 的完整定义快照，可直接用 `cronjob(action='create')` 重建）+ `ops/*.sh`（no_agent 脚本）。
> **所有时间 = 东京时区（JST, UTC+9）。** 最后更新：2026-07-01 JST。

---

## 一、一图看懂每日/每周时序（JST）

```
每个工作日（周一~周五）:
  08:30 ─ (Economic-Dashboard 项目, 非本项目)
  09:00 ─ ① Economics KOL Daily Track   ← 采集: 76 KOL 各跑 backfill_one → LLM 分析 → 写 By Day
  09:15 ─ ⑥ econ-kol-purity-watchdog    ← 体检: 扫 ANONYMIZED 污染(干净静默)
  09:30 ─ ② KOL Dashboard Push          ← 重生 data.json → push GitHub Pages(雷达图)
  (①→②有序: 先采集写库, 再拉库生成 dashboard; 相隔30min确保①写完)

每天(含周末):
  03:15 ─ ④ Economy-KOL context-distill ← 上下文压缩归档(session_search 过去24h)

每周一额外:
  09:00 ─ ③ KOL Weekly Summary          ← 汇总上周 By Day → 写 By Week 周报

后台(使命已完成, 见下):
  每20分 ─ ⑤ kol-term-backfill-auto     ← 期限回填自动推进器(remaining=0, 现空转)
```

**关键时序依赖**：① 09:00 采集写 By Day → ② 09:30 从 By Day 拉数据生成 dashboard。**② 必须晚于 ①**，间隔 30 分钟是给 ① 的采集+写入留时间。③ 周报依赖 By Day 已有本周数据（① 每天写，周一时上周数据已齐）。

---

## 二、6 个 Cron 逐一说明

### ① Economics KOL Daily Track（`0 9 * * 1-5` 工作日 09:00）
- **类型**：agent cron（skill=`economics-kol-daily-update`），toolsets=terminal/file/web/browser，deliver=origin
- **workdir**：项目根 `~/Projects/Economy-KOL-to-Notion`
- **做什么**：读 `data/kol_registry.json` 所有 `active=true` KOL（当前 76）→ 每个跑 `scripts/backfill_one.py <id> <窗口start> <today>`（工作日过去 24h，周一过去 72h 覆盖周末）→ LLM 逐条读懂语义、按标的拆多空腿+判期限→ `scripts/notion_writer.py` 写 By Day（幂等去重+防污染护栏）→ 记 `processed_daily.json` → 读回验证。
- **完整 prompt** 见 `ops/cron-jobs.json`。

### ② KOL Dashboard Push（`30 9 * * 1-5` 工作日 09:30）
- **类型**：agent cron（skill 同上），toolsets=terminal/file/browser，deliver=origin
- **workdir**：`~/Projects/Economy-KOL-to-Notion/dashboard/kol-dashboard`（**独立 git repo** = GitHub Pages `curarpikt0000/kol-dashboard`）
- **做什么**：`python3 generate_dashboard_data.py`（从 By Day 拉全量→算加权 sector 评分+今日信号+短期/长期雷达图数据）→ git commit → push origin main → GitHub Pages 自动部署 → curl 线上验证 data.json 条数+双雷达图渲染。
- **等价脚本**：`ops/kol_dashboard_hourly.sh`（原每小时版的逻辑，含 generate→diff→commit→push→验证；每小时 cron 已于 2026-07-01 取消，改为仅工作日 09:30 由本 agent cron 跑）。

### ③ KOL Weekly Summary（`0 9 * * 1` 周一 09:00）
- **类型**：agent cron（skill 同上），toolsets=terminal/file，deliver=origin
- **做什么**：从 By Day 查上周一~上周日数据，按 Sector 分组统计多空，**只总结本周新增/变化的观点**（不重复上周立场）→ 生成周报 → 写 By Week DB。

### ④ Economy-KOL context-distill（`15 3 * * *` 每日 03:15）
- **类型**：agent cron（无 skill），toolsets=terminal/file/session_search，deliver=local
- **做什么**：`session_search` 搜过去 24h 与 "Economy KOL"/"KOL Notion"/"kol_registry" 相关会话→压缩成当日上下文归档（存 `docs/context-log.md`）。属于全局「项目上下文自动归档」机制（skill `project-context-persistence`）。

### ⑤ kol-term-backfill-auto（`*/20 * * * *` 每 20 分钟）— ⚠️ 使命已完成
- **类型**：agent cron（无 skill），toolsets=terminal/file/delegation，deliver=local
- **历史作用**：期限回填期间自动推进（每轮派子 agent 判读缺期限的 KOL，安全写回，remaining=0 自停）。
- **现状**：4970 腿期限已 100% 回填，remaining=0，此 cron 每轮空转（不报错）。**可安全 cancel**（Chao 曾说不必清理，保留待将来大批新增 KOL 时复用）。完整 prompt 见 `ops/cron-jobs.json`。

### ⑥ econ-kol-purity-watchdog（`15 9 * * *` 每日 09:15）
- **类型**：**no_agent 纯脚本** cron，script=`econ_purity_watchdog.sh`（见 `ops/`），deliver=origin
- **做什么**：扫 Notion By Day + 本地 data/ 是否有 `ANONYMIZED` 脱敏污染。干净→静默（无输出不投递）；有污染→告警。防脱敏污染复发的第三道防线。

---

## 三、更新顺序 / 数据流机制（新 agent 必读）

**日常自动更新链（工作日）**：
```
09:00 ① 采集 → 写 Notion By Day (SSOT 数据落库)
09:15 ⑥ 体检污染 (守卫)
09:30 ② 拉 By Day → 生成 data.json → push Pages (对外展示层刷新)
```
- **By Day 是唯一事实源**；dashboard、周报都从它派生。改分析口径只需重跑 ②/③ 重新派生，不动 By Day 就不会错乱。
- **幂等**：① 的 notion_writer 去重（同 KOL+同日不重复写）；②/③ 可安全重跑（覆盖派生产物）。
- **手动补跑**：任一 cron 漏跑/失败，可用 `cronjob(action='run', job_id=...)` 立即补跑，或在 workdir 手动执行对应脚本。

**新增 KOL 的更新顺序**（不用改代码）：
1. 确认是真人非机构 → 加 Notion KOL List DB
2. 同步进 `data/kol_registry.json`（追加到 kols 数组，`active=true`，只增不减）
3. 次日 ① 自动覆盖他；需要历史基线则手动 `backfill_one.py <id> 2025-11-01 <today>` 回溯

---

## 四、新 Agent 如何重建这套 cron（换环境/新机器）

1. 拉 repo，读本 RUNBOOK + `README.md`（项目逻辑）+ `lessons.md`（踩坑）。
2. 拷 `self-skill/economics-kol-daily-update/` 到本机 skill 目录。
3. 确认项目在 `~/Projects/Economy-KOL-to-Notion/`，`config/.env` 有有效密钥（NOTION_TOKEN 等）。
4. 把 `ops/*.sh` 拷到 `~/.hermes/scripts/`（no_agent cron 脚本目录）。
5. 按 `ops/cron-jobs.json` 逐个 `cronjob(action='create')` 重建 6 个 job：
   - agent cron（①②③④⑤）：传 `name`/`schedule`/`prompt`/`skills`/`workdir`/`deliver`/`enabled_toolsets`
   - no_agent cron（⑥）：传 `name`/`schedule`/`script`/`no_agent=true`/`deliver`
   - **workdir 路径按新环境实际项目根目录调整**（cron-jobs.json 里是原 VM 路径）。
6. 用 `cronjob(action='run', job_id=...)` 手动触发一遍验证每个跑通，再靠调度自动运转。

---

## 五、验证与排障

- **健康检查**：`python3 scripts/add_term.py count`（看 remaining）、`python3 scripts/purity_watchdog.py`（应静默）、`python3 scripts/check_source_purity.py`（Notion 源纯净）。
- **cron 状态**：`cronjob(action='list')` 看每个 last_status；error 要查。
- **已知噪音**：git push 时 `proto: duplicate proto type registered` 是 git wrapper 无害噪音，非失败（脚本已用 grep `rejected|error|fatal` 区分真失败）。dashboard cron 曾因 `set -e` + 该噪音误判 error，已加固。
- **铁律**：声称成功必须读回验证（curl 线上 / 重 query Notion）；破坏性操作先确认；SearXNG 配置由 Chao 维护勿改。

---

*配套文件：`ops/cron-jobs.json`（可重建定义）、`ops/econ_purity_watchdog.sh`、`ops/kol_dashboard_hourly.sh`。所有内容已脱敏（无 Uber 内部专有名/密钥），脱离原环境也成立。*
