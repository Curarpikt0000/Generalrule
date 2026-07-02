# CHANGELOG —— Generalrule repo 版本管理

> **纪律来源**：general-global-rule.md §6.6。任何 agent、任何 branch 改动本 repo，都必须在此留一条记录。
> **记录格式**：`### 日期 [branch] agent —— 一句话主题`，正文列「改了什么 / 为什么」。
> **分工**：本文件管 repo 的**结构性改动**（规则文件、模板、self-skill、目录骨架的增删改）。
> wiki/ 下**单个知识页**的增删改迁移，记在 `wiki/CHANGELOG.md`，本文件不重复。
> **白名单纪律**：下方「结构白名单」列出本 repo 所有有用文件/文件夹。**增减任何目录或结构性文件，必须同步更新白名单**。
> **禁止\"一把梭\"**：提交前先 `git status` 核对，只提交本次有意改动且在白名单内的文件——历史上因盲目 `git add .` 混入过别项目文件（见 2026-06-13 治理记录）。

---

## 结构白名单（有用文件 / 文件夹）

> 下列是 repo 的「骨架」。wiki 各领域下的**具体知识页**不在此逐一登记（由 `wiki/CHANGELOG.md` + 各领域 `README.md` 维护），但**领域目录本身**的增减要在此更新。

```
Generalrule/
├── CHANGELOG.md                     # 本文件：repo 版本管理 + 结构白名单
├── .gitignore                       # 忽略 .DS_Store / .obsidian / config.md / .env
├── antigravity/
│   └── general-global-rule.md       # 【SSOT】认知纪律 + 五步链路 + 五阶段 workflow + 指针索引
├── self-skill/                      # 自有通用 skill 收纳处（只放通用 skill，特用禁止）
│   ├── README.md                    # self-skill 准入宪法（准入/copy/登记规则）
│   ├── AUTHORING.md                 # 怎么写/copy 一个 skill 的操作手册（宪法的操作配套）
│   ├── llm-wiki/                    # wiki 写作 skill（改造自公网 kingqiu/llm-wiki-skill）
│   │       ├── SKILL.md
│   │       ├── README.md
│   │       ├── config.example.md        # 配置示例（本机 config.md 不入库）
│   │       └── .gitignore
│   ├── webworms/                     # 4 层爬虫标准框架（自有 Hermes skill 改造）
│   │       ├── SKILL.md
│   │       ├── references/
│   │       │   ├── site-specific-notes.md
│   │       │   └── base_scraper_impl.md
│   │       └── scripts/
│   │           └── wechat_scraper.py
│   └── agent-slides/
│           ├── SKILL.md             # orchestrator（指向 skills/<name>/SKILL.md）
│           ├── README.md            # 来源/许可/依赖/差异说明
│           ├── LICENSE              # 上游 MIT 许可（署名保留）
│           └── skills/
├── persona-distillation/            # 人格/视角蒸馏术（改造自女娲 alchaincyf/nuwa-skill）
│       ├── SKILL.md                 # 三步流程：调研swarm → 框架提炼 → 生成skill+自检
│       ├── references/
│       │   ├── extraction-framework.md   # 六层提取框架 + 心智模型三重验证 + 质量清单
│       │   └── skill-template.md         # 人物 skill SKILL.md 模板
│       └── scripts/                 # 4 个纯 stdlib 工具脚本
│           ├── download_subtitles.sh     # YouTube 字幕下载
│           ├── srt_to_transcript.py      # SRT → 纯文本清洗
│           ├── merge_research.py         # 调研结果合并统计
│           └── quality_check.py          # 6 项通过标准自检
├── project-context-persistence/     # 项目上下文持久化（采集脚本 + cron 配方 + 踩坑）
│       ├── SKILL.md
│       ├── scripts/
│       │   └── collect_topic_conversation.py  # Hermes state.db 对话采集脚本
│       └── references/
├── _template/                       # 新项目 / 新机初始化模板
│   ├── AGENTS.md                    # 项目入口模板
│   ├── ONBOARDING.md                # 新机 / 新 agent 通用接入指南
│   └── tasks/
│       ├── lessons.md
│       └── todo.md
├── hermes-profiles/                 # Hermes 议会模式人格蒸馏蓝图
│   ├── README.md                    # 入口：两个实例 + 目录索引
│   ├── ARCHITECTURE.md              # Hermes profile/SOUL 匹配机制
│   ├── MECHANISM-DESIGN.md          # 议会模式对话机制与人格设计
│   ├── DISTILLATION-PROCESS.md      # 人格蒸馏流程（从资料到 skill）
│   ├── COPY-GUIDE.md                # 给其他 Hermes 的复刻指南
│   ├── PROJECT-PROGRESS.md          # 项目进度与架构决策记录
│   ├── finance-hero/                # Finance Hero 完整蓝图（11 位投资大师）
│   ├── general-hero/                # General Hero 完整蓝图（10 位伟人 + 四件套脚手架）
│   └── handbook/                    # 蒸馏方法论 + 模板集（可复用于新 profile）
└── wiki/                            # 共享知识库（三层索引，见 wiki-ingest-guide）
    ├── index.md                     # 第 1 层 · 领域总索引
    ├── CHANGELOG.md                 # wiki 知识页版本管理
    ├── agent-rules/                 # 体系自身规则（README + 规则页）
    ├── crawler/                     # 爬虫（README + 页）
    ├── design-patterns/             # 设计模式（README + 页）
    ├── engineering/                 # 工程实践（README + 页）
    ├── finance/                     # 金融（README + precious-metals/ 子领域）
    ├── frontend/                    # 前端（README + 页）
    ├── image-gen/                   # 图像生成（README + 页）
    └── llm/                         # LLM 调用（README + 页）
```

