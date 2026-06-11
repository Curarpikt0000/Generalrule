---
title: 家用机 Skill / Plugin / MCP 详细目录
domain: agent-rules
type: entity
keywords: [skill, catalog, 清单, 家用机, hermes, claude-code, antigravity, mcp]
tags: [skill-catalog, skills, mcp, inventory]
source: 家用机全量盘点 2026-06-11（逐项读 SKILL.md 据实登记）
created: 2026-06-11
updated: 2026-06-11
---

# 家用机 Skill / Plugin / MCP 详细目录

> 本页是 [[skill-registry]] 的明细附表。registry 管「A 类核心能力对账」，本页管「每个已装项是什么、给谁用、怎么获取」。
> **使用方法（给任何 Agent）**：读到一条后自问三件事——①这能力跟我的环境/任务相关吗？②来源是公共 registry（可直接装）还是自有 local（需从源机器传）？③按「安装/获取方式」列执行（安装是不可逆操作，先经用户确认）。
> 数据来源：2026-06-11 在家用机逐项读取各 skill 的 SKILL.md 据实登记；没写的字段标【待人工确认】，不含猜测。
> 范围：仅家用机（Claude Code / Hermes / Antigravity）。Uber 机见 ub-branch 的 uber-adaptation.md。

---

## 一、Claude Code（`~/.claude/skills/`，18 个）

> 获取方式说明：标「superpowers」的来自 https://github.com/obra/superpowers（`git clone` 后拷对应目录到 `~/.claude/skills/`）；标「claudekit」的来自 claudekit（ckm-* 系列，frontmatter 标注 author: claudekit）；标「local」的为自有 skill，其他机器需从家用机 `~/.claude/skills/<name>/` 整目录拷贝。

| 名称 | 类型 | 来源 | 用途（据 SKILL.md） | 依赖 | 适用 agent |
|---|---|---|---|---|---|
| brainstorming | skill | 公共·superpowers | 任何创意/功能工作前强制使用，通过对话探索需求与设计，含硬门（设计未获批准禁止实现） | writing-plans（后续衔接） | 所有编码 agent |
| writing-plans | skill | 公共·superpowers | 有了需求/spec 后写分步实现计划（文件、顺序、测试），假定实现者零上下文 | brainstorming（前置） | 所有编码 agent |
| systematic-debugging | skill | 公共·superpowers | 遇 bug/测试失败先 4 阶段找根因，禁止症状式快速修补 | — | 所有编码 agent |
| test-driven-development | skill | 公共·superpowers | 红-绿-重构：先写失败测试再写实现 | 项目测试框架 | 所有编码 agent |
| verification-before-completion | skill | 公共·superpowers | 宣称"完成/修好/通过"前必须先跑验证命令并确认输出，证据先于断言 | — | 所有编码 agent |
| using-superpowers | skill | 公共·superpowers | superpowers 元规则：定义 skill 检索与调用优先级（用户指令>skill>默认） | Skill tool | 装了 superpowers 的 agent |
| requesting-code-review | skill | 公共·superpowers | 分发 code-reviewer subagent 做审查，审查者只拿精确上下文不拿会话历史 | subagent 机制、git | 支持 subagent 的 agent |
| skill-creator | skill | 公共·官方 | 创建/修改/评测 skill（草稿、测试用例、描述优化） | — | 所有 agent |
| find-skills | skill | 公共·skills.sh 生态 | 在开放 skill 生态中发现并安装 skill（"有没有 skill 能做 X"） | 联网 | 所有 agent |
| copy-editing | skill | 公共 | 编辑/润色/审校已有营销文案（非从零写作） | — | 文案类任务 |
| gemini-image | skill | local | 用 Gemini 视觉能力分析图像：图像分析、截图 OCR、视觉理解 | Gemini API key、google-generativeai | 无视觉能力的 agent |
| ui-ux-pro-max | skill | 公共·claudekit 生态 | UI/UX 设计知识库：50+ 风格、161 配色、57 字体搭配、99 条 UX 准则，覆盖 10 个技术栈 | 可选 shadcn/ui MCP | 前端/设计任务 |
| ckm-design | skill | 公共·claudekit | 综合设计：logo（55 风格，Gemini AI）、CIP、HTML 演示、banner、图标、社交图片 | Gemini API（生成图） | 设计任务 |
| ckm-banner-design | skill | 公共·claudekit | 社媒/广告/网站 hero/印刷 banner 设计，多艺术方向+AI 生成视觉 | 调 ui-ux-pro-max 等 skill | 设计任务 |
| ckm-brand | skill | 公共·claudekit | 品牌声音、视觉识别、信息框架、品牌一致性 | — | 品牌/营销任务 |
| ckm-design-system | skill | 公共·claudekit | 三层 design token（primitive→semantic→component）、组件规格、幻灯生成 | — | 设计系统任务 |
| ckm-slides | skill | 公共·claudekit | 战略型 HTML 演示文稿（Chart.js、design token、响应式） | — | 演示任务 |
| ckm-ui-styling | skill | 公共·claudekit | shadcn/ui + Tailwind 的界面构建与主题定制 | — | 前端任务 |

