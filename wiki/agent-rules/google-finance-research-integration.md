---
title: Google Finance Beta「研究 AI」二次验证集成（议会模式 + 网页自动化）
domain: agent-rules
type: synthesis
keywords: [google-finance, gemini, playwright, chrome-profile, double-proof, 二次验证, hermes, finance-hero, web-automation, material-symbols]
tags: [google-finance, playwright, chrome-profile, web-automation, second-source, hermes, finance-hero]
source: Cowork 协作会话 2026-05-29（Claude Chao 与 Cowork Claude 共同实现 finance-hero 的 Google Finance Beta 二次验证管道）
sources:
  - https://www.google.com/finance/beta
  - https://playwright.dev/python/docs/auth#reuse-authentication-state
  - https://hermes-agent.nousresearch.com/docs/
  - Hermes 自带 browser_navigate / browser_click 工具实测
created: 2026-05-29
updated: 2026-05-29
last_updated: 2026-05-29
---

# Google Finance Beta「研究 AI」二次验证集成

> finance-hero 给议会综合裁决加一层独立来源验证。**按需触发**（用户说"再查一下" / "double check" 等关键词），把同一问题抛给 Google Finance Beta 的"研究"AI（Gemini Deep Research 嵌入），抓答案做对账。
> 这是议会模式架构里第一个"网页自动化外部源"的实例化，本条目沉淀全部架构决策 + 7 大踩坑。

---

## 一、为什么不用 API，要用网页自动化

按 §3 五步链路（Rule → Wiki → Skill → 公网 → 自己写）评估完所有 API 选项后得到的结论：

- **Google 官方 Finance API 早在 2012 年被关闭**——不存在"用 Google 账号就能调"的 REST/gRPC 接口
- 唯一"半官方"路径是 Google Sheets `GOOGLEFINANCE()` 函数 + Sheets API——但函数覆盖在最近几年被 Google 持续弱化
- yfinance / Alpha Vantage 等是**Yahoo / 第三方**，不是 Google
- 用户**已登录 Google 账号**的浏览器，去 google.com/finance/beta 能看到"研究"AI（实际是 Gemini Deep Research 内嵌）——质量极高、自带网页引用，**而且免费**

所以最终方案：**Playwright 复用用户已登录的 Chrome profile**，去 Google Finance Beta 输入问题、等 AI 答完、抓取文本。

## 二、为什么是 Playwright 而非 Hermes 自带 browser

实测 Hermes 内置 `browser_navigate` 没有持久化 Google 登录 session——访问 google.com/finance/beta 落地后 accessibility tree 显示右上角是 Sign in 按钮而不是用户头像。两条解决路径对比：

| 路径 | 优点 | 缺点 |
|---|---|---|
| **A. 让 Hermes browser 走 Google 登录流** | 不需要本地装 Playwright | Google 检测自动化登录可能锁号 / 频繁 2FA / session 短期过期 |
| **B. Playwright + 用户已存 Chrome cookies**（采用）| 100% 复用已登录 session、Google 看不出异常 | 需要本地装 Playwright + cp Chrome profile |

最终走 B。**B 是干净的，A 是脆的**。

## 三、7 大踩坑（按时间序，给后续 agent 直接照搬）

### 踩坑 1 · 沙箱 sync.sh 漏同步 tools/

蓝图 `tools/gfinance_research.py` 写在沙箱里没问题，**但 sync.sh 没把 tools/ 列在 rsync 路径里**，导致用户 profile 那边 `python3 ~/.hermes/profiles/finance/tools/gfinance_research.py` 找不到文件。

**教训**：写新 helper 工具时立刻同步更新 sync.sh 的 rsync 列表。**模板（sync.sh.template）应永远包含 tools/ 这一档**，宁可多 sync 空目录也别漏。

### 踩坑 2 · zsh history expansion 吃掉 `!r`

最初的"找 Chrome profile 文件夹名"脚本用了 Python f-string 的 `{name!r:20s}` 格式化语法。zsh 在解析含 `!` 的命令时触发 history 展开（`!r` = 上一条以 r 开头的命令），整个命令报 `zsh: no such word in event` 拒绝执行。

**教训**：给用户写**直接粘贴跑**的 zsh 命令时，禁用 `!` 字符（用 heredoc + 单引号包裹脚本体可彻底规避）。或把 Python 输出格式从 f-string 改成 % 风格 / .format()。

### 踩坑 3 · Chrome profile 文件夹名不是 "Default"

我默认 cp `~/Library/Application Support/Google/Chrome/Default/*` 到目标——失败，因为用户有 5 个 Chrome 账户，主用账号目录名是 `Profile 6` 而非 `Default`。

**正解（永远先查文件夹名）**：

