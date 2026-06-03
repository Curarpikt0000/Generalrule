# Antigravity（Claude Desktop）配置任务

> 给 Claude Cowork 的。在 UB 电脑上配置 Claude Desktop 的 Antigravity 系统。

---

## 任务目标

让 UB 电脑上的 Antigravity（基于 Claude Desktop Custom Instructions + Workflows）遵守与本地 Mac 相同的通用全局规则，并能将 lesson 写入 Wiki 并 git push。

## 背景（给 cowork 读）

Antigravity 是用户基于 Claude Desktop 自己搭建的一套结构化 Agent 系统。它由三部分组成：
1. **Custom Instructions（自定义指令）**：Claude Desktop 的 Personality 设定，指向通用全局规则
2. **Workflows（工作流）**：.md 文件定义的五阶段 SOP
3. **Customizations（自定义设置）**：Antigravity 目录下的 own rules 定义

本地 Mac 的 Antigravity 结构：
- 全局规则：`~/Antigravity Projects/Generalrule/antigravity/general-global-rule.md`
- Custom Instructions 指向这个路径
- 有 Workflows 对应五阶段（探索→计划→执行→验证→沉淀）

## 具体步骤

### Step 1: 确认 Antigravity 目录结构

在 UB 电脑上，用户说装了 Antigravity。先检查结构：

```bash
# 检查 Antigravity 相关的目录
ls ~/UBAntigravity\ Projects/
# 检查 Claude Desktop 的 Custom Instructions 设置
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json 2>/dev/null || echo "config not found"
# 检查 Antigravity 本身的结构
# 可能有一个独立的 Antigravity 配置目录（用户说装了，需要确认位置）
```

### Step 2: 如果已有 Antigravity 项目文件

大概率 Antigravity 自己的项目文件里引用了 `~/Antigravity Projects/Generalrule/` 路径。需要替换为 `~/UBAntigravity Projects/UBGeneralrule/`。

做法：
```bash
# 找到 Antigravity 相关的配置/项目文件
# 搜索所有 .md/.json/.yaml 文件中的旧路径引用
grep -r "Antigravity Projects/Generalrule" ~/UBAntigravity\ Projects/ 2>/dev/null || echo "No matches in UB projects"
grep -r "Antigravity Projects/Generalrule" ~/Library/Application\ Support/Claude/ 2>/dev/null || echo "No matches in Claude config"
# 如果找到了，全部替换
```

### Step 3: 配置 Claude Desktop Custom Instructions

Claude Desktop 的 Custom Instructions 决定了 Antigravity 的行为。用户需要它的 Personality 指向 `general-global-rule.md`：

1. 打开 Claude Desktop → Settings → Custom Instructions
2. 在 Custom Instructions 中包含以下内容：

> 你是 Chao 的长期 AI 协作助手（公司电脑版）。项目根目录：`~/UBAntigravity Projects/`。
> 
> 遵守通用全局规则：`~/UBAntigravity Projects/UBGeneralrule/antigravity/general-global-rule.md`
> 
> Wiki 知识库：`~/UBAntigravity Projects/UBGeneralrule/wiki/`
> 
> 学习到的 lesson 请写入 Wiki，然后执行 git push。

3. 或者在 Claude Desktop 的 `claude_desktop_config.json` 中配置 custom instructions（如果支持）

### Step 4: 配置 Workflows

Antigravity 的五阶段 Workflow（探索、计划、执行、验证、沉淀）需要能在 UB 上正常工作。
特别是最后一个阶段（LEARN/沉淀）需要能写入 Wiki 并 git push。

```bash
# 找到 Antigravity 的 Workflows 目录（可能在某些自定义路径下）
# 确认每个 workflow 中的路径引用都被 UB 化
```

### Step 5: 验证

打开 Claude Desktop，问它：

> "请读取你的通用全局规则文件，告诉我它位于哪里，以及它包含什么核心内容。"

验证返回的内容正确指向 UB 路径。

### Step 6: 测试 Wiki 写入

让 Claude Desktop 写一条测试内容到 Wiki，确认能 git push 成功。

---

## 注意事项

- Claude Desktop 不能直接执行终端命令，所以 Wiki push 可能需要一个脚本或快捷键
- 如果 Antigravity 使用 Workflows 来执行终端操作，确认 `git push` 的 SSH 权限已配置
- Custom Instructions 中路径要用绝对路径
- 修改 Claude Desktop config 时需要重启 Claude Desktop 才能生效
