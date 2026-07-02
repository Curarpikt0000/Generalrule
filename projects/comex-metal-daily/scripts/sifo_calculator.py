#!/usr/bin/env python3
"""
§8 SIFO 双轨隐含租赁费率计算模块
====================================

符号约定（全局统一，不可绕过）:
  ΔS     = S - F           正号 = Backwardation（实物挤压方向）
  ΔS_phy = S_phy - F       正号 = SGE 实物 > 西方期货 = 物理紧
  q      = r - (F-S)/(S*t) 正号 = 高 lease rate = 借方付天文租金 = physical squeeze 信号

变量来源:
  F      = CME Section 62 PDF settle（NOT Yahoo 连续期货）
  S_fin  = LBMA 当日定盘价（NOT SGE 折算）
  S_phy  = SGE 当日收盘价 × 31.1035 / USDCNY
  r      = 3M SOFR Term Rate（或 3M T-Bill 替代）
  t      = (FND - Today) / 360

FND 日期（CME 官方）:
  Au AUG26 FND = 2026-07-31
  Ag SIN26 FND = 2026-06-30（NOT 6/27，那是周六）
  Pt PLN26 FND = 2026-06-30（同上）

版本: 1.0
作者: Hermes SIFO 模块
"""

import json
from datetime import date

# ──────────────────────────────────────────────
# 自检单元测试（脚本启动时运行，失败则拒绝生成）
# ──────────────────────────────────────────────

_SELF_TEST_DATA = {
    "F": 65.35,
    "S_fin": 68.60,
    "S_phy": 75.46,
    "r": 0.043,
    "t": 20/360,  # = 0.055555...
    "expected_q_fin": 0.895,   # +89.5%
    "expected_q_phy": 2.452,   # +245.2%
    "tolerance": 0.005         # 0.5% tolerance
}

def run_self_test():
    """运行自检。失败则抛出 AssertionError。"""
    d = _SELF_TEST_DATA
    q_fin = sifo_q_fin(d["F"], d["S_fin"], d["r"], d["t"])
    q_phy = sifo_q_phy(d["F"], d["S_phy"], d["r"], d["t"])
    dS = sifo_delta_S(d["S_fin"], d["F"])
    dS_phy = sifo_delta_S(d["S_phy"], d["F"])

    errors = []
    if abs(q_fin - d["expected_q_fin"]) > d["tolerance"]:
        errors.append(f"q_fin: got {q_fin:.4f}, expected {d['expected_q_fin']:.4f}")
    if abs(q_phy - d["expected_q_phy"]) > d["tolerance"]:
        errors.append(f"q_phy: got {q_phy:.4f}, expected {d['expected_q_phy']:.4f}")

    # 符号验证
    if not (dS > 0):  # S=68.60 > F=65.35 → Backwardation
        errors.append(f"ΔS should be positive (Backwardation), got {dS:.4f}")
    if not (dS_phy > 0):
        errors.append(f"ΔS_phy should be positive, got {dS_phy:.4f}")
    if not (q_fin > 0):
        errors.append(f"q_fin should be positive (lease rate > r), got {q_fin:.4f}")
    if not (q_phy > 0):
        errors.append(f"q_phy should be positive, got {q_phy:.4f}")

    if errors:
        raise AssertionError(
            f"SIFO 自检失败 ({len(errors)} 项):\n" + "\n".join(f"  ❌ {e}" for e in errors)
        )

    return {
        "q_fin": q_fin,
        "q_phy": q_phy,
        "dS": dS,
        "dS_pct": dS / d["S_fin"] * 100,
        "dS_phy": dS_phy,
        "dS_phy_pct": dS_phy / d["S_phy"] * 100,
        "direction": "Backwardation" if dS > 0 else "Contango",
    }


# ──────────────────────────────────────────────
# 核心计算函数
# ──────────────────────────────────────────────

def sifo_delta_S(S, F):
    """ΔS = S - F，正号 = Backwardation"""
    return S - F


def sifo_q_fin(F, S_fin, r, t):
    """纸面隐含租赁费率 q = r - (F - S_fin) / (S_fin * t)"""
    return r - (F - S_fin) / (S_fin * t)


def sifo_q_phy(F, S_phy, r, t):
    """物理隐含租赁费率 q = r - (F - S_phy) / (S_phy * t)"""
    return r - (F - S_phy) / (S_phy * t)


def sifo_direction(dS):
    """方向标签: Backwardation (ΔS>0) / Contango (ΔS<0) / 平水 (ΔS≈0)"""
    if abs(dS) < 0.01:
        return "平水"
    return "Backwardation" if dS > 0 else "Contango"


def sifo_signal_label(dS, dS_pct, dS_phy_pct, q_phy, r):
    """
    按 §8.5 阈值（校正版）判定灯色。

    先判方向:
      ΔS>0 → Backwardation → q_phy 正值为 squeeze
      ΔS<0 → Contango → 反向解读

    阈值:
      q_phy > +50%        → 🔴 物理极端 squeeze
      +5% ~ +50%          → 🟠 物理紧
      -2% ~ +5%           → 🟢 正常
      < -2%               → 🔴 物理过剩（贵金属罕见）
    """
    if dS > 0:  # Backwardation
        if q_phy > 0.50:
            return "🔴", "物理挤压极端: q_phy>>r+SGE溢价+COT空头集中三叠加"
        elif q_phy > 0.05:
            return "🟠", f"物理偏紧: Backwardation+q_phy=+{q_phy*100:.1f}%"
        elif q_phy > -0.02:
            return "🟡", f"中性偏紧: Backwardation但q_phy≈r"
        else:
            return "🔴", f"物理断裂罕见: Backwardation+q_phy负数={q_phy*100:.1f}%"
    elif dS < 0:  # Contango
        if q_phy > 0.50:
            return "🟠", f"物理宽松有限: Contango+q_phy=+{q_phy*100:.1f}%(反向解读)"
        elif q_phy > 0.05:
            return "🟡", f"物理宽松+paper过升(反向解读)"
        else:
            return "🟢", f"物理正常: Contango且q_phy接近r"
    else:
        return "⚪", "平水，无信号"


