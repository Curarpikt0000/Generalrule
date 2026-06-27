---
title: Hermes 多 Profile 运维与重启（multi_watchdog + token 锁 + 活着≠在干活）
domain: agent-rules
type: concept
keywords: [hermes, 多profile, multi-profile, multi_watchdog, profiles.conf, token锁, gateway-locks, 重启, 共享代理, 8800, alive-not-working]
tags: [hermes, gateway, watchdog, multi-profile, uptime, restart]
source: Hermes 实测沉淀（chaojin-hermeschao Uber-vm，2026-06-27 一次性修复 3 个 Uber profile）
sources: [conversation-2026-06-27]
created: 2026-06-27
updated: 2026-06-27
last_updated: 2026-06-27
applies_to: hermes
---

# Hermes 多 Profile 运维与重启（仅 Hermes）

> **适用范围**：只对 Hermes 适用（gateway 常驻服务是 Hermes 独有）。单 profile 的 watchdog 基础见 [[hermes-gateway-watchdog]]，本页讲**多 profile 并存**时新增的坑。

## 一、架构事实（这台 Uber VM）

同一台 VM 跑 **4 个独立 gateway profile**，各自独立 **Telegram bot token / `state.db` / 日志目录**，但**共用**一个 LLM 代理 `localhost:8800`（→ cerberus 5436 → Uber GenAI，见 [[hermes-genai-api-integration]]）：

| profile | HERMES_HOME | 重启方式 |
|---|---|---|
| `default` | `~/.hermes` | `~/.hermes/scripts/clean_gateway_restart.sh` |
| `u-dara` | `~/.hermes/profiles/u-dara` | multi_watchdog 拉起（见下） |
| `u-financer` | `~/.hermes/profiles/u-financer` | 同上 |
| `u-consultant` | `~/.hermes/profiles/u-consultant` | 同上 |

各 profile config：`model.default=claude-opus-4-8`、`base_url=http://localhost:8800/v1`、`fallback_providers=deepseek`。
**关键推论**：8800 是单点共享——它一挂（隧道漂移 `502 [Errno 99]`），**4 个 profile 同时失去 LLM**。修隧道见 [[hermes-genai-api-integration]]。

**保活**：`~/.hermes/scripts/gateway_multi_watchdog.sh`（system cron，每几分钟）按 `~/.hermes/scripts/profiles.conf`（`<name>:<HERMES_HOME>` 每行一个）逐个检查，down 就 `setsid env -i HERMES_HOME=<home> ... hermes gateway run` 拉起。

## 二、最大陷阱：「活着」≠「在干活」

`multi_watchdog.log` 里的 `OK <name> alive` 只是**进程级 ping**（`/proc` 里有匹配 HERMES_HOME 的 `hermes gateway` 进程就算 alive）。它**不**代表这个 profile 还能正常处理对话。

2026-06-27 实例：3 个 Uber profile 全部 `OK alive`，但自上次重启（6/25 07:00）起**一次成功 LLM 调用都没有**——进程在、Telegram 在轮询、但实质空转。

**真健康检查**（务必看这个，别信 multi_watchdog 的 alive）：
```bash
# 该 profile 最近有没有真的调用过 LLM？
grep "API call #" ~/.hermes/profiles/<name>/logs/agent.log | tail -1
# 看时间戳：是分钟/小时级=在服务；是几天前=实质空转或没人用
```

**附带教训——profile 不热更新代码**：所有 profile 共用同一份 `~/.hermes/hermes-agent/` 代码，但**已运行的进程不会自动加载新改动**。给 hermes-agent 打了补丁（如 [[tool-call-emitted-as-text]] 的本地补丁）后，**必须逐个重启每个 profile** 才生效。本次 3 个 Uber profile 一直跑 6/25 旧代码、没吃到 antml/`call:` 补丁，就是漏了重启。

## 三、重启多 profile 的坑（2026-06-27 实测翻车两次才成）

### 1. token-scoped 锁不在 HERMES_HOME 下
Telegram token 锁在 **`~/.local/state/hermes/gateway-locks/telegram-bot-token-<hash>.lock`**（XDG_STATE_HOME 下，全机共享一个目录，**不**在各 profile 的 HERMES_HOME 里）。文件内容记 `pid` + `start_time` + token 的 `identity_hash`。
- 删 `HERMES_HOME/gateway.lock` / `gateway.pid` **不够**——真正卡你的是上面这个 token 锁。
- 症状：新实例报 `Gateway exiting cleanly: telegram: Telegram bot token already in use (PID <old>). Stop the other gateway first.` 后当场退出。

