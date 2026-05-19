# General Global Rule（通用全局规则）

> 本文件是 AI Agent 的**行为根规范**。所有其他文件（workflows、AGENTS.md、lessons.md）均在本文件的前提下工作。
> 更新后需手动复制粘贴到 Antigravity 的 User Rules 设置界面使其生效。
> 最后更新：2026-05-18

---

## §1 语言

- 所有回复、解释、提问、错误分析、建议均使用**中文简体**
- 代码注释使用中文简体；变量名、函数名、类名保持英文

---

## §2 代码规范（Python 专属）

### §2.1 风格
- 严格遵守 PEP 8
- 缩进 4 空格
- 每行不超过 88 字符
- 函数/类之间空两行，方法之间空一行

### §2.2 文件头注释（强制）
每个 `.py` 文件开头必须包含以下信息块：

```python
"""
文件功能：<一句话说明这个文件做什么>
实现方式：<用什么技术/方法实现>
主要模块：<包含哪些核心类或函数>
输入输出：<接收什么数据，返回什么数据>
依赖关系：<依赖哪些外部库或内部模块>
创建日期：YYYY-MM-DD
"""
```

### §2.3 函数/方法 docstring（强制）
每个函数/方法必须有 docstring，包含：
- 功能描述：这个函数做什么
- 实现逻辑：关键步骤
- 参数说明：每个参数的类型和含义
- 返回值：类型和含义
- 异常：可能抛出什么异常

### §2.4 行内注释
- 每一大块逻辑前加中文注释，说明：目的、思路、注意事项
- 复杂逻辑行内加中文简短注释

### §2.5 模块化原则
- 按**功能职责**拆分文件，不按行数硬切
- 单文件承担超过 2 个不相关职责时必须拆分
- 每个函数只做一件事；需要滚动才能看完的函数必须拆
- 公共工具函数统一放 `utils.py`
- 配置参数统一放 `config.py`，**严禁硬编码**
- 主入口统一放 `main.py`

### §2.6 Test-First 原则（核心业务逻辑专属）

涉及**核心业务逻辑**的开发，强制 Test-Driven Development（TDD）：

**必须 TDD 的场景**：
- LLM fallback / 调度逻辑改动
- 爬虫管道、数据清洗的核心流程
- Pydantic Schema 修改影响线上数据
- 修复关键 bug（业务流程中断、数据丢失等）

**TDD 执行顺序**：
1. 先写一个**失败的测试用例**（明确预期行为）
2. 让测试用例失败（确认 test 真的在测应该测的东西）
3. 再写业务代码让 test 通过
4. 重构（如需要），保持 test 仍然 pass

**可豁免 TDD 的场景**：配置项调整、文档、UI 微调、Trivial 任务。

→ 详见 `wiki/engineering/harness-engineering-principles.md` §6

---

## §3 鲁棒性模型调度准则（LLM 调用专属）

本项目核心是 LLM 应用，所有 LLM 调用必须遵守：

### §3.1 禁止硬编码模型 ID
- 禁止在代码中写死 `gemini-1.5-pro`、`claude-opus-4` 等具体模型代号
- 所有模型 ID 必须从 `config.py` 或动态发现结果中读取

### §3.2 动态发现（Model Discovery）
- 应用启动或首次调用前，必须通过 `list_models` 接口获取当前 API Key 真实可用的最新 Pro 级和 Flash 级模型 ID
- 发现结果缓存，避免每次调用都发请求

### §3.3 级联回退（Cascading Fallback）
- **第一优先级**：动态发现的最顶级稳定版模型（Vertex AI Pro 级）
- **第二优先级**：第一优先级报错（429 配额 / 500 异常）时，自动捕获并尝试次级稳定版（Vertex AI Flash 级）
- **跨平台兜底**：Vertex AI 整体不可用时，平滑切换到 AI Studio

### §3.4 容错回馈
- 所有候选链路都失败后才抛最终异常
- 异常信息必须包含"所有候选链路已尝试"的完整诊断路径

---

## §4 工作习惯（交互规则）

### §4.1 动手前先汇报
- 修改代码前先用**中文**说明修改思路
- 等用户确认后再动手
- 非平凡修改前暂停一次，自问："有没有更优雅的方案？"，把更优方案与原方案对比后再汇报

### §4.2 改动范围控制
- 一次改动不超过 **5 个文件**，改完停下等确认再继续
- 变更应只触及必要部分，避免引入新 bug

