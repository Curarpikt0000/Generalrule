---
title: RTK (Rust Token Killer) — CLI Token 优化代理
domain: engineering
keywords: [rtk, token-optimization, cli, terminal, proxy]
source: user approval 2026-05-22
created: 2026-05-22
last_updated: 2026-05-22
---

# RTK (Rust Token Killer)

## 概述

RTK 是一个 Rust 编写的 CLI 代理工具，用于压缩终端命令输出，减少 LLM 上下文 token 消耗（声称 60-90% 节省）。

## 安装

```bash
brew install rtk       # macOS
rtk --version          # 验证
```

## 初始化

```bash
rtk init -g            # 安装全局 ZSH hook + 生成 RTK.md
```

## Hermes Agent 使用规则

所有 terminal 命令优先用 `rtk` 代理形式：

| 原始命令 | 替代形式 |
|---|---|
| `ls` | `rtk ls` |
| `cat file` | `rtk read file` |
| `curl url` | `rtk curl url` |
| `git ...` | `rtk git ...` |
| `grep ...` | `rtk grep ...` |

**例外**：`rtk` 自身命令不加递归（`rtk init`、`rtk gain`、`rtk --version` 等）。

## 相关文件

- 全局规则：`general-global-rule.md §12`
- Claude RTK.md：`~/.claude/RTK.md`
- 全局过滤配置：`~/Library/Application Support/rtk/filters.toml`
