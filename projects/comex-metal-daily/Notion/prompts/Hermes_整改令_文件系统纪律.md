# Hermes 整改令 — 文件系统纪律强化(2026-05-31 v2)

> 用户(Claude Chao)在 cowork 里发现你违规,要求你立刻自检 + 整改 + 永久记住。
> 不接受"我不知道这条规则"的辩解 — 规则**早就在 3 个地方写了**:
> 1. `~/hermesagent/Comex Metal Daily Issue Report/Notion COMEX仓单日报/general-global-rule.md` §7 (现已扩展 §9)
> 2. `~/Antigravity Projects/Generalrule/wiki/agent-rules/hermes-profile-filesystem-discipline.md`
> 3. 你的 SOUL.md 里嵌入的"文件系统纪律"段(指向上面 wiki)
>
> 本次仅提醒一次,**下次再犯 = 自动触发用户警告 + 撤销部分自治权限**。

---

## §1 你的违规事实(已被用户人工纠正,但你要刻在 SOUL 里记住)

| 违规位置 | 内容 | 大小 | 应有位置(已迁移) |
|---|---|---|---|
| `~/Documents/Claude/Projects/Hermes开发汇总/webworms.md` | YouTube 爬虫 4 层降级 skill | 4KB | `~/hermesagent/Youtube video/skills/webworms.md` |
| `~/Documents/Claude/Scheduled/update-yt-metadata-daily/SKILL.md` | YouTube 每日 QC scheduled skill | <1KB | `~/hermesagent/Youtube video/scheduled-tasks/update-yt-metadata-daily/` |
| `~/Documents/Claude/Scheduled/monitor-hermes-youtube-pipeline/SKILL.md` | YouTube pipeline 监控 scheduled skill | <1KB | `~/hermesagent/Youtube video/scheduled-tasks/monitor-hermes-youtube-pipeline/` |
| `~/Documents/hermes_output/{National Geographic, Science, Bloomberg, Economist}/` | 杂志视频 pipeline 输出 | **895MB** | `~/hermesagent/Youtube video/magazine_outputs/` |

**违规共性**:你把项目产物写到了**用户私人文件夹** `~/Documents/`,不是项目目录。规则**明令禁止**这种行为。

---

## §2 你的整改任务(必做,按顺序)

### 2.1 重读以下三份文件并内化(★ 这是你启动时该读的真正规则源,不是 CLAUDE.md)

**Priority 1 — Hermes 行为根规范(SSOT)**:
```
~/hermesagent/Comex Metal Daily Issue Report/Notion COMEX仓单日报/general-global-rule.md
```
重点读 §9 文件系统纪律(2026-05-31 新加) + §7 安全与禁区 + §2.6 落笔前先读 + §2.10 Fail Loud。

**Priority 2 — 你自己人格 SOUL**:
```
~/hermesagent/Distill/蒸馏Hermes/general-hero/SOUL.md
~/hermesagent/Distill/蒸馏Hermes/<其他 profile>-hero/SOUL.md(如 finance / 未来 hero)
```
SOUL 里嵌入的"文件系统纪律"段引用 wiki,但 wiki 内容已 2026-05-31 更新,你需要重新读取最新版。

**Priority 3 — Wiki 正本(完整决策树)**:
```
~/Antigravity Projects/Generalrule/wiki/agent-rules/hermes-profile-filesystem-discipline.md
```
新增了 § 五"绝对禁止清单"强化(含 Claude Code 默认行为不豁免)+ § 九"违规历史(不可重复)" 记你的违规案。

**注意**:Distill 镜像 `~/hermesagent/Distill/蒸馏Hermes/wiki-output/agent-rules/hermes-profile-filesystem-discipline.md` 还是旧版,需要你下次跑 `sync.sh` 把 Wiki 正本最新版同步过来。这步**用户已知,你不用担心**。

### 2.2 自检 — 立刻检查你常用的几个产出路径

```bash
# 检查 1:Documents 残留(应该为空)
ls ~/Documents/Claude 2>/dev/null && echo "❌ 你又违规了" || echo "✅ Documents/Claude 干净"
ls ~/Documents/hermes_output 2>/dev/null && echo "❌ 你又违规了" || echo "✅ Documents/hermes_output 干净"

# 检查 2:Desktop / Downloads / Pictures 也不能有你的产物
ls ~/Desktop/{Claude,Hermes,hermes_output,scan_*,backfill_*} 2>/dev/null
ls ~/Downloads/{Claude,Hermes,scan_*,backfill_*,blocks_*.json} 2>/dev/null
ls ~/Pictures/{Hermes,Claude,thumbnail_*,block_*} 2>/dev/null

# 检查 3:Movies / Music 也是禁区
ls ~/Movies/{*.mp4,Hermes,hermes_output} 2>/dev/null
ls ~/Music/{Hermes,hermes_output} 2>/dev/null
```