### §4.3 问题发现原则
- 发现潜在问题立即指出
- **不要自动修改**——指出问题是 agent 的责任，决定是否修改是用户的权力

### §4.4 任务完成后总结
- 简短总结：做了什么、改动了哪些文件、有什么注意事项
- 如有后续风险，明确列出

### §4.5 Source Trace 强制要求（外部工具调用的真实性约束）

所有涉及**外部工具调用**的 agent 输出（web_search / web_fetch / curl / @find-skills / ruff / pytest / 以及任何终端命令），必须满足：

1. **展示调用痕迹**：输出中必须包含工具调用的实际命令或调用记录，例如 `【已调用 web_search】query=...`
2. **展示真实返回**：涉及的关键数字、日期、状态、版本号等**可验证事实**，必须附带工具的原始返回片段
3. **调用失败明说**：工具失败时明确写"调用失败：<原因>"，**禁止**用训练数据、印象或"大概"填充
4. **零容忍伪造**：凭印象编造工具返回等同于严重违规，自动触发 lesson 记录并重新执行

**违规后处理**：承认 → 记录 lesson → 重新执行完整流程，不隐瞒历史违规。

### §4.6 路径解析约定

所有 Workflow、规则、文档中提到的文件路径：
- 不带前导斜杠（如 `tasks/lessons.md`）→ 相对当前项目根目录解析
- 带前导斜杠（如 `/Users/chaojin/...`）→ 绝对路径
- 严禁将 `tasks/lessons.md` 等相对路径误认为根路径 `/lessons.md`

### §4.7 串行链式调用原则（LLM 多步管线专属）

- LLM 长文本生成与图像生成等重资源任务**严禁并行抢占**，必须严格串行执行（生成文章 → 抽取视觉 Prompt → 渲染图片）
- 遇到 429 配额报错，必须走代码中已建好的级联熔断机制（Pro 降级至 Flash），**绝对禁止**脱离熔断机制的自我无限重试
- 来源：L-2026-04-24-001

### §4.8 最小破坏原则（Bug 修复专属）

- 修复 bug 时每次只针对**一个具体报错点**进行局部修改，严禁连带大改周边架构
- 修前端不碰后端；修内部逻辑**绝不擅改**对外传参接口和函数签名
- 来源：L-2026-04-24-004

### §4.9 前端富文本渲染管道（有前端的项目必须遵守）

|- 严禁将 LLM 返回的 Markdown 原生字符串**裸露**给前端渲染或剪贴板操作
|- 必须通过 `marked.js` 等库解析为标准 HTML 后再渲染
|- 剪贴板写入必须使用 `Clipboard API (text/html)` + Blob 对象，并提供纯文本降级兜底
|- 来源：L-2026-04-24-003

### §4.10 Notion 数据验证必须循环翻页

Notion API 的 `get_block_children` 默认返回前 100 个 blocks。验证数据完整性时必须使用 `has_more` + `next_cursor` 循环翻页，不得仅查询首页。

→ 详见 Wiki: `wiki/engineering/notion-pagination-validation.md`
→ 来源: L-2026-05-04-003

### §4.11 新功能开发前检查现有 Skill

任何新功能实现前必须执行 `hermes skills search <关键词>` 检查现有 skill 库和开源方案。禁止重复造轮子。

→ 详见 Wiki: `wiki/engineering/skill-check-before-coding.md`
→ 来源: L-2026-05-04-005

### §4.12 严格使用用户提供的 URL

AI 或工具不得自作聪明替换用户的 URL。内容提取失败时应如实报告原因，询问用户是否尝试其他方式，而不是偷偷换 URL 继续。

→ 详见 Wiki: `wiki/engineering/url-fidelity.md`
→ 来源: L-2026-05-04-006

### §4.13 自治反思内循环（Reflexion Loop）

当 verify 失败或代码报错时，agent **不得立即向用户求助**，必须先尝试自治修复：

**强制流程**：
1. 输出 reflection 文本：「**What failed?** / **What change would fix it?** / **Am I repeating?**」
2. 基于反思尝试修复（计数器 +1）
3. 重新跑验证
4. 失败次数 < 3 → 回到第 1 步
5. 失败次数 = 3 → **强制退出**，向用户报告全部尝试历史

**Anti-drift 检测**：
- 如果连续两次修改**同一个文件**且改动相似 → 立即跳出循环
- 如果同一报错连续两次出现 → 立即跳出循环

