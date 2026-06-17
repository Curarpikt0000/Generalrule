---
title: Skill 与 MCP 总清单（对账 + 明细）
domain: agent-rules
type: entity
keywords: [skill, mcp, registry, catalog, 清单, 对账, self-skill, 多环境, 多agent]
tags: [skill-register, skills, mcp, reconciliation, inventory]
source: 三 agent skill 盘点 2026-05-24，对账机制升级 2026-06，全量盘点 2026-06-11，合并 registry+catalog 2026-06-13
sources: [conversation-2026-05-24, conversation-2026-06, conversation-2026-06-13]
created: 2026-05-24
updated: 2026-06-14
last_updated: 2026-06-14
---

# Skill 与 MCP 总清单（对账 + 明细）

> 本页是 [[skill-registry]]+[[skill-catalog]] 合并后的**单一清单**（2026-06-13 合并，原两文件已废弃；2026-06-14 Codex VM 接入对账已登记到 ub-branch 的 `uber-adaptation.md`）。
> 上半部分（一~六）= 对账机制 + A 类核心能力对账表 + MCP + 对账流程；下半部分（七~九）= 各环境/各 agent 全量明细 + Self-Skill 收纳区 + 跨环境获取速查。
> 适用所有 agent：私人 Mac（Claude Code / Hermes / Antigravity）+ Uber Mac/VM（Claude Code / Codex / Cursor / Hermes / Antigravity，未来更多）。
> **Uber 专属 skill/MCP 明细不在本（main）页展开，见 ub-branch 的 uber-adaptation.md（IP 隔离）。**

---

## 一、对账原则（核心机制）

**只对账 A 类核心能力**，不对账专用 skill（专用的各环境各装各的，噪音太大）。

三类管理：
- **A 类 · 核心能力（对账）** —— 每个环境都该有。缺了就提示安装。比的是「能力」不是「文件名」。
- **B 类 · 系统级（记录不对账）** —— 系统命令，本就全局可用。
- **C 类 · 专用（登记不对账）** —— 平台/项目特定，各干各的，只登记谁有什么。

**纪律（写进 general rule §6.5）**：
- 装 / 卸任何 A 类 skill 或 MCP 后，**必须更新本清单并 push**（通用→main；Uber 专属→ub-branch），并在根 `CHANGELOG.md` 留证据。
- 任何 Agent 开工时，**先读本清单对账**：列本环境已装 → 列缺的 → 给安装命令 → **用户确认后**再装（安装是不可逆操作，遵守 §7）。

---

## 二、A 类核心能力 —— 对账表

> 行是「能力」，不是 skill 文件名。同一能力在不同环境是不同 skill（如 brainstorming 在家用机是 superpowers 包，在 Uber 是 uberpowers）。对账时比能力有无。

| 核心能力 | 家用机 CC | Hermes | Uber（CC/Codex/Cursor 等） | 安装命令（按环境） |
|---|---|---|---|---|
| **brainstorming**（EXPLORE 硬门） | ✅ | ✅ | uberpowers | 家:superpowers包; Uber:`aifx plugin add uberpowers` |
| **writing-plans**（PLAN 阶段） | ✅ | ✅ | uberpowers | 同上 |
| **systematic-debugging**（根因调试） | ✅ | ✅ | uberpowers | 同上 |
| **test-driven-development**（TDD） | ✅ | ✅ | uberpowers | 同上 |
| **verification-before-completion**（VERIFY） | ✅ | builtin | uberpowers | 家:superpowers包 |
| **using-superpowers**（协同入口） | ✅ | — | uberpowers | 家:superpowers包 |
| **skill-creator**（造 skill） | ✅ | ✅ | skill-workshop | Uber:`aifx plugin add skill-workshop` |
| **find-skills**（查 skill 生态、查重） | ✅ | ✅ | find-skills | Uber:`aifx plugin add find-skills`（公网 vercel 版见七·Self-Skill 说明） |
| **requesting-code-review**（分级审查） | ✅ | ✅ | uberpowers含 | 家:superpowers包 |
| **wiki 写作**（ingest 知识库） | llm-wiki（self-skill） | wiki-update | llm-wiki（self-skill） | 见 `self-skill/llm-wiki`；所有 agent 优先调它统一 format |

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

