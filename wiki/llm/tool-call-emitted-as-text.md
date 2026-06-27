---
title: LLM 把工具调用写成正文文本（antml 泄漏 + 上下文污染循环）
domain: llm
type: concept
keywords: [tool-call, function-call, antml, invoke, 工具调用, 文本泄漏, 上下文污染, contamination, tool_search, openai-compatible, claude, hermes, 自我模仿]
tags: [tool-calling, llm-behavior, contamination, hermes, claude]
source: 2026-06-24 排障——Hermes(default profile) 在对话末尾反复把工具调用打成 antml 文本导致任务失败
sources: [conversation-2026-06-24, /home/user/.hermes/state.db]
created: 2026-06-24
updated: 2026-06-27
last_updated: 2026-06-27
machine: UB
---

# LLM 把工具调用写成正文文本（antml 泄漏 + 上下文污染循环）

> 症状：agent 在回复**正文里**打出一段看起来像工具调用的 XML（如下），但工具**根本没被执行**，任务静默失败；用户还能直接看到这段 XML。
> ```
> 好，我现在用真正的工具调用。
> <function_calls>
> <invoke name="cronjob">
> <parameter name="action">list</parameter>
> </invoke>
> ```

## 现象

- assistant 消息的 `content` 里出现 `<invoke name="…">` / `<parameter name="…">`（Claude 的 **antml** 原生工具语法），但该消息的结构化 `tool_calls` 字段**为空**（`has_tool_calls=0`）。
- 调用从未进入真正的工具通道 → 不执行 → 任务失败。
- 模型常自带前缀文字"我现在用**真正的**工具调用"——这是它在回应"上一条不是真调用"的纠正，但**又犯**。

## 根因（两层）

1. **模型没拿到原生工具，就自己编 antml 文本。** 当 OpenAI 兼容层/harness 没把 `tools` 原生下发给模型（例如 Hermes 的 `tools.tool_search` 开启后只下发一个"搜索工具"、不下发目标工具），Claude 想调用某工具却发现它不在原生工具表里 → 按训练时的 antml 格式**把调用写进正文**。
   - 验证法：直接拿一个工具定义打 OpenAI 兼容端点，若返回**结构化 `tool_calls`** 就说明端点/模型没问题，问题在 harness 没下发 tools。
2. **harness 既不执行、也清理不掉这个格式。** 有的 harness 有"清理泄漏工具调用文本"的逻辑，但常只认 `<tool_call>` / `<function_calls>` / `<function name=>`（Gemma 风格），**不认 Claude 的 `<invoke>` / `<parameter>`** → 这段文本既不执行、也不从显示里剥掉，用户直接看见。

## 自我污染循环（为什么"每次都犯、自己排查不了"）

1. 某轮模型吐了一次 antml 文本调用 → 这段 `<invoke…>` 进了**对话历史**；
2. 之后每轮模型看到自己历史里的范例 → **照着模仿**继续写文本调用；
3. 纠正它也没用——污染的历史还在，模型从会话内部看不到也改不掉。
> 实测：一个 164 条消息的会话里 31 条（18%）是文本调用，越积越多。**模型困在自己的坏历史里，无法自愈。**

## 诊断方法

- 在 session 存储/日志里搜 `invoke name=` / `<parameter name=` / `<function_calls>`，看是否出现在 assistant 的 `content`（而非 `tool_calls`）。
- 按 `session_id` 聚合，定位**被污染最重的会话**。
- 拿工具定义直接打底层端点验证"原生 tool_calls 是否正常"，以区分是**端点问题**还是 **harness 没下发 tools**。

## 修复（按杠杆）

1. **弃用被污染的会话**（最有效）：导出备份后**开新对话**，别再 resume 那条被自己坏范例教坏的会话。compact 也可，但摘要可能残留范例，新开更彻底。
2. **让工具始终原生下发**：关闭/调高 `tool_search` 阈值（Hermes：`tools.tool_search.enabled: false`），消除"目标工具没下发→模型编 XML"的诱因。代价：每次请求 prompt 更大、更费 token，**与超大对话的超时/成本相冲突**，按需权衡。
3. **harness 缺陷（根上）**：识别并**剥离/抢救** antml `<invoke>` 格式（既要从显示剥掉，最好还能解析成真调用）。上游 Hermes 原生只认 OpenAI 格式、从不处理 Claude antml（`git grep <invoke|antml` 上游整树零命中），官方修不了 → **本地补丁**（见下）。