**例外**：涉及不可逆动作（删除、git push、API 调用扣费）必须立刻停下问用户，禁止自治重试。

→ 触发 Workflow: `/self-correct`
→ 详见 `wiki/engineering/harness-engineering-principles.md` §3.2

### §4.14 上下文检查点（Context Checkpoint）

防止长会话中 agent 注意力衰退（context rot）：

**触发条件**：
- 一次 Complex 任务完成后
- 单次会话超过 2 小时
- 用户主动调用 `/context-checkpoint`

**强制动作**：
1. 写入 `tasks/context-checkpoint-YYYYMMDD-HHMM.md`，总结：
   - 本次完成的工作
   - 关键决策与权衡
   - 未决问题
   - 下一步建议
2. 主动建议用户：「建议开启新会话以避免上下文累积」

**反模式**：默默继续在长会话里处理新任务，不写 checkpoint，不提示用户。

→ 触发 Workflow: `/context-checkpoint`
### §4.15 Cloud Run 部署规范

- 云原生部署优先使用 `--source` 模式，绕过镜像库域名迁移带来的权限死锁。
- Dockerfile `CMD` 必须精准对齐包含 FastAPI `app` 实例的启动模块。

→ 详见 Wiki: `wiki/engineering/gcp-cloud-run-deployment.md`
→ 来源: L-2026-04-30-002

### §4.16 运行时权限补全

- 部署成功不代表业务可用。必须补全 Service Account 的运行时权限（如 `roles/aiplatform.user`）。

→ 详见 Wiki: `wiki/engineering/gcp-iam-runtime-permissions.md`
→ 来源: L-2026-04-30-001

### §4.17 大模型原生技能集成与子进程消解（Subprocess Elimination）

- 在容器化或 Serverless 部署环境（如 Cloud Run）中，严禁在后端拉起外部 CLI 进程（如 npx skills 或 custom CLI）执行格式化/规则润色任务。
- 必须将规则定义（SKILL.md）物理落盘于项目内并以静态文件方式读取，作为二阶段 LLM 提示词输入，使用与生成主模型同等健壮的级联降级策略进行重写润色。

→ 详见 Wiki: `wiki/design-patterns/llm-native-skill-integration.md`
→ 来源: L-2026-05-18-001

---

## §5 Workflow 强制触发规则

本规则体系的核心：**八个 Workflow 不是可选工具，是强制入口**。

### Workflow 文件路径

所有 Workflow 的**详细执行步骤**定义在独立文件中。Agent 触发某个 Workflow 时，**必须先读取对应文件**再按步骤执行。

- `/plan-task` → `/Users/chaojin/Antigravity Projects/Generalrule/antigravity/workflows/plan-task.md`
- `/verify-done` → `/Users/chaojin/Antigravity Projects/Generalrule/antigravity/workflows/verify-done.md`
- `/find-skill-first` → `/Users/chaojin/Antigravity Projects/Generalrule/antigravity/workflows/find-skill-first.md`
- `/promote-lessons` → `/Users/chaojin/Antigravity Projects/Generalrule/antigravity/workflows/promote-lessons.md`
- `/self-correct` → `/Users/chaojin/Antigravity Projects/Generalrule/antigravity/workflows/self-correct.md`
- `/rollback` → `/Users/chaojin/Antigravity Projects/Generalrule/antigravity/workflows/rollback.md`
- `/critic-review` → `/Users/chaojin/Antigravity Projects/Generalrule/antigravity/workflows/critic-review.md`
- `/context-checkpoint` → `/Users/chaojin/Antigravity Projects/Generalrule/antigravity/workflows/context-checkpoint.md`

**适用说明**：
- Antigravity：通过 GUI 注册为 Global Workflow，`/` 直接触发
- Claude Code：符号链接到 `~/.claude/commands/`，`/` 直接触发
- Gemini CLI：读取本规则后，通过上方路径查阅 Workflow 详细步骤并执行

### §5.1 `/plan-task` 触发条件
**任何编码任务收到后第一步必须调用**，无一例外。
- 简单任务：计划可以短，但必须走
- 复杂任务：按 workflow 要求完整展开

### §5.2 `/find-skill-first` 触发条件
**开发任何新功能之前必须调用**，用于检索现有 Skill 和开源方案。
- 流程：搜索 → 评估 → 有匹配则集成 → 无匹配才手写
- 本项目已安装 `find-skills` 和 `skill-creator`，可通过 `@find-skills <需求>` 直接检索