## 四、C 类专用（各环境登记概览，不对账）

> 每项「是什么、给谁用、怎么获取」的明细见下方第七节。

**仅 Hermes**：vision、webworms / scrapling / search-fallback、youtube-reviewer、atn-pipeline / magazine-pipeline-operations / comex-daily-report / fred-notion-pipeline / kol-tracker-operations / webhook-subscriptions / wiki-update、moomoo 系列（9 个）、management-consultant / mckinsey-* / 咨询框架（约 18 个）、mlops 微调系列（axolotl / trl / unsloth / outlines）、linear / spotify / native-mcp、各 builtin（70 个）。

**仅家用机 Claude Code**：ckm-* 设计系列（design / banner-design / brand / design-system / slides / ui-styling）、ui-ux-pro-max、copy-editing、gemini-image。

**仅 Antigravity**：frontend-design、humanizer-zh、code-review、agent-browser、webworms，外加 8 个 global workflow（plan-task / verify-done / self-correct / rollback 等，即 §4 五阶段链路的 Antigravity 实现）。

**仅 Uber 机**：见 ub-branch 的 uber-adaptation.md（uberpowers / code-mode / omni-mcp 及各 Uber 内部 plugin）。Uber 专属 skill 清单不进 main（IP 隔离）。

---

## 五、MCP 清单

| MCP | 用途 | 哪些环境 | 安装命令 |
|---|---|---|---|
| omni-mcp | 一个连接通 415+ servers | Uber | `aifx mcp add omni-mcp --skip-validation` |
| notion | Notion 读写（各 Notion 管道写入通道） | Hermes | `npx -y @notionhq/notion-mcp-server` |
| brave-search | Brave 网页搜索 | Hermes | `npx -y @anthropic/mcp-brave-search`（需 API key） |
| context7 | 拉取最新库文档 | Antigravity | mcp_config.json 配 `https://mcp.context7.com/mcp` + API key |

> 家用机 Claude Code 当前 **0 个 MCP**（`claude mcp list` 为空，2026-06-11 核实）。
> Uber 的 MCP 详情（含各内部 server，如 Codex 的 `~/.codex/config.toml`）登记在 ub-branch 的 uber-adaptation.md，不进 main。

---

## 六、对账流程（任何 Agent 开工可执行）

1. 读本页第二节 A 类对账表。
2. 列出本环境已装：
   - 家用机 Claude Code：`ls ~/.claude/skills/`
   - Hermes：`hermes skills list`
   - Uber 机（CC/Codex/Cursor）：`aifx plugin list`；公网通用 skill 见 `~/.agents/skills/`
3. 对比 A 类表，列出「本环境该有但没装」的核心能力。
4. 按表中「安装命令」列，给出本环境对应命令。
5. **用户确认后**安装（不可逆操作，遵守 general rule §7）。
6. 装完 → 更新本页对应环境列 + 根 `CHANGELOG.md` → push（通用改动 push main；Uber 专属 push ub-branch）。

---

## 七、各环境全量明细

> 使用方法（给任何 Agent）：读到一条后自问——①这能力跟我的环境/任务相关吗？②来源是公共 registry（可直接装）还是自有 local（需从源机器传）？③按「获取方式」执行（安装是不可逆操作，先经用户确认）。
> 范围：私人机三 agent。数据来源 2026-06-11 家用机逐项读 SKILL.md 据实登记。Uber 机明细见 ub-branch。

### 7.1 家用机 Claude Code（`~/.claude/skills/`，18 个）

> 来源说明：「superpowers」来自 https://github.com/obra/superpowers（clone 后拷目录到 `~/.claude/skills/`）；「claudekit」为 ckm-* 系列；「local」为自有 skill，他机需从源机器整目录拷。

