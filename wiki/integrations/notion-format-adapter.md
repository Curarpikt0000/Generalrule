# 跨系统格式适配：写入 Notion 的标准做法

**问题域**：从任何 LLM / 工具 / 抓取器 → Notion 数据库  
**适用对象**：Hermes、Claude Code、Antigravity、Gemini CLI、任何 AI Agent  
**难度**：低（即装即用）  
**核心原则**：永远不要假设两个系统的格式可以直接传递

---

## 0. TL;DR

**不要把 Markdown 字符串直接传给 Notion API**。

Notion API 只接受**结构化的 Block 对象**（JSON），不接受原始 Markdown。
直接传 Markdown 会导致：
- **bold** 显示成字面的 **bold**
- 标题没字号
- 列表没缩进
- 代码块没等宽字体
- 反斜杠满天飞（`\*\*`、`\#\#`）

**解决方案**：在中间加一个 Markdown → Notion Blocks 的适配器。

**推荐工具**：`mcp-mdnotion`（GitHub: `aia-ops/mcp-mdnotion`）—— 一个现成的 MCP 服务器，基于 martian 库，自动转换。

---

## 1. 问题的根本原因

### 1.1 为什么 Markdown 不能直接给 Notion？

Notion 的内容模型不是文本，是 **Block 树**：

```
Page
├── Block (heading_1, "标题")
├── Block (paragraph, [text, bold_text, link])
├── Block (bulleted_list_item, "列表项")
└── Block (code, language="python", "代码")
```

每个 Block 都是一个 JSON 对象，有特定的 type 字段和对应的内容结构：

```json
{
  "type": "heading_2",
  "heading_2": {
    "rich_text": [
      { "type": "text", "text": { "content": "标题文字" } }
    ]
  }
}
```

而 Markdown 是字符串：

```
## 标题文字
```

**两者形状完全不同**。Notion API 不会自动解析 Markdown 字符串里的 ## 把它变成 heading。

### 1.2 失败模式

```
LLM 输出 Markdown 字符串
    ↓
直接 POST 给 Notion API 的 paragraph block
    ↓
Notion 把整段当成纯文本处理
    ↓
用户看到的：## 标题文字 **bold** \n - 列表项
（字面字符，没有任何格式）
```

更糟的失败模式：**双重转义**

```
Python / JS 处理时为了"安全"自动转义 Markdown 元字符
    ↓
**bold** → \*\*bold\*\*
##标题 → \#\#标题
    ↓
传给 Notion，显示成：\*\*bold\*\*
```

---

## 2. 标准解决方案

### 2.1 适配器模式

```
[源系统：抓取器 / LLM / 文件]
    ↓ 输出 Markdown
[适配器：Markdown → Notion Blocks]
    ↓ 输出 JSON Block 数组
[目标系统：Notion API]
    ↓
完美渲染的 Notion 页面
```

### 2.2 推荐工具：mcp-mdnotion

**为什么选它**：

| 特性 | 说明 |
|------|------|
| 已经是 MCP 服务器 | 任何 MCP 客户端（Hermes / Claude Code / 等）即装即用 |
| 基于 martian 库 | 业界最成熟的 Markdown → Notion 转换器 |
| 自动处理边界条件 | Notion 的 2000 字符限制、嵌套深度限制等都自动处理 |
| 支持所有常见 Markdown | 标题、加粗、斜体、列表、代码块、表格、引用、链接、图片 |
| 单行安装 | npx mcp-mdnotion 即可 |

**支持的 Markdown 语法**：
- 标题 H1-H6（H4+ 自动降级到 H3，因为 Notion 只支持到 3 级）
- 加粗、斜体、删除线、行内代码、链接
- 有序/无序/复选框列表（任意嵌套深度）
- 代码块（带语言高亮）
- 引用块
- 表格
- 图片
- GFM Alerts（`> [!NOTE]`、`> [!WARNING]` 自动转 Notion Callout）
- Emoji Callouts（`> 📘 Note: ...` 转带颜色的 Callout）

### 2.3 安装配置

