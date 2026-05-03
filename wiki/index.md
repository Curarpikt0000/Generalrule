# AI Agent 知识库 Wiki

> 本 Wiki 由 promote-lessons Workflow 自动维护。
> `general-global-rule.md` 中的详细内容均指向此处。
> 最后更新：待 Agent 自动填写

## 领域索引

| 领域 | 路径 | 内容范围 |
|---|---|---|
| LLM 调用 | [[llm/|llm]] | 模型调度、fallback、配额、提示词 |
| 前端 | [[frontend/|frontend]] | 渲染管道、剪贴板、DOM |
| 工程实践 | [[engineering/|engineering]] | Bug修复、架构决策、代码规范 |
| 爬虫 | [[crawler/|crawler]] | 反爬、数据清洗、平台适配 |
| 图像生成 | [[image-gen/|image-gen]] | Imagen3、提示词、风格约束 |
| 集成适配 | [[integrations/|integrations]] | Notion 格式转换、跨系统适配器模式 |

## 使用方式

- **Obsidian 打开**：File → Open Vault → 选择 `wiki/` 目录
- **AI Agent 读取**：通过 promote-lessons Workflow 自动写入，通过 plan-task 自动查询
- **Quartz 发布**（可选）：见 SETUP.md（暂未建立）

## 元数据约定

每个知识页面顶部应包含：

- 来源 lesson ID
- 创建日期
- 适用领域
- 关键词（便于 grep 和 Obsidian 搜索）
