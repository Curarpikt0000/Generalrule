# Hindsight local_embedded 记忆后端在旧 glibc Linux 上的踩坑

**日期**：2026-07-02
**触发事件**：在 Hermes 上启用 hindsight 记忆后端（local_embedded + hybrid 双重记忆），从 `hermes memory status` 显示 `not available` 一路排到 `available ✓`，中途连撞三个互相独立的坑
**适用范围**：任何在**旧 glibc 的 Linux（如 Debian 12 / glibc 2.36）**上部署 hindsight local_embedded 模式的人；更广义地——任何用「预编译 native `.so` + 内嵌数据库 + 版本敏感的 Python 客户端」的自托管服务

---

## 核心原则

> **一个 `not available` 背后可能叠着三个毫不相关的根因。** 别看到第一个错就以为修完了——hindsight 本地模式把「native 扩展的 glibc 兼容性」「daemon 进程管理」「Python 包版本契约」三件事串在一条启动链上，任何一环断了整条链都亮红灯，且错误信息会互相掩盖（尤其旧日志残留会伪装成当前错误）。
>
> **CLI 报错的 banner 未必是当前状态**——native 服务重启后，管理 CLI 可能仍打印上一轮的缓存错误。**永远以带时间戳的日志文件为准，不信 CLI 的即时横幅。**

---

## 架构：本地模式实际跑了什么

搞清楚组件关系是排障前提，否则会对着错误的进程/端口瞎修：

- **`hindsight-api`** —— 本地 FastAPI 服务（Uvicorn）。底层用 **pg0-embedded**（`~/.pg0/` 下的一个内嵌 PostgreSQL 18.x）+ **pgvector** 做向量存储。
- **`hindsight-embed`** —— daemon 管理器。`hindsight-embed -p <profile> daemon start` 把 hindsight-api 拉在一个**按 profile 分配的动态端口**上（如 profile `hermes` @ :9177）。优先用 venv 里装的 `hindsight-api` 入口，找不到才 fallback 到 `uvx`（需要 `uv`）。
- **`hindsight-client`** —— 纯 HTTP 客户端（`Hindsight(base_url=...)`，同步 + 异步 `a*` 方法）。
- **Hermes 插件 `plugins/memory/hindsight/__init__.py`** —— local_embedded 模式下执行 `from hindsight import HindsightEmbedded`（一个顶层包，现代 0.8.x 包布局里**根本不存在**——这是坑 3）。

---

## 坑 1（最硬核）：pgvector `vector.so` 的 glibc 版本不兼容

### 症状
daemon 起不来，`~/.hindsight/profiles/<profile>.log` 里：
```
could not load library ".../.pg0/installation/<ver>/lib/vector.so":
  /lib/x86_64-linux-gnu/libc.so.6: version `GLIBC_2.38' not found
RuntimeError: pgvector extension is required but not installed
RuntimeError: Database migration failed
```

### 根因
pg0 打包分发的预编译 `vector.so` 是针对**更新的 glibc（如 2.38）** 编译的，但主机的 glibc 更旧（Debian 12 = 2.36）。so 加载失败 → `CREATE EXTENSION vector` 失败 → 数据库 migration 失败 → 服务起不来。

### 修法：用 pg0 自带的 pg_config 从源码重编译 pgvector
关键洞察：**SQL 迁移文件（`share/extension/vector--*.sql`）都在，只有那个 `.so` 二进制不对**。用 pg0 自己的 postgres 头文件重编译一个匹配本机 glibc 的即可。

```bash
export PGROOT=$HOME/.pg0/installation/<VER>      # e.g. 18.1.0
export PATH="$PGROOT/bin:$PATH"

# 1. 确认需要的 pgvector 版本（control 文件里）
find ~/.pg0 -name vector.control -exec grep default_version {} \;   # e.g. 0.8.1

