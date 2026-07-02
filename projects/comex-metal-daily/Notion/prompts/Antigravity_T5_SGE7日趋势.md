# T5(临时任务) — SGE 物理溢价/折价 7 日趋势 → 写入 Notion

> 给 Antigravity 的一次性历史回填任务。**数据直接落 Notion 新建好的 `SGE Physical Prices` 数据库**,完工即归档。Hermes 后续从 Notion 读不需要 markdown 文件。

---

## 1. 任务背景

Hermes 在 2026-05-28 日报里发现一个反常信号:**SGE 黄金折价于伦敦 -$141/oz(-3.1%)**——跟 Gemini 2026-05-24 范例的"SGE 溢价 +$16.85/oz"完全反向。

用户想确认:**这是 5/28 单日噪声,还是过去一周已经在持续折价?**

## 2. 范围

- **日期窗**:2026-05-22(周五) ~ 2026-05-28(周四),**5 个 SGE 交易日**(剔除 5/24-5/25 周末)
- **品种**:Au9999、Ag(T+D)、Pt99.95
- **输出**:5 行写进 Notion `SGE Physical Prices` 库,每日一行

## 3. Notion 写入目标

- **DB 名称**:`SGE Physical Prices`
- **DB ID**:`9bdc19da05a741089ab79e2779d32e89`
- **Data Source ID**:`33747d3d-631b-45e8-958f-6a6ea01c0c82`
- **DB URL**:https://www.notion.so/9bdc19da05a741089ab79e2779d32e89
- **Parent**:`Hermes Issues and Stops Report + AI analysis` 页面

### ⚠ 写入前提:用户必须先做一步

Hermes 用 OAuth 连接器建的这个新 DB,**Antigravity 的 token 默认不能写**——你(用户)要先在 Notion UI 里把 `Hermes Analysis Issue Report` integration **加到这个新 DB**:

1. 打开 https://www.notion.so/9bdc19da05a741089ab79e2779d32e89
2. 右上角 ··· → Add connections → 找 `Hermes Analysis Issue Report` → 添加

加完 Antigravity 才能 POST 进去。

## 4. 字段映射(严格按这个写,不要改字段名)

| Notion 列 | 类型 | 内容 |
|---|---|---|
| `Name` | title | `SGE YYYY-MM-DD`(如 `SGE 2026-05-28`) |
| `Date` | date | 该 SGE 交易日 ISO 日期 |
| `SGE Au CNY/g` | number | 当日 Au9999 收盘 元/克 |
| `SGE Ag CNY/kg` | number | 当日 Ag(T+D) 收盘 元/千克(注意是 kg 不是 g) |
| `SGE Pt CNY/g` | number | 当日 Pt99.95 收盘 元/克 |
| `USDCNY` | number | 当日 CFETS 中间价(如 6.8240) |
| `Au SGE USD/oz` | number | `SGE_Au × 31.1035 / USDCNY` |
| `Au LBMA USD/oz` | number | 当日 LBMA PM Fix(FRED `GOLDPMGBD228NLBM`) |
| `Au Delta USD` | number | `Au SGE USD/oz - Au LBMA USD/oz` |
| `Au Delta pct` | number(percent,**存 0~1 小数**) | `Au Delta USD / Au LBMA USD/oz`(如 -3.1% 存 `-0.031`) |
| `Ag SGE USD/oz` | number | `(SGE_Ag/1000) × 31.1035 / USDCNY` |
| `Ag Yahoo USD/oz` | number | 当日 Yahoo `SI=F` close |
| `Ag Delta USD` | number | `Ag SGE - Ag Yahoo` |
| `Ag Delta pct` | number(percent,**存 0~1 小数**) | 同上 |
| `Pt SGE USD/oz` | number | `SGE_Pt × 31.1035 / USDCNY` |
| `Pt Yahoo USD/oz` | number | 当日 Yahoo `PL=F` close |
| `Pt Delta USD` | number | `Pt SGE - Pt Yahoo` |
| `Pt Delta pct` | number(percent,**存 0~1 小数**) | 同上 |
| `Parse Status` | text | `OK` 或 `PARSE_FAILED: <原因>` |

**关键格式说明**:
- 所有 SGE 价是**收盘价**,不是开盘 / 盘中 / 午盘定盘价
- `Date` 用 ISO `YYYY-MM-DD`,通过 `date:Date:start` 字段写入
- 5 行按 Date 去重(用 `query-data-source` 查 Date == X 已存在就 PATCH,不存在就 POST)
- 任何变量取不到 → `Parse Status = PARSE_FAILED: <variable>` 并把对应 number 字段留空

