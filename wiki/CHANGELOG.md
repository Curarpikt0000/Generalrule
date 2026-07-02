# Wiki CHANGELOG —— 知识库版本管理

> **纪律来源**：general-global-rule.md §6（每次写 Wiki 须在此留记录）。
> **本文件管**：`wiki/` 下**知识页**的新增 / 删除 / 修改 / 迁移，以及**领域目录**的增减。
> repo 结构性改动（规则文件、模板、self-skill）记在根 `CHANGELOG.md`，本文件不重复。
> **记录格式**：`### 日期`，正文逐条 `[动作] 领域/页面 —— 说明`。动作 = 新增 / 删除 / 修改 / 迁移 / 重写。
> 写 wiki 优先调用 `self-skill/llm-wiki` skill，产出须符合 [[wiki-ingest-guide]]。

---

## 记录

### 2026-07-02 —— akshare 东财口径绕过 SHFE WAF（Hermes, Opus 4.8 [UB]）

- **[修改] `crawler/shfe-waf-bypass.md`** —— 给 akshare 方案「平反」并升为首选。**背景**：原页面（2026-05）判定「方案 2 akshare ❌ 失败」，理由是 `ak.futures_shfe_warehouse_receipt()` 内部直连 www.shfe.com.cn 撞 WAF。**修正（2026-07-02 实测）**：不是 akshare 不行，是接口选错——akshare 对 SHFE 有多个接口，官方口径撞 WAF，**东财口径 `ak.futures_inventory_em(symbol="沪金"/"沪银")` 走东方财富镜像、根本不发往 SHFE 官网、完全绕过长亭 WAF，且每日更新**（实测 2026-07-01 沪金 111648 / 沪银 822698）。这比原「最终方案」Playwright stealth（方案 5）更优——纯 API、无浏览器、0 WAF 风险，故将 akshare 升为⭐首选、Playwright 降为备用。附带同域可用接口：`ak.spot_hist_sge()`（SGE 现货 S_phy）、`ak.currency_boc_sina("美元")`（USDCNY）。**教训**：一个库有多接口时别测一个失败就判整库不可用（呼应 general rule「否定性结论要穷尽验证」）——同一交易所常有「官方口径 vs 第三方镜像口径」两套，撞 WAF 时换镜像口径。来源：COMEX 日报项目交接时实测。frontmatter last_updated→2026-07-02、keywords 加 akshare/futures_inventory_em/eastmoney/sge。

### 2026-07-01 —— Presto/Quark 超重多表 join 查询优化经验（Cursor, Opus 4.8 [UB]）

- **[新增] `engineering/presto-quark-heavy-join-query.md`** —— 来自 Uber 内部 Slack 只读检索（#presto-user-group / #querybuilder / #spark，含官方 oncall 与 SODA/BMO 机器人）+ engwiki TE0PRESTO / "Presto on Spark" 指南，检索日期 2026-07-01。**核心知识**：①**红线**——Presto 单查询集群侧硬超时=30min（不含排队、改不了、报 `EXCEEDED_TIME_LIMIT ... 30.00m`）；queryrunner 客户端 polling 超时可另配加长但顶不动集群 30min；唯二解=压回限额内或换 presto-on-spark(Quark)。②**join 优化清单**：大 fact 表 join 靠前、只用简单 equi-join、避免 output>input 爆炸 join、分窗跑再拼、`SET session hash_partition_count=64` 增大并行、仍重则转 Quark。③**分区裁剪硬要求**：不过滤全部分区列直接被拒 `Filters need to be specified on all partition columns`；更紧 datestr 裁扫描；确认 join 表同 region 且都带分区过滤（remote-read scan 拖慢打网络）。④**基于 Spark 物理计划的重 join 改写**：先把驱动表裁成 CTE 再 join→SortMergeJoin 转 broadcast 免全量 shuffle（LIMIT 放最后=反模式）、合并同表多次 scan、被 join 大表也加严格分区过滤（7天缩1天）。⑤**Quark 实操**：需 YARN queue 权限；QueryBuilder 不支持传 spark session 属性→走 uWorc presto job 或 queryrunner python client 的 `source_attributes`（例 `{"spark.yarn.queue":"hive-stats"}`）；`Kryo ... Buffer overflow`→`spark.kryoserializer.buffer.max=512m`。⑥**BMO/SODA checklist**：sargable 过滤别把分区列包函数里、只 select 需要列、join 前 pre-aggregate、逼 broadcast、热点 key salting、聚合下推、盯 spilled bytes>0、避免无 LIMIT 全局 ORDER BY 与超大 window、小文件 compact。⑦Hive/Presto view 不阻断分区裁剪、可落中间表。诚实标注：来自内部 Slack 检索、"finch fast path" 未找到对口内容、quark=presto-on-spark 已确认、不含项目专有细节。交叉链接 [[queryrunner-mcp-fetch-rows-and-queue]]。同步登记 `index.md` 第 2 层 + `engineering/README.md`（engineering 域已存在，第 1 层无需改）。

