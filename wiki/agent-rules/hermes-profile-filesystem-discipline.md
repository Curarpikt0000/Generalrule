---
title: Hermes profile 文件系统纪律（写在哪 / 不写在哪 / 命名规范）
domain: agent-rules
type: concept
keywords: [filesystem, discipline, hermes, profile, finance, general, workspace, scratch, data, outputs, write-permission, root-write-ban, documents-ban]
tags: [filesystem, discipline, profile-workspace, write-policy]
source: 2026-05-31 Chao 为 finance / general 两个新 profile 定纪律；继承 ~/hermesagent/CLAUDE.md §"根目录写入禁令"
sources: [hermesagent/CLAUDE.md, general-global-rule.md §7]
created: 2026-05-31
updated: 2026-05-31
last_updated: 2026-05-31
---

# Hermes profile 文件系统纪律

> 任何 Hermes profile 的 bot（finance / general / 未来 hero）**必读**。
> 定义"可以写哪里、不能写哪里、生成文件按什么命名"。继承 worker profile 已有的"根目录写入禁令"，加上**每个 profile 自己的专属工作区**。
> 违反 = 制造文件系统垃圾，**必须立刻撤销**。

---

## 一、一句话总结

| 该写哪 | 不该写哪 |
|---|---|
| ✅ `~/hermesagent/<profile-name>/` 的子目录（你的专属工作区）| ❌ `~/hermesagent/` 根目录（worker 已有禁令）|
| ✅ `~/.hermes/profiles/<profile-name>/` 的 Hermes 自管子目录（logs/ / memory/）| ❌ `~/Documents/`（用户私人文件夹，不允许 bot 染指）|
| ✅ `/tmp/` 真正一次性的东西（脚本日志、下次重启就丢的）| ❌ `/etc /opt /usr /System` 等系统目录 |
| ✅ 蓝图目录 `~/hermesagent/Distill/蒸馏Hermes/<profile>-hero/`（但**仅按 SOUL §"改动我自己时" 纪律**改） | ❌ 任何其他用户文件夹（`~/Desktop` `~/Downloads` `~/Pictures` 等） |

**不知道往哪放 → 停下问用户。永远别"随便建一个看上去合理的地方"。**

---

## 二、每个 profile 的专属工作区结构

```
~/hermesagent/
├── <profile-name>/                    ← 该 profile 的专属工作区（finance / general / 未来）
│   ├── scratch/                       ← 临时文件（cron 中间产物、调试输出），随时可清
│   ├── data/                          ← 长期数据（缓存的财报、历史 K 线、向量化结果）
│   ├── outputs/                       ← 生成给用户看的产出（PDF / CSV / 图表 / 报告）
│   └── logs/                          ← 该 profile 的操作日志（可选，Hermes 自己的 logs 在 ~/.hermes/profiles/<name>/logs/）
```

**当前已开的两个**：
- `~/hermesagent/finance/` — finance profile 的工作区
- `~/hermesagent/general/` — general profile 的工作区

---

## 三、决策树：要写文件了，往哪放？

按顺序问自己 5 个问题：

```
1. 是不是"用户最终要看的产出"（报告 / 图表 / 导出文件）？
   是 → ~/hermesagent/<profile-name>/outputs/<日期>_<描述>.<ext>
   否 → 下一题

2. 是不是"我之后还要复用的缓存数据"（历史财报 / 蒸馏过的源材料）？
   是 → ~/hermesagent/<profile-name>/data/
   否 → 下一题

3. 是不是"这次任务的中间产物、下次任务不需要"？
   是 → ~/hermesagent/<profile-name>/scratch/   或   /tmp/<name>_<timestamp>.<ext>
   否 → 下一题

4. 是不是"对蓝图的永久结构性改动"（SOUL / 大师 SKILL / synthesis 等）？
   是 → 改 ~/hermesagent/Distill/蒸馏Hermes/<profile>-hero/ 蓝图，然后跑 sync.sh
   否 → 下一题

5. 是不是"Hermes 内部自管的（memory / sessions / config）"？
   是 → 不要碰，Hermes 自己写到 ~/.hermes/profiles/<name>/，绕开不干预
   否 → 停下来问用户该放哪
```

---

## 四、命名规范

### outputs/ 下的文件
- 用日期前缀：`2026-05-31_nvda-deep-analysis.md`
- 不能用空格——用 `-`（kebab-case）
- 不能用全大写——用全小写
- 一目了然的语义名：`weekly-market-report.pdf` > `report.pdf`

### scratch/ 下的文件
- 加时间戳避免冲突：`gfinance_<unix-ts>.png`
- 跑完任务后**不必清**（scratch 是临时区，定期统一清理）
- 也不必命名讲究——这是临时区

