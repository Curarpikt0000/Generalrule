# RAG 向量索引：增量重建 vs 全量重建（避免定时刷新超时）

> 适用场景：一个本地 RAG 知识库（faiss + BM25），语料会周期性新增/变更少量文档，需要定时（cron）刷新。
> 核心教训：**定时刷新绝不能每次全量重 embed 整库**——这是 cron 超时和算力浪费的头号原因。

## 问题（真实踩坑，2026-06-27 WW Discovery 库）

- 库规模：994 docs / 50410 child chunks，全量 embed 一次 ≈ **25 分钟**（CPU 端点 localhost:8800，qwen3-embedding-8b dim4096）。
- 配了一个双周 cron 自动刷新（检测 Slack 新帖/Sheet 变化 → 深挖 → 重建索引 → 回填 Notion）。
- **cron 第一次跑就超时报警**：cron 的 `script=` 执行有硬超时（本环境约 120s），而全量 `build_index` 要 25min，必然被截断；更糟的是可能**刷新到一半中断**，向量库/下游 Notion 处于不一致半完成状态。

## 解决方案：双层拆分 + 增量索引

### 1. 增量索引（只 embed 新增/变更的 chunk）

全量重建的浪费在于：即使只新增 5 个文档，也把 50405 个没变的 chunk 重新 embed 一遍。embedding 是唯一的耗时步骤（faiss 组装 5万向量只要几秒）。

设计（见 `WW-Project-Tracker/src/build_index_incremental.py`）：
- **per-chunk embedding 缓存**：key = `sha256(enriched_chunk_text)` → vector，持久化为 `.npy + keys.json`。
- 每次重建：对所有 chunk 算 hash，**只对 cache 里没有的 hash 调用 embedder**；其余直接复用缓存向量。
- **per-doc 指纹**（`sha256(doc_text)`）做 diff，报告 added/changed/removed 文档数，供 cron 汇报。
- faiss 每次从缓存向量重新组装（IndexFlatIP，几秒）；删除的文档自然不再加入。
- cache 每次按当前在用的 key 集合 prune，避免无限增长。
- meta.json 记录 `embedded_this_run`，让汇报能说清"本次只 embed 了 N 个新 chunk"。

效果：新增几个文档时，刷新从 25min 降到**秒级~1-2 分钟**（只 embed 新增 chunk）。
**迁移成本**：从全量索引切到增量版，第一次跑仍需全量 embed 一次来填充 cache（一次性），之后都是增量。

陷阱：
- embedding 维度/模型变了，缓存全部失效（hash 不含模型名，但换模型应清 cache 重建）。
- hash 必须基于**实际送进 embedder 的文本**（如果 enrich 了 title 前缀，hash 也要含 title），否则 cache 命中错向量。

### 2. cron 双层拆分：检测脚本轻量，重活交给 agent

cron `script=` 有硬超时，**不要把重管线塞进 cron 脚本同步跑**。拆成：
- **cron 脚本 = detect-only**（约 2s）：只检测有无更新（比对游标 ts / Sheet mtime），打印 `NO_UPDATE` 或 `UPDATE_DETECTED`。永不超时。
- **agent（cron 的 LLM 端，执行预算更长）**：读到 `UPDATE_DETECTED` 后，自己用 terminal `background=true, notify_on_complete=true` 跑重管线（深挖→增量索引→回填），用 process wait/poll 等完成再汇报。

游标只在**全链成功后**推进（中途崩溃下次重试，不会漏）。无更新时脚本秒退、不浪费算力、不刷屏（配合静默）。

## 相关
- [[polling-bidirectional-bot-and-source-timeout-isolation]] - 轮询+游标模式、单源硬超时隔离
- [[cron-no-gui-preference]] - cron 设计偏好
- Skill `rag-knowledge-base-chatbot` - RAG 库整体建法
