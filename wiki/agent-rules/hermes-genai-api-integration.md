---
title: Hermes 接 Uber 内部 GenAI API（Claude Opus 4 / GPT-5.5）+ DevPod 24/7 持久化
domain: agent-rules
type: concept
keywords: [hermes, genai-api, cerberus, claude-opus-4, gpt-5.5, devpod, dinit, ssh-auth-sock, proxy, 24-7, persistence, frontier-model]
tags: [hermes-integration, genai-api, uber-internal, cerberus, dinit, persistence, model-config]
source: Cowork 协作会话 2026-06-12（GenAI API 接入排障 + dinit 持久化实装）
sources:
  - ~/.hermes/scripts/genai_proxy.py（proxy v2 实装稿）
  - /etc/dinit.d/genai-proxy（dinit 服务定义）
created: 2026-06-12
updated: 2026-06-12
last_updated: 2026-06-12
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

# 4. ussh cert（每天过期，早上需要重签）
ussh                                      # 重新签发 git + mtls cert
```

---

## 七、日常运维

| 场景 | 操作 |
|---|---|
| 早上 cert 过期 | `ussh`（重签），然后 `sudo dinitctl restart genai-proxy` |
| 切换模型 | `hermes config set model.default <model>` → `/restart` |
| proxy 挂了 | `sudo dinitctl restart genai-proxy` |
| 容器重启后 | dinit + crontab @reboot 自动拉起，无需手动 |
| GenAI 全挂 | 自动降级到 fallback `deepseek-v4-flash` |
