# Wiki CHANGELOG —— 知识库版本管理

> **纪律来源**：general-global-rule.md §6（每次写 Wiki 须在此留记录）。
> **本文件管**：`wiki/` 下**知识页**的新增 / 删除 / 修改 / 迁移，以及**领域目录**的增减。
> repo 结构性改动（规则文件、模板、self-skill）记在根 `CHANGELOG.md`，本文件不重复。
> **记录格式**：`### 日期`，正文逐条 `[动作] 领域/页面 —— 说明`。动作 = 新增 / 删除 / 修改 / 迁移 / 重写。
> 写 wiki 优先调用 `self-skill/llm-wiki` skill，产出须符合 [[wiki-ingest-guide]]。

---

## 记录

### 2026-06-17 —— GenAI 隧道 watchdog 认证升级边界 + 端口漂移踩坑（Claude Code, Opus 4.8 [UB]）

- **[修改] `agent-rules/hermes-genai-api-integration.md`** —— §5 新增坑 5（cerberus idle 掉线 + 端口漂移 5436→5437 → `502 [Errno 99] Cannot assign requested address`，含 `/proc/net/tcp` 端口反查 + 杀干净重启修复）；文末新增 §8「GenAI 隧道 watchdog（系统 cron · 认证失败自动 Telegram 提醒）」，§7 运维表加一行。背景：6-17 LLM 又掉线复发，根因是 cerberus 周期性 idle 断链 + 端口漂移。删除了循环依赖的 Hermes 内部 `genai-proxy-watchdog`（`no_agent=false`，要调 LLM 才能查 LLM），改用系统 cron 纯脚本 watchdog（健康静默 / 自动重启 / 认证失败发 Telegram）。
- **[修改] `engineering/container-reboot-service-persistence.md`** —— 通用教训新增第 6 条「自愈有边界：区分可自动修 vs 需人介入（认证）」——纯脚本 watchdog 能修瞬时故障（进程死 / 端口漂移：服务起来但绑错端口，须按约定端口健康检查）但修不了凭证过期，应判定认证类故障并经「不依赖被监控服务的旁路通道（IM bot）」主动通知人重认证 + 告警限频。**关键教训**：watchdog 不只是「拉起进程」，要能识别自己修不了的故障类型并升级给人，否则无声反复重启失败比没有更难发现。
- 同步更新 `agent-rules/README.md`、`engineering/README.md` 两处页面描述。

### 2026-06-17 —— 咨询框架 skill 冲突消歧与去重指南（Cowork, Opus 4.8 [UB]）

- **[修改] `agent-rules/skill-register.md`** —— 新增第十节「咨询框架 Skill 冲突消歧与去重（跨 agent 通用行动指南）」，原「相关页面」顺延为第十一节。背景：这批咨询 skill（issue-tree-builder / hypothesis-tree / scpr-framework / storyline-builder / decision-memo-builder / top-down-memo / prioritization / management-consultant / consulting 等）全靠 description 语义自动触发、无优先级表，宽泛描述会抢专用 skill 的触发。新节给出：① 去重结论（`consulting` body ⊂ `management-consultant` 超集 4.6MB/228 文件，应归档；`prioritization` 常缺 frontmatter → 死 skill，应修不删）；② 14 行触发消歧表（哪件事用哪个、别让谁抢）；③ prioritization frontmatter 修复模板；④ 4 条通用原则。**关键教训（L-2026-06-17-001）**：判断 skill 能否删必须看 body+支撑文件体量，不能只比 description（consulting 实为 180KB 知识库，差点被当"两行重复品"删）；删除先归档不 `rm`；整改产出要写进共享 registry 让所有 agent 受益，不是只改本地 SKILL.md 只惠及当前 agent。源自 Cowork 本机 17 个咨询 skill 全景实测。

### 2026-06-16 —— 容器重启后服务恢复与开机持久化（Cursor, Opus 4.8）

