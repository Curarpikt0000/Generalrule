---
title: 五步链路与五阶段 Workflow 细节
domain: agent-rules
type: concept
keywords: [五步链路, workflow, explore, plan, execute, verify, learn, 硬门, tdd]
tags: [pipeline, workflow, explore, plan, execute, verify, learn]
source: general-global-rule.md §3 §4 的展开
sources: [general-global-rule.md]
created: 2026-05-24
updated: 2026-05-24
last_updated: 2026-05-24
---

# 五步链路与五阶段 Workflow 细节

> 本页是 general rule §3（五步链路）和 §4（五阶段 workflow）的完整展开。
> general rule 里是浓缩版，本页是执行 SOP。三个 Agent 通用。

---

## 两个东西的关系（先分清）

**五步链路（§3）** 和 **五阶段 workflow（§4）** 不是一回事，容易混：

- **五步链路** = 回答"**遇到问题去哪找答案**"的顺序：Rule → Wiki → Skill → 公网 → 自己写。它是**信息检索的优先级**。
- **五阶段 workflow** = 回答"**一个任务怎么从头做到尾**"的流程：Explore → Plan → Execute → Verify → Learn。它是**任务执行的生命周期**。

两者嵌套：五阶段的第一阶段 EXPLORE，内部就用五步链路来加载上下文。

---

## 第一部分：五步链路（信息检索优先级）

任何非琐碎任务，找答案/方案时按此顺序，**禁止跳步**：

1. **读 Rule** —— 读 general-global-rule.md，找相关认知纪律（§2）和场景规范指针（§8）。
2. **查 Wiki** —— 读 `wiki/index.md` → 相关领域页面。命中直接用，标注「来自 Wiki: <文件名>」。详见 [[wiki-ingest-guide]] 第四节 QUERY。
3. **找 Skill** —— 检索已安装 skill（superpowers / wiki-update / skill-creator / RTK 等）。有匹配就调用，不重复造轮子。
4. **搜公网** —— GitHub / PyPI / 官方文档。找到现成方案就用；有价值的内容按 [[wiki-ingest-guide]] 写回 Wiki。
5. **自己写代码（兜底）** —— 前四步都没方案，才从零写。

> 为什么这个顺序：越靠前的来源越"已知可信、已为本项目验证"，越靠后越"未知、需验证"。先用沉淀的知识，再用外部的，最后才造新的。

---

## 第二部分：五阶段 Workflow（任务生命周期）

每个非琐碎任务按此五阶段走完。实现因 Agent 而异（Claude Code 用 `~/.claude/commands/`，Antigravity 用 Customizations→Workflows，Hermes 读 workflow 文件），但**阶段纪律通用**。

### 阶段 1：EXPLORE（探索）

- 读相关文件、读 Wiki（用五步链路）、检索 Skill。
- **只读不改**，加载足够上下文。
- 看不懂现有代码为何这样设计 → 先问，别动（§2.6 落笔前先读）。
- **能调 superpowers `brainstorming` skill 的平台**（Claude Code）：优先调用它做苏格拉底式需求澄清。
- **不能调的平台**（Hermes / Antigravity）：按同样方法论手动 —— 提问澄清需求、探索多种方案、分段呈现设计供确认。

### 阶段 2：PLAN（计划）【硬门】

产出书面计划，必须包含：
- 改什么、改哪些文件、什么顺序
- **验收标准**（成功长什么样）
- 任务复杂度评估
- TDD 是否适用的判断（见下方 TDD 规则）
- 建议豁免哪些步骤（如有）

**硬门规则**：计划必须经用户**明确批准（approve）**才能进入 EXECUTE。
**活口**：AI 可对琐碎任务**申请**精简或豁免步骤，但豁免与否由用户在批准时一并拍板，AI 不得自行跳过。

> 能调 superpowers `writing-plans` skill 的平台优先调用，生成带精确文件路径和验证步骤的结构化计划。

### 阶段 3：EXECUTE（执行）

- **EXECUTE 开始前自动建立 Git 检查点**（供回滚）：
```bash
  git status --short          # 确认工作区状态
  git commit --allow-empty -m "Auto-checkpoint before <task-name>"
```
- 严格按已批准的计划实现，边做边验证。
- 偏离计划需显式说明并重新确认。
- 一量改动控制在必要范围（§2.3 外科手术式修改），不超过 5 个文件就停下确认。

### 阶段 4：VERIFY（验证）

- 跑完整验证，确认达到 PLAN 定义的验收标准。
- **这是单一最高杠杆动作**：任何宣称"完成"前必须先验证。
- 跳过步骤却说"完成"、跳过测试却说"通过" = 违规（§2.10 显式失败）。
- 验证失败 → 触发 SELF-CORRECT（见第三部分）。