### 2026-06-29 —— queryrunner-MCP 取数突破 50 行（fetch_rows）+ 后端排队拥堵应对（Hermes default, Opus 4.8 [UB]）

- **[新增] `engineering/queryrunner-mcp-fetch-rows-and-queue.md`** —— Chao 纠正长期错误认知后沉淀。**核心知识**：①`get_execution_results` 的 50 行**不是硬上限**——请求参数 **`fetch_rows`**（如 `{"execution_uuids":[...],"fetch_rows":20000}`）可调高、无硬上限、传多少拿多少；之前误试的 `limit/offset/page_size/max_rows/row_limit` 确实被忽略，正确参数名是 `fetch_rows`。→ 常规全量提取直接走 MCP，**不必为破行数限制而绕 `queryrunner_client`+exeggutor（flaky 后端）**。②第二逃生通道=浏览器 querybuilder scratchpad「Download as CSV」+ 取消 Limit 复选框=无限制下载。③后端 `started_waiting_to_execute` 长时间不动=队列拥堵（环境侧波动，非并发槽，cancel 清空重提仍卡）→ 不干等，起静默重试 watchdog（background+notify）周期重提、成功落地、失败安静，同时把工作 pivot 到不依赖后端的部分；watchdog 区分确定性失败（列 CLAC 加密→不重试）vs 排队/duplicate（下轮重提）。同步登记 `engineering/README.md`（index.md 第一层无需改，engineering 域已存在）。同步纠正 skill `uber-gr-finance-analysis` 旧的「50 行硬上限」段。
### 2026-06-27 —— Hermes 多 profile 运维与重启 + antml/`call:` 本地补丁沉淀（Claude Code, Opus 4.8 [UB]）

- **[新增] `agent-rules/hermes-multi-profile-watchdog.md`** —— 一次性修好 3 个 Uber profile（u-dara/u-financer/u-consultant 自 6/25 重启后实质空转、跑旧代码）后沉淀。**核心知识**：①架构=4 profile 各自独立 token/state.db/日志但**共用** `localhost:8800` LLM 代理（单点，隧道 `502 [Errno 99]` 一挂 4 个全挂）；②**最大陷阱「活着≠在干活」**——`multi_watchdog.log` 的 `OK alive` 只是进程级 ping，真健康要查该 profile `logs/agent.log` 最近有没有 `API call #`；③**profile 不热更新代码**，给 `~/.hermes/hermes-agent/` 打补丁后须**逐个重启**每个 profile 才生效（本次 3 个 Uber profile 一直跑 6/25 旧代码没吃到 antml/`call:` 补丁）；④**重启坑**：token-scoped 锁在 `~/.local/state/hermes/gateway-locks/telegram-bot-token-<hash>.lock`（不在 HERMES_HOME 下），删 HERMES_HOME 的 gateway.lock 不够；multi_watchdog cron 会和手动重启**抢着拉起同一 profile→撞 token 双双退出**（gateway.out 两次 "Gateway Starting" 即此），watchdog 是 token-conflict-aware 撞一次会让路；⑤正确手法=精确按 `/proc/<pid>/environ` 的 HERMES_HOME kill→等优雅退出清锁→逐个 `setsid env -i HERMES_HOME=... hermes gateway run` 起+逐个 verify。同步登记 `agent-rules/README.md`。

