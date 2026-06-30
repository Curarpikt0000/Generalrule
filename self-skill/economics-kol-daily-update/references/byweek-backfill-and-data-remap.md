# By Week 历史回溯 + KOL 数据归属错配修复

> 三个本会话(2026-06-21/22)固化的可复用工作流。都遵守 Chao 铁律：
> **零遗漏逐源核对、声称成功必须自己读回验证(子 agent 自报不算数)、不可逆操作先确认、宁缺毋滥零编造。**

---

## A. By Week 历史回溯（多 DB 项目的覆盖盲点）

### 核心教训（首要）
**By Day 回溯了 ≠ By Week 也回溯了。两个 Notion DB 完全独立。**
本会话踩的坑：早先把 KOL By Day 补到 2025-11，以为"历史回溯做完了"，但 By Week 最早只到 2026-W11，漏了 21 周——是 Chao 主动点出才发现。
→ **铁律：多 DB 项目，每个目标 DB 都要单独跑覆盖核对，不能因为主表补了就假设附表也补了。**

### By Week 的粒度（确认过的口径）
- **每周一行的全市场综合周报**（不是每 KOL 一行，也不是每 sector 一行）。
- 一行 = 该周所有 By Day 观点综合成的多空综述。
- 字段：`Key Insight`(title) / `Comments` / `Sector`(select) / `Detail Sector`(select) / `Week Number`(number) / `多空标的` / `Date` / `Suggestion`。
- **Week Number** = 该年的 ISO 周号（2026 的周用 ISO 11~25，2025 的周用 ISO 44~52）。跨年时 Week Number 会重号/乱序（44 > 24），**靠 `Date` 字段（该周周一）做真实时间排序**，Week Number 仅作标签。
- 风格模板（必须对齐已有行）：
  - Key Insight：`W{周号} {一句多空综述}（{周一日期}）`
  - Comments：分板块用【贵金属】【宏观】【能源】【加密】【国债】标记 + 点名具体 KOL + 逻辑链(→)
  - 多空标的：`🟢 GLD(黄金ETF), SLV(白银ETF) | 🔴 TLT(长期美债), UUP(做多美元)`，从 By Day 的 targets 提炼
  - Suggestion：可操作配置建议

### 回溯流程（脚本化 + 子 agent 编排）
1. **导出缺口周**：`scripts/export_week_entries.py` —— 拉全量 By Day 按 ISO 周分组 + 拉现有 By Week 周集，自动算缺口(=有 By Day 无 By Week 的周)，把每个缺口周的观点导出成 `data/week_backfill/<year>-W<wk>.json`（含 entries[]: date/kol/sector/detail_sector/kol_or_ib/key_insight/comments/targets/suggestion）+ `_index.json`。
2. **子 agent 批量综合**：每批 3-4 周（早期周观点少可多塞），子 agent 读它负责的周 JSON → 综合成周报 → 调写入库 → 读回验证。并发上限 3。给子 agent 的 context 必须贴：风格样例 + 加权多空原则 + 写入命令 + 验证命令。
3. **写入库**：`scripts/write_week_report.py <report.json>` —— 幂等(已存在 Week Number 跳过) + select 合并 + rich_text 自动分块(<2000 字符 Notion 限制，按 1900 切)。report JSON：`{year,week,week_start,sector,detail_sector,key_insight,comments,targets,suggestion}`。
4. **加权多空原则**（综述里体现，不是简单数人头）：方向反转/新观点权重高；常年持仓派维持原立场权重低；综述反映该周**新增**观点的多空强度。零编造——entries 里没有的标的/方向绝不硬编，观点少就如实写简短。

### 验证（自己做，不信子 agent 自报）
构造 `起点周~终点周` 的连续 ISO 周期望集，与实际 got 集求差，**MISSING 必须为空**。检查无 thin Comments(<20字)、统计每行 cm/tg/sg 长度。最终行数 = 原有 + 新增。
```python
# 期望连续周序列
d=datetime.date.fromisocalendar(2025,44,1); end=datetime.date.fromisocalendar(2026,25,1)
expected=[]
while d<=end: iso=d.isocalendar(); expected.append((iso[0],iso[1])); d+=datetime.timedelta(weeks=1)
missing=[w for w in expected if w not in got]  # 必须 == []
```

