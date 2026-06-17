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

# Agent 配置自述矩阵（新 agent 如何配置自己）

> **目的**：补齐 SSOT 的「新 agent 如何配置自己」缺口。每个 agent 用 Prompt A 如实自述其配置机制（入口/人格/记忆/workflow/技能/与 repo 关系），归集于此。配新实例时照对应条目抄即可。
> **纪律**：自述以「不知道就说不知道」为准，未确认的标【待该 agent 自述】，不替别的 agent 猜。各 agent 回答后由收集者填入对应小节。
> **采集清单**（9 个目标）：3×CC（家用机/各机）、gemini-antigravity、hermes、cursor、CC-vm、codex-vm、hermes-vm、antigravity-macair、cowork。

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

## CC-home — 家用机 Claude Code（已采集 2026-06-14）

**1.【你是谁】** Claude Code（Anthropic 官方 CLI 编码 agent）；个人**家用机**（macOS darwin），非 Uber；harness = Claude Code CLI，模型 Fable 5（`claude-fable-5`）。

**2.【入口】** 唯一行为入口 `~/.claude/CLAUDE.md`，是**符号链接** → `Generalrule/antigravity/general-global-rule.md`（SSOT 规则在 repo 内、软链注入）。叠加项目级 `CLAUDE.md`/`AGENTS.md`（当前工作目录无）。`~/.claude/settings.json` 管能力开关（权限/autoMemory/通知），非行为规则。**不读 AGENTS.md**。

**3.【人格·SOUL】** **无人格层。** CC 无 SOUL 文件（`~/.claude/` 下无 soul/persona 配置）。SOUL.md 是 Hermes 的机制。CC 的"人格"等价物即 general-global-rule.md 的认知纪律。配新 CC 实例 = 把其 `~/.claude/CLAUDE.md` 软链到同一 general-global-rule.md，无额外人格步骤。

**4.【记忆】** **有 = Auto Memory**（CC 私有）。启用 `settings.json` 的 `autoMemoryEnabled: true`；存 `~/.claude/projects/<project>/memory/`，**一事一文件 + MEMORY.md 索引**，每条带 frontmatter（name/description/metadata.type）。分工：跨 agent 价值→Wiki，仅本机琐事→Auto Memory。细则见 [[auto-memory-setup]]、[[auto-memory-boundary]]。

**5.【workflow】** 五阶段**不用 slash command**（`~/.claude/commands/` 不存在）。载体 = superpowers skill + 规则文本：Explore→`brainstorming`(硬门)、Plan→`writing-plans`(硬门待批)、Execute→`test-driven-development`/`systematic-debugging`、Verify→`verification-before-completion`、Learn→手动按 wiki-ingest-guide 写 Wiki（CC 无自动 promote-lessons）。

**6.【技能】** 装在 `~/.claude/skills/`（每 skill 一目录含 SKILL.md），本机 18 个；发现用 `find-skills`，superpowers 系 `git clone` 拷目录；有官方 plugin marketplace（`~/.claude/plugins/`，enabledPlugins 空）；**MCP 0 个**。全量清单 → [[skill-register]]。

**7.【与 repo 关系】** **深度绑定**——全局规则即 repo 内 `antigravity/general-global-rule.md`（软链）；分支 **main**。有用：`antigravity/general-global-rule.md`、`wiki/agent-rules/`、`wiki/` 各领域库。用不到/建议清理：顶层 `workflows/` 已空（建议删）；`antigravity/` 目录名误导（实为三 agent 通用 general rule + CC 入口，建议改中性名，需同步软链，属牵连操作待确认）。

---

## Antigravity（家用机）— 已自述 2026-06-14

