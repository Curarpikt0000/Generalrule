---
title: 浏览器缓存与 Cache Buster 版本号
source_lesson: L-2026-05-21-002
created: 2026-05-21
domain: frontend
keywords: [Cache Buster, 缓存, 版本号, CSS, JS, GitHub Pages, 强制刷新]
applies_to: [全局, 静态网页项目]
status: active
related_rules: []
---

# 浏览器缓存与 Cache Buster 版本号

## 背景

静态网页部署更新后，用户浏览器往往仍然缓存旧版的 CSS/JS 文件，
导致新功能或样式没有生效。在 GitHub Pages 这类无后端项目中尤为常见，
因为无法通过服务器设置 `Cache-Control` 响应头。

## 核心规则

### 症状识别

当用户反映"我看到的样式/功能和你描述的不一样"时，首先怀疑浏览器缓存问题：
- 新增的 CSS class 不生效（样式还是旧的）
- 新加的 JS 事件绑定没有运行（点击没有反应）
- 页面看起来和代码不一致

### 解决方案：查询参数版本号（Cache Buster）

在 HTML 的 `<link>` 和 `<script>` 引用中加上版本号参数：

```html
<!-- 旧写法（浏览器可能使用缓存） -->
<link rel="stylesheet" href="assets/style.css">
<script src="assets/app.js"></script>

<!-- 新写法（版本号变化时浏览器必须重新下载） -->
<link rel="stylesheet" href="assets/style.css?v=20260521">
<script src="assets/app.js?v=20260521"></script>
```

浏览器把 `?v=20260521` 视为不同的 URL，因此会强制重新请求最新文件。

### 版本号命名规范

- 推荐：`?v=YYYYMMDD` 或 `?v=YYYYMMDD_N`（同一天多次发布时加序号）
- 每次有重大前端改动时更新版本号
- CSS 和 JS 版本号保持一致，方便管理

### 用户侧临时解决方案

在等待部署生效或需要立即验证时，告知用户：
- **Chrome/Safari（Mac）**：`Command + Shift + R` 强制刷新
- **Chrome/Edge（Windows）**：`Ctrl + F5`
- **最可靠**：使用浏览器**无痕/隐身窗口**打开，完全绕过缓存

## 反模式（禁止行为）

- ❌ 更新了代码但忘记更新版本号，导致用户长期看到旧版
- ❌ 让用户自行清除缓存而不说明方法
- ❌ 版本号使用随机字符串（难以追踪发布时间）

## 推荐做法

- ✅ 每次有前端改动就更新一次版本号（日期格式）
- ✅ 同一个 `index.html` 里的所有 CSS/JS 版本号保持统一
- ✅ 新功能上线后用无痕窗口自测，确认效果

## 来源

- 原始项目：Tokyo_Child_Event_Webpage（意见反馈功能部署后缓存问题）
- 升级日期：2026-05-21
