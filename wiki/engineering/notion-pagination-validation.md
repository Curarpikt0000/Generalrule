---
title: Notion 数据验证必须循环翻页
domain: engineering
keywords: [notion, pagination, blocks, has_more, validation]
source_lesson: L-2026-05-04-003
created: 2026-05-04
---

# Notion 数据验证必须循环翻页

## 核心规则
验证 Notion 页面内容时，必须循环处理 `has_more` 字段，不能只读第一页。

## 错误行为
只调用一次 Notion API，假设返回了全部内容。

## 正确做法
```python
results = []
cursor = None
while True:
    response = notion.blocks.children.list(
        block_id=page_id,
        start_cursor=cursor
    )
    results.extend(response["results"])
    if not response["has_more"]:
        break
    cursor = response["next_cursor"]
```

## 适用场景
- 验证 Notion 页面写入是否完整
- 读取超过 100 个 block 的页面
- 任何 Notion list API 调用
