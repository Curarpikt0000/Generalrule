# UB 工作机初始化 — Handover 文档

> 给 Claude Cowork 的交接文档。
> 目标：在公司电脑（UB）上搭建与本地 Mac 一致的规则体系、workflow、wiki 写入机制，所有文件路径加 UB 前缀。
> 最终效果：三个 Agent（Claude Code / Claude Desktop / Antigravity）在公司电脑上和本地 Mac 遵守相同的纪律，learning 写入同一个 Wiki，git push 到同一 GitHub 账号。

---

## 一、用户 GitHub 账号

- GitHub: `curarpikt0000`
- 要 clone 的 repo: `Generalrule` (git@github.com:Curarpikt0000/Generalrule.git)

## 二、最终目录结构（本地 Mac 对照 vs UB 目标）

| 本地 Mac 路径 | UB 目标路径 |
|---|---|
| `~/Antigravity Projects/Generalrule/` | `~/UBAntigravity Projects/UBGeneralrule/` |
| `~/Antigravity Projects/COMEX-Metal-Daily/` | `~/UBAntigravity Projects/UBCOMEX-Metal-Daily/` |
| 内部文件：直接 copy，不重命名 | 内部文件：直接 copy，不重命名 |

**核心规则**：只有顶层「Antigravity Projects」和「Generalrule」等文件夹名加 `UB` 前缀。**内部文件（general-global-rule.md、wiki/ 下所有文件、AGENTS.md 等）路径中的 `Antigravity Projects/Generalrule/` 要更新为 `UBAntigravity Projects/UBGeneralrule/`**，但文件名本身不变。

## 三、需要完成的三个任务

### 任务 1：文件同步 + Git Clone

把本地 Mac 的 `~/Antigravity Projects/Generalrule/` clone 到 UB 电脑的 `~/UBAntigravity Projects/UBGeneralrule/`

步骤：
1. 在 UB 电脑上创建 `~/UBAntigravity Projects/` 目录
2. `git clone git@github.com:Curarpikt0000/Generalrule.git ~/UBAntigravity Projects/UBGeneralrule/`
3. 后续 Agent 配置（Claude Code、Antigravity）全部指向这个路径

### 任务 2：Claude Code 配置（cowork 做）

让 Claude Code 在公司电脑上遵守通用全局规则。

关键操作：
1. 配置 `~/.claude/` 下的 CLAUDE.md 或 project 规则，指向 `~/UBAntigravity Projects/UBGeneralrule/antigravity/general-global-rule.md`
2. 确保每个新建项目自动读取该全局规则
3. 配置 Wiki 写入能力：当 Claude Code 学到的 lesson 写入 `~/UBAntigravity Projects/UBGeneralrule/wiki/` 并执行 git commit & push

> 注意：Claude Code 默认找 `CLAUDE.md`。本项目模板建议 `AGENTS.md` + `ln -s AGENTS.md CLAUDE.md`。这个符号链接方案也要在 UB 上保持一致。

### 任务 3：Antigravity 配置（cowork 做）

Antigravity 是 Claude Desktop 的 Custom Instructions + Workflows 组合。需要：
1. 在 Claude Desktop 的 Custom Instructions 里写入指向 `~/UBAntigravity Projects/UBGeneralrule/antigravity/general-global-rule.md` 的指针
2. 配置 Workflows 使其遵守同一套五阶段 workflow
3. 配置 Antigravity 的 wiki 写入能力：学习到 lesson 后写入 `~/UBAntigravity Projects/UBGeneralrule/wiki/` 并 git push

---

## 四、关键资源指针（全部需要 UB 化路径）

| 资源 | 本地路径 | UB 路径 |
|---|---|---|
| 全局规则 | `~/Antigravity Projects/Generalrule/antigravity/general-global-rule.md` | `~/UBAntigravity Projects/UBGeneralrule/antigravity/general-global-rule.md` |
| Wiki | `~/Antigravity Projects/Generalrule/wiki/` | `~/UBAntigravity Projects/UBGeneralrule/wiki/` |
| Wiki Ingest 指南 | `wiki/agent-rules/wiki-ingest-guide.md` | （同上，相对路径不变） |
| 项目模板 | `wiki/agent-rules/project-template.md` | （同上） |
| AGENTS.md 模板 | `wiki/agent-rules/AGENTS-template.md` | （同上） |

---

## 五、关于 git push

- 只有 Generalrule repo 需要 git push
- 所有 Agent（Claude Code / Desktop Antigravity）学到 lesson 写入 Wiki 后，都要 `cd ~/UBAntigravity Projects/UBGeneralrule && git add -A && git commit -m "..." && git push`
- git commit 格式参考现有 log：`[Wiki] <领域>: <描述>`
- 本 repo 的 origin 已经是 `git@github.com:Curarpikt0000/Generalrule.git`，clone 下来直接可用

---

## 六、难点与注意

1. **路径更新**：clone 下来后，Generalrule 内部的所有文件路径引用还是指向 `~/Antigravity Projects/Generalrule/`。需要做 sed 替换：`~/Antigravity Projects/Generalrule/` → `~/UBAntigravity Projects/UBGeneralrule/`
2. **符号链接**：Claude Code 要 `AGENTS.md ──symlink──> CLAUDE.md`，这个在 UB 上也要做
3. **Claude Desktop Custom Instructions** 里引用绝对路径时要注意指向 UB 路径
4. **首次 git push**：clone 下来的 repo 可能已经落后了，push 前先 `git pull --rebase`

---

## 七、流程协作方式

- Cowork 作为总协调，负责分解任务、指定 Antigravity 和 Claude Code 各自做哪部分
- Cowork 也负责验收：检查 UB 电脑上的路径是否正确、Agent 是否能读到规则、wiki 写入是否可用
- **不要直接改本地 Mac 上的任何东西**

---

## 八、交付标准

- [ ] `~/UBAntigravity Projects/UBGeneralrule/` 存在，git repo 完整，内部路径已替换为 UB 版本
- [ ] Claude Code 能在 UB 电脑上读到全局规则
- [ ] Antigravity（Claude Desktop）能在 UB 电脑上读到全局规则
- [ ] Claude Code 写入 Wiki 后能 git push 到 GitHub
- [ ] Antigravity 写入 Wiki 后能 git push 到 GitHub
