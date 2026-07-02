# Hermes Workflow 07：月度三大央行资产负债表

> **触发时间**：每月 10 号 JST 12:00（PBoC 一般 5-7 号发布，BoJ 10 天周期，Fed 上月末值已确定）
> **目标**：B1 写入 3 行（PBoC + BoJ + Fed）

---

## §1 数据源

### PBoC
- **货币当局资产负债表**：http://www.pbc.gov.cn/diaochatongjisi/116219/116319/index.html
- 字段：总资产、对其他存款性公司债权、对政府债权、基础货币
- **缺失处理**：本月若未更新，沿用上月并 `数据源` URL 标注 `(上月数据)`

### BoJ
- **BoJ Accounts**：https://www.boj.or.jp/en/statistics/boj/other/ac/index.htm
- 每 10 天发布，取最接近月末值
- 折算 USD = 总资产 (¥兆) / USD/JPY

### Fed
- 取 H.4.1 月末最后一周的 WALCL / WSHOTSL / WSHOMCB / WRESBAL

---

## §2 写入 B1（3 行）

```python
for cb in ["PBoC", "BoJ", "Fed"]:
    notion-create-pages(
        parent={"data_source_id": "cc862135-410e-4623-97fe-9484f3a322f6"},
        properties={
            "Month": "2026-05",
            "央行": f"🇨🇳 PBoC" if cb == "PBoC" else ...,
            "总资产_本币": ...,
            "总资产_USD_T": ...,
            "对政府债权": ...,
            "基础货币": ...,
            "扩缩表方向": ...,
            "环比_pct": ...,
            "逻辑解读": "(DeepSeek 短评)",
            "数据源": <URL>
        }
    )
```
