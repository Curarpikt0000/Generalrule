# COMEX SIFO 双轨租赁费率（独立 skill 存档）

> 本文件是原 `comex-sifo` skill 的内容，已合并入 `comex-daily-report` SKILL.md §8 ~ §8.5。
> 原 skill 只包含 SIFO 计算模块，是 comex-daily-report v3 的子集。

## 原 skill 已合并的内容

| 原 comex-sifo 内容 | v3 位置 |
|:------------------|:--------|
| 4 张 Notion 源表 | SKILL.md 数据源表 |
| JSON 反义提醒 | SKILL.md §0 |
| 外部数据（USDCNY, r, S_fin, S_phy） | SKILL.md §8 |
| 6 分析维度 | SKILL.md §1~§6 |
| q_fin/q_phy 公式 | SKILL.md §8 |
| ΔS 方向前置判断 + 组合信号表 | SKILL.md §8.5 |
| 历史修正 (Au 5/29 从🔴→🟡) | SKILL.md 用户偏好 |
| 三步审计 | SKILL.md §8 |
| moomoo OpenD 验证 | SKILL.md §8 |
| 写入注意事项 | SKILL.md 写入逻辑 |
| 范围与数据纪律 | SKILL.md §0 |

## 唯一未被 v3 SKILL.md 显式包含的内容

以下内容来自原 comex-sifo 但 v3 SKILL.md 已通过 references 覆盖：
- `t` 值详细计算（Au AUG26=63/360, Ag JUL26=32/360, Pt JUL26=29/360）— v3 中由公式生成，不硬编码天数
