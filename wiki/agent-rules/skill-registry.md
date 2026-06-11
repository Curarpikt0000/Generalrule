---
title: Skill 与 MCP 清单及对账机制
domain: agent-rules
type: entity
keywords: [skill, mcp, registry, 清单, 对账, 全局化, uberpowers, 多环境]
tags: [skill-registry, skills, mcp, reconciliation]
source: 三 agent skill 盘点 2026-05-24，对账机制升级 2026-06，VM 对账 2026-06-08，全量盘点 2026-06-11
sources: [conversation-2026-05-24, conversation-2026-06, conversation-2026-06-08]
created: 2026-05-24
updated: 2026-06-11
last_updated: 2026-06-11
machine: UB
---

# Skill 与 MCP 清单及对账机制

> 登记各 Agent / 各环境的 skill 与 MCP 安装情况，并定义对账流程。
> 目的：换任何一台机器、开任何一个 Agent，都能 check 本清单、定位本环境缺的核心能力、给出安装命令补齐。
> 环境：家用机（Claude Code / Hermes / Antigravity）、Uber 机（Uber Claude Code / Uber Antigravity，跑在云端 VM）。

---

## 一、对账原则（核心机制）

**只对账 A 类核心能力**，不对账专用 skill（专用的各环境各装各的，噪音太大）。

三类管理：
- **A 类 · 核心能力（对账）** —— 每个环境都该有。缺了就提示安装。比的是「能力」不是「文件名」。
- **B 类 · 系统级（记录不对账）** —— 系统命令，本就全局可用。
- **C 类 · 专用（登记不对账）** —— 平台/项目特定，各干各的，只登记谁有什么。

**纪律（写进 general rule §6）**：
- 装 / 卸任何 A 类 skill 或 MCP 后，**必须更新本清单并 push**。
- 任何 Agent 开工时，**先读本清单对账**：列本环境已装 → 列缺的 → 给安装命令 → **用户确认后**再装（安装是不可逆操作，遵守 §7）。

---

## 二、A 类核心能力 —— 对账表

> 行是「能力」，不是 skill 文件名。同一能力在不同环境是不同 skill（如 brainstorming 在家用机是 superpowers 包，在 Uber 是 uberpowers）。对账时比能力有无。
> Uber 列的「uberpowers 替代」等细节，详见 ub-branch 的 uber-adaptation.md（Uber 专属，不在 main 展开）。

| 核心能力 | 家用机 CC | Hermes | Uber | 安装命令（按环境） |
|---|---|---|---|---|
| **brainstorming**（EXPLORE 硬门） | ✅ | ✅ | uberpowers | 家:superpowers包; Uber:`aifx plugin add uberpowers` |
| **writing-plans**（PLAN 阶段） | ✅ | ✅ | uberpowers | 同上 |
| **systematic-debugging**（根因调试） | ✅ | ✅ | uberpowers | 同上 |
| **test-driven-development**（TDD） | ✅ | ✅ | uberpowers | 同上 |
| **verification-before-completion**（VERIFY） | ✅ | builtin | uberpowers | 家:superpowers包 |
| **using-superpowers**（协同入口） | ✅ | — | uberpowers | 家:superpowers包 |
| **skill-creator**（造 skill） | ✅ | ✅ | skill-workshop | Uber:`aifx plugin add skill-workshop` |
| **find-skills**（查 skill 生态、查重） | ✅ | ✅ | find-skills | Uber:`aifx plugin add find-skills` |
| **requesting-code-review**（分级审查） | ✅ | ✅ | uberpowers含 | 家:superpowers包 |
| **wiki-update**（写知识库） | 手动 | ✅ | 手动 | 无 Uber 等价物（engwiki 是写 Uber 内部）。写个人 wiki 用 wiki-update / 手动按 wiki-ingest-guide |

> 家用机安装 superpowers 包（含前 6 个能力）：
> ```
> git clone https://github.com/obra/superpowers.git
> cp -r superpowers/skills/<name> ~/.claude/skills/
> ```

---

## 三、B 类系统级（记录不对账）

| 工具 | 作用 | 状态 |
|---|---|---|
| **RTK** v0.40.0 | terminal 输出压缩，省 token | ✅ 家用机系统级 `/opt/homebrew/bin/rtk` |
| **code-mode** | Uber 环境的 token 压缩（替代 RTK） | Uber 机 `aifx plugin add code-mode` |

