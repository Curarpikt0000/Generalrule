# Finance Profile 部署清单

> 把本仓库 `蒸馏Hermes/finance-hero/` 这份**蓝图**部署成 `~/.hermes-finance/` 一个独立运行的 Hermes profile。
> 你在 Mac 本地照着跑命令；我（Cowork 这边）不能替你执行 `hermes` CLI、配 Telegram bot token、改本机 .env。
>
> **前置假设**：你已装 Hermes Agent（NousResearch），Mac 上 `hermes --version` 能跑出版本号。如果还没装，先看 https://hermes-agent.nousresearch.com/docs/

---

## 部署步骤

### Step 1 · 创建 finance profile

```bash
hermes profile create finance
```

**实际结果**（你这版 Hermes 已确认）：
- profile 目录在 `~/.hermes/profiles/finance/`（不是 `~/.hermes-finance/`）
- 87 个 bundled skills 自动同步进 profile
- 命令别名 `finance` 装在 `~/.local/bin/finance`
- profile 的 SOUL 在 `~/.hermes/profiles/finance/SOUL.md`

**验证：**
```bash
ls ~/.hermes/profiles/finance/
hermes profile list   # 应能看到 finance
```

### Step 2 · 用蓝图覆盖默认文件

```bash
BLUEPRINT="/Users/chaojin/hermesagent/Distill/蒸馏Hermes/finance-hero"
TARGET="$HOME/.hermes/profiles/finance"

# 用我们写的 SOUL 替换默认空 SOUL
cp "$BLUEPRINT/SOUL.md" "$TARGET/SOUL.md"

# 7 位大师 skill 灌入 profile 的 skills/
# 注意：profile 里已有 87 个 bundled skills，我们的 7 位是叠加，不会冲突（名字不重）
cp -R "$BLUEPRINT/skills/." "$TARGET/skills/"

# references 整个搬过去（SOUL.md 用相对路径指它）
mkdir -p "$TARGET/references"
cp -R "$BLUEPRINT/references/." "$TARGET/references/"
```

**验证**：
```bash
head -10 ~/.hermes/profiles/finance/SOUL.md         # 应看到 "Finance Hero · 行为核心"
ls ~/.hermes/profiles/finance/skills/ | grep -E '巴菲特|格雷厄姆|利弗莫尔|索罗斯|彼得林奇|西蒙斯|德曼' | wc -l   # 应 = 7
ls ~/.hermes/profiles/finance/references/           # synthesis / depth-modes / moomoo-setup
```

### Step 3 · 配独立 Telegram bot token + API key

每个 profile 用自己的 bot——这是 profile 隔离的关键，不要复用 worker 的 token。

⚠️ **token 永远不要贴进任何对话框 / chat 日志**。直接在终端写文件，或用 Hermes 内置引导。

**推荐用 `finance setup` 引导（更安全）**：
```bash
finance setup
```
按提示配 API key（LLM provider）和 Telegram bot token，工具会写进 profile 的安全位置，无须你手敲文件路径。

**或手动方案**：
1. Telegram **@BotFather** `/newbot` 创建新 bot（取名如 "ChaoFinanceHero"）；记下 token。
2. 写入 profile `.env`（**不要 cat 出来贴**）：
   ```bash
   # 推荐：直接用编辑器开
   nano ~/.hermes/profiles/finance/.env
   # 加一行：TELEGRAM_BOT_TOKEN=<token>
   # 保存退出
   ```
3. Telegram 里新建 group 叫"Finance Hero"，把新 bot 拉进去并设管理员。

**如果 token 不小心泄露过**（贴进任何对话/issue/截图）：BotFather `/revoke` 废旧的，`/token` 换新的，再按上面流程入 .env。token 一旦在日志里就视同泄露，不要心存侥幸。

### Step 4 · 关 Hindsight（MVP 选项）

按上一轮决策，MVP 阶段不开 Hindsight（规避 Apple Silicon daemon bug；hero 是问答场景对跨会话记忆需求低）。

```bash
# 先看 profile 默认 config 长什么样
cat ~/.hermes/profiles/finance/config.yaml
```

确认 memory 插件不指向 hindsight。**§2.10 提醒**：我不知道你装的 Hermes 版本具体字段名，部署时请实查 `~/.hermes/profiles/finance/config.yaml` 现有结构 + 官方文档对照，别凭印象改。

参考字段（须以实际 yaml 结构为准核对）：
```yaml
memory:
  provider: none     # 或注释掉整个 memory 块
```

### Step 5 · 启动网关，烟雾测试

```bash
finance gateway start
```

在 Telegram 群里 @你的新 bot 问一句："**现在该持币还是买股？**"

**预期产出形状**（对照 SOUL.md §"遇到新问题时"）：
- 主持人开场点明召唤了哪几位
- 2–3 位大师分声部发言（口吻明显不同）
- 综合裁决四问（共识/冲突/根源/我押哪个）
- 反例自检一句
- 免责声明一行

任何一项缺失 → 在群里直接告诉 bot 改，并回我贴出实际产出，我帮你调 SOUL/references。

---

## 部署完成后的清理（可选）

蓝图里两个空目录 `scaffold/` 和 `data/`（沙箱权限删不掉）和废弃的 `AGENTS.md` 可以本地清掉：

```bash
cd "$BLUEPRINT"
rmdir scaffold data 2>/dev/null
# AGENTS.md 留着或删都行，留着只是一行 deprecation 提示
```

---

## 第二步：general-hero（之后做）

跑通 finance profile 后，复制同一套流程：
```bash
hermes profile create general
# 把 蒸馏Hermes/general-hero/ 蓝图（待建）部署进 ~/.hermes/profiles/general/
```
general profile 的 SOUL 会包括费曼/证伪/横纵/演化-同类四件套脚手架 + 大师库（女娲蒸馏待办）。

---

## 风险提示

- **macOS Apple Silicon Hindsight daemon 启动超时**——已知 bug（[issue #7135](https://github.com/NousResearch/hermes-agent/issues/7135)）。本部署关掉 Hindsight 规避；将来想开记忆功能时实测一下。
- **bot token 冲突**——若不小心两个 profile 配同一 token，第二个网关启动会被挡，错误信息会指明冲突 profile。
- **profile 是个完整 home 目录**——意味着它有自己的 API key、Telegram token、记忆。**不要把 worker profile 的 .env 复制到 finance profile**，会污染身份隔离。
