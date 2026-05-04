# Workflow: /rollback

> Git 回滚逃生舱 Workflow，由 `general-global-rule.md §5.6` 强制约束。
> 用于在任务彻底失败（Reflexion 用尽、用户主动放弃）时，干净回到 `/plan-task` 第 0.5 步建立的 Git checkpoint。
> 最后更新：2026-04-27

---

## 触发条件

- 用户主动发 `/rollback`
- `/self-correct` 返回 MAX_REACHED 或 DRIFT_DETECTED 后用户选择 (b) 回滚
- `/verify-done` 失败后用户判断"无法修复"主动求救

---

## 不可触发条件（硬约束）

- 已经 `git push` 到远程的 commit（除非用户明确确认接受 force push 风险）
- 工作区有用户**手动**做的、未在 todo.md 记录的关键改动（防止误删用户成果）

---

## 第 0 步：定位 Checkpoint Hash

### 0.1 优先从 todo.md 读取

执行：

```bash
grep -i "Checkpoint" tasks/todo.md | tail -5
```

期望输出形如：`Checkpoint: a3f8d2c (auto-created at 2026-04-27 14:30)`

提取 hash（例如 `a3f8d2c`）作为 `<target-hash>`。

### 0.2 备用：从 git log 找最近的 Auto-checkpoint

如果 todo.md 里没有 Checkpoint 记录（可能是 Trivial 档跳过了），执行：

```bash
git log --oneline --all | grep "Auto-checkpoint" | head -5
```

让用户选择具体回滚到哪一个。

### 0.3 找不到 checkpoint 的处理

如果两种方法都没找到 → 输出：
```text
🚨 未找到自动建立的 Git checkpoint
可能原因：
- 本次任务是 Trivial 档，跳过了 /plan-task 第 0.5 步
- 任务在多次 plan 之间，checkpoint 被覆盖
- 此 Git 仓库的 reflog 已被清理

可选方案：
(a) 手动指定要回滚到的 commit hash（请提供）
(b) 放弃回滚，自行 git stash 后清理工作区
(c) 运行 git reflog 查看完整历史，再手动选择
```

并退出 Workflow，状态 `CHECKPOINT_NOT_FOUND`。

---

## 第 1 步：风险预检查

### 1.1 当前工作区状态

执行：

```bash
git status --short
git diff --stat HEAD
```

**汇报用户**：从 checkpoint 到现在累积了哪些改动。

### 1.2 检查是否已 push

执行：

```bash
git log <target-hash>..HEAD --oneline
git branch --contains HEAD
```

如果发现有 commit 已 push 到 remote → **强制询问用户**：
```text
⚠️ 警告：以下 commit 已推送到远程
<commit-list>
回滚后这些 commit 在本地会消失。如果要彻底清理远程，需要 git push --force（危险）。
请选择：
(a) 仅本地回滚，远程保留（标准做法）
(b) 本地+远程都回滚（force push，需用户明确同意）
(c) 取消回滚
```

未明确选择前不得继续。

### 1.3 检查未追踪的用户成果

执行：

```bash
git ls-files --others --exclude-standard
```

如果有未追踪文件 → 询问用户：
```text
检测到未追踪文件（git 不会自动恢复这些）：
<file-list>
回滚不会动这些文件，但建议你确认是否需要先 git stash -u 备份。
继续吗？(yes / stash-first / cancel)
```

---

## 第 2 步：用户最终确认

输出完整回滚摘要，要求用户**显式输入"确认回滚"**才能执行：
```text
🔄 即将执行 Git 回滚
目标 checkpoint: <target-hash> (<created-time>)

将丢弃的改动:
<commit 1>
<commit 2>

工作区未提交改动: <X 个文件>

执行命令:
git reset --hard <target-hash>

⚠️ 这是不可逆操作（除非你能从 git reflog 找回）。请输入"确认回滚"以继续，或输入其他任何内容取消。
```

未收到"确认回滚"四字 → 取消并退出。

---

## 第 3 步：执行回滚

### 3.1 主回滚命令

```bash
git reset --hard <target-hash>
```

### 3.2 如果用户选择了 1.2 的 (b) 远程回滚

```bash
git push --force-with-lease origin <branch>
```

注意用 `--force-with-lease` 而不是 `--force`，避免覆盖别人的 push。

### 3.3 验证回滚成功

```bash
git log -1 --oneline
git status
```

确认 HEAD 是 `<target-hash>` 且工作区干净。

---

## 第 4 步：清理与汇报

### 4.1 在 tasks/todo.md 标注本次任务失败

找到对应任务段落，追加：

```markdown
❌ 任务回滚 (YYYY-MM-DD HH:MM)
回滚原因: <用户填写的原因，或自动填"Reflexion Loop 用尽">
回滚到: <target-hash>
丢弃的尝试: <commit-count> 个 commit + <file-count> 个工作区文件
完整尝试历史: 详见 self-correct 输出（如有）
```

### 4.2 写入 lesson（强制）

`tasks/lessons.md` 顶部追加：

```markdown
## L-YYYY-MM-DD-NNN

- **场景**: 任务 <task-name> 触发 /rollback
- **错误行为**: <一句话总结失败模式>
- **用户纠正**: <如果是用户判断的，记下用户怎么说的>
- **规则**: 下次遇到 <类似场景> 时，提前 <如何避免>
- **关键词**: rollback, 失败模式, <具体技术词>
- **适用范围**: <"本项目" 或 "全局">
- **状态**: 新增
```

让 promote-lessons 后续可以从中提炼出"避免再次失败"的模式。

### 4.3 汇报用户
```text
✅ 回滚完成
已回到: <target-hash> (<commit-message>)
工作区状态: <git status 简要>

下一步建议:
1. 重新调用 /plan-task 规划修复方案
2. 或先用 /context-checkpoint 总结本次失败经验后再开新会话
```

---

## 反模式（禁止行为）

- ❌ 跳过第 2 步用户确认直接 reset
- ❌ 用 `git push --force`（必须用 `--force-with-lease`）
- ❌ 不写 lesson 就退出（失败的经验最值钱）
- ❌ 静默回滚不汇报用户
- ❌ checkpoint 找不到就用 `HEAD~1` 之类的猜测值

---

## 与其他 Workflow 的关系
```text
/plan-task 第 0.5 步建立 checkpoint
↓
执行任务
↓
[失败] /verify-done 第 7 步 → /self-correct
↓
[Reflexion 用尽] 用户选择回滚
↓
/rollback（本 Workflow）
↓
回到 checkpoint，重新 /plan-task 规划
```

---

## 更新记录

| 日期 | 变更 | 原因 |
|---|---|---|
| 2026-04-27 | 初版建立 | Harness 升级第 6 步 |
