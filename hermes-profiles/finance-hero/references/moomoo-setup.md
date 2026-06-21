# moomoo OpenD 数据接入说明

> finance-hero 的**行情数据源**。已于 2026-05-28 核实官方文档，事实如下（勿想当然）。

## 现实（先认清门槛，别假设开箱即用）

- **SDK 与 OpenD 网关免费**，支持 Python / Java / C# / C++ / JavaScript。
- **登录不需要开户**：可用 moomoo 账号（或注册用的手机号/邮箱）直接登录 OpenD。
- **但**首次登录后必须**完成 API 问卷并签署协议**才能继续使用。
- **行情深度与配额跟"已入金账户"挂钩**：
  - 有"实时报价订阅配额"（同时订阅的实时行情数量上限）和"历史 K 线配额"。
  - 配额自动分配、无需手动申请；**新入金账户约 2 小时内自动生效**。
  - 免费/未入金账户的港美股深度有限，A 股 Level-2 基本需要权限。
- 截至 2026-05-21 的版本：**OpenD Ver.10.6.6608**。

## 架构：行情 vs 分析的分工

```
moomoo OpenD（本地常驻网关）  ──实时/历史行情──▶  finance-hero
        │                                            │
        ▼                                            ▼
  需要：装 OpenD + 登录 + 签协议            Claude finance skill（分析/估值/财报结构化）
                                            ⚠️ finance skill 拉不了实时行情
```

**结论**：行情靠 moomoo，分析靠 finance skill。别指望一个干两件事。

## 接入步骤（Mac 实操清单）

### Step A · 下载并安装 OpenD

1. 浏览器开 https://www.moomoo.com/download/OpenAPI
2. 选 **macOS** 版下载 `OpenD_*.dmg`（截至 2026-05 是 Ver.10.6+）
3. 双击 dmg 安装，把 OpenD 拖进 Applications

### Step B · 首次登录 + 签协议

1. 启动 OpenD（Applications 里找 moomoo OpenD）。
2. 用你的 moomoo 账号登录（手机号/邮箱+密码，**不需要开户**）。
3. 弹出 **API 问卷**——逐项填完。
4. 签 **OpenAPI 用户协议**。
5. 登录后 OpenD 显示一个网关状态界面，默认监听 **127.0.0.1:11111**。**记住这个端口**。
6. **OpenD 必须保持运行**，FiHeroBot 取数全靠它在后台开着。可设开机自启。

### Step C · 装 Python SDK + 本地连通测试

```bash
# 装 SDK（用你常用的 Python 环境，建议 ≥ 3.8）
pip install futu-api

# 最小连通测试（保存为 test_moomoo.py 后跑）
python3 - <<'EOF'
from futu import OpenQuoteContext
ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
ret, data = ctx.get_market_snapshot(['HK.00700'])   # 测一下腾讯
print("OK" if ret == 0 else f"ERR: {data}")
print(data if ret == 0 else "")
ctx.close()
EOF
```

成功 → 看到 OpenD 返回的腾讯快照行情。
失败常见原因：① OpenD 没启动 ② 端口 11111 被占 ③ 还没签 API 协议 ④ quota 0（账号未入金且无免费配额）。

### Step D · 让 FiHeroBot 用上 OpenD

OpenD 是本地 HTTP 网关，FiHeroBot 有 terminal 工具能直接调 Python——**不需要写新 MCP/工具**，给它一个 helper 脚本就行。

部署一个 `~/.hermes/profiles/finance/tools/moomoo_quote.py`，封装常用接口（快照 / 历史 K / 订阅）。FiHeroBot 像这样调：

```bash
python3 ~/.hermes/profiles/finance/tools/moomoo_quote.py --symbol US.NVDA --type snapshot
python3 ~/.hermes/profiles/finance/tools/moomoo_quote.py --symbol HK.00700 --type kline --period day --count 60
```

返回 JSON，bot 在回答里按 §2.10 引用"日期 + 接口名 + 原始数值"。

> 这个 helper 我等你 Step A-C 跑通后帮你写——验证过端口/账号 quota 实际情况再写更稳。

### Step E · 权限/quota 现实

- **港美股快照行情**：免费账户够用（延迟分钟级）。
- **实时 Level-1 报价订阅**：要权限/入金，未入金账户 quota 很小。
- **A 股 Level-2**：需要单独申请。
- **历史 K 线**：每只股 1 个 quota；7 天内同股不重复扣；多周期复用一个 quota。

刚开始用免费快照足够。等真要看实时盘口或大量历史回测再考虑入金。

### 凭证管理（Global Rule §7）

- moomoo 账号密码用 OpenD 自己的登录界面，不写进任何文件。
- 如果将来要 unlock 交易接口（下单），用 OpenD 的 unlock_trade(password) 流程，**密码走 .env**（`MOOMOO_TRADE_PWD=`），严禁硬编码。本 profile 目前不接交易接口。

## §2.10 取数纪律

finance-hero 引用任何行情时必须附：**日期 + 接口名 + 原始数值**。
取不到就写"数据未取到"，禁止用印象填充。

## 待验证清单（落地前要实测）

- [ ] 你的 moomoo 账号是否需要入金才能拿到你关心市场（A股/港股/美股）的行情深度？
- [ ] OpenD 网关在你的运行环境（Hermes worker 所在机器）能否常驻？
- [ ] futu-api 的订阅配额够不够 finance-hero 的并发提问？

## 来源（2026-05-28 核实）

- [Moomoo API & OpenD Download](https://www.moomoo.com/download/OpenAPI)
- [Authorities and Quota | Moomoo API Doc v10.6](https://openapi.moomoo.com/moomoo-api-doc/en/intro/authority.html)
- [What is Moomoo API? — Help Center](https://www.moomoo.com/us/support/topic3_436)