> 另：Claude Code 已注册官方 plugin marketplace（anthropics/claude-plugins-official），当前 `enabledPlugins` 为空（无启用 plugin）。
> ⚠️ 旧 registry 中登记的 `cua-driver` 在本机已不存在（2026-06-11 核实），已从清单移除。

## 二、Claude Code MCP

`claude mcp list` 为空 —— **家用机 Claude Code 当前未配置任何 MCP server**（2026-06-11 核实）。

---

## 三、Antigravity（`~/.gemini/antigravity/skills/`，9 个 skill + 8 个 global workflow）

### Skills

| 名称 | 来源 | 用途（据 SKILL.md） | 依赖 |
|---|---|---|---|
| agent-browser | 公共 | 浏览器自动化：导航、填表、点击、截屏、数据提取；验证爬虫/调试前端 | Node.js / npm |
| brainstorming | 公共·superpowers 同源 | 同 CC 的 brainstorming（设计前对话探索，硬门） | writing-plans |
| code-review | 公共 | 代码评审：正确性、健壮性、可维护性、架构契合 | git repo |
| frontend-design | local | 产品级前端界面设计，强调鲜明美学方向 + CSS token；本机版含项目定制（玩具感/彩虹风格 + Noto Sans SC） | 【待人工确认】 |
| humanizer-zh | local | 消除中文 AI 写作痕迹：识别并重写 24 种 AI 模式（过度强调、三段式、粗体滥用等） | 【待人工确认】 |
| requesting-code-review | 公共·superpowers 同源 | 同 CC，本机版含项目特有检查清单（爬虫层/LLM 层/前端层） | git、subagent |
| webworms | local | Python 爬虫框架：4 层降级（requests+BS4→Jina Reader→CamoFox→Crawl4AI），内置 robots.txt 合规、限速、重试 | Python 3.10+、requests、bs4 |
| systematic-debugging | 公共·superpowers | 同 CC（2026-06-11 从家用机 CC 拷入补齐 A 类） | — |
| test-driven-development | 公共·superpowers | 同 CC（2026-06-11 从家用机 CC 拷入补齐 A 类） | 项目测试框架 |

### Global Workflows（`~/.gemini/antigravity/global_workflows/`，对应 general rule §4 五阶段链路的 Antigravity 实现）

| 名称 | 用途 |
|---|---|
| plan-task | 编码任务规划：复杂度判定→读 lessons→搜方案→TODO 清单→等用户确认 |
| find-skill-first | 编码前必搜：Skills 生态→PyPI/GitHub→Web，产出候选对比表 |
| critic-review | Producer→Critic→Judge 多智能体审查，防自我安慰式审查 |
| verify-done | 宣称完成前强制验证：TODO 核对→Ruff→pytest→场景验证 |
| self-correct | verify 失败后的反思修复循环，3 次上限，禁止重试不可逆操作 |
| rollback | 任务彻底失败时回滚到 plan-task 建立的 git checkpoint |
| promote-lessons | 把项目 lessons 分类升级：进 Wiki / 固化为 Skill / 留项目内 |
| context-checkpoint | 长会话上下文清场，输出 checkpoint 文件记录成果与决策 |

### Antigravity MCP

| MCP | 用途 | 安装 |
|---|---|---|
| context7 | 拉取最新库文档（防训练数据过时） | `~/.gemini/antigravity/mcp_config.json` 配 serverUrl `https://mcp.context7.com/mcp` + API key（key 在本机配置文件，勿入库） |

