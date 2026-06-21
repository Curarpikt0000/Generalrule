# 复刻指南：给你的 Hermes 也装一个"大师议会"

> **读者**：另一台机器上的 Hermes Agent、新开的 profile、或任何想复用本架构的 AI agent。
> **目标**：跟着做，约 2–3 小时跑通你自己的"大师议会" profile。

---

## 0. 前提条件

- Hermes Agent 已安装（[官方安装指南](https://hermes-agent.nousresearch.com/docs)）
- macOS（或 Linux；launchd 部分需改 crontab）
- `hermes --version` 能输出版本号

---

## 1. 快速路线图

```
30 min    选择阵容 + 设计 SOUL
   │
30 min    蒸馏/拉取大师 SKILL
   │
30 min    撰写 references/
   │
30 min    hermes profile create + 配置 bot
   │   
30 min    smoke test + 调优
   │
✓ 完成！
```

---

## 2. 第一步：设计你的议会

### 选择大师

关键原则：
- **至少 2–3 对有冲突立场的大师**（否则无辩论价值）
- **每人一个独特镜片**（不要两位大师做同一件事）
- **总人数 6–15 位**（太多输出爆炸，太少没辩论）

### 案例：Finance Hero 阵容设计逻辑

```
价值派（巴菲特、格雷厄姆、彼得·林奇、段永平）
趋势派（利弗莫尔）           ← 与价值派直接冲突
宏观派（索罗斯）             ← 独特的反身性视角
量化学者（西蒙斯、德曼）     ← 与基本面分析完全不同的范式
风险/哲学（塔勒布、芒格）    ← 反向/尾部风险视角
周期（霍华德·马克斯）        ← 时间位维度
```

每个冲突组合都有人站台：价值 vs 趋势（时间位冲突）、基本面 vs 量化（范式冲突）、进攻 vs 风险（偏好冲突）。

### 设计召唤映射

`references/depth-modes.md` 定义"什么问题召哪几位大师"：

```markdown
## 大师召唤映射表

### 问题类型 → 默认召唤组合

| 问题关键词 | 默认召唤 | 理由 |
|---|---|---|
| 该不该买/卖 | 巴菲特 + 利弗莫尔 + 塔勒布 | 价值 + 趋势 + 风险 |
| 现在市场位置 | 霍华德马克斯 + 索罗斯 + 格雷厄姆 | 周期 + 反身 + 估值 |
| 宏观利率 | 索罗斯 + 西蒙斯 + 霍华德马克斯 | 宏观 + 量化 + 周期 |
| 组合回撤/割肉 | 利弗莫尔 + 巴菲特 + 索罗斯 | 止损 + 持有 + 反身 |
| 个股基本面 | 巴菲特 + 格雷厄姆 + 段永平 | 三个价值派镜片 |

### 快答档（默认）
召 2-4 位，≤ 500 字

### 全议会档（"开会"/"全员"）
召全部 11 位，不限字数
```

---

## 3. 第二步：部署蓝图

### A. 创建 profile

```bash
# 创建新 profile，假设叫 my-hero
hermes profile create my-hero

# 验证
ls ~/.hermes/profiles/my-hero/
hermes profile list  # 应看到 my-hero
```

### B. 拷贝我们的文件

```bash
# 从本 repo 拿到文件后（假设已 git clone）
BLUEPRINT="./finance-hero"     # 或你的自定义蓝图目录
TARGET="$HOME/.hermes/profiles/my-hero"

# 替换 SOUL
cp "$BLUEPRINT/SOUL.md" "$TARGET/SOUL.md"

# 拷贝 skills（大师技能）
cp -R "$BLUEPRINT/skills/." "$TARGET/skills/"

# 拷贝 references
mkdir -p "$TARGET/references"
cp -R "$BLUEPRINT/references/." "$TARGET/references/"
```

### C. 配 Telegram bot

```bash
# 1. 在 Telegram @BotFather 创建新 bot，取名如 "MyHeroBot"
# 2. 记下 token（永远不要贴进聊天！）
# 3. 写入 profile .env
mkdir -p ~/.hermes/profiles/my-hero
nano ~/.hermes/profiles/my-hero/.env
# 添加: TELEGRAM_BOT_TOKEN=xxx:yyy

# 或用 Hermes 引导（更安全）
my-hero setup
```

### D. 启动

```bash
my-hero gateway start
```

---

## 4. 第三步：烟雾测试

在你的 Telegram 群里 @bot 问几个关键问题：

| 测试 | 预期 | 检什么 |
|---|---|---|
| "你好" | 主持人自我介绍+阵容 | 身份声明正确 |
| "现在该买股票吗？" | 2–4 位大师声部 + 综合裁决 | 快答档触发 |
| "开会" | 全员大师 + 完整综合裁决 | 全议会档触发 |
| 问一个大师不擅长的事 | 诚实说"不在我的镜片里" | 不越界 |
| "再查一下" | 触发二次验证（如有配置） | 条件触发正常 |
| "这个PE数据是哪里来的？" | 附来源+日期 | 数据纪律 |

### 常见修复

- 输出太长 → 调 `SOUL.md` §快答档字数限制
- 大师不说话 → 检查 skill 文件名是否匹配 *召唤映射表中的名字
- 数据编造 → 检查 references/ 和 §2.10 数据纪律
- bot 不回 → 检查 gateway log：`my-hero gateway logs`

---

## 5. 定制你自己的版本

### 改阵容

1. 编辑 `references/depth-modes.md` 的召唤映射表
2. 添加/删除 `skills/<大师>/` 目录
3. 修改 SOUL.md §身份 的大师列表

### 改综合裁决风格

编辑 `references/synthesis.md`：
- 四问可以改成三问或五问
- 综合层篇幅可以调整
- 反例自检的格式可以自定义

### 改语言/语气

编辑 SOUL.md §沟通规则：
- 语言（中文简体/繁体/英文/日文）
- 输出格式（bullet / 列表 / 段落）
- 语气（直白 / 幽默 / 正式）

### 增加新大师

按 `DISTILLATION-PROCESS.md` §蒸馏步骤：
1. 搜集资料（WebSearch，找著作/访谈/股东会）
2. 写 `skills/<大师>/SKILL.md`
3. 写 `skills/<大师>/references/research.md`
4. 加进 SOUL.md 的大师列表
5. 加进 `references/depth-modes.md` 的召唤映射

---

## 6. 维护

```bash
# 修改后部署
cd ~/hermesagent/Distill/蒸馏Hermes/<project>-hero/
./sync.sh

# 查看 gateway 日志
my-hero gateway logs

# 查看/清理记忆
cat ~/.hermes/profiles/my-hero/memories/MEMORY.md

# 重启
my-hero gateway stop && my-hero gateway start
```

---

## 7. 已知风险

| 风险 | 规避 |
|---|---|
| bot token 泄露 | 永远不进任何聊天/issue/截图 |
| 大师编造"听起来对的假观点" | references/ 强制约束 |
| 二次验证编造数据 | 附 §2.10 提醒 + 时间戳 + 来源 |
| profile 之间配同 bot token | 独立 bot，一个 profile 一个 token |
| Apple Silicon Hindsight daemon bug | MVP 关掉，或查阅 hermes issue #7135 |
