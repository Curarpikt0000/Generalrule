# General Global Rule（精简版，完整版见文件）

> 完整规则：/Users/chaojin/Antigravity Projects/Generalrule/antigravity/general-global-rule.md
> Wiki：/Users/chaojin/Antigravity Projects/Generalrule/wiki/

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

写完：更新 index.md + git push

## §11 新建 Skill

需要创建新 Skill 时必须先读本段。

**强制规则**：任何时候需要创建新 Skill，必须使用 `skill-creator`（已安装至 `~/.agents/skills/skill-creator`）辅助完成整个创建流程：

1. **加载 skill-creator** → 自动引导需求分析
2. **草拟 Skill.md** → skill-creator 辅助编写测试用例
3. **运行评估** → 并行 With/Without skill 对比测试
4. **迭代优化** → 基于测试反馈改进，最多 5 轮
5. **描述优化** → 用 20 条触发/非触发查询测试描述准确性
6. **最终验证** → 确认通过率达标后保存

禁止手动裸写 Skill.md 跳过评估流程。