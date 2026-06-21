# 议会模式人格蒸馏 Handbook

> **读者**：其他 AI agent（Claude / Hermes / Antigravity / GPT 等）准备接手或复刻 Chao 的"议会模式"人格蒸馏项目。
> **目标**：读完本文 + 抄 `templates/` 里的模板，能在 ~3 小时内完成一个新的"伟人议会 profile"——从设计到部署到 Telegram 跑起来。
> **不读这个会怎样**：你会重新踩我们已踩过的所有坑，浪费 Chao 至少 1 整天时间，且大概率做出和现有 finance/general 风格不一致的东西。
> **维护人**：Cowork Claude，2026-05-28
> **当前已实例化**：`finance-hero/`（11 位投资大师）、`general-hero/`（10 位通识伟人）

---

## 0. 这本 handbook 是什么

议会模式人格蒸馏 = **把若干个公开思想家蒸馏成可调用的 AI skill，让它们在一个 Hermes profile 里同台为同一个用户问题作答**。

四个核心组件：
1. **profile**（独立 Hermes home directory，自带 SOUL + bot + skills + memory）
2. **大师 skills**（每位一个 SKILL.md + references/，定义其镜片）
3. **主持人/编排层**（SOUL.md 定义议会规则，召谁、综合裁决怎么做、防编造）
4. **(可选) 脚手架四件套**（费曼/证伪/横纵/演化-同类，general 用，finance 没有）

读者顺序建议：
- 急用 → 跳 §6（目录结构）+ §7（部署）→ 抄 `templates/`
- 想懂为什么 → §1（架构理念）→ §3（阵容设计）→ §5（议会 4 层）
- 想避坑 → §10（lessons learned）

---

## 1. 核心架构理念（5 条铁律）

这 5 条是过去几个月反复推翻才落定的。**违反任一条，项目质量都会塌**。

### 铁律 1 · profile 是独立完整 home directory，不是数据库

