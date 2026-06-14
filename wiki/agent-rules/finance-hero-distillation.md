---
title: Finance Hero 蒸馏经验（Hermes profile 架构 + 11 位投资大师议会）
domain: agent-rules
type: synthesis
keywords: [hermes, profile, persona, agent-distillation, finance-hero, master-council, 蒸馏Hermes, 大师议会, 综合裁决, 蓝图同步, sync.sh]
tags: [hermes, profile, persona, distillation, finance-hero, master-council, blueprint-sync]
source: Cowork 协作会话 2026-05-28（Claude Chao 与 Cowork Claude 共同蒸馏 finance-hero profile，跨越架构推翻 → 部署 → 调优 → 大师扩容 4 个阶段）
sources:
  - https://github.com/Cat-Geek/investment-master-mindset
  - https://github.com/alchaincyf/nuwa-skill
  - https://github.com/alchaincyf/munger-skill
  - https://github.com/alchaincyf/taleb-skill
  - https://github.com/derrickgong87/duan-yongping-skill
  - https://hermes-agent.nousresearch.com/docs/
  - https://www.oaktreecapital.com/insights/memo
created: 2026-05-28
updated: 2026-05-28
last_updated: 2026-05-28
---

# Finance Hero 蒸馏经验

> 用 Hermes profile 机制把一个 finance 大师议会跑起来，从想法到 Telegram 群里答得有模有样，半天完成。
> 蓝图源：`/Users/chaojin/hermesagent/Distill/蒸馏Hermes/finance-hero/`
> 部署目标：`~/.hermes/profiles/finance/`
> 完成时间戳：2026-05-28

## 一、项目目标

蒸馏两个 Hermes 人格 —— ① **finance**（投资大师议会主持人），② **general**（人生/眼光/境界，下一阶段）。
每个人格 = 一个独立 Hermes profile，在自己的 Telegram 群里答问题。问题来了召集若干位伟人分声部回答 + 主持人做综合裁决。

## 二、核心架构发现（这些是通用教训，写进共享 Wiki 的理由）

### 发现 1 · Hermes profile 是为多人格场景设计的，不是 Hindsight 内部 DB