Step 1：测试可用

```bash
npx mcp-mdnotion
```

Step 2：添加到 MCP 配置

不同客户端的配置位置：
- **Hermes**：`~/.hermes/config.yaml`
- **Claude Desktop**：`~/Library/Application Support/Claude/claude_desktop_config.json`
- **Claude Code**：`~/.claude/.mcp.json` 或项目级 .mcp.json
- **Cursor / Windsurf**：`.cursor/mcp.json` 或 .windsurf/mcp.json
- **VS Code**：`.vscode/mcp.json`

**Hermes 配置示例**（YAML）：

```yaml
mcp_servers:
  markdown-to-notion:
    command: npx
    args:
      - mcp-mdnotion
    timeout: 30
```

**通用配置示例**（JSON）：

```json
{
  "mcpServers": {
    "markdown-to-notion": {
      "command": "npx",
      "args": ["mcp-mdnotion"]
    }
  }
}
```

**Step 3：重启客户端**，验证工具加载。

---

## 3. 标准工作流

### 3.1 写入 Notion 的标准三步

```
Step 1: 准备 Markdown 文本
  - 来自抓取器（如 url-md、qiaomu 等）
  - 来自 LLM 生成（如 DeepSeek、Claude 等）
  - 来自文件读取（.md 文件）

Step 2: 调用 mcp-mdnotion 转换
  - 输入：Markdown 字符串
  - 输出：Notion Blocks 数组（JSON）

Step 3: 调用 Notion MCP 写入
  - 用 create_page（新建页面）或 append_blocks（追加到现有页面）
  - 把 Step 2 的 blocks 数组传给 children 字段
```

### 3.2 完整代码示例（Pseudo-code）

```javascript
// Step 1: 拿到 Markdown
const markdown = await scrape_article(url);
// 或：const markdown = await llm.generate(prompt);

// Step 2: 转换为 Notion Blocks
const blocks = await mcp.call("markdown-to-notion", {
  tool: "convert",
  args: { markdown: markdown }
});

// Step 3: 写入 Notion
await mcp.call("notion", {
  tool: "create_page",
  args: {
    parent: { database_id: "your_db_id" },
    properties: {
      Title: { title: [{ text: { content: "文章标题" } }] }
    },
    children: blocks  // ← 关键：blocks 数组
  }
});
```

### 3.3 反模式（不要这样做）

❌ **直接把 Markdown 字符串塞进 paragraph block**

```javascript
// 错误！
await notion.create_page({
  children: [{
    type: "paragraph",
    paragraph: {
      rich_text: [{ text: { content: markdown } }]  // 整段 Markdown 当文本
    }
  }]
});
```

❌ 让 LLM 自己输出 Notion Block JSON

让 LLM 直接生成 Notion Block JSON 看似省事，但：
- LLM 容易写错 schema（字段名、嵌套结构）
- 浪费 token（JSON 比 Markdown 冗长 5-10 倍）
- 调试困难

❌ 手写 Markdown 解析器

"我自己 split 一下行就行了" —— 看起来简单，实际：
- 列表嵌套很难处理
- 代码块跨行很难处理
- 加粗 / 斜体的混合很难处理
- 表格基本不可能
- 永远比不过 martian 这种成熟库

---

## 4. 适用场景

### 4.1 立即受益的场景

- **内容采集 → Notion 笔记库**（本项目 AtN）
- AI 生成报告 → Notion 文档
- GitHub Issues / PRs → Notion 跟踪
- 会议转录 → Notion 会议纪要
- 博客 / Newsletter 草稿 → Notion 编辑
- Slack / 邮件摘要 → Notion 知识库

### 4.2 不同 Agent 的接入

| Agent | 接入方式 |
|-------|---------|
| Hermes | 加到 ~/.hermes/config.yaml 的 mcp_servers |
| Claude Code | 加到 ~/.claude/.mcp.json |
| Claude Desktop | 加到 claude_desktop_config.json |
| Cursor | 加到 .cursor/mcp.json |
| Windsurf | 加到 .windsurf/mcp.json |
| Antigravity | MCP 配置面板 |
| Gemini CLI | 通过 OpenAPI 或自定义 tool 注册 |
| n8n | 用 Mark2Notion 节点 |