# 2. 下源码，用 pg0 的 pg_config 编译（需要 gcc + make）
cd /tmp
curl -sL https://github.com/pgvector/pgvector/archive/refs/tags/v<VER>.tar.gz -o pgv.tgz
tar xzf pgv.tgz && cd pgvector-<VER>
make PG_CONFIG=$PGROOT/bin/pg_config

# 3. 验证新 so 只需要旧 glibc（应 <= 主机版本）
objdump -T vector.so | grep -oE 'GLIBC_2\.[0-9]+' | sort -V | uniq | tail
#   实测重编译后只需 GLIBC_2.14 —— 任何现代主机都安全

# 4. 备份 + 替换
cp $PGROOT/lib/vector.so $PGROOT/lib/vector.so.bak
cp vector.so $PGROOT/lib/vector.so
ldd $PGROOT/lib/vector.so | grep -i 'not found' || echo "deps OK"
```

### 教训
**预编译 native 扩展 + 旧发行版 = glibc 地雷。** 遇到 `version 'GLIBC_2.XX' not found` 别放弃或降级整个栈——只要有源码 + 目标环境的 `pg_config`/头文件，本地重编译一份就地兼容是最干净的解，比换外部数据库、改架构都省事。

---

## 坑 2：`uv`/`uvx` 未安装（daemon "Command not found: uvx"）

### 症状
```
Command not found: uvx
Full command: uvx hindsight-api@<ver> --daemon ...
Install hindsight-api with: pip install hindsight-api
```

### 根因
daemon 管理器（`hindsight_embed/daemon_embed_manager.py` 的 `_find_api_command`）在找不到 venv 本地 `hindsight-api` 入口时，fallback 去调 `uvx hindsight-api@<ver>`。如果机器没装 `uv`/`uvx`，这条路直接死。

### 修法（两手都做）
```bash
# ① 把 hindsight-api 装进 Hermes 用的同一个 venv，让入口能被 sysconfig 解析到
$VENV/python3 -m pip install hindsight-api    # 会拉 torch/sentence-transformers/pg0，几分钟

