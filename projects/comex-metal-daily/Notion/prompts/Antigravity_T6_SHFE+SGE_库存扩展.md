# T6 v2 — Daily_GoldSilvPT-inv_Notion 扩展:加入 SGE 银库存(SHFE 暂搁)

> 给 Antigravity 的扩展任务。**只做 SGE 白银周库存,不做 SHFE**(原因见 §2)。SGE 已确认正确入口页面,backfill 路径清晰。

---

## 1. 目标(简化版)

把 SGE(上海黄金交易所)白银周库存数据接入用户已有的 `Daily_GoldSilvPT-inv_Notion` GitHub job,每周往 Silver Notion DB 写一行(`市场 = SGE / 库存频率 = 每周`),回填过去 90 天历史。

**不做的事**(对比 v1):
- ❌ SHFE 沪金/沪银 — akshare 接口失效,WebSearch 没找到现成替代,**搁置等社区修复**
- ❌ Pt 任何东方源 — SGE/SHFE 都不交易铂金

## 2. SHFE 为什么搁置(用户已决策)

Antigravity v1 试运行结果(已验证):
- `ak.futures_stock_shfe_js` 对 2026 年日期全部返回空 DataFrame
- `ak.futures_shfe_warehouse_receipt` 抛 JSONDecodeError(404 当 JSON 解析)
- → akshare 失效,SHFE 官网又被 WAF 拦

用户决策:**暂搁 SHFE,等 akshare 维护者修**。短期影响有限——Hermes 分析的关键变量是 **SGE 银库存**(真现货市场),SHFE 期货库存只是辅助。

## 3. 工作目录(严格按这个,别碰邻仓库)

**目标仓库**:`Daily_GoldSilvPT-inv_Notion`(只有 `sync_cme_to_notion.py` + 1 个 workflow yml 的那个)

**❌ 不要碰**:`Daily_CME-issuestop-inventory_Notion`(T1 已经接过解析器的另一个仓库,改它会污染主链路)

两个仓库都恰好叫 sync_cme_to_notion.py 之类,**别看文件名,看 GitHub 仓库根目录是哪个**。`Daily_GoldSilvPT-inv_Notion` 文件极少(2~3 个),很好辨认。

## 4. Notion 写入目标

**Silver DB**:`2bc47eb5fd3c80f3a71ad8de149a4943`(`极简每日追踪表 Silver` 库)

Schema 已预埋,不需要改:

| 字段 | 类型 | 本任务用途 |
|---|---|---|
| `Silver日期` | date | SGE 周报的报告周末日(周五) |
| `市场` | select | 写 `SGE`(已是预埋选项) |
| `库存频率` | select | 写 `每周`(已是预埋选项) |
| `SH库存吨` | number | SGE 当周库存(单位吨,= PDF 里 kg ÷ 1000) |
| `Silver Reg库存` / `Silver Elig库存` | number(oz) | **留空**(SGE 不区分 Reg/Elig) |
| `URL` | url | PDF 来源 URL,可追溯 |
| `Name` | title | `Silver SGE 2026-MM-DD`(报告周末) |
| `说明` | text | 简要(`SGE 白银周库存 / akshare 无此接口 / PDF 来源`) |

## 5. ⚠ Integration 授权确认(用户已做)

`NOTION_TOKEN` 环境变量对应的 integration 是 **`goldptsilverupdate`**。

用户已确认这个 integration 在 Silver DB 的 connections 列表里(右上角 ··· → Connections)。Antigravity 直接用 NOTION_TOKEN 写即可,不会再 401/403。

## 6. SGE 入口页面(已确认正确)

### 6.1 主入口

**`https://www.sge.com.cn/sjzx/hqzb`**(数据资讯 → 行情周报)

这页有 87 页历史(每周一份 PDF),Antigravity v1 用错的 3 个 URL(`/sjzx/jysj`、`/xwzx/mtbd`、`/xxpl`)都是错栏目,**忽略它们**。

### 6.2 PDF 链接结构

页面上每周一个 PDF 链接,标题如:
- `20260518-20260522周报`(2026-05-25 发布)
- `20260511-20260515周报`(2026-05-18 发布)
- ...

实际 URL 模式:`/upload/file/YYYYMM/DD/<hash>.pdf`,直接从页面 `<a href>` 抽即可。

### 6.3 ⚠ 关键不确定性:行情周报 vs 指定仓库库存周报

**用户最早提供的样本 PDF**(`https://www.sge.com.cn/upload/file/202605/25/de3b502fac4e4843b39dac9510e538a6.pdf`)标题是 `上海黄金交易所指定仓库库存周报`,跟行情周报页(`hqzb`)上的"上海黄金交易所2026年第19期行情周报"**同一天发布**。

两种可能:
- **(A)** 它们是同一份 PDF,行情周报里就含一节"指定仓库库存周报" — 路径走完
- **(B)** 它们是两份独立 PDF,指定仓库库存周报在 SGE 别处页面 — 需要继续找

