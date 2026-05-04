# AI Agent 知识库 Wiki

> 本 Wiki 由 promote-lessons Workflow 自动维护。
> `general-global-rule.md` 中的详细内容均指向此处。
> 最后更新：2026-05-01

## 领域索引

| 领域 | 路径 | 内容范围 |
|---|---|---|
| LLM 调用 | [[llm/\|llm]] | 模型调度、fallback、配额、提示词 |
| 前端 | [[frontend/\|frontend]] | 渲染管道、剪贴板、DOM |
| 工程实践 | [[engineering/\|engineering]] | Bug修复、架构决策、代码规范 |
| 爬虫 | [[crawler/\|crawler]] | 反爬、数据清洗、平台适配 |
| 图像生成 | [[image-gen/\|image-gen]] | Imagen3、提示词、风格约束 |

## 使用方式

- **Obsidian 打开**：File → Open Vault → 选择 `wiki/` 目录
- **AI Agent 读取**：通过 promote-lessons Workflow 自动写入，通过 plan-task 自动查询

## 元数据约定

每个知识页面顶部应包含：来源 lesson ID、创建日期、适用领域、关键词。

---

## LLM 领域明细

| 规则标题 | 链接 | 关键词 | 创建日期 |
|---|---|---|---|
| LLM 级联熔断机制 | [[llm/fallback]] | fallback, 429, 配额 | 2026-04-30 |
| Vertex 模型发现陷阱 | [[llm/vertex-model-discovery-pitfall]] | model_discovery, 404, gemini-2.5 | 2026-05-01 |
| LLM 幻觉防护 | [[llm/hallucination-prevention]] | 幻觉, 空素材, 内容校验 | 2026-05-01 |

## 工程实践领域明细

| 规则标题 | 链接 | 关键词 | 创建日期 |
|---|---|---|---|
| Cloud Run 部署规范 | [[engineering/gcp-cloud-run-deployment]] | Cloud Run, Dockerfile | 2026-04-30 |
| GCP IAM 运行时权限 | [[engineering/gcp-iam-runtime-permissions]] | IAM, Service Account | 2026-04-30 |
| Cloud Run Revision 验证 | [[engineering/cloud-run-revision-verification]] | revision, 流量回退 | 2026-05-01 |
| Producer-Critic 调试模式 | [[engineering/producer-critic-pattern]] | Context Bias, Critic | 2026-05-01 |

## 爬虫领域明细

| 规则标题 | 链接 | 关键词 | 创建日期 |
|---|---|---|---|
| YouTube GCP IP 封锁 | [[crawler/youtube-gcp-ip-block]] | YouTube, IP封锁, Jina AI | 2026-05-01 |

## 图像生成领域明细

| 规则标题 | 链接 | 关键词 | 创建日期 |
|---|---|---|---|
| Imagen 3 必须 vertexai.init | [[image-gen/vertex-init-required]] | Imagen3, us-central1 | 2026-05-01 |
| Imagen 3 直接用稳定 ID | [[image-gen/imagen3-direct-model-id]] | 动态发现, 静默失败 | 2026-05-01 |
