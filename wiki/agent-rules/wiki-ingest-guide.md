---
title: Wiki 读写操作指南（Ingest / Query / Health）
domain: agent-rules
type: concept
keywords: [wiki, ingest, query, health, 知识库, frontmatter, 领域, 三agent]
tags: [wiki, ingest, query, health, knowledge-base]
source: 架构设计 2026-05-24
sources: [conversation-2026-05-24]
created: 2026-05-24
updated: 2026-05-24
last_updated: 2026-05-24
---

# Wiki 读写操作指南（Ingest / Query / Health）

> 本页是三个 Agent（Claude Code / Hermes / Antigravity / Gemini CLI）共享的 Wiki 操作宪法。
> 它定义"何时写、写哪、怎么写、怎么读、怎么体检"。所有 Agent 都遵守本规范。
> Hermes 可用 llmwiki skill 加速，但产出必须符合本规范；其他 Agent 按本规范手动执行。
> Wiki 根目录：`/Users/chaojin/Antigravity Projects/Generalrule/wiki/`

---

## 一、Wiki 的本质（先理解再操作）

这个 Wiki 不是 RAG（每次查询临时检索片段再重新合成）。它是 **compounding（复利累积）** 的知识库：源头读一次、提炼成结构化页面、永久保存、交叉链接。下次查询时，交叉引用已经建好、矛盾已经标注、综合已经完成。

三个角色：
- **你（用户）**：curate（策展）—— 决定方向、审阅、拍板。
- **Agent**：read / file / cross-reference / maintain（读取、归档、交叉引用、维护）。
- **Wiki 本身**：codebase（知识的代码库），Obsidian 是 IDE。

---

## 二、INGEST：何时写、写哪、怎么写

### 2.1 何时 Ingest（触发条件）

**强制触发**（对齐 general rule §4 五阶段的 LEARN 阶段）：

1. 用户**纠正**了 Agent（指出错误、否定方案、要求改方向）→ 同时记 lesson + ingest 到 Wiki
2. 公网搜索找到**有价值的解决方案**（可复用的方法、API 用法、工具）
3. 解决了一个**复杂 bug**，方案值得复用
4. 发现**新工具 / 新 API / 新模型**的使用方式
5. 复杂任务（5+ 工具调用）、调试、研究会话结束时

**不要 ingest**：临时状态、时间戳、实现细节琐碎、git 历史、纯调试过程、已在 Wiki 的内容。

### 2.2 写哪个领域（关键词 → 领域映射）

按任务关键词对号入座，写进对应领域目录：

| 关键词命中 | 领域目录 |
|---|---|
| LLM、模型、fallback、配额、429、Prompt、调度 | `wiki/llm/` |
| 前端、HTML、CSS、JS、DOM、剪贴板、渲染、Markdown | `wiki/frontend/` |
| bug 修复、函数签名、架构、接口、重构、部署、GCP、Cloud Run、权限 | `wiki/engineering/` |
| 爬虫、反爬、抓取、清洗、字幕、公众号、YouTube、URL | `wiki/crawler/` |
| 图像、Imagen、生成、风格、信息图、Pillow | `wiki/image-gen/` |
| 设计模式、级联、Producer-Critic、可复用架构 | `wiki/design-patterns/` |
| Agent 规则、workflow、代码规范、本体系自身的规则 | `wiki/agent-rules/` |

### 2.3 何时可以新建子目录（防止乱建）

**默认：不新建目录，写进上面 7 个现有领域之一。**

只有当满足**全部**条件时，才向用户申请新建领域目录：
- 某主题已积累 ≥ 3 个页面
- 且该主题不属于任何现有领域
- 且新建后能明显提升组织清晰度

新建领域目录必须：建 `README.md` 说明该领域范围 + 在 `wiki/index.md` 登记。

> **领域演化（人工决策）**：领域会随项目增长而增减。领域过多、过细、或出现大量交叉时，可能需要合并同类项。这是**人工决策**，health skill 不会自动做（见第五节）。需要时由用户发起，Agent 给出合并建议。

### 2.4 怎么写（统一格式）

**文件命名**：小写 kebab-case，一个概念一个文件（如 `notion-pagination.md`）。

**Frontmatter（方案 Z：双字段兼容）** —— 必须包含以下全部字段：

