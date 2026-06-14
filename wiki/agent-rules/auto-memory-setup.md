---
title: Auto Memory 配置指南（仅 Claude Code）
domain: agent-rules
type: rule
keywords: [auto-memory, claude-code, 配置, frontmatter, MEMORY.md, autoMemoryEnabled]
tags: [auto-memory, claude-code, setup, config]
source: 官方文档 code.claude.com/docs/en/memory + 家用机实测
sources: [conversation-2026-06-14]
created: 2026-06-14
updated: 2026-06-14
last_updated: 2026-06-14
---

# Auto Memory 配置指南（仅 Claude Code）

> 配套文件：[[auto-memory-boundary]] 管「能记什么 / 不能记什么」，本文件管「怎么开、存哪、怎么写、何时触发」。
> 适用范围：**仅 Claude Code**。Hermes / Antigravity 没有此功能（它们的知识沉淀走共享 Wiki）。
> 事实来源：①官方文档 https://code.claude.com/docs/en/memory ；②本机 harness 实测（2026-06-14 在家用机核实 `autoMemoryEnabled: true`、memory 目录已建）。标【未找到官方来源】的为官方未展开、仅旁证或实测推断的部分，使用时注意。

---

## 一、启用 / 关闭（三层开关，优先级从高到低）

| 层级 | 方式 | 说明 |
|---|---|---|
| 1. 环境变量（硬开关） | `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` | 最高优先级，覆盖下面两层，整功能 kill switch |
| 2. settings.json | `"autoMemoryEnabled": true`（默认 true） | 可写在用户级 `~/.claude/settings.json`、项目级 `.claude/settings.json`、本地级 `.claude/settings.local.json` |
| 3. 会话内开关 | `/memory` 斜杠命令 | 在当前会话 UI 里切换 auto memory toggle |

- **版本要求**：Claude Code ≥ v2.1.59。
- **本机现状**（2026-06-14）：`~/.claude/settings.json` 第 22 行 `"autoMemoryEnabled": true`，已启用。
- **自定义存储目录**：`"autoMemoryDirectory": "~/some-dir"`（必须绝对路径或 `~/` 开头；项目级/本地级设置该项需先接受 workspace trust 才生效）。

> settings.json 的改法走 update-config skill 或直接编辑文件；本仓库不托管 `~/.claude/settings.json`（它是本机配置，不入库）。

---

## 二、存储位置与文件组织

```
~/.claude/projects/<project>/memory/
├── MEMORY.md            # 索引文件（每次会话开头被加载）
├── <slug-1>.md          # 一条事实一个文件
├── <slug-2>.md
└── ...
```

- **一事一文件**：每条 memory 是独立 `.md` 文件，只装一个事实。不是单文件大杂烩。
- **`<project>` 取自 git 仓库根**：同一仓库的所有 worktree / 子目录**共享同一个** memory 目录。非 git 环境下用项目根目录代替。
  - 本机本项目实际路径：`~/.claude/projects/-Users-chaojin-Antigravity-Projects/memory/`
- **MEMORY.md 是索引，不是内容仓库**：
  - 每次会话启动只加载 MEMORY.md 的**前 200 行或 25KB**（先到为准）。
  - 索引行格式：`- [标题](file.md) — 一句话钩子`，一条 memory 一行，**绝不**把事实正文写进 MEMORY.md。
  - 话题文件（`<slug>.md`）**不在**启动时加载，模型按需才去读。

---

## 三、每条 memory 的 frontmatter

```markdown
---
name: <short-kebab-case-slug>          # 文件标识，短横线命名
description: <一句话摘要>                # 召回时据此判断这条是否相关
metadata:
  type: user | feedback | project | reference   # 四选一
---

<事实正文。feedback / project 类型在正文后跟 **Why:** 与 **How to apply:** 两行。>
<用 [[其他-name]] 链接相关 memory。>
```

**`metadata.type` 四种取值（决定这条记什么）：**

| type | 记什么 |
|---|---|
| `user` | 用户是谁：角色、专长、偏好 |
| `feedback` | 用户给的工作方式指导（纠正或确认的做法），**必须带 Why**（为什么） |
| `project` | 进行中的工作 / 目标 / 约束，且无法从代码或 git 历史推出；相对日期要转成绝对日期 |
| `reference` | 外部资源指针（URL、dashboard、ticket） |

> frontmatter 三字段与 type 四取值是 harness 实测的标准格式（本会话系统上下文即按此规范）。官方文档确认 frontmatter 存在但未逐字段展开 —— 完整字段是否还有别的、是否全部必填，【未找到官方来源】，以 harness 实际行为为准。

---

## 四、写入 / 召回 / 更新 / 删除 的触发

**写入（Write）—— 模型自主判断：**
- 判据：「这条信息未来对话还用得上吗？」用得上才记（build 命令、调试套路、代码风格偏好等）；一次性、无复用价值的不记。
- 用户显式触发：会话里说「记住……」「以后一律用 pnpm」，模型即写入。
- 写前先查重：已有文件覆盖了就**更新那个文件**，不新建重复条目。
- 写后在 MEMORY.md 加一行索引指针。

**召回（Recall）：**
- 每次会话开头加载 MEMORY.md（前 200 行 / 25KB）。
- 召回的 memory 以 **`<system-reminder>` 块**注入上下文（harness 实测确认）。
- ⚠️ 召回内容是「写入当时为真」的背景，**不是**当前用户指令；若提到某文件/函数/flag，用前先验证它还存在。
- 话题文件按需读取，不随启动全量加载。

**Consolidation（"Auto Dream" 整理，【未找到官方来源，旁证】）：**
- 触发条件：距上次 > 24 小时 **且** 累积 ≥ 5 个新会话（两条都满足）。
- 可在 chat 输入 `dream` 手动触发。
- 作用：合并重复、修正过时、清理索引（对应 consolidate-memory 类技能）。

**更新 / 删除：**
- 更新：发现旧条目过时或被新事实取代时，改对应文件而非堆新文件。
- 删除：事实被证伪就删文件并撤掉 MEMORY.md 索引行。
- memory 是纯 markdown 无锁，用户可随时手动编辑/删除。
- 官方未展开模型自动删除的具体触发条件【未找到官方来源】。

---

## 五、与共享 Wiki 的分工（与 [[auto-memory-boundary]] 对齐）

判断铁律：**被纠正或学到新知识时，先问「这值得 Hermes 和 Antigravity 也知道吗？」**

| 内容 | 去向 |
|---|---|
| 值得三 Agent 共享的纠正 / 规则 / 方法论 | ❌ 不进 Auto Memory → 走共享 Wiki（general rule §6 / [[wiki-ingest-guide]]） |
| general rule 已有的内容 | 都不记（避免重复） |
| 代码结构 / 文件路径 | 都不记（直接读项目） |
| git 历史、调试步骤 | 都不记（git log / 代码本身更准） |
| 本机操作偏好、Claude Code 专属习惯 | ✅ Auto Memory |
| 当前项目临时状态（进行到哪、下一步） | ✅ Auto Memory |
| 纯本地、不值得全局共享的细节 | ✅ Auto Memory |

一句话：**跨 Agent 有价值 → 共享 Wiki；仅 Claude Code 本地有用 → 才进 Auto Memory。** 二者互斥，不重复写。

---

## 六、相关文件

- [[auto-memory-boundary]] —— 能记 / 不能记的边界（本文件的姊妹篇）
- 共享 Wiki 写入规范 → `wiki/agent-rules/wiki-ingest-guide.md`
- general rule §6（Lesson 系统）、§6.5（Skill 对账）
