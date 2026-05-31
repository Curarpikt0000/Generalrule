---
title: moomoo OpenD + futu-api 接入指南（多 Hermes profile 共用一台 Mac）
domain: agent-rules
type: concept
keywords: [moomoo, opend, futu-api, hermes, finance-hero, market-data, multi-profile, 127.0.0.1:11111, login-items, launchd]
tags: [moomoo, opend, futu-api, market-data, hermes-integration, multi-profile]
source: Cowork 协作会话 2026-05-29 / 2026-05-31（finance-hero 实装 + 跨 profile 复用经验）
sources:
  - https://www.moomoo.com/download/OpenAPI
  - https://openapi.moomoo.com/moomoo-api-doc/en/intro/authority.html
  - https://github.com/FutunnOpen/py-futu-api
  - finance-hero/references/moomoo-setup.md（实装稿）
created: 2026-05-31
updated: 2026-05-31
last_updated: 2026-05-31
---

# moomoo OpenD + futu-api 接入指南

> 让 **任何 Hermes profile** 的 bot 通过 futu-api 调用 moomoo OpenD 拿股票/期货/期权行情、财报、历史 K 线。
> 设计原则：**一台 Mac = 一个 OpenD = 多 profile 共用**。Login Items 自启，无需每次手开。
> 凭证纪律：**moomoo 账号密码只进 OpenD 自己的 GUI 登录界面，绝不写进任何 wiki / .env / 代码 / 配置文件**。

---

## 一、整体架构

```
[Mac 机器]
    │
    ├── moomoo OpenD.app（GUI 网关，常驻后台）
    │       │
    │       ├── 用户的 moomoo 账号已登录（密码在 OpenD 内部 keychain）
    │       └── 监听 127.0.0.1:11111（HTTP/protobuf）
    │
    ├── ~/.hermes/profiles/finance/                ← finance hero
    │       └── tools/（或 bot 终端直接）          ┐
    │           调用 futu-api → 127.0.0.1:11111    │ 多个 profile
    │                                              │ 共用同一个
    ├── ~/.hermes/profiles/general/                │ OpenD 实例
    │       └── tools/                             │
    │           调用 futu-api → 127.0.0.1:11111    ┘
    │
    └── （未来更多 profile 同理）
```

**关键事实**：

- OpenD 是 macOS GUI app，**单实例**（绑端口 11111，再开第二个会冲突）
- futu-api Python 客户端支持**同一 OpenD 多客户端并发连接**
- 同一 moomoo 账号下的 quota 在所有连接间**共享**——不会因为多个 profile 同时连就翻倍
- 密码留在 OpenD 内部 keychain，**任何外部文件（包括本 wiki）都不应有密码字段**

---

## 二、一次性 Mac 安装（任何 Hermes profile 用之前都先做一遍）

### 2.1 下载 + 安装 OpenD

1. 浏览器开 https://www.moomoo.com/download/OpenAPI
2. 选 **macOS** 版下载 `OpenD_*.dmg`
3. 双击 dmg → 拖 OpenD 进 Applications

### 2.2 首次登录 + 签 API 协议（密码只在这里输入）

1. Applications 里启动 **moomoo OpenD**
2. **在 OpenD 自己的登录界面**输入你的 moomoo 账号（手机号/邮箱）+ 密码
   - **不要把密码贴进任何对话框 / 文件 / 截图分享**
   - 不需要为此专门开户；用 moomoo App 注册账号即可
3. 弹出 **API 问卷**——逐项填完
4. 签 **OpenAPI 用户协议**
5. 登录成功后 OpenD 主界面显示监听 **127.0.0.1:11111**

### 2.3 让 OpenD 开机自启（macOS Login Items）

```
System Settings → General → Login Items & Extensions → Open at Login
点 "+" → Applications 里选 "moomoo OpenD" → 添加
（可勾选 "Hide" 让它启动后隐藏到后台）
```

效果：登录 Mac 自动启动 OpenD；关机/注销会停。

> **进阶**：要"崩了自重启 + 日志落盘"，写一份 launchd plist（com.chao.moomoo.opend）放 `~/Library/LaunchAgents/`。模板参考 finance-hero 项目沿用的 Hermes gateway plist 风格。但对一般用例 **Login Items 已足够**。

