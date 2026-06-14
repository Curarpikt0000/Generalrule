# 新机 / 新 Agent 接入指南（通用）

> 一台新机器、或一个新 agent（Claude Code / Antigravity / Codex / Cursor / Hermes，未来更多）第一次接入本体系时读这份。
> 目标：让它和已有环境守同一套规则、写同一个 Wiki、推同一个 GitHub repo。
> **本指南给通用原则，不写死任何机器路径**——各机按本地习惯解析（呼应 [[general-global-rule]] §7.5 与 self-skill/README 的去写死路径纪律）。

---

## 零、先认清自己在哪

- **GitHub repo**：`git@github.com:Curarpikt0000/Generalrule.git`（SSOT，所有 agent 共享）。
- **分支**（详见 §7.5）：私人机用 `main`；Uber 机（Mac / VM）用 `ub-branch`（= main 超集 + `uber-adaptation.md`）。
- **clone 路径**：各机自选一个稳定目录 clone，**不规定也不写死具体路径**。下文凡提到 repo 内文件，一律用「repo 根 / 相对路径」表述。

---

## 一、Clone + 选对分支

```bash
git clone git@github.com:Curarpikt0000/Generalrule.git <你选的本地路径>
cd <你选的本地路径>
# 私人机：默认 main 即可
# Uber 机：切到 ub-branch
git checkout ub-branch   # 仅 Uber 机
```

> SSH key 没配好会 clone/push 失败：先确认本机有可用 key（`~/.ssh/` 下）且已注册到 GitHub。

---

## 二、把 agent 入口指向通用规则

每个 agent 有自己的"入口/记忆"机制，但**都要最终指向同一份 SSOT**：`antigravity/general-global-rule.md`。

| Agent | 入口机制 | 接入做法 |
|---|---|---|
| Claude Code | `CLAUDE.md` / `AGENTS.md` | 项目入口文件 `import` 或软链到本 repo 的 general rule（入口约定见各机 memory / 项目模板）|
| Antigravity | Custom Instructions + Workflows | Custom Instructions 写一句指针指向 general rule；Workflows 对齐五阶段 |
| Codex / Cursor | 各自的 rules / AGENTS 机制 | 同理，写一句指针指向 general rule，相对路径引用 |

> 原则：**入口文件本身极简**，只做「指向 general rule + 指向本机/项目上下文」，规则正文绝不复制进入口（避免多份失同步）。

---

## 三、开工第 0 步（每次开工都做，不只首次）

接入完成后，**每次开工的第一件事**按 [[general-global-rule]] §7.5「开工第 0 步」执行：

1. `git pull` 本 repo 全部文件（命令按分支，见 §7.5）。
2. 对账三件事：① 规则 / Wiki / workflow 有无更新；② 本地入口 / 配置是否要随之同步；③ 缺哪些核心技能 / MCP（对照 [[skill-register]]）。
3. 需安装的技能 / MCP——**经用户确认后**再装（安装不可逆，守 §7）。

---

## 四、开通 Wiki 写入 + 推送能力

本体系靠 Wiki 做跨 agent、跨机的知识复利（[[general-global-rule]] §6）。接入后该 agent 要能：

1. 学到 lesson / 新知识 → 写入 `wiki/<领域>/<页面>.md`，产出符合 [[wiki-ingest-guide]]（优先调 `self-skill/llm-wiki`）。
2. 更新对应领域 `README.md` 与 `wiki/index.md` 的反链。
3. 在 `wiki/CHANGELOG.md` 留记录；若动到 repo 结构，再在根 `CHANGELOG.md` 留记录（[[general-global-rule]] §6.6）。
4. `commit` + `push`——**守 §6.6**：先 `git status` 核对、只提交本次有意改动、禁止"一把梭"；通用内容推 `main` 再 merge 到 `ub-branch`，仅 Uber 适用的只推 `ub-branch`；Uber 机 commit message 带 `[UB]`。
5. `push` 是不可逆操作（§7），冲突时停下问用户，不擅自 `--force`。

---

## 五、接入验收清单

- [ ] repo 已 clone，分支选对（私人机 main / Uber 机 ub-branch）。
- [ ] 该 agent 开任意目录都能读到 `general-global-rule.md`。
- [ ] 能执行「开工第 0 步」：`git pull` + 本地更新 / 技能对账。
- [ ] 能写 Wiki 并成功 `git push` 到 GitHub。
- [ ] 入口文件极简、只做指针，未复制规则正文。

---

> 各 agent 的具体配置差异（命令、目录、机制）属于"本机/本 agent 上下文"，存各机 memory 或本机文档，**不写进本通用指南**——本指南只保证原则一致。