- **你是谁**：Google 原生的 Gemini CLI，Gemini 2.5 Flash/Pro 模型。个人家用机（Ubuntu Docker → ssh）；harness = Gemini CLI（Google MCP 客户端框架）。
- **入口**：平台硬编码 system prompt（含 `<identity>` 人格）→ 工作区 `antigravity/general-global-rule.md` 文件被自动以 `<RULE[user_global]>` 注入 → `~/.gemini/antigravity/.env`（配置文件）→ 项目级 `AGENTS.md`（有则叠加）。**不读 AGENTS.md / CLAUDE.md。无单独的 Custom Instructions / 指令文件**。
- **人格**：**无独立 SOUL 文件**。identity 硬编码在 system prompt `<identity>` 中（你是 project leader / builder，在本地环境运作…）。用户无改动接口。人格 ≈ general-global-rule.md 本身（它被注入为 user_global rule，就是 system prompt 里的行为规范）。
- **记忆**：**无原生持久层**。当前靠 Lesson 系统 + llm-wiki skill 手动写 Wiki（自动上传不成功）。Plan 上下文靠各项目 `tasks/`（context-snapshot.md、lessons.md、todo.md 等，Hermes 留下的）。= 无自动跨 session 检索。
- **workflow**：内置 `planning_mode` 作为 Agentic Workflow 的基座（浏览器 `google.ai` 开关，CLI 不可取消但可调力度多轮）。五阶段 = `planning_mode` + Artifacts：plan 产生 `implementation_plan.md`（`~/.gemini/antigravity/artifacts/`），运行中写 `task.md` + `walkthrough.md`（session 内）。**无单独的 workflow md 文件 / 目录**（不同于旧规则的猜测）。Explore/Plan 依赖规则中的 Scope Clarification 框架 + planning_mode；Execute = `gemini` MCP 文件工具直接实现；Verify = tell 给用户人工；Learn = Lesson + llm-wiki。
- **技能**：在 system prompt `<skills>` 注入（本机 7+2 个 base/background 型，base 为 Cursor 系高效原则等，background 含 No-Code Testing / bug-memo-standard）。对账走 [[skill-register]]。**无 MCP**（未配置）。
- **与 repo**：`Gemini` CLI 直接读写本地工作区 `Generalrule/`（`cd` 进目录启动即用）。分支取决于本地 checkout。有用：`general-global-rule.md` / `wiki/` / `self-skill/`（llm-wiki）/ CHANGELOG / `_template/`。空的 `workflows/` 在它流程里完全没用（Antigravity 用 planning_mode 替代）。

---

## Hermes — 家用机 + Uber-vm 实测（精简版）

- **你是谁**：Hermes Agent（Nous Research 框架，Go 网关 + 插件栈）。家用：MacBook Pro local backend。Uber：`chaojin-hermeschao` DevPod 容器（dinit init），模型 `claude-opus-4-8` 经 Uber GenAI proxy（`localhost:8800/v1`），fallback `deepseek-v4-flash`。对外经 Telegram 网关。
- **入口（级联注入 system prompt，按序）**：①框架预置（二进制内）②`~/.hermes/config.yaml`（`display.personality`）③`~/.hermes/SOUL.md` ④`memories/MEMORY.md`+`USER.md` ⑤项目 `AGENTS.md`（有 workdir 时）⑥全局规则**不自动读**（仅 SOUL.md 指针引用，agent 按需 `read_file`）⑦skills 按需。**无 CLAUDE.md / Custom Instructions 概念**。
- **人格**：**有 = `~/.hermes/SOUL.md`**，自由格式 markdown（无强制 schema），每条消息重载。完整可复用结构（家用机版 47 行）：`# 身份` / `## 沟通规则` / `## 底线（不可逾越）` / `## 遇到新项目时（启动开关）` / `## 指针`。新实例从零配 = ①config.yaml 配 provider/model/key ②建 SOUL.md（身份+沟通+底线+指针）③建 memories/MEMORY.md+USER.md ④（可选）skills/ ⑤需引用 repo 则 clone + SOUL 写指针。改 SOUL 纪律见 [[soul-authoring-guide]]。
- **记忆**：`config.yaml` `memory.memory_enabled:true` + `user_profile_enabled:true`。`memories/MEMORY.md`（agent 笔记）+ `USER.md`（用户画像），**§分隔、无 frontmatter、MEMORY.md 本身即索引**，上限约 2200/1375 字（满则 consolidate）+ 向量检索层（hindsight/holographic SQLite，自动索引检索）。分工：快速衰减→记忆；可复用→Wiki；可编码重复流程→Skill。
- **workflow**：非内置 pipeline。= skill（`software-development/plan`→`.hermes/plans/*.md`、TDD、systematic-debugging）+ general rule §4（SOUL 指针引用、按需读）+ 内置 todo。
- **技能**：`~/.hermes/skills/<cat>/<name>/SKILL.md`（YAML frontmatter，家用 56 / Uber-vm 88）；`npx skills find/add`、`skill_view()`、`skill_manage()`；系统 prompt 末尾自动嵌 `<available_skills>`。
- **与 repo**：读，clone（家用 `~/.hermes/generalrule`，Uber `~/uberhermes/Generalrule`）。家用 main / Uber-vm ub-branch。最高频用：SOUL.md（每条重载）、`project-template.md`（新项目强制引用）、`general-global-rule.md`（非琐碎任务手动读）、skills/。建议不删任何文件——加 `applies_to:` frontmatter 标注适用 agent，让各实例只 ingest 相关部分。

