# Anything-to-Notion (AtN) — Docker 知识包

## 项目简介

**URL→Notion 通用工具**，支持以下来源的内容提取与保存：

- **微信公众平台** — mp.weixin.qq.com 文章正文提取
- **YouTube** — 字幕/转录抓取（Level 1-3 逐级 fallback）
- **GitHub** — 通用内容提取
- **通用网页** — html2text 正文提取

所有提取结果写入 Notion **AtN Inbox** 数据库。

## 核心流程

```
用户发 URL → web_extract / fetch_transcript → /tmp/atn_raw.md + /tmp/atn_body.md → atn_write.py → Notion AtN Inbox
```

1. 根据 URL 类型选择提取方式（`web_extract` 或 `fetch_transcript`）
2. 写入临时文件 `/tmp/atn_raw.md`（frontmatter）+ `/tmp/atn_body.md`（正文）
3. `atn_write.py` 读取临时文件，通过 Notion API 写入数据库
4. body 必须 **原文直出**，严禁 LLM 总结；body ≥ 1000 字符才算成功

## 数据库配置

| 项目 | 值 |
|------|-----|
| Notion Database | **AtN Inbox** |
| DB ID | `35547eb5-fd3c-81db-bff3-c50275484e33` |
| Notion Integration | Hermes Analysis Issue Report |
| Schema | Name (title), Rating (select), Source (url), Date Captured (date) |

> ⚠️ **关键教训（2026-06-12）**：DB ID 曾被误改为 `2e047eb5...`（指向"Other Links"数据库），导致文章写入错误位置。于 2026-06-13 修正回 `35547eb5...`。修改 DB ID 时必须双端确认（AGENTS.md + 代码硬编码）。

## 关联 Skill

- **youtube-content** — 嵌入 AtN 管道，负责 YouTube 字幕/转录抓取（Level 1 oembed → Level 2 proxies → Level 3 faster-whisper）

## 文件结构

```
/tmp/atn-docker/
├── AGENTS.md              # 项目入口文档
├── context-log.md         # 上下文快照日志（每晚 cron 更新）
├── lessons.md             # 经验教训
├── todo.md                # 待办事项
├── scripts/
│   ├── atn_write.py       # Notion 写入脚本
│   └── check_env.py       # 环境检查脚本
└── cron/
    └── context-compression.json  # 上下文压缩 cron 配置
```

## 每晚 Cron

- 时间：每天 02:00
- 作用：压缩 Telegram HermesGroup 各 topic 的上下文到 `docs/context-log.md`
- 确保 agent 不会丢失关键的 Notion 数据库信息

## 注意事项

- body 严禁 LLM 总结，必须原文直出
- body 字符数 ≥ 1000 才算成功提取；< 1000 需用 browser_console 补充
- 所有 AtN 文章都写入 **AtN Inbox** 数据库，不要写到 Other Links 或其他地方
- 本知识包**不包含**真实 Notion token 或 API key