---

## 四、Hermes（`~/.hermes/skills/`，131 enabled：51 local / 10 hub / 70 builtin）

### 4.1 Local skills（51 个，自有；其他机器获取方式 = 从家用机 `~/.hermes/skills/<路径>` 拷目录）

**通用方法论（跨 agent 有价值，纯提示词无依赖）**：

| 名称 | 用途（据 SKILL.md） | 项目专用? |
|---|---|---|
| consulting | 50+ 管理咨询框架（MECE、Issue Tree、金字塔原理、SCQ、波特五力等）轻量参考 | 否 |
| management-consultant | MBB 级全套咨询 skill + 113 份参考文件（案例面试、干系人、变革管理、尽调） | 否 |
| decision-memo-builder | 1 页决策备忘录（Context→Options→Recommendation→Risks→Ask） | 否 |
| issue-tree-builder | McKinsey 风格 MECE 问题树 | 否 |
| hypothesis-tree | Day-1 假设树：答案在顶、子假设分支、底层是推翻测试 | 否 |
| mckinsey-critic | 像 McKinsey EM 一样审 deck/文档/策略，Green/Yellow/Red 评分 + Top3 修复 | 否 |
| mckinsey-charts | python-pptx 生成三类 McKinsey 风格原生 PPT 图表（依赖 python-pptx） | 否 |
| storyline-builder | McKinsey 故事线：每行即一页标题，问题→上下文→分析→方案 | 否 |
| scpr-framework | SCPR 结构化问题解决（Situation-Complication-Problem-Recommendation） | 否 |
| top-down-memo | Minto 金字塔结论先行写作（BLUF） | 否 |
| synthesis | 从杂乱输入强制提炼 So-What：3 条带证据的洞察 | 否 |
| prioritization | PM 优先级框架：RICE、Impact/Effort、加权打分 | 否 |
| stakeholder-map | Power/Interest 网格干系人地图 + 逐人影响策略 | 否 |
| meeting-prep-kit | 会议准备包：3 条预读、议程、Top3 谈话要点与反对应答 | 否 |
| workshop-designer | 半天/全天策略工作坊设计（小时级议程、分组、剧本） | 否 |
| ai-use-case-scorer | AI 用例 Value×Feasibility×Safety 评分，分 Do Now/Quarter/Park/Avoid | 否 |
| ideation | 约束驱动创意生成：从约束库出 3 个具体项目点子 | 否 |
| deck-pipeline | 四代理管道 Strategist→Builder→Critic→Fixer 自动产出经审查的演示 | 否 |
| skill-creator | 创建/修改/评测 skill（Hermes 本地版） | 否 |
| find-skills | skill 生态发现与查重（Hermes 本地版） | 否 |
| writing-plans / subagent-driven-development / systematic-debugging | superpowers 同源方法论的 Hermes 版；subagent-driven 经 delegate_task 执行计划并两阶段审查 | 否 |
| search-fallback | 内置搜索（Tavily/Google/Bing/DDG）全被反爬时的系统化回退（Google News RSS 等） | 否 |
| webworms | 同 Antigravity 条目（4 层降级爬虫框架） | 否 |
| native-mcp | Hermes 连接 MCP server（stdio/HTTP）注册工具 | 否 |
| gemini-image | Gemini 视觉分析图像（需 Gemini API key） | 否 |
| vision | DeepSeek 的"眼睛"：Telegram 图片→结构化文字（概述+OCR+视觉描述），后端 Gemini API。**纯文本 agent 配套用，有视觉的 agent 用不上** | DeepSeek 集成专用 |
| linear | Linear GraphQL API 管理 issue/项目（需 LINEAR_API_KEY，无 MCP 依赖） | 否 |
| spotify | Spotify 播放控制 7 工具（需 Spotify API token） | 否 |
| axolotl / fine-tuning-with-trl / unsloth / outlines | LLM 微调与结构化生成参考（Axolotl YAML 微调、TRL 后训练、Unsloth 加速、Outlines 结构化输出）；依赖各自 Python 库 | 否 |

**项目专用（仅服务特定管道，别的 agent 无需安装）**：

