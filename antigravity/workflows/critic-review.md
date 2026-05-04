# Workflow: /critic-review

> 多智能体协作 Workflow，由 `general-global-rule.md §5.5` 强制约束。
> 实现 Producer-Critic-Judge 三角架构（来自 Harness Engineering 2026 多智能体编排规范）。
> 用于 Complex 档任务或核心架构决策的二次评审。
> 最后更新：2026-04-27

---

## 触发条件

- `/plan-task` 判定为 **Complex** 档时**自动**触发（在用户确认计划之前）
- 涉及核心链路修改：LLM 调度、爬虫管道、Pydantic Schema、数据库 migration
- 用户主动发 `/critic-review <方案描述>`
- 一次任务影响超过 5 个文件时强制触发

---

## 不可触发条件

- Trivial 档任务（开销不值得）
- Normal 档任务（除非用户主动调用）
- 已经走过本 Workflow 的同一份方案（避免无限套娃）

---

## 角色定义（硬约束）

依照 `wiki/engineering/harness-engineering-principles.md §2`：

| 角色 | 职责 | **禁止行为** |
|---|---|---|
| **Producer**（主 agent） | 产出方案 | ❌ 不能审查自己的方案 |
| **Critic**（评审 agent） | 提出改进建议 | ❌ 不能否决/通过方案 |
| **Judge**（用户） | 决定通过/不通过 | ❌ 不写建议（只决定） |

**核心原则**：Critic 提建议，Judge 做决定，两者**绝对不能合并**——否则会产生"自我安慰式审查"。

---

## 第 0 步：确认 Producer 已产出方案

读取 `tasks/todo.md` 找到当前任务的"选择方案"段落。如果方案不存在或为空 → 退出 Workflow，提示"请先完成 /plan-task"。

---

## 第 1 步：召唤 Critic 视角

**重要：Critic 必须独立审查，不读 Producer 的推理过程。**

使用以下 prompt 在 agent 内部切换到 Critic 模式（或调用 sub-agent）：
```text
你现在是 Code Critic。
你不知道为什么作者选择了这个方案。
你只看到方案本身。
你的唯一任务：找出这个方案的潜在问题，提出改进建议。
你不能批准、不能否决、不能说"看起来不错"。
你必须从以下五个维度独立审查：

1. 正确性：方案能否真的解决用户的需求？
2. 健壮性：边界情况、并发、失败模式有没有覆盖？
3. 可维护性：未来 6 个月这个方案会不会变成技术债？
4. 安全性：有没有引入新的攻击面（注入、权限泄露、不可逆操作）？
5. 与现有架构的契合度：是否违反 general-global-rule.md 的某条规则？
```

---

## 第 2 步：Critic 输出格式（强制）

Critic 必须按以下格式输出，**不允许偏离**：
```text
🔍 Critic Review: <方案标题>

1. 正确性
⚠️ <发现的问题1>（理由）
✅ <方案做对的地方1>

2. 健壮性
⚠️ <发现的问题1>
⚠️ <发现的问题2>
✅ <方案做对的地方>

3. 可维护性
⚠️ <发现的问题>

4. 安全性
⚠️ <发现的问题>

5. 架构契合度
⚠️ 该方案违反 general-global-rule.md §X.Y（<具体条款>）
✅ 该方案遵循 §X.Y


📊 Critic 总结

严重问题（建议必须解决）：<列表>
一般问题（建议优化）：<列表>
优点：<列表>
```

Critic 不做最终决定。以上仅为建议。

如果某个维度真的没问题，写"✅ 该维度未发现问题"，**不许跳过维度**。

---

## 第 3 步：Producer 回应

把 Critic 的输出**完整**呈现给 Producer（如果是同一个 agent 切换角色，则在内部切回 Producer 模式）。

Producer 必须**逐条回应**严重问题：
```text
✍️ Producer 回应

严重问题 1: <Critic 的发现>
接受 / 部分接受 / 拒绝
理由：<...>
修订方案：<具体怎么改>

严重问题 2: <...>
...

一般问题（可选回应）
接受的：<列表>
暂不处理的：<列表 + 理由>
```

**禁止**敷衍式回应（"我会注意"、"加个 try-except 就好了"）——必须给出具体的方案修订。

---

## 第 4 步：递交 Judge（用户）

整理后的最终输出格式：
```text
⚖️ 提请 Judge 决定

原方案
<Producer 的初版方案摘要>

Critic 发现的严重问题
<列表>

Producer 的修订方案
<修订后的方案>

待决定
请用户选择：
(a) 通过修订方案，继续执行
(b) 通过原方案（接受 Critic 提出的风险）
(c) 不通过，回到 /plan-task 重新规划
(d) 其他意见
```

**停下等待用户输入**，未收到明确决定前不得继续。

---

## 第 5 步：决定后的去向

- 用户选 (a) → 用修订方案更新 `tasks/todo.md`，进入正常执行
- 用户选 (b) → 在 todo.md 标注"已知 Critic 风险，用户已接受"，进入执行
- 用户选 (c) → 退出本 Workflow，调用 `/plan-task` 重新开始
- 用户选 (d) → 按用户意见调整后重走第 4 步

---

## 反模式（禁止行为）

- ❌ Producer 和 Critic 用同一个 prompt 上下文（角色没切干净）
- ❌ Critic 给出"看起来不错"、"建议通过"等准 Judge 表态
- ❌ Critic 输出跳过五个维度中的某个
- ❌ Producer 用"我会注意"敷衍回应严重问题
- ❌ 不递交用户直接进入执行
- ❌ Trivial 档任务也跑这个 Workflow（浪费 token）

---

## 与其他 Workflow 的关系
```text
/plan-task 判定为 Complex
↓
自动触发 /critic-review（本 Workflow）
↓
Producer → Critic → Producer 修订 → Judge 决定
↓
[通过] 继续 plan-task 第 4 步写 todo.md
[不通过] 回到 plan-task 重新规划
```

---

## 更新记录

| 日期 | 变更 | 原因 |
|---|---|---|
| 2026-04-27 | 初版建立 | Harness 升级第 7 步 |
