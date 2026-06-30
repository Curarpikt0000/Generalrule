# 全量日扫 + 当日补写 + 字段补全（recurring 任务类）

> 触发：用户问"今天这 N 个人有没有新言论"/"把这些人上传/补写"/"为什么 cron 只写了 X 条"。
> 区别于 cron 自动日报（cron 只写"有新增观点且通过去重"的，常只 8-10 条，**不是全量覆盖**）。

## A. 全量日扫所有 active KOL（"今天 N 个人有没有新言论"）

cron 自动日报 ≠ 全量核实。用户问"今天这 76 个人有没有新言论"时，他要的是**逐个核实谁有/谁没**，不是看 cron 写了几条。如实说明这个区别再开干。

1. 读 registry 拿全部 `active=true` 名单，确认数量（`len(active)`）。
2. **并行子 agent 分批**（上限 3 并发）：76 人 ≈ 3 批 × 各 25 人。每批 toolsets=`[terminal, file]`。
3. 每个子 agent 对每个 id 跑 `backfill_one.py <id> <昨天> <今天>`（当日窗口），读 `data/backfill/<id>.json` 的**三桶 exa/tavily/ddgs**，逐个判断本人今日是否有真实新言论。
4. **扫描模式 = 只汇报不写库**（避免与 cron 重复写入冲突，先给全貌）。输出格式：`✅ <name>: 有新言论 — <摘要> (日期, 来源域名)` / `⬜ <name>: 今日无新言论`，末尾本批统计。
5. 铁律传给子 agent：严筛同名干扰（运动员/演员/医生/历史人物/讣告）；日期以正文实际发布日为准（Exa 的 date 常是抓取日）；查不到就如实说无，宁漏不虚。

> 时长 ~十几分钟正常。子 agent 自报的"有/无"是初判，最终条数以写库后主 agent 独立 query 读回为准。

## B. 当日补写（"把这 N 个人上传"）

把 A 扫出的有料 KOL 写进 By Day。

1. **先 query 今天已写入的 KOL**（cron 早上写的那批），避免重复（L2 也会挡，但明确告知子 agent 更稳）。
2. 剩余的人**重新精准跑当日窗口**（用升级后的 backfill_one，带 ddgs 兜底），不要复用可能被覆盖的旧 json。
3. 并行子 agent 分批写，每个走 `notion_writer.py write '<json>'`（自动 select 合并 + L2 去重 + 建 page）。字段填法见主 SKILL.md §二（含 `方向明细` JSON 中文键 + `主导方向`）。
4. **剔除规则（子 agent 必须执行，这是质量不是漏报）**：
   - 机构不算 KOL（FEMA、瑞银、花旗等）→ 不写。
   - 预言/占星类当日内容若是**政治预言而非经济/市场观点** → 不写（低权重 KOL 只在有市场观点时才计）。
   - 无可靠发布日 / 正文空 / 仅有标题的素材 → **不写，绝不推测日期**（Chao 零编造铁律实战命中：Exa 常返回 date=None、text 空、仅 title 的公司简介页/纯事件公告/付费墙截断条目，子 agent 易据此瞎填日期）。
   - 爬取日伪装成今日（正文实际是上周的旧文）→ 按正文日期剔除。
   - 同名干扰、立场实质重复（同方向+同标的+同催化剂，无新催化剂）→ 不写。
5. **主 agent 独立 query 读回验证**最终总条数（子 agent 自报不算），抽查 `方向明细` JSON 合法非空。

## C. 字段补全：旧记录有「主导方向」但「方向明细」空/非法

cron 早期跑的记录可能只有 `主导方向`+`多空标的`，缺结构化 `方向明细` JSON（dashboard 腿级统计会漏掉它们）。补全方法：

1. query 目标日期/范围，筛 `方向明细` 为空或 `json.loads` 失败的 page。
2. 子 agent **仅依据该记录已有的 Comments + 多空标的**逐条拆多空腿，构造 `方向明细` JSON（中文键 `[{"标的":..,"板块":..,"方向":..,"强度":..}]`），PATCH 回 page。**不新增编造 Comments 之外的标的。**
3. 读回验证目标记录 `方向明细` 全部合法非空（`isinstance(list) and len>0`）。

> 验证脚本范式：query Date 过滤 → 对每条 `json.loads(方向明细)` 试解析 → 统计 bad 数 == 0 才算完成。

## D. 搜索源加固（已落地到 backfill_one.py）

- `ddgs` 安装：`pip install ddgs --break-system-packages`（VM 系统 python 无 venv，cron 用 /usr/bin/python3）。新包名 `ddgs`（不是旧 `duckduckgo_search`），import `from ddgs import DDGS`。
- 降级链逻辑：`paid_hits = len(exa)+len(tavily); if paid_hits==0: 跑 ddgs`。ddgs 无日期窗，时效靠正文判断。
- **cron prompt 必须明示"三桶 exa/tavily/ddgs 都读"**，否则付费源断粮当天兜底数据被无视、观点全丢。
- 内部联网备选见主 SKILL.md（某 grounded-search 网关，免费不断粮，但人名被 PII 匿名化 → 用 handle/话题查）。
