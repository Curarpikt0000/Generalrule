# 大规模多 KOL 历史回溯 — 子 agent 编排模式

> 本文沉淀 2026-06 一次性回溯 75 KOL × (2025-11-01 → today) 的实战编排经验。
> 适用于任何"N 个独立单元 × 多源检索 → LLM 分析 → 幂等写入 sink"的批量任务。
> 符合 Chao 偏好：一单元一子 agent、保质保量、逐源核对、零遗漏验证。

## 架构：检索 / 分析 / 写入 三层分离

把流程拆成可独立验证的三层，**不要让子 agent 一把梭**：

1. **检索层**（确定性脚本）：`scripts/backfill_one.py <id> <start> <end>`
   - Exa（带 startPublishedDate/endPublishedDate 日期窗）+ Tavily 多源，结果落 `data/backfill/<id>.json`
   - 纯数据采集，不做判断 → 可重跑、可审计
2. **分析层**（子 agent 的 LLM 推理）：读 `data/backfill/<id>.json` → 按发布日期归档 → 提炼有交易含金量的观点
   - 这是唯一需要"智能"的环节，正是 delegate_task 的强项（推理密集 + 隔离上下文）
3. **写入层**（确定性库）：`scripts/notion_writer.py write <json>`
   - 自动 L2 去重 + select option 安全合并 + 建 page；返回 CREATED / SKIP_DUP
   - 子 agent 只需构造 record json 逐条调用，不碰 Notion API 细节

**先做 1 个单元的完整端到端样本**（本会话用 Luke Gromen + test_record），验证整条链路 + 字段读回，再批量铺开。不要 75 个一次性铺开。

## 批量参数（实测）

- **每批 3-4 个 KOL / 子 agent**。6 个会超 600s 子 agent 超时（每 KOL 检索~46条素材 + 分析 + 逐条写入 ≈ 2-3 min）。
- **3 个子 agent 并行**（delegation.max_concurrent_children 默认上限）。
- 一轮 = 3 agent × 4 KOL = 12 KOL。75 KOL ≈ 6-7 轮。
- 每轮完成后**父 agent 审查**（抽查 check EXISTS + 看子 agent 自报数字），再派下一轮。

## 关键防坑

- **文件名隔离**：并行子 agent 都写 `/tmp/`，必须用 `/tmp/kol_<id>_N.json` 或独立子目录 `/tmp/kol_sa_<id>/`，否则 sibling 互相覆盖（本会话出现过 `/tmp/dg_*.json` 冲突）。在子 agent context 里明确要求。
- **覆盖盘点脚本** `scripts/check_coverage.py`：查每个 registry KOL 在目标空白期是否已有记录，输出 still_todo 列表 → 精确派下一批，避免重复派。select option 不存在会让 filter 报 HTTP 400 → 用 try/except 兜底当作"待回溯"。
- **空白期真无数据 ≠ 遗漏**：很多 KOL 在某时段确实没发声（周更/不定期型、或后期才加入监控）。子 agent 查过确认无料就是无料 → 诚实少写/不写，不编造。最终验证要看"整个窗口"是否处理过，不能只看某子区间为空就判定遗漏。
- **同名干扰**：几乎每个 KOL 都有重名（运动员/医生/演员/政客）。子 agent 必须严筛只留本人观点。身份与 registry 板块严重不符的（如某 KOL 实为记者非分析师）→ 标 active=false 待核实，不硬凑。
- **写入前 select option**：新 KOL 名第一次写会因 `Name of KOL` option 不存在报 HTTP 400。子 agent 先 `notion_writer.py ensure_option "Name of KOL" "<name>"` 再 write。
- **Exa publishedDate 不可靠**：常是抓取日/重抓日，视频转载页尤甚，正文里还可能内嵌数年前的原始日期。一律以正文标注的实际发布日归档；窗口外的旧文剔除。

## 零遗漏收尾验证（Chao 验收标准）

1. `check_coverage.py` 跑到 still_todo 只剩"真实无空白期数据"的 KOL
2. 对这些 KOL 查整个窗口（on_or_after start）确认有记录 + 日期范围合理
3. 统计 sink 总记录数前后差（本会话 1603 → 2015，净增 412），按月分布确认空白期被填上、时间线连续
4. 抽查若干 (name, date) 组合 check EXISTS — API 自报 CREATED 不算证据，读回才算
