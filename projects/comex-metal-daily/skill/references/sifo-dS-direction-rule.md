# §8.5 ΔS 方向前置判断逻辑（2026-05-29 修正版）

## 背景

2026-05-29 首次日产出错：Au q_phy=-9.88% 直接套旧版阈值标为 🔴 物理断裂。
用户 Chao 纠正：Au ΔS=-$115/oz(-2.6%)是 **Contango**（F>S），不是 Backwardation 挤兑。
正确解读应为 🟡 物理短期宽松 + paper 升水偏激进。

## 修正后的规则

### 规则 1: 每个金属先读 ΔS 符号

```python
dS = S_phy - S_fin  # USD/oz
if dS > 0:
    direction = "BACKWARDATION (物理溢价/紧张)"
elif dS < 0:
    direction = "CONTANGO (物理折价/宽松)"
else:
    direction = "平水 (无信号)"
```

### 规则 2: 根据方向选择解读模板

**Backwardation (ΔS>0):** 挤兑信号生效
- q_phy >> r → 物理紧张 ➔ 🔴 短缺 / 🟠 虹吸
- q_phy 越低(负值) → 越极端挤兑

**Contango (ΔS<0):** 反向解读
- q_phy < 0 → 不是挤兑～是 **物理宽松+F升水过头**
- paper 可能向 SGE 下沿回归
- 典型场景：Au 5/28

**平水 (ΔS≈0):** 忽略

### 规则 3: 输出叙事区分

- Au Contango: 🟡 "物理短期宽松+期货升水偏激进。东方已完成阶段性吸货,paper可能向SGE下沿回归"
- Ag Backwardation: 🟠 "实物虹吸持续。SGE溢价维持,工业需求强劲或进口通道不畅"
- Pt Backwardation极端: 🔴 "短缺极端。套利资本无视carry成本搬运现货。Eligible几乎耗竭+交收稀疏"

## 来源

- 用户指令：2026-05-29 14:00 UTC+
- wiki 页面：Generalrule/wiki/com/dsifo-threshold-logic.md
