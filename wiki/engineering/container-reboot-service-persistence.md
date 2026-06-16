---
title: 容器重启后服务恢复与开机持久化（临时 /etc 陷阱）
domain: engineering
type: concept
keywords: [容器, 重启, 临时文件系统, ephemeral, /etc, 开机自启, boot, 幂等, setsid, watchdog, 循环依赖, 调用链排障, init, dinit]
tags: [container, reboot, ephemeral-fs, boot-persistence, idempotent, watchdog, debugging]
source: 一次容器化开发环境内 AI agent 模型链路意外停机的复盘（已匿名化/通用化）
sources: [conversation-2026-06-16]
created: 2026-06-16
updated: 2026-06-16
last_updated: 2026-06-16
---

# 容器重启后服务恢复与开机持久化（临时 /etc 陷阱）

> 在容器化开发环境里跑常驻服务（代理、隧道、消息 gateway 等）时遵守本页。
> 任何「需要跨容器重启存活」的初始化/服务定义，**别只写进 `/etc`**——那通常是临时文件系统，重启即丢。
> 本页用一次真实事故做匿名引子，提炼成通用工程教训；不含任何特定公司/内部系统细节。

---

## 背景架构（通用化）

某容器化开发环境里跑着一个 AI agent（CLI + 一个常驻的 messaging gateway，监听 Telegram/Discord 之类的消息平台）。它访问大模型的链路是一条多跳代理链：

```
agent → 本地代理(监听 :8800) → 本地隧道(监听 :5436, 经认证连到内部模型网关) → 后端大模型 API
```

本地代理、隧道、gateway 三个常驻进程，由容器的 init 系统（无 systemd，用 dinit 之类）在开机时作为服务拉起。

> 说明：端口号、「本地代理监听某端口转发到后端隧道」这种**本机通用架构模式**是可保留的工程细节；而「内部模型网关」「认证代理」只做抽象描述，不点名具体内部服务。

---

## 症状

- agent 调用模型全部报 `APIConnectionError / Connection error`（指向本地 `:8800`）。
- messaging gateway 收不到任何回复（用户侧表现为「机器人没反应」）。
- 重试 3 次后彻底失败。

---

## 排查方法论：沿调用链逐跳验证（这套方法本身就是要沉淀的通用知识）

整条链路是「agent → 代理 → 隧道 → 后端」。排障就**沿链逐跳往下验证，定位第一个断点**：

1. **查端口监听**：`ss -ltnp | grep -E ':8800|:5436'` —— 发现 `:8800` 和 `:5436` **都没有进程监听**，`curl localhost:8800` 直接 connection refused。整条代理链是断的。
2. **查进程树**：`pgrep -af '代理|隧道|gateway 特征'` —— 代理、隧道、gateway 三个进程**都不在了**。
3. **查日志**：代理日志最后写入时间**停在容器重启前一刻** —— 强烈暗示「重启后就没再起来过」。
4. **查 init 服务定义**：负责开机拉起代理的 init 服务定义文件（如 dinit 的 service 文件）**已经不存在了**。
5. **关键认知**：容器的 `/etc`（含 init/服务定义）是**临时文件系统**，容器重启/重建时被重置——之前**手动创建在 `/etc` 里的服务定义全部丢失**。
6. **顺带发现一个自愈缺陷**：原有的「代理 watchdog」是一个**需要调用大模型才能运行的 agent 任务**——而大模型链路恰恰是它要修复的对象，构成**循环依赖**：模型一断，watchdog 自己也跑不起来，救不回来。

> **方法论要点**：把错误信息当 oracle 反推配置。`:8800` connection refused → 不是模型 API 的问题，而是**第一跳**就没人监听 → 顺着往后逐跳排除，最终落到「开机拉起它的东西没了」。逐跳验证的顺序是：**端口监听 → 进程 → 日志 → 服务定义 → 平台持久化层**。

---

## 根因

```
容器重启
  → 临时 /etc 被重置
  → 开机自动拉起代理的 init 服务定义丢失
  → 重启后没有任何东西恢复代理/隧道/gateway
  → 整条模型链路全断
自愈 watchdog 又因「修模型却要先调模型」的循环依赖而失效，无法兜底。
```

一句话：**把跨重启才有意义的服务定义放进了重启就清空的目录。**

---

## 解决方案

### 1. 立即恢复（救火）

用**持久化在 home 目录**里的启动脚本重新拉起隧道 + 代理 + gateway。两个关键坑：

- **认证用的 agent socket 环境变量必须显式设置**（如 `SSH_AUTH_SOCK` 指向真实的 ssh-agent socket），否则隧道认证失败、连不上后端。后台脚本不继承交互 shell 的环境，必须自己导出。
- **后台进程要用 `setsid` 脱离当前 shell 会话**启动，否则它们会随父命令的进程组一起被回收——你以为起好了，命令一返回就被一锅端。

