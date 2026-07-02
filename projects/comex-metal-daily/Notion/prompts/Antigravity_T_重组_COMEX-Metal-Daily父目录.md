# Antigravity 任务 T-Reorg-2026-05-31 — 把散落的 COMEX repos 收进父目录

> 用户(Claude Chao)对结构治理的明确指示。今天发现 6 个 COMEX 相关 git repo 散落在 `~/Antigravity Projects/` 根目录下,污染了 Antigravity 工作区。要求重组到一个统一父目录。

---

## §1 现状

```
~/Antigravity Projects/
├── AI_Blog_Generator/                          ← 跟 COMEX 无关
├── Daily_CME-issuestop-inventory_Notion/       ← COMEX T1 (git repo)
├── Daily_GoldSilvPT-inv_Notion/                ← COMEX T6/T7 (git repo, 含 sync_shfe.py)
├── Daily_Metal-OI-CME_Notion/                  ← COMEX T2 (git repo)
├── Daily_ishareGLDSLVinv_Notion/               ← COMEX T4 (git repo)
├── Weekly_CFTC-Concentrate_Notion/             ← COMEX T3 (git repo)
├── comex-hermes-ingestor/                      ← Antigravity handover 规格项目(也是 git repo)
├── Generalrule/                                ← 跟 COMEX 无关(全局规则)
└── Tokyo_Child_Event_Webpage/                  ← 跟 COMEX 无关
```

6 个 COMEX 相关文件夹散在根目录,**用户认为这是反模式**。

---

## §2 目标结构(用户已批准 — B1 方案)

```
~/Antigravity Projects/
├── AI_Blog_Generator/                          ← 保留位置
├── COMEX-Metal-Daily/                          ← ★ 新建父目录
│   ├── Daily_CME-issuestop-inventory_Notion/   ← mv 进来
│   ├── Daily_GoldSilvPT-inv_Notion/            ← mv 进来(注意:sync_shfe.py 在这,plist 路径要改!)
│   ├── Daily_Metal-OI-CME_Notion/              ← mv 进来
│   ├── Daily_ishareGLDSLVinv_Notion/           ← mv 进来
│   ├── Weekly_CFTC-Concentrate_Notion/         ← mv 进来
│   └── comex-hermes-ingestor/                  ← mv 进来
├── Generalrule/                                ← 保留位置
└── Tokyo_Child_Event_Webpage/                  ← 保留位置
```

---

## §3 你的执行步骤(必须按顺序)

### Step 1: 创建父目录
```bash
mkdir -p ~/Antigravity\ Projects/COMEX-Metal-Daily
```

### Step 2: 移动 6 个文件夹(在 Mac 终端跑,同盘 mv 瞬间完成)
```bash
cd ~/Antigravity\ Projects
mv Daily_CME-issuestop-inventory_Notion COMEX-Metal-Daily/
mv Daily_GoldSilvPT-inv_Notion COMEX-Metal-Daily/
mv Daily_Metal-OI-CME_Notion COMEX-Metal-Daily/
mv Daily_ishareGLDSLVinv_Notion COMEX-Metal-Daily/
mv Weekly_CFTC-Concentrate_Notion COMEX-Metal-Daily/
mv comex-hermes-ingestor COMEX-Metal-Daily/
```

### Step 3: 验证每个 repo 的 .git/ 完整
```bash
for d in COMEX-Metal-Daily/*/; do
  if [ -d "$d.git" ]; then
    echo "✅ $d (git repo OK, branch: $(cd "$d" && git branch --show-current))"
  else
    echo "⚠ $d (no .git, might be regular folder)"
  fi
done
```

期望:6 个全部 ✅。

### Step 4: 修复硬编码路径(★ 关键!)

**用户 Mac 上有 1 个 launchd plist 引用旧路径**,必须改:

```bash
# 文件:~/Library/LaunchAgents/com.chaojin.shfe-weekly.plist
# 旧路径(line ~10):
#   <string>/Users/chaojin/Antigravity Projects/Daily_GoldSilvPT-inv_Notion/sync_shfe.py</string>
# 改成:
#   <string>/Users/chaojin/Antigravity Projects/COMEX-Metal-Daily/Daily_GoldSilvPT-inv_Notion/sync_shfe.py</string>

# 执行(原地替换):
sed -i '' \
  's|/Users/chaojin/Antigravity Projects/Daily_GoldSilvPT-inv_Notion/sync_shfe.py|/Users/chaojin/Antigravity Projects/COMEX-Metal-Daily/Daily_GoldSilvPT-inv_Notion/sync_shfe.py|g' \
  ~/Library/LaunchAgents/com.chaojin.shfe-weekly.plist

# 验证 plist 仍然合法
plutil -lint ~/Library/LaunchAgents/com.chaojin.shfe-weekly.plist

# 重载 launchd 任务以应用新路径
launchctl unload ~/Library/LaunchAgents/com.chaojin.shfe-weekly.plist
launchctl load ~/Library/LaunchAgents/com.chaojin.shfe-weekly.plist
launchctl list | grep shfe

# 手工触发一次验证新路径能跑通
launchctl start com.chaojin.shfe-weekly
sleep 30
tail -50 /tmp/shfe_weekly.log
```