## 变体：悬空 `call:` 断点（无 `<invoke>`，正文停在 `call:`）

同一格式转换失败的另一种表现，2026-06-27 实测：模型吐了一个工具调用引子行 **`call:`**（或 `call`）后，**没有**任何 `<invoke>`/工具名/参数，且 `finish_reason=stop` + `tool_calls` 空。
- 症状：Telegram 消息**正好停在 `call:`**，对话挂住**死等用户**（用户原话"每次 call: 就断"）。
- 难点：正文**非空**（真实叙述 + 末尾一个 `call:`），所以 harness 既有的"空响应 nudge/retry"全被跳过 → 半截消息原样返回。
- **务必区分两类 `call:`**：`finish_reason=tool_calls` 且 `tool_calls` 有值 = **正常引子**（模型在调工具的口头禅，无害，别误杀）；`finish_reason=stop` + `tool_calls` 空 = **真断**。
- **为什么 Hermes 自己永远修不了**：① `stop` 时控制权交还用户，模型没被再次调用，断的当下无人察觉；②会话历史被 `...call:` 尾巴污染→模型照抄自己→反复在同一边界断；③ antml salvage 补丁无 `<invoke>` 可解析、不触发。

## 已实装的本地补丁（Hermes VM，逐 profile 重启才生效）

> 上游修不了 → 在 `~/.hermes/hermes-agent/` 本地打补丁。改完**必须逐个重启每个 profile**（进程不热更新代码，见 [[hermes-multi-profile-watchdog]]）；改前备份 `*.bak.<ts>`。

- **A 剥离**：`agent/agent_runtime_helpers.py` 的 `strip_think_blocks()` 增加对 `<invoke>`/`<parameter>`/`<function_calls>`/裸 `call` 前缀的正则剥离（原本只认 `<tool_call>`/`<function>`），保证泄漏文本不显示给用户、不进历史当坏范例。
- **B 转译/抢救**：同文件新增 `parse_antml_tool_calls()`；`agent/conversation_loop.py` 在 `if assistant_message.tool_calls:` 前插 salvage——空 `tool_calls` + 完整 `<invoke>` + 名字 ∈ `valid_tool_names` 时，解析合成结构化 `tool_call` 注入并清洗 content。护栏：只在"无真调用 + 块完整 + 名字是已知工具"时才触发，防误执行正文里**引用**的格式。
- **C 悬空 `call:` 恢复**：`agent/conversation_loop.py` 的 no-tool-call 分支顶部加检测——`无 tool_calls + 无 <invoke> + 正文末行匹配 ^[ \t]*call[ \t]*:?$` → 剥掉悬空 `call:` + 一次性 nudge（guard `_dangling_call_retried`，工具成功后重置）让模型重发工具调用；guard 用尽则带清洗后正文 fall through，用户**绝不再看到 `call:`**。正则对 `recall`/`API call`/`make the call.`/`subprocess.call(` 零误伤（已验）。
- **清污染**：被 `...call:` 尾巴污染的会话历史可用 `venv/bin/python` 直接 `UPDATE state.db` 去尾（备份到 json），斩断自我模仿；sqlite3 CLI 没装，走 venv python 的 sqlite3 模块。

## 通用教训

- **工具调用是独立的结构化通道，不是正文文字。** 一旦模型把它写进正文，就既不执行又污染历史。
- **坏输出进了历史 = 会自我强化。** 强模仿型模型（Claude 尤甚）会照抄自己历史里的坏范例；遇到"反复犯同一个格式错"，先怀疑**上下文污染**，优先换干净会话，而不是反复纠正。
- 省 token 的"工具搜索/惰性下发"机制有副作用：**目标工具不在原生表里时，模型可能编造调用**。

## 来源

2026-06-24 Hermes(default profile, claude-opus-4-8 via custom/genai 网关) 排障实录；证据见 `~/.hermes/state.db` messages 表。

## 相关页面

- [[hermes-genai-api-integration]] —— 同机 Hermes 接 GenAI 网关的 provider=custom 配置（本问题的运行环境）
- [[fallback]] —— 模型 fallback；注意：**断连/Connection error 才触发 fallback，错误码或本类"文本泄漏"不触发**
- [[container-reboot-service-persistence]] —— 同机另一类"自愈边界"教训
