---
name: llm-wiki
version: 1.0.0-generalrule
description: |
  在「Generalrule 共享 wiki」上做知识复利累积。三模式：Ingest（写入知识）、Query（带复利增强的提问）、Lint+Heal（健康检查+自动修复）。
  已适配 general rule 体系：纯 markdown + Obsidian、领域目录、方案Z双字段 frontmatter、双 GitHub 分流(personal/uber 两 branch)、IP 红线门。无 Quartz、无双语翻译、无 GitHub Pages。
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - AskUserQuestion
  - WebSearch
  - WebFetch
  - Skill
  - Agent
---

# /llm-wiki — Generalrule Wiki 管理器（通用版）

在本机 clone 的 **Generalrule 仓库的 `wiki/` 目录**上 ingest / query / lint。这个 wiki 不是 RAG，是 **compounding（复利累积）** 知识库：源头读一次、提炼成结构化页面、永久保存、交叉链接。

> **本 skill 是通用的，不写死任何机器路径。** 各 agent 按自己环境解析路径（见 Phase 0）。
> 规则真源：Generalrule 仓库内 `wiki/agent-rules/wiki-ingest-guide.md`。
> 本 SKILL.md 与该文件冲突时，**以 wiki-ingest-guide.md 为准**（它是 SSOT，本文件是执行器）。

---

## 通用纪律（贯穿三模式）

- **语言**：所有用户可见沟通 + wiki 正文用【中文简体】。代码标识符、技术术语（Agent/CLI/LLM/MCP/API 等）保持英文。
- **红线门（写入前强制自检）**：写每条 wiki 正文前自问「这条脱离 Uber 还成立吗？」
  - 成立（通用方法论/工程教训/工具用法）→ 可写入。
  - 不成立（Uber 专有数据：OKR、人员名单、内部账号/链接、内部流程细节）→ **不写进个人 repo 正文**。
  - 工具/机制配置（连 repo、push、分支策略）本身是通用能力，不受此限——红线只管**内容**。
- **只读源**：绝不修改 `Source Directories` 里的原始资料。所有写入只落在 wiki 目录。
- **落笔前先读**：写/改任何页面前，先读 `wiki/index.md` 和将要动的目标页（general rule §2.6）。
- **显式失败**：git/search 等命令必须展示真实返回，失败就明说「失败：原因」，禁止用印象填充（general rule §2.10）。

---

## Phase 0: 启动检查（永远先跑）

### 解析本机路径（不写死，按以下顺序自解析）
1. 读 skill 自带配置 `config.md`（同目录；不存在则读 `config.example.md` 取默认结构）。
2. **定位 Generalrule 仓库根**（`REPO_ROOT`）：按本 agent 所在系统去找本机 clone 的 Generalrule 仓库（常见入口：工作区根的 `CLAUDE.md`/`AGENTS.md` 里有指针；或环境变量；或问用户）。**不要假设具体绝对路径**。
3. 据此推导：
   - `WIKI_DIR` = `{REPO_ROOT}/wiki`
   - `WIKI_REPO` = 该仓库的 git remote（`git -C {REPO_ROOT} remote get-url origin`）
4. 分支策略（体系约定，对所有 agent 通用）：
   - `personal_branch` = 私人机所有 agent 用的核心分支
   - `uber_branch` = Uber Mac/VM 所有 agent 用的分支（= 核心分支的超集，多 Uber 专属内容）
   - 当前机属于哪侧、日常 checkout 哪个分支：按本机 clone 的当前分支 + 入口规则判定（`git -C {REPO_ROOT} branch --show-current`）。

依赖检查（静默）：`git --version`。无 git 则停下提示。**不需要 Node.js，不初始化 Quartz。**
若 `REPO_ROOT` 找不到 → 停下问用户本机 Generalrule 仓库在哪，不要猜。

开工同步（进入任何模式前先做；命令对所有机通用）：
```bash
cd "{REPO_ROOT}" && git fetch origin && git merge origin/{personal_branch} && git pull origin {当前分支}
```
有冲突 → 停下问用户，禁止自动 force/merge。

然后进入 Phase 1。

---

## Phase 1: 意图路由

读 `{WIKI_DIR}/index.md` 了解现有结构，判断意图：
1. **问已有知识** → Query Flow
2. **要清理/体检/找空白** → Lint Flow
3. **给新知识/新主题去研究归档** → Ingest Flow

歧义就问用户三选一。

---

## Ingest Flow（写入知识）

### 何时该 ingest（强制触发，对齐五阶段 LEARN + wiki-ingest-guide §2.1）
1. 用户纠正了 Agent（同时记 lesson）；2. 公网找到可复用方案；3. 解决了值得复用的复杂 bug；4. 发现新工具/新API/新模型用法；5. 复杂任务（5+工具调用）/调试/研究会话收尾。
**不要 ingest**：临时状态、时间戳、琐碎实现细节、git 历史、纯调试过程、已在 wiki 的内容。

### Step 1: 领域归类（关键词→领域，不新建话题目录）
按 wiki-ingest-guide §2.2 映射表，对号入座到现有领域目录之一。
**默认不新建目录**。仅当全部满足（某主题已≥3页 + 不属任何现有领域 + 新建明显提升清晰度）才向用户申请新建，并建 README + 在 index.md 登记（§2.3）。需要更细分时按"领域/子领域/页面"建子文件夹（如 `finance/precious-metals/`）。

### Step 2: 红线过滤
对要写的内容逐条过红线门。剔除 Uber 专有具体数据；通用部分保留、必要时脱敏改写（去掉公司/人名/内部链接后是否仍成立）。

