---
title: RTK 使用规范（CLI Token 优化，三 Agent 通用）
domain: agent-rules
type: concept
keywords: [rtk, token, cli, terminal, 优化, 代理, rust-token-killer]
tags: [rtk, token-optimization, cli, terminal]
source: 整合 engineering/rtk-rust-token-killer.md + ~/.claude/RTK.md + rtk --help（2026-05-24）
sources: [user-approval-2026-05-22, rtk-help-output]
created: 2026-05-24
updated: 2026-05-24
last_updated: 2026-05-24
---

# RTK 使用规范（CLI Token 优化）

> RTK (Rust Token Killer) 是 CLI 代理，压缩终端输出，省 60-90% token。
> 跑终端命令时，**优先用 rtk 代理形式**，减少上下文消耗。三个 Agent 通用。
> 系统级命令：`/opt/homebrew/bin/rtk`（已装 v0.40.0）。

---

## 三个 Agent 的用法差异（重要）

- **Claude Code**：已装 hook，自动把 `git status` 改写成 `rtk git status`，**透明、0 token 开销，无需主动打 rtk**。配置见 `~/.claude/RTK.md`。
- **Hermes / Antigravity**：无 hook，需**主动**用 rtk 代理形式（按下方命令表）。

---

## 完整命令表（rtk <command>）

| rtk 命令 | 作用 | 替代的原始命令 |
|---|---|---|
| `rtk ls` | 列目录，token 优化输出 | `ls` |
| `rtk tree` | 目录树，token 优化 | `tree` |
| `rtk read <file>` | 读文件，智能过滤 | `cat file` |
| `rtk smart <cmd>` | 生成 2 行技术摘要（启发式） | — |
| `rtk git ...` | git 命令，紧凑输出 | `git ...` |
| `rtk gh ...` | GitHub CLI，token 优化 | `gh ...` |
| `rtk glab ...` | GitLab CLI，token 优化 | `glab ...` |
| `rtk aws ...` | AWS CLI，紧凑（强制 JSON、压缩） | `aws ...` |
| `rtk psql ...` | PostgreSQL，紧凑（去边框、压缩表格） | `psql ...` |
| `rtk pnpm ...` | pnpm，超紧凑输出 | `pnpm ...` |
| `rtk err <cmd>` | 只显示错误/警告 | — |
| `rtk test <cmd>` | 跑测试，只显示失败 | — |
| `rtk json <file>` | 显示 JSON（默认压缩值，`--keys-only` 只看键） | — |
| `rtk deps` | 汇总项目依赖 | — |
| `rtk env` | 环境变量（过滤、敏感信息脱敏） | `env` |
| `rtk find ...` | 查文件，紧凑树输出（支持 -name/-type 等原生 flag） | `find ...` |
| `rtk diff ...` | 超精简 diff（只显示改动行） | `diff ...` |
| `rtk log <cmd>` | 过滤、去重日志 | — |
| `rtk dotnet ...` | .NET 命令，紧凑（build/test/restore/format） | `dotnet ...` |
| `rtk docker ...` | Docker，紧凑输出 | `docker ...` |
| `rtk kubectl ...` | Kubectl，紧凑输出 | `kubectl ...` |
| `rtk summary <cmd>` | 跑命令并显示启发式摘要 | — |
| `rtk grep ...` | 紧凑 grep（去空白、截断、按文件分组） | `grep ...` |
| `rtk wget <url>` | 下载，紧凑（去进度条） | `wget ...` |
| `rtk curl <url>` | curl，紧凑输出 | `curl ...` |

## Meta 命令（始终直接用 rtk，不递归套用）

| 命令 | 作用 |
|---|---|
| `rtk gain` | 显示 token 节省分析 |
| `rtk gain --history` | 命令使用历史 + 节省量 |
| `rtk discover` | 分析历史，找漏用 rtk 的机会 |
| `rtk proxy <cmd>` | 执行原始命令不过滤（调试用） |
| `rtk --version` | 版本验证 |
| `rtk init -g` | 安装全局 ZSH hook + 生成 RTK.md |

---

## 铁律

1. **rtk 自身命令不递归**：`rtk init`、`rtk gain`、`rtk --version` 等不要写成 `rtk rtk ...`。
2. **需要原始完整输出时**：用 `rtk proxy <cmd>` 绕过过滤（调试、或下游脚本依赖原始格式时）。
3. **名称冲突警告**：若 `rtk gain` 报错，可能装错成了 `reachingforthejack/rtk`（Rust Type Kit）。用 `which rtk` 确认。

---

## 配置文件位置

- Claude Code hook + 说明：`~/.claude/RTK.md`
- 全局过滤配置：`~/Library/Application Support/rtk/filters.toml`

---

## 相关页面

- [[skill-register]] —— RTK 登记为 B 类系统级共享工具
- general-global-rule.md §8 指针索引