# ──────────────────────────────────────────────
# 完整计算入口
# ──────────────────────────────────────────────

def calc_sifo_metal(label, F, S_fin, S_phy, r, t):
    """
    对一个金属品种完整计算 SIFO，返回 dict。

    参数:
      label: 金/银/铂识别标签
      F: CME 期货 settle（美元/盎司）
      S_fin: LBMA 定盘（美元/盎司）
      S_phy: SGE 折算（美元/盎司）
      r: 无风险利率（小数）
      t: 到期时间（年）

    返回:
      {
        "metal": label,
        "F": F, "S_fin": S_fin, "S_phy": S_phy, "r": r, "t": t,
        "dS": ΔS值, "dS_pct": ΔS百分比, "dS_direction": 方向,
        "dS_phy": ΔS_phy值, "dS_phy_pct": ΔS_phy百分比,
        "q_fin": q_fin值, "q_fin_pct": q_fin百分比,
        "q_phy": q_phy值, "q_phy_pct": q_phy百分比,
        "signal_light": "🔴"等, "signal_text": 描述
      }
    """
    dS = sifo_delta_S(S_fin, F)
    dS_pct = dS / S_fin * 100
    dS_phy = sifo_delta_S(S_phy, F)
    dS_phy_pct = dS_phy / S_phy * 100
    q_fin = sifo_q_fin(F, S_fin, r, t)
    q_phy = sifo_q_phy(F, S_phy, r, t)
    direction = sifo_direction(dS)
    signal_light, signal_text = sifo_signal_label(dS, dS_pct, dS_phy_pct, q_phy, r)

    return {
        "metal": label,
        "F": F, "S_fin": S_fin, "S_phy": S_phy, "r": r, "t": t,
        "dS": round(dS, 4), "dS_pct": round(dS_pct, 4),
        "dS_direction": direction,
        "dS_phy": round(dS_phy, 4), "dS_phy_pct": round(dS_phy_pct, 4),
        "q_fin": round(q_fin, 6), "q_fin_pct": round(q_fin * 100, 4),
        "q_phy": round(q_phy, 6), "q_phy_pct": round(q_phy * 100, 4),
        "signal_light": signal_light,
        "signal_text": signal_text,
    }


def sifo_summary(results):
    """生成可读的 §8 摘要文本。"""
    lines = []
    lines.append("📌 本节符号约定: ΔS = S - F, 正号=Backwardation(实物挤压方向), 负号=Contango(期货升水)。q = r - (F-S)/(S·t), 正号=高lease rate=借方付天文租金=physical squeeze信号。原始F/S_fin/S_phy三个绝对值同时显示。")
    for r in results:
        m = r["metal"]
        # 一行紧凑
        line = (
            f"{m} {r['signal_light']} "
            f"ΔS=+{r['dS']:.2f}(+{r['dS_pct']:.2f}%) Backwardation " if r["dS"] > 0 else
            f"{m} {r['signal_light']} "
            f"ΔS={r['dS']:.2f}({r['dS_pct']:.2f}%) Contango "
        )
        # 修正方向显示
        dS_sign = "+" if r["dS"] > 0 else ""
        line = (
            f"{m} {r['signal_light']} "
            f"ΔS={dS_sign}{r['dS']:.2f}({dS_sign}{r['dS_pct']:.2f}%) {r['dS_direction']} "
            f"| ΔS_phy={dS_sign}{r['dS_phy']:.2f}({dS_sign}{r['dS_phy_pct']:.2f}%) "
            f"| 原始F={r['F']:.2f} S_fin={r['S_fin']:.2f} S_phy={r['S_phy']:.2f} "
            f"| q_fin={dS_sign}{r['q_fin_pct']:.2f}% q_phy={dS_sign}{r['q_phy_pct']:.2f}%"
        )
        lines.append(line)

    lines.append("")
    for r in results:
        lines.append(f"  {r['signal_light']} {r['metal']}: {r['signal_text']}")

    return "\n".join(lines)


# ──────────────────────────────────────────────
# 如果直接运行，执行自检
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("SIFO 计算模块 — 自检")
    print("=" * 60)
    result = run_self_test()
    print(f"✅ 自检通过")
    print(f"  q_fin  = +{result['q_fin']*100:.4f}% (预期 +89.5%)")
    print(f"  q_phy  = +{result['q_phy']*100:.4f}% (预期 +245.2%)")
    print(f"  ΔS     = +${result['dS']:.2f} (+{result['dS_pct']:.2f}%) {result['direction']}")
    print(f"  ΔS_phy = +${result['dS_phy']:.2f} (+{result['dS_phy_pct']:.2f}%)")
    print()
    print("完整计算示例 (6/10 Ag):")
    ag = calc_sifo_metal("Ag", 65.35, 68.60, 75.46, 0.043, 20/360)
    print(json.dumps(ag, indent=2))