- **[新增] `engineering/container-reboot-service-persistence.md`** —— 一次容器化开发环境内 AI agent 模型链路意外停机事故的复盘，已**匿名化/通用化**（剥离全部内部基础设施细节，仅保留通用架构模式与端口等本机通用细节）。核心教训：①容器 `/etc` 等系统目录通常是临时文件系统，跨重启的服务定义必须放持久化卷或平台持久 boot 机制，不能直接改 `/etc`（重启即丢）；②开机/恢复脚本要幂等 + 显式等依赖就绪以规避 boot 时序竞争；③后台常驻进程用 `setsid` 脱离会话避免被父进程组回收；④watchdog/自愈逻辑绝不能对它要修复的服务有循环依赖（反例：修模型链路的任务自己要先调模型）；⑤排障沿调用链逐跳验证（端口→进程→日志→服务定义→平台持久化层），用错误信息当 oracle 反推。同步登记进 `index.md` 第 2 层与 `engineering/README.md`。

### 2026-06-15 —— Cloud Run 部署同步陷阱（Claude Code, Opus 4.8）

- **[修改] `engineering/gcp-cloud-run-deployment.md`** —— 追加一节「部署同步陷阱：改了持久化层枚举/schema 却忘了重部署读取方」（来源 L-2026-06-15-001）。通用化教训：写入方往持久化层（Firestore/DB/MQ）加了新枚举值，但读取方仍跑不认得该值的旧镜像 → 旧读取方一遇新值即 `ValueError` 500 → 新数据进不了队列 → 下游静默停摆（最隐蔽，无报错只是「没数据」）。规则：枚举/schema 演进先升级所有读取方再写新值；非 git 项目靠 mtime + 部署 revision 时间戳对账是否上线；排查下游空转先查上游写入方。源自 magazine-podcast 扫描器停摆半月的真实事故。

### 2026-06-14 —— Codex VM 接入对账登记（Codex VM, GPT-5.4）

- **[修改] `agent-rules/skill-register.md`** —— 更新对账时间，注明 Codex VM 接入对账结果登记在 ub-branch 的 `uber-adaptation.md`。

### 2026-06-14 —— Agent 自述实测归集 + SOUL 指南 + 措辞统一 + workflow 载体修正（Claude Code CC-vm, Opus 4.8 [1m]）

- **[重写] `agent-rules/agent-config-matrix.md`** —— 用 8 份各 agent **第一人称实测**自述填全速查矩阵 + 逐 agent 七维详条：CC 家族（CC-home/Cowork/CC-vm 三类，机制同源差异在落地）、Antigravity（planning_mode+Artifacts，无 SOUL）、Hermes（家用+vm，有 SOUL.md）、Codex（SQLite 记忆）、Cursor（无持久层）。补 CC-vm 本机自述。**记一次教训**：一份替全部 9 个 agent 代填的旁观报告（uber-antigravity）经交叉核对系编造（虚构 CC 有 commands/、Hermes 是 soul.yaml、cowork 用 PostgreSQL、杜撰 Docker 镜像名），与各 agent 实测全面矛盾，整份弃用——只采信第一人称实测。
- **[新增] `agent-rules/soul-authoring-guide.md`** —— SOUL 写作指南 + SOUL.md 五节模板（身份/沟通规则/底线/启动开关/指针），据 Hermes 实测骨架。明确 SOUL **仅 Hermes 有**，其余 agent 无 SOUL 层、不要给它们造 SOUL 文件。登记进 `agent-rules/README.md`。
- **[修改] `agent-rules/five-step-pipeline.md`** —— 修正第二部分开头错误的五阶段载体描述（旧称「CC 用 ~/.claude/commands/、Antigravity 用 Customizations→Workflows」）：据多机实测改为各 agent 真实载体（CC=skill、Antigravity=planning_mode+Artifacts、Hermes=skill+SOUL、Codex=update_plan、Cursor=Plan Mode），明确无 agent 用 commands/ 目录。
- **[修改] 措辞统一** —— `agent-rules/README.md`（去 Gemini CLI、清「promote-lessons Workflow 自动维护」死引用、三 Agent→所有/各 agent，并注册 soul-guide）、`frontend/README.md`+`llm/README.md`+`image-gen/README.md`（清同款 promote-lessons 死引用）、`rtk-usage.md`/`auto-memory-setup.md`/`project-template.md`/`wiki-ingest-guide.md`（三 Agent→多 agent）、`crawler/bypass-waf-via-backend-api-discovery.md`（适用 Agent 去 Gemini CLI）。

