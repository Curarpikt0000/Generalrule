# 绕过 WAF 的真办法:用 DevTools 找后端 API,别折腾 browser 自动化

> **目标位置**:`wiki/crawler/bypass-waf-via-backend-api-discovery.md`
> **首次记录**:2026-05-31(SHFE 库存抓取案例)
> **适用 Agent**:所有 agent（Claude Code / Hermes / Antigravity / Codex / Cursor 等）

---

## 核心洞察(一句话)

**当看到需要"模拟人浏览网页"才能拿到数据时,先用 DevTools Network 标签找后端 AJAX/JSON endpoint。前端 UI 是装饰,真数据通过 HTTP API 直接流动——绕开 WAF 的浏览器层检测,只需要 cookie + headers 就能 Python requests 直抓。**

不要 default 跳到 Playwright / Selenium / computer_use 这类重武器。它们应该是 fallback,不是 first try。

---

## 为什么 default 思路常踩坑

遇到反爬网站(企业级 WAF 如 SafeLine / Akamai / Cloudflare),agents 常见错误路径:

1. ❌ **直接 curl** → 403 / 200+ 拼图挑战页 → 失败
2. ❌ **headless Playwright** → 被 navigator.webdriver 等指纹识破 → 滑块永远过不去
3. ❌ **stealth Playwright** → 复杂、慢、易碎、维护成本高
4. ❌ **AI computer_use 操作真 Chrome** → 需要 vision model + UI 模型 + cron 权限,卡 quota 又卡环境
5. ❌ **手工每周采集** → 人工低效,违背自动化目的

**所有这些都在跟 WAF 的"浏览器层防护"硬碰硬**。但 WAF 通常**对后端数据 endpoint 的检查松得多**——因为他们自己前端也要调这个接口。

---

## 正确流程(5 步法,实测 5~10 分钟搞定)

### Step 1:用 Chrome 走前门访问一次(过 WAF)

- 打开目标网站,**手工过滑块/captcha** 一次
- 之后 cookie 已经在 Chrome 里,**几天/几周不过期**

### Step 2:DevTools 找后端 endpoint

- `F12` 打开 DevTools
- 切到 **Network** 标签
- 勾选 **Fetch/XHR** 过滤(只看数据请求,忽略 css/图片/js)
- 左上角 🚫 **clear** 清空记录
- 在页面上**做你想自动化的那个操作**(选日期、点查询、切 tab)
- 看右侧出现的 1~3 个请求,**找返回大体积 JSON 或 HTML 的那个**(通常是数据 endpoint)

### Step 3:Copy as cURL

- 右键目标请求 → **Copy → Copy as cURL (bash)**
- 这条 cURL 包含**完整的复现配方**:URL / method / headers / cookies / payload

### Step 4:拆解 cURL,识别关键要素

典型 cURL 的关键字段:

| 字段 | 作用 | 通常需要 |
|---|---|---|
| URL | 数据 endpoint | ✅ 看 URL 模式,是否含可参数化部分(日期 / ID / 分页) |
| `User-Agent` header | 伪装真浏览器 | ✅ 必须 |
| `Referer` header | 证明从合法页面跳来 | ✅ 通常必须(WAF 防直链) |
| `X-Requested-With: XMLHttpRequest` | 标识 AJAX 请求 | ⚠ 视情况 |
| Cookies | 含 session / WAF token / 用户认证 | ✅ 通常必须 |
| `sec-ch-ua-*` | 浏览器版本指纹 | ⚠ 视情况(大部分不验) |

**关键判断**:cookie 里有没有看起来像 **WAF 通过证书** 的字段?常见名称:
- SafeLine: `safeline_bot_token`、`sl_xxx_fig`、`TrsAccessMonitor`
- Cloudflare: `cf_clearance`、`__cf_bm`
- Akamai: `ak_bmsc`、`bm_sv`、`_abck`

如果有,这些就是**"我已过 WAF 验证"的电子凭证**,直接 copy 到 Python 用即可。

### Step 5:写 Python requests 复现

```python
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 ...",     # 从 cURL copy
    "Referer": "https://...",            # 从 cURL copy
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "*/*",
}
COOKIES = {
    "safeline_bot_token": "...",  # 从 cURL copy(WAF 证书)
    "session_id": "...",           # 从 cURL copy(如果有)
}

# 参数化 URL(以日期为例)
url_template = "https://example.com/api/data/{date}/all.json"

for date_str in ["20260522", "20260515", ...]:
    url = url_template.format(date=date_str)
    r = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=15)
    r.raise_for_status()
    # 解析(JSON 用 r.json(),HTML 用 pandas.read_html(r.text))
```

---

## Cookie 管理:过期了怎么办

WAF cookies 通常有效期 1 周~1 个月。过期后:

1. **Chrome 重新访问目标页面**(可能再过一次滑块)
2. **F12 → Application → Cookies → 找到 WAF 相关 cookie 复制新值**
3. **替换脚本里的 cookie 字典**

