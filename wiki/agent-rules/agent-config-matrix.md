---
title: Agent 配置自述矩阵（新 agent 如何配置自己）
domain: agent-rules
type: reference
keywords: [agent-config, 自述, SSOT, 入口, SOUL, 记忆, workflow, skill, onboarding, 多机]
tags: [agent-config, self-report, matrix, onboarding]
source: 各 agent 第一人称实测自述（Prompt A）归集
sources: [conversation-2026-06-14]
created: 2026-06-14
updated: 2026-06-14
last_updated: 2026-06-14
applies_to: all
---

# Agent 配置自述矩阵

> **目的**：补齐 SSOT 的「新 agent 如何配置自己」缺口。每个 agent 第一人称如实自述其配置机制（入口/人格/记忆/workflow/技能/与 repo 关系），归集于此。配新实例时照对应条目抄即可。
> **采信纪律（重要）**：只采信**第一人称实测**（agent 真读了自己的文件系统）。**严禁替别的 agent 猜**——没有该 agent 本人确认的格子标【待自述】。
> **一次教训（2026-06-14）**：本轮收集时，一份「替全部 9 个 agent 代填」的旁观报告（uber-antigravity 出具）经交叉核对**整张表系编造**（虚构 CC 有 `~/.claude/commands/`+`config.json system_prompt` 且无记忆、Hermes 是 `soul.yaml`、Codex 无记忆、cowork 用 PostgreSQL，还杜撰了 `claude/code-vm` 等 Docker 镜像名），与各 agent 本人实测全面矛盾，**已整份弃用**（教训：只采信第一人称实测，不接受任何 agent 替别的 agent 代填的配置）。

---

## 速查矩阵（按 agent 家族 × 七维；均为第一人称实测）

