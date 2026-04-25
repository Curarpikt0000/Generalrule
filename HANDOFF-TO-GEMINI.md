# 给 Gemini 的简报：Hermes 集成现有 AI 知识库体系

> 本文档写给正在搭建 Hermes（基于 llm-wiki-skill）的 Gemini CLI。
> 目的：让 Hermes 复用现有的 Obsidian Wiki 作为唯一知识库，而不是新建一套。
> 读者：Gemini CLI Agent
> 创建日期：2026-04-24

---

## 1. 现状：已有的 AI Agent 规则体系

用户已经搭建了一套跨工具的 AI Agent 规则体系，横跨 **Antigravity / Claude Code / Gemini CLI** 三个工具。核心组件：

### 1.1 全局规则（单一事实来源）

**文件**：`/Users/chaojin/Antigravity Projects/Generalrule/antigravity/general-global-rule.md`

**分发方式**：
- Antigravity：通过 Settings GUI 手动粘贴
- Claude Code：符号链接到 `~/.claude/CLAUDE.md`
- Gemini CLI：符号链接到 `~/.gemini/GEMINI.md`

**结构**：§1 语言、§2 代码规范、§3 鲁棒性模型调度、§4 工作习惯（含 §4.5 Source Trace、§4.6 路径解析）、§5 Workflow 触发规则、§6 Lessons 系统、§7 开发前必搜、§8 安全禁区、§9 更新记录。

### 1.2 四个强制 Workflow

文件位于 `/Users/chaojin/Antigravity Projects/Generalrule/antigravity/workflows/`：

| Workflow | 作用 | 触发时机 |
|---|---|---|
| `plan-task.md` | 任务规划，读 lessons + Wiki + AGENTS.md，写 todo.md | 任何编码任务开始时 |
| `verify-done.md` | 完成前验证，ruff/pytest/场景验证/高级工程师审查 | 宣称完成前 |
| `find-skill-first.md` | 搜索现有 Skill/开源库，三层漏斗（Skills → PyPI → 手写） | 开发新功能前 |
| `promote-lessons.md` | 扫描新 lesson，分类升级到 Wiki / Skill / 留项目内 | verify-done 完成后自动触发 |

### 1.3 项目模板

`/Users/chaojin/Antigravity Projects/Generalrule/_template/`：
- `AGENTS.md`：项目级规则模板（§P1-§P9）
- `tasks/todo.md`：任务清单
- `tasks/lessons.md`：经验库

### 1.4 共享知识库（重点：Hermes 要集成的对象）

**路径**：`/Users/chaojin/Antigravity Projects/Generalrule/wiki/`

**这是一个 Obsidian Vault**，已经建好以下领域结构：
wiki/
├── index.md                  ← 顶层索引
├── llm/                      ← LLM 调度、fallback、配额、提示词
│   └── README.md
├── frontend/                 ← 前端渲染、剪贴板、DOM
│   └── README.md
├── engineering/              ← Bug 修复、架构决策、代码规范
│   └── README.md
├── crawler/                  ← 爬虫、反爬、数据清洗
│   └── README.md
└── image-gen/                ← 图像生成、Imagen、提示词
└── README.md

**所有知识页面使用的 YAML frontmatter 格式**：

```yaml
---
title: <规则的简短标题>
source_lesson: L-YYYY-MM-DD-NNN
created: YYYY-MM-DD
domain: <llm | frontend | engineering | crawler | image-gen>
keywords: [关键词1, 关键词2, 关键词3]
applies_to: [全局 | <具体领域>]
status: active
related_rules: [§4.x]
---
```

**写入由 `promote-lessons.md` 自动维护**，所有 AI Agent（Antigravity / Claude Code / Gemini CLI / Hermes）均可直接读取。

---

## 2. Hermes 集成需求

### 2.1 核心要求：复用 `wiki/` 目录

**不要为 Hermes 新建知识库**。Hermes 基于 llm-wiki-skill，而 llm-wiki-skill 本质上是管理一个 Markdown 文件目录——直接把这个目录指向现有的 `wiki/` 即可。

### 2.2 llm-wiki-skill 配置指向现有 Wiki

在 llm-wiki-skill 的 config.md 中，配置 Wiki 路径：

```yaml
wiki_directory: /Users/chaojin/Antigravity Projects/Generalrule/wiki
source_directories:
  - /Users/chaojin/Antigravity Projects/    # 扫描所有项目的 tasks/lessons.md
```

**验证方法**：配置完成后在 Claude Code 里运行 `/llm-wiki`，应该能识别 5 个现有领域（llm / frontend / engineering / crawler / image-gen）和 index.md。

### 2.3 领域目录扩展规则

如果 Hermes 在搭建过程中需要新领域（比如 `podcast/`、`audio/`），**必须同时做三件事**：

