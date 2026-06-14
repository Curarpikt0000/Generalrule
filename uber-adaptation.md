# Uber 环境适配层（仅 Uber 电脑，存在于 ub-branch，不进 main）

> 叠加在共享 general-global-rule.md 之上。general rule（认知纪律/五阶段/Lesson）原样遵守，本文件只补 Uber 环境差异。

## 开工同步纪律（本机日常在 ub-branch）
- 本机日常 checkout `ub-branch`（= main 全部内容 + 本文件）。
- 开工前：`git fetch origin && git merge origin/main && git pull origin ub-branch`。
- 通用认知纪律 / 通用 Wiki 知识 → 切到 main 提交并 push，再切回 ub-branch merge main。
- 本文件（Uber 适配）改动 → 直接在 ub-branch commit + push。

## 工具替换映射（Uber 机器上，重复就用公司的）
- superpowers → Uber 原生 uberpowers（aifx plugin add uberpowers）
- RTK token 压缩 → code-mode（aifx plugin add code-mode）
- skill-creator → skill-workshop
- MCP → omni-mcp（一个连接通 415+ servers）
- find-skills → 装 find-skills，装新 skill 前先查重
- 没有 Uber 等价物的（如写个人 GitHub wiki 的 wiki-update）→ 用个人的 / 手动按 wiki-ingest-guide

## Uber 机实际安装清单（VM 对账 2026-06-08）

> Uber 专属 skill / plugin 全量明细。按 IP 隔离不进 main——main 的 `skill-register.md` 指向本处。
> （本节由 2026-06-14 合并 main 治理时，从已废弃的 `skill-registry.md`[UB] 增量迁入。）

- **aifx plugin（12 个）**：alert-rca, ci-debugger, code-mode, data-analyst, find-skills, minion-dev, omni-mcp, page-publisher, skill-workshop, uber-dev, uber-reviewer, uberpowers
- **Claude Code skills（`~/.claude/skills/`，17 个咨询框架）**：consulting, management-consultant, issue-tree-builder, hypothesis-tree, synthesis, top-down-memo, decision-memo-builder, scpr-framework, storyline-builder, deck-pipeline, mckinsey-charts, mckinsey-critic, prioritization, ai-use-case-scorer, meeting-prep-kit, stakeholder-map, workshop-designer
  - 来源：`yoichiojima-2/consultant`（consulting）、`charlie989898/-mbb-management-consultant-claude-skill`（management-consultant）、`sruthir28/enterprise-ai-skills`（其余 15 个）。
- **omni-mcp 双注册**：`aifx plugin add omni-mcp`（plugin）+ `aifx mcp add omni-mcp --skip-validation`（注册编辑器）。

### Codex VM 接入实测（2026-06-14）

- **Generalrule clone**：`/home/user/codexvm/General-Global-Rule`，checkout `ub-branch`。
- **Codex 入口**：`/home/user/.codex/AGENTS.md` + `/home/user/AGENTS.md`，两者只写 SSOT 指针，指向 `antigravity/general-global-rule.md` 与本 repo 根。
- **aifx plugin（3 个）**：uberpowers、skill-workshop、find-skills。
- **Codex skills**：系统内置 `imagegen`、`openai-docs`、`plugin-creator`、`skill-creator`、`skill-installer`；本次接入新增 `~/.codex/skills/llm-wiki`（来自 `self-skill/llm-wiki`，本机 `config.md` 留空路径，由入口指针解析）。
- **未注册 MCP**：本次未执行 `aifx mcp add omni-mcp --skip-validation`；若任务需要 MCP，再按 §7 不可逆动作纪律经用户确认后安装。

## 双 GitHub 分流（各干各的，不混）
- 个人仓库 Curarpikt0000/Generalrule：只放 general rule / workflow / wiki 总结
  - 通用认知纪律、通用 wiki → push main
  - Uber 适配（本文件）→ push ub-branch
- 公司 GitHub（chao.jin@uber.com）：所有 Uber 项目代码，完全独立
- Antigravity 在本机产出的 Uber 项目代码 → 公司 GitHub（各项目目录单独 `git config user.email "chao.jin@uber.com"`）或本地存放；绝不进个人仓库

## 红线（Uber IP 保护，最重要）
- 个人仓库**绝不放 Uber 代码、内部数据、Uber 专有流程**（内部工具/skill 名称除外，用户已批准）。
- 写个人 wiki 前自问：这条脱离 Uber 也成立吗？不成立 → 不进个人仓库。
- Uber 项目代码一律 push 公司 GitHub。

## 认知纪律 / 五阶段 workflow / Lesson
→ 完全遵守 main 上的 general-global-rule.md，与家里一致。

## VM 工作区目录纪律（devpod）
- 工作区根（如 `~/claudecodeuber/`）只放：根入口 `CLAUDE.md` + 各任务文件夹，**不放散文件**。
- 命名：正式项目 `project-<名>/`；临时对话/实验 `temp-<日期>-<主题>/`；数据分析 `data-analysis/<主题>/`。
- 新任务第一步先建文件夹再动手（呼应 general rule §5）；项目内部结构按 `wiki/agent-rules/project-template.md`。
- Generalrule 仓库在 VM 上**独立 clone**（checkout ub-branch），与本地 Mac 互不依赖，经 GitHub 同步。

## 本环境运行时拓扑（Uber 侧 agent 分布）

> 记录 Uber 侧 agent 分布。仅环境事实，认知纪律仍归 main 的 general rule。各 agent 的入口/人格/记忆/技能配置见 [[agent-config-matrix]]，本处不重复。
> 标注依据：2026-06-14 各 agent 第一人称实测；【未自述】= 该实例本人未确认，按同类机制推断。

