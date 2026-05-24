# General Global Rule（精简版，完整版见文件）

> 完整规则：/Users/chaojin/Antigravity Projects/Generalrule/antigravity/general-global-rule.md
Wiki：/Users/chaojin/Antigravity Projects/Generalrule/wiki/
> 

---

## §1 语言

所有回复、解释、建议均使用**中文简体**。代码注释中文，变量名英文。

## §4 核心工作习惯

- 修改前先说明思路，等用户确认再动手
- 一次改动不超过 5 个文件
- 发现问题指出但不自动修改
- 非平凡修改前自问："有没有更优雅的方案？"

## §5 Workflow 强制触发（八个）

- `/plan-task`：任何编码任务开始前
- `/find-skill-first`：开发新功能前
- `/verify-done`：宣称完成前
- `/promote-lessons`：verify 完成后
- `/self-correct`：verify 失败时（MAX=3）
- `/rollback`：self-correct 用尽时
- `/critic-review`：Complex 任务时
- `/context-checkpoint`：Complex 任务完成后

Workflow 文件：/Users/chaojin/Antigravity Projects/Generalrule/antigravity/workflows/

## §6 Lessons 系统

用户纠正时立刻写入 tasks/lessons.md 顶部，回复末尾声明：已记录 lesson L-xxx

## §10 Wiki 知识库

路径：/Users/chaojin/Antigravity Projects/Generalrule/wiki/

**必须先查 Wiki**：debug / 复杂技术问题 / GCP、Notion、YouTube、LLM、爬虫

**必须写 Wiki**：用户纠正后 / 公网有价值方案 / 解决复杂 bug

写完：更新 [index.md](http://index.md/) + git push

## §11 新建 Skill

需要创建新 Skill 时必须先读：
/Users/chaojin/Antigravity Projects/Generalrule/antigravity/general-global-rule.md §11
## Global Skills

### requesting-code-review
**位置**：`~/.claude/skills/requesting-code-review/SKILL.md`

修改代码后必须触发的审查流程。dispatch 一个独立的 code-reviewer 子 agent，用精准的 git SHA 范围和需求描述作为上下文，把反馈分为 Critical / Important / Minor 三级。

**触发时机**：修改任何核心服务文件后、部署前、完成重大功能后。

@RTK.md

## §12 RTK 自动优化

所有 terminal 命令优先用 `rtk` 代理形式执行以压缩输出：

| 原始命令 | RTK 替代 |
|---|---|
| `ls` | `rtk ls` |
| `cat file` | `rtk read file` |
| `curl url` | `rtk curl url` |
| `git ...` | `rtk git ...` |
| `grep ...` | `rtk grep ...` |
| `ls -la dir` | `rtk ls -la dir` |

**例外**：`rtk` 自身命令（`rtk init`、`rtk gain`、`rtk --version` 等）不加递归。

**图片分析 fallback**：当前 DeepSeek provider 不支持 vision，收到图片时先用 `tesseract <path> stdout` OCR 提取文字，或尝试通过 Gemini/Claude API 分析。不问用户「这是什么」。

**状态**：RTK v0.40.0 已安装 (`/opt/homebrew/Cellar/rtk/0.40.0`)，`rtk init -g` 已完成。