**Antigravity 必须用第 §7 的 2 步策略来验证**。

## 7. 实现策略(两步走)

### Step 1:抓 `/sjzx/hqzb` PDF 列表

```python
import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
r = requests.get("https://www.sge.com.cn/sjzx/hqzb", headers=headers, timeout=15)
r.raise_for_status()
soup = BeautifulSoup(r.text, 'html.parser')

# 提所有 .pdf 链接 + 标题 + 报告期(从标题里的 YYYYMMDD-YYYYMMDD 抽)
pdf_entries = []
for a in soup.find_all('a', href=True):
    href = a['href']
    if href.endswith('.pdf'):
        title = a.get_text(strip=True)
        # 例:"20260518-20260522周报" → 报告期 5/18~5/22,报告末日 5/22(周五)
        m = re.search(r'(\d{8})-(\d{8})周报', title)
        if m:
            start, end = m.group(1), m.group(2)
            pdf_entries.append({
                "title": title,
                "url": urljoin("https://www.sge.com.cn", href),
                "week_end": datetime.strptime(end, "%Y%m%d").date(),  # 用做 Silver日期
            })

# 过去 90 天 ≈ 第一页前 13 条
pdf_entries = sorted(pdf_entries, key=lambda x: x["week_end"], reverse=True)[:13]
```

**如果 `requests` 被挡(403 / JS 渲染拿不到 PDF 链接)**:用 webworms / playwright 渲染后再抽。具体看你实际试出来的情况,**别瞎切方案,直接试 requests 看返回什么**。

### Step 2:下载最新一份 PDF,验证它是不是"指定仓库库存周报"

```python
import pdfplumber

latest = pdf_entries[0]
r = requests.get(latest["url"], headers=headers, timeout=30)
with open("/tmp/sge_test.pdf", "wb") as f:
    f.write(r.content)

with pdfplumber.open("/tmp/sge_test.pdf") as pdf:
    full_text = "\n".join((p.extract_text() or "") for p in pdf.pages)

# 验证关键字
has_inventory_table = "指定仓库库存周报" in full_text or \
                      ("白银" in full_text and "本周库存" in full_text)

if has_inventory_table:
    # 路径 A:行情周报含库存表,直接 parse
    # 用正则抽"白银 X X X"那行 (上周库存 / 本周增减 / 本周库存)
    m = re.search(r'白银\s+([\d,]+\.?\d*)\s+([+-]?[\d,]+\.?\d*)\s+([\d,]+\.?\d*)', full_text)
    if m:
        this_week_kg = float(m.group(3).replace(",", ""))
        this_week_tons = this_week_kg / 1000
        print(f"✅ SGE 银库存 {latest['week_end']}: {this_week_tons} 吨")
else:
    # 路径 B:行情周报不含库存,转去其它候选页面
    # 候选:
    #   /sjzx/xjjg     现金交割专栏
    #   /sjzx/hjzgtjsj 黄金资管统计数据
    # **不要瞎猜其他路径,这两个找不到就停下报告**
    raise RuntimeError(
        f"行情周报 PDF 不含库存表,需转候选页面 /sjzx/xjjg 或 /sjzx/hjzgtjsj。"
        f"已下载样本: {latest['url']}, 前 500 字: {full_text[:500]}"
    )
```

**Antigravity 必须报告 Step 2 的结果**(A 还是 B),然后在 walkthrough.md 里把第一份成功抽到库存的 PDF 完整文字片段贴出来给用户(让用户验证格式)。

## 8. Backfill 90 天

如果 Step 2 走通(无论 A 还是 B 路径),按 §11.A 跑过去 90 天 ≈ 13 周回填:

```python
# backfill_sge.py
TODAY = date.today()
START = TODAY - timedelta(days=90)

pdf_entries = discover_sge_inventory_pdfs(START, TODAY)  # Step 1 的函数

for entry in pdf_entries:
    try:
        result = parse_sge_silver_pdf(entry["url"])  # Step 2 的 parser
        push_to_notion_v2(
            metal="Silver", db_id=SILVER_DB, market="SGE",
            date_str=entry["week_end"].isoformat(), freq="每周",
            sh_tons=result["this_week_tons"],
            source_url=entry["url"],
            note=f"SGE 白银周库存,回填于 {TODAY}",
        )
        time.sleep(2)  # 别打 SGE
    except Exception as e:
        print(f"❌ {entry['week_end']} 失败: {e}")
        # 单条失败不阻断后续,但要在最终汇总里报告

print(f"✅ Backfill 完成: {n_success}/{n_total} 成功")
```

## 9. 日常 cron(backfill 验收通过后才启用)

加进现有 `sync_cme_to_notion.py` 的 `main()` 末尾(不要新建 cron):

