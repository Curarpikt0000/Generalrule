---
title: 静态网页表单邮件发送（FormSubmit.co）
source_lesson: L-2026-05-21-001
created: 2026-05-21
domain: frontend
keywords: [FormSubmit, 表单, 静态网页, 邮件, GitHub Pages, AJAX, 激活, Cache Buster]
applies_to: [全局, 静态网页项目]
status: active
related_rules: []
---

# 静态网页表单邮件发送（FormSubmit.co）

## 背景

GitHub Pages 等纯静态托管平台没有后端服务器，无法直接发邮件。
需要通过第三方表单转发服务（如 FormSubmit.co）来实现用户反馈收件功能。

## 核心规则

### 1. 使用标准 HTML POST 表单，而非 AJAX

**关键教训**：FormSubmit.co 的邮箱在第一次使用前必须完成激活。未激活时，
AJAX（fetch）接口会返回错误，导致 JavaScript 的 catch 捕获错误并显示"提交失败"。

**正确做法**：使用原生 HTML `form` 的 `action` POST 提交，而不是 AJAX：

```html
<form action="https://formsubmit.co/your@email.com" method="POST">
    <!-- 提交成功后重定向回原网站 -->
    <input type="hidden" name="_next" value="https://yoursite.github.io/">
    <!-- 防机器人蜜罐字段 -->
    <input type="text" name="_honey" style="display:none">
    <!-- 自定义邮件主题 -->
    <input type="hidden" name="_subject" value="用户反馈">
    
    <textarea name="message" required></textarea>
    <button type="submit">提交</button>
</form>
```

这样，第一次提交时 FormSubmit 会自动向目标邮箱发送激活邮件，用户点击激活后即可正常接收反馈。

### 2. 激活流程

1. 部署含表单的静态网页
2. 用户（或开发者自测）首次提交表单
3. FormSubmit 向目标邮箱发激活确认邮件
4. 点击邮件中的"Activate"链接
5. 激活完成，此后所有用户提交的反馈均会发到邮箱

### 3. 可用的隐藏字段

| 字段名 | 说明 |
|---|---|
| `_next` | 提交成功后重定向的 URL |
| `_subject` | 自定义邮件主题 |
| `_honey` | 蜜罐字段（`display:none`），防机器人 |
| `_captcha` | 设为 `false` 可关闭 CAPTCHA |
| `_template` | 邮件模板风格（`box`/`table`/`basic`） |

## 反模式（禁止行为）

- ❌ 用 AJAX（fetch）调用 FormSubmit 的 `/ajax/` 接口——邮箱未激活时必定报错
- ❌ 以为 AJAX 方式和标准 POST 方式效果相同——激活机制只对标准 POST 友好
- ❌ 忘记加 `_next` 参数——用户提交后会停在 FormSubmit 的默认感谢页，体验差

## 推荐做法

- ✅ 使用标准 HTML form POST 提交
- ✅ 加 `_next` 让用户提交后自动跳回原网站
- ✅ 首次部署后自己测试一遍，完成邮箱激活
- ✅ 使用 `_honey` 防机器人垃圾提交

## 相关知识

- [[cache-buster-versioning]] — 配合使用，确保用户加载最新代码

## 来源

- 原始项目：Tokyo_Child_Event_Webpage（意见反馈功能）
- 升级日期：2026-05-21