### Hermes 完整版自述（作为上面精简版的详细展开）

**入口核心** = `~/.hermes/SOUL.md`（人格 + 角色 + 沟通纪律 + 指针）+ `~/.hermes/config.yaml`（框架配置 + 模型 + provider）。不读单一 `CLAUDE.md` 或 `AGENTS.md` 作为全局入口。

**SOUL.md 标准结构（47 行/1968 字符）：**
```
# Hermes 行为核心
## 身份          — 一句话定义我是谁、跑在哪、帮谁干什么
## 沟通规则       — 语言/风格/诚实/边界（中文、先说结论、不确定就说）
## 底线（不可逾越）— 4 条铁律（不改/不删/不假/不可逆）
## 遇到新项目时   — 触发条件 + 起步动作
## 指针          — Generalrule 路径 / Wiki 路径 / 项目模板路径
```

**配新实例（checklist）：**
1. `~/.hermes/config.yaml` → 配 provider/model/api_key
2. `~/.hermes/SOUL.md` → 写身份 + 沟通规则 + 底线 + 指针
3. `~/.hermes/memories/MEMORY.md` + `USER.md` → 记忆初始化
4. （可选）`~/.hermes/skills/` → 装技能
5. git clone Generalrule → SOUL.md 写指针引用

**记忆三层详细对比：**
| 层 | 机制 | 位置 | 格式 |
|---|---|---|---|
| MEMORY.md | 系统 prompt 自动注入 | `~/.hermes/memories/MEMORY.md` | 纯文本，`§` 分段，无 frontmatter，上限 2,200 字符 |
| USER.md | 同上 | `~/.hermes/memories/USER.md` | 同上，上限 1,375 字符 |
| Hindsight | 语义检索（向量+关键词混合） | 后端 SQLite | `memory.provider: hindsight` 启用 |

**与 repo 关系详细：** SOUL.md 中写死了三个绝对路径指针，agent 在需要时手动 `read_file`。分支 **main**。通用规则不直接注入系统 prompt——SOUL.md 是 SSOT 入口，Generalrule 在其中引用而非内置。真实使用层级：
- ⭐⭐⭐⭐ `SOUL.md`（每次消息重载）
- ⭐⭐⭐⭐ `wiki/agent-rules/project-template.md`（新项目时强制引用）
- ⭐⭐⭐ `antigravity/general-global-rule.md`（仅非琐碎任务时手动读）
- ⭐⭐ `wiki/index.md`（按五步链路去查）
- ⭐⭐ 各 `wiki/engineering/*`、`wiki/crawler/*`（场景知识，随机命中）
- ⭐⭐⭐⭐⭐ `~/.hermes/skills/` 下 56 个 skill（每次系统 prompt 自动扫描匹配）

