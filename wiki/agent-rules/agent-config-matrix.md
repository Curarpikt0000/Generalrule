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

| 维度 | CC-home（已采集） | Antigravity | Hermes | 其余 |
|---|---|---|---|---|
| 入口文件 | `~/.claude/CLAUDE.md`（软链→repo） | `~/.gemini/antigravity/`（待证） | `~/.hermes/` + AGENTS.md（待证） | 【待自述】 |
| 人格层 | 无 | 待证 | 有 `SOUL.md` | 【待自述】 |
| 持久记忆 | Auto Memory（私有） | 待证 | 待证 | 【待自述】 |
| 五阶段载体 | superpowers skill | `global_workflows/*.md` | 待证 | 【待自述】 |
| skill 目录 | `~/.claude/skills/` | `~/.gemini/antigravity/skills/` | `~/.hermes/skills/` | 【待自述】 |
| 读 repo 分支 | main | 待证 | 待证 | 【待自述】 |

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

## Hermes（家用机）— 【待该 agent 自述】

> CC-home 旁观推断（待 Hermes 自述确认）：有 `~/.hermes/SOUL.md` 人格层；skill 在 `~/.hermes/skills/`（131 个，51 local）；MCP 有 notion/brave-search；入口疑用 AGENTS.md/config.yaml。记忆机制/五阶段载体/读 repo 分支未知。

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