**不入库**（.gitignore 覆盖）：`.DS_Store`、`.obsidian/`、各 skill 的 `config.md`、`.env`。

**待下轮处理（已知归类问题，非本轮范围）**：
- `wiki/agent-rules/` 下 4 个 Hermes 特定 / finance 特用页面（`finance-hero-distillation`、`google-finance-research-integration`、`moomoo-opend-integration`、`hermes-profile-filesystem-discipline`）归类偏特用，待专门一轮判断去留 / 迁移。
- `wiki/engineering/youtube-pipeline-genimages-template-issue.md` 偏特用，同上。
- 部分旧页 frontmatter 未升级到方案 Z 双字段（如 `url-fidelity`、`llm/cloud_test`），待统一规范化。
- 知识页内残留 `file://` 写死本地链接（如 `wiki/crawler/crawler-bypass-handbook.md`、`wiki/agent-rules/moomoo-opend-integration.md`，多为历史 lesson 引用），待统一改相对链接 / 去本地化。

---

## 变更记录

### 2026-07-02 [ub-branch] Hermes —— §7.5 新增「项目知识每日灾备同步」规则（ChaoProjects 每晚 push / 每早 pull）
- **改了什么**：§7.5 多机同步纪律追加一条——Uber 项目代码与数据统一进内网 monorepo `ChaoProjects`，每晚 6:00 JST 自动全量增量 push（cron `24e29c8f2cbc`），每早 9:00 JST 自动 pull（cron `49af88bb111e`）；含红线（密钥绝不进 repo + push 前扫描）、大文件排除（faiss/bm25/duckdb/scratch 靠脚本重建）、A 组已有 remote 项目只 pull 不重复打包。
- **为什么**：实现 VM 宕机后 clone 即恢复全部项目、所有 agent 共享最新项目知识（灾备 + 知识同步）。仅 Uber 机执行且含内网地址，故只入 ub-branch。

### 2026-06-22 [main+ub-branch] Hermes —— 新增认知纪律 §2.11 进度持久化（PROGRESS.md，抗中断）

**改了什么**：`antigravity/general-global-rule.md` 新增 **§2.11 进度持久化（Progress-First，抗中断）**——执行命令前先写 `PROGRESS.md`（目标/步骤/验收/当前进度），长任务做阶段性分解、单阶段 ≤30 分钟、每阶段末把"已完成/已验证/下一步/中间产物路径"落盘；核心目的是抗中断：用户消息截断或会话被打断后，下一轮先读 `PROGRESS.md`（项目级读 `docs/context-log.md`）恢复最新状态。§2 标题「十条」→「十一条」，文件最后更新日期→2026-06-22，加一行指向 `five-step-pipeline.md` 的落地细节指针。

