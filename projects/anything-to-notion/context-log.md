# 项目上下文日志

> 每 session 或重要变更后更新此日志，记录决策、事实配置、进展和待办。

---

## 2026-06-13

### 决策
- 项目初始化，首批上下文快照迁移

### 事实配置
- **项目路径**: `~/hermesagent/Anything-to-Notion/`
- **脚本**: `atn_write.py` → 写入 Notion AtN Inbox
- **DB ID**: `35547eb5-fd3c-81db-bff3-c50275484e33`
- **Integration**: Hermes Analysis Issue Report
- **临时文件**: `/tmp/atn_raw.md` + `/tmp/atn_body.md`

### 核心规则
1. 所有 AtN 文章写入 AtN Inbox 数据库（`35547eb5...`），不是 Other Links 或其他 DB
2. body 严禁 LLM 总结，必须原文直出
3. 每篇文章一篇 page，标题 = 文章标题，Rating = 📥 待读
4. body ≥ 1000 字符才算成功，否则用 browser 补充
5. 脚本路径 `~/hermesagent/Anything-to-Notion/atn_write.py`（不是 `~/scripts/`）

### 进展
- 项目已运行中，每晚 02:00 cron 自动压缩上下文

### 待办
- 持续维护上下文快照

---

## 2026-06-12

### 决策
- atn_write.py 的 DB ID 被改为错误的 `2e047eb5...`（之前叫 "Other Links"），导致写到错误数据库

### 待办
- `2026-06-13` 修正回 `35547eb5-fd3c-81db-bff3-c50275484e33`

---

## 2026-06-22

### 决策
- 每晚 cron 已正常运行，AGENTS.md 的过时路径引用（tasks/context-snapshot.md → docs/context-log.md）已于 6月21日 cron 运行中修正

### 事实配置
- **项目路径**: `~/hermesagent/Anything-to-Notion/` ✅
- **脚本**: `atn_write.py` → 写入 Notion AtN Inbox ✅
- **DB ID**: `35547eb5-fd3c-81db-bff3-c50275484e33` ✅
- **Integration**: Hermes Analysis Issue Report ✅

### 进展
- DB ID、脚本路径、核心规则均无变更
- context-log.md 和 AGENTS.md 已对齐（路径引用全部指向 docs/context-log.md，cron时间02:00）
- 无新用户纠正或工作流修改

### 待办
- 持续维护上下文快照

---

## 2026-06-27

### 决策
- 无变更 — AtN pipeline 持续正常运行
- 无新的用户纠正、DB ID 更新或工作流修改

### 事实配置
- **项目路径**: `~/hermesagent/Anything-to-Notion/` ✅
- **脚本**: `atn_write.py` → 写入 Notion AtN Inbox ✅
- **DB ID**: `35547eb5-fd3c-81db-bff3-c50275484e33` ✅
- **Integration**: Hermes Analysis Issue Report ✅

### 进展
- 6月27日 01:46: YouTube "外星人"视频 → oembed → faster-whisper 转录 (627.5s, 3638字, 繁转简) → atn_write.py → 成功写入 Notion ✅
- DB ID、脚本路径、核心规则均无变更
- AGENTS.md 关键信息全部准确

### 待办
- 持续维护上下文快照

---

## 2026-06-29

### 决策
- 无变更 — AtN pipeline 持续正常运行
- 无新的用户纠正、DB ID 更新或工作流修改

### 事实配置
- **项目路径**: `~/hermesagent/Anything-to-Notion/` ✅
- **脚本**: `atn_write.py` → 写入 Notion AtN Inbox ✅
- **DB ID**: `35547eb5-fd3c-81db-bff3-c50275484e33` ✅
- **Integration**: Hermes Analysis Issue Report ✅

### 进展
- 6月28日 21:49: 微信公众号文章「创意设计师必装10大Skills」→ html2text 提取 → atn_write.py → 成功写入 ✅
- 所有 AtN 操作均正确写入 AtN Inbox DB，无写错数据库的纠正
- DB ID、脚本路径、核心规则均无变更
- AGENTS.md 关键信息全部准确

### 待办
- 持续维护上下文快照
