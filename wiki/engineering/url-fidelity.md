---
title: 严格使用用户提供的 URL
domain: engineering
keywords: [url, user-intent, exact-url, no-substitution]
source_lesson: L-2026-05-04-006
created: 2026-05-04
---

# 严格使用用户提供的 URL

## 核心规则
必须严格使用用户提供的原始 URL，禁止自作主张替换或修改。

## 错误行为
- 把用户给的 URL 替换成"更好的"版本
- 自动去掉 URL 参数
- 用搜索结果替换用户给的链接

## 正确做法
用户给什么 URL 就用什么 URL，不做任何修改。

## 适用场景
- 所有涉及 URL 的任务
- 内容抓取、API 调用、页面访问