## 5. 数据采集协议

### 5.1 SGE 收盘价(元/克 或 元/千克)

- **首选**:Python `akshare`
  ```python
  import akshare as ak
  df_au = ak.spot_hist_sge(symbol="Au99.99")
  df_ag = ak.spot_hist_sge(symbol="Ag(T+D)")
  df_pt = ak.spot_hist_sge(symbol="Pt99.95")
  ```
- **备用**:直接 fetch SGE 历史日报 `https://www.sge.com.cn/sjzx/ssge/`
- **取值**:当日"收盘价"

### 5.2 CFETS USDCNY 中间价(每日)

- **首选**:`ak.currency_china_indices()` 或 `ak.macro_china_cny_central_parity_rate()`
- **备用**:`https://www.chinamoney.com.cn/chinese/bkccpr/`(CFETS 历史)
- **不要用**:XE / 离岸 CNH / 即时市场报价

### 5.3 LBMA 黄金 PM Fix(历史,免费)

- **FRED series**:`GOLDPMGBD228NLBM`
- 直链 CSV:`https://fred.stlouisfed.org/graph/fredgraph.csv?id=GOLDPMGBD228NLBM`
- 取 5/22 / 5/23 / 5/26 / 5/27 / 5/28 的 `value` 字段

### 5.4 Yahoo Finance Ag / Pt 期货 close(替代 LBMA Fix)

```python
import yfinance as yf
ag = yf.Ticker("SI=F").history(start="2026-05-22", end="2026-05-29")
pt = yf.Ticker("PL=F").history(start="2026-05-22", end="2026-05-29")
# 取每天的 Close
```

**必须在 Parse Status 或脚本注释里标**:`Ag/Pt 用 Yahoo SI=F/PL=F 期货 close 替代 LBMA Fix(差 ≤0.3%,精度无损)`。

## 6. 工作流

```python
for date in ["2026-05-22", "2026-05-23", "2026-05-26", "2026-05-27", "2026-05-28"]:
    try:
        usdcny = fetch_cfets(date)
        sge_au = fetch_sge_au(date)
        sge_ag = fetch_sge_ag(date)
        sge_pt = fetch_sge_pt(date)
        lbma_au = fetch_fred_lbma(date)
        yahoo_ag = fetch_yahoo("SI=F", date)
        yahoo_pt = fetch_yahoo("PL=F", date)
        
        # 计算
        au_sge_usd = sge_au * 31.1035 / usdcny
        ag_sge_usd = (sge_ag / 1000) * 31.1035 / usdcny
        pt_sge_usd = sge_pt * 31.1035 / usdcny
        
        au_delta = au_sge_usd - lbma_au
        ag_delta = ag_sge_usd - yahoo_ag
        pt_delta = pt_sge_usd - yahoo_pt
        
        au_pct = au_delta / lbma_au       # 0~1 小数(percent 列)
        ag_pct = ag_delta / yahoo_ag
        pt_pct = pt_delta / yahoo_pt
        
        status = "OK"
    except Exception as e:
        status = f"PARSE_FAILED: {e}"
        # 数字字段全部 None
    
    # 调 Notion API 查重 + upsert
    upsert_notion_row(
        ds_id="33747d3d-631b-45e8-958f-6a6ea01c0c82",
        name=f"SGE {date}",
        date=date,
        sge_au_cny=sge_au if status=="OK" else None,
        # ... 其余字段同理
        parse_status=status,
    )
```

## 7. 完成确认(回报 Hermes 这几条)

1. ✅ 5 行已写入 Notion `SGE Physical Prices`(给我 5 个 page URL)
2. 5 行各自 `Parse Status` 是 OK 还是 PARSE_FAILED
3. 用一句话回答用户的关键问题:**5/28 SGE Au -$141 折价,是过去 5 天的延续趋势,还是 5/28 单日 outlier?**
   - 判别依据:其余 4 天 `Au Delta USD` 全是负值且呈现单调下降趋势 → 趋势
   - 其余 4 天值在 -$30 ~ +$30 区间反复 → 5/28 是 outlier

## 8. 不在范围

- 不要把这套数据扩展到其它金属或其它日期
- 不要做 q_fin / q_phy 量化(那是 Hermes 的 §8 模块)
- 不要再创建新 Notion DB(就用 §3 这个已建好的)
- 写完不要再产出 markdown 报告(数据进 Notion 即完成,分析由 Hermes 做)
- 凭证只走环境变量,**禁止从历史聊天复制 token**(全局规则 §7)