| 运行时 | 宿主 | 角色 | 分支 |
|---|---|---|---|
| Cowork（Claude Code，Cowork 形态，cwd `~/ClaudeCowork`） | 物理机 MacBook Air（用户名 `chao.jin`） | Uber 编码（咨询 skill + uberpowers） | ub-branch |
| Antigravity | 同一物理机 MacBook Air | Uber 项目架构 / 编码 | 取决于本地 checkout【未自述确认】 |
| Claude Code（CC-vm，本页归集者） | 独立 devpod VM（linux） | Uber 项目编码（aifx / uberpowers / omni-mcp） | ub-branch |
| Codex | Codex Desktop App（gpt-5.4，aifx provider） | Uber 编码 | ub-branch |
| Hermes | DevPod 容器 `chaojin-hermeschao`（dinit） | Uber 知识检索 / wiki 辅助 | ub-branch（clone `~/uberhermes/Generalrule`） |
| Cursor | 宿主未知（GPT-5.5） | Uber 编码 | 未知（本会话无证据读到 repo） |

- 各 agent 互不依赖，全部经个人 GitHub 仓库（ub-branch）同步规则，不互相读对方文件系统。
- 物理机用户名是 `chao.jin`（含点），与家用机 `chaojin` 不同；写路径勿照搬。
- **更正（实测）**：旧版把唯一一条 Claude Code 标为「devpod VM」，实际 Uber 侧有两类 CC——物理机 Mac Air 上的 **Cowork** 形态 + 独立 **devpod VM** 上的 CC-vm，二者均 ub-branch。
- **这些 agent 均为做 Uber 工作而设，可正常读写 Uber 代码 / 内部文档 / 内部数据。**

### 唯一红线：Uber 内容不进个人 GitHub 仓库
- Uber 项目代码、内部数据、专有流程 → 一律 push **公司 GitHub**（`chao.jin@uber.com`），或本机/VM 本地存放。
- 个人仓库 `Curarpikt0000/Generalrule` 只放脱离 Uber 也成立的通用规则 / wiki（内部工具名称除外，已批准）。
- 写个人 wiki 前自问：这条脱离 Uber 也成立吗？不成立 → 不进个人仓库。

### Hermes 模型出境（据 Uber-vm 实测更新）
- Uber hermes-vm 实测：**主模型 `claude-opus-4-8`，经 Uber 内部 GenAI proxy（`localhost:8800/v1`）**——主路径**不出公司边界**。
- **fallback `deepseek-v4-flash` 为第三方**：一旦回退，上下文会发往 DeepSeek 出境。让 Hermes 处理 Uber 内部数据时，须确保不触发第三方 fallback，或先经 Cortana / 公司政策确认是否允许。
- 家用机 Hermes 用个人模型，仅处理通用知识 / 个人 wiki，无此约束。

## 上下文持久化方案（断网/SSH 断裂不丢上下文，仅 Uber 机/agent）

> **目标**：断网、SSH 断裂、重开电脑/VS Code 后，每个 agent 能**按 agent + 按项目**找回自己的对话上下文。
> **红线**：本方案依赖 Uber 内部存储（terrablob），**仅 Uber 机/agent 可用**；个人机/家用 agent 不适用（它们走本地 + 个人 GitHub）。备份内容含会话，**绝不含明文密钥**（密钥本就只进 `.env`，见 §7）。

### 机制按 agent（能力对齐，非同一个 skill）
不同 agent 的会话存储机制不同，**不能用同一个命令**。各用各的原生持久化，纪律统一：

| Agent | 持久化机制 | 恢复方式 |
|---|---|---|
| **Claude Code 家族**（Cowork / CC-vm，装了 `uber-dev` 插件的） | `uber-dev:share-session` skill——把 transcript **上传到 terrablob**（关键词："share/save session"、"upload session to terrablob"、"backup this conversation"、"export session"） | 日常用本地 `--resume` / `--continue`；跨机或本地被清后，从 terrablob 取回备份 |
| **Hermes** | 会话已由 `~/.hermes/sessions/` + `state.db`（SQLite + FTS5）**本地持久**，gateway 重连自动续 | 重连/重启 gateway 自动加载；容器被销毁才需离机备份（导出机制待补） |
| **Codex** | `~/.codex/sessions/` + `session_index.jsonl` + sqlite **本地持久** | 重开 Codex 续会话 |
| **Cursor** | **无自管理持久层**（仅产品层，不可控） | 不保证；重要上下文须主动落盘到项目文件 / wiki |

### 统一纪律
- **「实时」= 检查点备份**（`share-session` 是按需 skill 调用，非每 token 后台守护）。检查点时机：①PLAN 批准后 ②每个 EXECUTE 步骤后 ③不可逆操作前 ④长任务定时（可用 hook / 定时器触发）。
- **分 agent + 分项目命名**：备份标签/路径带 `<agent>/<project-slug>/<时间戳>`，使重连后能按「哪个 agent 的哪个项目」精确取回。
- **重连后第一动作**：按当前项目 slug 找回最近一次备份，先读回上下文再继续（与「开工第 0 步 git pull」并列为重连恢复动作）。
- **terrablob = Uber 内部受控存储**：上传不出公司边界，符合 IP 红线；但仍只备份 Uber 工作上下文，个人内容不混入。
- **没有 `uber-dev:share-session` 的 agent**（Hermes/Codex/Cursor）不强求同一 skill——靠各自上表机制达成同一目标；Cursor 这类无持久层的，靠把关键上下文写进项目文件兜底。
