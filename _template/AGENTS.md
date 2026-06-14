# 项目规则 (Project Rule)

> 本文件是**项目级约束**，在 `general-global-rule.md` 的全局规则基础上叠加生效。
> 只写本项目特有的约束，不重复全局规则的内容。
> 所有 AI Coding 工具（Antigravity / Claude Code / Cursor 等）均自动识别本文件。
> 创建日期：YYYY-MM-DD

---

## §P1 项目基本信息

- **项目名称**：<项目名>
- **项目类型**：<LLM 应用 / Web API / 数据处理 / 自动化脚本 / 其他>
- **主要技术栈**：<Python 3.x + FastAPI + Pydantic / 其他>
- **部署环境**：<Cloud Run / Docker / 本地 / 其他>
- **项目根目录**：<绝对路径，例如 ~/projects/项目名>（各机按本地 clone 路径填写）

---

## §P2 技术栈特有约束

> 填写本项目使用的特定框架/库的约束，空白处删除不填。

### 核心依赖版本锁定
填写需要严格锁定版本的依赖（不是所有依赖，只写锁定理由特殊的）
例：
pydantic==2.x.x   # 因 v1/v2 接口不兼容，禁止升级到 v3
fastapi>=0.100.0  # 需要 lifespan 支持

### 禁用依赖
- <例：禁止引入 Django，本项目只用 FastAPI>
- <例：禁止引入 Selenium，统一用 playwright>
- <如无则填"无">

### 必须遵守的框架规范
- <例：FastAPI 路由统一放 routers/ 目录，不写在 main.py>
- <例：Pydantic model 统一放 models/ 目录>
- <如无则填"无">

---

## §P3 业务领域约束

> 填写本项目业务逻辑的特殊规则，防止 Agent 做出"技术上没错但业务上不对"的决策。

### 核心业务规则
- <例：所有外部 API 调用必须走 services/ 层，Controller 层不直接调 HTTP>
- <例：用户数据在写入前必须经过 validators.py 的校验，不得绕过>
- <如无则填"无">

### 数据流向约束
- <例：原始爬取数据 → raw/ 目录 → 清洗后 → processed/ 目录，不得混用>
- <如无则填"无">

### 已知的业务陷阱（必读）
- <例：微信公众号接口每天有调用次数限制，测试时必须用 mock，不得真实调用>
- <例：YouTube API 配额每天 10000 单位，批量任务必须加速率限制>
- <如无则填"无">

---

## §P4 目录结构约定

> 填写本项目的目录结构，让 Agent 知道新文件该放哪里。
<项目名>/
├── main.py              # 主入口
├── config.py            # 配置参数（从环境变量读取）
├── utils.py             # 通用工具函数
├── requirements.txt     # 依赖清单
├── .env                 # 密钥（已在 .gitignore 中）
├── tasks/
│   ├── todo.md          # 任务计划（Agent 自动维护）
│   └── lessons.md       # 经验积累（Agent 自动维护）
├── <其他目录>/          # 按项目实际填写
│   └── ...
└── AGENTS.md            # 本文件

### 文件放置规则
- 新增工具函数 → `utils.py`（除非职责完全不同，才新建文件）
- 新增配置项 → `config.py`（从环境变量读，不硬编码）
- 新增业务逻辑 → `<对应模块>.py`（参考上方目录结构）
- **禁止**直接在 `main.py` 里堆业务逻辑

---

## §P5 环境变量清单

> 列出本项目依赖的所有环境变量，让 Agent 在涉及配置时有据可查。

```bash
# 必填
<VAR_NAME>=<说明，例：Gemini API Key>
<VAR_NAME>=<说明>

# 可选（有默认值）
<VAR_NAME>=<说明，例：LOG_LEVEL，默认 INFO>
```

**注意**：`.env` 文件已在 `.gitignore` 中，Agent 不得将密钥写入任何被 Git 追踪的文件。

---

## §P6 LLM 调用专项约束

> 仅 LLM 应用类项目需要填写，纯工具类项目可删除本节。

### 使用的 LLM 平台
- **主平台**：<例：Vertex AI (gemini-pro 系列)>
- **备用平台**：<例：AI Studio>
- **调用入口文件**：<例：llm_client.py>

### Fallback 链路配置
- 参见 `general-global-rule.md §3.3`（全局级联回退规则）
- 本项目特有的 Fallback 调整（如有）：<例：Flash 级别不可用时直接报错，不降级到第三平台>

### 禁止行为
- 禁止在业务逻辑代码里直接实例化 LLM 客户端（统一走 `llm_client.py`）
- 禁止硬编码 model ID（参见全局规则 §3.1）

---

## §P7 测试与验证约定

### 当前测试状态
- [ ] 有 `tests/` 目录和测试代码
- [x] 暂无测试（依赖 `/verify-done` 的场景化手动验证）

### 手动验证的关键场景（项目特有）
> 填写本项目特有的验证场景，补充 `/verify-done` Workflow 第 3 步覆盖不到的地方。

- <例：修改爬虫逻辑后，必须用真实 URL 跑一次确认输出格式不变>
- <例：修改 Pydantic Schema 后，必须用线上真实数据的样本做一次反序列化测试>
- <如无则填"无">

---

## §P8 本项目专属 Lessons 入口

> 本节不需要手动填写，由 Agent 在 `tasks/lessons.md` 中自动维护。
> 此处只做路径声明，确保所有工具都知道经验库在哪里。

- **经验库路径**：`tasks/lessons.md`
- **TODO 路径**：`tasks/todo.md`
- **格式规范**：见 `general-global-rule.md §6.2`

---

## §P9 更新记录

| 日期 | 变更 | 原因 |
|---|---|---|
| YYYY-MM-DD | 初版建立 | 项目启动 |

---

> **给 Agent 的提示**：本文件是项目级约束的**唯一来源**。如发现本文件与 `general-global-rule.md` 有冲突，**项目级约束优先**（本文件胜出）。如发现本文件有遗漏或需要更新，请在任务完成后提示用户更新本文件。