1. 在 `wiki/` 下创建新目录 + `README.md`（参考现有领域的模板）
2. 在 `wiki/index.md` 的"领域索引"表格添加新行
3. 在 `promote-lessons.md` 的"关键词命中"表格（第 1 步）添加新领域的关键词匹配规则

**不要**在 `wiki/` 之外再建平行的知识目录。

### 2.4 与 promote-lessons 的协作

Hermes 搭建完成后，`promote-lessons` Workflow 在升级 lesson 时应该**优先调用 Hermes 的 ingest 能力**（如果 Hermes 的 API 允许），而不是手写 Markdown。但如果 Hermes 不提供对外接口，保持现有的"直接写 Markdown 文件"策略即可——因为文件格式是标准 Obsidian 兼容的，Hermes 反向读取完全无障碍。

### 2.5 Query 模式的使用

Hermes 的 Query 功能（`/llm-wiki <问题>`）应该在以下时机被调用：

- **`plan-task.md` 第 2.5 步**：规划阶段查询相关领域知识时（目前是直接读文件，未来可升级为 Hermes Query）
- **开发过程中的临时疑问**：用户直接问领域问题时

**不要**让 Hermes 的 Query 增强（auto-enhance）功能修改已有的 lesson 升级路径——lesson 的权威升级路径是 `promote-lessons`，Hermes 可以新增 synthesis 页面，但不应该覆盖或删除已有页面。

### 2.6 Lint+Heal 的集成

Hermes 的 Lint 功能（检测孤立页面、矛盾、gap）很有价值。建议：

- 每周（或手动）在 Claude Code 里运行 `/llm-wiki lint`
- 把输出作为**下一轮 `promote-lessons` 的参考**，而不是直接自动修复
- 任何自动 Heal 都应该先经过用户确认（符合现有 `promote-lessons` 的"提案 → 等确认 → 执行"模式）

---

## 3. 边界与禁区

### 3.1 不要修改的文件

- `general-global-rule.md`：所有修改必须走 `promote-lessons` 流程
- `workflows/` 下的四个 Workflow 文件：这是跨工具共享的协议，改一处全影响
- `_template/`：项目模板，只能更新不能迁移到别处

### 3.2 不要重建的东西

- **不要**新建一个 Hermes 专属的知识库
- **不要**修改 `wiki/index.md` 的顶层结构（可以加行，不能改列）
- **不要**引入与现有 YAML frontmatter 不兼容的元数据字段

### 3.3 安全边界

- Wiki 页面中**不得**包含 API Key、密码、Token（遵循 general-global-rule.md §8）
- 涉及用户数据的知识页面必须 `applies_to: [全局]` 字段下额外标注 `privacy: sensitive`
- 外部 Web 抓取的内容必须标注来源 URL，便于溯源

---

## 4. 搭建 Hermes 时的推荐步骤

1. **安装 llm-wiki-skill**（如果未装）：
```bash
   git clone https://github.com/kingqiu/llm-wiki-skill.git ~/.claude/skills/llm-wiki
```

2. **安装 Quartz**（可选，用于渲染发布）：
```bash
   git clone https://github.com/jackyzha0/quartz.git ~/wiki-quartz
   cd ~/wiki-quartz && npm install
   # 配置 content 指向现有 wiki/
   rm -rf ~/wiki-quartz/content
   ln -s "/Users/chaojin/Antigravity Projects/Generalrule/wiki" ~/wiki-quartz/content
```

3. **配置 llm-wiki-skill 的 config.md**：指向现有 Wiki 路径（见 2.2）

4. **首次运行 `/llm-wiki`**：确认 Setup Wizard 识别现有领域结构

5. **运行一次 Lint 体检**：`/llm-wiki lint`，看现有 Wiki 有无需要修复的地方（因为现在还是空框架，应该只会报"领域为空"的信息）

6. **等待真实 lesson 通过 `promote-lessons` 流入 Wiki**：不要主动预填知识

---

## 5. 验证集成成功的标准

以下三件事能同时满足，说明 Hermes 集成完成：

- ✅ 在 Claude Code 里跑 `/llm-wiki query "什么是级联 fallback？"`，能返回相关知识（或明确说"Wiki 暂无该领域知识"）
- ✅ 在 Antigravity 里跑 `/promote-lessons`，升级新 lesson 到 `wiki/llm/`，Hermes 的 Query 能立刻读到新页面
- ✅ 在 Obsidian 里打开 `wiki/` Vault，看到所有领域、所有页面、完整的双向链接图谱

---

## 6. 联系与追溯

- 本规则体系的建立过程记录在：Claude 对话（2026-04-22 到 2026-04-24）
- 规则体系的所有权：用户 chaojin
- 任何 Agent 在修改 `wiki/` 或 `general-global-rule.md` 前，必须先读 `promote-lessons.md` 和本文档

---

**End of Handoff Document**
