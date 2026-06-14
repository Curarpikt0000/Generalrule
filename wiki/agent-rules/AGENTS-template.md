---
title: AGENTS.md 项目入口模板（多 Agent 通用）
domain: agent-rules
type: source
keywords: [agents.md, 项目入口, 模板, claude.md, 多agent通用]
tags: [agents-md, template, project-entry]
source: 架构设计 2026-05-24
sources: [conversation-2026-05-24]
created: 2026-05-24
updated: 2026-05-24
last_updated: 2026-05-24
---

# AGENTS.md 项目入口模板（多 Agent 通用）

> 这是每个新项目的入口文件模板。Claude Code / Hermes / Antigravity / Codex / Cursor 等所有 Agent 都读 `AGENTS.md`。
> 初始化新项目时，把下方"模板正文"复制成项目根目录的 `AGENTS.md`，填好方括号部分。
> Claude Code 偏好 `CLAUDE.md`，用符号链接解决：`ln -s AGENTS.md CLAUDE.md`。
> 本文件薄——只写项目特有内容；通用规则在全局 general rule 和 Wiki。

---

## 使用方法

1. 新项目初始化时（按 [[project-template]]），复制下方"模板正文"到 `项目根/AGENTS.md`。
2. 填写所有 `[方括号]` 部分。
3. 建符号链接：`cd 项目名 && ln -s AGENTS.md CLAUDE.md`。
4. 空小节先留着，随项目成长补充。

---

## 模板正文（复制以下全部）

```markdown
# [项目名]

> 本项目遵守全局规则：见 Generalrule 仓库 `antigravity/general-global-rule.md`（本机 clone 路径自行定位）。
> 通用规范与踩坑教训见 Generalrule 仓库 `wiki/`。
> 本文件只写本项目特有的内容。做项目的步骤、认知纪律、五阶段 workflow 在全局规则里，这里不重复。

## 项目简介

[一两句话：这个项目做什么，解决什么问题]

## 技术栈

- 语言/框架：[如 Python 3.12 / FastAPI / Next.js]
- 关键依赖：[如 ...]
- 部署：[如 本地 / GCP Cloud Run / Vercel]

## 目录约定

- 前端代码：[如 src/frontend/]
- 后端代码：[如 src/api/]
- 临时文件：scratch/（不进 git，一次性产物都放这）
- 配置：[如 config.py，严禁硬编码密钥，密钥进 .env]

## 常用命令

- 启动：[如 python main.py / pnpm dev]
- 测试：[如 pytest / pnpm test]
- 部署：[如 gcloud run deploy --source .]
- 其他：[如 数据库迁移、构建等]

## 工作规则（本项目特有）

[只写和全局规则不同的、本项目独有的约定。没有就留空，遵守全局规则即可。]
[例：本项目所有 Notion 写入必须走 markdown→blocks 转换器，禁止裸 markdown]

## 输出要求

[本项目对产物的特殊要求。]
[例：API 返回格式统一为 { code, data, message }]
[例：内容生成保持原文语言，禁止自动翻译]

## 禁止事项

[本项目绝对不能做的事。]
[例：不要碰 src/legacy/ 旧代码]
[例：不要把生成的视频/音频提交到 git，放 scratch/]
[例：不要修改线上数据库 Schema 而不先备份]

## 验收标准

[怎么算"做完了"——这是 §2.4 目标驱动执行的项目级落地。]
[例：所有测试通过 / 本地能启动且核心流程跑通 / 无硬编码密钥]

## 项目 Wiki

本项目的经验沉淀见 `wiki/README.md`，按领域分组逐层下钻。

> Wiki 读写规范（三层索引、kebab-case 命名、frontmatter 格式）遵守全局 `wiki/agent-rules/wiki-ingest-guide.md`。
> 沉淀新知识：写进项目 wiki 对应领域 → 更新该领域 README → 不要逐条往本文件加索引。
```

---

## 相关页面

- [[project-template]] —— 项目标准目录结构
- [[five-step-pipeline]] —— 做项目的执行流程
- general-global-rule.md §5（新项目初始化）