#### VERIFY 场景化验证清单（按改动类型对号入座，多项适用全做）

- **Pydantic 模型**：构造 3 种输入（合法边界 / 非法类型 / 缺失必填），跑实例化，确认校验行为符合预期。
- **LLM 调用链**：grep 确认模型 ID 非硬编码；验证级联 fallback（一级故意失败→降二级→切平台→全失败时异常含"所有候选链路已尝试"）。
- **爬虫/清洗**：用真实样本 URL 跑完整流程，确认反爬有效、输出结构字段齐全编码正确。
- **FastAPI 端点**：启 uvicorn，curl 打最小 payload，确认状态码对、JSON 结构对、错误输入触发 4xx 而非 500。
- **前端**：本地点一遍受影响交互，看 Console 无 JS 报错、fetch 正常、UI 符合预期。
- **config/环境变量**：确认不导致启动失败，缺失变量有清晰报错（非裸 KeyError）。

每个场景都要**输出实际验证结果**（命令 + 返回摘要），不能只说"验证过了"。

#### VERIFY 高级工程师自检（宣称完成前必答）

逐项回答，任何 ⚠️ 必须修掉或显式声明"用户确认保留"：
1. **命名**：表意清晰？有无 data2/tmp/handle 偷懒命名？
2. **职责单一**：每个函数只做一件事？有无 50 行以上巨型函数？
3. **异常处理**：有无裸 `except:` 或 `except: pass` 吞异常？
4. **魔法数字**：有无未解释的硬编码数值？
5. **副作用**：有无隐含的全局状态修改/写文件？必要吗？
6. **向后兼容**：会破坏已有调用方吗？


### 阶段 5：LEARN（沉淀）

任务收尾必做，不可省略：
- 用户的纠正 → 记 lesson（general rule §6）。
- 公网/调试中获得的有价值新知识 → ingest 到 Wiki（[[wiki-ingest-guide]]）。
- 全局通用的 lesson → 同时 ingest 到 Wiki。

> 为什么 LEARN 是强制阶段而非可选：沉淀是整个体系的目的。不沉淀，知识就随会话蒸发，下次重新踩坑。

---

## 第三部分：两个按需流程

不是每次都走，触发时才走：

### SELF-CORRECT（自治修复）

VERIFY 失败时启动：
1. 输出 reflection：**What failed? / What would fix it? / Am I repeating?**
2. 基于反思修复（计数 +1），重新验证。
3. 失败次数 < 3 → 回第 1 步；= 3 → **强制停下**，向用户报告全部尝试历史。

**Anti-drift**：连续两次改同一文件且改动相似 → 立即跳出；同一报错连续两次 → 立即跳出。
**例外**：不可逆动作（删除、git push、付费 API、发消息）禁止自治重试，立刻停下问用户。

### ROLLBACK（回滚）

SELF-CORRECT 用尽仍失败，或用户主动要求时：
```bash
git reset --hard <checkpoint-hash>
```
输出"已回到任务开始前的状态"。

---

## 第四部分：TDD 强制规则

涉及**核心业务逻辑、数据 Schema、关键 bug 修复** → TDD 强制（先写失败测试 → 写实现 → 验证通过）。
**内容生成类**（文章/视频/播客等非确定性输出）→ 默认豁免 TDD。
PLAN 阶段若判断某个本该 TDD 的任务不必那么复杂，可在硬门处向用户申请豁免，用户手动批准。

详细 TDD 执行顺序见 [[python-coding]] 第 6 节。

---

## 第五部分：复杂度自适应（留活口）

不是所有任务都要走完整五阶段。PLAN 阶段，AI 应根据复杂度**建议**：

- **琐碎任务**（改错别字、调一个配置）：可建议跳过 EXPLORE 深度、跳过 TDD，快速走 PLAN→EXECUTE→VERIFY。
- **Normal 任务**：完整五阶段。
- **Complex 任务**（架构决策、核心链路改动）：五阶段 + 可选的多 Agent 审查（Producer 出方案、用户当 Judge 拍板）。

**但简化建议必须经用户批准**（PLAN 硬门），AI 不得自行决定跳过。

---

## 相关页面

- [[wiki-ingest-guide]] —— Wiki 读写操作（QUERY/INGEST/HEALTH 细节）
- [[python-coding]] —— TDD 执行顺序、代码规范
- [[llm-orchestration]] —— LLM 调度（涉及模型调用的任务）
- general-global-rule.md §2 §3 §4
