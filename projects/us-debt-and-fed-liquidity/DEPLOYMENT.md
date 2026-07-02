# 部署步骤（手把手）

> 你只需要做 **2 件事**：① 申请 FRED key 并填到 `.env` ② 把 `HERMES_WORKER_BOOTSTRAP.md` 内容粘贴给一个 Hermes worker。
>
> 完成后 Hermes 每天自动跑。

---

## 第 1 步：申请 FRED API Key（5 分钟，免费）

1. 打开浏览器访问：https://fredaccount.stlouisfed.org/apikeys
2. 用邮箱注册一个 St. Louis Fed 账号（免费）
3. 登录后点 "Request API Key"，填用途（写 "Personal market monitoring" 即可），提交
4. 会立刻得到一串 32 位字符串，类似：`abcdef1234567890abcdef1234567890`
5. **复制保存好**

---

## 第 2 步：创建 `.env` 文件（2 分钟）

打开 Mac 终端（Spotlight 搜 "终端" 或 "Terminal"），逐行粘贴：

```bash
# 进入项目目录
cd "/Users/chaojin/hermesagent/US Debt and Fed Liquidity/美债收益率和Fed中美日流动性日报"

# 把模板复制成真实 .env 文件
cp .env.example .env

# 用系统默认编辑器打开
open -e .env
```

会弹出 TextEdit 窗口，你看到的内容大概是：

```
FRED_API_KEY=your_fred_key_here
# DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

把 `your_fred_key_here` 换成你第 1 步拿到的 key，例如：

```
FRED_API_KEY=abcdef1234567890abcdef1234567890
```

**`DEEPSEEK_API_KEY` 那行保持注释不动**（前面的 `#` 不要删）。Hermes 后端自己已经是 DeepSeek 了，不需要额外的 key。

保存（⌘+S），关闭窗口。

✅ 验证：在终端跑一下，应该看到你刚填的 key
```bash
cat .env | grep FRED_API_KEY
```

---

## 第 3 步：让 Hermes 接管（5 分钟）

打开一个**新的 Hermes worker 对话**，把 `HERMES_WORKER_BOOTSTRAP.md` 整个文件的内容**完整复制粘贴**进去发送。

Hermes 会自动：
1. 读懂这个项目的结构
2. 把 7 个 workflow 注册成 cron
3. 立刻跑一次首日全量数据（让你今天就能看到 Notion 里有内容）
4. 报告任何配置问题

---

## ❓ 出问题怎么办

| 现象 | 原因 | 解决 |
|------|------|------|
| FRED 调用 403 | API key 没填或填错 | 重新打开 `.env` 检查，没有空格、引号 |
| Notion 写入失败 | Notion MCP 在 Hermes 没配 | 让 Hermes 跑 `notion-search` 测试一下 |
| 抓不到日债 / PBoC | 反爬被拦 | 让 Hermes 切换成 MoF Japan 官方 CSV 源 |
| Hermes 把 prompt 当聊天 | 没在对话里说明是"长期 workflow" | 把 BOOTSTRAP 文件**整个**贴上，不要节选 |
| Notion 字段对不上 | 你手动改过 DB schema | 让 Hermes 重新读 `notion_db_ids.json` |

---

## 📊 验证清单（首日跑批后）

打开 Notion 两个 page，检查：

**🚸 经济危机预警**：
- [ ] A1 (UST_Yields_Daily) 有今天一行，5 个期限都有数字
- [ ] A5 (Fed_Liquidity_Daily) SOFR_Sprd_bp 有值，风控状态自动着色
- [ ] A7 (Daily_Risk_Report) 有今天一行，AI 短评不为空，点开有完整长分析

**🏧 中美日央行**：
- [ ] B2 (PBoC) 有今天一行（如果是中国工作日）
- [ ] B3 (BoJ) 有今天一行
- [ ] B6 (CN_JP_Daily_Analysis) AI 短评 + 长分析齐全

如果某行"运行状态" = ❌失败，看 logs/ 目录的当日日志。