```yaml
---
title: <人类可读的标题>
domain: <engineering|llm|crawler|frontend|image-gen|design-patterns|agent-rules>
type: <concept|entity|source|synthesis>
keywords: [关键词1, 关键词2]
tags: [关键词1, 关键词2]
source: <来源 URL 或 lesson ID 或简述>
sources: [<来源1>]
created: YYYY-MM-DD
updated: YYYY-MM-DD
last_updated: YYYY-MM-DD
---
```

> 为什么双字段：`domain/keywords/source/created/last_updated` 是本体系的语义；`type/tags/sources/updated` 是 llmwiki skill 的 health 检查所需。两套并存，既清晰又兼容 skill。
> `type` 取值：`concept`（概念/模式/原则）、`entity`（人/工具/系统/项目）、`source`（书/文章/文档摘要）、`synthesis`（跨概念综合分析）。

**正文结构**：

```markdown
（用自己的话综合，不是复制源头。1-3 段讲清核心。）

## 核心规则 / Key Insights
- 要点一
- 要点二

## 正确做法（如适用）
...

## 来源
<lesson ID 或 URL>

## 相关页面
- [[其他wiki页面]]
```

**铁律**：
- 提炼，不复制。distill insights, don't copy.
- 一个概念一个页面，宽泛主题要拆分。
- 优先更新已有页面，而非新建重复页。新建前先搜 `wiki/<领域>/`。
- 每个页面至少有一个 `[[wikilink]]`（避免孤儿页）。
- 写完更新 `wiki/index.md` 索引。

### 2.5 三个 Agent 各自怎么 Ingest

- **Hermes**：可调用 `llmwiki-ingest` skill 加速，但**产出必须符合本规范**（写进领域目录、用方案 Z frontmatter）。skill 已通过 WIKI_PATH 指向本 Wiki。
- **Claude Code**：装了 skill 则用 skill；未装则按本规范手动（读源 → 提炼 → 判断领域 → 写文件 → 更新 index）。
- **Antigravity**：按本规范手动执行（读本 guide → 判断领域 → 写文件 → 更新 index）。

无论用 skill 还是手动，**产出长一样**。

---

## 三、写完后：Git 同步

```bash
cd "/Users/chaojin/Antigravity Projects/Generalrule"
git add wiki/
git commit -m "[Wiki] <一句话描述写入的知识>"
git push origin main
```

由执行 ingest 的 Agent 自己 push（general rule §6 纪律）。

---

## 四、QUERY：怎么读 Wiki

**触发**：任何 debug / 复杂技术问题 / 涉及已有领域的任务，先查 Wiki（general rule §3 五步链路第 2 步）。

**步骤**：
1. 先读 `wiki/index.md` 找相关领域。
2. 读对应领域目录下最相关的页面。
3. 跟随 `[[wikilinks]]` 读关联页面补充上下文。
4. 综合出答案，标注来源「来自 Wiki: <文件名>」。
5. **如果查询中推导出了新知识**：file back（写回 Wiki）—— 这是 Wiki 复利累积的关键。
6. **如果 Wiki 没覆盖**：明确报告"Wiki 缺什么"，再走五步链路的下一步（找 skill / 搜公网）。

> Hermes 可用 `llmwiki-query` skill；其他 Agent 手动按上述步骤。读 Wiki 优先于从零重新推导。

---

## 五、HEALTH：Wiki 体检（及其局限）

**触发**：用户发 `run health` 或 `/wiki-health`。

**health 检查什么**（质量审计）：
1. 孤儿页（没有任何 `[[wikilink]]` 的页面）—— 最严重
2. 断链（指向不存在页面的 `[[链接]]`）
3. 残桩页（正文少于 5 行）
4. 过期页（`updated` 超过 90 天）—— 标记复审，不自动删
5. 缺失 frontmatter 字段

**health 不做什么（重要局限）**：
- ❌ 不做"领域太多帮你合并同类项"
- ❌ 不做架构重构
- ❌ 不判断知识对错

health 是"体检"，不是"重构"。**领域合并、架构精简是人工决策**（见 2.3 领域演化）。需要时由用户发起，Agent 给出建议供你拍板。

> Hermes 可用 `llmwiki-health` skill；其他 Agent 手动按上述清单检查。

---

## 六、相关页面

- general-global-rule.md §3（五步链路）、§4（LEARN 阶段）、§6（Lesson 系统）
- [[five-step-pipeline]] —— 五步链路与五阶段 workflow 细节
- [[skill-registry]] —— 三个 Agent 的 skill 清单与安装（含 llmwiki skill 改造）