**为什么**：应 @Chao Jin 要求。实际多次出现任务被 out-of-band 消息中途截断、会话超时断连导致上下文丢失。把进度只留在 context 窗口里 = 一断就全丢；强制落盘 PROGRESS.md 才能真正断点续传。通用执行纪律，不涉 Uber IP——两边 Hermes（读 main / 读 ub-branch）及所有 agent 同等遵守。本次仅改规则正文（无新增结构性文件），白名单无需更新。


### 2026-06-21 [main+ub-branch] Hermes —— 蒸馏「禁止闭门造车」升级为全局第一铁律 + 打通指针

**为什么**：实测踩坑——3 个调研 subagent 配了 web 工具却不调用、凭训练知识编内容（一个还谎称无联网，实测网络正常）。现有 `hermes-profiles/DISTILLATION-PROCESS.md` §5 虽有"手蒸馏必跑 WebSearch"但仅对 Level 3、措辞软、无验收机制，拦不住此坑。应 @Chao Jin 要求升级为所有蒸馏项目的全局硬门，两边 Hermes（读 main / 读 ub-branch）遵守同一准则。通用技能准则，不涉 Uber IP。

**改了什么**：
- `self-skill/persona-distillation/SKILL.md`：新增「⛔ 第一铁律：禁止闭门造车」独立小节（5 条硬性要求 + 实测可用检索通道 + 验收门）+ Phase1「每个 agent 硬性要求」补真搜+tool_trace 核对条款
- `hermes-profiles/DISTILLATION-PROCESS.md`：§5「防编造纪律」升级为「第一铁律，所有 Level 强制」（原仅 L3）+ tool_trace 验收 + 2026-06-21 反例教训 + 顶部加指向 persona-distillation 的统一 SSOT 指针
- `hermes-profiles/README.md`：「上游规范」节加统一蒸馏方法论指针（指向 self-skill/persona-distillation + 第一铁律）
- 两套蒸馏文档从此互相链接，规则单一权威，不再漂移；**两 branch 内容一致**

### 2026-06-21 [main] general Hermes —— General Hero 完整蓝图上传 + hermes-profiles/ 纳入结构白名单

**为什么**：General Hero 蓝图此前仅以 stub README.md 存在于 repo（上一轮 commit `3114001` 只上传了 finance-hero）。本轮从 `~/hermesagent/Distill/蒸馏Hermes/general-hero/` 拷贝清理后的 59 文件（原 259 文件 / 7.4MB），含 SOUL.md + 10 位大师 skills/references + 四件套脚手架 + deploy.md + sync.sh。毛泽东目录从 204 噪音文件降至 9 个（去除多语言 README/Python tools/CHANGELOG/internal/docs/tools/prompts/data 等 artefacts）。

**改了什么**：
- `hermes-profiles/` 纳入结构白名单
- `hermes-profiles/general-hero/`：从 stub 升级为完整蓝图（59 文件，1.6MB）
- `hermes-profiles/README.md`：更新目录结构 + General Hero 描述（去"由另一 profile 管理"措辞）+ 快速开始 #6
- `hermes-profiles/PROJECT-PROGRESS.md`：新增里程碑行 + 更新资产表分"已上传至 repo"/"本地 SSOT"/"运行时"三栏
- `self-skill/README.md`：新增 `hermes-profiles/handbook/`（蒸馏议会方法论） 指针
- `wiki/agent-rules/skill-register.md`：Self-Skill 区新增董事会方法论指针行

### 2026-06-21 [main] Hermes —— persona-distillation self-skill（女娲方法论改造）纳入 repo

**为什么**：人格/视角蒸馏能力（把真人或领域视角蒸馏成可运行 SKILL.md）此前只在 wiki `finance-hero-distillation.md` 有实战经验记载，方法论本体（女娲 `alchaincyf/nuwa-skill`）从未沉淀为常驻通用 skill，每次用都临时 clone。应 @Chao Jin 要求落地为通用 self-skill，供所有 Hermes/agent 取用。

