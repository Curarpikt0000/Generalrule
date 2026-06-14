---
title: Agent 配置自述矩阵（新 agent 如何配置自己）
domain: agent-rules
type: reference
keywords: [agent-config, 自述, SSOT, 入口, SOUL, 记忆, workflow, skill, onboarding, 多机]
tags: [agent-config, self-report, matrix, onboarding]
source: Prompt A 各 agent 通用自述归集
sources: [conversation-2026-06-14]
created: 2026-06-14
updated: 2026-06-14
last_updated: 2026-06-14
---

# Agent 配置自述矩阵

> **目的**：补齐 SSOT 的「新 agent 如何配置自己」缺口。每个 agent 用 Prompt A 如实自述其配置机制（入口/人格/记忆/workflow/技能/与 repo 关系），归集于此。配新实例时照对应条目抄即可。
> **纪律**：自述以「不知道就说不知道」为准，未确认的标【待该 agent 自述】，不替别的 agent 猜。各 agent 回答后由收集者填入对应小节。
> **采集清单**（9 个目标）：3×CC（家用机/各机）、gemini-antigravity、hermes、cursor、CC-vm、codex-vm、hermes-vm、antigravity-macair、cowork。

---

## 速查矩阵（七维对比）

| 维度 | CC-home（已采集） | Antigravity | Hermes（已自述） | 其余 |
|---|---|---|---|---|
| 入口文件 | `~/.claude/CLAUDE.md`（软链→repo） | `~/.gemini/antigravity/`（待证） | `~/.hermes/SOUL.md` + `config.yaml`（分层级联） | 【待自述】 |
| 人格层 | 无 | 待证 | **有** `~/.hermes/SOUL.md` | 【待自述】 |
| 持久记忆 | Auto Memory（私有） | 待证 | **有** — `~/.hermes/memories/MEMORY.md` + `USER.md` + Hindsight 语义检索 | 【待自述】 |
| 五阶段载体 | superpowers skill | `global_workflows/*.md` | **无内建** — skill 按需加载 + manual 执行 general-global-rule.md §4 | 【待自述】 |
| skill 目录 | `~/.claude/skills/` | `~/.gemini/antigravity/skills/` | `~/.hermes/skills/`（56 个） | 【待自述】 |
| 读 repo 分支 | main | 待证 | **main**（手动 read_file，不自动注入） | 【待自述】 |

> 上表中 Antigravity/Hermes 的"待证"格，来自 CC-home 对它们的旁观推断，**必须由各自 agent 自述确认后才转正**。

---

## CC-home — 家用机 Claude Code（已采集 2026-06-14）

**1.【你是谁】** Claude Code（Anthropic 官方 CLI 编码 agent）；个人**家用机**（macOS darwin），非 Uber；harness = Claude Code CLI，模型 Fable 5（`claude-fable-5`）。

**2.【入口】** 唯一行为入口 `~/.claude/CLAUDE.md`，是**符号链接** → `Generalrule/antigravity/general-global-rule.md`（SSOT 规则在 repo 内、软链注入）。叠加项目级 `CLAUDE.md`/`AGENTS.md`（当前工作目录无）。`~/.claude/settings.json` 管能力开关（权限/autoMemory/通知），非行为规则。**不读 AGENTS.md**。

**3.【人格·SOUL】** **无人格层。** CC 无 SOUL 文件（`~/.claude/` 下无 soul/persona 配置）。SOUL.md 是 Hermes 的机制。CC 的"人格"等价物即 general-global-rule.md 的认知纪律。配新 CC 实例 = 把其 `~/.claude/CLAUDE.md` 软链到同一 general-global-rule.md，无额外人格步骤。

**4.【记忆】** **有 = Auto Memory**（CC 私有）。启用 `settings.json` 的 `autoMemoryEnabled: true`；存 `~/.claude/projects/<project>/memory/`，**一事一文件 + MEMORY.md 索引**，每条带 frontmatter（name/description/metadata.type）。分工：跨 agent 价值→Wiki，仅本机琐事→Auto Memory。细则见 [[auto-memory-setup]]、[[auto-memory-boundary]]。