### 2.4 装 futu-api Python SDK（一次，全局可见）

```bash
pip3 install futu-api
```

确认：

```bash
python3 -c "from futu import OpenQuoteContext; print('OK')"
# OK
```

### 2.5 连通测试（不依赖任何 Hermes profile）

```bash
python3 - <<'PYEOF'
from futu import OpenQuoteContext
ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
ret, data = ctx.get_market_snapshot(['HK.00700'])  # 测腾讯
print("OK" if ret == 0 else f"ERR: {data}")
if ret == 0:
    print(data[['code', 'name', 'last_price', 'update_time']])
ctx.close()
PYEOF
```

看到腾讯快照 → OpenD ↔ futu-api 通了，可以进入 §三给各 profile 接入。

---

## 三、给单个 Hermes profile 接入（finance / general / 其他）

每个 profile 都需要做以下三件事：

### 3.1 拷一份取数说明到 profile 的 references/

```bash
PROFILE=finance   # 或 general / 其他
cp ~/hermesagent/Distill/蒸馏Hermes/finance-hero/references/moomoo-setup.md \
   ~/hermesagent/Distill/蒸馏Hermes/$PROFILE-hero/references/moomoo-setup.md
```

然后**改其中的项目特化部分**（如果 general 想用它，得改"行情 vs 分析分工"那段，把"finance"全换成 general 的场景描述）。

### 3.2 在该 profile SOUL.md 加取数纪律

```markdown
## 行情取数（如适用）

- 数据源：moomoo OpenD（详 `references/moomoo-setup.md`）
- §2.10 强制：任何引用的行情/数字，必须附 **日期 + 接口名 + 原始数值片段**。
  取不到（OpenD 未运行 / quota 超限）就明说"数据未取到"或自动降级到备用源（如 Yahoo Finance），**不许编**。
```

> ⚠️ general profile 加这条**前先想清楚**：general 主攻人生/眼光/境界类问题，本来不该频繁查行情。只有当某个问题确实需要金融事实（如"我在思考要不要买房，全国房价走势怎么看"）才用。**别把 general 变成 finance**——profile 隔离原则。

### 3.3 sync + 测试

```bash
cd ~/hermesagent/Distill/蒸馏Hermes/$PROFILE-hero && ./sync.sh
```

Telegram 里问 bot 一句涉及具体股票的问题，看它是否调 futu-api / 引用真实数据。

---

## 四、多 profile 共用一个 OpenD 的注意事项

### 4.1 同时连接没问题

futu-api 支持同一 OpenD 多客户端。finance 和 general 的 bot 可以同时 `OpenQuoteContext(host='127.0.0.1', port=11111)`——OpenD 都接得住。

### 4.2 quota 是共享的，不是翻倍

OpenD 给的实时订阅 quota + 历史 K 线 quota 是绑账号的——所有客户端共享。
- 免费档：港美股快照行情够用；A 股 Level-2 基本要付费
- 实时报价订阅数有上限（视入金状态）
- 同一只股 7 天内重复查历史 K 不重复扣 quota（OpenD 自带去重）

实操：免费档对 hero 议会用例完全够。不必为 Level 2/3（截图里 5-50 USD/月那些订阅）付费。

### 4.3 OpenD 关掉时所有 profile 都失去行情

bot 设计要有 fallback：调 futu-api 报"OpenD 未连接"时，自动降到 **Yahoo Finance / Google Finance** 等备用源。finance-hero 实测里 bot 已经会自动 fallback 到 Yahoo Finance（见 wiki [[google-finance-research-integration]] 的二次验证机制可作为更高级的备份层）。

### 4.4 一台机一份 OpenD——别开第二个

第二个 OpenD 起不来（端口被占），会报错。如果需要"两个账号同时跑"——不行，OpenD 设计如此。要切账号必须先 logout 当前再 login 新的。

---

## 五、跨机器部署（如果未来需要）

> 本节给完整性，**当前不适用**（你两个 profile 都在同一台 Mac）。

每台机器独立 OpenD：
1. 那台机也装 OpenD + 用 **它自己的 moomoo 账号**登录（账号可以是同一个，但 OpenD 实例是各自的）
2. 那台机也装 futu-api
3. 那台机连本机的 127.0.0.1:11111