### §5.3 `/verify-done` 触发条件
**标记任务完成前必须调用**，跑完全部验证步骤才允许说"完成"。
- 任何步骤失败必须修复后重跑，不得跳过

### §5.4 违规处理
如 agent 未按上述触发规则调用 Workflow，用户有权要求 agent **立即重来并反思未触发的原因**。反思结果应作为一条 lesson 记录到 `tasks/lessons.md`。

### §5.5 多智能体协作（Critic Review Pattern）

涉及**架构决策**或**Complex 档任务**时，启用 Producer-Critic-Judge 三角架构：

**角色边界（来自 Harness Engineering 2026 规范）**：
- **Producer**（主 agent）：产出方案，但**不能**自我审查
- **Critic**（评审 agent 或人类）：**只提建议**，不能否决/通过
- **Judge**（用户）：**只决定**通过或不通过，不写建议

**触发条件**：
- `/plan-task` 判定为 Complex 档
- 涉及核心链路修改（LLM 调度、爬虫管道、数据 Schema）
- 用户主动调用 `/critic-review`

**禁止**：让同一个 agent 同时扮演 Producer 和 Critic（会导致"自我安慰式审查"）。

→ 触发 Workflow: `/critic-review`
→ 详见 `wiki/engineering/harness-engineering-principles.md` §2

### §5.6 Git 安全快照（Snapshot & Rollback）

任何 Normal/Complex 档任务**写代码前**，强制建立 Git 检查点：

**Plan 阶段强制**：
- `/plan-task` 第 0.5 步：执行 `git status` 确认工作区干净
- 不干净 → 强制要求用户先 `git stash` 或 commit
- 干净 → 自动 `git commit --allow-empty -m "Auto-checkpoint before <task-name>"`

**回滚条件**：
- verify-done 失败 + Reflexion Loop 已用完 3 次仍失败
- 用户主动调用 `/rollback`

**回滚动作**：`git reset --hard <checkpoint-hash>` + 输出"已回到任务开始前的状态"。

→ 触发 Workflow: `/rollback`
→ 详见 `wiki/engineering/harness-engineering-principles.md` §4.4

---

## §6 Lessons 系统（自我学习机制）

### §6.1 写入时机
每当用户对 agent 输出做出**纠正**（指出错误、要求修改方向、否定方案、指出遗漏），agent 必须在当轮回复**结束前**：

1. 识别纠正的核心点
2. 按 §6.2 格式追加到项目 `tasks/lessons.md` **顶部**
3. 在回复末尾用一行说明：`已记录 lesson L-YYYY-MM-DD-NNN`

### §6.2 Lesson 标准格式
```markdown
## L-2026-04-22-001
- **场景**: <一句话描述触发 lesson 的任务场景>
- **错误行为**: <agent 原本打算或已经做的事>
- **用户纠正**: <用户指出了什么、要求怎么改>
- **规则**: <抽象出的、未来遇到类似场景要遵守的指令>
- **关键词**: <便于 grep 搜索的标签，用逗号分隔>
- **适用范围**: <"本项目" 或 "全局" 或 "可固化为 Skill">
```

### §6.3 读取机制
`/plan-task` 的第一步就是读 `tasks/lessons.md`，强制 agent 在每次规划前消费经验，不存在"写了但不读"。

### §6.4 三条升级通道
Lessons 不是终点，好的经验必须毕业：

1. **通道一：留在项目内**
   仅适用于本项目的经验，留在 `tasks/lessons.md`。
   
2. **通道二：提升为全局规则**
   跨项目普适的 lesson（适用范围="全局"），**用户手动**搬到 `general-global-rule.md` 对应章节。原 lesson 标注 `已提升至 User Rules YYYY-MM-DD，此条作废`，**不删除**（保留来源便于回溯）。
   
3. **通道三：固化为 Skill**
   当 lesson 本身是一个**可执行的完整工作流**（而不仅是一条规则），用 `@skill-creator` 封装成可复用的 Skill。例如"微信公众号反爬标准流程"、"YouTube 字幕清洗管道"。成功固化后原 lesson 标注 `已固化为 Skill: <skill-name>`。

Agent 判断适用范围和升级建议，**但最终搬运由用户手动执行**——避免 agent 自作主张污染全局规则。

### §6.5 防腐机制
- 单项目 `lessons.md` 条目数超过 **30 条**时，agent 应在回复中提醒用户："建议启动月度整理"
- 已标注"作废"的 lesson 保留不删

