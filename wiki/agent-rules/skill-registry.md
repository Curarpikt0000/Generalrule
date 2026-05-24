---
title: 三 Agent Skill 清单与统一管理
domain: agent-rules
type: entity
keywords: [skill, registry, 清单, 全局化, superpowers, wiki-update, rtk, 三agent]
tags: [skill-registry, skills, global-skills]
source: 三 agent skill 盘点 2026-05-24
sources: [conversation-2026-05-24]
created: 2026-05-24
updated: 2026-05-24
last_updated: 2026-05-24
---

# 三 Agent Skill 清单与统一管理

> 登记 Claude Code / Hermes / Antigravity 三个 Agent 的 skill 安装情况。
> 目的：解决"想用某 skill 却发现只有一个 Agent 装了"的问题。
> 核心方法论 skill 应三处统一；平台专用 skill 不强求。
> 盘点日期：2026-05-24（Hermes 107 / Claude Code 14 / Antigravity 走 rules+workflows）

---

## 一、统一原则

**不追求三个 Agent 装一模一样的全部 skill**（Hermes 有 107 个，很多用不到）。
只统一**你高频使用的核心方法论 skill**。三类管理：

- **A 类 · 必须三处统一** —— 工作流核心，缺了就行为不一致。
- **B 类 · 系统级共享** —— 系统命令，本就全局可用。
- **C 类 · 单 Agent 专用** —— 平台特定或专用，不强求统一。

---

## 二、A 类：必须三处统一的核心 skill

| Skill | 作用 | Hermes | Claude Code | Antigravity | 待办 |
|---|---|---|---|---|---|
| **wiki-update** | Wiki 知识写入（量身定做：正确路径+多领域+自动push） | ✅ | 手动 | 手动 | CC/AG 按 [[wiki-ingest-guide]] 手动 ingest |
| **skill-creator** | 创建新 skill 的标准流程 | ✅ | ✅ | ❌ | 给 AG 补 |
| **find-skills** | 检索现有 skill 生态 | ✅ | ✅ | ❌ | 给 AG 补 |
| **brainstorming**（superpowers） | 写代码前苏格拉底式需求澄清（EXPLORE 阶段用） | ✅ | ❌ | ❌ | 给 CC 补装 |
| **writing-plans**（superpowers） | 结构化任务规划（PLAN 阶段用） | ✅ | ❌ | ❌ | 给 CC 补 |
| **systematic-debugging**（superpowers） | 4 阶段根因调试流程 | ✅ | ❌ | ❌ | 给 CC 补 |
| **test-driven-development** | TDD 红绿重构 | ✅ | ❌ | ❌ | 给 CC 补 |
| **requesting-code-review** | 派子 agent 做分级代码审查 | ✅ | ✅ | ❌ | 给 AG 补 |

> **现状解读**：核心方法论 skill 几乎都在 Hermes，Claude Code 缺一大半。这是"想用却没装"的根源。
> **superpowers 是个包**，含 brainstorming / writing-plans / systematic-debugging / TDD 等。在 Hermes 上通过 skills.sh 装了部分；Claude Code 完全没装。

---

## 三、B 类：系统级共享（本就全局）

| 工具 | 作用 | 状态 |
|---|---|---|
| **RTK** v0.40.0 | terminal 输出压缩代理（`rtk ls`/`rtk read`/`rtk git` 等），省 token | ✅ 系统级 `/opt/homebrew/bin/rtk`，三个 Agent 在 shell 中都能用 |

RTK 用法见各 Agent 入口文件的 RTK 小节。原始命令优先用 `rtk` 代理形式以压缩输出。

---

## 四、C 类：单 Agent 专用（不强求统一）

**仅 Hermes（平台/项目特定）**：
- `vision` —— 图片转文字（DeepSeek 无视觉，靠它+Gemini 补）
- `webworms` / `scrapling` —— 反爬抓取（微信/受保护网页）
- `youtube-reviewer` —— YouTube 内容质检
- `atn-pipeline` / `magazine-pipeline-operations` —— 你的具体项目 skill
- `gemini-image` —— Gemini 图像
- 各类 builtin（apple/github/mlops/media 等）—— 按需，不必同步到其他 Agent

**仅 Claude Code（设计专用）**：
- `ckm-*` 系列（banner-design / brand / design-system / slides / ui-styling / ui-ux-pro-max）—— 你的设计 skill
- `copy-editing`、`cua-driver`、`gemini-image`

---

## 五、补装方式（各 Agent 不同）

> ⚠️ 实际补装放到"步骤 7"专门执行。这里先登记方法，避免装错。

**Claude Code** —— skill 是纯文本，拷进 `~/.claude/skills/<name>/`：
```bash
# 例：装 superpowers（含 brainstorming 等）
git clone https://github.com/obra/superpowers.git
cp -r superpowers/skills/* ~/.claude/skills/
```
slash 命令在 `~/.claude/commands/`（已有 8 个 workflow 命令）。

**Hermes** —— 已装齐，无需补。新增用 `hermes skills install <source>`。

**Antigravity** —— 无传统 skill 机制，走 `.agents/rules/` + Customizations→Workflows。
**wiki 写入，Antigravity/Claude Code 通过读 [[wiki-ingest-guide]] 手动执行**，无需装 skill。
确需 skill 化的，用 skill-creator 生成 Antigravity 兼容版（名字保持一致，便于记忆）。

---

## 六、Wiki 写入方案（wiki-update）

三个 Agent 写 Wiki 的统一方案：

- **Hermes**：用 local skill `wiki-update`（productivity 类）。它为本 Wiki 量身定做——正确路径、多领域结构、自动 git push。用自然语言触发（如"把这个总结进 wiki"）。
- **Claude Code / Antigravity**：无需 skill，按 [[wiki-ingest-guide]] 手动 ingest（判断领域→写文件→更新 index→git push）。

> 历史说明：曾装过 `wangsw/llm-wiki-skills`（llmwiki-ingest/query/health），因默认指向错误路径、用 concepts/ 扁平结构、与本架构不符，已于 2026-05-24 删除，统一改用 wiki-update。
> Wiki 读取（query）与体检（health）目前均为手动，无专门 skill；wiki 规模增大后可再引入。

## 七、相关页面

- [[wiki-ingest-guide]] —— Wiki 读写规范（wiki-update 用法）
- [[five-step-pipeline]] —— 第 3 步"找 Skill"
- general-global-rule.md §3（五步链路）