跨机连接（不推荐）：理论可改 OpenD 监听 0.0.0.0 但有安全风险，且 moomoo 协议未必允许公网访问。最佳实践：每台机一个 OpenD。

---

## 六、凭证 / 安全（必读）

| 该放哪 | 不该放哪 |
|---|---|
| ✅ moomoo 账号密码：OpenD GUI 登录界面（OpenD 内部 keychain 保管）| ❌ 任何 wiki / SKILL.md / SOUL.md / references/*.md |
| ✅ moomoo unlock 交易密码（如启用交易接口）：profile 的 `.env`，环境变量 `MOOMOO_TRADE_PWD=`，**`.env` 必入 .gitignore** | ❌ Python 脚本里硬编码 |
| ✅ 1Password / iCloud Keychain 跨机同步用户密码 | ❌ chat 历史 / 截图 / issue / commit |

**铁律**（继承自 General Global Rule §7）：**写入任何"会进 git 的文件"前，先 grep 一遍敏感词**（password / passwd / secret / token / pwd）。

---

## 七、踩坑清单

1. **OpenD 没起来 = bot 拿不到数据**：写 fallback 链路（Yahoo / Google Finance）+ §2.10 显式标注"OpenD 未运行，已降级到备用源"。
2. **新装 OpenD 没签 API 协议** → futu-api 连得上但 API 调用全报"未授权"。GUI 弹窗签完再用。
3. **macOS Apple Silicon**：OpenD 当前版本（截至 2026-05）原生支持 ARM，但仍可能偶发启动慢——给 Login Items 启动后等 5-10 秒再用 futu-api。
4. **futu-api 版本 vs OpenD 版本**：差太多协议不兼容。建议升级 `pip3 install --upgrade futu-api` 时也升 OpenD。
5. **同账号同时在 moomoo App 和 OpenD 登录**：通常能并存；但极端情况下 moomoo 风控会踢一个出去。**重要场景下别频繁切换**。
6. **港股 Level-2**：需要单独订阅（截图那张 market data 页里的 HKG Securities LV2）。免费档只有 LV1 快照。Hero 议会场景**不需要**。
7. **A 股 Level-2**：基本要付费 + 国内券商资质。议会场景**不需要**。

---

## 八、让另一个 Hermes profile 读这份 wiki

**同一台 Mac 上**，所有 profile 都能直接读 wiki 路径：

```
/Users/chaojin/Antigravity Projects/Generalrule/wiki/agent-rules/moomoo-opend-integration.md
```

**给另一个 profile 接入的最快路径**（如要 general 也接 moomoo）：

1. **在 Telegram 群里和那个 profile 的 bot 说**：
   > "请读 wiki 这份文件：
   > `/Users/chaojin/Antigravity Projects/Generalrule/wiki/agent-rules/moomoo-opend-integration.md`
   > 按 §三 给我接入。"

   bot 会用它的文件读取工具读这份文档，按里面的 §3.1-3.3 给自己的 profile 接入。

2. **或在 Cowork 里告诉我**（Claude）：
   > "把 moomoo 接入给 general profile 也做一遍。"

   我会 cp references/moomoo-setup.md 到 general-hero 蓝图、改 SOUL.md、sync。

3. **跨机器**（如未来扩展）→ 那台机 `git clone Generalrule.git` 后路径一致；按 §五独立装 OpenD。

---

## 九、相关页面

- [[finance-hero-distillation]] —— finance hero 议会模式底座（moomoo 是其行情数据层）
- [[google-finance-research-integration]] —— Google Finance 二次验证（OpenD 不可用时的高质量备用源）
- [[skill-registry]] —— Hermes profile 的 skill 加载机制
- general-global-rule.md §7（凭证管理）、§2.10（显式失败）

---

## 来源

- moomoo OpenAPI 官方文档：https://openapi.moomoo.com/moomoo-api-doc/en/intro/authority.html
- futu-api Python SDK：https://github.com/FutunnOpen/py-futu-api
- finance-hero 项目实装稿：`finance-hero/references/moomoo-setup.md`
- 2026-05-31 多 profile 共用 OpenD 经验沉淀
