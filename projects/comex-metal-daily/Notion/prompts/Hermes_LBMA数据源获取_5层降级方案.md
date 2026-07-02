# Hermes — LBMA 历史 fix 数据获取(5 层降级自动尝试)

> 用户(Claude Chao)在 cowork 跟 cowork Claude 确定:**LBMA 自 2025-03-18 起被 ICE 限制免费分发,所有 vanilla 金融数据源(Yahoo / FRED / Kitco / Investing CFD)都拿不到真 LBMA 数据,全部退化为 COMEX 期货代理价格**。
>
> 但 MacroMicro 仍有授权展示 LBMA(图表 UI 可见)。本文档给 Hermes 一套 **5 层降级自动尝试**方案,目标是拿到 2026-05-22 ~ 2026-06-10 这 13 天 LBMA Au/Ag/Pt fix 的真值。
>
> **用户对自身介入的明确要求**:不到玩不得已不要介入手动截图。Hermes 必须先把 Tier 1~4 自动尝试一遍,**全部失败**才触发 Tier 5(用户手工)。

---

## §0 必需数据 + 已知锚点

### 0.1 必需输出

| 字段 | 范围 | 用途 |
|---|---|---|
| LBMA Au PM Fix | 2026-05-22 ~ 2026-06-10 每个交易日 | SIFO §8.1 q_fin(Au) 输入 |
| LBMA Ag Fix(12:00 noon London) | 同上 | q_fin(Ag) 输入 |
| LBMA Pt AM Fix | 同上 | q_fin(Pt) 输入 |

(周末跳过:5/23-5/25、5/30-5/31、6/6-6/7;实际工作日 = 13 天)

### 0.2 已知锚点(cowork Claude 用户截图)

**LBMA Silver Spot Price 2026-06-09 = $68.60**(来自用户给的 MacroMicro 截图)

**任何方案获取的 6/9 银 fix 必须 ≈ $68.60(误差 < 1%)才算成功**。如果偏离 > 1%,说明方案抓错数据源,跳到下一层。

### 0.3 MacroMicro Series ID 候选

```
LBMA Silver:   https://en.macromicro.me/series/7949/lbma-silver-price
LBMA Gold:     https://en.macromicro.me/series/4886/lbma-gold-price (cowork Claude 提供,需验证)
LBMA Platinum: 未知,Hermes 自己在 MacroMicro 搜索栏找
```

---

## §1 Tier 1:HTTP 直抓 MacroMicro 后端 API(预期 30 分钟内能搞定)

### 1.1 思路

MacroMicro 是 SPA(单页应用),前端图表必然通过 AJAX/REST endpoint 拿数据。直接找到这个 endpoint,用 Python `requests` 抓即可。**这条路完全照搬 SHFE WAF bypass 成功经验**(`wiki/crawler/bypass-waf-via-backend-api-discovery.md`)。

### 1.2 候选 endpoint 路径(按概率排序,逐个 try)

```python
import requests

SERIES_ID = 7949  # LBMA Silver
candidates = [
    f"https://en.macromicro.me/charts/data/{SERIES_ID}",
    f"https://en.macromicro.me/series/{SERIES_ID}/data",
    f"https://en.macromicro.me/api/v1/series/{SERIES_ID}",
    f"https://en.macromicro.me/api/v1/charts/{SERIES_ID}/data",
    f"https://api.macromicro.me/charts/{SERIES_ID}",
    f"https://en.macromicro.me/data/series/{SERIES_ID}.json",
    f"https://en.macromicro.me/series/{SERIES_ID}.json",
]

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": f"https://en.macromicro.me/series/{SERIES_ID}/lbma-silver-price",
    "X-Requested-With": "XMLHttpRequest",
}

for url in candidates:
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200 and "json" in r.headers.get("content-type", "").lower():
            data = r.json()
            print(f"✅ SUCCESS: {url}")
            print(f"   sample: {str(data)[:500]}")
            break
    except Exception as e:
        print(f"❌ {url} → {e}")
```

### 1.3 备用:HTML 源码里找 `__NEXT_DATA__` 或类似嵌入 JSON

如果是 Next.js / Nuxt.js 应用,初始数据常嵌在 HTML `<script>` 里:

