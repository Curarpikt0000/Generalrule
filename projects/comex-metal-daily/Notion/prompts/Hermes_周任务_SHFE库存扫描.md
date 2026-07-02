# Hermes 周扫描任务 — SHFE 库存周报(computer use 路线)

> 给 Hermes 的常驻周任务。**与 22:00 daily 报告任务并列**,周末跑一次,把 SHFE 沪金/沪银的周库存数据写进 Notion。
> 不走 akshare(已死)、不走 Antigravity GitHub Action(WAF 拦数据中心 IP)。**用户 residential IP + 真实 Chrome + computer use 才能过 WAF**——这是唯一可行路径。

---

## §0 触发时机

- **当地时间**:每周六 09:00 JST(= UTC 00:00 周六)
- **频率**:每周一次
- **为什么周六**:SHFE 周五 16:00 SH 时间发布上周库存数据,周六 09:00 已稳定可读
- **触发条件**:用户机器开机 + Chrome 可用 + Hermes 有 computer use 权限

## §1 执行流程

### 1.1 打开 SHFE 库存周报页

```
URL: https://www.shfe.com.cn/reports/tradedata/dailyandweeklydata/
```

打开 Chrome 新标签页跳到这里。如果 WAF 弹出滑动拼图,**人工辅助一次**(等用户在场时)或者尝试用 computer use 模拟鼠标拖动拼图。**首次设置时建议用户在场看一次**。

### 1.2 选库存周报 + 选目标日期

- 右侧"表单筛选"面板,点击 **"库存周报"**(蓝色高亮即选中)
- 中间日历,点击**上周五**(本次任务的目标日期)
- 页面下方应该出现表格(白银 + 黄金两张表上下排列,或上下切换)

### 1.3 抓 4 个数字 × 3 金属 + 1 个日期

**3 个金属:白银 / 黄金 / 铂金**(铂金视 SHFE 当周是否有数据而定)。每个金属抓:

| 字段 | 位置 | 单位 |
|---|---|---|
| 总计 → 本周期货 | 表格末行"总计"那行,"本周期货"列 | 千克 |
| 总计 → 增减 | 同上,"增减"列 | 千克 |

例(白银 5/22 截图):
- 总计 本周期货 = **986,791 kg = 986.791 吨**
- 总计 增减 = **+88,644 kg = +88.644 吨**

### 1.4 写入 Notion

调用 Notion MCP `create-pages` 写:

**Gold DB** (`2bc47eb5fd3c8083966eecfd9f396b44`):
```python
{
    "Name": f"Gold SHFE {friday_date}",
    "Gold日期": friday_date,
    "市场": "SHFE",
    "库存频率": "每周",
    "SH库存吨": gold_total_kg / 1000,
    "URL": "https://www.shfe.com.cn/reports/tradedata/dailyandweeklydata/",
    "说明": f"SHFE 沪金周库存(Hermes computer use 抓取),增减 {gold_change_kg/1000:+.3f} 吨"
}
```

**Silver DB** (`2bc47eb5fd3c80f3a71ad8de149a4943`):
```python
{
    "Name": f"Silver SHFE {friday_date}",
    "Silver日期": friday_date,
    "市场": "SHFE",
    "库存频率": "每周",
    "SH库存吨": silver_total_kg / 1000,
    "URL": "https://www.shfe.com.cn/reports/tradedata/dailyandweeklydata/",
    "说明": f"SHFE 沪银周库存(Hermes computer use 抓取),增减 {silver_change_kg/1000:+.3f} 吨"
}
```

**Pt DB** (`2d647eb5fd3c801a9ce5d5db4d0b961a`) — **仅当 SHFE 当周有铂金品种时写**:
```python
{
    "Name": f"Pt SHFE {friday_date}",
    "Pt日期": friday_date,
    "市场": "SHFE",
    "库存频率": "每周",
    "SH库存吨": pt_total_kg / 1000,
    "URL": "https://www.shfe.com.cn/reports/tradedata/dailyandweeklydata/",
    "说明": f"SHFE 铂金周库存(Hermes computer use 抓取),增减 {pt_change_kg/1000:+.3f} 吨"
}
```

⚠ **SHFE 历史上不交易铂金期货。如果当周库存周报里没有铂金品种(很可能),Pt DB 不写,只在 walkthrough 报告里说"SHFE 当周无铂金品种,Pt 行跳过"**。**绝对不要瞎填 0 或编造数字**(global rule §2.10)。

**Upsert 逻辑**(三个 DB 通用):写之前先 query (Date == friday_date, 市场 == SHFE)。存在 → PATCH;不存在 → POST。

## §2 一次性历史回填(首次任务)

第一次跑时,**循环过去 13 个周五**:
1. 周历从最新月翻到 3 个月前
2. 每个周五重复 §1.2~§1.4
3. 全部完成后报告:写入 13 周 × 2 个金属 = 26 行,失败明细

## §3 失败处理

| 失败 | 处置 |
|---|---|
| Chrome 没开 / 用户不在 | 跳过本次,记 log,周一早上提醒用户人工跑一次 |
| WAF 滑动拼图无法自动过 | 通知用户介入(Telegram / macOS notification) |
| 表格定位失败(SHFE 改版) | 截图保存 + 报告 |
| Notion 写入 401 | 检查 token,通知用户 |

按 global rule §2.10 **绝不静默吞错**。

## §4 与 daily 22:00 任务的协调

- 周扫描任务**只写 Notion 不分析**,完成后退出
- daily 22:00 任务**只读 Notion 不写 SHFE 源**,正常工作
- 周扫描失败 → daily 22:00 报告里 §2 东方对照段写"SHFE 本周数据暂缺",不阻塞整体分析

## §5 注册到 Hermes config.yaml

```yaml
scheduled_tasks:
  - name: shfe_weekly_inventory_scan
    cron: "0 9 * * 6"             # 每周六 09:00 本地时区
    timezone: "Asia/Tokyo"
    enabled: true
    requires_computer_use: true   # ★ 这个任务必须有 computer use 权限
    requires_user_chrome: true    # ★ 需要用户机器上的 Chrome 可用
    prompt_file: "/Users/chaojin/hermesagent/Comex Metal Daily Issue Report/Notion COMEX仓单日报/Hermes_周任务_SHFE库存扫描.md"
    on_failure:
      max_retries: 2
      retry_delay_minutes: 120
      notify_user_on_failure: true  # SHFE 抓失败时立即提醒,以便用户人工补一次
```

## §6 一次性首次部署 checklist

1. ✅ 在用户在场时**手动跑一次** §2 回填,确认 computer use 能过 WAF
2. ✅ 验收 Notion:Gold/Silver DB 各 13 行 SHFE 数据,日期周五,数值合理(沪金 5~30 吨 / 沪银 800~1500 吨)
3. ✅ 启用 cron,等下周六验自动跑通
4. ✅ 用户机器配置:确保周六 09:00 时机器是开的且 Chrome 可用

## §7 不在范围

- 不抓除 Au/Ag 以外的 SHFE 金属(Cu/Al/Pb/Zn 等)
- 不抓 SHFE 每日数据(只要周库存)
- 不抓 SHFE 期权(只要期货库存)
- 不修改 22:00 daily 报告任务的代码(它已经 ready 读 Notion SHFE 数据)
