# Hermes 定时任务 — COMEX 贵金属日报每日 22:00 自动生成

> 给 Hermes 的常驻定时任务规范。在 `~/.hermes/config.yaml` 注册 + 触发时按本文档执行。

---

## §0 触发时机

- **当地时间**:每天 22:00(用户本地时区,目前是 JST,= UTC 13:00)
- **频率**:每天(含周末——周末跑会发现 OI/库存等没新数据,按 §1 规则跳过即可)
- **为什么是 22:00**:
  - Antigravity 的 GitHub Actions 通常**当天早晨**跑(JST 06:00 ~ 09:00),把 CME 前一交易日数据落进 Notion
  - 22:00 之前,4 张源表已经有当日所需数据 12+ 小时缓冲
  - 22:00 写完,你睡前可以看一眼

## §1 前置数据齐整性检查(强制)

执行分析前,**先查 5 张源库当日最新行的 Parse Status**:

| 库 | 期望 BD(business date) | 允许滞后上限 | 失败处置 |
|---|---|---|---|
| `Daily auto tracking`(CME 库存) | T-1(昨日) | T-2 | 全部 8 行 PARSE_FAILED → 跳过当天 |
| `OI` | T-1 | T-2 | PARSE_FAILED → 跳过当天 |
| `CFTC Con H` | 上周二报告(每周一更新) | T-10 | PARSE_FAILED → 在长文标"本期 CFTC 无新数据" |
| `SLV` | T-1 | T-2 | PARSE_FAILED → 在长文标"SLV 本期无新数据" |
| `SGE Physical Prices` | T-1 | T-2 | 没新行 → 长文 §7 退化为"SGE 本期无新数据,SIFO 跳过" |

**确定 BD(业务日期)的规则**:
```
BD = max(date among CME 库存最新 OK 行, OI 最新 OK 行)
若两者不一致(罕见,通常发生在周末/节假日),取较旧那个
```

**跳过条件(任一满足即整个任务 abort)**:
- 上面任一"❌ 跳过当天"列触发
- 整张分析库 `Delivery Notice & AI Analysis` 当日已经有非空 `Hermes Analysis ` 列(说明手动写过/已生成过)→ 不覆盖

**跳过时**:
- 不写新 page
- 把跳过原因记到 `~/.hermes/logs/comex_daily.log`
- 不通知(下次正常跑就好,不要骚扰)

## §2 数据采集(按顺序,有顺序依赖)

1. **读 5 张源库 BD 当日 OK 行**:
   - CME 库存 3 行(Au/Ag/Pt;Cu/Al/Pb/Zn/Pd 即便 PARSE_FAILED 也不读)
   - OI 1 行(读 `OI Futures (JSON)` + `OI Options (JSON)`,**记得反转义 `\\{→{` `\\}→}` `\\[→[` `\\]→]`**)
   - CFTC 1 行(读 `COT (JSON)`,同样反转义)
   - SLV 1 行(数字直接读)
   - SGE 1 行(数字直接读)

2. **东方库存数据采集**(2026-05-31 新增):
   - **SHFE Au/Ag**(读 Gold DB 和 Silver DB, `市场=SHFE` AND `库存频率=每周`,取最新行)
     - Gold DB `2bc47eb5fd3c8083966eecfd9f396b44`
     - Silver DB `2bc47eb5fd3c80f3a71ad8de149a4943`
     - 关键字段:`Gold日期`/`Silver日期`、`SH库存吨`(吨)
   - **SGE Ag**(读 Silver DB, `市场=SGE` AND `库存频率=每周`,取最新行)
     - 关键字段:`Silver日期`、`SH库存吨`(吨)
   - **不同步说明**:SHFE 周六 09:00 JST 更新(launchd);SGE 由 Antigravity GitHub Action 维护
   - **滞后的处理**:如果最新可用周次不是本周,用该周数据并在说明加"东方源数据滞后,使用上周 X-XX 快照"
   - **两源都失败**:Ag 东方库存 cell 写"⚠ 数据暂缺",绝不瞎填

2. **外部数据补充**(如有 web search 工具)按 `Hermes_分析层任务_Prompt.md §7` 执行
   - SOFR / Term SOFR 代理 → FRED `DGS3MO`
   - LBMA 替代 → Yahoo `GC=F`/`SI=F`/`PL=F` 当日 close
   - 大行观点(Daniel Ghali / Christopher Louney 等)→ 搜索引擎
   - **查不到就明白写"未获取",不要编**

3. **SIFO 量化**:按 `Hermes_SIFO_量化模块.md §8` 执行
   - 5 个变量取齐后,**先列原始数据再算 q**
   - 应用方向判定(`ΔS > 0` vs `ΔS < 0`)再套阈值表

## §3 分析与组织(按 v3 红绿灯)

完整按 `Hermes_格式改造单_v3_红绿灯.md` 执行:
- §0 风控仪表盘(顶部 18 灯表)
- §0.5 三条战术(顶置)
- §1~§7 各节加灯 + 篇幅按颜色压缩
- §8 SIFO 三步审计加灯
- §9 首席风控官结语(真相缺口 / 脱节判决 / 三战术)

## §4 写入 Notion(upsert)

目标库:**`Delivery Notice & AI Analysis`**(DB `2be47eb5fd3c80bab065f188139834b9`)