| 名称 | 来源 | 用途（据 SKILL.md） | 适用 agent |
|---|---|---|---|
| brainstorming | 公共·superpowers | 创意/功能工作前对话探索需求与设计，含硬门 | 所有编码 agent |
| writing-plans | 公共·superpowers | 有 spec 后写分步实现计划（假定实现者零上下文） | 所有编码 agent |
| systematic-debugging | 公共·superpowers | 遇 bug 先 4 阶段找根因，禁症状式修补 | 所有编码 agent |
| test-driven-development | 公共·superpowers | 红-绿-重构：先写失败测试 | 所有编码 agent |
| verification-before-completion | 公共·superpowers | 宣称"完成"前必跑验证命令确认输出 | 所有编码 agent |
| using-superpowers | 公共·superpowers | superpowers 元规则：skill 检索/调用优先级 | 装了 superpowers 的 agent |
| requesting-code-review | 公共·superpowers | 分发 code-reviewer subagent 做审查 | 支持 subagent 的 agent |
| skill-creator | 公共·官方 | 创建/修改/评测 skill | 所有 agent |
| find-skills | 公共·skills.sh 生态 | 在开放生态发现并安装 skill | 所有 agent |
| copy-editing | 公共 | 编辑/润色/审校已有文案 | 文案类 |
| gemini-image | local | Gemini 视觉分析图像（OCR/视觉理解） | 无视觉能力的 agent |
| ui-ux-pro-max | 公共·claudekit 生态 | UI/UX 知识库（50+风格/161配色/57字体/99 UX准则） | 前端/设计 |
| ckm-design | 公共·claudekit | 综合设计：logo/CIP/HTML 演示/banner/图标 | 设计 |
| ckm-banner-design | 公共·claudekit | 社媒/广告/网站 hero/印刷 banner | 设计 |
| ckm-brand | 公共·claudekit | 品牌声音、视觉识别、信息框架 | 品牌/营销 |
| ckm-design-system | 公共·claudekit | 三层 design token + 组件规格 | 设计系统 |
| ckm-slides | 公共·claudekit | 战略型 HTML 演示（Chart.js/design token） | 演示 |
| ckm-ui-styling | 公共·claudekit | shadcn/ui + Tailwind 构建与主题 | 前端 |

家用机 Claude Code MCP：`claude mcp list` 为空（2026-06-11 核实）。

### 7.2 Antigravity（`~/.gemini/antigravity/skills/`，9 skill + 8 workflow）

Skills：agent-browser、brainstorming、code-review、frontend-design(local)、humanizer-zh(local)、requesting-code-review、webworms(local)、systematic-debugging、test-driven-development。
Global Workflows（§4 五阶段的 Antigravity 实现）：plan-task / find-skill-first / critic-review / verify-done / self-correct / rollback / promote-lessons / context-checkpoint。
MCP：context7（拉最新库文档，mcp_config.json + API key）。

### 7.3 Hermes（`~/.hermes/skills/`，131 enabled：51 local / 10 hub / 70 builtin）

- **通用方法论（local，跨 agent 有价值）**：consulting、management-consultant、decision-memo-builder、issue-tree-builder、hypothesis-tree、mckinsey-critic、mckinsey-charts、storyline-builder、scpr-framework、top-down-memo、synthesis、prioritization、stakeholder-map、meeting-prep-kit、workshop-designer、ai-use-case-scorer、ideation、deck-pipeline、skill-creator、find-skills、writing-plans / subagent-driven-development / systematic-debugging、search-fallback、webworms、native-mcp、gemini-image、vision、linear、spotify、axolotl / fine-tuning-with-trl / unsloth / outlines。
- **项目专用（local，仅服务特定管道）**：moomooapi / install-moomoo-opend / trading-connectivity、moomoo-{capital-anomaly,comment-sentiment,derivatives-anomaly,news-search,stock-digest,technical-anomaly}、comex-daily-report、fred-notion-pipeline、kol-tracker-operations、magazine-pipeline-operations、atn-pipeline、youtube-reviewer、webhook-subscriptions、wiki-update、debugging-hermes-turn-stalls。
- **hub（10，`hermes skills install <name>`）**：agent-browser、brainstorming、requesting-code-review、systematic-debugging（community）；baoyu-comic、pixel-art、dspy、scrapling、minecraft-modpack-server、pokemon-player（official）。
- **builtin（70，自带）**：apple/agent/creative/github/mlops/productivity/research/media/software 各系（含 research 系的 `llm-wiki`——注意这是 builtin 版，本体系用的是 self-skill 改造版）。
- MCP：notion、brave-search。

