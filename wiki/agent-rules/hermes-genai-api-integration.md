---
title: Hermes 接 Uber 内部 GenAI API（Claude Opus 4 / GPT-5.5）+ DevPod 24/7 持久化
domain: agent-rules
type: concept
keywords: [hermes, genai-api, cerberus, claude-opus-4, gpt-5.5, devpod, dinit, ssh-auth-sock, proxy, 24-7, persistence, frontier-model, port-drift, idle-disconnect, tunnel-watchdog, telegram-alert, auth-escalation, errno-99]
tags: [hermes-integration, genai-api, uber-internal, cerberus, dinit, persistence, model-config, watchdog]
source: Cowork 协作会话 2026-06-12（GenAI API 接入排障 + dinit 持久化实装）；2026-06-17 补隧道 watchdog + 端口漂移踩坑
sources:
  - ~/.hermes/scripts/genai_proxy.py（proxy v2 实装稿）
  - /etc/dinit.d/genai-proxy（dinit 服务定义）
  - ~/.hermes/scripts/genai_tunnel_watchdog.sh（隧道 watchdog，2026-06-17）
created: 2026-06-12
updated: 2026-06-17
last_updated: 2026-06-17
machine: UB
---

# Hermes 接 Uber 内部 GenAI API + DevPod 24/7 持久化

> 让运行在 **Uber DevPod 虚拟机** 上的 Hermes 用上前沿模型（Claude Opus 4 系列 / GPT-5.5），
> 走 Uber 内部 GenAI Gateway，而非外部 API。
> 设计原则：**Cerberus 隧道 + 本地 proxy 注入 RPC header**，dinit + crontab 双保险做 24/7 持久化。
> 凭证纪律：**所有 X.509 cert / ussh 凭证由 ussh 工具自动签发，绝不手抄进 wiki / .env / 代码**。

---

## 一、整体架构

```
[Uber DevPod VM: chaojin-hermeschao]
    │
    ├── Cerberus 隧道 (cerberus -s genai-api)
    │       │  需要 SSH_AUTH_SOCK 认证到 bastion.uberinternal.com
    │       └── 监听 localhost:5436 → 内部 genai-api 服务
    │
    ├── GenAI Proxy (genai_proxy.py v2, port 8800)
    │       │  注入 RPC header (rpc-service / rpc-caller)
    │       │  429 自动重试 3 次 (2s/4s backoff)
    │       └── 转发 localhost:8800 → localhost:5436
    │
    └── Hermes (model.provider=custom, base_url=http://localhost:8800/v1)
            └── default model: claude-opus-4-8 / gpt-5.5
                fallback: deepseek-v4-flash (外部 API 兜底)
```

请求链路：`Hermes → :8800 proxy → :5436 cerberus → Uber genai-api`

---

## 一·补、两种接入方式对比（重要！）

接 Uber GenAI API 有**两条路**，本质都是「OpenAI 兼容客户端 → 内部 GenAI Gateway」，
区别在**认证方式**与**连接路径**。我们当前用的是 **A（Cerberus 隧道）**，
Uber 工程师建议的是 **B（USSO token 直连）**。

| 维度 | **A. Cerberus 隧道（当前在用）** | **B. USSO token 直连（工程师建议）** |
|---|---|---|
| Base URL | `http://localhost:8800/v1`（本地 proxy）→ Cerberus → `genai-api` | `https://genai-api.uberinternal.com/v1`（直连内部域名） |
| 认证 | **Cerberus 证书**（`generate-cerberus-cert` + ussh cert，devpod 自动维护） | **USSO token** 当 `Authorization: Bearer` |
| 计费 header | `rpc-caller: chao.jin` + `rpc-service: genai-api`（proxy 注入） | `rpc-caller` + **`OpenAI-Organization: <uOwn 项目 UUID>`** |
| 需要 uOwn UUID | **不需要**（证书身份，计费归 ldap） | **需要**（go/maa 注册的 uOwn / MA Studio 项目 UUID） |
| token 过期 | Cerberus cert 自动续期（无 401 困扰） | USSO token 约 **30 分钟过期**，长跑 agent 必须**每请求重取** |
| 合规定位 | ⚠️ Cerberus 自带警告「LOCAL DEBUGGING ONLY，不可用于 automation/scripts/cron」 | ✅ 生产级官方推荐路径 |

### 为什么当前 A 方式不需要 UUID 也能跑通

A 走的是**证书隧道**，身份由 ussh/cerberus cert 承载，计费靠 `rpc-caller: chao.jin`
归到个人 ldap —— 所以**不需要 uOwn 项目 UUID**。这也是为什么没填 UUID 也能成功。

### 长期建议（何时切到 B）

A 现在稳定、零额外配置，**短期不用改**。但两个长期风险值得注意：

