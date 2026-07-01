---
title: Presto / Quark 超重多表 join 与大表查询优化
domain: engineering
type: concept
keywords: [presto, quark, presto-on-spark, 大表查询, 多表join, EXCEEDED_TIME_LIMIT, 30min超时, hash_partition_count, 分区裁剪, broadcast-join, shuffle, spill, kryo, uber]
tags: [presto, quark, query-optimization, join, spark, uber]
source: "Slack #presto-user-group/#querybuilder oncall + engwiki TE0PRESTO 检索 2026-07-01"
sources: ["Slack #presto-user-group / #querybuilder / #spark 只读检索 2026-07-01", "engwiki TE0PRESTO Query Optimization", "engwiki Presto on Spark"]
created: 2026-07-01
updated: 2026-07-01
last_updated: 2026-07-01
---

> **本页含 Uber 内部查询引擎经验（Presto / Quark / queryrunner），属 ub-branch。**

# Presto / Quark 超重多表 join 与大表查询优化

当一条 Presto 查询涉及多张大 fact 表 join、扫描窗口过长或输出爆炸时，很容易撞上集群侧硬超时或内存/shuffle 上限。本页提炼「把查询压回限额内」与「压不回就换引擎（presto-on-spark / Quark）」两条主线的官方 oncall 一致建议，作为跨项目可复用的调优手册。核心心智：**30 分钟集群硬超时改不了，能做的只有让查询更轻，或换到 Spark 上跑。**

## 核心红线：30min 集群硬超时

- **Presto 单查询集群侧硬超时 = 30 分钟，且不含排队时间，无法调大。** 触发时报 `EXCEEDED_TIME_LIMIT ... 30.00m`。
- queryrunner **客户端** polling 超时是另一回事，可另配加长（例如拉到 5 小时），但那只影响客户端等多久，**顶不动集群 30min 上限**。
- 因此唯二正解：① 把查询优化到 30min 内跑完；② 换 **presto-on-spark（Quark）**。

## Join / 查询优化清单（oncall 反复给的一致建议）

1. **大 fact 表放 join 顺序靠前。**
2. **只用简单 equi-join**，避免复杂 join 条件。
3. **避免 output 行数 > input 的 join**（多对多爆炸）。
4. **缩短时间窗口分窗跑，再拼结果。**
5. 查询首行 `SET session hash_partition_count=64;` **增大 hash 分区并行度**，缓解 per-node memory limit。
6. 仍然重 → **改跑 presto-on-spark（Quark）。**

## 分区裁剪（硬要求）

- Presto 会直接拒绝报 `Filters need to be specified on all partition columns`——**必须在 `WHERE` 显式过滤所有分区列**（如 `datestr`），否则查询被拒。
- 用**更紧的 `datestr` 过滤**裁剪扫描量。
- 注意 **remote-read scan**（跨 region 只读表）会拖慢查询并打网络；确认**所有 join 表同 region 且都带分区过滤**。

## 重 join 改写方案（基于 Spark 物理计划）

针对 item-line 这类多表 join 最具体、最有效的三步改写：

1. **先把驱动表过滤/裁剪成 CTE**（先 `WHERE`，必要时 `LIMIT`），再 join 其它大表 → 让优化器把 SortMergeJoin 转成 **broadcast join**，避免全量 shuffle。⚠️ **把 `LIMIT` 放在最后是反模式**（先 join 再限行，等于全量算完再砍）。
2. **合并对同一张表的多次 scan**（同表多列一次取干净）。
3. **对被 join 的大表也加严格分区过滤**（把 7 天扫描缩成 1 天，shuffle 骤降）。

## presto-on-spark（Quark）实操

- **quark = presto 跑在 spark 上的内部叫法。** 超 30min 的重查询走它。
- 需 **YARN queue 访问权限**（见 engwiki "Presto on Spark" 的 YARN queues 配置，需 Allowed-Group 权限）。
- **QueryBuilder 目前不支持传 spark session 属性**，两个 workaround：
  - 走 **uWorc 的 presto job**（`insert into` 临时表），在 uWorc 里设 session 属性；
  - 走 **queryrunner python client**，用 `source_attributes` 传：

```python
cursor = qr.execute('presto-on-spark', 'select ...',
    source_attributes={"spark.yarn.queue": "hive-stats"})
```

- 常见报错 `Kryo serialization ... Buffer overflow` → 设 `spark.kryoserializer.buffer.max=512m`。

## BMO / SODA oncall 标准调优 checklist

**减少扫描**
- 过滤分区列且保持 **sargable**：`WHERE ds BETWEEN ...` 优于 `date(ts)=...`；**别把分区列包在函数里**，否则分区裁剪失效。
- 只 `select` 需要的列。

**避免大 shuffle / 倾斜**
- join 前先 **pre-aggregate**。
- 一侧小就逼成 **broadcast**。
- 热点 key 做 **salting** 或拆出单独处理。

**聚合下推**
- `GROUP BY` / `DISTINCT` 尽量放在 join 之前做。
- 重复的 `COUNT(DISTINCT)` 合成单个预聚合 CTE。

**内存压力信号**
- 关注 **spilled bytes > 0**（内存吃紧）→ 减 shuffle、减行宽、把大 join 拆成分级临时结果 / 中间表。

**已知昂贵操作**
- 全局 `ORDER BY` 不带 `LIMIT`、超大 partition 上的 window function 都很贵。
- 小文件过多也拖慢 → compact / 写更大的 Parquet。

## Hive 物化 / 视图

- Hive/Presto view **不阻断分区裁剪**：会把分区过滤下推、在 planning 阶段裁剪分区（前提是查询本身带分区过滤）。
- 可用**中间 / 临时表**把重 join 结果先落一层，再供下游消费。

## 官方支持入口 / 频道

- 官方优化指南：`t.uber.com/PrestoQueryOptimization`（engwiki TE0PRESTO / Query Optimization）。
- presto-on-spark 指南：engwiki "Presto on Spark"。
- 超重查询协助入口：`t.uber.com/presto-heavy-query-assistance`。
- 求助频道：#presto-user-group、#queryrunner、#querybuilder、#datacentral-helpdesk、#presto-perf、#presto-consumption-help、#query-help、#data-helpline、#spark、#ads-metrics-attribution-support（GR/Ads，用 `!q` 提问）。

## 诚实说明 / 局限

- 本页建议来自 **Uber 内部 Slack 只读检索**（#presto-user-group / #querybuilder / #spark 等，含官方 oncall 与 SODA/BMO 机器人）+ engwiki 指南，**检索日期 2026-07-01**。
- "finch fast path" 未找到直接对口内容，暂未纳入；**quark 已确认 = presto-on-spark**。
- 本页只收录**通用可复用**的查询优化知识，不含任何具体项目的表名/口径细节。

## 来源

- Slack 只读检索：#presto-user-group / #querybuilder / #spark（官方 oncall + SODA/BMO 机器人），2026-07-01。
- engwiki：TE0PRESTO Query Optimization（`t.uber.com/PrestoQueryOptimization`）、"Presto on Spark"。

## 相关页面

- [[queryrunner-mcp-fetch-rows-and-queue]] —— queryrunner-MCP 取数突破 50 行 + 后端排队拥堵应对（同属 Uber 内部取数链，本页优化后的查询即经此链提交/取回）。
