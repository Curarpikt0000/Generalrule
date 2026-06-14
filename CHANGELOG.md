# CHANGELOG —— Generalrule repo 版本管理

> **纪律来源**：general-global-rule.md §6.6。任何 agent、任何 branch 改动本 repo，都必须在此留一条记录。
> **记录格式**：`### 日期 [branch] agent —— 一句话主题`，正文列「改了什么 / 为什么」。
> **分工**：本文件管 repo 的**结构性改动**（规则文件、模板、self-skill、目录骨架的增删改）。
> wiki/ 下**单个知识页**的增删改迁移，记在 `wiki/CHANGELOG.md`，本文件不重复。
> **白名单纪律**：下方「结构白名单」列出本 repo 所有有用文件/文件夹。**增减任何目录或结构性文件，必须同步更新白名单**。
> **禁止"一把梭"**：提交前先 `git status` 核对，只提交本次有意改动且在白名单内的文件——历史上因盲目 `git add .` 混入过别项目文件（见 2026-06-13 治理记录）。

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
│   └── llm-wiki/                    # wiki 写作 skill（改造自公网 kingqiu/llm-wiki-skill）
│       ├── SKILL.md
│       ├── README.md
│       ├── config.example.md        # 配置示例（本机 config.md 不入库）
│       └── .gitignore
├── _template/                       # 新项目 / 新机初始化模板
│   ├── AGENTS.md                    # 项目入口模板
│   ├── ONBOARDING.md                # 新机 / 新 agent 通用接入指南
│   └── tasks/
│       ├── lessons.md
│       └── todo.md
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