### Step 3: 来源收集
- 有 `SOURCE_DIRS`：`find "{dir}" -type f \( -name "*.md" -o -name "*.pdf" -o -name "*.png" -o -name "*.jpg" \) 2>/dev/null`，筛选后列给用户确认。
- 无 SOURCE_DIRS 或资料 <3 条：联网补充（WebSearch，优先 arxiv/官方文档/github），交叉验证。

### Step 4: 写页面（方案Z双字段 frontmatter）
一个概念一个文件，小写 kebab-case。frontmatter 必须含全部字段（wiki-ingest-guide §2.4）：
```yaml
---
title: <页面标题>
domain: <领域之一>
type: concept | entity | source | synthesis
keywords: [关键词, ...]
tags: [tag, ...]
source: <来源描述>
sources: [<来源标识>, ...]
created: YYYY-MM-DD
updated: YYYY-MM-DD
last_updated: YYYY-MM-DD
---
```
正文中文为主。交叉引用用 `[[领域/文件名|显示文字]]`，链接相关页。单源事实标 `⚠️ 待验证`；多源一致才写断言。
**三层索引都要更新**（wiki-ingest-guide §二·五）：写第3层具体页 → 更新第2层 `{领域}/README.md` 列表 → 第1层 `index.md` 确认领域已登记。
在 `wiki/CHANGELOG.md` 追加一行变更记录。

### Step 5: 提交（双 GitHub 分流 + 红线复检）
**push 是不可逆对外动作，执行前停下给用户看 diff 并请求批准（general rule §7）。**
1. 红线复检：`git diff` 全文再过一遍，确认无 Uber 专有数据、无凭据。
2. 选分支：通用知识 → `personal_branch`（核心），再按 §7.5 merge 到 `uber_branch`；仅 Uber 适用的 → 只进 `uber_branch`。
3. commit message：`[Wiki] {领域}: {一句话}`；Uber 机所写 Uber 专属内容 commit 带 `[UB]`。
4. 展示 push 真实返回。失败明说。

---

## Query Flow（提问 + 知识复利）

1. **检索**：读 `{WIKI_DIR}/index.md` → 定位相关页 → 读它们 → 跟随 wikilink。
2. **回答**：综合 + 标注「来自 Wiki: <文件名>」。
3. **自动记录**：追加到 `{WIKI_DIR}/query-stats.json`（不存在先建 `[]`）：
   `{"timestamp":"<ISO>","query":"<问题>","pages_consulted":["<页>"],"tokens_generated":<估算>,"enhancement_type":null,"action_taken":"answered only"}`
4. **评估增强**（阈值：≥3 页 / >500 tokens / 发现矛盾或空白）：A 新建 synthesis；B 增强现有页；C 补交叉引用；D 记知识空白。
5. **执行增强**：C/D 自动（补 wikilink / 写 `knowledge-gaps.md`），A/B 需用户确认。产生新页/改页 → 走 Ingest Step4-5（三层索引 + 红线复检 + 双分支 push，经批准）。

---

## Lint + Heal Flow（健康检查 + 修复）

### Phase 1: 扫描（自动）
读 `{WIKI_DIR}/` 下全部 markdown。检查：①断链 ②孤立页 ③缺概念页（跨页≥2次无对应页，取前5）④矛盾 ⑤知识空白（2-3个答不了的问题）⑥过期（`⚠️ 待验证` 且 >180天）⑦frontmatter 合规（方案Z字段缺失）⑧Query 模式（高频主题无页）⑨Query 归档（>180天记录）。

### Phase 2: 报告
按严重度分组（断链🔴/孤立🟡/缺概念🟡/矛盾🟠/空白🔵/frontmatter🟡/复核⏰/Query📊）。

### Phase 3: 确认修哪些
- **A 类（自动不联网）**：A1 修/删断链；A2 孤立页补入链；A3 补全 frontmatter。
- **B 类（联网）**：B1 生成缺失概念页；B2 填知识空白；B3 补高频 Query 主题。
- **C 类（Query 维护）**：C1 归档 180 天前记录。

### Phase 4: 修复执行
- A 类：直接修。B 类：WebSearch（arxiv/aclanthology > 官方 > github > huggingface）→ 必要时 WebFetch → 交叉验证（≥2源断言/单源标待验证）→ 按 Ingest Step4 写入对应领域（**先过红线门**）+ 附来源，**绝不覆盖现有内容，只追加/新建**。C 类：按季度拆分 query-stats.json。

### Phase 5: 收尾
更新三层索引 + `wiki/CHANGELOG.md` 追加 `## [YYYY-MM-DD] lint+heal | ...`；有改动则走 Ingest Step5 双分支 push（经批准）；给用户改动总结。

---

## 重要规则汇总
- 中文简体沟通 + wiki 正文。**不写死机器路径**（Phase 0 自解析 REPO_ROOT）。
- 领域目录 + 方案Z双字段 frontmatter + 三层索引（见 wiki-ingest-guide）。
- 红线门：写入前逐条判断「脱离 Uber 还成立吗」，Uber 专有数据不进个人 repo。
- 双 GitHub 分流：通用→personal_branch（核心）→merge uber_branch；仅 Uber 适用→只 uber_branch。push 前展示 diff、经批准、展示真实返回。
- 每次操作更新 index.md / 对应 README / wiki/CHANGELOG.md。
- 与 wiki-ingest-guide.md 冲突时以该文件为准。
- 无 Quartz / 无双语翻译 / 无 GitHub Pages。
