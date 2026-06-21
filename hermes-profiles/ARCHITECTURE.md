# Hermes Profile 架构机制：SOUL 与 Profile 如何匹配

> 本文解释 Hermes Agent 的 **profile 隔离机制**、**SOUL.md 的角色**、以及"议会模式人格蒸馏"如何利用它们实现多角色隔离。

---

## 1. Hermes Profile 是什么

根据 [Hermes 官方文档](https://hermes-agent.nousresearch.com/docs/)：

> *"A profile is a separate Hermes home directory. Each profile gets its own directory containing its own config.yaml, .env, SOUL.md, memories, sessions, skills, cron jobs, and state database."*

**实测路径**：`~/.hermes/profiles/<name>/`

**是什么**：一个完整的、隔离的 Hermes Agent 运行环境，包含：

| 组件 | 路径 | 作用 |
|---|---|---|
| SOUL.md | `~/.hermes/profiles/<name>/SOUL.md` | 行为核心，每次消息作为系统提示注入 |
| config.yaml | `~/.hermes/profiles/<name>/config.yaml` | 模型/provider/工具/网关配置 |
| .env | `~/.hermes/profiles/<name>/.env` | API key、Telegram token 等密钥 |
| skills/ | `~/.hermes/profiles/<name>/skills/` | 知识库（bundled + 自定义） |
| memories/ | `~/.hermes/profiles/<name>/memories/MEMORY.md` | 持久化记忆 |
| sessions/ | `~/.hermes/profiles/<name>/sessions/` | 对话历史 |
| cron/ | `~/.hermes/profiles/<name>/cron/` | 定时任务 |

### 与传统方案的关键区别

| | 单 Hermes + AGENTS.md 覆盖 | Hermes Profile 隔离 |
|---|---|---|
| 身份切换方式 | 在 channel 内用 prompt 覆盖 | 每个 profile 自带独立 bot + SOUL |
| 记忆污染 | 一个记忆池混多个角色 | 各自独立 memory，互不污染 |
| Telegram bot | 一个 bot 处理所有场景 | 每个 profile 一个 bot，各自一个群 |
| skill 冲突 | 所有 skill 塞一起 | 每个 profile 只装需要的 skill |
| 网关 | 单个网关 | 每个 profile 独立 launchd 服务 |

---

## 2. SOUL.md 的角色

SOUL.md 是 profile 的**行为核心**。Hermes 在每条消息（每个 turn）的 system prompt 中自动注入 SOUL.md 内容。

### SOUL.md 包含什么

在一个议会模式的 SOUL.md 中，必须写的几块：

1. **身份声明** — "你是谁？召谁？怎么召？"
2. **沟通规则** — 语言、输出格式、语气、数据纪律
3. **底线** — 不可逾越的红线（如免責、防编造、数据纪律）
4. **起步开关** — 收到问题后的执行顺序（SOP）
5. **二次验证模式** — 按需触发的事实核查机制
6. **指针** — 指向 skill/*.md、references/、上游规则
7. **改动纪律** — 改蓝图→跑 sync.sh，禁止直接改 profile
8. **文件系统纪律** — 哪些目录可读写，哪些绝对禁止

### 加载流程

```
用户问题 → Hermes Gateway 接收
  → system prompt 前缀注入 SOUL.md
  → 读到 "大师思维定义在 skills/<大师>/SKILL.md"
  → 动态加载对应 skill
  → 按 SOUL.md §"遇到新问题时" 的 SOP 执行
  → 分声部（大师）→ 综合裁决 → 反例自检 → 免責行 → 输出
```

---

## 3. 蓝图 ↔ Profile SSOT 同步模型

这是本项目耗时最长的架构决策之一。最终方案：

```
蒸馏Hermes/<project>-hero/     ← 蓝图（版本受控源，SSOT）
        │
        │  ./sync.sh (一键同步)
        ▼
~/.hermes/profiles/<name>/     ← 部署结果（运行时）
```

**铁律**：永远改蓝图 → 跑 sync.sh → 自动重启网关生效。

**禁止**直接修改 `~/.hermes/profiles/[name]/*` 里的 SOUL.md / skills / references。如果直接改了，下次 sync 会被覆盖，git 也跟踪不到。

### sync.sh 做什么

```
[1/5] 同步 SOUL.md               → cp 蓝图 SOUL.md 到 profile
[2/5] 同步 skills/               → rsync 大师 skill 到 profile skills/
[3/5] 同步 references/           → rsync 引用文件（--delete 同步删除）
[4/5] 同步 tools/                → rsync 辅助脚本（保留执行权限）
[5/5] 重启 finance gateway       → launchctl kickstart 或 stop/start
```

---

## 4. 三个 Profile 的隔离设计

```
~/.hermes/                         ← Worker profile（默认，工程项目）
└── SOUL.md                        工程师纪律 + "新对话 → 建工程项目结构"
└── Telegram bot: 一个 bot

~/.hermes/profiles/finance/       ← Finance Hero（金融问答）
└── SOUL.md                        投资大师议会主持人 + "新对话 → 答金融问题"
└── Telegram bot: 独立 bot（ChaoFinanceHero）
└── skills/: 11 位投资大师 SKILL.md

~/.hermes/profiles/general/       ← General Hero（人生/通识）
└── SOUL.md                        10 位伟人议会主持人 + "新对话 → 答人生问题"
└── Telegram bot: 独立 bot
└── skills/: 10 位伟人 SKILL.md
```

**三层隔离**：
- Profile 文件系统隔离（各自 config/.env/memory/sessions）
- 独立 Telegram bot（各自一个 bot，各自一个群）
- 独立 model provider（可配置不同 LLM 做不同角色）

---

## 5. 核心设计模式：议会模式 vs 独占人格

### 问题

大多数现成的 AI 人格 skill（如 Nuwa-style）设计为"独占人格扮演"——激活后 AI **完全变成那个人**，用"我"发言、不跳出角色、不混搭。

但议会模式的本质是：**多个大师同台为同一个问题作答 + 一个主持人做综合裁决**。

### 解决方案

SOUL.md 中显式写冲突覆盖声明：

> *「在本 profile 里，大师 skill 的『独占人格』规则被本文件**覆盖**：大师是**声部/分段**，不是独占接管。主持人借口吻讲段、跳出来做综合裁决。」*

这行声明解决了：
- 大师抢 EXIT TRIGGER 的混乱
- 没有主持人视角的问题
- 无法收敛到结论的问题

### 声部结构

```
主持人开场（身份+召唤了谁）
├── 大师 1：巴菲特声部（用"我"）
├── 大师 2：利弗莫尔声部（用"我"）
├── 大师 3：塔勒布声部（用"我"）
└── 主持人综合裁决
    ├── 共识
    ├── 冲突
    ├── 冲突根源（时间位 vs 风险偏好 vs 前提假设）
    ├── 我押哪个（结合提问者约束）
    └── 反例自检
└── 免責行
```

---

## 6. 数据纪律与防编造

所有引用数据必须：

1. **附来源 + 日期 + 原始值**（如：`2026-06-01 SPX PE=24.3 (multpl.com)`）
2. **取不到就说"未取到"**，禁止用印象填
3. **引用大师具体观点时**，必须能回溯到 `skills/<大师>/references/` 中的公开著作/访谈
4. **行情数字不编** — 通过 moomoo API 或 web fallback 获取，取不到就空着

上游规范：General Global Rule §2.10（显式失败优先于编造）。

---

## 7. Profile 命令与运维

```bash
# 创建一个新 profile
hermes profile create <name>       # → ~/.hermes/profiles/<name>/
                                    # → ~/.local/bin/<name>   (CLI 别名)
                                    # → 自动生成 launchd plist

# 列出所有 profile
hermes profile list

# 启动/停止网关
<name> gateway start
<name> gateway stop

# 查看日志
<name> gateway logs

# 删除 profile
hermes profile delete <name>
```

相关链接：
- Hermes 官方文档：[https://hermes-agent.nousresearch.com/docs](https://hermes-agent.nousresearch.com/docs)
- 蒸馏手册：`handbook/DISTILLATION-HANDBOOK.md`
- 议会机制详解：`MECHANISM-DESIGN.md`