**5.【workflow】** 五阶段**不用 slash command**（`~/.claude/commands/` 不存在）。载体 = superpowers skill + 规则文本：Explore→`brainstorming`(硬门)、Plan→`writing-plans`(硬门待批)、Execute→`test-driven-development`/`systematic-debugging`、Verify→`verification-before-completion`、Learn→手动按 wiki-ingest-guide 写 Wiki（CC 无自动 promote-lessons）。

**6.【技能】** 装在 `~/.claude/skills/`（每 skill 一目录含 SKILL.md），本机 18 个；发现用 `find-skills`，superpowers 系 `git clone` 拷目录；有官方 plugin marketplace（`~/.claude/plugins/`，enabledPlugins 空）；**MCP 0 个**。全量清单 → [[skill-register]]。

**7.【与 repo 关系】** **深度绑定**——全局规则即 repo 内 `antigravity/general-global-rule.md`（软链）；分支 **main**。有用：`antigravity/general-global-rule.md`、`wiki/agent-rules/`、`wiki/` 各领域库。用不到/建议清理：顶层 `workflows/` 已空（建议删）；`antigravity/` 目录名误导（实为三 agent 通用 general rule + CC 入口，建议改中性名，需同步软链，属牵连操作待确认）。

---

## Antigravity（家用机）— 【待该 agent 自述】

> CC-home 旁观推断（待 Antigravity 自述确认）：入口疑在 `~/.gemini/antigravity/`；skill 在 `~/.gemini/antigravity/skills/`（7+2 个）；五阶段 = `~/.gemini/antigravity/global_workflows/*.md`（8 个：plan-task/verify-done/self-correct/rollback 等）；MCP 有 context7。人格层/记忆/读 repo 分支未知。

## Hermes（家用机）— 已自述 2026-06-14

**1.【你是谁】** Hermes Agent（Nous Research 出品）。个人**家用机**（macOS "Chaos-Big-MacBook-Pro"），local backend。Harness = Hermes Agent 原生框架（Go 网关 + Python/Node 插件栈），通过 Telegram 网关对外服务。

**2.【入口】** 分层级联配置，每层叠加到系统 prompt，不依赖单一文件：
| 优先级 | 层级 | 路径/机制 |
|---|---|---|
| 内置 | 框架预置行为核心 | Hermes 二进制内，不可改 |
| config | config.yaml 的 `display.personality` | `~/.hermes/config.yaml` |
| SOUL | 身份/人格/指针 SSOT | `~/.hermes/SOUL.md` |
| 记忆 | MEMORY.md + USER.md 自动注入 | `~/.hermes/memories/` |
| 项目 | 项目级 AGENTS.md | `./AGENTS.md`（当前 cwd） |
| 规则 | 通用全局规则（不自动读） | SOUL.md 指针指引 agent 手动 `read_file` |
| Skill | 按任务匹配自动加载 | `~/.hermes/skills/<cat>/<name>/SKILL.md` |

**入口核心** = `~/.hermes/SOUL.md`（人格 + 角色 + 沟通纪律 + 指针）+ `~/.hermes/config.yaml`（框架配置 + 模型 + provider）。不读单一 `CLAUDE.md` 或 `AGENTS.md` 作为全局入口。

**3.【人格·SOUL】** **有。** 文件 `~/.hermes/SOUL.md`。标准结构（47 行/1968 字符）：
```
# Hermes 行为核心
## 身份          — 一句话定义我是谁、跑在哪、帮谁干什么
## 沟通规则       — 语言/风格/诚实/边界（中文、先说结论、不确定就说）
## 底线（不可逾越）— 4 条铁律（不改/不删/不假/不可逆）
## 遇到新项目时   — 触发条件 + 起步动作
## 指针          — Generalrule 路径 / Wiki 路径 / 项目模板路径
```
配新实例：在 `~/.hermes/config.yaml` 配好 provider/model/api_key → 创建 `~/.hermes/SOUL.md` → 创建 memories/ 目录 → clone Generalrule 到指定路径 → SOUL.md 写指针。

