# Workflow: /promote-lessons

> Lessons 自动升级 Workflow，三工具共享（Antigravity / Claude Code / Gemini CLI）。
> 由 `/verify-done` 第 6 步完成后自动触发，也可手动调用。
> 最后更新：2026-04-24

---

## 核心设计原则

- `general-global-rule.md` **永远精简**（封顶 200 行），只存标准条文和 Wiki 指针
- 详细知识存 **Obsidian Vault 兼容的 Wiki**：`/Users/chaojin/Antigravity Projects/Generalrule/wiki/`
- 三工具共享读取，写入由本 Workflow 统一负责
- 所有 Wiki 页面**必须**带 YAML frontmatter，便于 Obsidian 按元数据筛选

---

## 触发条件

- `/verify-done` 第 6 步完成后自动触发
- 用户手动发 `/promote-lessons`

---

## 第 0 步：扫描待处理 Lessons

读取当前项目的 `tasks/lessons.md`，找出所有 **状态字段为"新增"** 的条目。

- 无新增条目 → 输出"✅ 无待处理 lesson"并结束
- 有新增条目 → 继续第 1 步

---

## 第 1 步：逐条分类判断

对每条"新增" lesson，按决策树判断：

### 判定为"提升至 Wiki"（需同时满足）
- 适用范围字段写了"全局"或领域名称
- 规则内容与具体项目业务无关
- 领域匹配下表任一关键词：

| 关键词命中 | Wiki 目录 | 说明 |
|---|---|---|
| LLM, 模型, fallback, 配额, 429, Prompt, 提示词 | `wiki/llm/` | LLM 调度与使用 |
| 前端, HTML, CSS, JS, DOM, 剪贴板, 渲染, Clipboard, Markdown | `wiki/frontend/` | 前端交互与渲染 |
| bug修复, 函数签名, 架构, 接口, 最小破坏, 重构 | `wiki/engineering/` | 工程实践 |
| 爬虫, 反爬, 抓取, 清洗, 字幕, 公众号, YouTube | `wiki/crawler/` | 爬虫与数据采集 |
| 图像, Imagen, Nano Banana, 生成, 风格, 信息图 | `wiki/image-gen/` | 图像生成 |

### 判定为"固化为 Skill"
- 规则本身是一个完整的可执行流程（不只是约束）
- 跨项目直接可复用

### 判定为"留在项目内"
- 强依赖当前项目业务
- 或仅适用于当前项目特有的技术栈细节

---

## 第 2 步：生成升级提案

输出以下格式并**停下等待用户确认**：

```
## 📋 Lessons 升级提案

### 🌐 建议提升至 Wiki（同步在 general-global-rule.md 加指针）
| ID | Wiki 路径 | 章节指针 | 理由 |
|---|---|---|---|
| L-xxx | wiki/llm/cascading-fallback.md | §4.7 | ... |

### 🔧 建议固化为 Skill
| ID | Skill 名 | 理由 |
|---|---|---|
| L-xxx | skill-name | ... |

### 📁 建议留在项目内
| ID | 理由 |
|---|---|
| L-xxx | 依赖项目特有业务 |

---
请回复：
- "全部确认" → 按提案执行所有升级
- "确认 L-xxx L-yyy" → 只升级指定条目
- "跳过" → 本次不升级
```

---

## 第 3 步：执行确认的升级

### 3a. 提升至 Wiki 的完整操作

#### 步骤 1：生成 Wiki 页面文件

在对应领域目录下创建文件（命名规则：`kebab-case.md`），**必须**包含 YAML frontmatter：

```markdown
---
title: 
source_lesson: L-YYYY-MM-DD-NNN
created: YYYY-MM-DD
domain: 
keywords: [关键词1, 关键词2, 关键词3]
applies_to: [全局 | ]
status: active
related_rules: [§4.x]
---

# 

## 背景


## 核心规则


## 反模式（禁止行为）
- ❌ 
- ❌ 

## 推荐做法
- ✅ 
- ✅ 

## 代码示例（如适用）


## 相关知识
- [[其他 wiki 页面的链接]]（如有）

## 来源
- 原始 Lesson: L-YYYY-MM-DD-NNN
- 升级日期: YYYY-MM-DD
- 关联 User Rules: §4.x
```