| 名称 | 服务的项目 | 关键依赖 |
|---|---|---|
| moomooapi / install-moomoo-opend / trading-connectivity | moomoo 券商 API 集成 | moomoo OpenD ≥10.4.6408、futu/moomoo-api SDK |
| moomoo-capital-anomaly / -comment-sentiment / -derivatives-anomaly / -news-search / -stock-digest / -technical-anomaly | moomoo 股票异动/情绪/新闻分析 | moomoo OpenAPI、curl+openssl |
| comex-daily-report | COMEX 贵金属日报（写 Notion） | Notion API、moomoo API |
| fred-notion-pipeline | FRED→Notion 财务数据管道运维 | FRED API key、Notion API、cron |
| kol-tracker-operations | KOL 日追踪管道运维 | Tavily、Notion、DeepSeek API |
| magazine-pipeline-operations | YouTube 杂志视频管道运维 | Google Drive SA、launchd |
| atn-pipeline | URL 内容提取→Notion AtN Inbox | Notion API |
| youtube-reviewer | YouTube Automation 各阶段质检（delegate_task 起 Sonnet 子代理） | delegate_task |
| webhook-subscriptions | 外部服务 webhook 触发 Hermes 运行 | webhook 平台、HMAC secret |
| wiki-update | 把新知识写入本 Generalrule Wiki（路径硬编码本机） | 本地文件系统 |
| debugging-hermes-turn-stalls | Hermes 自身 turn 卡死调试 | Hermes 内部 |

### 4.2 Hub 安装（10 个，公共 registry，可在任何 Hermes 实例 `hermes skills install` 安装）

agent-browser、brainstorming、requesting-code-review、systematic-debugging（来源 skills.sh，community）；baoyu-comic、pixel-art、dspy、scrapling、minecraft-modpack-server、pokemon-player（来源 official）。安装命令：`hermes skills install <name>`。

### 4.3 Builtin（70 个，随 Hermes 自带，无需安装，仅列名）

apple 系（apple-notes/apple-reminders/findmy/imessage/macos-computer-use）、agent 系（claude-code/codex/hermes-agent/opencode）、creative 系（architecture-diagram/ascii-art/ascii-video/baoyu-infographic/claude-design/comfyui/design-md/excalidraw/humanizer/manim-video/p5js/popular-web-designs/pretext/sketch/songwriting/touchdesigner-mcp）、github 系（codebase-inspection/github-auth/github-code-review/github-issues/github-pr-workflow/github-repo-management）、mlops 系（audiocraft/evaluating-llms-harness/huggingface-hub/llama-cpp/obliteratus/segment-anything/serving-llms-vllm/weights-and-biases）、productivity 系（airtable/google-workspace/maps/nano-pdf/notion/ocr-and-documents/powerpoint/teams-meeting-pipeline）、research 系（arxiv/blogwatcher/llm-wiki/polymarket/research-paper-writing）、media 系（gif-search/heartmula/songsee/youtube-content）、software 系（hermes-agent-skill-dev/node-inspect-debugger/plan/python-debugpy/spike/test-driven-development）、其他（dogfood/yuanbao/jupyter-live-kernel/himalaya/obsidian/godmode/openhue/xurl/gif 等）。

### 4.4 Hermes MCP

| MCP | 用途 | 安装 |
|---|---|---|
| notion | Notion 读写（各 Notion 管道的写入通道） | `npx -y @notionhq/notion-mcp-server`（hermes mcp add） |
| brave-search | Brave 网页搜索 | `npx -y @anthropic/mcp-brave-search`（需 Brave API key） |

---

## 五、跨环境获取速查

- **公共项**：superpowers → `git clone https://github.com/obra/superpowers.git` 拷 skills；Hermes hub → `hermes skills install <name>`；claudekit ckm-* → claudekit 发行渠道【待人工确认具体安装命令】。
- **自有 local 项**：源机器 = 家用机。Claude Code 的在 `~/.claude/skills/`，Hermes 的在 `~/.hermes/skills/`，Antigravity 的在 `~/.gemini/antigravity/skills/`。传输 = 整目录拷贝（scp / U 盘 / 私有 git）。**不可经任何公共 registry 安装**。
- **项目专用项**：除非要在新机器跑同一管道，否则不必装。
- 安装/卸载后更新 [[skill-registry]] 对账表并 push（general rule §6.5）。

## 六、相关页面

- [[skill-registry]] —— A 类核心能力对账表（精简版）
- [[wiki-ingest-guide]]、[[five-step-pipeline]]