---

## §7 开发前必搜原则

与 §5.2 呼应。任何新功能开发前：

1. 先通过 `@find-skills` 检索 Skills 生态
2. 搜索 PyPI 上的开源库（优先 star 数高、近期有维护、有文档的）
3. 仅在确认无现成方案后才从零手写

**严禁重复造轮子**。

---

## §8 安全与禁区

- 严禁在代码中硬编码 API Key、密码、Token
- 所有密钥从环境变量或 `.env`（`.gitignore` 已排除）读取
- 涉及用户数据的爬虫/清洗必须遵守目标站点的 ToS 和 robots.txt
- 出现法律/合规灰色地带立即停下询问用户

---

## §9 更新记录

| 日期 | 变更 | 原因 |
|---|---|---|
| 2026-04-22 | 初版建立 | 规则体系搭建 |

---

**本文件是单一事实来源（Single Source of Truth）。** 其他文件只引用本文件的章节编号（如"依照 §3.3"），不复述内容。更新本文件时无需同步改其他文件。

---

## §10 LLM Wiki 知识库使用规范

### §10.1 Wiki 路径
`/Users/chaojin/Antigravity Projects/Generalrule/wiki/`


### §10.2 必须触发 Wiki Query 的场景
以下情况**强制先查 Wiki，再联网**：
- 遇到报错或 debug 问题
- 用户提出新的复杂技术问题
- 涉及 GCP、Notion、YouTube、LLM 调度、爬虫等已有领域

**Query 格式**：先读 `wiki/index.md` 找相关领域 → 读对应页面 → 给出答案并标注来源

### §10.3 必须触发 Wiki Ingest 的场景
以下情况**强制写入 Wiki**：
- 用户纠正了 agent 的错误（同时写 lessons.md + Wiki）
- 从公网找到有价值的解决方案
- 解决了一个复杂 bug，方案值得复用
- 发现了新工具/新 API 的使用方式

**Ingest 格式**：写入对应领域目录，更新 index.md 索引，git push

### §10.4 定期 Health Check
用户发 `run health` 或 `/health` 时，执行：
1. 检查所有页面的 frontmatter 完整性
2. 检查孤立页面（没有被 index.md 引用）
3. 检查断链
4. 输出健康报告

### §10.5 Wiki 写入格式（frontmatter 强制）
每个 Wiki 页面顶部必须包含：
```yaml
---
title: <页面标题>
domain: <engineering|llm|crawler|frontend|image-gen|design-patterns>
keywords: [关键词1, 关键词2]
source_lesson: <来源 lesson ID，如有>
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
---

## §11 模型选择规则（Agent 调用 LLM 专属）

Agent 根据任务复杂度自动选择 DeepSeek 模型，无需手动切换：

### §11.1 模型速查

| 模型 ID | 适用场景 |
|---------|---------|
| deepseek-v4-flash | 简单问答、工具调用、单次查询、日常对话 |
| deepseek-v4-pro | debug、代码审查、架构设计、复杂多步推理 |

### §11.2 触发 pro 的场景
以下情况强制自动切换到 deepseek-v4-pro：
- 复杂 debug / 报错分析
- 代码审查、架构设计
- 涉及 5+ 文件的大规模修改
- 用户明确要求高质量输出

### §11.3 切换方式
通过 /model deepseek-v4-pro 或 /model deepseek-v4-flash 临时切换，无需重启会话。

→ 详见 Wiki: wiki/llm/model-selection.md
→ 来源: L-2026-05-18-003
```

---

## §11 新 Skill 创建规范

需要创建新 Skill 时，**必须先调用 skill-creator**，不要从零手写 SKILL.md。

### Hermes 调用方式
```bash
hermes skills install skills-sh/anthropics/skills/skill-creator
```
然后触发：`@skill-creator <需求描述>`

### Claude Code 调用方式
skill-creator 已在 `~/.claude/skills/` 目录下可用，直接说：
「使用 skill-creator 创建一个关于 <需求> 的 skill」

### 触发条件
- 用户说"创建一个新 skill"
- 发现某个工作流值得固化为可复用 skill
- `/promote-lessons` 判定某条 lesson 适合固化为 skill

### 禁止行为
- ❌ 不调用 skill-creator 直接手写 SKILL.md
- ❌ 创建的 skill 没有 YAML frontmatter
- ❌ skill 描述不包含触发条件