期望:`shfe_weekly.log` 显示成功 PATCH 一行数据(已有的会被 idempotent 更新)。

### Step 5: 全局搜索是否还有其他硬编码引用

```bash
# 在 ~/hermesagent 和 ~/Antigravity Projects 全局搜
grep -r "Antigravity Projects/Daily_" ~/hermesagent ~/Antigravity\ Projects --include="*.py" --include="*.md" --include="*.sh" --include="*.json" --include="*.plist" 2>/dev/null
grep -r "Antigravity Projects/Weekly_" ~/hermesagent ~/Antigravity\ Projects --include="*.py" --include="*.md" --include="*.sh" --include="*.json" --include="*.plist" 2>/dev/null
grep -r "Antigravity Projects/comex-hermes-ingestor" ~/hermesagent ~/Antigravity\ Projects --include="*.py" --include="*.md" --include="*.sh" --include="*.json" --include="*.plist" 2>/dev/null
```

**任何还指向旧路径(不含 `COMEX-Metal-Daily/`)的命中,逐个 sed 修复**。常见涉及:
- GitHub Action workflow YAML
- requirements.txt 路径
- Hermes referenced_prompts
- 文档里的"项目结构图"

### Step 6: 更新自己的 AGENTS.md

在 `~/Antigravity Projects/COMEX-Metal-Daily/comex-hermes-ingestor/AGENTS.md` 顶部加:

```markdown
## 🚨 COMEX 项目结构纪律(2026-05-31 加入)

**所有 COMEX 相关 repo 必须在 `~/Antigravity Projects/COMEX-Metal-Daily/` 下,不得新增到根目录**。

具体来说,**未来新建 COMEX 子项目时**:
- ❌ 错误:`~/Antigravity Projects/Monthly_LBMA-Au-Vault_Notion/`(放根目录)
- ✅ 正确:`~/Antigravity Projects/COMEX-Metal-Daily/Monthly_LBMA-Au-Vault_Notion/`

**违反此纪律 = 给用户制造文件夹垃圾,必须立刻撤回**。

如果不确定一个项目算不算"COMEX 相关",停下来问用户。
```

### Step 7: 同步更新全局规则

在 `~/Antigravity Projects/Generalrule/AGENTS.md` 加一条:

```markdown
## 项目文件归属铁律(2026-05-31 加入)

**项目相关 repo / 文件夹必须放进对应"项目父目录"下,不得直接散落在 `~/Antigravity Projects/` 根目录**。

已确定的项目父目录:
| 项目族 | 父目录 |
|---|---|
| COMEX 贵金属日报 | `~/Antigravity Projects/COMEX-Metal-Daily/` |
| (其他项目待定) | 由用户在新建第一个 repo 时指定 |

**判定规则**:如果一个 repo 是"项目族"的第 1 个 repo,跟用户确认是否需要为它建父目录;如果是第 2 个或更多,**必须**放进既有父目录。

**违规惩罚**:用户人工迁移 + 历史教训记录到本文件。
```

---

## §4 验收清单(全部要 ✅)

- [ ] `~/Antigravity Projects/COMEX-Metal-Daily/` 存在,里面有 6 个子文件夹
- [ ] 6 个子文件夹各自 .git/ 完整,`git status` 不报错
- [ ] `~/Antigravity Projects/` 根目录下不再有以 `Daily_`、`Weekly_`、`comex-` 开头的散落文件夹
- [ ] launchd plist 路径已更新,`plutil -lint` 通过
- [ ] `launchctl start com.chaojin.shfe-weekly` 跑通,`/tmp/shfe_weekly.log` 写入数据
- [ ] 全局 grep 不再有指向旧路径的硬编码引用
- [ ] `COMEX-Metal-Daily/comex-hermes-ingestor/AGENTS.md` 已加纪律段落
- [ ] `Generalrule/AGENTS.md` 已加"项目文件归属铁律"

---

## §5 完成后向用户报告什么

```
✅ 重组完成。新结构:~/Antigravity Projects/COMEX-Metal-Daily/{6 个子文件夹}
✅ launchd plist 路径已更新并跑通(/tmp/shfe_weekly.log 最新行:[贴一行])
✅ 全局引用已修复 X 处(列出具体改过的文件)
✅ AGENTS.md 双位置加纪律
```

如果任何 step 失败,**立刻停**,贴错误信息和卡在哪一步给用户,不要自作主张跳过。

---

## §6 不在范围

- 不动 AI_Blog_Generator/、Generalrule/、Tokyo_Child_Event_Webpage/(跟 COMEX 无关)
- 不动 ~/hermesagent/ 下任何文件(那是 Hermes 的工作区,不是 Antigravity 的)
- 不动 6 个 repo 内部代码(只换位置,不改 .py / .yml / .md 内容,除非是路径修复)
- 不主动 git push(等用户确认结构 OK 后再决定是否提交)