| 维度 | Claude Code 家族 | Antigravity（Google） | Hermes | Codex | Cursor |
|---|---|---|---|---|---|
| 入口 | `~/.claude/CLAUDE.md`（软链或 @import → repo general rule）±`rules/*.md`±项目 CLAUDE.md | 工作区 `general-global-rule.md` 自动注入 `<RULE[user_global]>`；底层 config 沙箱不可读 | 级联注入：框架预置→`config.yaml`→`SOUL.md`→`memories/`→项目 `AGENTS.md`→skills | 平台隐藏 prompt 层 + `~/.codex/AGENTS.md` + 项目 `AGENTS.md` + `~/.codex/config.toml` | 平台注入 System/Developer/User prompt；`.cursor/rules/**`（本会话无证据加载） |
| 人格层 | **无**（认知纪律即人格） | **无**（identity 硬编码在 system prompt `<identity>`） | **有 `~/.hermes/SOUL.md`**（自由格式 md） | **无**（会话级 prompt 注入 + `.personality_migration`） | **无**（依赖会话 prompt） |
| 持久记忆 | Auto Memory：`~/.claude/projects/<slug>/memory/` md+frontmatter+`MEMORY.md` 索引 | **无原生**（靠 Lesson+llm-wiki 手动写 wiki / `tasks/context-snapshot.md`） | `memories/MEMORY.md`+`USER.md`（§分隔无 frontmatter）+ 向量层（hindsight/holographic SQLite） | SQLite：`memories_1.sqlite`/`state_5.sqlite`/`sessions/`（memory_mode 默认 enabled） | **无**可自管理持久层 |
| 五阶段载体 | superpowers/uberpowers **skill** + 规则文本（**无 commands/**） | 内置 `planning_mode` + Artifacts（`implementation_plan.md`/`task.md`/`walkthrough.md`，session 目录） | skill（plan/TDD/debugging）+ SOUL 内嵌指针 + 内置 todo（**无 slash/独立文件**） | `update_plan` 工具 + prompt 纪律（**无 workflow md**） | Plan Mode（**无自动加载 workflow md**） |
| 技能位置/发现 | `~/.claude/skills/`（每 skill 一 SKILL.md）+ plugin marketplace；`find-skills` | system prompt `<skills>` 注入；对账在 [[skill-register]] | `~/.hermes/skills/<cat>/<name>/SKILL.md`；`npx skills add` / `skill_view()` | `~/.codex/skills/.system/` + `plugins/cache/`；`skill-installer` | Cursor harness 注入工具 + MCP；**不从 repo 装** |
| 读 repo 分支 | 家用机 main / Uber 机 ub-branch | 取决于本地 checkout | 家用机 main / Uber-vm ub-branch（clone `~/uberhermes/Generalrule`） | ub-branch | 不知道（本会话无证据读到 repo） |

> 关键共性：**SOUL 人格层只有 Hermes 有**；**几乎没有 agent 用「commands/ 目录的 md 文件」承载五阶段**——这一点推翻了旧规则的描述（见下方「横切结论」）。

---

## Claude Code 家族（三类实例，机制同源，差异在落地）

CC 三类实例（家用 CC-home / Uber Cowork / Uber devpod CC-vm）**机制同源**：唯一行为入口都落到 repo 的 `antigravity/general-global-rule.md`（SSOT），叠加项目级入口；**无人格层**（认知纪律即人格）；**有 Auto Memory**；五阶段靠 **skill + 规则文本**（无 `~/.claude/commands/`）。配新 CC 实例 = 让其 `~/.claude/CLAUDE.md` 落到同一 general rule + checkout 对应分支，无额外人格步骤。差异如下：

| 实例 | 机器 | 模型 | 入口落地方式 | 分支 | skill/MCP |
|---|---|---|---|---|---|
| **CC-home** | 个人 macOS | Fable 5 | `~/.claude/CLAUDE.md` **软链** → repo general rule | main | `~/.claude/skills/` 18；MCP 0 |
| **Cowork**（Uber Mac Air，Cowork 形态，cwd `~/ClaudeCowork`） | Uber MacBook Air（user `chao.jin`） | Opus 4.8（CLI v2.1.161） | `~/.claude/CLAUDE.md` **软链** + `~/.claude/rules/*.md`（3 个：auto-memory-boundary / ub-machine-paths / uber-adaptation 软链） | ub-branch | `~/.claude/skills/` 17 咨询 + claude-plugins-official marketplace |
| **CC-vm**（本页归集者，Uber devpod） | Uber devpod（linux） | Opus 4.8 [1m] | `~/.claude/CLAUDE.md`（**实体文件**）→ `~/claudecodeuber/CLAUDE.md` **@import** repo general rule + uber-adaptation；**无 rules/** | ub-branch | `~/.claude/skills/` 33；uberpowers 生态 + omni-mcp |

- **记忆**：CC-home memory 目录已建当前空；Cowork slug `-Users-chao-jin-ClaudeCowork` 目录待首次写入创建；CC-vm Auto Memory **已激活**（`~/.claude/projects/-home-user-claudecodeuber/memory/` 现 4 条 + `MEMORY.md`）。格式：一事一文件 + frontmatter（name/description/metadata.type）+ `MEMORY.md` 索引。配置/边界见 [[auto-memory-setup]] / [[auto-memory-boundary]]。
- **真实存在的 slash command** 是 harness/plugin 自带（`/code-review` `/verify` `/run` `/init` `/security-review` `/loop` `/schedule` 等），**不是**体系定义的五阶段命令。

---

## Antigravity（Google）— 家用机实测（gemini-antigravity）

- **你是谁**：Antigravity（Google DeepMind 自主编码 agent）；个人 Mac（`~/.gemini/antigravity`）；Google Antigravity 平台管生命周期。
- **入口**：工作区 `general-global-rule.md` 每次启动**自动注入** system prompt（`<RULE[user_global]>`）。底层 `config.yaml` 等因安全沙箱 **Permission denied 不可读**（对 agent 透明）。
- **人格**：**无人格层**。基本人格 = 系统内置 prompt `<identity>` 标签（硬编码、不可改）；项目行为靠注入的 general rule。
- **记忆**：**无原生自动记忆**。沉淀靠 general rule Lesson 系统 + `llm-wiki` 手动写 `wiki/` 或 `tasks/context-snapshot.md`。
- **workflow**：内置 `planning_mode` + Artifacts。非琐碎任务自动进 Planning Mode，维护三个 Markdown 伪文件（Artifacts，存 session brain 目录）：`implementation_plan.md`（PLAN 阶段 `request_feedback=true` 阻塞待批）/ `task.md`（`[ ]`/`[/]`/`[x]` TODO）/ `walkthrough.md`（完成总结）。**不是** `commands/*.md` 或 `global_workflows/*.md`（后者为 CC 旁观推断，本人未证实）。
- **技能**：system prompt `<skills>`/`<plugins>` 标签注入可用 skill；对账在 [[skill-register]]；缺核心 skill 时列命令、经用户批准再装；通用 skill 收 `self-skill/`。
- **与 repo**：直接读写本地工作区 `Generalrule/`，分支取决于本地 checkout。有用：`general-global-rule.md` / `wiki/` / `self-skill/`（llm-wiki）/ CHANGELOG / `_template/`。空的 `workflows/` 在它流程里完全没用（Antigravity 用 planning_mode 替代）。

> antigravity-macair（Uber Mac Air 上的 Antigravity）：**机制应同上**，但**无该实例第一人称自述**（本轮唯一一份标称它的报告即上文已弃用的编造件）。标【待 antigravity-macair 本人自述确认】。

---

## Hermes — 家用机 + Uber-vm 实测

- **你是谁**：Hermes Agent（Nous Research 框架，Go 网关 + 插件栈）。家用：MacBook Pro local backend。Uber：`chaojin-hermeschao` DevPod 容器（dinit init），模型 `claude-opus-4-8` 经 Uber GenAI proxy（`localhost:8800/v1`），fallback `deepseek-v4-flash`。对外经 Telegram 网关。
- **入口（级联注入 system prompt，按序）**：①框架预置（二进制内）②`~/.hermes/config.yaml`（`display.personality`）③`~/.hermes/SOUL.md` ④`memories/MEMORY.md`+`USER.md` ⑤项目 `AGENTS.md`（有 workdir 时）⑥全局规则**不自动读**（仅 SOUL.md 指针引用，agent 按需 `read_file`）⑦skills 按需。**无 CLAUDE.md / Custom Instructions 概念**。
- **人格**：**有 = `~/.hermes/SOUL.md`**，自由格式 markdown（无强制 schema），每条消息重载。完整可复用结构（家用机版 47 行）：`# 身份` / `## 沟通规则` / `## 底线（不可逾越）` / `## 遇到新项目时（启动开关）` / `## 指针`。新实例从零配 = ①config.yaml 配 provider/model/key ②建 SOUL.md（身份+沟通+底线+指针）③建 memories/MEMORY.md+USER.md ④（可选）skills/ ⑤需引用 repo 则 clone + SOUL 写指针。改 SOUL 纪律见 [[soul-authoring-guide]]。
- **记忆**：`config.yaml` `memory.memory_enabled:true` + `user_profile_enabled:true`。`memories/MEMORY.md`（agent 笔记）+ `USER.md`（用户画像），**§分隔、无 frontmatter、MEMORY.md 本身即索引**，上限约 2200/1375 字（满则 consolidate）+ 向量检索层（hindsight/holographic SQLite，自动索引检索）。分工：快速衰减→记忆；可复用→Wiki；可编码重复流程→Skill。
- **workflow**：非内置 pipeline。= skill（`software-development/plan`→`.hermes/plans/*.md`、TDD、systematic-debugging）+ general rule §4（SOUL 指针引用、按需读）+ 内置 todo。
- **技能**：`~/.hermes/skills/<cat>/<name>/SKILL.md`（YAML frontmatter，家用 56 / Uber-vm 88）；`npx skills find/add`、`skill_view()`、`skill_manage()`；系统 prompt 末尾自动嵌 `<available_skills>`。
- **与 repo**：读，clone（家用 `~/.hermes/generalrule`，Uber `~/uberhermes/Generalrule`）。家用 main / Uber-vm ub-branch。最高频用：SOUL.md（每条重载）、`project-template.md`（新项目强制引用）、`general-global-rule.md`（非琐碎任务手动读）、skills/。建议不删任何文件——加 `applies_to:` frontmatter 标注适用 agent，让各实例只 ingest 相关部分。

---

## Codex — Uber 实测（codex-vm）

- **你是谁**：Codex（"based on GPT-5"），模型 `gpt-5.4`，provider `aifx`（`genai-api.uberinternal.com/v1`），Harness = Codex Desktop App（cwd `/Users/chao.jin/...`）。
- **入口**：平台隐藏 prompt 层（system/developer/personality/plugin）+ 用户级 `~/.codex/AGENTS.md`（= General Global Rule 副本/链接）+ 项目级 repo `AGENTS.md` + `~/.codex/config.toml`（模型/provider/审批/sandbox）。
- **人格**：**无可见独立 SOUL**。人格层 = 会话级 prompt 注入（结构 personality_spec / Personality / Values / Tone & UX / Escalation）；有 `~/.codex/.personality_migration`（仅记 v1，只证平台有迁移概念，非用户可维护的 SOUL 文件）。
- **记忆**：**有 = SQLite**（非 Markdown 体系）：`~/.codex/memories_1.sqlite`（表 stage1_outputs，字段 raw_memory/rollout_summary/usage_count，当前 0 行）、`state_5.sqlite`（`threads.memory_mode` 默认 `enabled`）、`session_index.jsonl`、`sessions/`。共享知识仍走 Wiki，不依赖本地 memory。
- **workflow**：**无 workflow md / slash 目录**。会话靠 prompt 纪律 + `update_plan` 工具 + Collaboration Mode 落地五阶段。
- **技能**：运行时注入 "Available skills"；`~/.codex/skills/.system/`（imagegen/openai-docs/plugin-creator/skill-creator/skill-installer）+ `~/.codex/plugins/cache/<plugin>/<ver>/skills/`；默认装到 `~/.codex/skills/<name>`（装后需 Restart）。
- **与 repo**：正在读 Generalrule，分支 **ub-branch**。用 `~/.codex/AGENTS.md`、repo `AGENTS.md`、`wiki/index.md`、`five-step-pipeline.md`、`skill-register`。建议：**不要因「我用不到」删文件**（对 Hermes/Antigravity 有用）；本质是「补一页对照表」而非「删文件」。

---

## Cursor — Uber 实测（cursor-vm）

- **你是谁**：Cursor IDE coding agent，模型 GPT-5.5；运行环境 Linux 6.12.68+ / zsh；**机器归属不知道**（无法判断个人/Uber）。
- **入口**：平台注入 System / Developer / User prompt（不在 repo 文件里）+ Cursor 附加上下文（打开文件/诊断）。**本会话无证据**自动读取 repo。可能相关入口：`.cursor/rules/**`、Cursor Project/User Rules、显式 `@AGENTS.md`/`@CLAUDE.md`。
- **人格**：**无独立人格层**。人格来自会话 system/developer instructions。若要给 Cursor 配 SOUL，**别假设它自动读某个 SOUL.md**——须接入 Cursor 确认会加载的机制（`.cursor/rules/persona.mdc` / User Rules / 显式引用）。
- **记忆**：**无**可自管理持久记忆层；跨会话不保证记住。
- **workflow**：五阶段非内置；可落地为 Explore（读/搜）→Plan（Plan Mode）→Execute（编辑工具）→Verify（测试/lint/诊断）→Learn（按需写回）。无自动加载的 workflow md。若 repo 要支持 Cursor，建议放 `.cursor/rules/*.mdc`（workflow/persona/git-discipline/verification）。
- **技能**：能力来自 Cursor harness 注入工具（ReadFile/ApplyPatch/rg/Glob/Shell/ReadLints/Subagent/MCP）+ MCP descriptor；**技能清单不在 repo**。
- **与 repo**：本会话**没读到** repo；分支/workspace/是否 git repo 均未知。对它有用：`.cursor/rules/*.mdc`、明确给 Cursor 的 `AGENTS.md`、简短 workflow/git/验证文档。建议**不要直接删**别 agent 的文件——按 agent 分入口，并在 wiki 标注「自动加载 / 手动引用 / 仅文档」。

---

## 横切结论（可直接落进规则的事实）

1. **人格层只有 Hermes 有**（`~/.hermes/SOUL.md`，自由格式 markdown）。CC / Antigravity / Codex / Cursor 全无独立 SOUL——「人格」= general rule 认知纪律或平台 system prompt 注入。→ 想要「跨 agent 统一人格」，只能继续靠 general rule 承载 + Hermes 用 SOUL 指针引用它；不要假设其他 agent 会读某个 SOUL 文件。
2. **持久记忆机制各不相同**：CC=Auto Memory（md+frontmatter+索引）、Hermes=MEMORY/USER.md（§分隔）+向量、Codex=SQLite、Antigravity=无原生（手动 wiki）、Cursor=无。→ 跨 agent 共享知识**只能走 Wiki**，不能依赖任一 agent 的本地记忆。
3. **「五阶段 = commands/ 目录 md 文件」是错的**：实测无任何 agent 这样用。CC=skill、Antigravity=planning_mode+Artifacts、Hermes=skill+SOUL 内嵌、Codex=update_plan 工具、Cursor=Plan Mode。规则原描述（`five-step-pipeline.md`、general rule §4）已据此修正。
4. **不要因「我用不到」删文件**（Codex/Hermes/Cursor 共识）。更优解：每文件 frontmatter 加 `applies_to:` 标注适用 agent + 状态（自动加载 / 手动引用 / 仅文档）。
5. **去中心化同步**：所有 agent 经个人 GitHub repo（main / ub-branch）同步规则，不互读对方文件系统。

---

## 相关页面

- [[soul-authoring-guide]] —— SOUL 写作指南 + SOUL.md 模板（Hermes 机制）
- [[auto-memory-setup]] / [[auto-memory-boundary]] —— CC 记忆配置与边界
- [[skill-register]] —— 各环境 skill/MCP 全量清单
- [[five-step-pipeline]] —— 五阶段 workflow SOP（各 agent 载体差异已修正）
- [[AGENTS-template]] / [[project-template]] —— 项目入口模板与初始化