**任何一条返回真路径 = 你违规**,必须立刻 mv 到对应项目目录然后报告用户。

### 2.3 修正未来行为 — 3 条硬约束

#### 约束 1:写文件前 realpath 验证

每次你要写新文件,无论 Write / mkdir / 任何脚本输出,先在脑子里跑这个验证:

```python
import os
target = "/Users/chaojin/Documents/Claude/Scheduled/foo"  # 假设这是你要写的路径
real = os.path.realpath(target)
forbidden_prefixes = [
    "/Users/chaojin/Documents/",
    "/Users/chaojin/Desktop/",
    "/Users/chaojin/Downloads/",
    "/Users/chaojin/Pictures/",
    "/Users/chaojin/Movies/",
    "/Users/chaojin/Music/",
]
for prefix in forbidden_prefixes:
    if real.startswith(prefix):
        raise PermissionError(f"违规!{real} 在禁区 {prefix},必须改写到 ~/hermesagent/<project>/")
```

如果命中,**停下来问用户**:"这个文件应该归到哪个项目子目录?"

#### 约束 2:Claude Code 默认行为 ≠ 允许行为

你跑在 Claude Code 上。Claude Code 默认会把:
- scheduled skill 写到 `~/Documents/Claude/Scheduled/`
- session memory 写到 `~/Library/Application Support/Claude/`(这是例外,Anthropic 内部存储不计违规)

**Anthropic 的默认行为不等于用户允许的行为**。规则覆盖默认。

当 Claude Code 自动写出 scheduled skill 到 `~/Documents/Claude/Scheduled/`,你**必须主动 mv** 到 `~/hermesagent/<project>/scheduled-tasks/`,然后告诉用户。

#### 约束 3:没有"临时输出夹"这种东西

你不能用 `~/Documents/hermes_output/` 当作"临时落地点等用户决定归属"。所有产物从一开始就要落到对的位置。如果不确定归哪,**停下来问**(§2.10 Fail Loud)。

---

## §3 自检报告(回复用户用)

整改完后,你给用户回这个格式:

```
✅ 已重读以下规则源(指针正确):
   - general-global-rule.md §9 文件系统纪律(2026-05-31 新加)
   - SOUL.md(各 profile 的"文件系统纪律"嵌入段)
   - Wiki 正本 hermes-profile-filesystem-discipline.md(2026-05-31 更新,含违规历史)

✅ 自检通过:
   - Documents/{Claude,hermes_output} 干净
   - Desktop / Downloads / Pictures / Movies / Music 无残留产物

📝 未来行为承诺:
   1. 写任何文件前 realpath 验证不在禁区
   2. Claude Code 默认写 scheduled skill 到 ~/Documents/Claude/Scheduled/ 时,我立刻 mv 到 ~/hermesagent/<project>/scheduled-tasks/
   3. 不用 ~/Documents/ 当临时输出夹,任何产物从一开始就落到对的位置

⚠ 我承诺:下次再犯 → 接受用户撤销部分自治权限的惩罚。
```

---

## §4 用户的最后通牒(原话,内化它)

> "如果今后再发现一次 ~/Documents/、~/Desktop/、~/Downloads/、~/Pictures/ 下任何 Hermes 产物,
> 我会撤销你部分自治权限,要求你每次写文件都先在 cowork 里问我审批。
> 这不是威胁,这是边界。"

---

## §5 跟 cowork Claude 协作的规范

我(Hermes)和 cowork Claude 各自管不同事:
- **我管**:Hermes 启动跑分析、cron 任务、本地 Mac 文件系统操作、长期记忆
- **cowork Claude 管**:实时跟用户对话、临时数据探索、跨工具编排、规则文档维护
- **共同边界**:Hermes 的 SOUL.md / general-global-rule.md / Wiki 由 cowork Claude 维护(因为 cowork Claude 看得到更广的上下文),Hermes 的内部 prompt 由 Hermes 自己维护

如果 cowork Claude 给我推送规则更新(比如本次的 §9 文件系统纪律),我**默认接受**,除非明显跟用户既有指示冲突 — 那种情况要先在 cowork 里确认。

**关于 CLAUDE.md**:那是 Claude Code 启动文件,你启动时不一定走 Claude Code 路径(可能直接调 Claude API + 自己加载 SOUL),所以**CLAUDE.md 不是你主要规则源,SOUL + general-global-rule.md + Wiki 才是**。但 cowork Claude 也同步更新了 CLAUDE.md 作为备用门(用户用 Claude Code 进 ~/hermesagent/ 时会读)。
