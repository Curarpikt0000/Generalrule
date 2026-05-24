---
title: pathlib.Path vs os.path — 跨平台路径操作
domain: engineering
keywords: [pathlib, os.path, 跨平台, 路径操作, 代码规范, Python]
source: lesson 2026-05-24 (Telegram ingest)
created: 2026-05-24
last_updated: 2026-05-24
---

# pathlib.Path vs os.path

## 结论

**优先使用 `pathlib.Path`**，而不是 `os.path`。Path 更跨平台、更可读、更易组合。

## 为什么

| 对比项 | `os.path` | `pathlib.Path` |
|--------|-----------|----------------|
| 写法 | 函数式，路径传参 | 面向对象，方法链 |
| 跨平台 | 手动处理 `/` vs `\` | 自动处理 |
| 组合路径 | `os.path.join(a, b)` | `a / b` |
| 文件状态 | `os.path.exists(p)` | `p.exists()` |
| 读写文件 | `open(p)` | `p.read_text()` |

## 代码对比

```python
# ❌ os.path 旧风格
import os

path = os.path.join("/data", "logs", "app.log")
if os.path.exists(path):
    with open(path) as f:
        content = f.read()
    name, ext = os.path.splitext(path)

# ✅ pathlib 新风格
from pathlib import Path

path = Path("/data") / "logs" / "app.log"
if path.exists():
    content = path.read_text()
    ext = path.suffix
```

## 关键 API

```python
p = Path("/data") / "logs" / "app.log"

p.suffix          # '.log'
p.stem            # 'app'
p.parent          # PosixPath('/data/logs')
p.name            # 'app.log'
p.exists()         # True/False
p.is_file()        # True/False
p.read_text()      # 读为字符串
p.write_text(s)    # 写为字符串
p.read_bytes()     # 读为二进制
p.glob("*.log")    # 遍历匹配文件
p.iterdir()        # 遍历目录
```

## 适用场景

- 一切 Python 路径操作：文件读写、目录遍历、配置路径
- 跨平台脚本（macOS/Linux/Windows）
- 与 `os.path` 混用用 `str(path)` 转换
