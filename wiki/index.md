# AI Agent 知识库 Wiki

> 本 Wiki 是本体系所有 agent 共享的知识库，由 lesson/ingest 流程维护（优先用 llm-wiki skill，见 [[wiki-ingest-guide]]）。
> `general-global-rule.md` 中的详细内容均指向此处。
> 知识增删改的版本记录见 `wiki/CHANGELOG.md`。
> 最后更新：2026-06-13

## 第 1 层 · 领域索引

| 领域 | 路径 | 内容范围 |
|---|---|---|
| LLM 调用 | [[llm/\|llm]] | 模型调度、fallback、配额、提示词 |
| 前端 | [[frontend/\|frontend]] | 渲染管道、剪贴板、DOM、表单、缓存 |
| 工程实践 | [[engineering/\|engineering]] | Bug 修复、架构决策、代码规范、部署、权限 |
|| 爬虫 | [[crawler/\\|crawler]] | 反爬、数据清洗、平台适配、分页、WAF 绕过 |
| 图像生成 | [[image-gen/\|image-gen]] | Imagen3、提示词、风格约束 |
| 设计模式 | [[design-patterns/\|design-patterns]] | 级联降级、对抗性系统、自适应架构 |
| 金融 | [[finance/\|finance]] | 市场结构、指标解读、风险信号（下设 precious-metals 等子领域） |
| Agent 规则 | [[agent-rules/\|agent-rules]] | 本体系自身规则：五步链路、wiki 写作、skill 对账、代码规范等 |

> 三层索引约定（见 [[wiki-ingest-guide]] 第二节）：本页 = 第 1 层只列领域；各领域页清单见各领域 `README.md`（第 2 层）；单页为第 3 层。

## 第 2 层 · 各领域明细（高频页摘录，完整清单见各领域 README）

### agent-rules（本体系规则）

| 页面 | 链接 | 用途 |
|---|---|---|
| 五步链路 + 五阶段 workflow | [[agent-rules/five-step-pipeline\|five-step-pipeline]] | 任务执行 SOP |
| Wiki 写作规范 | [[agent-rules/wiki-ingest-guide\|wiki-ingest-guide]] | 知识库读写真源 |
| Skill 与 MCP 总清单 | [[agent-rules/skill-register\|skill-register]] | 对账 + 各环境全量明细 + self-skill |
| Agent 配置自述矩阵 | [[agent-rules/agent-config-matrix\|agent-config-matrix]] | 各 agent 入口/人格/记忆/workflow 自述 |
| 项目标准结构 | [[agent-rules/project-template\|project-template]] | 新项目初始化 |
| Python 代码规范 | [[agent-rules/python-coding\|python-coding]] | 注释 / docstring |
| LLM 调度规范 | [[agent-rules/llm-orchestration\|llm-orchestration]] | 模型 fallback / 配额 |
| 前端渲染规范 | [[agent-rules/frontend-rendering\|frontend-rendering]] | 渲染 / Markdown / 剪贴板 |
| RTK Token 优化 | [[agent-rules/rtk-usage\|rtk-usage]] | terminal token 压缩 |
| Auto Memory 边界 | [[agent-rules/auto-memory-boundary\|auto-memory-boundary]] | Claude Code 私有笔记 vs 共享 wiki |
| Auto Memory 配置 | [[agent-rules/auto-memory-setup\|auto-memory-setup]] | 启用开关 / 存储 / frontmatter / 触发 |
| AGENTS 模板 | [[agent-rules/AGENTS-template\|AGENTS-template]] | 项目入口模板 |

### finance（金融）

| 页面 | 链接 | 关键词 |
|---|---|---|
| SIFO §8.5 阈值表 · ΔS 方向前置判断 | [[finance/precious-metals/sifo-threshold-logic\|sifo-threshold-logic]] | sifo, q_phy, ΔS, backwardation, contango, 贵金属 |

### frontend（前端）

| 页面 | 链接 | 关键词 |
|---|---|---|
| 静态网页表单邮件发送 | [[frontend/static-site-form-email]] | FormSubmit, 表单, 邮件 |
| 浏览器缓存与 Cache Buster | [[frontend/cache-buster-versioning]] | Cache Buster, 版本号, 缓存 |

### crawler（爬虫）