### 2. multi_watchdog cron 会和你的手动重启抢
你刚 `kill` 掉某 profile，cron watchdog（每几分钟）也检测到它 down → **并行拉起一个**。于是你的实例和 watchdog 的实例**抢同一个 token** → 双双报 token 冲突退出。`gateway.out` 里出现**两次 "Gateway Starting" 横幅**就是这个症状。
- 好消息：watchdog 是 **token-conflict-aware** 的（grep `gateway.out` 末 5 行有 `bot token already in use` 就**不再抢**、只报一次让路）。所以撞一次后它会退出竞争，你第二次重启就能成。

### 3. 正确重启手法（逐个，验证驱动）
```bash
SSH_SOCK=/var/lib/devpod/ssh/active_ssh_auth_sock
HERMES_BIN=/home/user/.hermes/hermes-agent/venv/bin/hermes

# (a) 精确按 HERMES_HOME 找进程并 kill（别按名字模糊杀）
for p in $(pgrep -f "venv/bin/python.*hermes gateway"); do
  eh=$(tr '\0' '\n' < /proc/$p/environ | sed -n 's/^HERMES_HOME=//p'); [ -z "$eh" ] && eh=/home/user/.hermes
  [ "$eh" = "$HOME_TARGET" ] && kill "$p"
done
# (b) 等旧进程优雅退出（它会自己清 token 锁）；确认 dead：kill -0 <oldpid> 报错=已死
# (c) 用 watchdog 同款命令逐个起，起一个 verify 一个：
setsid env -i HOME=/home/user USER=chao.jin \
  PATH=/home/user/.hermes/hermes-agent/venv/bin:/usr/local/bin:/usr/bin:/bin \
  TZ=Asia/Tokyo HERMES_HOME="$HOME_TARGET" SSH_AUTH_SOCK="$SSH_SOCK" \
  bash -c "'$HERMES_BIN' gateway run >> '$HOME_TARGET/logs/gateway.out' 2>&1" </dev/null >/dev/null 2>&1 &
disown
```
- profile 只连 8800，**不需要自己的 SSH/cerberus**（SSH_AUTH_SOCK 给上无妨）。
- 若 token 锁是陈旧的（记的 pid 已 dead），可直接删 `~/.local/state/hermes/gateway-locks/telegram-bot-token-<hash>.lock` 再起。

### 4. 验证（两道都要过）
```bash
hermes gateway list                       # 4 个全 ✓ + 新 PID
tail -5 ~/.hermes/profiles/<name>/logs/gateway.log
#   预期: "Gateway running with 1 platform(s)" + "Cron ticker started"
curl -sf http://localhost:8800/v1/models >/dev/null && echo 8800-OK   # 共享 LLM 代理
```

## 四、排错速查

| 现象 | 真因 | 处置 |
|---|---|---|
| 某 profile「不回消息/不正常」 | 多半进程在但实质空转 / 跑旧代码 / 8800 挂过 | 看 §二真健康检查；重启上当前代码 |
| 4 个 profile **同时**失语 | 共享 8800 / 5436 隧道挂（`502 [Errno 99]`） | 修隧道见 [[hermes-genai-api-integration]] |
| 重启后 profile 起不来，报 `token already in use (PID <old>)` | 陈旧 token 锁 或 watchdog 抢重启 | §三：清锁 / 撞一次让 watchdog 退竞争后再起 |
| `gateway.out` 出现两次 "Gateway Starting" | 你和 watchdog 并行拉起撞 token | 等一轮、逐个重起 |
| `multi_watchdog.log` 全是 `OK alive` 但用户说坏了 | alive 只是进程 ping，非真健康 | 别信，查 agent.log 最近 `API call #` |
| Telegram `httpx.ReadError` 反复重连 | 正常网络抖动（每次都 `polling resumed`） | 无害，忽略 |

## 相关页面

- [[hermes-gateway-watchdog]] —— 单 profile gateway watchdog 基础（run/restart cmdline 匹配坑）
- [[hermes-genai-api-integration]] —— 共享 8800 代理 + cerberus 5436 隧道 + `502 [Errno 99]` 修复
- [[hermes-profile-filesystem-discipline]] —— 各 profile 写文件的工作区纪律
- [[tool-call-emitted-as-text]] —— antml/`call:` 工具调用泄漏为正文（profile 重启才能吃到补丁）
- [[agent-config-matrix]] —— 各 agent 配置矩阵（gateway 是 Hermes 独有项）