```bash
python3 << 'PYEOF'
import json, os
p = os.path.expanduser('~/Library/Application Support/Google/Chrome/Local State')
d = json.load(open(p))
for name, info in d.get('profile', {}).get('info_cache', {}).items():
    email = info.get('user_name', '(无)')
    display = info.get('name', '(无)')
    print(f'  文件夹名: {name:20s}  显示名: {display:30s}  邮箱: {email}')
PYEOF
```

Chrome `Local State` 这个 JSON 文件含所有 profile 文件夹名 ↔ 邮箱映射，比手动 ls 猜文件夹名可靠。

### 踩坑 4 · URL /beta 是必要但不充分——必须点 UI 上的 Beta toggle

`https://www.google.com/finance/beta` 这个 URL 让页面**外观**进入 Beta 版，**但 AI 提交功能依赖 UI 状态切换**——右上角的"经典版 / ✓ Beta 版" toggle 实际是控制 AI 激活的开关。

直接 navigate 进 /beta 后**还需要程序点一次"Beta 版"按钮**才能解锁 AI 提交。**幂等处理**：检查是否已有 `✓` 标记或 `aria-pressed=true`，避免重复点反而切回经典版。

```python
beta_elem = page.locator('button:has-text("Beta 版")').first
if "✓" not in beta_elem.inner_text():
    beta_elem.click()
```

### 踩坑 5 · Gemini chat 风格 UI 里 Enter 不一定提交

输入框是 chat 风格的 textarea：

- Enter 有时被解析为换行（特别是 Shift+Enter / IME 输入态下）
- 真正提交按钮是**输入框右侧的"上箭头"按钮**

最稳做法：**先找 send 按钮点；找不到才退到 Enter**。但实测里 Enter 居然也工作了（`debug_transition_detected: true`）——所以两条都留着作为保险。

```python
# 优先点 send 按钮
send_button_candidates = [
    'button[aria-label*="发送"]', 'button[aria-label*="Send"]',
    'button:has-text("Send")', 'button[aria-label*="询问"]',
]
# 找不到再 Enter fallback
```

### 踩坑 6 · 答案不在 aria-live="polite"，是在 [role="region"]

最大的迷惑——`[aria-live="polite"]` selector 拿到的永远是字符串 `"已就绪"`（Ready），从不更新。是给读屏者的状态公告区，**不是答案内容**。

真正的答案在右侧研究面板的 `[role="region"]`（页面上第二个 region），里面同时含：
- 用户问题
- "N 个网站" 引用计数
- 时间戳
- AI 答案正文

**正解**：用"问题文本"过滤 `[role="region"]`——含用户问题前缀且文本长度 > 80 字符的那个就是答案区：

```python
def find_answer_region(page, question):
    regions = page.locator('[role="region"]')
    cands = []
    for i in range(regions.count()):
        txt = regions.nth(i).inner_text()
        if question[:15] in txt and len(txt) > 80:
            cands.append((len(txt), i, regions.nth(i)))
    cands.sort(key=lambda x: -x[0])  # 选最长
    return (cands[0][2], cands[0][1]) if cands else (None, None)
```

### 踩坑 7 · Material Symbols 字体让 inner_text() 出现"图标名"

Google 用 Material Symbols 图标字体。一个按钮的 HTML 内容可能是字符串字面量 `expand_content`，浏览器渲染时字体把它显示为对应图标（展开箭头）——但 `inner_text()` 拿到的还是字符串 `expand_content`。

副作用：
- 答案 region 的文本里夹杂 `link` / `edit_square` / `prompt_suggestion` / `arrow_upward` 这些图标名
- 按钮 selector `button:has-text("展开")` 可能匹中，但 `button:has-text("expand_content")` 也能匹中（同一按钮）

**清洗规则**（写进 helper）：

```python
_UI_NOISE = {
    'link', 'expand_content', 'collapse_content', 'edit_square',
    'notes_spark', 'prompt_suggestion', 'open_in_new',
    'arrow_upward', 'arrow_downward', '展开', '收起',
    '发起新消息串', '会话历史记录', '研究',
}
# 按行剥离 UI noise
```

---

## 四、最终架构 · 完整流程图

```
[Telegram 用户消息 含触发词 "再查一下" / "double check"]
                │
                ▼
[FiHeroBot 正常出议会综合裁决（不变）]
                │
                ▼
[首选 A：Hermes 自带 browser_navigate]
   未登录 ────────┐
                ▼
[回退 B：python3 ~/.hermes/profiles/finance/tools/gfinance_research.py "<question>"]
                │
                ▼
[Playwright launch_persistent_context(user_data_dir=~/.gfinance-chrome-profile)]
                │
                ▼
[访问 google.com/finance/ → 点 Beta toggle → fill 问题 → 点 send / Enter]
                │
                ▼
[轮询 [role="region"][1] 直到文本 6 秒无变化（流式生成完毕）]
                │
                ▼
[清洗 UI noise + 提取 sources_count → 返回 JSON]
                │
                ▼
[bot 把 Google AI 答案 + 议会答案做"主持人对账"输出]
```

