# [PROJECT_NAME] 部署清单

<!--
═══════════════════════════════════════════════════════════════
deploy.md 模板
═══════════════════════════════════════════════════════════════
填空：
  [PROJECT_NAME]    — 项目名（如 Finance Hero）
  [PROFILE_NAME]    — Hermes profile 名（如 finance）
  [BOT_NAME_SUGG]   — 建议 bot 名（如 ChaoFinanceHero）
  [GROUP_NAME_SUGG] — 建议 Telegram 群名（如"蒸馏大师 Group"）
  [BLUEPRINT_PATH]  — 蓝图绝对路径
═══════════════════════════════════════════════════════════════
-->

> 把本仓库 `[BLUEPRINT_PATH]` 这份**蓝图**部署成 `~/.hermes/profiles/[PROFILE_NAME]/` 一个独立运行的 Hermes profile。
> 用户在 Mac 本地照着跑命令；agent 不能替你执行 `hermes` CLI、配 Telegram bot token、改本机 .env。

## 部署步骤

### Step 1 · 创建 [PROFILE_NAME] profile

```bash
hermes profile create [PROFILE_NAME]
```

**预期输出**：
- profile 目录在 `~/.hermes/profiles/[PROFILE_NAME]/`
- 命令别名 `[PROFILE_NAME]` 装在 `~/.local/bin/[PROFILE_NAME]`
- launchd plist 自动写在 `~/Library/LaunchAgents/ai.hermes.gateway-[PROFILE_NAME].plist`

**验证**：
```bash
ls ~/.hermes/profiles/[PROFILE_NAME]/
hermes profile list   # 应能看到 [PROFILE_NAME]
```

### Step 2 · 用蓝图覆盖默认文件

```bash
BLUEPRINT="[BLUEPRINT_PATH]"
TARGET="$HOME/.hermes/profiles/[PROFILE_NAME]"

cp "$BLUEPRINT/SOUL.md" "$TARGET/SOUL.md"
cp -R "$BLUEPRINT/skills/." "$TARGET/skills/"
mkdir -p "$TARGET/references" && cp -R "$BLUEPRINT/references/." "$TARGET/references/"
```

**或一行**：
```bash
cd [BLUEPRINT_PATH] && ./sync.sh
```

**验证**：
```bash
head -3 ~/.hermes/profiles/[PROFILE_NAME]/SOUL.md         # 应看到 "[PROJECT_NAME] · 行为核心"
ls ~/.hermes/profiles/[PROFILE_NAME]/skills/ | wc -l       # 应 >= 阵容数
ls ~/.hermes/profiles/[PROFILE_NAME]/references/           # synthesis / depth-modes / ...
```

### Step 3 · 配独立 Telegram bot + LLM API key

每个 profile 用自己的 bot——profile 隔离的关键。

⚠️ **token 永远不要贴进任何对话框 / chat 日志**。直接在终端写文件，或用 Hermes 内置引导。

**推荐用 `[PROFILE_NAME] setup` 引导**（更安全）：
```bash
[PROFILE_NAME] setup
```

按提示配 LLM API key（如 DeepSeek / Anthropic / OpenAI）和 Telegram bot token，工具会写进 profile 的安全位置。

**或手动**：
1. Telegram **@BotFather** `/newbot` 创建新 bot（取名如 [BOT_NAME_SUGG]）
2. 写入 profile `.env`（**不要 cat 出来贴**）：
   ```bash
   nano ~/.hermes/profiles/[PROFILE_NAME]/.env
   # 加一行：TELEGRAM_BOT_TOKEN=<token>
   # 保存退出
   ```
3. Telegram 新建群 [GROUP_NAME_SUGG]，把新 bot 拉进去并设管理员

### Step 3.5 · ⚠️ 关 bot privacy mode（最容易忘的一步）

**新 bot 默认 privacy = ON** — 群里 bot 只能看 `/cmd` 和 @mention。普通"hi"它收不到。

BotFather → `/mybots` → 选你的 bot → **Bot Settings → Group Privacy → Turn off**
然后**把 bot 踢出群再加回来**让设置生效。

### Step 4 · 关 Hindsight（MVP 选项）

规避 Apple Silicon daemon 启动超时 bug ([issue #7135](https://github.com/NousResearch/hermes-agent/issues/7135))，hero 类问答场景对跨会话记忆需求低。

```bash
cat ~/.hermes/profiles/[PROFILE_NAME]/config.yaml
```

找 memory 字段，改 provider 为 none 或注释掉。

### Step 5 · 启动 + 烟雾测试

```bash
[PROFILE_NAME] gateway start
```

这会激活 launchd 守护（开机自启 + 崩溃自恢复）。

**验证**：
```bash
[PROFILE_NAME] gateway status
launchctl list | grep ai.hermes.gateway-[PROFILE_NAME]    # 应看到带 PID 的一行
```

Telegram 群里 @ 你的新 bot，问一个**真实问题**。

**预期产出形状**（对照 SOUL.md §"遇到新问题时"）：
- [视项目特化] 反问澄清处境（如适用）
- 召唤 [N] 位最相关大师，每位分声部
- 综合裁决四问全到位
- [脚手架四件套触发（如适用）]
- 反例自检 + 免责声明

任一项缺失 → 改蓝图（**别改 profile**），跑 `./sync.sh`，重测。

---

## 24h 自动运行（launchd）

Hermes 自带 launchd 集成。`[PROFILE_NAME] gateway start` 跑过一次后：
- 开机自启 ✓
- 崩溃自恢复 ✓
- 关终端不影响 ✓

**但 Mac 睡眠时 bot 也睡**（launchd 救不了睡眠状态）。三选：
1. 白天用，晚上让它睡（最省电）
2. 让 Mac 不睡：System Settings → Battery → "Prevent automatic sleeping..."
3. 迁到云/Pi（profile 可整包迁移）

---

## 常见排查

| 现象 | 检查 |
|---|---|
| bot 不响应 "hi" 但 `/start` 响应 | bot privacy mode 没关（见 Step 3.5）|
| `<name> chat` 终端能聊，Telegram 不响应 | gateway 没起 or bot 没在群里 |
| `<name> chat` 也不响应 | LLM API key 没配（`<name> setup`）|
| `gateway status` 显示 ✗ Not loaded | 跑 `<name> gateway start` 激活 |
| LastExitStatus 不是 0 | 看 logs/gateway.error.log |

```bash
tail -f ~/.hermes/profiles/[PROFILE_NAME]/logs/gateway.log         # 实时输出
tail -50 ~/.hermes/profiles/[PROFILE_NAME]/logs/gateway.error.log  # 错误
```

---

## 风险提示

- macOS Apple Silicon Hindsight daemon 启动超时 ([issue #7135](https://github.com/NousResearch/hermes-agent/issues/7135))——本部署关掉 Hindsight 规避
- bot token 冲突——两 profile 配同 token 第二个网关被挡掉
- profile 是个完整 home 目录——意味着它有自己的 API key / token / 记忆。**不要 cp worker profile 的 .env 到这里**，会污染身份隔离
