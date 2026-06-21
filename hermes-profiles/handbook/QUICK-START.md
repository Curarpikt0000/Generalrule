# 蒸馏 Handbook · 快速开始

> 给急用的 agent：跳过 handbook 主文档，按本 checklist 直接干。
> 假设你已经读了 `DISTILLATION-HANDBOOK.md` §1（铁律 5 条）和 §3（阵容设计原则）。

---

## 30 秒决定你处在哪一步

- 没有用户需求 → 去 §EXPLORE
- 有需求，没批准的计划 → 去 §PLAN
- 计划批准了，要建蓝图 → 去 §EXECUTE
- 蓝图建好了，用户要部署 → 去 §DEPLOY
- 部署完跑通，要沉淀 → 去 §LEARN

---

## §EXPLORE（30-60 分钟）

```
□ 1. 用 AskUserQuestion（或类似）问 4 个问题：
     a. 场景（金融 / 通识 / 创业 / 其他）
     b. 大师人选候选（至少 6 位）
     c. 是否需要四件套脚手架
     d. 是否需要实时数据源
□ 2. 检查阵容不重叠：每位写一句"招牌核心问"——两两对比
□ 3. 检查阵容有冲突源：至少 2-3 对立场相反的大师
```

---

## §PLAN（30 分钟，硬门）

```
□ 1. 出书面 PLAN 给用户批：
     - 目录结构（用 templates/README.template.md 那张表）
     - 大师阵容（终版）
     - 每位的蒸馏路径（复用 / GitHub / 女娲 / 手蒸馏）
     - 验收标准（哪 2-3 个真实问题用来烟雾测试）
     - 复杂度评估
□ 2. 用户明确批准 → 进 EXECUTE
□ 3. 用户说"调整某部分" → 改完再问一次
```

---

## §EXECUTE（2-4 小时）

```
□ 1. mkdir 蓝图骨架
     mkdir -p 蒸馏Hermes/<project>-hero/{skills,references}

□ 2. 收大师（按蒸馏路径）
     - 复用：cp -R ../<其他project>/skills/<大师> ./skills/
     - GitHub：git clone --depth 1 <repo> /tmp/<name>; rsync -a --exclude='.git' ...
     - 手蒸馏：跑 5-10 次 WebSearch，按 templates/master-SKILL.template.md 填

□ 3. 写 SOUL.md（抄 templates/SOUL.template.md）
     ⚠️ 必含"覆盖大师独占人格规则"段（铁律 4）

□ 4. 写 references/synthesis.md（抄 templates/synthesis.template.md）

□ 5. 写 references/depth-modes.md（抄 templates/depth-modes.template.md）
     ⚠️ 召唤映射要写 8-15 类问题类型

□ 6.（如适用）写 4 份 scaffold-*.md（参考 general-hero 的 references/）

□ 7.（如适用）写数据源接入说明（如 moomoo-setup.md）

□ 8. 写 sync.sh（抄 templates/sync.sh.template）
     chmod +x sync.sh

□ 9. 写 deploy.md（抄 templates/deploy.template.md）

□ 10. 写 README.md（抄 templates/README.template.md）

□ 11. 更新项目记忆 / 任务列表
```

---

## §DEPLOY（用户在 Mac 本地，5-15 分钟）

```
□ 1. hermes profile create <name>
□ 2. cd 蓝图 && ./sync.sh
□ 3. <name> setup    （配 LLM key + bot token）
□ 4. BotFather 关 bot privacy mode（最易忘！）
     /mybots → Bot Settings → Group Privacy → Turn OFF
     然后踢出群再加回来
□ 5. 配 config.yaml 关 Hindsight（Apple Silicon MVP）
□ 6. <name> gateway start
□ 7. Telegram 群里 @ bot 测验收题
□ 8. 形状不对 → 改蓝图 → sync → 重测
```

---

## §LEARN（30-60 分钟）

```
□ 1. 写 wiki/agent-rules/<project>-distillation.md
     参考 wiki-output/agent-rules/finance-hero-distillation.md 那个模板
□ 2. 更新 wiki/agent-rules/README.md 索引加一行
□ 3. 更新 auto-memory 的 project 文件
□ 4. 用户在 Mac 本地：
     cd /Users/chaojin/Antigravity\ Projects/Generalrule
     git add wiki/agent-rules/<project>-distillation.md wiki/agent-rules/README.md
     git commit -m "[Wiki] <project>: ..."
     git push origin main
□ 5. （可选）整理大师名册成 Notion 表给用户
```

---

## 常见加速法

### 复用已有大师（finance ⇄ general）
芒格、塔勒布、索罗斯在两个 profile 都有意义——直接 cp 即可，profile 隔离意味着各保独立副本。

### 已知现成 nuwa skill
| 大师 | 来源 |
|---|---|
| 巴菲特/格雷厄姆/利弗莫尔/索罗斯/彼得·林奇/西蒙斯/德曼/炒股养家 | Cat-Geek/investment-master-mindset |
| 芒格 | alchaincyf/munger-skill |
| 塔勒布 | alchaincyf/taleb-skill |
| 段永平 | derrickgong87/duan-yongping-skill |
| 毛泽东 | wwwaapplleecu-source/mao-skill ⚠️ 必须 rsync --exclude |
| 费曼 / 乔布斯 / 马斯克 / 纳瓦尔 / 张雪峰 / 张一鸣 / 川普 / Karpathy / Ilya 等 | alchaincyf/nuwa-skill/examples/ |

### 手蒸馏速查
每位约 30-45 分钟：5-10 次 WebSearch → 填 master-SKILL.template.md → 写 references/research.md。
**质量保证**：每个心智模型至少能引一句**真实原文**；每个"决策启发式"至少能对应到一篇**著作章节**。

---

## 一句话总结

**复用 > GitHub > 女娲 > 手蒸馏 > 自己拍脑袋**。永远从左边路径开始，不行才往右走。
