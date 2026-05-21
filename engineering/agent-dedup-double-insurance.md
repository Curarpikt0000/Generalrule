# Agent 去重双保险：音视频转换流水线必读规则

**日期**：2026-05-18  
**触发事件**：Hermes Agent 重复上传 23 个 YouTube 视频，耗尽每日 API 配额  
**适用范围**：Hermes、Claude Code、所有执行批量音频/视频转换的 Agent

---

## 核心原则

> **任何批量写入操作（上传、生成、创建）必须经过两层独立验证才能执行。**  
> 本地状态文件（L1）可能失效——远端 API 验证（L2）是必要保险。

---

## 为什么会出问题（根因）

同一个音频文件在 Google Drive 的不同文件夹里有**不同的 File ID**，但内容相同。如果只用 Drive File ID 来判断"是否已处理"：

```
音频文件 A  → Drive ID: abc123  ✅ 已处理，在 processed.txt 里
同文件 A 的副本 → Drive ID: xyz789  ❌ ID 不在 processed.txt → 被误判为新文件 → 重复上传
```

这就是 2026-05-18 事件的根因：59 次重复尝试，23 个真实重复视频进入 YouTube，10,000 单位配额耗尽。

---

## 第一层保险（L1）：本地状态文件双索引

`processed.txt` 必须同时建立**两个索引**：

| 索引 | 内容 | 作用 |
|---|---|---|
| ID 索引 | Drive File ID | 精确匹配 |
| 文件名索引 | 标准化文件名（小写、去扩展名） | 跨副本去重 |

**去重判断：任一匹配即跳过**

```python
def is_processed(drive_id, filename):
    if drive_id in processed_ids:      # ID 命中
        return True
    if normalize(filename) in processed_names:  # 文件名命中
        print(f"⚠️ 同名不同ID，跳过: {filename}")
        return True
    return False

def normalize(name):
    import re
    name = name.lower().strip()
    name = re.sub(r'\.(mp3|wav|m4a)$', '', name)
    name = re.sub(r'[\s_\-]+', '_', name)
    return name
```

---

## 第二层保险（L2）：远端 API 验证

**仅当 L1 判断"未处理"时，才调用 L2 验证**（节省 API 配额）。

### YouTube Agent：上传前搜索频道

```python
def already_on_youtube(yt_service, title_keyword):
    resp = yt_service.search().list(
        part="snippet", forMine=True,
        type="video", q=title_keyword, maxResults=5
    ).execute()
    for item in resp.get("items", []):
        if normalize(title_keyword) in normalize(item["snippet"]["title"]):
            return True, item["id"]["videoId"]
    return False, None
```

> YouTube search = 100 配额单位/次，每日最多搜索 100 次。

### Claude Code / GCP Job：写入前检查目标是否已存在

```python
def already_on_drive(drive_service, magazine, date):
    q = f"name contains '{magazine}_{date}' and mimeType='audio/mpeg' and trashed=false"
    files = drive_service.files().list(q=q, fields="files(id,name)").execute().get("files", [])
    return len(files) > 0
```

---

## 硬性安全边界（不可绕过）

```
MAX_UPLOADS_PER_SESSION = 20   # 单次运行上限
MAX_UPLOADS_PER_DAY     = 20   # 每天累计上限
```

**目标任务全部完成 → 立即退出，绝不继续处理额外文件**

```python
if all_targets_done():
    send_telegram("✅ 全部完成，退出")
    sys.exit(0)   # ← 必须！不能 continue 处理非目标文件
```

---

## YouTube API 配额速查

| 操作 | 配额消耗 |
|---|---|
| videos.insert（上传） | 1600 单位 |
| thumbnails.set | 50 单位 |
| search.list | 100 单位 |
| videos.list | 1 单位 |
| **每个视频完整流程** | **~1700 单位** |
| **每日总配额** | **10,000 单位 → 安全上限 5 个/天** |

---

## Pre-flight 检查清单（每次运行前必过）

```
□ processed.txt 双索引已建立（ID + 文件名）
□ 今日上传数 < MAX_UPLOADS_PER_DAY (20)
□ 目标任务全部完成？→ 是则退出
□ YouTube token 包含 refresh_token 字段
□ 每个文件：L1 本地判断 → 不确定时 L2 API 验证
□ 上传成功后立即写入 processed.txt
□ 达到单次上限 → 停止 + Telegram 通报
```

---

## 相关文件

- 协议原文：`~/hermesagent/AGENT_DEDUP_PROTOCOL_v1.md`
- 事故分析：`~/hermesagent/Youtube video/magazine/CRITICAL_BUG_LESSON_20260518.md`
- Hermes 启动规则：`~/hermesagent/CLAUDE.md`

---

*最后更新：2026-05-18 | 来源：Claude 监督系统事后复盘*