或者更省事:在脚本里检测 401/403 时**通知用户更新 cookie**(Telegram / email / macOS notification),保持手工成本极低(几周一次,30 秒)。

进阶方案:**Playwright stealth 仅用于"过一次 WAF 拿 cookie"**,拿完保存 cookie 给主脚本用(主脚本仍是简单 requests)。这是"重武器只用一次"的混合方案,但**通常没必要**。

---

## 何时这套方法不适用(需要 fallback)

| 场景 | 原因 | 替代方案 |
|---|---|---|
| WAF 给每个请求都 issue 新 token(per-request CSRF) | cookie 一次性,无法 reuse | Playwright stealth 走真浏览器 |
| 端点 response 是 WebSocket 流 | requests 不支持 WS 长连接 | `websockets` Python 库 |
| 数据在 canvas 绘制(图片格式) | DevTools Network 看不到原始数据 | computer_use vision OCR 或 fallback 手工 |
| 端点严重依赖 JavaScript 计算 sign 参数 | sign 是 JS 函数生成,Python 难复刻 | Playwright(让真 JS 引擎执行)+ 截取 sign |
| 需要登录才能看的私人数据 | session 短期失效 | OAuth / 真账号会话保持 |

**判别要点**:Step 2 那个目标请求的 URL,**是否在第 2 次刷新页面后仍是同一个 URL**(只有时间戳变了)?是 → 端点稳定,适合 requests;不是 → 可能有动态 sign 参数,要小心。

---

## 与其他方案的能力/成本对比

| 方案 | 工作量 | 稳定性 | 部署位置 | 月成本 | 何时用 |
|---|---|---|---|---|---|
| **Python requests + cookie** | ⭐ 极低 | ⭐⭐⭐⭐ 极稳 | 任何地方 | $0 | **永远先试** |
| akshare / tushare 等封装库 | ⭐ 极低 | ⭐⭐ 看维护者勤奋度 | 任何地方 | $0~小额 | 库还活着的话(经常死) |
| Playwright stealth | ⭐⭐⭐ 中 | ⭐⭐⭐ 看 WAF 强度 | 任何机器(需 Chromium) | $0 | requests 真不行才用 |
| AI computer_use | ⭐⭐⭐⭐ 高 | ⭐⭐ 易碎 | 用户机器 + AI quota | $5~50 | 最后兜底 |
| 手工每周采集 | ⭐⭐ 低 | ⭐⭐⭐⭐⭐ 稳 | 人 | $0 但费心 | 极少量/不频繁 |

---

## 案例:SHFE 库存周报(2026-05-31)

**问题**:上海期货交易所网站(www.shfe.com.cn)有 SafeLine WAF。akshare 失效。Antigravity 在 GitHub Actions(数据中心 IP)被拦。AI computer_use 在用户机器上失败(DeepSeek 没 vision、Gemini quota 限制、cron 权限不足)。

**发现**:Chrome DevTools 在"库存周报"页面点日期,Network 抓到 1 个请求:

```
URL: https://www.shfe.com.cn/data/tradedata/future/stockdata/weeklystock_20260522/ZH/all.html?params=1780154035822
Method: GET
Headers: User-Agent / Referer / X-Requested-With
Cookies: TrsAccessMonitor / safeline_bot_token / sl_xxx_fig
Response: 21.4 kB HTML(含 <table>),200 OK,311ms
```

**关键判断**:
- URL 含日期可参数化(`weeklystock_YYYYMMDD`)→ ✅
- `params` 参数是时间戳,SHFE 不校验值 → ✅
- Cookie 含 SafeLine WAF 通过证书 → ✅
- 响应是 HTML 含表格,`pandas.read_html()` 可直接解析 → ✅

**实施**:30 行 Python 脚本,本机 launchd 周六 09:00 跑,绕开 WAF / cron 权限 / vision 模型限制等**所有痛点一次性解决**。

---

## 给未来 Agent 的检查清单

接到"抓某个反爬网站数据"任务时,**按顺序问自己**:

1. ✅ 用户能在自己浏览器手工访问吗?→ 能,继续
2. ✅ Chrome DevTools Network 能看到清晰的数据 endpoint 吗?→ 能,继续
3. ✅ Endpoint URL 第二次访问时模式稳定吗?→ 是,继续
4. ✅ Cookie 里能识别出 WAF 通过证书吗?→ 是,**直接 Python requests + cookie reuse,搞定**

任一步答否,降级到 Playwright stealth 或 computer_use。但**别跳过 Step 1~4 直接降级**——这是这条 lesson 想避免的最大坑。

---

## 关联

- 项目案例:`Daily_GoldSilvPT-inv_Notion` → `shfe_weekly_inventory.py`
- 关联 lesson:`weekly-report-pagination.md`(同期 Antigravity 在 SGE 处理时学到的分页教训)
- 关联工具:Chrome DevTools / pandas.read_html / requests.cookies