```python
import re
import json

r = requests.get("https://en.macromicro.me/series/7949/lbma-silver-price", headers=headers)
html = r.text

# Next.js: <script id="__NEXT_DATA__" type="application/json">
m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.+?)</script>', html, re.DOTALL)
if m:
    data = json.loads(m.group(1))
    # 在 data 里递归找 series 数据
    
# Nuxt.js: window.__NUXT__ = {...}
m = re.search(r'window\.__NUXT__\s*=\s*({.+?});', html, re.DOTALL)
if m:
    # 处理 NUXT 数据

# 其他 SPA: window.__INITIAL_STATE__
m = re.search(r'__INITIAL_STATE__\s*=\s*({.+?})[;<]', html, re.DOTALL)
```

### 1.4 成功验证

抓到的数据 JSON 找 `2026-06-09` 那一行,值必须 ≈ $68.60(±$0.50)。

### 1.5 失败条件

- 所有 7 个 endpoint 全 4xx/5xx
- HTML 抠 JSON 找不到价格数据
- 抓到的 6/9 银价跟 $68.60 偏离 > 1%

→ **降级 Tier 2**

---

## §2 Tier 2:Playwright headless browser(预期 1 小时,处理 JS 渲染)

### 2.1 思路

如果 Tier 1 失败,说明 MacroMicro 用 client-side JS 计算/获取数据。**Playwright headless Chromium 可以执行 JS,然后从 DOM / Network 拿数据**。

### 2.2 安装(Hermes 自检)

```bash
pip install playwright --break-system-packages
playwright install chromium
```

### 2.3 方案 A:用 Playwright 抓 Network 请求(看页面 JS 调用了什么 API)

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    
    # 监听所有网络请求
    api_calls = []
    def log_response(response):
        if response.status == 200 and "json" in response.headers.get("content-type", "").lower():
            url = response.url
            if "macromicro" in url or "chart" in url or "series" in url or "data" in url:
                api_calls.append(url)
    
    page.on("response", log_response)
    
    page.goto("https://en.macromicro.me/series/7949/lbma-silver-price")
    page.wait_for_selector(".chart", timeout=30000)  # 等图表渲染
    page.wait_for_timeout(3000)  # 多等 3 秒确保 AJAX 完成
    
    print(f"发现 {len(api_calls)} 个 API 调用:")
    for url in api_calls:
        print(f"  {url}")
    
    browser.close()

# 然后把发现的 URL 直接用 requests 重放(Tier 1 思路)
```

### 2.4 方案 B:Playwright 直接读 DOM 里的 chart 数据

```python
# 如果 chart 是 highcharts / echarts / chartjs,数据在 JS 全局变量里
data = page.evaluate("""
    () => {
        // Highcharts
        if (window.Highcharts && window.Highcharts.charts.length > 0) {
            return window.Highcharts.charts[0].series[0].data.map(p => ({
                date: new Date(p.x).toISOString().split('T')[0],
                value: p.y
            }));
        }
        // ECharts
        if (window.echarts) { ... }
        // 其他
        return null;
    }
""")
print(data)
```

### 2.5 成功验证

同 Tier 1.4,6/9 银价 ≈ $68.60。

### 2.6 失败条件

- Playwright 装不上(Chromium 下载失败 / 权限错)
- Network 没看到任何 JSON 数据流(可能 chart 用 WebSocket 或 protobuf)
- DOM 里读不到 chart 数据(JS 全局变量被混淆)
- 拿到的数据格式无法对应日期

→ **降级 Tier 3**

---

## §3 Tier 3:Playwright 截图 + vision skill OCR(预期 2 小时)

### 3.1 思路

如果 Tier 1+2 都失败(数据 endpoint 太隐蔽),退路是**用 Playwright 把 chart 截图保存,然后让 vision skill 读出每天的 close 值**。

### 3.2 流程

```python
from playwright.sync_api import sync_playwright

