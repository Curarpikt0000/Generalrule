# Anything-to-Notion (AtN) — 项目入口

## 一句话

把 URL（微信、YouTube、GitHub、通用网页）的内容提取 + 转录后，保存到 Notion **AtN Inbox** 数据库。

## 核心数据关系

```
用户发 URL → 提取正文(raw+body) → /tmp/atn_raw.md + /tmp/atn_body.md → atn_write.py → Notion AtN Inbox
```

## 关键配置

| 项目 | 值 |
|------|-----|
| Notion Database | **AtN Inbox** (`35547eb5-fd3c-81db-bff3-c50275484e33`) |
| Notion Integration | Hermes Analysis Issue Report (`36e47eb5-fd3c-81ce-a7a7-0027fc3b03c1`) |
| 脚本位置 | `~/hermesagent/Anything-to-Notion/atn_write.py` |
| 临时文件 | `/tmp/atn_raw.md` (frontmatter) + `/tmp/atn_body.md` (正文) |
| 上下文快照 | `docs/context-log.md` (每晚 cron 更新) |

## 数据库 Schema (AtN Inbox)

```
Name:       title (文章标题)
Rating:     select (📥 待读 / ⭐ 重点 / ✅ 已读)
Source:     url (原文链接)
Date Captured: date (抓取日期)
```

**📌 记住：所有 AtN 文章都写入这个数据库，不要写到 Other Links 或其他地方！**

## AtN 管道速查

### 微信公众号 (mp.weixin.qq.com)
1. `web_extract(url)` 获取全文
2. 写 frontmatter → `/tmp/atn_raw.md`
3. 写 body → `/tmp/atn_body.md`
4. 跑 `python3 ~/hermesagent/Anything-to-Notion/atn_write.py`

### YouTube
1. `fetch_transcript.py` 获取字幕（Level 1-3 逐级 fallback）
2. 同上流程

### 注意事项
- **严禁对 body 做任何 LLM 总结** — 原文直出
- body 字符数 ≥ 1000 才算成功提取；< 1000 用 browser_console 补充
- atn_write.py 已固定正确的 DB ID（2026-06-13 修正）

## 相关文件
- `docs/context-log.md` — 每晚 cron 自动更新，记录每条 Telegram topic 的上下文快照
- `AGENTS.md`（本文件）— 项目入口
- `CLAUDE.md` → `AGENTS.md`（符号链接）

## 每晚 cron
- 时间：每天 02:00
- 作用：压缩当前 Telegram HermesGroup 各 topic 的上下文到 `docs/context-log.md`
- 确保 agent 不会丢失关键的 Notion 数据库信息
