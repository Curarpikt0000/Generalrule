# General Profile 部署清单

> 把本仓库 `蒸馏Hermes/general-hero/` 这份**蓝图**部署成 `~/.hermes/profiles/general/` 一个独立运行的 Hermes profile。
> 流程和 finance hero 完全一致；下面只列 general 特有的部分。

## 部署步骤

### Step 1 · 创建 general profile

```bash
hermes profile create general
```

Hermes 会生成 `~/.hermes/profiles/general/`，自动写好 launchd plist 在 `~/Library/LaunchAgents/ai.hermes.gateway-general.plist`，命令别名 `general` 装在 `~/.local/bin/general`。

### Step 2 · 拷贝蓝图

```bash
cd ~/hermesagent/Distill/蒸馏Hermes/general-hero && ./sync.sh
```

`sync.sh` 已含 rsync `--exclude` 规则，跳过毛泽东 repo 的 Python 工具 / 开发文档 / 测试数据等噪音。**部署到 profile 后是干净的**。

### Step 3 · 配独立 Telegram bot + API key

**新建独立 bot**（别复用 finance 或 worker 的 token）：

1. Telegram **@BotFather** `/newbot` 创建新 bot（取名如 "ChaoGeneralHero"）；记下 token。
2. **token 不要贴进任何对话**。
3. 编辑 `~/.hermes/profiles/general/.env`（推荐 `nano`）：
   ```bash
   nano ~/.hermes/profiles/general/.env
   # 加一行：TELEGRAM_BOT_TOKEN=<token>
   ```
   或用 `general setup` 引导。

### Step 4 · 关 Hindsight（MVP）

延续 finance 的决策：MVP 阶段关 Hindsight（避免 Apple Silicon daemon bug；general 是问答场景跨会话记忆需求低）。

```bash
cat ~/.hermes/profiles/general/config.yaml
# 找 memory 字段，确认 provider 是 none 或注释掉
```

### Step 5 · 启动 + 测试

```bash
general gateway start
```

Telegram 里新建 group "**通识大师 Group**"（或别的名字），把新 bot 拉进去并设管理员。

@ 它问下面任一题做烟雾测试：

| 测试题 | 预期召唤的大师 | 核心镜片 |
|---|---|---|
| "我同时想做 3 件事，精力完全不够" | 毛泽东 + 老子 + 波特 | 主要矛盾 / 不争 / 聚焦 |
| "微信封号问题怎么看" | 福柯 + 毛泽东 + 阿克洛夫 | 规则 / 利益 / 信息不对称 |
| "我刚买的股跌 30% 该不该割" | 塔勒布 + 老子 + 芒格 | 风险 / 反向 / 人性 |
| "现在 AI 这波是真革命还是泡沫" | 库恩 + 索罗斯 + 毛泽东 | 范式 / 反身性 / 主要矛盾 |

**预期产出形状**（对照 SOUL §"遇到新问题时"）：
- 主持人开场点名召唤了哪几位 + 反问澄清约束
- 3 位大师分声部发言（口吻明显不同）
- 综合裁决四问（共识 / 冲突 / 冲突根源 / 我倾向哪条路径）
- **四件套脚手架**全触发（演化位 + 同类位 + 证伪自检 + 费曼翻译）
- 免责声明一行

任一项缺失 → 把实际产出贴回 Cowork（**不要贴账号 / token**），我改蓝图重 sync。

## 与 finance 的关键差异

| 维度 | finance | general |
|---|---|---|
| profile 路径 | `~/.hermes/profiles/finance/` | `~/.hermes/profiles/general/` |
| bot | FiHeroBot | GeneralHeroBot（你新建） |
| 群 | 蒸馏大师 Group | 通识大师 Group（你新建） |
| 大师数 | 11 | 9 |
| 快答档大师数 | 2-3 | 3 |
| 快答档篇幅 | ≤500 字 | ≤700 字（脚手架占空间） |
| 脚手架 | 轻（反例自检）| **重（四件套）** |
| 数据源 | moomoo OpenD | 无（思想分析为主） |
| 免责 | 不构成投资建议 | 不构成人生建议 |

## 关于"两个 profile 互不串"

- 两个 profile 用**不同 bot**，互不接收消息
- 各自独立 launchd 服务（`ai.hermes.gateway-finance` vs `ai.hermes.gateway-general`）
- 各自独立 memory / sessions / .env
- **不要把同一个 bot token 用在两个 profile** —— Hermes 会挡掉第二个 gateway 启动

## 部署完成后的清理（可选）

蓝图 `skills/毛泽东/` 因 mao-skill repo 太重 cp 进来 200+ 文件（沙箱权限删不掉）。你本地可以：

```bash
cd ~/hermesagent/Distill/蒸馏Hermes/general-hero/skills/毛泽东
rm -rf internal tools docs prompts data
rm -f *.py requirements.txt README.de.md README.es.md README.ja.md README.ko.md README.en.md CHANGELOG.md CONTRIBUTING.md
```

部署到 profile 时 sync.sh 已 `--exclude` 这些噪音，**所以这步只是为了蓝图本身干净**，不影响运行。