1. **计费合规**：A 计费归个人 ldap，若 Uber 要求 GenAI 用量必须挂到注册的 uOwn 项目
   （成本中心），将来可能被风控拦。
2. **Cerberus 非生产用途**：启动时自带警告，我们的长跑 agent + cron 技术上算 automation，
   若 service owner 收紧 Charter policy，隧道可能被掐。

**迁移到 B 的前置条件**：去 [go/maa](https://michelangelo-studio.uberinternal.com/ma)
注册/确认一个 **uOwn 项目 UUID**。拿到后把 proxy 升级为
「USSO token + `OpenAI-Organization` header + 每请求自动刷新 token」的生产级方式，
Cerberus 退为 fallback。proxy 层做**每请求重取 token**（不硬编码），即可解决 USSO 30 分钟过期 401 问题。

### B 方式参考实现（Uber 工程师原始建议）

```python
import subprocess, openai
usso_token = subprocess.check_output(["usso-cli", "token"]).decode().strip()  # devpod 上 aifx 维护刷新
client = openai.OpenAI(
    base_url="https://genai-api.uberinternal.com/v1",
    api_key=usso_token,                                  # USSO token 作 Bearer
    default_headers={
        "OpenAI-Organization": "<你的-uOwn项目-UUID>",   # 必需，计费
        "rpc-caller": "chao.jin",                        # 成本归属
    },
)
```

> Hermes 走标准 OpenAI SDK，支持 `model.base_url` + 自定义 header 注入。
> B 方式下 `OpenAI-Organization` 这种自定义 header 仍建议在 proxy 层注入（与 A 同构），
> 避免改 Hermes client 初始化代码。

---

## 二、支持的模型（截至 2026-06）

GenAI API 暴露 **261 个 LLM 类模型**，核心：

| 系列 | 可用型号 | 备注 |
|---|---|---|
| **Claude Opus 4** | `claude-opus-4` / `-4-1` / `-4-5` / `-4-6` / `-4-7` / `-4-8`（+ `-thinking` 变体） | `-4-8` 是当前最高 |
| **Claude Sonnet 4** | `claude-sonnet-4` / `-4-5` / `-4-6`（+ thinking） | |
| **GPT-5.x** | `gpt-5.5` ✅, `gpt-5.4` / `-pro` ✅, `gpt-5.3`, `gpt-5.2`, `gpt-5.1`, `gpt-5` | **`gpt-5.5-pro` 返回 Forbidden（账号无权限）** |
| **OpenAI o 系列** | `o3` / `o3-mini` / `o3-pro`, `o4-mini`, `o1` / `o1-pro` | |
| **Gemini** | `gemini-3-pro-preview`, `gemini-3.5-flash`, `gemini-2.5-pro` | |
| **其他** | `deepseek-v4-pro`, `kimi-k2.6`, `minimax-m2.7`, `glm-5.1`, `qwen3-coder-next` | |

查全部：`curl -s http://localhost:8800/v1/models`

---

## 三、配置步骤

### 3.1 Hermes config

```bash
hermes config set model.default "claude-opus-4-8"
hermes config set model.provider "custom"
hermes config set model.base_url "http://localhost:8800/v1"
# fallback 兜底（GenAI 全挂时降级到外部 deepseek）
hermes config set fallback_providers \
  '[{"provider":"deepseek","model":"deepseek-v4-flash","base_url":"https://api.deepseek.com/v1"}]'
```

改完 config 后需要 **`/restart`**（gateway）或重开 `hermes`（CLI）才生效 —— 模型在会话启动时读取。

### 3.2 GenAI Proxy v2

`~/.hermes/scripts/genai_proxy.py` —— 一个 stdlib HTTP 转发器：

- 注入 `rpc-service: genai-api` + `rpc-caller: <email>` header
- **遇到 429 自动重试 3 次（2s / 4s backoff）**，3 次都失败才透传错误
- 监听 `127.0.0.1:8800`，转发到 `127.0.0.1:5436`（Cerberus）

---

## 四、24/7 持久化（DevPod = dinit，不是 systemd）

> ⚠️ DevPod 容器用 **dinit** 做 init（`hermes gateway install` 不支持，会报 "not supported on this platform"）。

### 4.1 dinit 服务

`/etc/dinit.d/genai-proxy`（启动 Cerberus + proxy，自动重启）：

```ini
type = process
command = /etc/dinit.d/scripts/genai-proxy.sh
run-as = user
restart = true
smooth-recovery = true
depends-on: setup-home-dir
depends-on: generate-cerberus-cert
load-options: export-passwd-vars
```

软链到 `boot.d/` 实现开机自启：
```bash
sudo ln -sf /etc/dinit.d/genai-proxy /etc/dinit.d/boot.d/genai-proxy
```

生命周期管理：
```bash
sudo dinitctl start   genai-proxy
sudo dinitctl restart genai-proxy
sudo dinitctl list | grep genai
```

### 4.2 crontab @reboot（双保险）

```cron
@reboot /usr/bin/nohup /etc/dinit.d/scripts/genai-proxy.sh > /home/user/logs/genai-proxy-cron.log 2>&1 &
```

---

## 五、踩坑记录（关键！）

排障花了多轮，根因是三层叠加：

### 坑 1：SSH_AUTH_SOCK —— 最核心 🎯

**dinit / cron 启动的进程不继承登录 Shell 的环境变量。** Cerberus 认证 bastion 需要
`SSH_AUTH_SOCK`，缺它直接报：

```
ERROR Unable to connect to ssh agent error=dial unix: missing address
Error: failed to connect to bastion: no suitable authentication methods
```

**修复**：启动脚本里硬 export：
```bash
export SSH_AUTH_SOCK=/var/lib/devpod/ssh/active_ssh_auth_sock
```

### 坑 2：429 透传成 502 → Hermes 崩溃

GenAI API 限流返回 429，proxy v1 原样透传 → Hermes 当成 502 服务错误 → 重试 3 次全挂 →
**整个会话死机**。注意：Hermes 的 `fallback_providers` 只在**连不上** provider 时切换，
**API 返回错误码（429/502）不触发 fallback**。所以兜底要在 proxy 层做。

**修复**：proxy v2 内部对 429 自动重试。

### 坑 3：日志目录不存在 → 错误被吞

脚本写日志到 `/home/user/logs/`，但目录不存在 → 输出全丢 → 看不出为啥失败。

**修复**：脚本开头 `mkdir -p ${LOG_DIR}`。

### 坑 4：路径写死错误

最早脚本把 HOME 写死成 `/home/chao.jin`，但实际 `$HOME=/home/user`
（用户名 `chao.jin` ≠ home 目录名 `user`）。用 `/home/user` 实际路径。

### 坑 5：cerberus idle 掉线 + 端口漂移 → `502 [Errno 99]`（2026-06-17 复发）

**现象**：Hermes 报 `HTTP 502: {'error': '[Errno 99] Cannot assign requested address'}`，errors.log 里 `provider=custom base_url=http://localhost:8800/v1 model=claude-opus-4-8`。这 **不是后端真 502**，而是 proxy(:8800) 连不上 :5436 时的本地错误（IPv4 refused → IPv6 `::1` 也 `Cannot assign` → 透传成 502）。

**根因 A（idle 掉线）**：cerberus 空闲约 5 分钟后日志写 `Idle session detected. Stopping Cerberus daemon` / `Periodic handshake run failed: connection is shut down` → 本地 `:5436` 端点消失。

**根因 B（端口漂移）**：旧 cerberus 没完全退出、仍占着 `:5436` 时又起了一个新的 → 新进程绑到 **`:5437`**，而 proxy 写死连 `:5436` → connection refused。`ss`/`netstat` 缺失时用 `/proc/net/tcp` 解析监听端口（十六进制），必要时用 inode 反查持有端口的 pid：

```bash
# 列本机所有 LISTEN 端口（st=0A），确认 cerberus 实际绑在 5436 还是漂到了 5437
awk '$4=="0A"{print strtonum("0x" substr($2,index($2,":")+1))}' /proc/net/tcp | sort -un
# 直接验 5436 健康（最快）
curl -sf http://localhost:5436/health -H "rpc-service: genai-api" -H "rpc-caller: <email>" && echo OK
```

**修复**：杀干净再重启——杀干净才会重新抢回 `:5436`，否则又漂到 5437：
```bash
export SSH_AUTH_SOCK=/var/lib/devpod/ssh/<your-agent>.sock   # 坑 1：后台进程不继承，必须显式
pkill -f "cerberus -s genai-api"; sleep 2
bash ~/.hermes/scripts/start_genai.sh
```

> 这类「idle 掉线 + 漂移」是高频复发故障，靠下面 §8 的隧道 watchdog（每分钟纯脚本）自动兜底，不用人盯。

---

## 六、健康检查 / 验证

```bash
# 1. dinit 服务状态
sudo dinitctl list | grep genai          # 期望 [[+]] genai-proxy

# 2. 进程都在
ps aux | grep -E "cerberus|genai_proxy" | grep -v grep

# 3. 端到端测试
curl -s http://localhost:8800/v1/chat/completions \
  -H "content-type: application/json" \
  -d '{"model":"claude-opus-4-8","messages":[{"role":"user","content":"ping"}],"max_tokens":5}'
# 期望返回 choices[0].message.content

# 4. ussh cert（自动续期，正常无需手动）
ussh --ussh-replace                       # 只在自动续期失败时才会要 YubiKey tap
```

> **YubiKey / ussh 认证说明（重要）**：devpod 上 dinit 服务 `agentic-ussh-refresh`
> **每 10 小时自动续期** ussh x509 cert（有效期 20h，留 10h 缓冲，10 次重试 backoff）。
> 所以**只要 devpod 不重启，Chao 早晨不需要 tap YubiKey 重认证**。
> 需要 YubiKey 的场景只有：① devpod 重启 / 被回收后首次启动；② 自动续期连续失败。
> **过期信号** = GenAI 突然 401 / cerberus 连不上。出现时再 tap YubiKey 跑 `ussh --ussh-replace`。

---

## 七、日常运维

| 场景 | 操作 |
|---|---|
| ussh cert 自动续期失败（GenAI 突然 401） | `ussh --ussh-replace`（tap YubiKey）→ `sudo dinitctl restart genai-proxy` |
| GenAI 突然 502 `[Errno 99]` / `:5436` 不在 | 隧道 watchdog（系统 cron，§8）每分钟自动重启 cerberus；若属认证过期会发 Telegram 提醒你 `ussh --ussh-replace` |
| 切换模型 | `hermes config set model.default <model>` → `/restart` |
| proxy 挂了 | `sudo dinitctl restart genai-proxy` |
| 容器重启后 | dinit + crontab @reboot 自动拉起，无需手动 |
| GenAI 全挂 | 自动降级到 fallback `deepseek-v4-flash` |

---

## 八、GenAI 隧道 watchdog（系统 cron · 认证失败自动 Telegram 提醒）

§4 的 dinit/crontab 解决「容器重启 / proxy 进程崩」；但 cerberus 会**周期性 idle 掉线 / 端口漂移**（坑 5），需要一个**更高频、纯脚本、不依赖 LLM** 的兜底。

> ⚠️ **为什么不用 Hermes 内部 cron 做这个**：曾有一个 `genai-proxy-watchdog`（Hermes cron, `no_agent=false`）——它要**起 LLM agent** 才能检查，可 LLM 掉线时它自己也连不上同一条隧道，构成循环依赖（errors.log 里一直 `Job 'genai-proxy-watchdog' failed`）。已 `hermes cron remove` 删除，改用下面的**系统 cron 纯脚本**。通用原理见 [[container-reboot-service-persistence]] 教训 4 与 6。

`~/.hermes/scripts/genai_tunnel_watchdog.sh`（系统 crontab `* * * * *`，每分钟跑）：

- **健康**（`curl :5436/health` 通）→ 静默，清除告警限频 marker。
- **掉线** → `export SSH_AUTH_SOCK=...`（坑 1）→ `pkill cerberus; sleep 2; nohup cerberus -s genai-api` → 等最多 30s 复检；恢复则顺带补起 proxy(:8800)。
- **重启后仍挂 + 判定为认证问题** → **Telegram 直接提醒用户重新认证**（关键新增）。
- **非认证原因** → Telegram 提醒手动检查。
- 告警**限频 1 小时 1 次**（`/tmp` marker 文件），恢复后自动清零。

**认证问题怎么判定**（任一命中即视为「需人介入」）：
1. `SSH_AUTH_SOCK=... ssh-add -l` 无身份（ussh cert 不在 agent）；
2. USSO token 文件 `~/.usso-tokens/.genai-api.uberinternal.com` 缺失；
3. cerberus 日志近 60 行命中 `no ssh cert|ussh|usso|unauthor|permission denied|401|expired`。

**为什么要专门区分认证**：自愈有边界——进程死/端口漂移脚本能自动修；但**凭证过期需要人重新登录（tap YubiKey 跑 `ussh --ussh-replace`）**，脚本修不了，必须**主动通知人**，否则只会无声地反复重启失败。通知通道（Telegram bot API）**不依赖被监控的 LLM 链路**，所以 LLM 全挂时告警仍能送达。通用版见 [[container-reboot-service-persistence]]「自愈的认证升级边界」。

**Telegram 发送要点**：运行时从 `.env` 读 `TELEGRAM_BOT_TOKEN` + `TELEGRAM_HOME_CHANNEL`（**不硬编码**，遵 general-rule §7）→ `curl api.telegram.org/bot<token>/sendMessage`。注意 Telegram bot **不能给「没先私聊过 bot」的用户发消息**，首次接通要发一条测试消息确认返回 `ok:true`。

> 与 [[hermes-gateway-watchdog]] 的分工：那个守 **gateway 进程**（崩溃自愈），本 watchdog 守 **genai 隧道**（idle 掉线/端口漂移 + 认证升级）。两者都是 `no_agent`/纯脚本路径，健康时静默。