**事实**（来自 [Hermes 官方文档](https://hermes-agent.nousresearch.com/docs/)）：
> "A profile is a separate Hermes home directory. Each profile gets its own directory containing its own config.yaml, .env, SOUL.md, memories, sessions, skills, cron jobs, and state database."

**实测路径**：`~/.hermes/profiles/<name>/`（不是 `~/.hermes-<name>/`）
**命令别名**：`~/.local/bin/<name>`，由 `hermes profile create <name>` 自动生成
**launchd plist**：`~/Library/LaunchAgents/ai.hermes.gateway-<name>.plist`，Hermes 自动写好

**不要**：自己写 launchd plist、把人格塞进 Hindsight 记忆、共用 bot token、在 worker profile 里搞议会。

### 铁律 2 · 蓝图 ↔ profile SSOT 同步

```
蒸馏Hermes/<project>-hero/   ← 蓝图（git 跟踪、版本受控、SSOT）
        │
        │  ./sync.sh
        ▼
~/.hermes/profiles/<name>/   ← 部署结果
```

**永远改蓝图，跑 sync.sh**。**禁止直接改 profile 内文件**——会绕过 git，下次部署冲掉。Hermes 自己有终端权限可以那么干，纪律上不允许。

SOUL.md 里写一段「改动我自己时」明确告诉 bot 这条纪律（见 `templates/SOUL.template.md`）。

### 铁律 3 · 1 profile = 1 bot = 1 Telegram 群

- 两个 bot 塞同一群 → 抢答（privacy mode on/off 都救不了）
- 一个 bot 跨多群 → 上下文容易串
- profile 隔离 + 群隔离 + bot 隔离**三层一致**，才干净

新 bot 用 BotFather 单独建，token 写入 `~/.hermes/profiles/<name>/.env`。**token 永远不进任何对话框**。

### 铁律 4 · 大师 skill 的"独占人格" vs 议会"声部"的显式覆盖

绝大多数现成 nuwa 风格 skill 都写着「激活后独占人格、用『我』、不跳出角色」。但议会模式要的是**多位同台 + 综合裁决**——综合裁决本质是 meta 分析。

**显式冲突处理**（§2.5）：SOUL.md §身份段必须明确写：
> 「在本 profile 里，大师 skill 的『独占人格』规则被本文件**覆盖**：大师是**声部/分段**，不是独占接管。主持人借口吻讲段、跳出来做综合裁决。」

不写这条，bot 会陷入"每位大师都想要 EXIT TRIGGER"的混乱。

### 铁律 5 · 防编造 = references/ + 免责 + §2.10 数据纪律

- 每位大师必须自带 `references/research.md`（或女娲六层 references/01-05）——bot 引用具体观点时必须能回查
- SOUL.md 必带免责：「**用各位大师的思维框架做的模拟，非本人真实发言，也不构成 [投资/人生] 建议**」
- 引用数据必须附**日期 + 来源 + 原始数值**；取不到就说"未取到"，禁止用印象填

手蒸馏的大师必须现场跑 WebSearch 抓真实公开材料，**禁止凭训练记忆瞎写**——质量会塌且无法溯源。

---

## 2. 全流程 SOP（从想法到 bot 跑起来）

按以下 8 步走，不许跳。

### Step 1 · EXPLORE（澄清需求）

回答 4 个问题：
1. **场景**：金融分析？人生决策？产品设计？特定行业咨询？——决定 profile 的"灵魂偏向"
2. **大师人选**（候选名单）：每人锁一个**独家镜片**，互不重叠（详 §3）
3. **是否需要脚手架**：general-hero 有四件套（费曼/证伪/横纵/演化-同类），finance-hero 只有轻量反例自检。看场景需要
4. **是否需要实时数据源**：finance 有 moomoo，general 没有；如有，单独写 references/`<data-source>`-setup.md

用 AskUserQuestion（如你是 Claude）或类似机制和用户敲定这 4 项。**别替用户拍板核心人选**。

### Step 2 · PLAN（写计划过硬门）

产出书面计划，包含：
- 目录结构（参考 §6）
- 大师阵容（6-12 位最佳）
- 蒸馏路径每位归到哪条（复用 / GitHub / 女娲 / 手蒸馏）
- 验收标准（"用某真实问题跑一遍应得到 X 形状"）
- 复杂度 / TDD（默认豁免，内容生成类）

**计划必须经用户明确批准才能进 EXECUTE**（Global Rule §4 硬门）。别问"可以了吗"，要列出来给批。

### Step 3 · 收大师（蒸馏路径决策树）

按 ROI 顺序：

**路径 A · 复用已有 profile 的大师**（最快）
某位大师如果别的 profile 已经做了，直接 cp。注意 profile 隔离不"共享"——每个 profile 留独立副本。
```bash
cp -R ../finance-hero/skills/芒格 ./skills/芒格
```

**路径 B · clone GitHub 现成 nuwa 风格 skill**
查这些索引：
- [tmstack/awesome-persona-skills](https://github.com/tmstack/awesome-persona-skills) — 综合索引
- [alchaincyf/nuwa-skill/examples/](https://github.com/alchaincyf/nuwa-skill/tree/main/examples) — 13+ 位 nuwa 产物
- [Cat-Geek/investment-master-mindset](https://github.com/Cat-Geek/investment-master-mindset) — 8 位投资大师
- 个别独立 repo：[alchaincyf/munger-skill](https://github.com/alchaincyf/munger-skill) / [taleb-skill](https://github.com/alchaincyf/taleb-skill) / [derrickgong87/duan-yongping-skill](https://github.com/derrickgong87/duan-yongping-skill) / [wwwaapplleecu-source/mao-skill](https://github.com/wwwaapplleecu-source/mao-skill)

```bash
git clone --depth 1 <repo>.git /tmp/<name>
rsync -a --exclude='.git' --exclude='.github' /tmp/<name>/ ./skills/<中文名>/
```

**⚠️ mao-skill 警告**：那个 repo 200+ 文件，含 Python 工具/开发文档/测试数据。**必须**在 sync.sh 里 rsync `--exclude` 排掉 `internal/ tools/ docs/ prompts/ data/ *.py requirements.txt`。

**路径 C · 用户本地跑女娲 nuwa-skill**
适用：用户有 Claude Code + 装了 nuwa-skill + 愿意付出蒸馏时间。
```
> 蒸馏一个 [人名]
```
女娲会跑 6 路调研 + 三重验证 + 生成 SKILL.md + references/。质量最稳但慢。

**路径 D · agent 手蒸馏（Cowork 风格）**
适用：没现成、用户不想跑女娲。流程：
1. 5-10 次 WebSearch 抓公开材料（书 / 论文 / 演讲 / 著名访谈）
2. 按 `templates/master-SKILL.template.md` 填空
3. 写 `references/research.md` 列**真实出处**（每条带 URL / ISBN）
4. 标注「Cowork 手蒸馏」并诚实交代质量与女娲版差距

每位约 30-45 分钟。

### Step 4 · 写主持人 SOUL.md

抄 `templates/SOUL.template.md`，填 7 处：身份 / 大师阵容 / 沟通规则 / 底线 / 起步开关 / 指针 / 改动纪律。

**身份段必须显式覆盖大师"独占人格"规则**（铁律 4）。

### Step 5 · 写议会 4 层

- `references/synthesis.md`（综合裁决四问，见 §5.2）
- `references/depth-modes.md`（快答 vs 全议会档 + 召唤映射表）
- （如有脚手架）`references/scaffold-*.md`

### Step 6 · 写部署三件套

- `sync.sh` — 抄 `templates/sync.sh.template`，改路径
- `deploy.md` — 抄 `templates/deploy.template.md`，改 profile 名字 / bot 名字 / 群名
- `README.md` — 抄 `templates/README.template.md`，列阵容表

### Step 7 · 部署（用户在 Mac 本地跑）

```bash
hermes profile create <name>           # 自动建目录 + launchd plist + 命令别名
cd 蒸馏Hermes/<project>-hero && ./sync.sh
<name> setup                            # 配 LLM API key + Telegram bot token
# 在 BotFather: /mybots → Bot Settings → Group Privacy → Turn OFF (新 bot 默认 ON！)
<name> gateway start                    # 激活 launchd 守护
```

Telegram 新建群，把新 bot 拉进去并设管理员，@ 它问一道**真实问题**做烟雾测试。

### Step 8 · VERIFY + LEARN

烟雾测试至少 3 道不同类型的真实问题，验证：
- 召唤大师符合 depth-modes 映射？
- 综合裁决四问全到位？
- (general) 四件套脚手架都"看得见"？
- 篇幅在规定上限内？
- 引用真实出处，没编造？
- 免责声明？

任一项不达标 → 改蓝图（不改 profile）→ sync.sh → 重测。

收尾 LEARN：把这次项目经验沉淀到 Wiki 的 `agent-rules/<name>-distillation.md`（参考 `wiki-output/agent-rules/finance-hero-distillation.md`）。

---

## 3. 大师阵容设计

### 三条强约束

1. **每人一个独家镜片**：写下每位的"招牌核心问"，互相对比——如果两位的核心问看起来很像，**砍掉一位或重新定位**。
2. **必须有冲突源**：阵容里至少要有 2-3 对"立场相反"的大师，否则综合裁决会变成"大家都同意"——无综合价值。
   - finance 例：巴菲特（等）vs 利弗莫尔（追势）vs 索罗斯（拐点）
   - general 例：老子（不争）vs 毛泽东（斗争）；乔布斯（极致取舍）vs 老子（顺其自然）
3. **6-12 位是甜区**：< 6 维度不足；> 12 难触发对比 + 蒸馏成本太高 + 用户记不住。

### 怎么选

按"维度全覆盖"原则。一些常用维度大类：

| 维度 | 候选大师 |
|---|---|
| 价值/商业 | 巴菲特、格雷厄姆、彼得·林奇、段永平 |
| 风险/反脆弱 | 塔勒布、霍华德·马克斯 |
| 反向/多元思维 | 芒格 |
| 趋势/择时 | 利弗莫尔、索罗斯 |
| 量化/模型 | 西蒙斯、德曼 |
| 范式/演化 | 库恩 |
| 顺势/不争（东方） | 老子、王阳明 |
| 权力/规则 | 福柯 |
| 竞争/定位 | 波特 |
| 信息/信号 | 阿克洛夫 |
| 博弈/动力 | 毛泽东 |
| 第一性/翻译 | 费曼 |
| 产品/极简取舍 | 乔布斯 |
| 行为金融/认知偏误 | 卡尼曼、塞勒 |
| 宏观/债务周期 | 达里奥 |

### 阵容不重叠的检查方法

每位写完 SKILL.md 后，把所有人的"招牌核心问"贴到一张表里。**如果两位的核心问字面太像（如两位都问"风险在哪"），就有重叠**——重新定位或砍一位。

---

## 4. 蒸馏路径决策树（图）

```
用户提到一位大师
       │
       ▼
┌─ 是不是已经在别的 profile 里？ ── 是 ──▶ cp 复用（30 秒）
│                                       └─ 注意 profile 隔离，留独立副本
否
│
▼
┌─ 是不是在 awesome-persona-skills / nuwa examples / 个人 nuwa repo 里？
│   ├─ 是 ──▶ git clone（5 分钟）
│   │       └─ 注意 mao-skill 类重 repo 要 rsync --exclude
否
│
▼
┌─ 用户有 Claude Code + 装了 nuwa-skill + 愿意跑？
│   ├─ 是 ──▶ 用户本地跑女娲（30-45 分钟/位，自动）
否
│
▼
└─ Agent 手蒸馏（30-45 分钟/位，手动）
    1. WebSearch 5-10 次抓公开材料
    2. 按 templates/master-SKILL.template.md 填
    3. 写 references/research.md 列真实出处
    4. 诚实标注「手蒸馏，质量参考 SEP / Wikipedia / 原著」
```

---

## 5. 议会模式 4 层架构

### 5.1 大师层（声部）

每位大师 = 一个 SKILL.md 文件夹（详 `templates/master-SKILL.template.md`）。
关键：**SOUL.md 必须显式覆盖大师 skill 里"独占人格"的规则**——把他们降格为"段落级别声部"，主持人随时切回 meta 视角做综合。

### 5.2 综合裁决层（强制四问）

每次回答**末尾必须收**这一段：

1. **共识** — 撇开口吻差异，他们底层共同认可的是什么？
2. **冲突** — 他们在哪一步给出相反指令？指名道姓。
3. **冲突根源** — 必须归到下面**三类之一**（不含糊）：
   - **时间位不同**（短期 vs 长期）
   - **关注层级不同**（个体 vs 系统 / 当事人 vs 旁观结构 / 行业层 vs 产品层）
   - **前提假设不同**（信息对称、人是否理性、目标是什么）
4. **对你这个处境我倾向哪条路径** — 结合用户的**具体约束**给立场：
   - "在你的约束下，我更倾向 [大师 X 的路径]，因为……"
   - **敢取舍，不和稀泥**

反模式：「每位大师都有道理，要结合自身情况」——等于没裁决。

### 5.3 深度档位（防爆篇幅）

| 档 | 触发 | 大师数 | 篇幅 |
|---|---|---|---|
| **快答**（默认）| 普通提问 | 2-3 位（视议会规模）| 软上限 700 字 / 硬上限 1000 字 |
| **全议会** | "开会" / "全维度" / "详细点" | 相关全员 | 不限 |

**复杂题口子**：超 1000 字 bot **必须显式报告**："这题复杂，我需要 X 字才能负责任地讲清——介意继续吗？"——不偷偷超字数（§2.10 显式失败的篇幅版）。

完整召唤映射模板见 `templates/depth-modes.template.md`。

### 5.4 反例自检（必带）

综合裁决后**必须**带一段：

> "**这个结论最可能错在哪？什么反例会让它翻车？**"

固定回答两件事：
- 我最可能错在哪个**具体前提**？
- 什么**具体反例情境**会让结论崩？

不许"宽泛地说可能不对"——要指名前提 + 给反例。

### 5.5 (general 专属) 四件套脚手架

general 类问题（人生 / 困境 / 眼光 / 境界）多用一层强化：

1. **费曼翻译层** — 讲给 5 岁小孩 + 6 步讲述训练
2. **波普尔/塔勒布证伪自检** — 即上面 5.4，但 general 中是独立要素
3. **索绪尔历时/共时横纵** — 时间维 + 空间维双扫
4. **演化 + 同类强制辅维** — 借库恩 + 波特镜片

四件套要"看得见"——**不许隐性压缩进某位大师发言里**，必须独立段落。

finance 类不需要四件套——金融分析有更直接的数据驱动结构，硬塞会冗余。

---

## 6. 目录结构 + 文件清单

### 蓝图根目录（git 跟踪）

```
蒸馏Hermes/<project>-hero/
├── SOUL.md                              # 主持人行为根（profile 装这个）
├── README.md                            # 蓝图说明 + 阵容表
├── deploy.md                            # 本地部署清单
├── sync.sh                              # 蓝图→profile 同步脚本
├── skills/                              # 大师库
│   └── <大师中文名>/
│       ├── SKILL.md                     # 主入口
│       └── references/
│           ├── research.md              # 手蒸馏需要：真实出处
│           └── (若来自女娲: 6 个 references/01-06.md)
└── references/                          # 议会层 + 脚手架
    ├── synthesis.md                     # 综合裁决四问
    ├── depth-modes.md                   # 快答 vs 全议会 + 召唤映射
    ├── (data-source 接入说明, 如适用)    # 如 moomoo-setup.md
    └── (general 专属:)
        ├── scaffold-feynman.md
        ├── scaffold-falsification.md
        ├── scaffold-saussure.md
        └── scaffold-evolution-peer.md
```

### Profile 部署目录（Hermes 管理，sync 写入）

```
~/.hermes/profiles/<name>/
├── SOUL.md          ← cp 自蓝图
├── skills/          ← rsync 自蓝图（--exclude 噪音）
├── references/      ← rsync 自蓝图
├── config.yaml      ← Hermes 生成
├── .env             ← 用户手填 token / API key
├── memories/        ← Hermes 生成
├── sessions/        ← Hermes 生成
└── logs/            ← Hermes 写
```

每个文件的 template 见 `templates/`。

---

## 7. 部署到 Hermes profile（用户本地执行）

完整流程在每个项目的 `deploy.md` 里，关键步骤：

```bash
# 1. 创 profile（Hermes 自动建目录 + plist + 命令别名）
hermes profile create <name>

# 2. 拷贝蓝图
cd ~/hermesagent/Distill/蒸馏Hermes/<project>-hero && ./sync.sh

# 3. 配 LLM key + bot token（推荐 setup 引导，避免泄露 token）
<name> setup
# 或手动：nano ~/.hermes/profiles/<name>/.env

# 4. 关 Hindsight（MVP，规避 Apple Silicon 已知 bug #7135）
cat ~/.hermes/profiles/<name>/config.yaml
# 找 memory 字段改 provider 为 none

# 5. BotFather 关 bot privacy
# /mybots → Bot Settings → Group Privacy → Turn OFF
# 然后把 bot 踢出群再加回来让设置生效

# 6. 启动 launchd 守护（Hermes 自带 plist）
<name> gateway start

# 7. 验证
<name> gateway status
launchctl list | grep ai.hermes.gateway-<name>
```

详细 Mac 操作清单见 `templates/deploy.template.md`。

---

## 8. 篇幅 / 触发 / 扩展纪律

### 篇幅
- 快答：软 700 / 硬 1000（general 是 700/1000，finance 可压到 500）
- 全议会：不限但每位落到问题上
- 超硬上限：bot **显式报告**，不偷偷超

### 触发关键词（用户在群里说）
| 用户说 | bot 行为 |
|---|---|
| 普通问句 | 快答档 |
| "开会" / "全维度" / "N 个都说说" / "详细点" | 全议会档 |
| "用 X 视角看" | 单一大师 |
| "请 X、Y、Z 看" | 指定阵容 |
| "别召 X 上" | 排除 |
| "退出" / "切回正常" / "跳出角色" | 大师 EXIT TRIGGER（如果某位太入戏脱不出来）|

### 扩展（加新大师 / 改综合层）
- **永久结构性改动** → 改蓝图 → sync.sh
- **当场临时调整**（"这次只用 2 位"）→ 用户直接在群里说 → bot 当次遵守，不进 git
- **加新大师** → 走蒸馏路径决策树 → cp 进 `skills/` → 改 SOUL 阵容 + depth-modes 召唤映射 → sync

---

## 9. 防编造纪律（铁律 5 的展开）

### references/ 的强制
- 每位大师 SKILL.md 必须**配套** references/——女娲版有 6 个 `01-06.md`，手蒸馏版至少有 `research.md` 列真实出处
- 引用大师具体观点时，**必要时回查 references/**
- SOUL.md 底线段必须写：「**不替大师编造观点。引用具体判断限于其公开著作/访谈中真实表达过的**」

### §2.10 数据纪律
finance 类涉及行情、估值时**强制**：
- 引用数字必带 **日期 + 接口名 + 原始片段**
- 取不到就写"数据未取到"，**禁止用"大概""最近"糊弄**

### 免责声明
SOUL.md 每次回答末尾必带：
- finance：「**用各位大师的思维框架做的模拟，非本人真实发言，也不构成投资建议**」
- general：「**用各位大师的思维框架做的模拟，非本人真实发言，也不构成人生建议；最终判断在你**」

---

## 10. 踩坑清单（lessons learned，按重要性排）

### 部署
1. **新 bot 默认 privacy ON** — BotFather 里关掉，否则群里普通消息 bot 收不到
2. **bot token 永远不要贴对话框** — 任何对话/截图/issue 都视同泄露 → BotFather `/revoke` + `/token`
3. **`<name> gateway start` 必须跑一次** — Hermes 写好了 plist 但需要首次启动激活 launchd
4. **launchd 是醒着时守护** — Mac 睡眠 bot 也睡；要真 24h 需 Mac 不睡或上云
5. **Apple Silicon Hindsight daemon bug #7135** — MVP 先关 Hindsight

### Profile / 路径
6. **实际路径是 `~/.hermes/profiles/<name>/`** — 不是 `~/.hermes-<name>/`，官方文档有误传
7. **mao-skill repo 太重** — sync.sh 必带 rsync `--exclude internal/ tools/ docs/ prompts/ data/ *.py`
8. **沙箱挂载点权限限制** — Cowork sandbox 无法 rm 已存在的旧文件；用户本地清理或靠 sync 的 exclude 兜底
9. **Hermes profile = home directory** — 不是 Hindsight DB；profile-as-feature 走 SOUL/skills 文件层，不走记忆层

### 议会设计
10. **大师"独占人格"必须显式覆盖** — 不然议会会乱（铁律 4）
11. **同方向大师太多 = 无综合价值** — 阵容必须有 2-3 对冲突源
12. **快答档默认 2-3 位** — 超过 4 位输出会爆，违反 §2.2 简单至上
13. **(general) 四件套不许隐性压缩** — 演化位/同类位必须独立明说一句
14. **(general) 转型/重大决策类问题强制反问** — SOUL Step 1 写死，不反问 = 在空气里建议
15. **综合裁决"无冲突"也要诚实说** — 不抹平真实差异，但若大师选位太同方向应该重选

### 数据
16. **finance skill ≠ 实时行情源** — Claude finance 系列 skill 是分析/会计，不拉行情；行情靠 moomoo OpenD
17. **moomoo 实时报价跟入金账户挂钩** — 免费快照够 hero 用，深度数据要权限/入金
18. **OpenD 网关必须常驻** — 不开 bot 就用 curl/网页兜底

### 工具链
19. **复用 > 蒸馏** — finance 7 位投资大师有现成 investment-master-mindset，直接用，别重做
20. **GitHub 优先于女娲优先于手蒸馏** — ROI 顺序，§3 五步链路在这条上活用
21. **Hermes 自带 launchd 集成** — 不要自己写 plist；查 `<name> gateway status` 看 Hermes plist 位置

### 网页自动化外部源集成（如 Google Finance / Perplexity 等二次验证）

议会模式天然适合"双源对账"——给综合裁决加一层独立来源验证。这是一个 hero 项目可以加的高价值增量功能。完整踩坑见 wiki `agent-rules/google-finance-research-integration.md`，下面摘要 5 大要点：

22. **优先 Playwright + 用户 Chrome profile**，不要让 bot 在沙箱里走 OAuth 登录流（Google 检测自动化会锁号/2FA 拉锯）
23. **Chrome profile 文件夹名不一定是 "Default"** — 永远先读 `Local State` JSON 查邮箱对应的文件夹名
24. **URL 不一定足够激活功能**——很多页面（如 Google Finance Beta）需要点 UI 的 toggle 才解锁 AI；写幂等 toggle 处理
25. **不要相信 [aria-live]** —— 那是给读屏者的状态公告区，不是答案。用"含用户问题文本 + 文本长度 > 80"过滤 [role="region"] 才是正解
26. **Material Symbols 图标字体陷阱**——按钮 inner_text 拿到的可能是 "expand_content" 这种图标名字面量。selector 同时用 text 和 aria-label 双保险，输出文本要剥离这些 UI noise
27. **按需触发，不污染常规问答**——SOUL.md 里写关键词列表（"再查一下" / "double check"），没说就别调；触发后必须显式标注是哪个来源

---

## 11. Wiki 沉淀

项目收尾必跑 LEARN 阶段：

1. 把本次蒸馏的**通用教训**写进共享 wiki `agent-rules/<project>-distillation.md`（参考 `wiki-output/agent-rules/finance-hero-distillation.md` 那个模板）
2. 包含：架构决策、工具选型、阵容名册、关键设计点、踩坑清单
3. 更新 `agent-rules/README.md` 索引加一行
4. git commit + push

不沉淀 → 下一个项目重新踩坑。**沉淀是议会模式能"复利累积"的关键**。

---

## 附录 A · 女娲六层在议会模式里的调整

女娲方法论（来自 [alchaincyf/nuwa-skill](https://github.com/alchaincyf/nuwa-skill)）的六层提取：

| 层 | 内容 | 议会模式调整 |
|---|---|---|
| 1. 怎么说话 | 表达 DNA | **不变**——议会需要每位口吻区分 |
| 2. 怎么想 | 心智模型 3-7 个 | **不变**——综合裁决要看冲突需要心智模型 |
| 3. 怎么判断 | 决策启发式 5-10 条 | **不变** |
| 4. 什么不做 | 反模式 / 价值观底线 | **不变** |
| 5. 知道局限 | 诚实边界 | **强化**——议会要列「与其他大师的镜片差异」一段，明确为什么需要召这位 |
| 6. (附加) 角色扮演规则 | EXIT TRIGGER / "用我" | **覆盖**——SOUL.md 显式声明此规则在议会里降级为"分段口吻"（铁律 4）|

详细模板见 `templates/master-SKILL.template.md`。

---

## 附录 B · 常用召唤映射模式

按场景写 depth-modes 召唤映射时参考：

| 问题类型（关键词识别）| 映射模式 |
|---|---|
| "X 是不是高位 / 低位 / 拐点" | 周期阶段 + 反身性 + 趋势判定 |
| "该不该买 / 卖 / 持有" | 价值（基本面）+ 趋势 + 风险 |
| "我转型行不行" | 演化阶段（库恩）+ 同类定位（波特）+ 嫁接 vs 重学（毛泽东）|
| "做选择 A 还是 B" | 主要矛盾（毛）+ 反向（芒格）+ 风险（塔勒布）|
| "这事看不清/看不透" | 第一性（费曼）+ 权力规则（福柯）+ 演化（库恩）|
| "这事很复杂" | 多元思维（芒格）+ 主要矛盾（毛）+ 翻译（费曼）|
| "怎么取舍 / 砍掉什么" | 极简（乔布斯）+ 不争（老子）+ 主要矛盾（毛泽东）|
| "为什么人不听我的" | 话语（福柯）+ 信号（阿克洛夫）+ 信任（巴菲特"复利"）|

---

## 附录 C · 当前已实例化项目

### finance-hero
- **位置**：`蒸馏Hermes/finance-hero/`
- **profile**：`~/.hermes/profiles/finance/`
- **阵容（11 位）**：巴菲特 / 格雷厄姆 / 利弗莫尔 / 索罗斯 / 彼得·林奇 / 西蒙斯 / 德曼 / 塔勒布 / 芒格 / 霍华德·马克斯 / 段永平
- **特点**：无脚手架四件套；快答档 ≤500 字；moomoo OpenD 接行情
- **wiki**：`agent-rules/finance-hero-distillation.md`

### general-hero
- **位置**：`蒸馏Hermes/general-hero/`
- **profile**：`~/.hermes/profiles/general/`
- **阵容（10 位）**：毛泽东 / 费曼 / 芒格 / 塔勒布 / 库恩 / 老子 / 福柯 / 波特 / 阿克洛夫 / 乔布斯
- **特点**：四件套脚手架（费曼/证伪/横纵/演化-同类）；快答档软 700 硬 1000；起步强制反问；无数据源
- **wiki**：(待加) `agent-rules/general-hero-distillation.md`

---

## 给读这本 handbook 的 agent 的最后一句话

**完全照模板填可以做到 80 分。剩下 20 分在两个地方**：
1. **阵容设计的眼光**——选谁、不选谁、谁的镜片真正独特。这是策展工作，不是工程。
2. **手蒸馏时的扎实度**——多搜一个出处、多对一句原文、多回查一次 references——质量差别在这里。

复用 + 模板让你跑得快，眼光和扎实让你跑得对。**两个都重要**。

如果你接手时遇到本 handbook 没覆盖的情况，按你的判断处理，**然后把决定 + 理由写回这个 handbook 的某一节**——这是议会模式自身的"复利累积"。

—— Cowork Claude，2026-05-28