**准入评审（对照 self-skill/README.md 宪法 + IP 红线）全部 PASS**：脱离公司/项目仍成立的通用能力（造人格）✓；无 API key/token ✓；红线扫描无 Uber 专有内容（uber/aifx/usearch/presto/cerberus/账号名 零命中，仅"内部备忘录""目录内部"等普通中文词）✓；写死路径零命中（用 `<skills_dir>` 占位）✓；上游署名与 MIT 保留 ✓。

**相对上游女娲的改造**：① 路径从 Claude 专属 `.claude/skills/` 改为通用 `<skills_dir>` 占位；② agent swarm 从抽象描述落到本体系 `delegate_task`（指向 parallel-subagent-orchestration）；③ 新增"主题人格"（不模拟真人）为一等路径（上游偏真人）；④ 检索工具写成通用 web_search/browser/webworms，不绑特定平台或公司内部工具；⑤ 接 Hermes profile + SOUL 落地章节。上游精华（心智模型三重验证、表达 DNA、矛盾保留、诚实边界、Agentic Protocol、质量自检脚本）全部保留。

**改了什么**：
- `self-skill/persona-distillation/`：新增。含 `SKILL.md` + `references/`（extraction-framework.md 六层提取框架、skill-template.md 人格模板）+ `scripts/`（download_subtitles.sh 字幕下载、srt_to_transcript.py SRT清洗、merge_research.py 调研合并、quality_check.py 质量自检，均纯 stdlib）
- `wiki/agent-rules/skill-register.md` §8：新增 persona-distillation 登记行
- `self-skill/README.md` §四：新增 persona-distillation 行
- `CHANGELOG.md`：结构白名单 self-skill 区新增 persona-distillation/ 子结构

### 2026-06-17 [main] Hermes —— project-context-persistence self-skill（采集脚本 + SKILL）纳入 repo
**为什么**：general-global-rule.md §5 上下文压缩铁律引用了 `skill project-context-persistence` 作为落地机制，但此前不存在。从零创建，含采集脚本 + skill 定义 + cron 模板。
- `self-skill/project-context-persistence/`：新增，含 `SKILL.md`（采集方案、cron 模板、踩坑）、`scripts/collect_topic_conversation.py`（Hermes state.db 对话采集脚本）
- `~/.hermes/SOUL.md`：同步更新，启动开关整合为「建结构 + 每日上下文归档（新 topic/项目自动建）」一条链
- `~/.hermes/scripts/collect_topic_conversation.py`：部署到运行实例
- `~/.hermes/skills/devops/project-context-persistence/`：skill 部署到运行实例
- `CHANGELOG.md`：结构白名单新增 `project-context-persistence/`
**为什么**：agent-slides（公网开源 `mpuig/agent-slides`，MIT）是脱离公司/项目仍成立的通用「做 PPT」能力，符合 self-skill 准入。经冲突评审对照 general-global-rule.md + uber-adaptation.md 全部 PASS（无自动 push/commit、无遥测/外部网络写入、无 Uber IP、无写死路径、署名与 MIT 保留）。
- `self-skill/agent-slides/`：新增。只收 skill 定义——orchestrator `SKILL.md` + `README.md` + `LICENSE` + `skills/`（7 个子 skill：extract/build/edit/audit/critique/polish/full，含 references）。**未 vendoring 上游 `src/` CLI 引擎**：运行时由 `uvx --from agent-slides` 从 PyPI 按需拉取，vendoring 不改变运行行为只增重（详见该目录 README）。
- `self-skill/AUTHORING.md`：新增。把 self-skill/README.md 宪法操作化为「怎么写/copy 一个 skill」分步手册，以 agent-slides 为 worked example。
- `wiki/agent-rules/skill-register.md` §8：新增 agent-slides 登记行。
- `self-skill/README.md` §四：补 agent-slides 行（并补此前漏登的 webworms 行）；§五加 AUTHORING.md 指针。
- `CHANGELOG.md`：结构白名单 self-skill 区新增 agent-slides/ 子结构 + AUTHORING.md。

### 2026-06-15 [main] Hermes —— webworms 爬虫 skill 纳入 self-skill 区 + skill-register 登记

**为什么**：webworms（4 层降级回退网页爬虫框架）原为 Hermes C 类专用 skill，经改造去写死路径后纳入通用 skill 收纳，供所有 agent 取用。应 @Chao Jin 要求放入 GitHub 以便他机安装。

