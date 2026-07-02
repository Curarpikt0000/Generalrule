# COMEX 日报 v2 格式规范（存档 — 被 v3 红绿灯版取代）

> 本文件记录了 `comex-report` skill 的内容（v2 规范），已于 2026-06-05 合并入 `comex-daily-report` (v3) SKILL.md。
> v3 是当前活跃版。本文件仅为历史存档，供迁移参考。

## v2 核心差异

v3 (§0 仪表盘 + §0.5 战术 + 红绿灯每节标题) 替代了 v2 的纯长文格式。
迁移时需注意的非格式差异：

### SIFO 模块：v2 vs v3

| 项目 | v2 | v3 |
|:----|:---|:---|
| r (无风险利率) | 3M Term SOFR (CME) | DGS3MO (FRED, 相关性>0.99 代理) |
| F 源 | Section62 PDF + pdftotext | Section62 PDF (GitHub raw) |
| S_fin 源 | LBMA / Kitco | Yahoo Finance API (无auth) |
| 信号方向 | 无 ΔS 前置判断 | **严格先判 ΔS 方向再套阈值表** |
| Au ΔS<0 | 标 🔴 物理断裂 | 🟡 中国需求软化（反向解读） |
| Pt 阈值 | 同 Au/Ag | 🔴 短缺极端（>r+100%） |
| 输出 | Hermes Analysis 列 ≤300字 | 同上 + §0 仪表盘 18 灯表 |
| 写入逻辑 | archive 旧 page + 创建新 | 同上 |

### OI 展期拆解格式（v2 三层风格）

v2 的展期拆解在 v3 中沿用但调整为红绿灯格式：

```
GC: 总OI 348,209 (+2,504)
  ├─ 6月主力(FND临近) JUN26 25,382 (-6,426)  ← 展期流出
  ├─ 8月新主力 AUG26 261,561 (+7,310)         ← 接力
  └─ 远月 DEC26 32,788 (+1,818)               ← 主动建仓 ⭐
净判定: 远月+1,818是真增量(非展期)
```

### API 坑点（v2 独有，已合并入 v3）

- Bullet annotations 被拒：创建 block 时 strip annotations
- 新建 page 自动 archived → 需先 unarchive 再写
- Hermes Analysis 列名尾随空格
- 批量写入 ≤50 blocks/批
