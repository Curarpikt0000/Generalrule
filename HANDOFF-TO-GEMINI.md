# Handover：Gemini 负责在 GCP 上部署 Hermes AI Agent

> 本文档是给 Gemini CLI 的完整任务简报。
> 目标：在 GCP 上部署一个生产级 Hermes AI Agent，并集成到现有的 Generalrule 知识库体系。
> 优先级：今天完成部署。
> 创建日期：2026-04-27

---

## 第 0 章：在开始之前必须读的东西

**在你做任何事之前，先读这两个文件**：

```bash
cat "/Users/chaojin/Antigravity Projects/Generalrule/antigravity/general-global-rule.md"
cat "/Users/chaojin/Antigravity Projects/Generalrule/wiki/engineering/harness-engineering-principles.md"
```

这两个文件定义了你必须遵守的行为规范和工程原则。特别注意：

- §4.10 Reflexion Loop：报错先自治修复 3 次，不要立刻停下问用户
- §4.8 最小破坏原则：一次只改一个点，不要大范围重构
- §5.6 Git 安全快照：每次任务开始前建 checkpoint
- §4.5 Source Trace：所有工具调用必须展示真实返回，禁止编造数据

---

## 第 1 章：现有体系概览

### 1.1 规则体系根目录

```
/Users/chaojin/Antigravity Projects/Generalrule/
├── antigravity/
│   ├── general-global-rule.md        # 全局行为规范（354 行）
│   └── workflows/                    # 8 个强制 Workflow
│       ├── plan-task.md
│       ├── verify-done.md
│       ├── find-skill-first.md
│       ├── promote-lessons.md
│       ├── self-correct.md           # Reflexion Loop
│       ├── rollback.md               # Git 逃生舱
│       ├── critic-review.md          # Producer-Critic-Judge
│       └── context-checkpoint.md    # 防 context rot
├── wiki/                             # Obsidian Vault（知识库）
│   ├── index.md
│   ├── llm/
│   ├── frontend/
│   ├── engineering/
│   │   └── harness-engineering-principles.md  # 理论基石
│   ├── crawler/
│   └── image-gen/
└── _template/                        # 新项目模板
    ├── AGENTS.md
    └── tasks/{todo.md, lessons.md}
```

### 1.2 八个强制 Workflow

| Workflow | 作用 | 触发时机 |
|---|---|---|
| `/plan-task` | 任务规划（含 Git checkpoint、Wiki 查询） | 任何编码任务开始时 |
| `/verify-done` | 完成前验证（含 TDD 检查、Reflexion 失败处理） | 宣称完成前 |
| `/find-skill-first` | 三层漏斗搜索现有 Skill/开源库 | 开发新功能前 |
| `/promote-lessons` | 扫描 lesson 升级到 Wiki / Skill / 全局规则 | verify-done 完成后自动触发 |
| `/self-correct` | Reflexion Loop（MAX_ITERATIONS=3，含 Anti-drift 检测） | verify-done 第 1-4 步失败时自动触发 |
| `/rollback` | Git 回滚逃生舱，回到 plan-task checkpoint | self-correct 用尽 + 用户选择回滚 |
| `/critic-review` | Producer-Critic-Judge 三角架构评审 | Complex 档任务或核心架构决策 |
| `/context-checkpoint` | 长会话清场，防止 context rot | Complex 任务完成后或会话超 2 小时 |

### 1.3 Wiki 知识库

路径：`/Users/chaojin/Antigravity Projects/Generalrule/wiki/`

这是一个 **Obsidian Vault 兼容的 Markdown 知识库**，三个工具（Antigravity / Claude Code / Gemini CLI）共享读取。

**你部署 Hermes 的过程中学到的任何经验，都要通过 `/promote-lessons` 写入这个 Wiki**，不要新建独立知识库。

如果需要新领域（比如 `gcp/`、`hermes/`），先在 `wiki/` 下创建子目录，同时更新 `wiki/index.md` 的索引表格。

### 1.4 Harness Engineering 2026 理论基石

基于以下行业研究（2026 年 Q1）：

- Martin Fowler：Harness Engineering（2026-02）
- LangChain 实验：只改 Harness，benchmark 52.8% → 66.5%
- Adnan Masood：65% 企业 AI 失败源于 Harness 缺陷
- Multi-agent 编排规范：Producer-Critic-Judge 五角色模式

核心理论文档：`wiki/engineering/harness-engineering-principles.md`

---

## 第 2 章：Hermes Agent 部署任务

### 2.1 任务目标

在 GCP 上部署一个生产级 Hermes AI Agent，满足以下条件：

- [ ] Hermes 的 Wiki 知识库指向现有的 `wiki/` 目录（不另建）
- [ ] 部署到 GCP（Cloud Run 优先，或 GKE 视情况而定）
- [ ] 今天完成，能跑通基本的 Ingest / Query / Lint 流程
- [ ] 接入现有的 Generalrule 体系（遵守 general-global-rule.md）

### 2.2 技术栈参考

根据现有项目（AI_Blog_Generator 等）的技术栈：