### 2026-06-14 —— Agent 配置自述矩阵（Claude Code, Opus 4.8）

- **[新增] `agent-rules/agent-config-matrix.md`** —— 归集各 agent（Prompt A 通用自述）的配置机制，补 SSOT「新 agent 如何配置自己」缺口。首条填入 CC-home（家用机 Claude Code）完整七维自述；其余 8 个目标留【待该 agent 自述】占位（Antigravity/Hermes 附 CC 旁观推断，待各自确认转正）。登记进 `index.md` 第 2 层与 `agent-rules/README.md`。

### 2026-06-14 —— Auto Memory 配置指南（Claude Code, Opus 4.8）

- **[新增] `agent-rules/auto-memory-setup.md`** —— 补齐 [[auto-memory-boundary]] 缺的「怎么配」：三层启用开关（env / settings.json `autoMemoryEnabled` / `/memory`）、一事一文件 + MEMORY.md 索引、frontmatter 字段与 `metadata.type` 四取值、写入/召回/更新/删除触发、与共享 Wiki 的互斥分工。事实区分官方文档确证与【未找到官方来源】两档。同步登记进 `index.md` 第 2 层与 `agent-rules/README.md`（顺带补登原本漏登的 boundary 条目）。

### 2026-06-13 —— repo 治理伴随的 wiki 调整（Claude Code, Opus 4.8）

- **[新增] 领域 `finance/`** —— 金融领域，含 `README.md`（领域范围说明）+ 子领域 `precious-metals/`。同步登记进 `index.md` 与 `wiki-ingest-guide.md` 领域映射表（领域数 7 → 8）。
- **[迁移] `com/dsifo-threshold-logic.md` → `finance/precious-metals/sifo-threshold-logic.md`** —— 原 `com/` 目录命名无意义且领域归类错误。文件重命名为更清晰的 `sifo-threshold-logic`，frontmatter 升级为方案 Z 双字段（domain: finance）。`com/` 已删除。
- **[迁移+重写] `auto-memory-boundary.md` 入 `agent-rules/`** —— 原散落在顶层 `workflows/claude-code-rules/`，升级为正式规则页：补方案 Z frontmatter、去写死 Mac 路径、措辞从"三 Agent"扩为"所有 agent"。
- **[合并] `skill-registry.md` + `skill-catalog.md` → `skill-register.md`** —— 两文件内容重叠易失同步，合并为单一清单（对账 + 全量明细 + Self-Skill 区）。13 处反链已更新。
- **[重写] `index.md`** —— 从过期版（2026-05-21）重写为 8 领域三层索引，摘录各领域高频页，承诺"完整清单见各领域 README"，全部引用经校验零断链。
- **[修改] `wiki-ingest-guide.md`** —— 领域映射表新增 finance 行；去写死路径（详见根 CHANGELOG 的 G 步）。
- **[补登记] `index.md` engineering 摘录** —— 补 `url-fidelity`。

> 已知待下轮：`agent-rules/` 下 4 个 Hermes/finance 特用页 + `engineering/youtube-pipeline-genimages-template-issue` 归类待判；部分旧页 frontmatter 待升级方案 Z。见根 `CHANGELOG.md` 白名单「待下轮处理」。
