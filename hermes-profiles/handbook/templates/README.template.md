# [PROJECT_NAME] · Profile 部署蓝图

> **本目录不是项目，是蓝图。** 是 Hermes `[PROFILE_NAME]` profile（`~/.hermes/profiles/[PROFILE_NAME]/`）的版本受控源。
> 改动这里 → 跑 `sync.sh` 同步到 profile → 自动重启 launchd 服务生效。

## 文件分工

| 蓝图文件 | 部署后位置 | 作用 |
|---|---|---|
| `SOUL.md` | `~/.hermes/profiles/[PROFILE_NAME]/SOUL.md` | profile 的"行为核心"，每条消息重载 |
| `skills/<大师>/SKILL.md` + `references/` | `~/.hermes/profiles/[PROFILE_NAME]/skills/<大师>/` | [N_MASTERS] 位大师的思维定义 |
| `references/synthesis.md` | 同上 | 综合裁决四问规则 |
| `references/depth-modes.md` | 同上 | 快答 vs 全议会档位 + 召唤映射 |
[SCAFFOLD_FILES_ROWS]
<!-- 如有脚手架：
| `references/scaffold-*.md` | 同上 | 脚手架四件套细则 |
-->
[DATA_SOURCE_ROW]
<!-- 如有数据源：
| `references/<source>-setup.md` | 同上 | 数据源接入说明 |
-->
| `sync.sh` | （不部署）| 蓝图→profile 一键同步 |
| `deploy.md` | （不部署）| 首次部署清单 |

## [N_MASTERS] 位大师阵容

| 大师 | 来源 | 招牌镜片 |
|---|---|---|
[MASTER_TABLE_ROWS]

<!-- 示例行：
| 巴菲特 | [investment-master-mindset](https://github.com/Cat-Geek/investment-master-mindset) | 护城河 / 安全边际 / 集中长持 |
-->

[SCAFFOLD_DESCRIPTION]
<!-- 如有四件套脚手架：
## 四件套脚手架（[项目名] 灵魂，每次回答强制走完）

1. **费曼翻译层** —— 讲给 5 岁小孩 + 6 步讲述训练
2. **证伪自检** —— "我可能错在哪 + 一个具体反例"
3. **索绪尔历时/共时横纵** —— 时间位 + 系统位双扫
4. **演化 / 同类强制辅维** —— 借库恩 + 波特镜片
-->

## 它和其他 profile 的关系

```
~/.hermes/profiles/worker/          ← 工程师纪律
~/.hermes/profiles/finance/         ← 投资大师议会（11 位）
~/.hermes/profiles/general/         ← 通识/人生议会（10 位 + 四件套）
~/.hermes/profiles/[PROFILE_NAME]/  ← 本蓝图部署目标
```

每个 profile 完全独立：自己的 SOUL / bot / 记忆 / skills，互不污染。

## 设计要点

议会模式四层（详 [`handbook/DISTILLATION-HANDBOOK.md`](../handbook/DISTILLATION-HANDBOOK.md) §5）：
1. **大师层** — 每位 SKILL.md 定义"声部"
2. **综合裁决层** — 共识 / 冲突 / 根源 / 我倾向哪条路径（强制四问）
3. **深度档位** — 快答（默认 [N] 位）vs 全议会（最多 [N_MASTERS] 位）
4. **反例自检** — 综合后必带"我可能错在哪 + 反例"

[项目特化点：如 finance 的 moomoo 取数纪律 / general 的四件套脚手架]

## 上游

服从 General Global Rule（认知纪律、§2.10 显式失败、研究先行）。
方法论详见 [`handbook/DISTILLATION-HANDBOOK.md`](../handbook/DISTILLATION-HANDBOOK.md)。
