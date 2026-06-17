# self-skill/ —— 怎么写 / 怎么 copy 一个 skill（操作手册）

> 本文件是 [`README.md`](README.md)（准入宪法）的**操作配套**：宪法管「能不能放、必须登记」，本文件管「具体怎么落地」。
> 冲突时以 `README.md` 与 `general-global-rule.md` §6.5 为准。

---

## 0. 先判准入（必过门）

一句话自检：**「把它给一台跟 Uber 无关的机器上的 agent，它还有用吗？」** 有用 → 通用 skill，可放；没用（绑定某项目/某公司内部系统）→ 特用 skill，**禁止**进本目录。
不放含凭据 / 含 Uber 专有内容（内部链接、流程、人员/业务数据）的东西。

---

## 1. 两种来源，两种写法

### A. copy 一个外部开源 skill（如 agent-slides）

1. **整目录拷入** `self-skill/<skill-name>/`。
2. **只收 skill 定义，不背运行时引擎**：若上游靠一个已发布的包/CLI 运行（PyPI / npm 等），只 vendoring `SKILL.md` + references + `LICENSE`，运行时让取用机按需拉包。vendoring 一份引擎源码不会改变运行行为，只增重——除非要离线/钉版本。
3. **去写死路径**：机器绝对路径（`/Users/xxx`、`/home/xxx`、固定账号名）→ 占位符 + 「各 agent 按本机解析」。体系约定（`main`/`ub-branch` 分支名等）可保留。
4. **去凭据 / 去内部链接**：删 API key、token、内部 URL、Uber 专有内容。
5. **保留许可与署名**：开源 skill 的 `LICENSE`（如 MIT）+ 原作者署名必须随附。
6. **写 `README.md`**：标明来源/许可、运行时依赖、与上游的差异（删了什么、为什么）、用法、准入登记指针。
7. **红线自检**：`grep -rnE "/Users/|/home/[a-z]|token|api[_-]?key|secret"` 通读一遍。

### B. 把自有 skill 改造成通用版（如 webworms / llm-wiki）

同上 3~7，外加：把项目/公司专有逻辑抽象成通用结论；config 走 `config.example.md`（本机 `config.md` 进 `.gitignore`，不入库）。

---

## 2. SKILL.md 的 frontmatter 约定

对齐本目录既有 skill：至少 `name` + `description`；多文件/有版本的加 `version: <x.y.z>-generalrule`、`compatibility: <运行前提>`。`description` 写清「何时用」，便于 agent 路由。中文为主，代码标识符保持英文。

---

## 3. copy 之后必须登记（准入的一部分，不是可选）

每放入/更新一个 skill，三处同步：

1. **`wiki/agent-rules/skill-register.md` §8 Self-Skill 区**：加一行（skill / 用途 / 来源 / 取用方式）。
2. **`self-skill/README.md` §四「当前已收纳」**：加一行。
3. **根 `CHANGELOG.md`**：① 在「结构白名单」补本 skill 的子结构；② 在「变更记录」记一笔（日期 / branch / agent / 改了什么 / 为什么）。

> 不登记 = 别的 agent 找不到 = 白放。

---

## 4. 分支与推送

- 通用 skill = 通用内容 → 提交到 **`main`**，再 merge 到 `ub-branch`（§7.5）。
- 仅 Uber 适用的内容才进 `ub-branch`。
- 提交前 `git status` 核对，**只提交本次有意改动**，禁止 `git add .` 一把梭（§6.6）。
- `git push` 是不可逆动作：按 §7，自治执行前停下与用户确认。

---

## 5. worked example：agent-slides

`self-skill/agent-slides/` 即按本手册「A. copy 外部开源 skill」落地的范例——只收 7 个子 skill 的定义 + `LICENSE`，CLI 走 PyPI（`uvx --from agent-slides`），未 vendoring `src/`；附 `README.md` 说明差异；登记于 §8 + 本目录 README §四 + 根 CHANGELOG。可作为下一个 copy 的模板参考。
