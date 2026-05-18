---
title: YouTube Pipeline - gen_images Template Issue
domain: engineering
keywords: [youtube, pipeline, gen_images, template, scan_and_process]
source: L-20260519-001
created: 2026-05-19
last_updated: 2026-05-19
---

# YouTube Pipeline: gen_images.py is a Template, Not CLI-Compatible

## Problem
`scan_and_process.py` calls `gen_images.py` with CLI arguments:
```python
cmd = ['python3', gen_script, blocks_path, img_dir,
       '--magazine-name', mag, '--date-str', suffix]
subprocess.run(cmd, timeout=600, capture_output=True, text=True)
```

But `gen_images.py` is a **hardcoded template** — it has constants like `MAGAZINE = "杂志名称"` at the top, and it does NOT use `argparse`. The CLI arguments are silently ignored, and the script tries to read blocks from `/tmp/杂志名称_YYYYMMDD_blocks.json` which doesn't exist.

This causes a **silent failure**: subprocess.run returns exit code 0, but no images are generated.

## Fix
Use a dedicated script that either:
1. Edits the template constants before running
2. Generates Pillow gradient images directly (no Imagen dependency)

See `/tmp/batch_gen_images.py` for the working approach.
