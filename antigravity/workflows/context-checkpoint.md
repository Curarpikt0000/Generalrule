# Workflow: /context-checkpoint

> 上下文清场 Workflow，由 `general-global-rule.md §4.11` 强制约束。
> 防止长会话中 agent 注意力衰退（context rot）。
> 用于 Complex 任务收尾或单次会话过长时主动清理。
> 最后更新：2026-04-27

---

## 触发条件

- 一次 **Complex** 档任务完成后**自动**触发
- 单次会话**超过 2 小时**或 agent 自我检测到上下文紧张
- 用户主动发 `/context-checkpoint`
- `/promote-lessons` 完成后用户准备休息

---

## 不可触发条件

- Trivial / Normal 档任务结束（开销不值得）
- 同一会话已经走过本 Workflow（避免重复写 checkpoint）

---

## 第 0 步：判断是否真的需要 checkpoint

执行以下自检：

| 自检项 | 阈值 | 是否触发 |
|---|---|---|
| 本会话 agent 输出累计 token | > 30k | ✅ |
| 本会话 user-agent 交互轮次 | > 20 | ✅ |
| 修改的文件数 | > 5 | ✅ |
| 走过的 Workflow 数 | ≥ 3 | ✅ |
| 距离会话开始时间 | > 2 小时 | ✅ |

任一命中 → 进入第 1 步。
全部未命中且非用户主动 → 输出"上下文未达 checkpoint 阈值，跳过"并退出。

---

## 第 1 步：扫描会话产出

读取本次会话相关的所有改动：

```bash
git log --since="<开始时间>" --oneline
git diff <会话开始前的commit>..HEAD --stat
```

读取本次会话写过的 lessons：

```bash
grep -A 7 "状态.*新增" tasks/lessons.md
```

读取本次会话写过的 todo 完成项：

```bash
grep "^### ✅" tasks/todo.md | tail -10
```

---

## 第 2 步：生成 checkpoint 文件

写入 `tasks/context-checkpoint-YYYYMMDD-HHMM.md`，格式：

```markdown
# Context Checkpoint: <会话主题>

> 创建时间：YYYY-MM-DD HH:MM
> 会话长度：<X 小时 Y 分钟>
> 触发原因：<自动 / 用户主动 / Complex 任务收尾>

---

## 1. 本次会话完成的工作

### 任务列表
- [x] <任务 1>：<成果>
- [x] <任务 2>：<成果>

### 修改的文件（按重要性排序）
- `path/to/file1.py`：<修改了什么>
- `path/to/file2.md`：<修改了什么>

### 通过的验证
- Ruff: ✅
- Pytest: <X/Y> ✅
- 场景验证: <列表>

---

## 2. 关键决策与权衡

> 仅记录"选 A 不选 B"且 B 也合理的情况，便于未来回溯。

- **决策 1**: <描述>
  - **理由**: <为什么选A>
  - **被放弃的方案**: <B方案是什么>
  - **未来可能要重新考虑的条件**: <什么情况下B会比A好>

---

## 3. 未决问题

> 本次会话识别到但**没有解决**的问题。下次会话开局直接读这一节。

- ⏳ <问题 1>：<现状>
- ⏳ <问题 2>：...

---

## 4. 下一步建议

### 立刻可做（短）
- [ ] <短期行动项 1>
- [ ] <短期行动项 2>

### 需要规划（长）
- [ ] <长期行动项 1>
- [ ] <长期行动项 2>

---

## 5. 本次会话产出的 Lessons

| Lesson ID | 关键词 | 状态 |
|---|---|---|
| L-YYYY-MM-DD-NNN | <关键词> | 新增 / 已升级 |

---

## 6. 重启会话的引导词

> 复制下面这段到新会话开局，agent 能快速 catch up：

```text
请先读取 `tasks/context-checkpoint-YYYYMMDD-HHMM.md` 了解上次会话进度。
重点关注 §3 未决问题和 §4 下一步建议。
然后进入正常的 /plan-task 流程。
```

会话清场完成时间：YYYY-MM-DD HH:MM
```

---

## 第 3 步：主动建议用户开新会话

输出：
```text
🧹 Context Checkpoint 已生成
文件：tasks/context-checkpoint-YYYYMMDD-HHMM.md
触发原因：<...>

本次会话状态
累计 token：<估算值>
修改文件：<N> 个
完成 todo：<X> 项
写入 lesson：<Y> 条

强烈建议
✋ 现在是开启新会话的最佳时机。
理由：
1. 长会话会累积上下文噪声，agent 决策质量下降
2. 新会话开局读 checkpoint 文件，能 100% catch up
3. 旧会话的 token 历史不会影响新会话的判断

切换到新会话的步骤
1. 关闭当前对话窗口
2. 开新对话
3. 第一句话用以下引导词：
"请先读取 tasks/context-checkpoint-YYYYMMDD-HHMM.md 了解进度。
然后我们继续推进 §4 列出的下一步。"

是否要我现在做最后一次扫描确保没有遗漏，还是直接结束本会话？
```

---

## 第 4 步：等待用户响应

| 用户回复 | 处理方式 |
|---|---|
| "结束" / "好的" / 类似确认 | 输出告别语，停止响应 |
| "再扫描一次" | 回到第 1 步重新执行 |
| "我还有 X 任务要做" | 询问是否升级到下一会话再做，还是本会话强行继续（不推荐） |

---

## 反模式（禁止行为）

- ❌ 不写 checkpoint 文件就告诉用户"建议开新会话"
- ❌ checkpoint 文件没有"未决问题"和"下一步建议"两节
- ❌ 在用户明确说"还要继续"时强行结束会话
- ❌ 引导词写得太复杂，用户复制粘贴还要修改
- ❌ Trivial / Normal 任务也跑这个流程（成本浪费）

---

## 与其他 Workflow 的关系
```text
Complex 任务完成
↓
/verify-done 通过
↓
/promote-lessons 完成
↓
自动触发 /context-checkpoint（本 Workflow）
↓
建议用户开新会话
↓
新会话开局读 checkpoint 文件
↓
进入 /plan-task 推进未决项
```

---

## 更新记录

| 日期 | 变更 | 原因 |
|---|---|---|
| 2026-04-27 | 初版建立 | Harness 升级第 8 步 |
