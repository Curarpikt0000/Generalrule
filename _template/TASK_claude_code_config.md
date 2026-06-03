# Claude Code 配置任务

> 给 Claude Cowork 的。在 UB 电脑上配置 Claude Code 遵守全局规则。

---

## 任务目标

让 UB 电脑上的 Claude Code 能和本地 Mac 的 Claude Code 一样：
1. 遵守通用全局规则
2. 学习到 lesson 后写入 Wiki 并 git push

## 具体步骤

### Step 1: Clone 仓库

```bash
mkdir -p ~/UBAntigravity\ Projects/
git clone git@github.com:Curarpikt0000/Generalrule.git ~/UBAntigravity\ Projects/UBGeneralrule/
```

### Step 2: 替换内部路径引用

clone 下来的文件内部所有 `~/Antigravity Projects/Generalrule/` 需替换为 `~/UBAntigravity Projects/UBGeneralrule/`：

```bash
cd ~/UBAntigravity\ Projects/UBGeneralrule/
# .md 文件中的路径引用
find . -name '*.md' -exec sed -i '' 's|~/Antigravity Projects/Generalrule/|~/UBAntigravity Projects/UBGeneralrule/|g' {} +
# 其他文本文件
find . -name '*.yaml' -exec sed -i '' 's|~/Antigravity Projects/Generalrule/|~/UBAntigravity Projects/UBGeneralrule/|g' {} +
find . -name '*.yml' -exec sed -i '' 's|~/Antigravity Projects/Generalrule/|~/UBAntigravity Projects/UBGeneralrule/|g' {} +
```

### Step 3: 设置 Claude Code 项目规则

配置 Claude Code 的全局项目规则文件，使其在新项目或任何目录下都能读到通用全局规则。

方案：
- `~/.claude/projects.json` 或 `~/.claude/global_instructions.md` 配置
- 目标：Claude Code 打开任何项目时，都能读到 `~/UBAntigravity Projects/UBGeneralrule/antigravity/general-global-rule.md`

具体检查：
1. 检查 UB 电脑上 Claude Code 是否已安装
2. 检查 `~/.claude/` 目录结构
3. 设置全局指令（global instructions），让 Claude Code 在每次启动时自动加载 `general-global-rule.md`
4. Claude Code 的全局指令方法：`claude config set globalInstructions <path>` 或修改 `~/.claude/config.yaml`

### Step 4: 验证 Claude Code 可读取规则

在 UB 电脑上随便开一个项目目录（或空目录），运行 `claude -p "请读取你的全局规则文件并告诉我它是什么"`，看能否正确返回 `general-global-rule.md` 的内容。

### Step 5: 配置 Wiki 写入能力

让 Claude Code 能写入 Wiki 并 push：

1. 确认 `~/UBAntigravity Projects/UBGeneralrule/` 的 git remote 正常
2. 确认 SSH key 已配置，能 push 到 `git@github.com:Curarpikt0000/Generalrule.git`
3. 在 Claude Code 中配置一个可用的命令（如 `/wiki-ingest`）或 workflow，让它可以：
   - 创建/更新 `wiki/<domain>/<topic>.md` 文件
   - 更新 `wiki/index.md`
   - 执行 `cd ~/UBAntigravity Projects/UBGeneralrule && git add -A && git commit -m "[Wiki] <domain>: <desc>" && git push`

### Step 6: 测试完整链路

1. 让 Claude Code 写一条测试 lesson 到 Wiki
2. 确认它能够 git push 成功
3. 删除测试内容

---

## 注意事项

- `git push` 是不可逆操作，必须先确认 SSH key 正确配置
- 第一次 git push 前记得先 `git pull --rebase`
- 如果 SSH 配置不对，先帮用户检查 `~/.ssh/id_ed25519` 或 `~/.ssh/id_rsa` 是否存在、对应 key 是否在 GitHub 上注册