- **[修改] `llm/tool-call-emitted-as-text.md`** —— 补两节：①**变体「悬空 `call:` 断点」**——模型吐 `call:` 引子后无 `<invoke>`/工具名、`finish_reason=stop`+`tool_calls` 空，消息停在 `call:` 死等用户；务必区分 `finish_reason=tool_calls`（正常引子，别误杀）vs `=stop`（真断）；Hermes 自己修不了的三因（stop 时模型没被再调用→当下无人察觉 / 历史污染自我模仿 / antml salvage 无 `<invoke>` 不触发）。②**已实装的本地补丁 A+B+C**（上游原生只认 OpenAI 格式、`git grep` 零命中、官方修不了→本地改 `agent/agent_runtime_helpers.py` + `agent/conversation_loop.py`）：A 剥离 antml 文本、B 解析 `<invoke>` 抢救成结构化调用、C 检测悬空 `call:` 并 nudge 重发（正则对 recall/API call/subprocess.call( 零误伤）；附清污染会话历史（venv python UPDATE state.db 去尾）。强调**改后须逐个重启 profile**（指向 [[hermes-multi-profile-watchdog]]）。


- **[新增] `engineering/rag-chatbot-first-build-pitfalls.md`** —— 首次为内部 Slack 频道构建三层降级 RAG 问答 bot，上生产前做完整 code review（逐文件审 + 独立 reviewer subagent fail-closed 交叉验证 + 亲自复核最高危项），发现 3 个阻断上线的 Critical，提炼为脱平台通用知识（Slack/Telegram/Discord 均适用）。**4 大坑**：①**共享账号下的自回复死循环**（最隐蔽）——bot 与人类共用账号、回复走用户 OAuth token 发出故不带 `bot_id`，用 `m.get("bot_id")` 过滤自己的消息完全失效，当下不死循环纯属"回复恰不以触发词开头"的偶然；正解=用发送方追加的稳定签名（如 `*Sent using*`）判定自己的消息，且顶层+线程两个过滤点都要应用，上线前真实账号实测一轮。②**缓存是防编造逻辑的后门**——L1 缓存命中返回 `sources=[]`（违反"必带来源"）且永不过期（数据每日刷新后返回陈旧答案）；正解=缓存存 sources 命中回填 + TTL 对齐刷新周期 + 坏时间戳当过期。③**chatbot 质量住在分支里，零测试=裸奔**——防编造/降级/路由/触发词全是判定逻辑，最易被迭代改坏；正解=写不依赖 LLM/向量库/网络的纯逻辑单测（monkeypatch 把缓存/state 路径指向临时目录），26 测 <2s 兜底。④**长跑 bot 的 state 必须原子写**——游标/去重表用 `json.dump(open(...))` 崩溃会留半截文件破坏崩溃重试与自回复去重；正解=tempfile+os.replace。**通用箴言**：聊天机器人会对自己说话；任何快路径/缓存/早返回都可能绕过慢路径的安全/合规逻辑要补回；代码工艺好≠可上生产，独立 fail-closed reviewer 总能发现作者盲点。同步登记 `index.md` 第 2 层 + `engineering/README.md`。

### 2026-06-25 —— 搜索 wiki 正名为「搜索工具栈」，GenAI grounded 从"推荐主力"改写为"项目级辅助兜底"（Hermes default, Opus 4.8 [UB]）

- **[迁移+重写] `engineering/uber-genai-gateway-web-search.md` → `engineering/uber-hermes-web-search-stack.md`** —— Chao 2026-06-25 拍板核心事实：**SearXNG 是公网搜索主力/默认兜底；GenAI Gateway grounded search 只是【项目级可选辅助兜底】，不是标准搜索步骤之一**（AI-Guard 对人名做 PII 匿名化，搜人名不可靠）。改写：①文件正名（不再以 GenAI 为题）；②标题/frontmatter 重写为「公网搜索工具栈与兜底层级」；③**置顶权威小节**明确标准层级（L1 SearXNG→L2 ddgs；GenAI 仅可选）+ 记录两条正在跑的真实降级链（usearch CLI：SearXNG→GenAI 辅助→ddgs；Economy-KOL backfill：Exa→Tavily→SearXNG→ddgs，已删 GenAI）；④删除原「Exa→GenAI→ddgs 推荐降级链」等把 GenAI 当主力的误导措辞，GenAI 教程段保留但加「历史/辅助方案，非标准步骤」横幅并说明 PII 局限为降级根因；⑤保留 usearch CLI / Cerberus idle 保活等技术事实内容（措辞对齐：GenAI 标注为辅助层）。**不管是谁写的，以最新事实对齐。** README 索引同步更新文件名与定位。

- **[修改] `engineering/uber-genai-gateway-web-search.md` 的 README 描述** —— 原拟把 GenAI Gateway grounded search 推广为通用免费联网方案，**实测发现致命局限**：AI-Guard 对 prompt 做 PII 匿名化，人名查询不稳定（76 KOL 抽测仍有 1 人 Daniel Ghali 被匿名化截断、9 人综述未直呼全名）；"去空格连写"绕过只是缓解非根治。**结论：不适合"按人名精确搜索"的 KOL 监控**。Economy-KOL 项目已改用**自托管 SearXNG**（localhost:8888，可搜真名零截断、免费不断粮），降级链定为 **Exa→Tavily→SearXNG→ddgs**（项目专属，不外推）。GenAI 相关搜索逻辑已从项目 `backfill_one.py` 移除。该 wiki 文件本体的 usearch CLI / Cerberus idle 内容由另一 Hermes 实例维护，保留不动。

### 2026-06-24 —— 模型把工具调用写成正文 antml 文本 + 上下文污染循环（Claude Code, Opus 4.8 [UB]）

- **[新增] `llm/tool-call-emitted-as-text.md`** —— Hermes(default profile, claude-opus-4-8 via custom/genai 网关) 反复把工具调用打成 antml 文本（`<invoke name=…>`）塞进正文而非结构化 `tool_calls` → 不执行（任务失败）+ 不被清理（用户可见）。根因两层：①harness 没原生下发工具（疑 `tool_search` 诱发）→ 模型按 antml 编造调用；②harness 的泄漏清理只认 `<tool_call>`/`<function_calls>`/`<function>`，不认 Claude 的 `<invoke>`/`<parameter>`。核心机制=**自我污染循环**：坏输出进历史→模型照抄自己历史→反复犯、从会话内无法自愈（实测某会话 164 条里 31 条=18% 是文本调用）。修复：弃用污染会话开新对话 / 关 `tool_search` 让工具原生下发 / 上游修复格式识别。**通用教训**：工具调用是独立结构化通道非正文；坏输出进历史会自我强化，反复犯同一格式错先疑上下文污染、优先换干净会话。同步登记 `index.md` 第 2 层 + `llm/README.md`。

### 2026-06-22 —— GenAI proxy v3：超时/异常兜底修「伪装成掉线的 Connection error」（Claude Code, Opus 4.8 [UB]）

- **[修改] `agent-rules/hermes-genai-api-integration.md`** —— 新增**坑 7**：proxy `urlopen(timeout=120)` 写死 120s，超大对话（`msgs=244 tokens=~99,725`）上游 >120s 超时抛 `TimeoutError`（非 `URLError` 子类，旧 `except` 接不住）→ handler 线程崩 → 连接硬断 → Hermes 只看到 `APIConnectionError: Connection error`（像掉线，且**绕过 fallback**，呼应坑 2）。确诊关键：retry 真实间隔 ~122s 精确指向 120s 超时；隧道全程健康。修复（已实装 genai_proxy.py v3）：超时 120→600s（`GENAI_UPSTREAM_TIMEOUT`）+ 补 `except (TimeoutError, socket.timeout)`→504 + 兜底 `except Exception`→502，保证任何异常都返回干净错误码不断连。**通用教训**：转发/代理类服务的上游超时或任何异常都必须转成干净 HTTP 错误码，绝不能让异常冒泡断连（否则下游误判为掉线 + 绕过基于错误码的 fallback）。
- 注：本页 frontmatter 与 §3.2（v2→v3 标注）由本机另一并发写者（Hermes/agent）在同一时段一并更新，内容一致、已合并；坑 7 与本 CHANGELOG 条目由 Claude Code 补齐。

### 2026-06-19 —— 轮询式双向 bot + 多源管道单源硬超时隔离（Hermes-VM, Opus 4.8 [UB]）

- **[新增] `engineering/polling-bidirectional-bot-and-source-timeout-isolation.md`** —— 两个可通用的可靠性工程模式（已匿名化，不含任何公司/内部系统/站点名）。**模式一·轮询式双向 bot**：消息平台无事件回调（webhook 禁用 / socket 要重审批）时，用「定时轮询读 API + 游标去重 + thread 回复」模拟双向问答；关键决策——触发前缀过滤、**游标必须在「回复成功后」才推进**（不是读到就推进，否则崩溃即丢消息）、无新输入静默不刷屏、剥除发送 API 的签名尾巴污染、多人频道开放执行权前必须定能力边界并留痕。**模式二·多源管道单源硬超时隔离**：遍历 N 个外部源时，一个挂源会拖垮全量；修复用 `ThreadPoolExecutor(max_workers=1)` + `fut.result(timeout=)` 给单源套硬超时。**两个关键陷阱**：① `with ThreadPoolExecutor()` 的 `__exit__` 默认 `shutdown(wait=True)` 会 join 僵线程→硬超时失效，须手动 `shutdown(wait=False)`；② 工作线程非 daemon 会拖住进程正常退出，须在入口末尾 `os._exit(0)`（业务完成后）。**关键教训**：任何「遍历多个外部源」的管道必须给单源加硬超时隔离 + 容错跳过；端到端验证要真跑（确认挂源被跳过、进程退出码 0、bot 回复读回 thread 确认落地、游标推进后不重复回答）。源自一次多源追踪系统补双向问答 + 修「慢站连挂多日拖垮每日推送」的实战复盘。
- 同步更新 `engineering/README.md` 页面列表。

### 2026-06-18 —— GenAI cerberus 缺 UBER_LDAP_UID 坑（Claude Code, Opus 4.8 [UB]）

- **[修改] `agent-rules/hermes-genai-api-integration.md`** —— §5 新增**坑 6**：cron/后台重启 cerberus 报 `Error: UBER_LDAP_UID not set`（5436 持续 DOWN、watchdog 每分钟空转、且被误判「非认证」）。根因：cerberus 启动除 `SSH_AUTH_SOCK`（坑 1）还需 `UBER_LDAP_UID`（=ldap 名），登录 shell 有但 cron/setsid/nohup 不继承，watchdog **首次真正自动重启**时才暴露。修复：`genai_tunnel_watchdog.sh` 在重启 cerberus 前同时 export 两个变量；§8「掉线」步骤同步标注。**通用教训**：后台/cron 拉起的服务要一次核对**全部**依赖环境变量，别只修第一个报错的（先 SSH_AUTH_SOCK 后 UBER_LDAP_UID，挤牙膏踩了两次）。

### 2026-06-17 —— GenAI 隧道 watchdog 认证升级边界 + 端口漂移踩坑（Claude Code, Opus 4.8 [UB]）

- **[修改] `agent-rules/hermes-genai-api-integration.md`** —— §5 新增坑 5（cerberus idle 掉线 + 端口漂移 5436→5437 → `502 [Errno 99] Cannot assign requested address`，含 `/proc/net/tcp` 端口反查 + 杀干净重启修复）；文末新增 §8「GenAI 隧道 watchdog（系统 cron · 认证失败自动 Telegram 提醒）」，§7 运维表加一行。背景：6-17 LLM 又掉线复发，根因是 cerberus 周期性 idle 断链 + 端口漂移。删除了循环依赖的 Hermes 内部 `genai-proxy-watchdog`（`no_agent=false`，要调 LLM 才能查 LLM），改用系统 cron 纯脚本 watchdog（健康静默 / 自动重启 / 认证失败发 Telegram）。
- **[修改] `engineering/container-reboot-service-persistence.md`** —— 通用教训新增第 6 条「自愈有边界：区分可自动修 vs 需人介入（认证）」——纯脚本 watchdog 能修瞬时故障（进程死 / 端口漂移：服务起来但绑错端口，须按约定端口健康检查）但修不了凭证过期，应判定认证类故障并经「不依赖被监控服务的旁路通道（IM bot）」主动通知人重认证 + 告警限频。**关键教训**：watchdog 不只是「拉起进程」，要能识别自己修不了的故障类型并升级给人，否则无声反复重启失败比没有更难发现。
- 同步更新 `agent-rules/README.md`、`engineering/README.md` 两处页面描述。

### 2026-06-17 —— 咨询框架 skill 冲突消歧与去重指南（Cowork, Opus 4.8 [UB]）

- **[修改] `agent-rules/skill-register.md`** —— 新增第十节「咨询框架 Skill 冲突消歧与去重（跨 agent 通用行动指南）」，原「相关页面」顺延为第十一节。背景：这批咨询 skill（issue-tree-builder / hypothesis-tree / scpr-framework / storyline-builder / decision-memo-builder / top-down-memo / prioritization / management-consultant / consulting 等）全靠 description 语义自动触发、无优先级表，宽泛描述会抢专用 skill 的触发。新节给出：① 去重结论（`consulting` body ⊂ `management-consultant` 超集 4.6MB/228 文件，应归档；`prioritization` 常缺 frontmatter → 死 skill，应修不删）；② 14 行触发消歧表（哪件事用哪个、别让谁抢）；③ prioritization frontmatter 修复模板；④ 4 条通用原则。**关键教训（L-2026-06-17-001）**：判断 skill 能否删必须看 body+支撑文件体量，不能只比 description（consulting 实为 180KB 知识库，差点被当"两行重复品"删）；删除先归档不 `rm`；整改产出要写进共享 registry 让所有 agent 受益，不是只改本地 SKILL.md 只惠及当前 agent。源自 Cowork 本机 17 个咨询 skill 全景实测。

### 2026-06-16 —— 容器重启后服务恢复与开机持久化（Cursor, Opus 4.8）

- **[新增] `engineering/container-reboot-service-persistence.md`** —— 一次容器化开发环境内 AI agent 模型链路意外停机事故的复盘，已**匿名化/通用化**（剥离全部内部基础设施细节，仅保留通用架构模式与端口等本机通用细节）。核心教训：①容器 `/etc` 等系统目录通常是临时文件系统，跨重启的服务定义必须放持久化卷或平台持久 boot 机制，不能直接改 `/etc`（重启即丢）；②开机/恢复脚本要幂等 + 显式等依赖就绪以规避 boot 时序竞争；③后台常驻进程用 `setsid` 脱离会话避免被父进程组回收；④watchdog/自愈逻辑绝不能对它要修复的服务有循环依赖（反例：修模型链路的任务自己要先调模型）；⑤排障沿调用链逐跳验证（端口→进程→日志→服务定义→平台持久化层），用错误信息当 oracle 反推。同步登记进 `index.md` 第 2 层与 `engineering/README.md`。

### 2026-06-15 —— Cloud Run 部署同步陷阱（Claude Code, Opus 4.8）

- **[修改] `engineering/gcp-cloud-run-deployment.md`** —— 追加一节「部署同步陷阱：改了持久化层枚举/schema 却忘了重部署读取方」（来源 L-2026-06-15-001）。通用化教训：写入方往持久化层（Firestore/DB/MQ）加了新枚举值，但读取方仍跑不认得该值的旧镜像 → 旧读取方一遇新值即 `ValueError` 500 → 新数据进不了队列 → 下游静默停摆（最隐蔽，无报错只是「没数据」）。规则：枚举/schema 演进先升级所有读取方再写新值；非 git 项目靠 mtime + 部署 revision 时间戳对账是否上线；排查下游空转先查上游写入方。源自 magazine-podcast 扫描器停摆半月的真实事故。

### 2026-06-14 —— Codex VM 接入对账登记（Codex VM, GPT-5.4）

- **[修改] `agent-rules/skill-register.md`** —— 更新对账时间，注明 Codex VM 接入对账结果登记在 ub-branch 的 `uber-adaptation.md`。

### 2026-06-14 —— Agent 自述实测归集 + SOUL 指南 + 措辞统一 + workflow 载体修正（Claude Code CC-vm, Opus 4.8 [1m]）

- **[重写] `agent-rules/agent-config-matrix.md`** —— 用 8 份各 agent **第一人称实测**自述填全速查矩阵 + 逐 agent 七维详条：CC 家族（CC-home/Cowork/CC-vm 三类，机制同源差异在落地）、Antigravity（planning_mode+Artifacts，无 SOUL）、Hermes（家用+vm，有 SOUL.md）、Codex（SQLite 记忆）、Cursor（无持久层）。补 CC-vm 本机自述。**记一次教训**：一份替全部 9 个 agent 代填的旁观报告（uber-antigravity）经交叉核对系编造（虚构 CC 有 commands/、Hermes 是 soul.yaml、cowork 用 PostgreSQL、杜撰 Docker 镜像名），与各 agent 实测全面矛盾，整份弃用——只采信第一人称实测。
- **[新增] `agent-rules/soul-authoring-guide.md`** —— SOUL 写作指南 + SOUL.md 五节模板（身份/沟通规则/底线/启动开关/指针），据 Hermes 实测骨架。明确 SOUL **仅 Hermes 有**，其余 agent 无 SOUL 层、不要给它们造 SOUL 文件。登记进 `agent-rules/README.md`。
- **[修改] `agent-rules/five-step-pipeline.md`** —— 修正第二部分开头错误的五阶段载体描述（旧称「CC 用 ~/.claude/commands/、Antigravity 用 Customizations→Workflows」）：据多机实测改为各 agent 真实载体（CC=skill、Antigravity=planning_mode+Artifacts、Hermes=skill+SOUL、Codex=update_plan、Cursor=Plan Mode），明确无 agent 用 commands/ 目录。
- **[修改] 措辞统一** —— `agent-rules/README.md`（去 Gemini CLI、清「promote-lessons Workflow 自动维护」死引用、三 Agent→所有/各 agent，并注册 soul-guide）、`frontend/README.md`+`llm/README.md`+`image-gen/README.md`（清同款 promote-lessons 死引用）、`rtk-usage.md`/`auto-memory-setup.md`/`project-template.md`/`wiki-ingest-guide.md`（三 Agent→多 agent）、`crawler/bypass-waf-via-backend-api-discovery.md`（适用 Agent 去 Gemini CLI）。

### 2026-06-14 —— Agent 配置自述矩阵（Claude Code, Opus 4.8）

- **[新增] `agent-rules/agent-config-matrix.md`** —— 归集各 agent（Prompt A 通用自述）的配置机制，补 SSOT「新 agent 如何配置自己」缺口。首条填入 CC-home（家用机 Claude Code）完整七维自述；其余 8 个目标留【待该 agent 自述】占位（Antigravity/Hermes 附 CC 旁观推断，待各自确认转正）。登记进 `index.md` 第 2 层与 `agent-rules/README.md`。

### 2026-06-14 —— Auto Memory 配置指南（Claude Code, Opus 4.8）

- **[新增] `agent-rules/auto-memory-setup.md`** —— 补齐 [[auto-memory-boundary]] 缺的「怎么配」：三层启用开关（env / settings.json `autoMemoryEnabled` / `/memory`）、一事一文件 + MEMORY.md 索引、frontmatter 字段与 `metadata.type` 四取值、写入/召回/更新/删除触发、与共享 Wiki 的互斥分工。事实区分官方文档确证与【未找到官方来源】两档。同步登记进 `index.md` 第 2 层与 `agent-rules/README.md`（顺带补登原本漏登的 boundary 条目）。

### 2026-06-13 —— repo 治理伴随的 wiki 调整（Claude Code, Opus 4.8）

- **[新增] 领域 `finance/`** —— 金融领域，含 `README.md`（领域范围说明）+ 子领域 `precious-metals/`。同步登记进 `index.md` 与 `wiki-ingest-guide.md` 领域映射表（领域数 7 → 8）。
- **[迁移] `com/dsifo-threshold-logic.md` → `finance/precious-metals/sifo-threshold-logic.md`** —— 原 `com/` 目录命名无意义且领域归类错误。文件重命名为更清晰的 `sifo-threshold-logic`，frontmatter 升级为方案 Z 双字段（domain: finance）。`com/` 已删除。
- **[迁移+重写] `auto-memory-boundary.md` 入 `agent-rules/`** —— 原散落在顶层 `workflows/claude-code-rules/`，升级为正式规则页：补方案 Z frontmatter、去写死 Mac 路径、措辞从"三 Agent"扩为"所有 agent"。
- **[合并] `skill-registry.md` + `skill-catalog.md` → `skill-register.md`** —— 两文件内容重叠易失同步，合并为单一清单（对账 + 全量明细 + Self-Skill 区）。13 处反链已更新。
- **[重写] `index.md`** —— 从过期版（2026-05-21）重写为 8 领域三层索引，摘录各领域高频页，承诺"完整清单见各领域 README"，全部引用经校验零断链。
- **[修改] `wiki-ingest-guide.md`** —— 领域映射表新增 finance 行；去写死路径（详见根 CHANGELOG 的 G 步）。
- **[补登记] `index.md` engineering 摘录** —— 补 `url-fidelity`。

> 已知待下轮：`agent-rules/` 下 4 个 Hermes/finance 特用页 + `engineering/youtube-pipeline-genimages-template-issue` 归类待判；部分旧页 frontmatter 待升级方案 Z。见根 `CHANGELOG.md` 白名单「待下轮处理」。