建议清理：根 `AGENTS.md` 中的「项目文件归属铁律」（属 COMEX 项目治理非通用 agent 配置），`workflows/` 目录（已空）。

---

## Codex — Uber 实测（codex-vm）

- **你是谁**：Codex（"based on GPT-5"），模型 `gpt-5.4`，provider `aifx`（`genai-api.uberinternal.com/v1`），Harness = Codex Desktop App（cwd `/Users/chao.jin/...`）。
- **入口**：平台隐藏 prompt 层（system/developer/personality/plugin）+ 用户级 `~/.codex/AGENTS.md`（= General Global Rule 副本/链接）+ 项目级 repo `AGENTS.md` + `~/.codex/config.toml`（模型/provider/审批/sandbox）。
- **人格**：**无可见独立 SOUL**。人格层 = 会话级 prompt 注入（结构 personality_spec / Personality / Values / Tone & UX / Escalation）；有 `~/.codex/.personality_migration`（仅记 v1，只证平台有迁移概念，非用户可维护的 SOUL 文件）。
- **记忆**：**有 = SQLite**（非 Markdown 体系）：`~/.codex/memories_1.sqlite`（表 stage1_outputs，字段 raw_memory/rollout_summary/usage_count，当前 0 行）、`state_5.sqlite`（`threads.memory_mode` 默认 `enabled`）、`session_index.jsonl`、`sessions/`。共享知识仍走 Wiki，不依赖本地 memory。
- **workflow**：**无 workflow md / slash 目录**。会话靠 prompt 纪律 + `update_plan` 工具 + Collaboration Mode 落地五阶段。
- **技能**：**无本地 skill 目录**（`~/.codex/skills/` 不存在）。skills 装于 `~/.codex/skills/.system/` + `plugins/cache/`（等于是 Codex Desktop 强制管理的固化区）；安装走 `npx codex skills install <name>`。MCP 0 个。
- **与 repo**：主读 ub-branch（Uber 机，`~/dev/curarpikt/Generalrule`）。有用：`general-global-rule.md`→～`~/.codex/AGENTS.md` 副本（手动 cat 式的复制维系同步）、`wiki/agent-rules/`、`wiki/` 各领域。Codex 无软链能力，靠人力 cat 复制来同步 general rule——这是已知的薄弱环节。

---

## Cursor — 【待该 agent 自述】

> CC-vm 旁证（待 Cursor 自述确认）：入口 = 平台注入 System/Developer/User prompt（开发工具人设定）+ `.cursor/rules/**`（本机有 .cursor/rules/ 目录，但本会话无日志证明工作区自动注入过）。人格 / 记忆：无独立 SOUL 文件、无用户可管理持久层。五阶段 = Cursor 的 Plan Mode / Agent Mode 内置。技能 = 从 Cursor harness 注入工具 + MCP。与 repo：本会话无证据表明 Cursor 读过此 repo。

---

## 已采集横切结论

> 经过本轮（2026-06-14）全部 agent 实测自述，**可以推倒**旧规则以下两条结论：
>
> - **「五阶段由 commands/ 目录的 md 文件承载」** → 错。Hermes 无 commands/，Antigravity 无单独的 worklow md 目录，CC 无 commands/（靠 skill），Codex 无 workflow md——**无一 agent 用 slash commands + md 文件实现五阶段**。
> - **「三个 Agent（CC / Hermes / Antigravity）」** → 过时。现已**实有 5+ agent**（CC 家族 / Hermes / Antigravity / Codex / Cursor），且风格差异远超预期。

---

## 相关页面

- [[AGENTS-template]] —— 项目入口模板
- [[project-template]] —— 新项目初始化
- [[auto-memory-setup]] / [[auto-memory-boundary]] —— CC 记忆机制
- [[skill-register]] —— 各环境 skill/MCP 全量清单
- [[five-step-pipeline]] —— 五阶段 workflow SOP
- [[soul-authoring-guide]] —— SOUL.md 写作指南
