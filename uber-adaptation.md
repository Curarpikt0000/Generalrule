# Uber 环境适配层（仅 Uber 电脑，存在于 ub-branch，不进 main）

> 叠加在共享 general-global-rule.md 之上。general rule（认知纪律/五阶段/Lesson）原样遵守，本文件只补 Uber 环境差异。

## 开工同步纪律（本机日常在 ub-branch）
- 本机日常 checkout `ub-branch`（= main 全部内容 + 本文件）。
- 开工前：`git fetch origin && git merge origin/main && git pull origin ub-branch`。
- 通用认知纪律 / 通用 Wiki 知识 → 切到 main 提交并 push，再切回 ub-branch merge main。
- 本文件（Uber 适配）改动 → 直接在 ub-branch commit + push。

## 工具替换映射（Uber 机器上，重复就用公司的）
- superpowers → Uber 原生 uberpowers（aifx plugin add uberpowers）
- RTK token 压缩 → code-mode（aifx plugin add code-mode）
- skill-creator → skill-workshop
- MCP → omni-mcp（一个连接通 415+ servers）
- find-skills → 装 find-skills，装新 skill 前先查重
- 没有 Uber 等价物的（如写个人 GitHub wiki 的 wiki-update）→ 用个人的 / 手动按 wiki-ingest-guide

## 双 GitHub 分流（各干各的，不混）
- 个人仓库 Curarpikt0000/Generalrule：只放 general rule / workflow / wiki 总结
  - 通用认知纪律、通用 wiki → push main
  - Uber 适配（本文件）→ push ub-branch
- 公司 GitHub（chao.jin@uber.com）：所有 Uber 项目代码，完全独立
- Antigravity 在本机产出的 Uber 项目代码 → 公司 GitHub（各项目目录单独 `git config user.email "chao.jin@uber.com"`）或本地存放；绝不进个人仓库

## 红线（Uber IP 保护，最重要）
- 个人仓库**绝不放 Uber 代码、内部数据、Uber 专有流程**（内部工具/skill 名称除外，用户已批准）。
- 写个人 wiki 前自问：这条脱离 Uber 也成立吗？不成立 → 不进个人仓库。
- Uber 项目代码一律 push 公司 GitHub。

## 认知纪律 / 五阶段 workflow / Lesson
→ 完全遵守 main 上的 general-global-rule.md，与家里一致。

## VM 工作区目录纪律（devpod）
- 工作区根（如 `~/claudecodeuber/`）只放：根入口 `CLAUDE.md` + 各任务文件夹，**不放散文件**。
- 命名：正式项目 `project-<名>/`；临时对话/实验 `temp-<日期>-<主题>/`；数据分析 `data-analysis/<主题>/`。
- 新任务第一步先建文件夹再动手（呼应 general rule §5）；项目内部结构按 `wiki/agent-rules/project-template.md`。
- Generalrule 仓库在 VM 上**独立 clone**（checkout ub-branch），与本地 Mac 互不依赖，经 GitHub 同步。