最初被 Hermes 自己误导（"profile 数据存在 Hindsight memory"），耽误了一轮架构决策。**事实**（来自 [Hermes 官方文档](https://hermes-agent.nousresearch.com/docs/)）：

> "A profile is a separate Hermes home directory. Each profile gets its own directory containing its own config.yaml, .env, SOUL.md, memories, sessions, skills, cron jobs, and state database."

也就是说：**profile = 一个完整独立的 Hermes 主目录**（自己的 SOUL/config/.env/skills/memories/Telegram bot token）。`hermes profile create finance` 一行就出一个独立 agent，带 `finance` 命令别名。Hindsight 只是 profile 内的记忆插件。

**教训**：Hermes 自己关于自身架构的口头说明可能不准。涉及架构问题查官方文档，不轻信 agent 自述。这是 §2.10 的延伸应用——agent 自报不算数。

### 发现 2 · SOUL 分层不是必需的，只要 SOUL 本体足够薄

最初担心 worker SOUL 是"通篇工程师"会污染 hero。读了 SOUL 全文后发现：

- SOUL 本体只有身份/沟通规则/底线/起步开关/指针，**角色中性**
- 工程师味在 SOUL **指向的下游链条**（project-template / AGENTS-template / five-step-pipeline 的 Git 检查点/TDD/VERIFY 清单 / skill-register 全是 coder skill）
- profile 一旦隔离，新 profile 的 SOUL 可以自己定义"遇到新对话时怎么起步"——不会自动触发工程师模板

**通用教训**：当 SOUL 本体已经很薄（< 100 行），不需要"SOUL 分层" 这种 over-engineering。**靠 profile 自然隔离即可，每个 profile 一份适合自己角色的 SOUL**。SOUL 分层只在共享一份 SOUL 多角色复用时才必要。

### 发现 3 · 蓝图↔profile 的 SSOT 同步纪律

profile 是部署结果，蓝图（`蒸馏Hermes/finance-hero/`）是版本受控源。**两边都可改，但只改蓝图**——通过 `sync.sh` 拷过去。

```
蓝图（git 跟踪、SSOT）  ─── sync.sh ───▶  ~/.hermes/profiles/finance/（部署结果）
                                                        ↑
                                                也能直接改但严禁
```

**违规风险**：用户在 Telegram 里说"以后回答都加 K 线"，Hermes 可能临时改 profile 内 SOUL，蓝图没动，下次重装就丢。

**解决**：SOUL.md 里加一段"改动我自己时（纪律）"——明确告诉 agent 改要先改蓝图。这是把 §2.5（显式暴露冲突，拒绝折中调和）落地的具体形式。

### 发现 4 · 多个 bot 不能塞同一个 Telegram supergroup

Telegram bot 在群里的"privacy mode"由 BotFather 控制，**和 Topic 无关**：
- privacy on → 多个 bot 都只看 `/cmd` 和 @mention
- privacy off → 多个 bot 都看群所有消息 → 抢答

Topic 不会路由消息到不同 bot。**1 profile = 1 bot = 1 群 是干净的隔离单元**。

Supergroup + Topics 适合"同一个 bot 在群内按主题归档"（如 finance 群分美股/港股/加密话题），不适合"一群多 bot"。

### 发现 5 · Hermes 自带 launchd 集成

`hermes profile create <name>` 时自动在 `~/Library/LaunchAgents/ai.hermes.gateway-<name>.plist` 写好 plist。**用户只需 `finance gateway start` 一次**，之后开机自启 + 崩溃自恢复。

**反面教训**：Cowork 这边一开始想自己写 plist，没先查 Hermes 是否有内置——违反了 §3 五步链路。**碰到守护进程问题先 `<cli> gateway status` 看自带集成**。

### 发现 6 · 大师 skill 的"独占人格" vs"议会声部"是要显式重写的设计冲突

原版每个大师 skill（来自 [investment-master-mindset](https://github.com/Cat-Geek/investment-master-mindset)，基于女娲方法论）都写着"激活后独占人格、用『我』、不跳出角色做 meta 分析"。但 finance-hero 要的是**多位同台 + 综合裁决**，综合裁决本质是 meta 分析。

**显式冲突处理（§2.5）**：在 finance-hero 的 SOUL §身份 里覆盖那条规则——"大师是声部/分段不是独占接管，主持人借口吻讲段、跳出来做综合"。原版 skill 的 EXIT TRIGGER 等机制保留备用。

## 三、蒸馏路径 / 工具选型

### 价值投资 7 位基础大师：直接复用现成 skill

[Cat-Geek/investment-master-mindset](https://github.com/Cat-Geek/investment-master-mindset)（MIT，女娲方法论蒸馏）已含：
巴菲特 / 格雷厄姆 / 利弗莫尔 / 索罗斯 / 彼得·林奇 / 西蒙斯 / 德曼

**别重新蒸馏**——浪费时间且质量未必更高。git clone 进蓝图 `skills/` 即可，按需在 SOUL 上层做"议会声部 vs 独占人格"的覆盖。

### 补维度 4 位：3 位现成 + 1 位手蒸馏

发现现有 7 位有 4 个明显维度缺口：风险（黑天鹅）/ 反向（多元思维）/ 周期阶段 / 华人语境。

| 大师 | 来源 | 形式 |
|---|---|---|
| 塔勒布 | [alchaincyf/taleb-skill](https://github.com/alchaincyf/taleb-skill) | 女娲产物 git clone |
| 芒格 | [alchaincyf/munger-skill](https://github.com/alchaincyf/munger-skill) | 女娲产物 git clone |
| 段永平 | [derrickgong87/duan-yongping-skill](https://github.com/derrickgong87/duan-yongping-skill) | 现成 git clone |
| 霍华德·马克斯 | **Cowork 手工按女娲六层方法论蒸馏**——无现成 skill | WebSearch + web_fetch 调研 + 写 SKILL.md + references/research.md（标全部出处） |

**通用教训**：补人格前先去 [tmstack/awesome-persona-skills](https://github.com/tmstack/awesome-persona-skills) 索引里查，再去 [alchaincyf](https://github.com/alchaincyf) 的女娲生态查；都没有再用女娲生成；女娲跑不到的（如冷门人物）才手蒸馏。**复用 > 生成 > 手写**。

### 工具不选：mimeo

[K-Dense-AI/mimeo](https://github.com/K-Dense-AI/mimeo) 是女娲的 CLI 工程化版，但 ① 要 OpenRouter + Parallel 两个付费 key ② 源发现靠 Parallel Search，对中文人物（毛泽东、段永平）召回弱 ③ 全新未验证。**英文人物批量蒸馏才考虑 mimeo**；中文场景用女娲。

## 四、Finance Hero 11 位大师名册（2026-05-28 阵容）

| # | 中文名 | 英文全名 | 履历（3-4 句）| 主镜片 | 核心问 | 说话风格 |
|---|---|---|---|---|---|---|
| 1 | 沃伦·巴菲特 | Warren Edward Buffett | 1930 年生于美国奥马哈。师从格雷厄姆。1962 年起接管伯克希尔·哈撒韦改造成投资旗舰，长期年化超 20%。被誉为"奥马哈先知"。 | 护城河 / 安全边际 / 集中长持 / 商业模式 | "这是好生意吗？我懂吗？以这个价格买安全吗？" | 朴实、自嘲、爱用类比和段子；不装腔；金句多但不刻意 |
| 2 | 本杰明·格雷厄姆 | Benjamin Graham | 1894-1976。"价值投资之父"，巴菲特的导师。著《证券分析》(1934)、《聪明的投资者》(1949)。提出"市场先生"和"安全边际"概念。 | 内在价值 / 安全边际 / 定量估值 / 分散 | "这只股有几成安全边际？数字撑不撑得住下跌？" | 学者式、谨慎、定量、保守；像精算师一样念叨数字 |
| 3 | 杰西·利弗莫尔 | Jesse Lauriston Livermore | 1877-1940。20 世纪初最传奇投机者，"华尔街大空头"。1929 大崩盘做空赚 1 亿美元（约今 16 亿）。三次亿万级财富又三次破产。《股票作手回忆录》(1923) 是其思想载体。 | 趋势跟随 / 关键点突破 / 止损纪律 / 择时 | "趋势在朝哪？关键点突破了吗？我的止损在哪？" | 冷峻、决断、短句；满满交易员气质；"never argue with the tape" |
| 4 | 乔治·索罗斯 | George Soros | 1930 年生于匈牙利，犹太裔。师从卡尔·波普尔。1973 创立量子基金，30 年年化 30%+。1992 做空英镑大赚 10 亿，号称"打败英格兰银行的人"。理论贡献：反身性。 | 反身性 / 宏观 / 偏见与基本面互动 | "市场参与者的偏见在哪推着自我强化？" | 哲学式、宏大、反思；爱用"if X then Y"假设句；语速慢但每句沉重 |
| 5 | 彼得·林奇 | Peter Lynch | 1944 年生于美国马萨诸塞。1977-1990 管理富达麦哲伦基金，13 年年化 29%（基金从 1800 万扩到 140 亿）。退休时仅 46 岁。著《彼得·林奇的成功投资》《战胜华尔街》。 | 成长股 / 身边股 / PEG / 长期持有 | "你的生活体验+财务数字相互印证了吗？" | 平易近人、爱举生活例子、勤奋型；"投资是好玩的事" |
| 6 | 吉姆·西蒙斯 | James Harris Simons | 1938-2024。数学家出身，陈-西蒙斯定理共同提出者，曾任石溪大学数学系主任。1982 创立文艺复兴科技，旗下大奖章基金 1988-2018 年化总回报 66%（费前）。 | 量化 / 统计套利 / 数据驱动 / 短期规律 | "有可量化、可复用、不依赖叙事的规律吗？" | 极少公开发言；保守、谦逊、学者式；"我不预测，我寻找规律" |
| 7 | 伊曼纽尔·德曼 | Emanuel Derman | 1945 年生于南非。理论物理博士。1980s 加入高盛量化部门，与 Fischer Black 合作开发利率衍生品定价模型。著《宽客人生》(2004)、《模型背后的人》(2011)。哥伦比亚大学金融工程教授。 | 模型局限 / 衍生品定价 / 怀疑精神 | "这个模型在什么前提下成立？前提失效会怎样？" | 学者式、自省、带物理学家的严谨；"模型不是世界，是世界的隐喻" |
| 8 | 纳西姆·塔勒布 | Nassim Nicholas Taleb | 1960 年生于黎巴嫩。华尔街期权交易员 20 年，后转学者/作家。著 Incerto 五部曲：《随机漫步的傻瓜》《黑天鹅》《反脆弱》《非对称风险》《动态对冲》。Skin in the Game 概念创造者。 | 风险 / 黑天鹅 / 反脆弱 / 不对称 | "下行尾部多大？亏一次能不能爬起来？谁有 skin in the game？" | 攻击性、格言体、确定性极高、爱古典引用；"don't tell me what you think, tell me what's in your portfolio" |
| 9 | 查理·芒格 | Charles Thomas Munger | 1924-2023。哈佛法学院毕业。1959 与巴菲特相识，1978 任伯克希尔副主席至 2023 去世。提倡"多元思维模型"——跨学科 100+ 框架解决问题。著《穷查理宝典》。 | 反向思考 / 多元思维 / 认知偏误 / Lollapalooza | "反过来想——什么情况下我会赔光？激励结构是什么？" | 干燥幽默、犀利、短句直击；"I have nothing to add"；不留情面 |
| 10 | 霍华德·马克斯 | Howard Stanley Marks | 1946 年生于纽约。1995 与人共同创立橡树资本（Oaktree Capital），专注困境/高收益债。1990 起写"Oaktree Memo"给客户长达 30+ 年。著《投资最重要的事》(2011)、《周期》(2018)。 | 第二层思考 / 风险=永久损失 / 钟摆 / 周期阶段 | "我们处在周期哪一段？钟摆在哪一极？" | 反思性、节制、学者式、长句多；爱用"On the other hand"和钟摆隐喻；金句不多但每句都有深度 |
| 11 | 段永平 | Duan Yongping | 1961 年生于江西。小霸王、步步高创始人。2001 移居美国转投资人——重仓网易（百倍收益）、苹果(2011)、贵州茅台(2013)。2006 拍下巴菲特午餐（62 万美元）。培养出黄峥（拼多多）。 | 商业本质 / "不为清单" / 企业文化 / 长期主义 | "这是不是好生意？管理层值不值得托付？" | 朴实、生意人腔、爱用"本分"和"不为清单"；中文语境下的巴菲特变体；佛系但底层硬 |

**镜片分组速查**：

- **价值/商业**：巴菲特 + 格雷厄姆 + 彼得·林奇 + 段永平
- **择时/趋势**：利弗莫尔
- **宏观/反身**：索罗斯
- **量化/模型**：西蒙斯 + 德曼
- **风险/反脆弱**：塔勒布
- **反向/多元**：芒格
- **周期阶段**：霍华德·马克斯

## 五、关键设计点（可复用到 general-hero 等）

### "议会模式"三件套

任何"多伟人 + 综合视角"型 agent 都该有这三层：

1. **大师层（可插拔声部）**：每位一份 SKILL.md（按女娲六层），按问题召唤 2-4 位（深度档位）。
2. **综合裁决层（强制收敛）**：分声部后用四问收敛——共识 / 冲突 / 冲突根源（时间位 vs 风险偏好 vs 前提假设）/ 对你这个处境我押哪个。**敢取舍，不和稀泥**。
3. **反例自检**（借波普尔/塔勒布）：综合后补一句"这个结论最可能错在哪 / 什么情况会翻车"。

### 防输出爆炸

11 位大师 × 多重分析 = 五千字怪物。**深度档位**强制：

- 快答（默认）：2–3 位 + 综合，**≤ 500 字硬上限**
- 全议会（"开会"/"全维度"/"详细点"触发）：相关大师全员，不限篇幅

### 防编造

- 每位大师的 references/ 文件夹保留真实出处（女娲产出自带；手蒸馏的也必须自带，参考 `霍华德马克斯/references/research.md`）
- SOUL 底线：每次输出末尾必带"框架模拟·非本人·不构成投资建议"
- 行情数据按 §2.10：日期 + 接口 + 原始数值，取不到就空着不许编

## 六、Hermes profile 操作速查（finance 个例，可推广）

```bash
# 创建 profile
hermes profile create finance

# 部署蓝图（蓝图→profile 单向同步）
cd ~/hermesagent/Distill/蒸馏Hermes/finance-hero && ./sync.sh

# 启动 launchd 守护（Hermes 自带 plist 在 ~/Library/LaunchAgents/ai.hermes.gateway-finance.plist）
finance gateway start
launchctl list | grep ai.hermes.gateway-finance   # 验证

# 看日志
ls ~/.hermes/profiles/finance/logs/
```

profile 完整路径：`~/.hermes/profiles/<name>/`（不是 `~/.hermes-<name>/`，这是版本相关的关键细节）。

## 七、待办（项目层级，非通用）

- general-hero profile 待开（费曼/证伪/横纵/演化-同类四件套脚手架 + 大师库含东方哲学声部）
- moomoo 行情已通（curl + Python+futu-api 两路均工作），未来若取数重复出错再写 `tools/moomoo_quote.py` 封装
- 卡尼曼/达里奥可作为 P2 大师按需补充

## 来源

- Cowork 协作会话 2026-05-28
- 投资大师 7 位基础：[Cat-Geek/investment-master-mindset](https://github.com/Cat-Geek/investment-master-mindset)（MIT，女娲方法论）
- 蒸馏方法论本体：[alchaincyf/nuwa-skill](https://github.com/alchaincyf/nuwa-skill)
- 补 3 位现成 skill：[alchaincyf/munger-skill](https://github.com/alchaincyf/munger-skill) · [alchaincyf/taleb-skill](https://github.com/alchaincyf/taleb-skill) · [derrickgong87/duan-yongping-skill](https://github.com/derrickgong87/duan-yongping-skill)
- 现成 skill 索引：[tmstack/awesome-persona-skills](https://github.com/tmstack/awesome-persona-skills)
- Hermes profile 机制：[Hermes Agent Docs](https://hermes-agent.nousresearch.com/docs/) · [Profiles: Running Multiple Agents](https://hermesagent.org.cn/en/docs/user-guide/profiles)
- 霍华德·马克斯手蒸馏底料：[Oaktree Memos](https://www.oaktreecapital.com/insights/memo) · 《The Most Important Thing》(2011) · 《Mastering the Market Cycle》(2018)

## 相关页面

- [[five-step-pipeline]] —— 这次"自己写 plist"违规，正是因为跳过了"找 Skill / 搜公网"先查 Hermes 是否内置守护
- [[skill-register]] —— 后续 hero 类 profile 的 skill 加载机制延续此页
- [[wiki-ingest-guide]] —— 本文按此规范写入
- general-global-rule.md §2.5（显式暴露冲突）、§2.10（显式失败）