#### 步骤 2：在 `general-global-rule.md` 加指针（不加详细内容）

找到 §4 最后一个子节，追加新小节。**注意保持精简**：

```markdown
### §4.x （一句话核心）



→ 详见 Wiki: `wiki//.md`
→ 来源: L-YYYY-MM-DD-NNN
```

#### 步骤 3：更新 `wiki/index.md` 索引

在对应领域表格的"页面列表"区域追加：

```markdown
|  | [[/]] |  |  |
```

如果索引文件里还没有对应领域的明细表格，先创建：

```markdown
###  领域明细

| 规则标题 | 链接 | 关键词 | 创建日期 |
|---|---|---|---|
|  |
```

#### 步骤 4：更新对应领域的 `README.md`

把 `wiki/<领域>/README.md` 里的"暂无内容"替换成实际页面列表：

```markdown
#  领域知识

> 由 promote-lessons 自动维护。

## 页面列表

- [[]] - 
```

#### 步骤 5：更新 `tasks/lessons.md`

把对应 lesson 的状态字段改为：

```
- **状态**: 已提升至 Wiki: wiki/<领域>/<文件名>.md + User Rules §4.x (YYYY-MM-DD)，此条作废但保留
```

### 3b. 固化为 Skill 的操作

1. 调用 `@skill-creator`，把 lesson 的"规则"字段作为 Skill 描述输入
2. Skill 创建完成后，在 lessons.md 标注：
```
- **状态**: 已固化为 Skill: <skill-name> (YYYY-MM-DD)，此条作废但保留
```

### 3c. 留在项目内的操作

把对应 lesson 的状态字段改为：

```
- **状态**: 保留在项目内（与业务强绑定），最后审查 YYYY-MM-DD
```

---

## 第 4 步：同步提醒（每次必输出）

```
## 📌 同步检查清单

✅ Claude Code：符号链接自动同步（~/.claude/CLAUDE.md）
✅ Gemini CLI：符号链接自动同步（~/.gemini/GEMINI.md）
⚠️  Antigravity Settings → Rules：需手动重新粘贴

运行以下命令复制最新规则到剪贴板：
cat "/Users/chaojin/Antigravity Projects/Generalrule/antigravity/general-global-rule.md" | pbcopy

---
## 📊 本次升级汇总

- 新建 Wiki 页面: <N> 个
- general-global-rule.md 新增指针: <N> 条
- 固化 Skill: <N> 个
- 保留项目内: <N> 条
- Wiki 总页面数（全部领域累计）: <N>

👉 打开 Obsidian 查看图谱: /Users/chaojin/Antigravity Projects/Generalrule/wiki/
```

---

## 反模式（禁止行为）

- ❌ 把详细内容直接追加到 `general-global-rule.md`（只加指针）
- ❌ Wiki 页面不加 YAML frontmatter
- ❌ 不更新 `wiki/index.md` 索引
- ❌ 不更新 `wiki/<领域>/README.md`
- ❌ 不等用户确认就自动写入
- ❌ Wiki 页面命名用 CamelCase 或中文（统一 kebab-case 英文）

---

## 与其他 Workflow 的关系

```
/plan-task
  → 第 1 步 读 tasks/lessons.md
  → 第 2.5 步 读 wiki/index.md + wiki/<相关领域>/
  → 规划
/verify-done
  → 验证完成 → 自动触发 /promote-lessons
/promote-lessons
  → 扫描新 lesson → 分类 → 提案 → 等确认 → 升级 → 同步提醒
```

---

## 更新记录

| 日期 | 变更 | 原因 |
|---|---|---|
| 2026-04-24 | 初版建立 | Wiki 化改造 |