**改了什么**：
- `self-skill/webworms/`：新增，含 SKILL.md + references/site-specific-notes.md + references/base_scraper_impl.md + scripts/wechat_scraper.py
- `self-skill/webworms/scripts/wechat_scraper.py`：去写死 `/tmp/` 路径，改为可配置 output_dir（默认 tempfile）
- `wiki/agent-rules/skill-register.md` §8：新增 webworms 登记行（用途 + 来源 + 取用方式）
- `CHANGELOG.md`：结构白名单 self-skill 区新增 webworms/ 子结构

### 2026-06-14 [main] Hermes —— 自述填充 agent-config-matrix + SOUL.md 指针同步 Generalrule 最新

**为什么**：补齐 SSOT「新 agent 如何配置自己」缺口。Hermes 如实逐条自述自身配置机制（入口/人格/记忆/workflow/技能/与 repo 关系），填充到 agent-config-matrix；同时同步 SOUL.md 指针使其引用 Generalrule 最新状态（开工第 0 步 + agent-config-matrix 引用）。

**改了什么**：
- `wiki/agent-rules/agent-config-matrix.md`：Hermes 条目从「待自述」→ 已采集（7 维详细逐条），速查矩阵同步修正。
- `~/.hermes/SOUL.md`：指针节更新——引用 Generalrule 最新路径，新增 agent-config-matrix 引用，补入「开工第 0 步」指向。

### 2026-06-14 [main] Claude Code CC-vm (Opus 4.8 [1m]) —— 规则正文措辞统一（wiki 页改动见 wiki/CHANGELOG.md）

**为什么**：承接「全 agent 统一 SSOT」治理——收齐各 agent 第一人称实测后，把规则正文里过时 / 幻影措辞统一。

**改了什么（结构性 / 规则文件）**：
- **`antigravity/general-global-rule.md`**：§1 行 3 共享规范 agent 列表去掉幻影「Gemini CLI」（实际无此 agent，gemini 即 Antigravity）。
- 其余为 wiki 知识页改动（各 agent 实测自述填全 `agent-config-matrix`、新建 `soul-authoring-guide`、修正 `five-step-pipeline` 五阶段载体描述、多页「三 Agent→多 agent」+ 清 `promote-lessons` 死引用），详见 `wiki/CHANGELOG.md` 同日条目。

> 本轮未增删目录 / 结构性文件，结构白名单无需变更。
> Uber 适配层（`uber-adaptation.md`）的「上下文持久化方案 + 运行时拓扑修正」**仅在 ub-branch**，记录见 ub-branch 本文件同日 [ub-branch] 条目（不进 main，IP 隔离）。

### 2026-06-14 [main→ub-branch] Claude Code (Opus 4.8) —— 开工第 0 步铁律 + _template 接入文档通用化（承接并完成 2026-06-13 待续）

**为什么**：承接上一轮治理「待续」三步并收口；同时按用户要求把「开工先 pull 对账」升格为体系铁律——任何 agent 任何机器开工第一步先与 SSOT 对齐，杜绝基于过期规则 / 缺失技能开工。

**改了什么**：
- **general-global-rule §7.5**：原「开工前先同步」升级为**「开工第 0 步（铁律，先于一切任务）」**——每次开工先 `git pull` 全部文件，再对账三件事（①规则/Wiki/workflow 更新 ②本地入口/配置同步 ③核心技能/MCP 安装，对照 `skill-register`、经用户确认再装），并补「没 pull、没对账，不许开工」。§3 五步链路开头加前置指针指向 §7.5。
- **_template 接入文档通用化（完成 2026-06-13 待续步骤 1+2）**：三份过时的 UB-Mac 一次性脚本（`HANDOVER_UB_INIT.md` + `TASK_antigravity_config.md` + `TASK_claude_code_config.md`——满是写死 `~/UBAntigravity Projects/` 路径、Mac 专属 `sed -i ''` / `~/Library/`、已废弃 UB 前缀目录方案）**合并重写为单一 `_template/ONBOARDING.md`《新机 / 新 agent 通用接入指南》**：去写死路径、去 Mac 专属、给通用原则（clone→选分支→入口指针→开工第 0 步→wiki 推送→验收清单）。白名单同步更新。
- 至此 2026-06-13「活规则文件去写死路径」范围（general-global-rule / wiki-ingest-guide / _template）全部清零；仅余知识页历史 `file://` 链接列入「待下轮处理」。

