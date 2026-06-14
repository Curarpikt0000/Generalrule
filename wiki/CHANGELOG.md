# Wiki CHANGELOG —— 知识库版本管理

> **纪律来源**：general-global-rule.md §6（每次写 Wiki 须在此留记录）。
> **本文件管**：`wiki/` 下**知识页**的新增 / 删除 / 修改 / 迁移，以及**领域目录**的增减。
> repo 结构性改动（规则文件、模板、self-skill）记在根 `CHANGELOG.md`，本文件不重复。
> **记录格式**：`### 日期`，正文逐条 `[动作] 领域/页面 —— 说明`。动作 = 新增 / 删除 / 修改 / 迁移 / 重写。
> 写 wiki 优先调用 `self-skill/llm-wiki` skill，产出须符合 [[wiki-ingest-guide]]。

---

## 记录

### 2026-06-14 —— Agent 配置自述矩阵（Claude Code, Opus 4.8）

- **[新增] `agent-rules/agent-config-matrix.md`** —— 归集各 agent（Prompt A 通用自述）的配置机制，补 SSOT「新 agent 如何配置自己」缺口。首条填入 CC-home（家用机 Claude Code）完整七维自述；其余 8 个目标留【待该 agent 自述】占位（Antigravity/Hermes 附 CC 旁观推断，待各自确认转正）。登记进 `index.md` 第 2 层与 `agent-rules/README.md`。

### 2026-06-14 —— Auto Memory 配置指南（Claude Code, Opus 4.8）

- **[新增] `agent-rules/auto-memory-setup.md`** —— 补齐 [[auto-memory-boundary]] 缺的「怎么配」：三层启用开关（env / settings.json `autoMemoryEnabled` / `/memory`）、一事一文件 + MEMORY.md 索引、frontmatter 字段与 `metadata.type` 四取值、写入/召回/更新/删除触发、与共享 Wiki 的互斥分工。事实区分官方文档确证与【未找到官方来源】两档。同步登记进 `index.md` 第 2 层与 `agent-rules/README.md`（顺带补登原本漏登的 boundary 条目）。

### 2026-06-13 —— repo 治理伴随的 wiki 调整（Claude Code, Opus 4.8）

- **[新增] 领域 `finance/`** —— 金融领域，含 `README.md`（领域范围说明）+ 子领域 `precious-metals/`。同步登记进 `index.md` 与 `wiki-ingest-guide.md` 领域映射表（领域数 7 → 8）。
- **[迁移] `com/dsifo-threshold-logic.md` → `finance/precious-metals/sifo-threshold-logic.md`** —— 原 `com/` 目录命名无意义且领域归类错误。文件重命名为更清晰的 `sifo-threshold-logic`，frontmatter 升级为方案 Z 双字段（domain: finance）。`com/` 已删除。
- **[迁移+重写] `auto-memory-boundary.md` 入 `agent-rules/`** —— 原散落在顶层 `workflows/claude-code-rules/`，升级为正式规则页：补方案 Z frontmatter、去写死 Mac 路径、措辞从"三 Agent"扩为"所有 agent"。
- **[合并] `skill-registry.md` + `skill-catalog.md` → `skill-register.md`** —— 两文件内容重叠易失同步，合并为单一清单（对账 + 全量明细 + Self-Skill 区）。13 处反链已更新。
- **[重写] `index.md`** —— 从过期版（2026-05-21）重写为 8 领域三层索引，摘录各领域高频页，承诺"完整清单见各领域 README"，全部引用经校验零断链。
- **[修改] `wiki-ingest-guide.md`** —— 领域映射表新增 finance 行；去写死路径（详见根 CHANGELOG 的 G 步）。
- **[补登记] `index.md` engineering 摘录** —— 补 `url-fidelity`。

> 已知待下轮：`agent-rules/` 下 4 个 Hermes/finance 特用页 + `engineering/youtube-pipeline-genimages-template-issue` 归类待判；部分旧页 frontmatter 待升级方案 Z。见根 `CHANGELOG.md` 白名单「待下轮处理」。
