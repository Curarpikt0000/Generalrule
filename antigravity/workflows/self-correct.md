# Workflow: /self-correct

> 自治反思修复 Workflow，由 `general-global-rule.md §4.10` 强制约束。
> 本 Workflow 是 `/verify-done` 第 7 步的失败处理路径，也可手动调用。
> 实现 Reflexion Loop（来自 LangChain 2026 实验，benchmark 提升 13.7 个百分点的核心改造）。
> 最后更新：2026-04-27

---

## 触发条件

- `/verify-done` 第 1-4 步失败时**自动**触发
- 用户手动发 `/self-correct <错误描述>`
- 代码报错且**不在不可逆动作清单**内

---

## 不可触发条件（硬约束）

依照 `general-global-rule.md §4.10` 例外条款。以下情况**禁止**调用本 Workflow，必须立即停下问用户：

- `git push` / `git reset --hard` / `rm -rf` / 删除文件、数据库记录
- 涉及付费的 API 调用（OpenAI billing、AWS 计费操作等）
- 发送邮件、推送通知、调用 webhook
- 写入线上数据库（区别于本地测试 DB）
- 修改用户数据相关的不可逆操作

**判断方法**：如果操作"做了之后无法 undo"，就是不可逆，禁止自治重试。

---

## 输入参数

调用本 Workflow 时必须传入：

- `failure_step`：失败的具体步骤（例如"verify-done 第 2 步 pytest"）
- `error_message`：完整报错信息（不允许截断）
- `task_context`：当前 `tasks/todo.md` 中正在执行的任务段落

---

## 状态机

本 Workflow 维护以下状态：
```python
state = {
    iteration: 0,           # 当前是第几次尝试，初始 0
    max_iterations: 3,      # 硬上限
    history: [],            # 每次尝试的 [reflection, change_summary, result]
    drift_detector: {       # Anti-drift 状态
        last_file_modified: None,
        last_error_signature: None,
        consecutive_same_file: 0,
        consecutive_same_error: 0
    }
}
```

---

## 第 0 步：检查不可逆例外

读入 `failure_step` 和 `error_message`，扫描是否包含不可逆操作关键词：

```python
forbidden_patterns = [
    "git push", "git reset --hard", "rm -rf",
    "DROP TABLE", "DELETE FROM",
    "stripe", "billing", "charge",
    "send_email", "webhook",
    # ... 项目可在 AGENTS.md 自定义扩展
]
```

如果命中 → 立即输出：
```text
🚨 检测到不可逆操作失败，禁止自治重试
失败步骤：<failure_step>
错误：<error_message>
请用户亲自介入处理。
```
并**直接退出 Workflow**，返回状态 `IRREVERSIBLE_BLOCKED`。

---

## 第 1 步：Reflection（强制）

输出严格三段式 reflection 文本（不许跳过任何一段）：
```text
🔄 Reflexion #<iteration>
1. What failed?
<具体失败原因，必须引用 error_message 的关键行>
2. What change would fix it?
<提出本次的修复假设，必须明确"改哪个文件 / 改哪一行 / 改成什么">
3. Am I repeating?
<对比 history 中的前几次尝试。如果改动方案与上次相似，必须明确说明"是 / 否 / 部分相似"。如果"是"，立即触发 anti-drift 短路（跳到第 5 步）>
```

---

## 第 2 步：Anti-drift 检测

每次进入第 1 步之后、第 3 步之前，强制检查：

### 2.1 同文件检测

```python
if iteration > 0 and current_modified_file == drift_detector.last_file_modified:
    drift_detector.consecutive_same_file += 1
else:
    drift_detector.consecutive_same_file = 0
    drift_detector.last_file_modified = current_modified_file

if drift_detector.consecutive_same_file >= 2:
    return DRIFT_DETECTED("连续两次修改同一文件")
```

### 2.2 同报错检测

提取报错的"签名"（错误类型 + 关键行号或函数名，不含具体值）：

```python
signature = extract_error_signature(error_message)
# 示例：("ValidationError", "models.py:45", "field 'name'")

if iteration > 0 and signature == drift_detector.last_error_signature:
    drift_detector.consecutive_same_error += 1
else:
    drift_detector.consecutive_same_error = 0
    drift_detector.last_error_signature = signature

if drift_detector.consecutive_same_error >= 2:
    return DRIFT_DETECTED("连续两次出现相同报错签名")
```

### 2.3 触发短路

任一检测命中 → 直接跳到第 5 步（DRIFT_DETECTED 退出），**不再尝试修改**。

---

## 第 3 步：执行修复尝试

基于第 1 步的 reflection 写代码：

1. 严格按 reflection #2 的"修复假设"执行（不要顺手改其他东西，违反 §4.8 最小破坏原则）
2. 改完后**立即** 重新跑触发本次 Reflexion 的那个 verify 步骤（不是整个 /verify-done，只跑失败的那一步）
3. 把本次 [reflection, change, result] 追加到 `history`

---

## 第 4 步：判断结果

| 结果 | 行动 |
|---|---|
| 修复成功（验证通过） | 跳到第 6 步 SUCCESS 退出 |
| 修复失败但 iteration < 3 | iteration += 1，回到第 1 步继续下一轮 |
| 修复失败且 iteration == 3 | 跳到第 5 步 MAX_REACHED 退出 |

---

## 第 5 步：失败退出（DRIFT_DETECTED 或 MAX_REACHED）

输出完整尝试历史：
```text
🚨 Self-Correct 退出
退出原因：<DRIFT_DETECTED: 连续 X 次修改同一文件 | MAX_REACHED: 3 次尝试都失败>
完整尝试历史：
尝试 1

Reflection: <文本>
改动: <diff 摘要>
结果: <仍然失败 / 引发新错误>

尝试 2

...

尝试 3

...


下一步选项（请用户选择）：
(a) 手动接手修复（我会停下让你看代码）
(b) 调用 /rollback 回滚到 checkpoint，重新规划
(c) 其他方案
```

写入 `tasks/lessons.md` 一条新 lesson（状态："新增"），记录这次失败模式，便于后续 promote-lessons 升级。

退出 Workflow。

---

## 第 6 步：成功退出

输出：
```text
✅ Self-Correct 修复成功
迭代次数：<X> / 3
最终修改：<diff 摘要>
```

返回 verify-done 主流程的第 1 步重新跑（不是只跑失败的那一步——成功修复后必须重新跑全部验证，防止修复引入新问题）。

---

## 反模式（禁止行为）

- ❌ 跳过第 1 步 reflection 直接改代码
- ❌ reflection 三段式不完整（特别是漏掉 #3 "Am I repeating?"）
- ❌ 第 3 步顺手"优化"其他无关代码
- ❌ 命中 anti-drift 短路后还要再试一次
- ❌ 不可逆操作偷偷尝试自治重试
- ❌ 失败退出时不写 lesson

---

## 与其他 Workflow 的关系
```text
/verify-done 第 1-4 步失败
↓
/self-correct（本 Workflow）
├─ SUCCESS → 回到 /verify-done 第 1 步重跑
├─ DRIFT_DETECTED → 提示用户选择手动 or /rollback
└─ MAX_REACHED → 提示用户选择手动 or /rollback
```

---

## 更新记录

| 日期 | 变更 | 原因 |
|---|---|---|
| 2026-04-27 | 初版建立 | Harness 升级第 5 步 |
