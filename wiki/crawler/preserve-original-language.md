---
title: 爬虫数据采集保持原文语言
domain: crawler
keywords: [transcript, language, data-integrity, crawl, 原文]
source_lesson: L-2026-05-04-004
created: 2026-05-04
---

# 爬虫数据采集保持原文语言

## 核心规则
采集到的内容必须保持原始语言，禁止自动翻译。

## 错误行为
自动将英文 transcript 翻译成中文后存储。

## 正确做法
- 保留原文，语言字段记录原始语言
- 如需翻译，作为单独字段存储，不覆盖原文
- 用户明确要求翻译时才执行

## 适用场景
- YouTube transcript 采集
- 网页内容爬取
- 任何外部数据采集管道