---

## B. KOL 数据归属错配修复（一个 select 名下混了多来源数据）

### 场景
核实某 KOL 记录时发现：**一个 `Name of KOL` select 值名下混挂了多批完全不同来源的数据**。本会话实例："Anu Anand"(占星师)名下 21 条里，3 条是真占星，18 条是大宗商品/能源基本面分析(早期管道错挂)。
→ **教训：验证 KOL 数据不能只看名字，要看内容。一个 select 名下可能混了多个真实作者的数据。**

### 识别 + 归属查证流程
1. **按内容分组**：拉该 KOL 全部记录，读完整 Comments(不是摘要)，按内容特征分组(板块/论点框架/标的偏好/引用对象)。本会话用占星标记【占星预测·低权重】vs Energy&Commodities 大宗周期。
2. **归属判断(子 agent)**：把错配那批的内容特征 vs registry 全部 KOL 背景(focus/bio/sector)比对。三类证据找强候选：
   - **registry focus 字面命中**（如 McDonald 的 focus="商品牛市框架+被动ETF泡沫+硬资产逆向" 三词全中）
   - **同库已正确归属记录是同模板**（同一作者的术语/标的配对/逻辑链一致）
   - **引用习惯吻合**（反复引用同一批评论员/数据源）
   注意区分"被引用的人"(如 Michael Pinto/Dan Drifus 出现在正文但不在 registry → 是被引用对象不是作者)。
3. **诚实声明置信度**：无法 100% 证明每条原话时如实说，但整批三重证据一致即可高置信归位。

