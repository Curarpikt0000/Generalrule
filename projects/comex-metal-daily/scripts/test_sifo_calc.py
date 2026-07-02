#!/usr/bin/env python3
"""
SIFO 计算自检单元测试
=====================

每次写报告脚本在启动时执行:
  python3 test_sifo_calc.py
  如果返回码 != 0，拒绝生成报告。

测试用 6/10 实测数据:
  F=65.35, S_fin=68.60, S_phy=75.46, r=0.043, t=20/360

期望:
  q_fin = +89.5% ± 0.5%
  q_phy = +245% ± 1%
  ΔS    = +$3.25 (+4.74%) Backwardation

版本: 1.0
"""

import sys, os

# 添加脚本路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from sifo_calculator import run_self_test, calc_sifo_metal

def test_self_test():
    """运行内置自检（6/10 Ag 数据）"""
    result = run_self_test()
    
    # 符号验证
    assert result["dS"] > 0, f"ΔS应为正(Backwardation), 实为 {result['dS']}"
    assert result["direction"] == "Backwardation", f"方向应为Backwardation, 实为 {result['direction']}"
    assert result["q_fin"] > 0, f"q_fin应>0, 实为 {result['q_fin']}"
    assert result["q_phy"] > 0, f"q_phy应>0, 实为 {result['q_phy']}"
    
    # 数值验证
    assert 0.89 <= result["q_fin"] <= 0.90, f"q_fin应在0.89~0.90, 实为 {result['q_fin']}"
    assert 2.42 <= result["q_phy"] <= 2.48, f"q_phy应在2.42~2.48, 实为 {result['q_phy']}"
    assert 3.20 <= result["dS"] <= 3.30, f"ΔS应在3.20~3.30, 实为 {result['dS']}"
    assert 4.70 <= result["dS_pct"] <= 4.80, f"ΔS%应在4.70~4.80%, 实为 {result['dS_pct']}"
    
    return True

def test_contango_scenario():
    """测试 Contango 场景（F > S，ΔS 负值）"""
    result = calc_sifo_metal("Test", F=100, S_fin=98, S_phy=110, r=0.05, t=30/360)
    assert result["dS_direction"] == "Contango", f"F>S应Contango, 实为 {result['dS_direction']}"
    assert result["dS"] < 0, f"ΔS应为负, 实为 {result['dS']}"
    return True

def test_flat_scenario():
    """测试平水场景（F ≈ S）"""
    result = calc_sifo_metal("Test", F=100, S_fin=99.99, S_phy=100, r=0.05, t=30/360)
    assert result["dS_direction"] in ["Contango", "平水"], f"近平水应为Contango或平水"
    return True

def test_summary_output():
    """测试摘要输出可读性"""
    results = [
        calc_sifo_metal("Au", 4286.40, 4182.60, 4203.00, 0.038, 50/360),
        calc_sifo_metal("Ag", 65.35, 68.60, 75.46, 0.043, 20/360),
        calc_sifo_metal("Pt", 1711.60, 1690.00, 1944.00, 0.043, 20/360),
    ]
    from sifo_calculator import sifo_summary
    summary = sifo_summary(results)
    assert "F=" in summary
    assert "S_fin=" in summary
    assert "S_phy=" in summary
    assert "Backwardation" in summary or "Contango" in summary
    return True


if __name__ == "__main__":
    tests = [
        ("自检 (6/10 Ag)", test_self_test),
        ("Contango 场景", test_contango_scenario),
        ("平水场景", test_flat_scenario),
        ("摘要输出", test_summary_output),
    ]
    
    failures = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  ✅ {name}")
        except AssertionError as e:
            print(f"  ❌ {name}: {e}")
            failures += 1
        except Exception as e:
            print(f"  ❌ {name}: 异常 {type(e).__name__}: {e}")
            failures += 1
    
    print()
    if failures == 0:
        print(f"✅ 全部 {len(tests)} 项测试通过")
        sys.exit(0)
    else:
        print(f"❌ {failures}/{len(tests)} 项测试失败 — 拒绝生成报告")
        sys.exit(1)