- **后端**：Python 3.11 + FastAPI + Pydantic
- **部署**：Cloud Run（`uvicorn` 挂载，异步/同步混合接口）
- **LLM**：Vertex AI（Pro 级主力）→ AI Studio（备用兜底）
- **配置**：所有密钥从环境变量 / `.env` 读取，严禁硬编码

### 2.3 Hermes 知识库配置要求

Hermes 基于 `llm-wiki-skill`，配置时必须指向现有 Wiki：

```yaml
# ~/.claude/skills/llm-wiki/config.md 或对应配置文件
wiki_directory: /Users/chaojin/Antigravity Projects/Generalrule/wiki
source_directories:
  - /Users/chaojin/Antigravity Projects/
```

**验证方法**：配置完后在 Claude Code 里运行 `/llm-wiki`，应识别到 5 个现有领域（llm / frontend / engineering / crawler / image-gen）。

### 2.4 Wiki 扩展规则

如果 Hermes 需要新领域（`gcp/`、`hermes/`），必须同时做三件事：

1. 在 `wiki/` 下创建新目录 + `README.md`
2. 在 `wiki/index.md` 的领域索引表格添加新行
3. 在 `promote-lessons.md` 的"关键词命中"表格添加新领域的关键词

**不要**在 `wiki/` 之外建平行知识库。

---

## 第 3 章：GCP 部署 SOP

### 3.1 部署前检查

```bash
# 1. 确认 GCP 环境
gcloud auth list
gcloud config get-value project

# 2. 确认所需 API 已启用
gcloud services list --enabled | grep -E "run|build|artifactregistry"

# 3. 确认本地代码干净
git status
```

### 3.2 Cloud Run 部署流程

**参考现有项目的部署方式**（AI_Blog_Generator 等）：

```bash
# Step 1: 构建镜像
gcloud builds submit --tag gcr.io//hermes-agent:latest .

# Step 2: 部署到 Cloud Run
gcloud run deploy hermes-agent \
  --image gcr.io//hermes-agent:latest \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated \
  --set-env-vars="WIKI_PATH=/app/wiki" \
  --memory=2Gi \
  --cpu=2

# Step 3: 验证部署
gcloud run services describe hermes-agent --region asia-east1
curl https:///health
```

### 3.3 环境变量清单（必须配置）

```bash
# GCP / Vertex AI
GOOGLE_CLOUD_PROJECT=
VERTEX_AI_LOCATION=asia-east1

# LLM 备用（AI Studio）
GOOGLE_AI_API_KEY=

# Wiki 路径（容器内）
WIKI_PATH=/app/wiki

# Hermes 配置
HERMES_PORT=8080
HERMES_LOG_LEVEL=INFO
```

### 3.4 Dockerfile 注意事项

```dockerfile
# 必须复制 wiki/ 目录到容器
COPY wiki/ /app/wiki/

# 或者通过 GCS bucket mount（推荐，可热更新）
# 见 3.5 GCS Mount 方案
```

### 3.5 Wiki 热更新方案（推荐）

Wiki 内容会被 `promote-lessons` 持续更新。避免每次更新都要重新部署 Cloud Run，建议：

```bash
# 1. 创建 GCS bucket 存 Wiki
gsutil mb gs://-hermes-wiki
gsutil -m rsync -r "/Users/chaojin/Antigravity Projects/Generalrule/wiki/" gs://-hermes-wiki/

# 2. Cloud Run 挂载 GCS（需要 Cloud Storage FUSE）
# 在 cloud run yaml 里配置 volumes

# 3. 每次 promote-lessons 完成后同步 Wiki 到 GCS
gsutil -m rsync -r "/Users/chaojin/Antigravity Projects/Generalrule/wiki/" gs://-hermes-wiki/
```

---

## 第 4 章：今天的完成标准

按优先级排序。**P0 必须今天完成**，P1/P2 可以后续迭代：

### P0（今天必须完成）

- [ ] Hermes Agent 跑通，能响应 `/health` 接口
- [ ] `/llm-wiki ingest` 能把内容写入 `wiki/` 目录
- [ ] `/llm-wiki query <问题>` 能返回有意义的答案
- [ ] 部署到 Cloud Run，有公开访问 URL
- [ ] Wiki 知识库正确指向 `Generalrule/wiki/`，不是新建的

### P1（本周完成）

- [ ] GCS bucket 挂载，Wiki 热更新无需重新部署
- [ ] `/llm-wiki lint` 能检测孤立页面和矛盾
- [ ] 双语支持（中英文）
- [ ] Cloud Run 自动缩容到 0（节省费用）

### P2（以后迭代）

- [ ] Quartz 发布为静态网站（GitHub Pages）
- [ ] Hermes Query 升级为 plan-task 第 2.5 步的后端
- [ ] 与 promote-lessons Workflow 的 API 集成

---

## 第 5 章：边界与禁区

### 5.1 不要碰的文件

- `general-global-rule.md`：所有修改必须走 `/promote-lessons` 流程
- `workflows/*.md`：这是跨工具共享协议，不能随意改
- `_template/`：项目模板，不能迁移到别处

