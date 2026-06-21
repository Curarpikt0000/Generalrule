# self-skill/ —— 自有通用 skill 收纳处（宪法）

> 本目录存放**经改造适配本体系的通用 skill**，供所有 agent（私人 Mac + Uber Mac/VM 上的 Claude Code / Hermes / Antigravity / Codex / Cursor，未来更多）取用。
> 本 README 是本目录的宪法。往这里放 skill 前**必读**。

---

## 一、这里放什么、不放什么

**只放通用 skill**——脱离具体公司/项目仍然成立的能力（如 wiki 写作、通用调试、通用代码审查方法论）。

**禁止放**：
- **特用 skill**：只服务某一项目/某一管道/某一公司内部系统的 skill（如某券商 API 集成、某内部平台运维）。这些留在各自项目或各 agent 自己的 skill 目录，不进本 repo。
- 含 API key / token / 凭据的文件。
- 含 Uber 专有内容（内部链接、内部流程细节、人员/业务数据）的内容（红线）。

判断准入一句话：**「把它给一台跟 Uber 无关的机器上的 agent，它还有用吗？」** 有用 → 可放；没用 → 不放。

---

## 二、怎么 copy 一个 skill 进来

1. **整目录拷入** `self-skill/<skill-name>/`（含 SKILL.md + 配置示例 + README）。
2. **去写死路径**：把任何机器绝对路径（`/Users/xxx`、`~/某固定目录`、某账号名）改成占位符 + "各 agent 按本机环境解析"的说明。分支名（main/ub-branch）等**体系约定**可保留，因为对所有 agent 通用。
3. **去凭据/内部链接**：删除 API key、token、内部 URL、Uber 专有内容。
4. **红线自检**：通读一遍，确认符合第一节准入。
5. **登记**（见第三节）。

> 注意：本目录存的是 skill 的**通用源**，不是某台机的运行副本。各 agent 取用时拷到自己的 skill 目录（如 `~/.agents/skills/` 或对应路径）并按本机填 config。

---

## 三、copy 之后必须登记（让别的 agent 找得到）

每放入/更新一个 skill，**必须**在 [`wiki/agent-rules/skill-register.md`](../wiki/agent-rules/skill-register.md) 的 **Self-Skill 区**加一行指针：

| skill | 用途（一句话） | 来源（原始 repo / 作者） | 安装/取用方式 |
|---|---|---|---|

并在根 [`CHANGELOG.md`](../CHANGELOG.md) 记一笔（新增/更新了哪个 skill、为什么）。

不登记 = 别的 agent 不知道它存在 = 白放。**登记是准入的一部分，不是可选项。**

---

## 四、当前已收纳

| skill | 用途 | 来源 | 备注 |
|---|---|---|---|
| `llm-wiki/` | 在 Generalrule 共享 wiki 上做知识复利累积（Ingest/Query/Lint+Heal），已适配本体系（纯 markdown、领域目录、方案Z frontmatter、双分支、红线门） | 改造自公网 `kingqiu/llm-wiki-skill`（vercel skills 生态） | 已去 Quartz/双语/写死路径。各 agent 写 wiki 时优先调它，统一 format |
| `webworms/` | 4 层降级回退的网页爬虫标准框架（requests+BS4 → Jina Reader → CamoFox → Crawl4AI），内置 robots.txt 合规、限速、重试 | 自有 Hermes skill 改造 | 已去写死路径。`pip install requests beautifulsoup4 lxml camoufox crawl4ai` |
| `agent-slides/` | 从 brief 生成专业 PPTX deck：7 个可组合子 skill（extract/build/edit/audit/critique/polish/full），基于 python-pptx 的确定性 CLI | 公网开源 `mpuig/agent-slides`（MIT） | 只收 skill 定义，CLI 走 PyPI（`uvx --from agent-slides`）；需本机 `uv` + Python 3.12+。无遥测/外部写入 |
| `project-context-persistence/` | 一个 agent 服务多项目时，按 topic/项目做每日上下文归档：cron 把当天对话蒸馏进项目文件夹（AGENTS.md + docs/context-log.md），新会话自动加载历史决策/事实/进展/待办。Memory-Bank 模式（Cline / CLAUDE.md 风格）在 Hermes 上的落地 | 自有 Hermes skill 改造 | 已去写死路径。含采集脚本 + cron recipe。诚实标注 state.db 不存 topic_id 的限制 |
| `hermes-profiles/handbook/` | 议会模式人格蒸馏完整方法论：从架构设计、大师阵容选择、蒸馏流程到部署。附两个完整实例（Finance Hero / General Hero）和可复用的模板集 | 自有 Cowork 蒸馏实践沉淀 | 路径：`hermes-profiles/handbook/DISTILLATION-HANDBOOK.md`（全貌）→ `QUICK-START.md`（急用）→ `templates/`（填空建新 profile） |

---

## 五、相关

- [`AUTHORING.md`](AUTHORING.md) —— 怎么写/copy 一个 skill 的操作手册（本宪法的操作配套）
- [[wiki/agent-rules/skill-register.md]] —— skill/MCP 总清单 + 对账（Self-Skill 区在此登记）
- [[wiki/agent-rules/wiki-ingest-guide.md]] —— wiki 写作规范（llm-wiki 的产出须符合）
- 根 `CHANGELOG.md` —— 任何增减留证据
- general-global-rule.md §6.5（skill 对账纪律，含本目录指针）
