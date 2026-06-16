# agent-slides（Generalrule 收纳版）

从一句话 brief 生成专业 PowerPoint（`.pptx`）deck。7 个可组合子 skill + 一个 PyPI 上的 `slides` CLI（基于 `python-pptx`，确定性、agent 友好）。

- **extract** —— 从 `.pptx` 模板抽取布局/原型/色区契约。
- **build** —— 按 brief + 模板契约生成整套 deck（storytelling plan → slide ops → render → QA）。
- **edit** —— 文本编辑、布局变换、ops 补丁。
- **audit** —— 技术 lint（字体、重叠、对比度）。
- **critique** —— 叙事评审（行动标题、MECE、层级）。
- **polish** —— 收尾（备注、元数据、来源行）。
- **full** —— 端到端流水线，一条命令跑完。

## 来源与许可

- 上游：公网开源 `github.com/mpuig/agent-slides`（作者 Marc Puig），**MIT** 许可，见 `LICENSE`。
- 属通用 skill（脱离任何公司/项目仍成立：做 PPT），符合 `self-skill/` 准入。无 Uber 专有内容。

## 运行时依赖

- 本机需有 `uv`（含 `uvx`）+ Python 3.12+。子 skill 中所有命令形如 `uvx --from agent-slides slides ...`，`uvx` 会按需从 PyPI 拉取 `agent-slides` 包并置备 3.12 运行环境。
- 该包运行时依赖：`python-pptx`、`lxml`、`pydantic`、`typing-extensions`。**纯本地生成 `.pptx`，无遥测、无外部网络写入**（源码内出现的 http(s) URL 均为 OpenXML 命名空间与 JSON-schema `$id`，不在运行时抓取）。

## 与上游的差异（为什么改）

为适配本体系（`self-skill/` 通用收纳处）做了**最小化**改造：
- ✅ 只 vendoring **skill 定义**（`skills/` 下 7 个子 skill 的 SKILL.md + references）+ 顶层 orchestrator `SKILL.md` + `LICENSE`。
- ❌ **不 vendoring `src/`（Python CLI 引擎）、`tests/`、`uv.lock`、`website/`、`.github/`、`examples/*.pptx`、`pyproject.toml`**——见下。
- ✅ 顶层 `SKILL.md` 改为指向 `skills/<name>/SKILL.md`（保留上游目录结构，未走上游 `package-skills.sh` 的 references 扁平化）。
- ✅ 中文 frontmatter 描述 + 体系准入/登记指针，对齐 `self-skill/` 既有 skill（llm-wiki / webworms）。

### 为什么不 vendoring `src/`

子 skill 全部通过 `uvx --from agent-slides slides ...` 调用，**始终从 PyPI 拉取已发布的 `agent-slides` 包**——vendoring 一份 `src/` 不会改变这个行为，只会让本仓库平白多背一整个 Python 包 + 130KB `uv.lock`，与「本仓库是规则/wiki/skill-源 仓库、不是代码仓库」的定位冲突。故只收 skill 定义，CLI 走 PyPI。

> 若将来需要离线/钉版本运行，可在取用机上 `uv pip install agent-slides==<version>` 或 `pipx install agent-slides`，再把子 skill 里的 `uvx --from agent-slides slides` 换成 `slides`。

## 用法

各 agent 取用时：把本目录 `self-skill/agent-slides/` 整目录拷到自己的 skill 目录（如 `~/.agents/skills/` 或 `~/.claude/skills/`），确保本机有 `uv`，然后在 agent 里调用 `/agent-slides`（或直接读 `skills/<name>/SKILL.md` 按流程走）。无需 config 文件。

## 准入与登记

本 skill 属于 `self-skill/` 通用收纳处，准入与登记规则见上级 `self-skill/README.md`；通用 copy/authoring 手册见 `self-skill/AUTHORING.md`。已登记于 `wiki/agent-rules/skill-register.md` §8 与根 `CHANGELOG.md`。