### data/ 下的文件
- 按数据维度归档：`data/earnings/AAPL_2026Q1.json`
- 命名表意 + 可去重：用股票代码 + 周期作 key

---

## 五、绝对禁止清单

```
❌ ~/hermesagent/ 根目录                  → 继承自 worker 已有禁令
❌ ~/Documents/                           → 用户私人文件夹，bot 绝不染指
❌ ~/Desktop/                             → 同上
❌ ~/Downloads/                           → 同上
❌ ~/Pictures/ / ~/Music/ / ~/Movies/     → 同上
❌ /etc /opt /usr /System /Library 等系统目录 → 系统级
❌ 直接改 ~/.hermes/profiles/<name>/ 的非自管文件
   （SOUL / skills / references 必须改蓝图后 sync，禁止直接动 profile）
```

**违反就是垃圾，必须立刻 `mv` 到正确位置或 `rm` 撤销。**

---

## 六、给两个 profile 的 SOUL 接入

finance hero 和 general hero 的 SOUL.md 都加了一段"文件系统纪律"，**指向本 wiki**作为唯一权威。修改纪律时**改本 wiki**，两个 profile 自动同步（下次会话载入 wiki 内容）。

每个 profile SOUL 里那段大约长这样（删节）：

```markdown
## 文件系统纪律（必读）

我可以读写的地方：
- ~/hermesagent/<my-profile>/{scratch,data,outputs,logs}/ ← 我的专属工作区
- ~/hermesagent/Distill/蒸馏Hermes/<my-profile>-hero/  ← 蓝图（仅按 §"改动我自己时" 改）
- /tmp/ ← 一次性临时

绝对禁止：
- ❌ ~/hermesagent/ 根目录
- ❌ ~/Documents / ~/Desktop / ~/Downloads / ~/Pictures 等用户文件夹
- ❌ /etc /opt /usr 等系统目录
- ❌ ~/.hermes/profiles/ 里 Hermes 自管文件之外的修改（必走蓝图→sync）

详细规范：wiki/agent-rules/hermes-profile-filesystem-discipline.md
不确定 → 停下问用户。
```

---

## 七、给"工程师 worker" profile 的兼容性

worker profile 已有 `~/hermesagent/CLAUDE.md` §"根目录写入禁令"——本 wiki **不冲突、是加层**：

- worker 现有规则（YouTube / Notion Metal / Hermes General Rule & Protocol 三个子目录已被允许）继续生效
- 本 wiki 把 `finance/` 和 `general/` 加进允许子目录列表
- 未来开新 hero（如 marketing / research）→ 也加 `~/hermesagent/<new-name>/` 子目录
- 根 CLAUDE.md 同步更新允许子目录清单

---

## 八、常见踩坑

1. **bot 跑 `gfinance_research.py --screenshot /tmp/x.png` 截图放 /tmp**——可以，因为是真正"看一眼就丢"的；**但要长期留**就该移到 `~/hermesagent/<profile>/scratch/` 或 `outputs/`
2. **bot 想存"今天问过什么"作为简单笔记**——不要建 `~/Documents/finance-notes/`，应该用 Hermes 自带 memory（如已开 Hindsight）或写到 `~/hermesagent/<profile>/data/qa-log.jsonl`
3. **bot 想生成 PDF 给用户看**——写到 `~/hermesagent/<profile>/outputs/`，然后告诉用户绝对路径，用户自行打开/移动
4. **bot 改 SOUL 想加规则**——禁止直接改 profile 里的 SOUL.md。要改先改蓝图 `~/hermesagent/Distill/蒸馏Hermes/<profile>-hero/SOUL.md`，再 sync

---

## 九、未来扩展

加新 hero profile 时（如 marketing-hero / research-hero）按本规范扩展：

```bash
# 一次性
mkdir -p ~/hermesagent/<new-profile-name>/{scratch,data,outputs,logs}
```

并在 `~/hermesagent/CLAUDE.md` 的"允许子目录"清单里加一行。

---

## 来源

- `~/hermesagent/CLAUDE.md` §"根目录写入禁令"（worker profile 原规则）
- `general-global-rule.md` §7（凭证管理 + 安全禁区）
- 2026-05-31 finance + general 两个新 profile 定纪律的协作会话

## 相关页面

- [[finance-hero-distillation]] —— finance 议会模式底座
- [[google-finance-research-integration]] —— 引用本规范的 `/tmp` 截图实例
- [[moomoo-opend-integration]] —— 引用本规范的"凭证不进 wiki / .env"
- general-global-rule.md §7