---

## 八、Self-Skill 区（自有改造通用 skill）

> 收纳处 = repo 根 `self-skill/`，宪法见 [`self-skill/README.md`](../../self-skill/README.md)。
> **准入**：只放通用 skill（脱离公司/项目仍成立）；特用 skill 禁止。**copy 后必须在此登记**（这是准入的一部分）。

| skill | 用途 | 来源（原始） | 取用方式 |
|---|---|---|---|
|| `self-skill/llm-wiki/` | 在 Generalrule 共享 wiki 上做知识复利累积（Ingest/Query/Lint+Heal）；已适配本体系（纯 markdown、领域目录、方案Z frontmatter、双分支、红线门、无写死路径） | 改造自公网 `kingqiu/llm-wiki-skill`（vercel skills 生态，公网 `npx skills add`） | 拷 `self-skill/llm-wiki/` 到本机 skill 目录（如 `~/.agents/skills/`），复制 config.example.md→config.md 按本机填。所有 agent 写 wiki 优先调它 |
| `self-skill/webworms/` | 4 层降级回退的网页爬虫标准框架（requests+BS4 → Jina Reader → CamoFox → Crawl4AI），内置 robots.txt 合规、限速、重试。附站点爬虫备忘录 | 自有 Hermes skill 改造 | 拷 `self-skill/webworms/` 到本机 skill 目录。pip install requests beautifulsoup4 lxml camoufox crawl4ai |
| `self-skill/agent-slides/` | 从 brief 生成专业 PPTX deck：7 个可组合子 skill（extract/build/edit/audit/critique/polish/full），基于 python-pptx 的确定性 agent-ready CLI。无遥测/外部网络写入 | 公网开源 `mpuig/agent-slides`（MIT） | 拷 `self-skill/agent-slides/` 到本机 skill 目录；只收 skill 定义，CLI 走 PyPI——需本机 `uv`（含 `uvx`）+ Python 3.12+，命令 `uvx --from agent-slides slides ...` 按需拉包 |
| `self-skill/project-context-persistence/` | 一个 agent 服务多项目时按 topic/项目做每日上下文归档：cron 把当天对话蒸馏进项目文件夹（AGENTS.md + docs/context-log.md），新会话自动加载历史决策/事实/进展/待办。Memory-Bank 模式（Cline / CLAUDE.md 风格）在 Hermes 上的落地。诚实标注 state.db 不存 topic_id 的限制 | 自有 Hermes skill 改造（已去 Uber 措辞） | 拷 `self-skill/project-context-persistence/` 到本机 skill 目录，把 `scripts/collect_topic_conversation.py` 放进 `~/.hermes/scripts/`，按 `references/memory-bank-cron-recipe.md` 建 cron |

---

## 九、跨环境获取速查

- **公共项**：superpowers → `git clone https://github.com/obra/superpowers.git` 拷 skills；Hermes hub → `hermes skills install <name>`；Uber → `aifx plugin add <name>`；公网通用 skill → `npx --registry=https://registry.npmjs.org skills add <repo> --skill <name>`（会过安全审计，装前看风险等级）。
- **自有 local 项**：源机器 = 家用机（`~/.claude/skills/` 或 `~/.hermes/skills/` 或 `~/.gemini/antigravity/skills/`），整目录拷贝，不可经公共 registry 安装。
- **自有改造通用项**：见第八节 Self-Skill 区（统一从 repo `self-skill/` 取，已去写死路径）。
- **项目专用项**：除非要跑同一管道否则不必装。
- 安装/卸载后更新本页 + 根 `CHANGELOG.md` 并 push（general rule §6.5）。

---

## 十、咨询框架 Skill 冲突消歧与去重（跨 agent 通用行动指南）

> **适用对象**：任何装了这批咨询框架 skill 的 agent（CC / Cowork / CC-vm / Hermes / Antigravity / Codex / Cursor）。
> **背景**：这批 skill 全靠 `description` 语义自动触发，**无优先级表**；描述越宽泛越会"抢"专用 skill 的触发。下表是**该用哪个**的硬规则。任何 agent 开工时据此自检本机 description，发现冲突按 10.3/10.4 自行修。
> **首次落地**：2026-06-17，家用机 + Cowork 实测体量对比后得出（[UB]）。

