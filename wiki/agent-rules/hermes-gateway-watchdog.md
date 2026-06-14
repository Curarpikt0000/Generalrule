---
title: Hermes Gateway 24/7 Watchdog（cron 自动拉起，仅 Hermes）
domain: agent-rules
type: concept
keywords: [hermes, gateway, watchdog, cron, 24/7, 自动重启, 守护进程, no-systemd, dinit]
tags: [hermes, gateway, watchdog, cron, uptime]
source: Hermes 实测沉淀（chaojin-hermeschao Uber-vm，2026-06-14/15）
sources: [conversation-2026-06-15]
created: 2026-06-15
updated: 2026-06-15
last_updated: 2026-06-15
applies_to: hermes
---

# Hermes Gateway 24/7 Watchdog（仅 Hermes）

> **适用范围（重要）**：本页**只对 Hermes 适用**。只有 Hermes 有 `gateway` 这个常驻服务进程（监听 Telegram/Discord 等并唤醒 agent）。Claude Code / Codex / Antigravity / Cursor **没有 gateway 概念**，不要把本机制套用到它们身上。

## 一、要解决什么

让 Hermes gateway 在**无 systemd 的主机**（如 Uber DevPod 容器用 dinit）上 24/7 不间断：进程被杀/崩溃时自动拉起。无守护进程时，gateway 不会自愈。

**关键认知**：AI 大脑不是常驻进程；真正 24/7 的是 **gateway 服务**——它一直挂在消息平台监听，有消息时才唤醒 agent 处理一次。"让 Hermes 不停工作" = "保持 gateway 进程存活"。

## 二、先诊断

```bash
# 真正的 gateway 主进程（注意要同时匹配 run 和 restart，见踩坑）
pgrep -af "venv/bin/python.*hermes gateway"
# 重启/崩溃历史：
tail -40 ~/.hermes/logs/gateway-exit-diag.log   # gateway.start / exit_clean / exit_nonzero
tail -40 ~/.hermes/logs/errors.log              # "Another gateway instance" / "token already in use"
dmesg -T 2>/dev/null | grep -i -E "oom|killed"  # OOM（通常为空=无 OOM）
```

## 三、核心踩坑（本机制最容易翻车的地方）

### 1. 必须同时匹配 `gateway run` 和 `gateway restart`
gateway 若用 `hermes gateway restart` 启动，其进程命令行里永远是 `hermes gateway **restart**`，而不是 `run`。watchdog 若只 grep `"gateway run"`：
- **看不见这个 gateway** → 误判"掉线"（false-DOWN）
- → 试图启新实例 → 新实例发现 token 被占用，报 `Telegram bot token already in use (PID …)` 后退出
- → watchdog 每个 tick 都报 `FAILED restart`，**无限空转，而真 gateway 其实一直活得好好的**

**正解**：遍历 `/proc/$p/cmdline`，匹配 `run` 或 `restart` 两种动词。

### 2. `gateway.pid` 文件会变陈旧
多次重启后，`~/.hermes/gateway.pid` 记的 PID 可能和实际持有 token 的进程**不一致**。别把它当唯一真相源，要对照活进程列表验证。

### 3. 排除 shell 包装进程
agent 终端工具执行命令时会派生 `bash -c ... <含该字符串的命令> ...`，也会被 `pgrep -f` 匹配，虚增进程数。**只认 cmdline 含 `venv/bin/python` 的进程**，过滤裸 shell 包装。

### 4. Hermes 禁止 gateway 自重启
从 gateway 进程内部（即 agent 自己）跑 `hermes gateway restart` 会被拒绝（防循环）。重启必须从 gateway 外部的 shell 发起；让 watchdog 用 `nohup ... gateway run &` 拉起。

## 四、watchdog 脚本要点

`~/.hermes/scripts/gateway_watchdog.sh`（核心逻辑）：
- `find_gateway()`：遍历 `pgrep -f "venv/bin/python.*hermes gateway"`，对每个 PID 读 `/proc/$p/cmdline`，case 匹配含 `python` + (`hermes gateway run` 或 `hermes gateway restart`)。
- 存活 → 仅写日志、stdout 为空（静默，不打扰）。
- 不存活 → `rm -f gateway.lock gateway.pid`（仅在确认无活进程后才安全）→ `nohup hermes gateway run >> gateway.out 2>&1 &` → sleep 5 → 用 `find_gateway` 复检，成功/失败都 echo 到 stdout（让 no_agent cron 通知用户）。

## 五、cron 配置（no_agent = 零 token）

```
cronjob(action=create, name="Gateway Watchdog",
        schedule="*/30 * * * *",        # 每 30 分钟
        script="gateway_watchdog.sh",   # 相对 ~/.hermes/scripts/
        no_agent=true,                  # 纯脚本，不走 LLM，不耗 token
        deliver="origin")
```
`no_agent=true` 语义：stdout 为空 = 静默（健康时不刷屏）；stdout 非空 = 原样发给用户（仅重启/失败时出声）。

## 六、验证

1. `chmod +x` 后手动跑一次 → 预期 `~/.hermes/logs/watchdog.log` 出现 `OK gateway alive (pid=…)`，无 stdout。
2. `cronjob(action=run, job_id=…)`，等 ~25s，确认新 `OK` 行 + `last_status: ok`。
3. 改过匹配逻辑后，务必确认能认出**当前实际**的 gateway（无论它是 run 还是 restart 启的）。

## 七、局限

watchdog 只解决"进程被杀/崩溃 → 自愈"。**整台容器被重建/重启**时 cron 和 gateway 都会停（无 systemd 开机自启）。这种情况需在主机恢复后手动起一次 gateway（或配 dinit 服务 / crontab @reboot 作开机兜底），之后 watchdog 接管。

## 相关页面

- [[hermes-genai-api-integration]] —— Hermes 接 Uber GenAI API + dinit/crontab 24/7 持久化（另一条 24/7 路径）
- [[hermes-profile-filesystem-discipline]] —— Hermes profile 文件纪律
- [[agent-config-matrix]] —— 各 agent 配置矩阵（gateway 是 Hermes 独有项）
