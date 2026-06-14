---
title: 项目标准结构与初始化模板
domain: agent-rules
type: concept
keywords: [项目模板, 初始化, 目录结构, agents.md, 脚手架, scaffold]
tags: [project-template, scaffold, init, agents-md]
source: 架构设计 2026-05-24，参考 ECC 结构
sources: [conversation-2026-05-24]
created: 2026-05-24
updated: 2026-05-24
last_updated: 2026-05-24
---

# 项目标准结构与初始化模板

> 开任何新项目、或在 Hermes Group 新建 channel（≈ 新项目）时，**第一步不是写代码，是按本页建好目录结构**。
> 这样能避免 Agent 乱放文件、随手新建文件夹，导致项目越长越乱。
> 三个 Agent（Claude Code / Hermes / Antigravity）通用。

---

## 一、为什么要先建结构

一个没有预设结构的项目，Agent 会把文件随意乱放：源码、测试、文档、临时脚本混在一起；同一类东西每次放不同地方；找文件靠运气。

预先建好标准结构后，Agent 知道"前端代码该进 `src/`、临时实验该进哪、文档该进 `docs/`"，项目从第一天起就是整洁的，长到几百个文件依然清晰。

**原则：结构先行（structure-first）。先搭骨架，再填血肉。**

---

## 二、标准目录结构
项目名/
├── AGENTS.md          # 项目入口文件（三个 Agent 都读这个）
├── CLAUDE.md          # 符号链接 → AGENTS.md（Claude Code 原生偏好此名）
├── .claude/
│   └── rules/         # 仅本项目特例规则（极少用，见下方说明）
├── src/               # 源码（前端 + 后端都在这，按子目录分）
├── tasks/
│   ├── todo.md        # 当前任务清单（plan 阶段写这里）
│   └── lessons.md     # 本项目踩坑记录（定期升级到全局 Wiki）
├── tests/             # 测试代码
├── docs/              # 项目文档、设计稿、说明
├── scratch/           # 临时文件、实验脚本、一次性产物（不进 git）
├── agents/            # 【占位】未来做 agent 工具包时放子 agent 定义
├── hooks/             # 【占位】未来放触发式自动化钩子
├── commands/          # 【占位】未来放自定义 / 命令
├── .env               # 密钥、API Key（务必 gitignore，绝不提交）
└── .gitignore         # 忽略 .env、scratch/、sessions/、缓存等

---

## 三、每个文件夹放什么（人类友善说明）

**`AGENTS.md`** —— 项目的"说明书"和入口。Agent 每次进项目先读它。它很**薄**：只写这个项目特有的东西（简介、技术栈、常用命令、特殊约定），通用规则全在全局 general rule 和 Wiki 里，不在这里重复。模板见第五节。

**`CLAUDE.md`** —— 不是独立文件，是 `AGENTS.md` 的**符号链接**。因为 Claude Code 原生找 `CLAUDE.md`，而其他工具找 `AGENTS.md`，符号链接让一份内容两个名字都能读。创建：`ln -s AGENTS.md CLAUDE.md`。

**`.claude/rules/`** —— 只放**本项目独有、且只有 Claude Code 在用**的特例规则（配 YAML `paths` glob 按文件类型自动加载）。**绝大多数项目这个目录是空的**——因为通用规则在全局 Wiki，三个 Agent 共享。只有当某个项目有"别的项目都不适用、且必须 Claude Code 自动加载"的怪规则时才用它。

**`src/`** —— 所有源码。**前端代码**放这里（如 `src/frontend/` 或 `src/components/`），**后端代码**也放这里（如 `src/api/`、`src/services/`）。按功能子目录划分，不要把所有文件平铺在根目录。

**`tasks/todo.md`** —— 当前任务清单。五阶段 workflow 的 PLAN 阶段，把计划写这里；Git 检查点的 hash 也记这里顶部。

**`tasks/lessons.md`** —— 本项目踩坑记录。被用户纠正、解决复杂 bug 后，记在这里。定期（或满 30 条时）升级到全局 Wiki（见 [[wiki-ingest-guide]]）。

**`tests/`** —— 测试代码。涉及核心业务逻辑、数据 Schema 的开发必须先写测试（TDD，见 [[python-coding]] 第 6 节）。

**`docs/`** —— 项目文档：设计稿、架构说明、API 文档、需求文档。给人看的长文档放这，不要塞进代码注释。

**`scratch/`** —— **临时文件的家**。一次性实验脚本、调试输出、临时下载的样本、跑完就扔的东西，全放这里。它在 `.gitignore` 里，不会污染版本库。有了它，Agent 就不会把临时文件乱丢到项目根目录或 `src/`。

**`agents/` `hooks/` `commands/`** —— 【占位目录】现在空着。未来当这个项目要做成 agent 工具包时：`agents/` 放专门化的子 agent 定义、`hooks/` 放触发式自动化、`commands/` 放自定义斜杠命令。现在建好占位，未来直接用，不用临时想该放哪。

**`.env`** —— 所有密钥、API Key、Token。**必须在 `.gitignore` 里**，绝不提交到 git（general rule §7 安全铁律）。代码通过环境变量读取，绝不硬编码。

**`.gitignore`** —— 至少忽略：`.env`、`scratch/`、`sessions/`、`__pycache__/`、`node_modules/`、各类缓存。

---

## 四、初始化步骤（Agent 照做）

新项目第一步，Agent 按顺序执行：

1. 读本页，理解标准结构。
2. 建目录：
```bash
   mkdir -p 项目名/{src,tasks,tests,docs,scratch,agents,hooks,commands,.claude/rules}
```
3. 建入口文件：用第五节模板创建 `AGENTS.md`，填入本项目信息。
4. 建符号链接：
```bash
   cd 项目名 && ln -s AGENTS.md CLAUDE.md
```
5. 建 `tasks/todo.md` 和 `tasks/lessons.md`（空文件即可）。
6. 建 `.gitignore`，至少含 `.env`、`scratch/`、`sessions/`、缓存目录。
7. `git init`（如尚未初始化）。

> 本页是纯文档，不提供脚本——这样未来修改结构时只改这一页，不用维护脚本同步。

---

## 五、AGENTS.md 入口模板

项目入口文件 AGENTS.md 的完整模板（多 agent 通用）见 [[AGENTS-template]]。
初始化时复制它到项目根目录，填好项目信息，并建符号链接 `ln -s AGENTS.md CLAUDE.md`。

## 六、相关页面

- general-global-rule.md §5（新项目初始化）、§7（安全禁区）
- [[five-step-pipeline]] —— 任务执行流程
- [[wiki-ingest-guide]] —— lesson 怎么升级到 Wiki
- [[python-coding]] —— 代码规范、TDD