---

## 5. 衍生原则：跨系统格式适配

这个案例揭示了一个更通用的设计原则：

> 永远不要假设两个独立系统的格式可以直接传递。  
> 在中间加一个适配器，做无损转换。

### 5.1 适配器模式的判断标准

需要适配器的信号：
- ✅ 源系统输出 A 格式，目标系统期望 B 格式
- ✅ 源系统的某些特性在目标系统里"消失"了
- ✅ 看到字面字符（`**`、`\n`、`<br>` 等）出现在最终输出里
- ✅ 任何"格式不对但内容对"的现象

### 5.2 其他常见的适配器需求

| 源 | 目标 | 适配器 |
|----|------|--------|
| Markdown | Notion | mcp-mdnotion / martian |
| Markdown | Slack | slack-blocks-builder |
| Markdown | Discord | discord embed builder |
| HTML | Markdown | turndown / markdownify / url-md |
| Notion | Markdown | notion-to-md |
| LLM JSON | Database row | schema validator + transformer |
| Webhook payload | Email | template engine |

### 5.3 设计建议

当你新建一个跨系统流水线时：

1. 先写出每一步的输入 / 输出格式

```
抓取器：Web URL → Markdown
LLM：Markdown → Markdown（重组）
Notion：???
```

2. 检查每个箭头两侧的格式是否匹配

```
抓取器输出 Markdown   →   LLM 输入 Markdown ✓
LLM 输出 Markdown     →   Notion 输入 Block ✗  ← 需要适配器
```

3. **在不匹配处加适配器**，而不是希望系统自己处理

4. **优先用现成的成熟库 / MCP**，不要自己实现

---

## 6. 故障排查

### 6.1 如果 Notion 显示了字面 ** 或 \*\*

**症状**：Notion 页面显示 `**加粗**` 而不是 **加粗**

**诊断**：
1. 你用了 mcp-mdnotion 吗？没有 → 安装它
2. 用了但还是这样 → 检查你给 mcp-mdnotion 的输入是不是已经被转义了
   - 跑一下：`echo "**test**" | mcp-mdnotion convert`
   - 如果这样能正常加粗，说明问题在你的 Markdown 输入端
3. LLM 输出有 \*\* 这种转义 → 让 LLM 不要转义，或在传给 mcp-mdnotion 前 unescape

### 6.2 如果列表 / 代码块没渲染

- 检查 Markdown 里列表项前是否有正确的 - 或 1.
- 检查代码块是否用 ``` 包围（三个反引号）
- 检查是否有空行分隔列表和段落

### 6.3 如果内容被截断

- Notion 单个 rich_text 限制 2000 字符
- martian 默认会自动分块（`truncate: false` 选项可关闭）
- 整个页面 children 限制 100 个 blocks（超长内容要分多次 append）

---

## 7. 参考资源

- **mcp-mdnotion**：https://github.com/aia-ops/mcp-mdnotion
- martian (底层库)：https://github.com/tryfabric/martian
- md2notion (Python 替代)：https://pypi.org/project/md2notion/
- notionmd (Go 替代)：https://github.com/brittonhayes/notionmd
- notion-to-md (反向转换)：https://github.com/souvikinator/notion-to-md
- **Notion API Block 文档**：https://developers.notion.com/reference/block

---

## 8. 学习价值

这个文档展示的不只是一个工具，而是一个**通用的工程原则**：

✓ 接口适配是软件设计的核心问题之一  
✓ 不要相信"应该能直接传"的直觉，要看实际格式  
✓ 优先复用成熟的适配器库，不要自己写  
✓ 看到字面字符 / 反斜杠出现在输出里，就是适配器缺失的信号  
✓ 在 AI Agent 系统里，这个原则适用于每一步管道  

记住：**Markdown 是程序员的格式，不是 Notion 的格式**。
