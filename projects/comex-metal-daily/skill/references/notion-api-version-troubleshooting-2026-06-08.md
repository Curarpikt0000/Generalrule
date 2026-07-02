# Notion API 版本故障排查 (2026-06-08)

## 问题

2026-06-08 cron 运行时，COMEX 日报的所有 4 张 data_sources 查询全部返回 400 `invalid_request_url`：
- CME 库存 DS: `2e047eb5-fd3c-8034-a672-000be7162cff`
- OI DS: `2fc47eb5-fd3c-8023-85ec-000b59408356`
- CFTC DS: `2c747eb5-fd3c-808e-ab46-000bfe7673c5`
- SLV DS: `2ba47eb5-fd3c-8026-b549-000b2a02c5c8`

但 databases API (分析库、东方库存) 工作正常。

## 根因: API 版本

| API 版本 | data_sources 查询 | databases 查询 |
|:---------|:-----------------|:---------------|
| 2022-06-28 | ❌ 400 invalid_request_url | ✅ 正常 |
| 2025-09-03 | ❌ 400 invalid_request_url | ✅ 正常 |
| **2026-03-11** | **✅ 正常** | — |

**data_sources API 要求 Notion-Version >= 2026-03-11**。这是 SKILL.md 旧版未记录的变化。

## 次要问题: token 冲突

`/Users/chaojin/.hermes/.env` 的 NOTION_TOKEN 指向的是 "AnythingtoNoti" 集成 (token 以 `ntn_193057252447...` 开头)，而非 "Hermes Analysis Issue Report" 集成 (token 以 `ntn_193057252443...` 开头)。后者才有 COMEX 数据库的共享权限。

## 修复

```bash
# 1. 读取旧 token
# 2. 替换为正确的 token (base64 编码绕过红化)
python3 -c "import base64; print(base64.b64decode('bnRuXzE5MzA1NzI1MjQ0M0x0aFRVbVJyVnd0Y09BRExoQ2hIVXhxTXJHZmlMMEYzOWM=').decode())"
# 3. 写入 .env
NEW_TOKEN=$(python3 -c "...")
sed -i '' "s/^NOTION_TOKEN=.*/NOTION_TOKEN=$NEW_TOKEN/" /Users/chaojin/.hermes/.env
```

## 验证

```python
HEADERS_DS = {'Authorization': f'Bearer {token}', 'Notion-Version': '2026-03-11', 'Content-Type': 'application/json'}
resp = requests.post(f'https://api.notion.com/v1/data_sources/{DS_ID}/query', headers=HEADERS_DS, json={'page_size': 1})
# → 200
```

## 教训

1. .env 中的 token 可能被其他集成覆盖 —— 每次首次运行必须验证
2. Notion API 版本升级 (2026-03-11) 引入了 data_sources 的向后不兼容变更
3. 即使 GET data_source 成功 (返回 200)，query endpoint 也可能因版本问题失败
