---
title: Notion API 去重校验防静默失败与 Fail Loud 协议
domain: engineering
type: concept
keywords: [notion, deduplication, fail-loud, runtime-error, exception-handling]
tags: [notion, integration, deduplication, fail-loud]
source: L-2026-05-30-002
sources: [conversation-58ba548d-76d0-41b8-adb1-b9b24483e883]
created: 2026-05-30
updated: 2026-05-30
last_updated: 2026-05-30
---

# Notion API 去重校验防静默失败与 Fail Loud 协议

## 核心原则

> **在 Notion API 数据集成管道中，去重校验（Deduplication Check）的请求失败或异常必须以 Fail Loud（显式失败）原则拦截，严禁做静默兜底。**

---

## 错误行为模式 (Anti-Patterns)

### 1. 异常被 Swallow 后继续执行
当去重查询出现 Notion API 升级变更（如新版 `data_sources` 升级）、网络超时、API 密钥权限不足等异常时，使用 `try/except` 仅打印日志（或 print）并直接 `return` 或兜底返回 `exists = []`：
```python
# 错误示范
try:
    exists = notion.databases.query(...)
except Exception as e:
    print(f"去重查询失败: {e}")
    # 默默继续写入流程，导致无休止创建重复页
```

### 2. 缺少必要元数据字段时静默兜底
查询数据库元数据 `db_info` 时，如果关键字段（如 `data_sources`）不存在或列表为空，默默将其初始化为 `[]` 并直接返回空结果，误导系统判断为“数据不存在”：
```python
# 错误示范
if "data_sources" not in db_info:
    exists = []  # 错误！应抛出致命异常
```

---

## 正确做法 (Best Practices)

### 1. 强制 Fail Loud 拦截
去重查询抛出任何 Exception 时，应抛出 `RuntimeError`，导致 CI/CD 定时任务（如 GitHub Actions）挂红灯，以便人工尽早介入。
```python
try:
    if hasattr(notion, 'data_sources'):
        db_info = notion.databases.retrieve(database_id=db_id)
        assert db_info is not None, f"无法检索到数据库元数据: {db_id}"
        
        if "data_sources" in db_info and len(db_info["data_sources"]) > 0:
            ds_id = db_info["data_sources"][0]["id"]
            exists_check = notion.data_sources.query(
                data_source_id=ds_id,
                filter=filter_data
            ).get("results")
        else:
            raise RuntimeError("db_info 缺 data_sources 字段，异常情况需人工介入")
    else:
        exists_check = notion.databases.query(
            database_id=db_id,
            filter=filter_data
        ).get("results")
        
    assert exists_check is not None, "去重查询返回了 None 结果"
    assert isinstance(exists_check, list), f"去重查询返回了非列表: {type(exists_check)}"
    exists = exists_check

except Exception as e:
    raise RuntimeError(f"执行去重查询时出错，可能存在 Notion 权限或 API 路径配置问题，已强行 Fail Loud 拦截: {e}")
```

### 2. 批量清理脚本安全设计
清理历史存量重复页面时，必须实施以下双保险原则：
1. **默认 Dry Run 保护**：执行时不带任何参数或带 `--dry-run` 时仅做分析、展示表格对齐的待删除数据清单（page_id / 日期 / 创建时间），不进行实际写入。只有显式提供 `--execute` 标志才进行真实变更。
2. **审计日志输出**：实际执行归档（archive）时，每成功一条均须输出 `[Archive] page_id={id} date={d} created={ct}` 日志，便于复盘审计。

---

## 来源
* [L-2026-05-30-002](file:///Users/chaojin/Antigravity%20Projects/Daily_GoldSilvPT-inv_Notion/tasks/lessons.md#L6)
* [conversation-58ba548d-76d0-41b8-adb1-b9b24483e883](file:///Users/chaojin/.gemini/antigravity/brain/58ba548d-76d0-41b8-adb1-b9b24483e883/walkthrough.md)

## 相关页面
* [[notion-pagination-validation]]
* [[agent-dedup-double-insurance]]
