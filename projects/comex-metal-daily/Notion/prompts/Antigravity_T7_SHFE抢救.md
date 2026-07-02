# T7 — SHFE 数据源抢救(akshare 备选函数)

> Hermes 分析:akshare 不是只有 1 个 SHFE 函数,你 v1 只试了 2 个失效的,**漏了第 3 个独立数据源**。先试这个,再决定要不要走 Tushare。

## 1. 背景

T6 v1 时你试的:
- ❌ `ak.futures_stock_shfe_js` 走 **金十数据 Jin10** — Jin10 改 API 挂了
- ❌ `ak.futures_shfe_warehouse_receipt` 走 **SHFE 官网直链** — SHFE 改 URL 挂了

但 akshare 内还有:
- ✅ **`ak.futures_inventory_em(symbol="沪金")`** ← **走东方财富网**(独立于 Jin10/SHFE)
- ✅ `ak.futures_inventory_99(symbol="沪金")` ← 走 99 期货网(更老备选)

东方财富是国内最大财经数据聚合,**独立 backbone**,它跟 Jin10 / SHFE 直链都不挂。极可能还活着。

## 2. 任务(2 小时内能验完)

### Step 1:试 `futures_inventory_em`

```python
import akshare as ak

# 试 4 个符号(akshare 命名可能用拼音或中文)
for symbol in ["沪金", "沪银", "Au", "Ag"]:
    try:
        df = ak.futures_inventory_em(symbol=symbol)
        print(f"✅ {symbol}: {len(df)} 行,最新日期 {df['日期'].max()}")
        print(df.head(3))
    except Exception as e:
        print(f"❌ {symbol}: {e}")
```

**期望**:`沪金` / `沪银` 返回最近 60 天每日 DataFrame,字段含 `日期`、`库存`、`增减` 等。

### Step 2:如果 Step 1 通了,验数据合理性

- 沪金库存通常 **5~30 吨** 区间(0.5~3 万千克)
- 沪银库存通常 **800~1500 吨** 区间

**注意单位**:em 接口可能用 `千克` 或 `吨`,Look at the actual values 推断。文档没说就跟最新一周 SHFE 公开新闻报道交叉核对。

### Step 3:如果 Step 1 也失败,试 `futures_inventory_99`

同样的 symbol 试一遍。99 期货是更老的中文网站,数据可能滞后但通常稳定。

### Step 4:都失败 → 转 Tushare 后备方案

Tushare 有 `ts.pro_api().fut_holding()` 这类接口,但要免费注册账号拿 token。**如果到这一步,先停下报告,等用户决定是否注册**。

## 3. 适配到 Notion

如果 `futures_inventory_em` 通,因为它是**每日**数据(不像 SGE 是周报),要么:
- **方案 X**:每天写入(频率字段 = `每日`,跟 CME 一样)——但 Hermes 分析只关心周末快照,会有噪声
- **方案 Y(推荐)**:**只取每周五的行写入**(频率字段 = `每周`,跟 SGE 对齐)——简洁,跟 SGE 对照分析

走方案 Y。代码骨架:

```python
# sync_shfe_em.py
import akshare as ak
from datetime import datetime

df_au = ak.futures_inventory_em(symbol="沪金")
df_ag = ak.futures_inventory_em(symbol="沪银")

# 过滤每周五的行
for df, db_id, metal in [(df_au, GOLD_DB, "Gold"), (df_ag, SILVER_DB, "Silver")]:
    df["日期"] = pd.to_datetime(df["日期"])
    fridays = df[df["日期"].dt.weekday == 4]  # 4 = Friday
    
    for _, row in fridays.iterrows():
        push_to_notion_v2(
            metal=metal, db_id=db_id, market="SHFE",
            date_str=row["日期"].strftime("%Y-%m-%d"),
            freq="每周",
            sh_tons=float(row["库存"]) / (1000 if unit_is_kg else 1),
            source_url="akshare futures_inventory_em (东方财富网)",
            note=f"SHFE 沪{'金' if metal=='Gold' else '银'} 周库存(每周五快照),回填于 {today}",
        )
```

跟 SGE 同样的 `市场=SHFE / 频率=每周 / SH库存吨` 字段填法。

## 4. 验收

跟 T6 同节奏:
1. Step 1~3 探索,**报告哪个函数活着**
2. 如果有活的:回填过去 90 天 ≈ 13 周五,Notion Gold/Silver DB 各加 ~13 行 `市场=SHFE` 数据
3. 用户人工核查:数值合理、日期都是周五、URL/说明字段规范
4. 通过 → 合并进 `sync_cme_to_notion.py` daily cron

## 5. Fail Loud 纪律

- Step 1 4 个 symbol 都失败 → 试 Step 3
- Step 3 也失败 → **停,报告 4 + 4 = 8 次尝试全失败,等用户决定 Tushare**
- 不要瞎试其他随机函数(akshare 还有 100+ 个 futures 函数,但跟 SHFE 库存无关)

## 6. 不在范围

- **不动 SGE 当前实现**(T6 已稳)
- **不动 Hermes prompt**(Hermes 已经准备好接 SHFE,只要 Notion 有数据就自动用)
- 不试 webworms 反 WAF(SHFE 主页人机验证强度高,不值得)

## Sources

- [AKShare 期货数据文档](https://akshare.akfamily.xyz/data/futures/futures.html) — 含 `futures_inventory_em` 接口说明
- [东方财富网期货行情](https://quote.eastmoney.com/qihuo/) — em 接口实际数据源