### 10.1 去重结论（哪些被别的完全 cover）

| Skill | 处置 | 理由 | 各 agent 行动 |
|---|---|---|---|
| `consulting` | **归档/移除** | body 与 `management-consultant` 重叠，后者为**严格超集**（4.6MB / 228 文件 / 115 文件参考库 vs 180KB / 13 文件，主题全覆盖：case/strategy/finance/operations/problem-solving/projects/design） | 本机若两者并存→保留 management-consultant，把 consulting 移到 `skills-archive/`（**先归档不 `rm`**，可逆）。本机若只有其一→不动 |
| `prioritization` | **修复，勿删** | 该 skill 的 `SKILL.md` 可能缺 frontmatter（无 `name`/`description`）→ **永不自动触发**，是死 skill | 本机自查文件首行：若不是 `---` frontmatter，按 10.3 补全 |

### 10.2 触发消歧规则（同类里到底选谁）

| 你要做的事 | ✅ 用这个 | ❌ 别让它抢 |
|---|---|---|
| 拆解**问题空间**（MECE 分支、调查计划） | `issue-tree-builder` | management-consultant |
| **先押一个答案**再去验证 | `hypothesis-tree` | issue-tree-builder |
| 1 页**决策**备忘（给某人拍板） | `decision-memo-builder` | top-down-memo |
| 通用"**答案优先**"写作（Minto 金字塔） | `top-down-memo` | scpr-framework |
| 明确要 **SCPR** 结构 | `scpr-framework` | top-down-memo |
| Deck **叙事骨架**（每行＝slide 标题） | `storyline-builder` | deck-pipeline |
| **端到端**做完整 deck | `deck-pipeline` | storyline-builder |
| 只要 **pptx 图表** | `mckinsey-charts` | — |
| **审阅**成品 deck/doc | `mckinsey-critic` | — |
| Feature/任务**优先级**排序 | `prioritization` | — |
| 给 **AI 用例**打分排序 | `ai-use-case-scorer` | prioritization |
| 把杂乱输入逼出"**so what**" | `synthesis` | — |
| 广义商业问题/行业分析**兜底** | `management-consultant` | 仅当上面无专用项匹配时 |
| 会议准备包 / 干系人地图 / 工作坊设计 | `meeting-prep-kit` / `stakeholder-map` / `workshop-designer` | 三者互不重叠 |

### 10.3 prioritization 修复模板（任何 agent 本机自查）

若本机 `prioritization/SKILL.md` 顶部不是 `---` frontmatter，补到最顶：
```
---
name: prioritization
description: Prioritize features/initiatives/tasks via RICE/ICE/MoSCoW/Value-vs-Effort/Kano scoring; outputs a ranked table. Use when you have candidates and must decide what to do first/next/cut. AI use cases → ai-use-case-scorer; alignment workshop → workshop-designer.
---
```

### 10.4 通用原则（沉淀，跨场景迁移）

- **判断 skill 能否删，必须看 body + 支撑文件体量，不能只比 description。** 描述像但 body 各异 → 误删会销毁知识库（consulting 即 180KB 知识库，差点被当"两行重复品"删掉）。
- **删除先归档不 `rm`**：移到同机 `skills-archive/<name>-<日期>/` 即停止触发，可逆；确认彻底无用再清。
- **给宽泛 skill 加分流句**：在其 `description` 末尾显式写"做 X 用 skill-Y"，把触发主动让给专用 skill（management-consultant 已示范）。
- **整改产出写进本 registry，不是只改本地 SKILL.md**：本地编辑只惠及当前 agent；消歧规则进共享 registry 才能让所有读它的 agent 受益。

---

## 十一、相关页面

- [[wiki-ingest-guide]] —— Wiki 读写规范（llm-wiki 的产出须符合）
- [[five-step-pipeline]] —— 第 3 步"找 Skill"
- [`self-skill/README.md`](../../self-skill/README.md) —— Self-Skill 收纳宪法
- general-global-rule.md §3（五步链路）、§6.5（skill 对账纪律 + self-skill 指针）、§7.5（多机分流）
