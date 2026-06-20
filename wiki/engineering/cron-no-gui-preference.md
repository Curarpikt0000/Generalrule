---
title: Cron Job — GUI 方案不可靠，优先纯脚本 no_agent 模式
domain: engineering
keywords: [cron, computer_use, browser, playwright, no_agent, gui, headless]
source: hermes-cron-architecture-lesson-20260620
created: 2026-06-20
last_updated: 2026-06-20
---

# Cron Job 架构：GUI 方案不可靠，优先 no_agent 纯脚本模式

## 教训

凡是需要 **automated / scheduled** 执行的任务，不要依赖任何 GUI 交互方案。

| 方案 | 适用场景 | 可靠度 |
|------|----------|--------|
| computer_use（操控本地 Chrome/Firefox） | 交互式调试、用户在场的一次性任务 | ❌ 低（后台无 GUI 环境） |
| browser 工具（browser_navigate/click） | 无 WAF 的普通网页抓取 | ⚠️ 中（WAF 拦截 datacenter IP） |
| Playwright stealth 脚本 | 有 WAF 的网站抓取 | ✅ 高 |
| curl + 公开 API | 有公开 API 的数据源 | ✅ 最高 |
| no_agent + 本地脚本 | 任何纯数据处理/写入任务 | ✅ 最高 |

## computer_use 的局限

`computer_use` 工具设计为 **background co-work**（用户和 agent 共用同一台 Mac），但在以下场景不可靠：

1. **Chrome 不在当前 Space** — cua-driver 无法 capture 窗口内容（所有元素 bounds = [0,0,0,0]）
2. **无显示器 session** — cron job 通常运行在后台，无屏幕可 capture
3. **Accessibility permissions 缺失** — 没有辅助功能权限时无法读取 AX tree
4. **窗口尺寸为 0x0** — 最小化或隐藏窗口导致 vision mode 返回空

**结论：** computer_use 只适合用户在场、Chrome 在前台可见的交互式操作。不要用于 cron job。

## browser 工具的局限

Hermes 内置的 browser_navigate/browser_click 使用 Browserbase 的 **datacenter IP**，会被 WAF 拦截（如 SHFE 的长亭 SafeLine，返回 JS challenge 页面）。

**绕过条件：**
- 网站无 WAF → browser 工具 OK
- 网站有 WAF → browser 工具无效，需 Playwright stealth 或 residential proxy

## 最佳实践：no_agent 模式

```json
{
  "job_id": "xxx",
  "name": "shfe_weekly_inventory",
  "schedule": "0 9 * * 6",
  "script": "shfe_weekly_notion_wrapper.sh",
  "no_agent": true
}
```

**优势：**
- 0 token 消耗 — 不调用 LLM
- 稳定 — 纯 shell + Python 执行，不依赖外部服务
- 可调试 — stdout 就是输出，失败就是非零退出码
- 低延迟 — 无需等待 LLM 响应，脚本直接出结果

**环境变量处理：**
no_agent 模式中 script 的 stdout 直接作为消息发送。
需要 API key 时，用 bash wrapper 先 source `.env` 再 exec Python。

## 判断准则

Scheduled task 选型优先级：

```
有公开 API 的 → curl/requests 直连
无 API 但无 WAF → browser 工具 或者 playwright headless
无 API + 有 WAF → playwright stealth (headless=True)
纯数据处理 → no_agent 模式 + Python 脚本
需要 LLM 参与 → agent 模式
```
