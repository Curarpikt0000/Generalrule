---
title: Notion API Token — ntn_ 格式与 shell 截断陷阱
domain: engineering
keywords: [notion, api-token, ntn, shell, 截断, secret, dotenv]
source: hermes-notion-token-lesson-20260620
created: 2026-06-20
last_updated: 2026-06-20
---

# Notion API Token — ntn_ 格式与 shell 截断陷阱

## 背景

Notion 2024-09-25 起将 Internal Integration Token 从 `secret_` 前缀改为 `ntn_` 前缀。新旧 token 功能一致，但 `ntn_` 格式更容易被 secrets scanner 识别。

## 踩坑：shell 中的 `...` 截断

当用户在 Telegram/聊天中发送 token，且工具响应中 token 被截断显示为 `ntn_19...9c` 时：

**直接复制 `ntn_19...9c` 到脚本或终端 → 实际写入的是字面量 `ntn_19...9c`（长度 11），而非完整 token。**

这是因为 Hermes 的 response 可能被截断显示（`...` 是省略号），而非 token 本身的内容。

### 正确做法

1. 从用户的原始消息读 token，不从工具输出的预览截断中读
2. 在 Python 脚本中写完整 token 字面量，避免 shell 变量传递
3. 验证 token 长度：完整 `ntn_` token 长度约 45-55 字符

## 验证方法

```python
import requests

key = "ntn_..."  # 从用户原始消息准确复制
headers = {
    "Authorization": f"Bearer {key}",
    "Notion-Version": "2022-06-28"
}

r = requests.get("https://api.notion.com/v1/databases/{database_id}", headers=headers)
print(r.status_code)  # 200 = 有效，401 = 无效
```

如果返回 401 但确认 token 字面无误，检查：
1. Integration 是否已 connect 到目标 workspace
2. Integration 是否已 share 到目标 Database（在 Notion 页面右上角 → Connections → 添加）
3. Database ID 是否正确（UUID 格式）

## 生产环境配置

cron job 的 no_agent 模式使用 bash wrapper 加载 token：

```bash
#!/bin/bash
export NOTION_API_KEY="ntn_..."
exec python3 script.py "$@"
```

- `exec` 确保 Python 进程继承环境变量
- 双引号包裹 token 防止 shell 特殊字符展开
- 脚本内用 `os.environ.get("NOTION_API_KEY")` 读取