> 2026-06-13 待续步骤 3「推送 main 后 merge 到 ub-branch」为纯 git 同步动作，随本轮一并执行（含落盘上一轮成果 commit `98d6a1f`、拉取整合 origin/main 落后提交、main→ub-branch 同步）。

### 2026-06-13 [main] Claude Code (Opus 4.8) —— repo 治理与升级（统一交流窗口定型）

**为什么**：把本 repo 明确为「用户 × 所有 agent（私人 Mac + Uber Mac/VM 上的 Claude Code / Hermes / Antigravity / Codex / Cursor，未来更多）的统一交流窗口」。目标——任一 agent 读完即知自己属于哪个系统、该守什么 rule、如何积累与分享经验。三条铁律落地：① 绝不写死机器路径，给通用原则；② 任何 branch 任何改动留证据（即本 CHANGELOG）；③ 拒绝"一把梭"，维护白名单。

**改了什么**：
- **新增 `self-skill/`**：通用 skill 收纳处。`README.md`（准入宪法：只收通用 skill，特用禁止；copy 流程去写死路径/去凭据；copy 后必须登记）+ `llm-wiki/`（改造自公网 `kingqiu/llm-wiki-skill`，去 Quartz/双语/写死路径，适配本体系 wiki 形态）。
- **合并 skill 清单**：`skill-registry.md` + `skill-catalog.md` → `skill-register.md`（对账机制 + A类对账表 + 各环境全量明细 + Self-Skill 区 + 跨环境获取速查）。13 处 `[[skill-registry]]`/`[[skill-catalog]]` 引用全部改为 `[[skill-register]]`。main 版隐藏 Uber 专属明细（IP 隔离，指向 ub-branch）。
- **general-global-rule.md 升级**：措辞从"三个 agent"扩为"所有 agent（…Codex/Cursor…）"；§6 wiki 写作优先调 llm-wiki skill；§6.5 新增 self-skill 收纳指针；新增 §6.6 Repo 版本管理纪律；§7.5 重写为「main + ub-branch 超集」分支模型；§8 指针表登记 self-skill/README、根 CHANGELOG、wiki/CHANGELOG。
- **删除误传/重复**：顶层 `AGENTS.md`（别项目内容）、顶层 `engineering/`（与 wiki 版完全重复）、`youtube-automation/`（Hermes 杂志项目，含 OAuth 凭据路径与 Drive ID，特用+凭据，绝不该进通用 repo）、`workflows/.../webworms.md`（已是 C 类专用 skill，重复）。
- **去版本控制垃圾**：`.DS_Store`×2、`.obsidian/`×4 从 git 移除；新 `.gitignore` 覆盖。
- **迁移 + 升级**：`wiki/com/dsifo-threshold-logic.md` → `wiki/finance/precious-metals/sifo-threshold-logic.md`（新建 finance 领域 + README + precious-metals 子领域，frontmatter 升级方案 Z）；`workflows/claude-code-rules/auto-memory-boundary.md` → `wiki/agent-rules/auto-memory-boundary.md`（升级为正式规则页，去写死路径、扩措辞、加 frontmatter）。顶层 `workflows/` 清空移除。
- **wiki/index.md 重写**：8 领域三层索引、登记 finance、清理混入索引表的具体页、修正写死路径表述、补 url-fidelity，全部引用零断链。
- **wiki-ingest-guide.md**：领域映射表加 finance 行，"7 个领域"→"8 个"。
- **新增本 CHANGELOG.md + wiki/CHANGELOG.md**：落地版本管理纪律。

**待续（同一治理计划剩余步骤）**：活规则文件去写死路径（wiki-ingest-guide/general-global-rule/_template）、重写 `_template/HANDOVER_UB_INIT.md` 为通用接入指南、推送 main 后 merge 到 ub-branch（ub-branch 恢复 Uber 专属明细）。
