---
# LLM Wiki 配置模板（通用版，无写死路径）
# 复制为 config.md 后填本机实际值。config.md 已被 .gitignore 排除。
configured: true
---

# LLM Wiki 配置文件

本 skill 适配「general rule + Generalrule 共享 wiki」体系：
纯 markdown + Obsidian、领域目录、方案Z双字段 frontmatter、双 GitHub 分流、IP 红线。
无 Quartz、无双语翻译、无 GitHub Pages。

> **不要在本文件写死任何机器绝对路径。** 下列值由各 agent 在自己机器上按实际 clone 位置填写；
> 留空时 skill 在 Phase 0 自解析（见 SKILL.md）。

## Repo Root
# 本机 clone 的 Generalrule 仓库根。留空则 skill 自动探测（入口 CLAUDE.md/AGENTS.md 指针 / 询问用户）。
# 例（仅示意，按本机填）：<本机 Generalrule 仓库根>

## Wiki Directory
# = {Repo Root}/wiki。留空则由 Repo Root 推导。

## Wiki Repo
# = 该仓库 git remote origin。留空则 `git -C {Repo Root} remote get-url origin` 自取。

## Source Directories
# 可选。批量 ingest 时扫描的本地原始资料目录（只读，绝不修改）。没有就留空。
# - <本机某原始笔记目录>

## Git Branch Policy
# 体系约定（对所有 agent 通用，分支名固定）：
# - personal_branch = 私人机所有 agent 的核心分支
# - uber_branch     = Uber Mac/VM 所有 agent 的分支（核心分支的超集，多 Uber 专属内容）
# 当前机用哪个分支：按本机 clone 当前分支判定（git branch --show-current）。
personal_branch: main
uber_branch: ub-branch

## Language
# 用户可见沟通 + wiki 正文：中文简体。代码标识符保持英文。
language: zh-CN
