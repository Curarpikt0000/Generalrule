# llm-wiki（Generalrule 适配版）

在本机 clone 的 **Generalrule 仓库 `wiki/`** 上做知识复利累积。三模式：
- **Ingest** —— 把新知识提炼成结构化页面写入对应领域。
- **Query** —— 基于 wiki 回答，并按阈值自动增强（补交叉引用 / 记知识空白 / 建综合页）。
- **Lint+Heal** —— 健康检查（断链/孤立页/缺概念/矛盾/frontmatter）+ 修复。

## 与原版的差异（为什么改）

本版改造自公网 `kingqiu/llm-wiki-skill`，为适配本体系做了**深改**：
- ❌ 移除 Quartz 静态站引擎 → ✅ 纯 markdown + Obsidian（本体系 wiki 形态）
- ❌ 移除强制双语 + GLM 翻译 API → ✅ 中文为主
- ❌ 移除 GitHub Pages 同步
- ✅ 领域目录 + 方案Z双字段 frontmatter + 三层索引（见 `wiki-ingest-guide.md`）
- ✅ 双 GitHub 分流（personal/uber 两 branch）+ IP 红线门
- ✅ **不写死机器路径**：Phase 0 自解析 REPO_ROOT

## 用法

各 agent 取用时：把本目录拷到自己的 skill 目录，复制 `config.example.md` 为 `config.md` 并按本机填值（或留空让 skill 自解析）。详见 `SKILL.md` 的 Phase 0。

> 规则真源是 `wiki/agent-rules/wiki-ingest-guide.md`；本 skill 是它的执行器，冲突以真源为准。

## 准入与登记

本 skill 属于 `self-skill/` 通用收纳处，准入与登记规则见上级 `self-skill/README.md`。