```python
def sync_sge_latest():
    """每次 daily 跑都调用,SGE 有新 PDF 就写,没新的就跳过"""
    pdf_entries = discover_sge_inventory_pdfs_latest_only()
    if not pdf_entries:
        print("SGE: 索引页未找到周报 PDF,跳过")
        return
    
    latest = pdf_entries[0]
    # 看 Notion 是否已有 (week_end, market=SGE)
    if notion_exists(market="SGE", date=latest["week_end"]):
        print(f"SGE: {latest['week_end']} 已存在,跳过")
        return
    
    # 下载、解析、写入
    result = parse_sge_silver_pdf(latest["url"])
    push_to_notion_v2(...)
```

## 10. 部署 4 阶段(严格顺序,不要跳)

### 阶段 A — Backfill(一次性,Antigravity 跑)

**前置 sanity check**(必须):
1. 跑 Step 1,确认能抓到 PDF 列表(至少 13 条)
2. 跑 Step 2 验证 A/B 路径,**把第一份成功抽到库存的 PDF 文本片段贴 walkthrough.md** 给用户看
3. 用户阅读后批准 → 进入正式 backfill

**正式 backfill**:跑 `backfill_sge.py`,13 周回填。每条:
- 失败 → 报告失败原因,不阻断后续
- 成功 → 写入 Notion + log 一行

**完工后报告**:
- ✅ X/13 成功
- ❌ 失败明细(URL / 周期 / 原因)
- 第一行 + 最后一行的 Notion page URL 给用户做抽检

### 阶段 B — 用户人工验收(用户做)

打开 Silver DB,确认:
1. 13 行新增,`市场 = SGE`,`库存频率 = 每周`
2. `SH库存吨` 范围 600~900 吨(SGE 银的合理量级)
3. `Silver日期` 都是周五
4. `URL` 字段可点击访问到 SGE PDF
5. 无重复行(同一周末日 + SGE 只有一条)

任一不通过 → 用户报告 Antigravity,Antigravity 修脚本,清掉脏行(用户在 Notion UI 手动 delete,我们已知 Notion MCP 没 archive 能力),重跑 backfill。

### 阶段 C — 日常 cron(用户批准后 Antigravity 推)

阶段 B 全通过后,把 §9 的 `sync_sge_latest()` 合并进 `sync_cme_to_notion.py`,push 到 main。沿用现有 GitHub Action cron(不另起新的)。

### 阶段 D — Hermes 集成(暂缓,至少等 C 跑稳 7 天)

C 稳定运行至少一周(每周二/三 SGE 出新 PDF 时正常写入,无脏数据)后,**才**回头改 Hermes prompt:
- 给 `Hermes_分析层任务_Prompt.md` §2(库存)加"东方对照"子节,从 Silver DB 读 SGE 周数据
- §0 红绿灯仪表盘可考虑加 1 列"东方库存"信号(SGE 银周环比 > +5% 视为 🟡 入库;< -5% 视为 🟠 失血)

**这步不是本任务范围,这里只是给 Antigravity 留个上下文**。本 T6 完工后用户来找我,我改 Hermes 那边。

## 11. Fail Loud 纪律(强制,违反就当 bug)

- SGE 索引页(`/sjzx/hqzb`)抓不到 PDF 列表 → **停,报告"找不到 PDF 列表",别构造瞎猜的 URL**
- Step 2 行情周报 PDF 不含库存表 → **停,报告"已转 /sjzx/xjjg 候选"或"已转 /sjzx/hjzgtjsj 候选",这两个还找不到再停**
- 单 PDF 解析失败(如正则匹配失败)→ 把 PDF 前 500 字贴 log,**不要静默跳过**
- Notion 写入 401/403 → 报告"goldptsilverupdate integration 权限问题",**别 retry**

## 12. 不在范围

- 不做 SHFE(已暂搁)
- 不做 Pt 任何东方源
- 不动 CME 现有写入逻辑(只新增 SGE 分支)
- 不动另一仓库 `Daily_CME-issuestop-inventory_Notion`(T1 的)
- 不擅自启用日常 cron(必须等用户阶段 B 验收)
- 不修改 Hermes 这边任何 prompt(那是阶段 D 的事,本任务完工后用户主动来)
- 凭证只走环境变量(NOTION_TOKEN / GH_PERSONAL_TOKEN)

---

## Sources(本任务依据)

- SGE 行情周报页面(经确认含 PDF 列表):https://www.sge.com.cn/sjzx/hqzb
- 用户提供的样本 PDF(2026-05-25 发布):https://www.sge.com.cn/upload/file/202605/25/de3b502fac4e4843b39dac9510e538a6.pdf
- SGE 主页导航(确认菜单结构):https://www.sge.com.cn/
- AKShare 接口失效记录:`ak.futures_stock_shfe_js` 和 `ak.futures_shfe_warehouse_receipt` 对 2026 年日期均失效(Antigravity v1 已实测)