### 5.2 不要新建的东西

- ❌ 不要新建 Hermes 专属知识库（用现有 `wiki/`）
- ❌ 不要修改 `wiki/index.md` 的顶层结构（只加行，不改列）
- ❌ 不要引入与现有 YAML frontmatter 不兼容的元数据字段

### 5.3 安全边界

- 所有 API Key 从环境变量读取，禁止硬编码（§8）
- Wiki 页面中不得包含密钥或用户隐私数据
- 外部抓取的内容必须标注来源 URL

---

## 第 6 章：遇到问题的处理方式

### 6.1 报错处理（Reflexion Loop）

遵守 §4.10：先自治修复 3 次，再求助用户。

每次 reflection 必须回答三个问题：
1. What failed?（具体引用报错关键行）
2. What change would fix it?（明确改哪个文件哪一行）
3. Am I repeating?（和上次尝试对比）

### 6.2 GCP 特有的常见坑

- **Cloud Run 冷启动超时**：设置 `--min-instances=1` 避免第一次请求超时
- **Vertex AI 429 配额**：启用级联回退（Vertex Pro → Vertex Flash → AI Studio），参考 §3.3
- **Cloud Build 内存不足**：在 `cloudbuild.yaml` 里加 `machineType: E2_HIGHCPU_8`
- **GCS 挂载权限**：Cloud Run 服务账号需要 `Storage Object Viewer` 权限
- **Wiki 路径在容器内的映射**：本地绝对路径 `/Users/chaojin/...` 在容器内无效，统一用相对路径或 `/app/wiki`

### 6.3 如何记录 GCP 部署经验

每次解决一个部署问题，在当前项目的 `tasks/lessons.md` 追加一条 lesson，格式遵守 §6.2。

标注 `适用范围: 全局` 的 lesson，后续会被 `/promote-lessons` 升级到：
- `wiki/engineering/` 或新建的 `wiki/gcp/`
- `general-global-rule.md` 的对应章节

---

## 第 7 章：快速开始命令

```bash
# 1. 克隆 llm-wiki-skill（如果还没装）
git clone https://github.com/kingqiu/llm-wiki-skill.git ~/.claude/skills/llm-wiki

# 2. 安装 Quartz（可选，用于发布）
git clone https://github.com/jackyzha0/quartz.git ~/wiki-quartz
cd ~/wiki-quartz && npm install
rm -rf ~/wiki-quartz/content
ln -s "/Users/chaojin/Antigravity Projects/Generalrule/wiki" ~/wiki-quartz/content

# 3. 验证 Wiki 指向正确
ls "/Users/chaojin/Antigravity Projects/Generalrule/wiki/"
# 应该看到：crawler/ engineering/ frontend/ image-gen/ index.md llm/

# 4. 初始化项目 tasks 目录
DEST=""
mkdir -p "$DEST/tasks"
cp "/Users/chaojin/Antigravity Projects/Generalrule/_template/tasks/todo.md" "$DEST/tasks/"
cp "/Users/chaojin/Antigravity Projects/Generalrule/_template/tasks/lessons.md" "$DEST/tasks/"
cp "/Users/chaojin/Antigravity Projects/Generalrule/_template/AGENTS.md" "$DEST/AGENTS.md"

# 5. 开始部署（调用 plan-task 规划）
# /plan-task 在 GCP 上部署 Hermes Agent，要求今天完成
```

---

## 第 8 章：集成验证标准

部署完成后，以下三件事能同时满足，说明集成成功：

- ✅ `curl https://<SERVICE_URL>/health` 返回 200
- ✅ `/llm-wiki query "什么是级联 fallback？"` 能返回相关知识（读的是 `wiki/llm/` 下的内容）
- ✅ 在 Antigravity 里跑 `/promote-lessons`，升级新 lesson 到 Wiki，Hermes Query 能立刻查到新页面
- ✅ 在 Obsidian 里打开 `wiki/` Vault，看到 Hermes 部署过程中新增的页面

---

## 附录：关键路径速查

```
全局规则：
/Users/chaojin/Antigravity Projects/Generalrule/antigravity/general-global-rule.md

Workflow 目录：
/Users/chaojin/Antigravity Projects/Generalrule/antigravity/workflows/

Wiki 知识库：
/Users/chaojin/Antigravity Projects/Generalrule/wiki/

理论基石：
/Users/chaojin/Antigravity Projects/Generalrule/wiki/engineering/harness-engineering-principles.md

项目模板：
/Users/chaojin/Antigravity Projects/Generalrule/_template/

Gemini CLI 全局规则（符号链接）：
~/.gemini/GEMINI.md → general-global-rule.md

Claude Code 全局规则（符号链接）：
~/.claude/CLAUDE.md → general-global-rule.md
```

---

**End of Handoff Document**

> 记住：你今天的任务是部署完成，让 Hermes 在 GCP 上跑起来。
> 遇到问题先走 Reflexion Loop，3 次解决不了再问用户。
> 每次解决一个 GCP 坑，写一条 lesson，这是给未来的你最好的礼物。