# ② 顺手装 uv 作为 uvx fallback 的兜底
curl -LsSf https://astral.sh/uv/install.sh | sh   # -> ~/.local/bin/uv, uvx
```
`_find_api_command` 优先用 `sysconfig` 的 scripts 目录（`<venv>/bin/hindsight-api`）——一旦装到那里就不会再走 uvx。

### 坑中坑
装了 uv 后，**启动 daemon 前必须** `export PATH="$HOME/.local/bin:$PATH"`（uv 装在这），否则子进程仍找不到 uvx。

---

## 坑 3：缺顶层 `hindsight` 包，`_check_local_runtime` 永远失败

### 症状
`hermes memory status` 一直显示 `Status: not available ✗`，即使 daemon 已经在跑、health 返回 200、Python client 直连也通。

### 根因
Hermes 插件的 `_check_local_runtime()` 执行 `import hindsight`（顶层包），插件后面还有 `from hindsight import HindsightEmbedded`。但**现代包布局（0.8.x）根本没有顶层 `hindsight` 模块**——只有 `hindsight_client` / `hindsight_embed` / `hindsight_api`。`import hindsight` 抛 `ModuleNotFoundError` → 探测返回 False → status 报不可用，且真实 session 里插件会因此 fallback 到内置 MEMORY.md，**灌进去的记忆根本用不上**。

两个死路（别走）：
- **`pip install hindsight`** —— PyPI 上叫这名的是个无关的 Py2 死包，报 `use_2to3 is invalid`。
- **降级 `hindsight-client` 到 0.6.1** —— 也没有 `HindsightEmbedded` 类。

### 修法：写一个 compat shim 包
在 `<venv>/.../site-packages/hindsight/__init__.py` 放一个 shim，提供 `HindsightEmbedded`：
1. `get_embed_manager().ensure_running(cfg, profile)` 确保 daemon 起来
2. `.get_url(profile)` 拿运行中 daemon 的动态 URL
3. 包装 `hindsight_client.Hindsight(base_url=url)`
4. 暴露 **async** 方法 `aretain/arecall/areflect/aretain_batch/aset_reflect_mission/aclose`、同步 passthrough、`.url` 属性、`__getattr__` 兜底转发

**载荷契约**（决定 shim 必须提供什么）：Hermes 插件 `await operation(client)` 并读 `client.url`——所以 **async `a*` 方法 + `.url` 属性**是必需的。`hindsight_client.Hindsight` 0.8.2 恰好已有全部 `a*` 方法，shim 只是补上「顶层命名空间 + daemon 自动管理 + kwargs 适配」。

### 教训
**Hermes 插件代码写死了对某个包版本的接口契约（`from hindsight import HindsightEmbedded`），当装的是不同版本时不会优雅报错，而是静默 fallback。** 遇到「一切看起来都通了但 status 仍说不可用」，去读插件的 `is_available` / `_check_*` 探测逻辑——问题常在探测本身，而非真实功能。

---

## 其他要点

### profile 与端口
- 默认 profile 硬编码端口 **8888**；若被系统进程占用，建命名 profile 用空闲端口：
  ```bash
  $VENV/hindsight-embed profile create hermes --port 9177
  $VENV/hindsight-embed profile set-active hermes
  ```
- **不能把 profile 命名为 `default`**（保留字）。

### daemon 启动/验证
- `daemon start` 在前台会**挂起不返回**——必须后台启动 + 独立验证：
  ```bash
  export PATH="$HOME/.local/bin:$PATH"; set -a && . ~/.hermes/.env && set +a
  $VENV/hindsight-embed -p hermes daemon start &      # 后台
  sleep 40
  $VENV/hindsight-embed -p hermes daemon status       # 期望 "✓ Daemon Running (hermes @ :PORT)"
  curl -s -o /dev/null -w '%{http_code}\n' http://localhost:<PORT>/health   # 期望 200
  tail -30 ~/.hindsight/profiles/hermes.log | grep -iE 'startup complete|Uvicorn|error'
  ```
- **替换 vector.so 后，CLI/status 可能仍打印上一轮的旧 "GLIBC_2.38" 错误**——务必看日志文件的新时间戳行，别信 CLI 缓存横幅。

### 那个下载来的 hindsight CLI 二进制在旧 glibc 上不可用
`~/.local/bin/hindsight`（`hindsight-embed memory ...` 会自动下载）需要 GLIBC_2.39，旧机器跑不了。**别依赖它。** Hermes 也不用它——走的是 Python client。所有冒烟测试用 `hindsight_client.Hindsight` 或 shim 做，别用那个 CLI。

### 验证端到端
```bash
hermes memory status    # Provider: hindsight / Status: available ✓
```
再跑一个 Python 冒烟：import `hindsight` → 实例化 `HindsightEmbedded` → `await aretain(...)` → `await arecall(...)`。（无害警告 "Unclosed client session" 可忽略——是测试脚本没关连接，不影响功能。）

### 灌历史记忆的注意
- 每条 retain 会触发一次记忆提炼模型（如 haiku）调用——**慢**，批量导入要后台跑。
- 一条 fact 会被提炼成**多个原子记忆单元**（43 条 fact → 100+ units 是正常的）。
- **retain 路径依赖记忆提炼模型走的那条 proxy/隧道**（本例走 localhost:8800）。如果有「闲时省资源」机制会 idle 停掉那条隧道，异步 retain（每 N 轮触发）会失败——保持隧道在线或调高闲停阈值。

---

## 相关页面

- [[container-reboot-service-persistence]] —— 自托管 native 服务的重启持久化与端口漂移排障
- [[rag-chatbot-first-build-pitfalls]] —— 另一个「向量库 + 本地服务」栈的首次构建踩坑
- [[rag-incremental-index-refresh]] —— 向量索引维护与 cron 双层拆分