```python
# 伪代码,Hermes 用 Notion MCP 实现
existing = query_data_source(
    data_source_id="2be47eb5-fd3c-81d8-985b-000b6ed57171",
    filter={"property": "Date", "date": {"equals": BD}},
)
if existing:
    page_id = existing[0]["id"]
    update_page(page_id, command="replace_content", new_str=long_form_markdown)
    update_page(page_id, command="update_properties", properties={
        "Hermes Analysis ": short_comment,   # ← 必带尾随空格
        "Period": "Daily",
    })
else:
    create_pages(
        parent={"data_source_id": "2be47eb5-fd3c-81d8-985b-000b6ed57171"},
        pages=[{
            "properties": {
                "Name": f"COMEX 日报 {BD}",
                "Date": BD,
                "Period": "Daily",
                "Hermes Analysis ": short_comment,
            },
            "content": long_form_markdown,
        }],
    )
```

**特别注意**:
- `Hermes Analysis ` 列名**带尾随空格**,写错就 422
- 短评 ≤ 1900 字符
- 长文用 `replace_content` 时如果有 children pages 会报错(本 DB 不会,但记着)

## §5 完成后通知

通知通道(三选一,看 Hermes 接哪个):
- **Telegram bot**(用户已确认有,直接发消息到指定 chat_id)
- **macOS osascript 通知**(`display notification`)
- **写文件**到 `~/Desktop/COMEX日报状态.txt`

**通知内容(简洁)**:

```
📊 COMEX 日报 {BD} 已生成
🥇Au {🟢/🟡/🟠/🔴} | 🥈Ag {🟢/🟡/🟠/🔴} | ⚪Pt {🟢/🟡/🟠/🔴}
{综合最严重灯} {一句战术}
🔗 https://www.notion.so/{page_id}
```

例:
```
📊 COMEX 日报 2026-05-28 已生成
🥇Au 🟡 | 🥈Ag 🟠 | ⚪Pt 🔴
🔴 铂金小仓位埋伏 5% 仓位
🔗 https://www.notion.so/...
```

## §6 失败处理

| 失败类型 | 处理 |
|---|---|
| §1 数据齐整性失败 | 跳过当天,记 log,不通知 |
| §2 web search 失败 | §7 退化为"外部数据未获取",继续 §3 |
| §3 LLM 自身报错 | 重试 1 次,30 分钟后 |
| §4 Notion 写入失败(401/403) | 检查 token,通知用户"权限失效",abort |
| §4 Notion 写入失败(429 限流) | 退避 5 分钟,重试 3 次 |
| 二次重试仍失败 | 通知用户 + 把生成的长文 dump 到 `~/Desktop/COMEX日报_{BD}_备份.md` |

**所有路径都不要静默吞错**——按 global rule §2.10 Fail Loud,失败必须留痕。

## §7 配置(写进 `~/.hermes/config.yaml`)

```yaml
scheduled_tasks:
  - name: comex_daily_report
    cron: "0 22 * * *"          # 每天 22:00(本地时区)
    timezone: "Asia/Tokyo"       # 改成你的本地时区
    enabled: true
    prompt_file: "/Users/chaojin/hermesagent/Comex Metal Daily Issue Report/Notion COMEX仓单日报/Hermes_定时任务_每日22pm报告.md"
    referenced_prompts:
      # Hermes 启动这个任务时,这几份文件一起加载到 context
      - "/Users/chaojin/hermesagent/Comex Metal Daily Issue Report/Notion COMEX仓单日报/Hermes_分析层任务_Prompt.md"
      - "/Users/chaojin/hermesagent/Comex Metal Daily Issue Report/Notion COMEX仓单日报/Hermes_格式改造单_v3_红绿灯.md"
      - "/Users/chaojin/hermesagent/Comex Metal Daily Issue Report/Notion COMEX仓单日报/Hermes_SIFO_量化模块.md"
      - "/Users/chaojin/hermesagent/Comex Metal Daily Issue Report/Notion COMEX仓单日报/Hermes_通知_SGE+SHFE东方库存上线.md"
    on_failure:
      max_retries: 1
      retry_delay_minutes: 30
      notify_user_on_final_failure: true
    logging:
      log_file: "~/.hermes/logs/comex_daily.log"
      log_level: "INFO"
```

**如果 Hermes 的 scheduled_tasks 字段名不是这个**,把 `cron` / `timezone` / `prompt_file` / `referenced_prompts` 这几个语义概念映射到它实际的字段名即可。

## §8 第一次部署的 sanity test

正式启用前,**手动触发一次跑 5/28 数据**:

```bash
hermes run --task comex_daily_report --dry-run --date 2026-05-28
```

(或者 Hermes 等价命令)

**期望产出**:
1. ✅ 长文 page URL
2. ✅ 短评里 3 个灯都出现且匹配 §0 仪表盘
3. ✅ §9 结语含"真相缺口"和"脱节判决"两个词
4. ✅ 通知到达指定通道
5. ✅ log 文件有完整执行记录

任一不通过,**先修再启用 cron**——别把坏的部署成每日。

## §9 维护与监控(每周一次,手动)

每周一上午,用户自己:
- 翻 `~/.hermes/logs/comex_daily.log` 看上周 5~7 次执行是否都成功
- 翻 Notion `Delivery Notice & AI Analysis` 看上周 5~7 行是否都齐
- 缺失的:查 log 看失败原因,补救

每月一次:
- 复查 5 张源表 Parse Status 失败率,如果高于 5%,找 Antigravity 修对应 parser
- 复查 Hermes Analysis 列的短评质量(没有进步说明 prompt 需要调)

## §10 不在范围

- 不要让 Hermes 在这个定时任务里"顺手"修源表数据
- 不要让 Hermes 跑历史回填(那是 Antigravity 一次性任务,T5 那种)
- 不要让 Hermes 直接调用 GitHub Actions
- 凭证只走 `~/.hermes/config.yaml` + 环境变量
