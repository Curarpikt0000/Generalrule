# llm 领域知识

> 新页面写完后在此登记一行（手动维护）。

## 页面列表

- [sentiment-direction-extraction.md](sentiment-direction-extraction.md) — LLM 情绪/多空方向抽取红线：绝不浅层文本/emoji 匹配或默认中性，必须逐条读懂语言意味+按标的拆分+存结构化方向字段+聚合读字段。
- [tool-call-emitted-as-text.md](tool-call-emitted-as-text.md) — 模型把工具调用写成正文 antml 文本（`<invoke>`）而非结构化 tool_calls：不执行+不被清理+自我污染历史循环；诱因 tool_search 未原生下发工具；修复=弃用污染会话/原生下发工具。