target_dates = [
    "2026-05-22", "2026-05-26", "2026-05-27", "2026-05-28", "2026-05-29",
    "2026-06-01", "2026-06-02", "2026-06-03", "2026-06-04", "2026-06-05",
    "2026-06-08", "2026-06-09", "2026-06-10"
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    
    for series_id, metal in [(7949, "Ag"), (4886, "Au"), ("PT_ID", "Pt")]:
        page.goto(f"https://en.macromicro.me/series/{series_id}/lbma-{metal.lower()}-price")
        page.wait_for_selector(".chart", timeout=30000)
        page.wait_for_timeout(2000)
        
        # 把图表缩放到 "1M" 或 "3M" 视图,这样 13 天能在同一张图清楚显示
        page.click("text=1M")
        page.wait_for_timeout(1500)
        
        # 截图(可以截整个图表,也可以 hover 每个日期单独截 tooltip)
        chart = page.query_selector(".chart")
        path = f"/tmp/lbma_{metal}_chart.png"
        chart.screenshot(path=path)
        print(f"截图保存: {path}")
    
    browser.close()
```

### 3.3 用 vision skill 读图

调用 `vision` skill(在 `available_skills` 里,Gemini 后端):

```python
# 伪代码 - 实际调用方式看 vision skill SKILL.md
from skills.vision import analyze_image

prompt = f"""
This is a line chart of LBMA Silver fix prices.
Identify the value of each of these dates (read off the chart):
{', '.join(target_dates)}

Return a JSON array: [{{"date": "YYYY-MM-DD", "value": float}}, ...]

The chart shows USD per troy ounce on Y axis.
The known anchor: 2026-06-09 = $68.60
"""

result = analyze_image("/tmp/lbma_Ag_chart.png", prompt=prompt)
```

### 3.4 改进:多角度截图

如果一张图 13 天读不准,把图分成 4 段截图(每段 4 天),vision 单独读每段更准。或者用 Playwright `hover` 在每个日期上让 tooltip 显示,然后单独截图 + OCR。

### 3.5 成功验证

vision 输出的 6/9 银价跟 $68.60 误差 < 1%(实际 $68.00~$69.20 都接受)。

### 3.6 失败条件

- vision skill 读出的数字明显错(>5% 偏离 $68.60)
- vision 拒绝读(说"unclear")
- chart 渲染不正常(没数据 / loading 状态)

→ **降级 Tier 4**

---

## §4 Tier 4:Computer use 驱动用户 Chrome + vision OCR(预期 4 小时)

### 4.1 思路

如果 Tier 3 失败(headless 浏览器抓不到完整 chart),最后的**自动化**手段是**用 computer use 控制用户 Mac 上真实 Chrome**(浏览器指纹 + cookies 都是真人的,WAF 不拦)。

### 4.2 前提

- Hermes gateway 有 computer-use MCP 权限(check `~/.hermes/profiles/<name>/config.yaml` 是否启用)
- 用户 Mac 当前活跃 + Chrome 已打开

### 4.3 流程

```python
# 伪代码 - 看 computer-use MCP 真实接口

# Step 1: 申请权限
request_access(apps=["Google Chrome"], reason="抓取 LBMA 历史价格")

# Step 2: 打开 MacroMicro
open_url_via_chrome("https://en.macromicro.me/series/7949/lbma-silver-price")

# Step 3: 等图表加载,截全屏
sleep(5)
screenshot_full = take_screenshot()

# Step 4: 用 vision 找图表区域,然后 hover 每个日期
chart_coords = vision_find_element(screenshot_full, "the LBMA Silver price line chart")
for date_str in target_dates:
    # 计算该日期在 X 轴的像素位置(基于图表起止日期范围)
    x = calc_pixel_for_date(date_str, chart_coords)
    y = chart_coords['center_y']
    
    mouse_hover(x, y)
    sleep(0.5)
    
    # 截屏 tooltip 区域
    tooltip_screenshot = take_screenshot()
    tooltip_value = vision_read_tooltip(tooltip_screenshot)
    
    results[date_str] = tooltip_value
```

### 4.4 失败条件

- Hermes 没 computer-use 权限
- 用户 Mac 当前在锁屏 / 没人监督
- Chrome 没装 / 用户不让访问
- 自动化操作被人/系统打断

→ **降级 Tier 5**(让用户人工)

---

## §5 Tier 5:用户手工(**最后退路**,前 4 层全失败才用)

### 5.1 触发条件

**必须 Tier 1~4 全部尝试过且全部失败**,才能跳到这一层。每跳过一层,在 cowork 日志里说明:
- Tier X 失败原因(具体错误信息)
- Tier X+1 启动时间

### 5.2 用户操作清单(给用户的精简任务)

把这段贴到 cowork(@用户):

> Tier 1~4 全部尝试失败,需要你手工 5 分钟介入:
> 
> 1. 打开 https://en.macromicro.me/series/7949/lbma-silver-price
> 2. 把图表时间范围调到 "3M" 或 "6M"
> 3. 鼠标依次 hover 在下面 13 个日期上,把 tooltip 显示的价格抄到表格:
>    - 5/22, 5/26, 5/27, 5/28, 5/29
>    - 6/01, 6/02, 6/03, 6/04, 6/05
>    - 6/08, 6/09, 6/10
> 4. 重复对 Au 和 Pt(序号 4886 和待找)
> 5. 共 3 个金属 × 13 天 = 39 个数字,粘贴回 cowork
> 
> Hermes 收到后自动:
> - 存到 `~/hermesagent/Comex Metal Daily Issue Report/data/lbma_fix_backup_20260522_20260610.csv`
> - 继续 SIFO §8 q 重算审计

### 5.3 数据保管

任何 Tier 拿到的数据 → 同时存一份到本地 CSV(防 MacroMicro 未来访问失败):
```
~/hermesagent/Comex Metal Daily Issue Report/data/lbma_fix_history.csv
```

CSV schema:
```
date,metal,fix_value,source,confidence
2026-06-09,Ag,68.60,macromicro_tier3_vision,0.95
2026-06-09,Au,XXX,macromicro_tier3_vision,0.92
...
```

`source` 字段记录哪个 Tier 来的(便于未来怀疑数据时溯源)。

---

## §6 报告进度纪律(贯穿 5 层)

每完成一层(或失败降级),Hermes 必须在 cowork 报:

```
[LBMA Audit Progress]
✅ Tier 1: 尝试 7 个候选 endpoint + HTML JSON 抠取
   → 失败原因:全部 403,HTML 无嵌入 JSON
⏳ Tier 2: 启动 Playwright headless
   → 当前状态:Chromium 下载中
```

**禁止静默 fallback**(§2.10 Fail Loud)。

---

## §7 最终交付物(任何 Tier 成功后)

1. **本地 CSV**:`~/hermesagent/Comex Metal Daily Issue Report/data/lbma_fix_history.csv`(13 天 × 3 金属 = 39 行)
2. **更新 SIFO doc**:在 `Hermes_SIFO_量化模块.md` §8.2 的"S_fin 数据源"段加一节"**LBMA 自获取兜底**",描述本次 5 层降级方案
3. **写入 wiki**:把 MacroMicro endpoint 发现经验(如果 Tier 1 成功)记到 `~/Antigravity Projects/Generalrule/wiki/crawler/macromicro-lbma-endpoint.md`(类似 SHFE 那个 lesson)
4. **触发审计 Step 2**:用新拿到的 LBMA 数据真值,完成 12 天 §8 SIFO q 全量重算(按之前的审计令文档 §3-§6 流程)
5. **审计报告**:`audit_q_calculations_20260610.md`
6. **PATCH 12 份 Notion 报告**:按符号约定 + 新 q 数字 + 新灯色判决

---

## §8 时间预算

| Tier | 预算 | 失败上限 |
|---|---|---|
| Tier 1 | 30 分钟 | 1 小时 |
| Tier 2 | 1 小时 | 2 小时 |
| Tier 3 | 2 小时 | 3 小时 |
| Tier 4 | 4 小时 | 6 小时 |
| **5 层全过完** | **~7 小时** | 9 小时 |
| Tier 5(用户) | + 5 分钟用户操作 | — |

如果任何一层卡超过失败上限,**立刻 Fail Loud 触发 Telegram 报警 + cowork 报告**,不要无限循环重试。

---

## §9 一句话总结给 Hermes

> 走 5 层降级,**只在 Tier 1~4 全部尝试且全部 Fail Loud 后**才让用户手工介入。每层启动 + 失败都要在 cowork 实时报进度。
> 
> 最终目标:**自动化拿到 2026-05-22~2026-06-10 的 LBMA Au/Ag/Pt 真实 fix 数据,用真值完成 SIFO q 审计**。
