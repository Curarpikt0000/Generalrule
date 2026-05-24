---
title: 前端富文本渲染管道
domain: agent-rules
keywords: [前端, markdown, 渲染, 剪贴板, clipboard, marked.js, html, blob]
source: 原 general-global-rule.md §4.9（2026-05-24 迁移至 Wiki），L-2026-04-24-003
created: 2026-05-24
last_updated: 2026-05-24
---

# 前端富文本渲染管道

> 有前端的项目必须遵守。涉及把 LLM 输出展示到网页、或写入剪贴板时，先读本页。
> 纯后端 / 无前端任务可跳过。

---

## 核心规则

- 严禁将 LLM 返回的 Markdown 原生字符串**裸露**给前端渲染或剪贴板操作。
- 必须通过 `marked.js` 等库解析为标准 HTML 后再渲染。
- 剪贴板写入必须使用 `Clipboard API (text/html)` + Blob 对象，并提供纯文本降级兜底。

*因为 LLM 返回的是 Markdown 源码（带 `#`、`*`、`-` 等符号），直接塞进 DOM 或剪贴板，用户看到的是一堆原始符号而非渲染后的富文本。*

---

## 正确做法

1. **渲染到页面**：先用 `marked.js`（或同类库）把 Markdown 解析成 HTML，再插入 DOM。
2. **写入剪贴板**：用 `Clipboard API` 的 `text/html` 类型 + Blob 对象写富文本；同时提供 `text/plain` 纯文本作为降级兜底，保证粘贴到不支持富文本的地方也能用。

---

## 来源

L-2026-04-24-003（原 general rule §4.9）

## 相关页面

- general-global-rule.md §2.10 显式失败（渲染失败要明说，不要静默吞掉）
