"""批量 apply 驱动器: 读 verdict JSON (page_id -> 期限标签数组), 逐行安全写回。
verdict 只含期限标签, 不含原文。apply_terms 内部自读真 leg 合并+多重校验+读回。
用法: python3 batch_apply.py <verdict.json>
"""
import json, sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from add_term import apply_terms

verdict = json.load(open(sys.argv[1]))
ok = fail = 0
for pid, terms in verdict.items():
    try:
        r = apply_terms(pid, terms)
        if r: ok += 1
        else: fail += 1
    except Exception as e:
        print(f"ERR {pid[:8]}: {str(e)[:80]}", file=sys.stderr); fail += 1
    time.sleep(0.35)  # Notion 限流友好
print(f"\n=== 批量完成: OK {ok} / FAIL {fail} / 共 {len(verdict)} ===")
