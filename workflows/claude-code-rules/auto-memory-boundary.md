# Auto Memory 边界规则（仅 Claude Code）

> Auto Memory 是 Claude Code 私有的自动笔记，Hermes 和 Antigravity 没有它。
> 因此 Auto Memory 只能记"Claude Code 本地琐事"，绝不能记"该三 Agent 共享的知识"。

## 可以记（Claude Code 私有）
- 本机操作偏好、Claude Code 专属使用习惯
- 当前项目的临时状态（进行到哪、下一步）
- 纯属本地、不值得全局共享的细节

## 禁止记（这些走共享 Wiki，不进 Auto Memory）
- 值得三 Agent 共享的纠正、规则、方法论 → 走 llmwiki-ingest 写入共享 Wiki
  （/Users/chaojin/Antigravity Projects/Generalrule/wiki/）
- general rule 已有的内容（避免重复）
- 代码结构、文件路径（直接读项目）
- git 历史（git log 更准）
- 调试步骤（修复已在代码里）

## 判断标准（每次要记前自问）
被用户纠正或学到新知识时，先问：**这值得 Hermes 和 Antigravity 也知道吗？**
- 值得 → 走 Wiki ingest（general rule §6 / wiki-ingest-guide）
- 仅 Claude Code 本地有用 → 才记进 Auto Memory