```bash
# 显式导出认证 socket（按本机实际路径）
export SSH_AUTH_SOCK="$(ls -t /tmp/ssh-*/agent.* 2>/dev/null | head -1)"
# setsid 脱离会话，nohup + 重定向，确保命令返回后进程仍存活
setsid nohup ~/bin/start-tunnel.sh  >>~/logs/tunnel.out  2>&1 &
setsid nohup ~/bin/start-proxy.sh   >>~/logs/proxy.out   2>&1 &
setsid nohup ~/bin/start-gateway.sh >>~/logs/gateway.out 2>&1 &
```

### 2. 持久化（真正的修复）

**不要把恢复逻辑放回临时的 `/etc`**，而是放进**平台提供的、跨重启持久的开机自定义机制**——例如：

- 平台的 boot 钩子 / boot playbook（home 目录里的一个配置文件，平台在每次容器 create/restart 时执行它）；
- 或 cloud-init / 启动脚本；
- 或挂载到持久化卷里的初始化脚本 + `@reboot` crontab 兜底。

要点：**开机脚本必须幂等**。

```bash
#!/usr/bin/env bash
# boot 脚本：幂等 + 先等依赖就绪再启动，规避开机时序竞争
set -u

# (a) 先等认证 socket 就绪（boot 时各组件起来有先后，硬等会竞争失败）
for i in $(seq 1 30); do
  [ -S "${SSH_AUTH_SOCK:-/nonexistent}" ] && break
  sleep 1
done

# (b) 幂等：已健康就跳过，只拉起挂掉的
ensure() {  # ensure <name> <port> <start-cmd>
  if ss -ltn "( sport = :$2 )" | grep -q ":$2"; then
    echo "OK $1 already listening on :$2"; return
  fi
  echo "DOWN $1 -> starting"; setsid nohup bash -c "$3" >>~/logs/$1.out 2>&1 &
}

ensure tunnel  5436 "~/bin/start-tunnel.sh"
ensure proxy   8800 "~/bin/start-proxy.sh"
ensure gateway 0    "~/bin/start-gateway.sh"   # 无监听端口的用 pgrep 判活
```

把该脚本**登记进平台的 boot 配置**，使其在每次容器重启时自动执行。这样重启后链路自动恢复，不再依赖任何写在 `/etc` 里、会被清空的东西。

### 3. 修掉循环依赖

监控/自愈逻辑必须用**纯脚本（不依赖被监控的服务本身）**实现：

- watchdog 用 `ss`/`pgrep` 探活 + shell 直接拉起，**全程不调用大模型**。
- 绝不让 watchdog 依赖它要修复的东西（「修模型链路的任务自己要先调模型」是反例）。
- 调度上让它走「零 token / 不唤醒 agent」的纯脚本路径（如 cron 的纯脚本任务），健康时静默、异常时才出声。

---

## 要提炼的通用教训（核心）

1. **容器里 `/etc` 等系统目录通常是临时的**。任何需要跨重启存活的初始化/服务定义，必须放在**持久化卷**或**平台的持久 boot 自定义机制**里，而**不是直接改 `/etc`**。改了 `/etc` 就等于「重启即蒸发」。
2. **开机/恢复脚本要写成幂等**，并**显式等待依赖就绪**（处理 boot 时序竞争）：已健康就跳过、只拉挂掉的；依赖（如认证 socket）没就绪就轮询等待，别硬启。
3. **后台常驻进程要用 `setsid`/完全脱离会话启动**，避免随父进程组被回收。配 `nohup` + 日志重定向。
4. **watchdog/自愈机制绝不能对它要修复的服务有循环依赖**。自愈逻辑要用最底层、最少依赖的手段（纯脚本 + 系统命令）实现，确保「被监控对象全挂」时它自己还能跑。
5. **排障方法论：沿调用链逐跳验证**——`端口监听 → 进程 → 日志 → 服务定义 → 平台持久化层`，用错误信息当 oracle 反推（如「第一跳 connection refused」直接排除「后端 API 故障」假设）。

---

## 来源

一次容器化开发环境内 AI agent 模型链路意外停机的事故复盘（2026-06-16，已匿名化/通用化，剥离全部内部基础设施细节）。

## 相关页面

- [[hermes-gateway-watchdog]] —— 进程级 watchdog（崩溃自愈）的具体实现与踩坑；其「局限」一节正对应本页的「整台容器被重建/重启」场景
- [[gcp-cloud-run-deployment]] —— 另一类「线上与本地状态漂移导致静默停摆」的部署陷阱
- general-global-rule.md §7 —— 安全与禁区（不可逆操作、密钥禁区）
