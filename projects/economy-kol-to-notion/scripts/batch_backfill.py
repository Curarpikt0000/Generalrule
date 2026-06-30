#!/usr/bin/env python3
"""并发批量回溯所有活跃 KOL 当日窗口。
用法: python3 batch_backfill.py <start> <end> [max_workers]
逐 KOL 调用 backfill_one 的搜索逻辑, 输出汇总到 data/backfill/<id>.json
"""
import json, sys, subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_one(kol_id, start, end):
    try:
        p = subprocess.run(
            ["python3", "scripts/backfill_one.py", kol_id, start, end],
            capture_output=True, text=True, timeout=150)
        # parse last summary line
        return kol_id, p.returncode, p.stdout.strip().splitlines()[-1] if p.stdout.strip() else p.stderr[:120]
    except subprocess.TimeoutExpired:
        return kol_id, -1, "TIMEOUT"
    except Exception as e:
        return kol_id, -2, str(e)[:120]

def main():
    start, end = sys.argv[1], sys.argv[2]
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    reg = json.load(open("data/kol_registry.json"))
    kols = [k["id"] for k in reg["kols"] if k.get("active")]
    print(f"批量回溯 {len(kols)} KOL | {start}~{end} | workers={workers}")
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(run_one, kid, start, end): kid for kid in kols}
        for f in as_completed(futs):
            kid, rc, msg = f.result()
            done += 1
            flag = "OK" if rc == 0 else f"ERR({rc})"
            print(f"[{done}/{len(kols)}] {flag} {kid}: {msg}")
    print("DONE")

if __name__ == "__main__":
    main()