---

## 四、C 类专用（各环境登记，不对账）

> 每项「是什么、给谁用、怎么获取」的明细 → 见 [[skill-catalog]]（详表，2026-06-11 全量盘点）。本节只留概览。

**仅 Hermes**：vision（图片转文字，DeepSeek 配套）、webworms / scrapling / search-fallback（抓取与搜索回退）、youtube-reviewer、atn-pipeline / magazine-pipeline-operations / comex-daily-report / fred-notion-pipeline / kol-tracker-operations / webhook-subscriptions / wiki-update（项目运维 skill）、moomoo 系列（炒股分析，9 个）、management-consultant / mckinsey-* / 各类咨询框架 skill（约 18 个）、mlops 微调系列（axolotl / trl / unsloth / outlines）、linear / spotify / native-mcp、各 builtin（70 个，apple/github/mlops 等）。

**仅家用机 Claude Code**：ckm-* 设计系列（design / banner-design / brand / design-system / slides / ui-styling）、ui-ux-pro-max、copy-editing、gemini-image。~~cua-driver~~（2026-06-11 核实本机已不存在，移除）。

**仅 Antigravity**：frontend-design、humanizer-zh、code-review、agent-browser、webworms，外加 8 个 global workflow（plan-task / verify-done / self-correct / rollback 等，即 §4 五阶段链路的 Antigravity 实现）。2026-06-11 已补齐 A 类缺口：systematic-debugging、test-driven-development（从家用机 CC 拷入）。

**仅 Uber 机**（2026-06-08 实际确认）：aifx plugin 包括 alert-rca, ci-debugger, code-mode, data-analyst, find-skills, minion-dev, omni-mcp, page-publisher, skill-workshop, uber-dev, uber-reviewer, uberpowers；Claude Code skills 包括 consulting, management-consultant, issue-tree-builder, hypothesis-tree, synthesis, top-down-memo, decision-memo-builder, scpr-framework, storyline-builder, deck-pipeline, mckinsey-charts, mckinsey-critic, prioritization, ai-use-case-scorer, meeting-prep-kit, stakeholder-map, workshop-designer。Uber 专属 plugin 详细用途见 ub-branch 的 uber-adaptation.md（IP 隔离，不进 main）。

---

## 五、MCP 清单

| MCP | 用途 | 哪些环境 | 安装命令 |
|---|---|---|---|
| omni-mcp | 一个连接通 415+ servers | Uber | `aifx plugin add omni-mcp`（plugin）+ `aifx mcp add omni-mcp --skip-validation`（注册编辑器） |
| notion | Notion 读写（各 Notion 管道写入通道） | Hermes | `npx -y @notionhq/notion-mcp-server` |
| brave-search | Brave 网页搜索 | Hermes | `npx -y @anthropic/mcp-brave-search`（需 API key） |
| context7 | 拉取最新库文档 | Antigravity | mcp_config.json 配 `https://mcp.context7.com/mcp` + API key |

> 家用机 Claude Code 当前 **0 个 MCP**（`claude mcp list` 为空，2026-06-11 核实）。
> Uber 的 MCP 详情（含各内部 server）登记在 ub-branch 的 uber-adaptation.md，不进 main。

---

## 六、对账流程（任何 Agent 开工可执行）

1. 读本清单第二节 A 类对账表。
2. 列出本环境已装：
   - 家用机 Claude Code：`ls ~/.claude/skills/`
   - Hermes：`hermes skills list`
   - Uber 机：`aifx plugin list`
3. 对比 A 类表，列出「本环境该有但没装」的核心能力。
4. 按表中「安装命令」列，给出本环境对应命令。
5. **用户确认后**安装（不可逆操作，遵守 general rule §7）。
6. 装完 → 更新本清单对应环境列 → push（通用改动 push main；Uber 专属 push ub-branch）。

---

## 七、相关页面

- [[skill-catalog]] —— 家用机全量明细目录（每个 skill 是什么、给谁用、怎么获取）
- [[wiki-ingest-guide]] —— Wiki 读写规范
- [[five-step-pipeline]] —— 第 3 步"找 Skill"
- general-global-rule.md §3（五步链路）、§6（装 skill 后更新清单的纪律）