**4.【记忆】** **有。** 两层：
| 层 | 机制 | 位置 | 格式 |
|---|---|---|---|
| MEMORY.md | 系统 prompt 自动注入。用 `memory`/`hindsight_retain` 写入 | `~/.hermes/memories/MEMORY.md` | 纯文本，`§` 分段，**无 frontmatter，无索引**，上限 2,200 字符 |
| USER.md | 同上 | `~/.hermes/memories/USER.md` | 同上，上限 1,375 字符 |
| Hindsight | 语义检索（向量+关键词混合） | 后端 SQLite | `memory.provider: hindsight` 启用 |

**与 Wiki 分工**：记忆 = 跨 session 的**紧凑事实**（偏好/环境/工具怪癖/上下文碎片），快速衰减；Wiki = 可沉淀的**完整知识**（规则/教训/教程），有 frontmatter + index.md + git 版控，三 Agent 共享。

**5.【workflow】** **无内建五阶段 pipeline。** 通过两个机制落地：
- **Skill 按需加载**：`plan`（写 `.hermes/plans/`）、`test-driven-development`（RED-GREEN-REFACTOR）、`systematic-debugging`（4-phase root cause）。无 slash commands。无 `commands/` 目录。
- **Generalrule §4 定义**：五阶段 + SELF-CORRECT + ROLLBACK + TDD 规则写在 `general-global-rule.md`，每次非琐碎任务前 agent 应手动读取（SOUL.md 指针指引）。**不自动触发**，靠 agent 凭规则文本自身的执行。Hermes 无 brainstroming/writing-plans skill——对应能力由 agent 依据规则文本手动执行。

**6.【技能】** 56 个已装 skill，分类存储在 `~/.hermes/skills/<category>/<name>/SKILL.md`。发现用 `npx skills find <query>`（外部生态）或 `skills_list()` 内置工具。管理用 `skill_manage(action=create/patch/edit/delete)`。系统 prompt 末尾自动嵌入 `<available_skills>` 区块 + 「Before replying, scan the skills below」指令实现自动匹配。MCP 通过 `config.yaml` 的 `mcp.servers` 配置，本机有 Notion/brave-search/playwright 等。

**7.【与 repo 关系】** **读，但不自动加载。** SOUL.md 中写死了三个绝对路径指针（`SOUL.md §指针`），agent 在需要时手动 `read_file`。分支 **main**。通用规则不直接注入系统 prompt——SOUL.md 是 SSOT 入口，Generalrule 在其中引用而非内置。真实使用层级：
- ⭐⭐⭐⭐ `SOUL.md`（每次消息重载）
- ⭐⭐⭐⭐ `wiki/agent-rules/project-template.md`（新项目时强制引用）
- ⭐⭐⭐ `antigravity/general-global-rule.md`（仅非琐碎任务时手动读）
- ⭐⭐ `wiki/index.md`（按五步链路去查）
- ⭐⭐ 各 `wiki/engineering/*`、`wiki/crawler/*`（场景知识，随机命中）
- ⭐⭐⭐⭐⭐ `~/.hermes/skills/` 下 56 个 skill（每次系统 prompt 自动扫描匹配）

建议清理：根 `AGENTS.md` 中的「项目文件归属铁律」（属 COMEX 项目治理非通用 agent 配置），`workflows/` 目录（已空）。

## Cursor — 【待该 agent 自述】
## CC-vm（Uber）— 【待该 agent 自述】
## codex-vm（Uber）— 【待该 agent 自述】
## hermes-vm（Uber）— 【待该 agent 自述】
## antigravity-macair — 【待该 agent 自述】
## cowork — 【待该 agent 自述】

---

## 相关页面

- [[AGENTS-template]] —— 项目入口模板
- [[project-template]] —— 新项目初始化
- [[auto-memory-setup]] / [[auto-memory-boundary]] —— CC 记忆机制
- [[skill-register]] —— 各环境 skill/MCP 全量清单
- [[five-step-pipeline]] —— 五阶段 workflow SOP
