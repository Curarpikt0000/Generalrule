---
title: GitHub Actions 定时任务中 GitHub API 限流防护
domain: engineering
type: concept
keywords: [github-actions, github-api, rate-limit, github-token, secrets]
tags: [github-actions, github-api, rate-limit]
source: L-2026-06-06-001
sources: [conversation-58ba548d-76d0-41b8-adb1-b9b24483e883]
created: 2026-06-06
updated: 2026-06-06
last_updated: 2026-06-06
---

# GitHub Actions 定时任务中 GitHub API 限流防护

## 核心原则

> **在 GitHub Actions 执行的定时同步或数据抓取脚本中，任何向 GitHub API（如 Contents API, Repos API）发起的请求都必须携带认证 Token。**

未认证的 API 请求限流为 **60次/小时**（且同一个 Actions 出口 IP 池会共享此配额，极易在定时段被挤爆），使用 Token 认证后限流将大幅提升至 **1000次/小时**。

---

## 错误行为模式 (Anti-Patterns)

1. **依赖空环境默认请求**
   Python 脚本调用 GitHub API 仅读取自定义的 `GH_PERSONAL_TOKEN`，但在 Workflow 部署时没有在 `env` 中声明或注入该 Token，导致请求在 Actions 运行环境退化为“未认证请求”：
   ```python
   # 脚本读取
   GITHUB_TOKEN = os.getenv("GH_PERSONAL_TOKEN")
   # 若未注入，GITHUB_TOKEN 变成 None，发送 HTTP 请求时不携带 Authorization header
   ```

2. **静默失败或吞错**
   API 限流失败（HTTP 403 Rate Limit Exceeded）被 `try/except` 吞掉，导致后续文件写入或数据提取异常没有被 Fail Loud 机制抛出，或者被忽略导致数据出现空值。

---

## 正确做法 (Best Practices)

### 1. 脚本端增加降级兼容
在加载 Token 时，除支持自定义 Token 境外，同时兜底读取 GitHub Actions 原生提供的 `GITHUB_TOKEN` 环境变量：
```python
# 脚本端读取双重环境变量
GITHUB_TOKEN = os.getenv("GH_PERSONAL_TOKEN") or os.getenv("GITHUB_TOKEN")

# 请求构建
headers = {"Cache-Control": "no-cache", "Pragma": "no-cache"}
if GITHUB_TOKEN:
    headers["Authorization"] = f"token {GITHUB_TOKEN}"

response = requests.get(api_url, headers=headers)
response.raise_for_status() # 必须显式抛出异常
```

### 2. 工作流中注入 GITHUB_TOKEN
在 `.github/workflows/*.yml` 运行步骤中，利用 Actions 的系统内置密钥 `${{ secrets.GITHUB_TOKEN }}` 注入环境：
```yaml
      - name: Run Sync Script
        env:
          NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
          GH_PERSONAL_TOKEN: ${{ secrets.GITHUB_TOKEN }} # 显式注入系统 Token
        run: python sync_cme_to_notion.py
```

---

## 相关页面
* [[notion-dedup-fail-loud]]
* [[url-fidelity]]