### 处置（让 Chao 拍板，不可逆不自治）
- 选项给全：A=改挂到正确 KOL / B=先查归属再决定 / C=删除 / D=贴内容给用户自己判断。
- **改挂前必做**：(1) 核实目标 select option 精确拼写已存在(避免新建孤儿)；(2) 看目标 KOL 同库记录的 Sector/Detail Sector 用什么(对齐)；(3) **备份这批记录原始状态到 scratch/**(可回滚)；(4) 安全断言(改前确认全是源 KOL 名，否则 abort)。
- 改挂 = 逐条 PATCH `/v1/pages/<id>` 改 `Name of KOL` + `Sector` + `Detail Sector`(都用已有 option)。加 time.sleep(0.35) 防限流。
- **改挂比删除更保值**：18 条有逻辑链的真实观点归位到正确作者 > 直接删掉。

### 验证
读回确认：源 KOL 名下只剩应留的；目标 KOL 名下 = 原数 + 改挂数；改挂的记录 Sector 全部正确(0 条异常)。

---

## B2. 脏 KOL 名的两种数据腐烂（hex 验证磁盘真实字节）

> 这是 B 的姊妹场景：B 处理"真实内容但名字错配"，B2 处理"名字本身是脏字符串/记录是垃圾"。区分关键 = **先 hex 验证磁盘真实字节，再决定还原还是删**。

### 腐烂类型 1：脱敏字符串当真名写进了磁盘
- **症状**：dashboard/Notion 里 KOL 名显示为 `ANONYMIZED_PERSON_0` 之类，反转信号里出现"ANONYMIZED_PERSON_X 看空→看多"。用户问"这是谁，找不到人就删"。
- **关键区分（最容易踩错）**：聊天/工具输出里的 `ANONYMIZED_PERSON_*` 通常是 redactor **显示层临时脱敏**，磁盘真实字节是正确人名——**这种不能盲信不能 regex 删**。但本会话发现【更糟的一类】：脱敏字符串被早期某次子 agent 当真名【真的写进了 Notion 磁盘】。
- **诊断 = hex 验证**：读出 KOL 名后 `name.encode().hex()`。若 hex = `414e4f4e594d495a45445f...`（="ANONYMIZED_PERSON_..." 的字面字节）→ 磁盘真的存了脱敏字符串(脏)。若 hex 解出正常人名(`526f626572742047...`="Robert G...")→ 只是显示层脱敏(干净，别动)。
  - registry 里的真名在 terminal 显示时也会被脱敏成 ANONYMIZED_PERSON_X——比对时信任 hex 字节/内容匹配逻辑，别被显示误导。
- **还原 vs 删（Chao 规则：能还原就还原，找不到才删）**：脏名记录的 **Comments 内容往往是真实观点**(只是名字丢了)。读完整 comments 找作者线索(点名"Gottlieb"、职务"High Ridge 芝加哥金属交易主管"、机构"Amplify ETFs 副总裁")→ 比对 registry → 能高置信认出就改挂回真名(同 §B 流程)；认不出(泛泛宏观评论多人皆可言)就删。本会话 31 条 → 改挂 16(David Meger 10/Gottlieb 4/Nate Miller 2) + 删 15。
  - ⚠️ 正文里也可能有脱敏字面量(如"Amplify ETFs 副总裁ANONYMIZED_PERSON_0")→ 靠职务/机构上下文还原，不靠那个脏 token。

### 腐烂类型 2：空 KOL 名 + 臆测/占位垃圾内容
- **症状**：dashboard 脚本 legged_rows < total(本会话 1950/2020)，差额 = 一批 `Name of KOL` 为空的记录。聚合脚本 `if not kol: continue` 会静默跳过它们(导致覆盖率计数对不上——这是个有用的"探针")。
- **识别垃圾特征**（这批该全删，跟类型1不同——内容本身就是垃圾）：
  - **臆测体**："Doomberg **会**认为…""瑞银**可能**发布报告…""Druckenmiller **强调**…"——AI 臆测某 KOL 会说什么，**违反零编造**，不是真实抓到的观点。
  - **机构混入**：瑞银/UBS/花旗/Citi（机构不算 KOL）。
  - **跨域噪音**："Ivan Zhao 作为 Notion CEO"——科技公司 CEO 根本不是经济 KOL。
  - **无锚点模板**："白银兼具工业和货币属性"这种无来源、无日期锚点的通用话。
  - 时间集中在项目早期(本会话 2026-03~04，早期管道产物)。
- **处置**：备份后全删(archived:true)。这类无真实来源+无法归属+违反零编造，留着污染 dashboard。删前安全断言"都是空 KOL 名"，幂等脚本(重查空名再删，已删不重复)。
- **删除会超时**：70 条 × sleep(0.3) + API 延迟 > 60s 前台限制。用 background=true + notify_on_complete，或分批；幂等脚本可安全重跑续删。

### 通用：dashboard 覆盖率是数据脏的探针
`generate_dashboard_data.py` 打印 `已结构化方向: X/Y`。X<Y 且差额不随回填减少 → 多半是空 KOL 名记录被 `if not kol: continue` 跳过。这是发现脏数据的免费信号，别忽略。

---

## C. 占星/预测类 KOL 的低权重隔离（叙事监控）
占星师等无可证伪方法论的 KOL，若 Chao 决定纳入(作叙事/情绪监控，因其能影响散户情绪)：
- registry 加 `weight_class=low` + `monitor_type=叙事/情绪监控`。
- **每条 Comments 开头强制标 `【占星预测·低权重】`**，以便和基本面分析师区分、在加权评分里降权隔离、不与基本面同权。
- 一手抓取验证频道名(本会话发现 Abhigya Anand 真实频道是 "Praajna Jyotisha" @praajnajyotisha 1.23M，不是先前以为的 "Conscience"——纯 web 搜索给的频道名可能错，agent-browser 抓一手才准)。
- 占星类经济内容偏少且含糊 → 含糊处如实写含糊，不硬推具体多空(零编造)。