## 五、SOUL.md 触发设计（按需，不污染常规问答）

写进 finance-hero/SOUL.md §"二次验证模式"：

- **触发关键词**：`double check / 再查一下 / 再查一遍 / Google 验证 / proof twice / 另一个来源`
- **没说这些词 → 绝对不调**（节省时间和 token）
- 输出格式固定：议会综合裁决 + `🔎 Google Finance 二次验证` 段 + 主持人对账（一致点 / 分歧点 / 综合结论）+ §2.10 警示

## 六、关键文件清单

| 文件 | 作用 |
|---|---|
| `finance-hero/tools/gfinance_research.py` | Playwright helper 脚本 |
| `finance-hero/SOUL.md` §"二次验证模式" | 触发词 + 工作流 + 输出格式定义 |
| `finance-hero/sync.sh` | 必须含 tools/ 同步（**别漏**） |
| 用户本地 `~/.gfinance-chrome-profile/` | Chrome cookies 副本（cp 自 Profile 6） |

## 七、一次性部署清单（用户本地）

```bash
# 1. 装 Playwright（一次性）
pip3 install playwright

# 2. 找出存目标 Google 账号的 Chrome profile 文件夹名（见踩坑 3 的 Python 命令）

# 3. 复制 profile 到独立目录（避免和正在用的 Chrome 冲突）
CHROME_SRC="$HOME/Library/Application Support/Google/Chrome"
PROFILE_NAME="Profile 6"   # 替换成实际文件夹名
mkdir -p ~/.gfinance-chrome-profile/Default
rsync -a \
  --exclude='Cache' --exclude='Code Cache' --exclude='GPUCache' \
  --exclude='Service Worker' --exclude='IndexedDB' --exclude='File System' \
  "$CHROME_SRC/$PROFILE_NAME/" ~/.gfinance-chrome-profile/Default/

# 4. 跑连通测试
python3 ~/.hermes/profiles/finance/tools/gfinance_research.py \
    "今天美股是不是在高位？" \
    --chrome-profile ~/.gfinance-chrome-profile \
    --screenshot /tmp/gfinance_test.png
```

## 八、未解决项 / 待优化

- ⚠️ `sources_count` 提取失败：Google 把引用收进"全部显示"折叠时，inner_text 拿不到"N 个网站"的明文。**暂时影响小**——`answer_text` 里有具体引用源（U.S. Bank / CNBC / Trading Economics 等）。后续可改用 `aria-label` 或专门 selector 直接数引用元素。
- ⚠️ 展开按钮 selector 仍未匹中：拿到的 raw_text 1494 字已是完整答案，**不展开也能用**。如果未来 Google 默认渲染更少，需要再调。
- ⚠️ Headful 模式有 Chrome 窗弹出：用户多次触发会很烦。可选改 `--headless` 但 Google 反自动化可能识别。退而求其次：把 Chrome 窗放到独立 Space / Mission Control 不打扰。

## 九、给后续 agent 接手的话

如果你接到"给某个 hero 加另一个第三方网页 AI 验证源"（如 Perplexity / Claude.ai / 微软 Copilot Finance）——本条目里的 7 大踩坑 80% 通用，特别是：

1. **永远先 cp 用户已登录的浏览器 profile**，别让 bot 在自己沙箱里走登录流程
2. **页面 UI 状态可能是除 URL 之外的第二个准入门**（如 Beta toggle）
3. **永远先做"候选 region dump"再锁定 selector**，别基于猜测设 selector
4. **Material Symbols / 图标字体陷阱**：所有 Google 系产品都用，按钮 selector 既要 text 也要 aria-label
5. **流式答案要轮询稳定，不是单次读**

完整脚本骨架直接借用 `tools/gfinance_research.py`，改 URL + selector 即可。

---

## 来源

- Cowork 协作会话 2026-05-29（finance-hero 二次验证集成）
- Hermes Agent Docs: https://hermes-agent.nousresearch.com/docs/
- Playwright Python 文档（persistent context）: https://playwright.dev/python/docs/auth
- Google Finance Beta: https://www.google.com/finance/beta（实测页面）
- 议会模式架构: [[finance-hero-distillation]]

## 相关页面

- [[finance-hero-distillation]] —— finance hero profile 架构与议会模式底座
- [[five-step-pipeline]] —— 本集成的 §3 五步链路决策记录
- general-global-rule.md §2.5（显式暴露冲突）、§2.10（显式失败）、§7（凭证管理：Chrome profile cookies 不进 git）