| 页面 | 链接 | 关键词 |
|---|---|---|
| 反爬虫绕过手册 | [[crawler/crawler-bypass-handbook]] | bypass, waf, camoufox, crawl4ai, jina-reader |
| 后端 API 发现绕过 WAF | [[crawler/bypass-waf-via-backend-api-discovery]] | waf, backend-api, 接口发现 |
| YouTube 客户端伪装绕过 | [[crawler/yt-dlp-client-spoofing]] | youtube, yt-dlp, tv_embedded, bypass |
| 采集保持原文语言 | [[crawler/preserve-original-language]] | transcript, language, data-integrity |
| 周报分页与数据遗漏防范 | [[crawler/weekly-report-pagination]] | pagination, weekly-report, backfill |
| SHFE WAF 绕过 — Playwright stealth 方案 | [[crawler/shfe-waf-bypass]] | shfe, waf, playwright, stealth, js-challenge |

### engineering（工程实践）

| 页面 | 链接 | 关键词 |
|---|---|---|
| Agent 去重双保险 | [[engineering/agent-dedup-double-insurance]] | dedup, idempotency, 双保险 |
| GCP Cloud Run 部署 | [[engineering/gcp-cloud-run-deployment]] | gcp, cloud-run, 部署 |
| GCP IAM 运行时权限 | [[engineering/gcp-iam-runtime-permissions]] | gcp, iam, 权限 |
| GitHub Actions 限流防护 | [[engineering/github-actions-rate-limit-mitigation]] | github-actions, rate-limit, secrets |
| Google AntiGravity IDE | [[engineering/google-antigravity]] | 工具对比, IDE |
| Notion 去重 Fail Loud | [[engineering/notion-dedup-fail-loud]] | notion, dedup, fail-loud |
| Notion 分页校验 | [[engineering/notion-pagination-validation]] | notion, pagination, has_more |
| pathlib vs os.path | [[engineering/pathlib-vs-ospath]] | pathlib, 跨平台路径 |
| URL 保真度协议 | [[engineering/url-fidelity]] | url, user-intent, 严格使用用户URL |
| 编码前先查 skill | [[engineering/skill-check-before-coding]] | skill, 五步链路 |
| 容器重启服务恢复与开机持久化 | [[engineering/container-reboot-service-persistence]] | 容器, 重启, 临时/etc, 幂等 boot, setsid, watchdog |
| 轮询式双向 bot + 单源硬超时隔离 | [[engineering/polling-bidirectional-bot-and-source-timeout-isolation]] | 轮询, 双向 bot, 游标, ThreadPoolExecutor 硬超时, shutdown(wait=False), os._exit, 多源管道 |
| 首次构建 RAG 问答 Chatbot 的工程踩坑 | [[engineering/rag-chatbot-first-build-pitfalls]] | chatbot, RAG, 自回复死循环, 共享账号, 缓存丢来源/TTL, 纯逻辑单测, state 原子写 |
| Notion API Token — ntn_ 格式与 shell 截断陷阱 | [[engineering/notion-api-token-ntn-trap]] | notion, api-token, shell, 截断 |
| Cron Job — GUI 方案不可靠，优先 no_agent 纯脚本 | [[engineering/cron-no-gui-preference]] | cron, computer_use, no_agent, playwright |

### llm（LLM 调用）

| 页面 | 链接 | 关键词 |
|---|---|---|
| 级联 fallback | [[llm/fallback]] | fallback, 多模型, 配额 |
| 云端测试 | [[llm/cloud_test]] | 测试, 云端 |
| 工具调用泄漏成文本 | [[llm/tool-call-emitted-as-text]] | antml, invoke, tool_calls, 上下文污染, tool_search |

### design-patterns（设计模式）

| 页面 | 链接 | 关键词 |
|---|---|---|
| 级联降级 | [[design-patterns/cascade-fallback]] | 级联, 降级, fallback |
| LLM 原生 skill 集成 | [[design-patterns/llm-native-skill-integration]] | skill, 集成, 架构 |

### image-gen（图像生成）

> 见 [[image-gen/README]]。

## 使用方式

- **Obsidian 打开**：File → Open Vault → 选择 `wiki/` 目录
- **AI Agent 读取**：先读本页找领域 → 进领域 README 找页 → 读具体页（[[wiki-ingest-guide]] 第三节）
- **写入**：优先调用 llm-wiki skill，按 [[wiki-ingest-guide]] 规范；增删改后更新 `wiki/CHANGELOG.md`

## 元数据约定

每个知识页面顶部包含方案 Z 双字段 frontmatter（title / domain / type / keywords / tags / source / sources / created / updated / last_updated），详见 [[wiki-ingest-guide]] 第二节。
