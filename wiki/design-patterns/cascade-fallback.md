# 付费墙爬虫：级联降级设计模式 (Cascade Fallback Pattern)

- **来源 lesson ID**: qiaomu-anything-to-notebooklm
- **创建日期**: 2026-05-03
- **适用领域**: 爬虫、反爬对抗
- **关键词**: cascade fallback, paywall bypass, anti-crawler, content scraping, graceful degradation

---

## 核心设计理念

> 不要赌一个方法能对所有网站有效。
> 而是准备 N 个互补的策略，按"成本 → 成功率"的递增顺序尝试。
> 快速方法失败时，自动升级到更复杂但更可靠的方法。

适用于解决"网站反爬虫"这种对抗性问题。

---

## 三层抽象设计

### 第 1 层：策略库（Strategy Layer）

一套互补的、独立的绕过策略，每个针对不同的反爬虫机制：

| 策略 | 针对反爬机制 | 成本 | 成功率 |
|------|-----------|------|--------|
| 代理服务 | IP 黑名单 | 极低（网络调用） | 60% |
| Bot UA 伪装 | User-Agent 检测 | 低（HTTP 头修改） | 75% |
| Referer 欺骗 | 流量来源检测 | 低 | 75% |
| JSON-LD 提取 | JS 渲染隐藏 | 低（HTML 挖掘） | 70% |
| AMP 降级 | 主站付费墙 | 中（URL 重构） | 80% |
| 存档服务 | 所有反爬 | 中（依赖第三方） | 70% |
| Google Cache | 所有反爬 | 中 | 65% |
| 真实浏览器 | 所有反爬 | 高（资源密集） | 95% |

### 第 2 层：域名分类（Domain Classification）

不同网站采用不同的反爬手段，所以要预先分类：

```
GOOGLEBOT_FRIENDLY = { "wsj.com", "ft.com", "economist.com", ... }
BINGBOT_FRIENDLY   = { "haaretz.com", "nzherald.co.nz", ... }
SOCIAL_REFERER_ALLOWED = { "law.com", "law360.com", ... }
AMP_AVAILABLE      = { "wsj.com", "bostonglobe.com", ... }
ALL_PAYWALL        = { 包含上面所有 + 更多 }
```

### 第 3 层：验证层（Validation Layer）

不能盲目相信获取的内容，须多维度验证：

```python
def is_valid_content(content):
    if line_count < 8 or char_count < 500:
        return False
    if "404 Not Found" in content or "Access Denied" in content:
        return False
    if "subscribe to continue" in content or "paywall" in content:
        return False
    if "CAPTCHA" in content or "Cloudflare" in content:
        return False
    return True
```

---

## 核心流程

### 快速通道（High Priority）— < 1 秒
1. 代理服务 1（r.jina.ai）→ 验证 → 成功返回 / 继续
2. 代理服务 2（defuddle.md）→ 验证 → 成功返回 / 继续
3. 进入中速通道

### 中速通道（Medium Priority）— 1~5 秒
1. 查询 GOOGLEBOT_DOMAINS → 发送 Googlebot UA + IP + Referer → HTML→文本转换
2. 查询 BINGBOT_DOMAINS → 同上
3. 检查 AMP 可用性 → 尝试 AMP 变体
4. Social Referer 欺骗（Facebook, Twitter）
5. 进入慢速通道

### 慢速通道（Fallback）— 5~60 秒
1. archive.today（公共存档）→ 有 CAPTCHA 返回码 75 让人工验证
2. Google Cache（webcache.googleusercontent.com）
3. 真实浏览器（Playwright / Puppeteer），成功率 > 95%

---

## 关键技术技巧

### JSON-LD 挖掘
许多新闻媒体在 HTML 中嵌入 `application/ld+json` 用于 SEO，其中包含完整的 `articleBody`。网站给用户隐藏付费墙，但 SEO 数据必须在 HTML 里。

### User-Agent + IP + Referer 三重伪装
单个维度伪装有风险，三个维度同时伪装才能通过严格检查。

### AMP 版本降级
AMP 页面为了速度，反爬虫逻辑更弱，尝试 `/amp`, `?outputType=amp`, `.amp.html` 等变体。

### Public Archive 作为第三方来源
archive.today / archive.org 已经存档的内容可以作为备份获取。遇到 CAPTCHA 时返回特殊码 75。

### Google Cache 作为缓存备份
`webcache.googleusercontent.com/search?q=cache:<URL>` 不依赖第三方。

### Real Browser Fallback
最后的保险，启动真实浏览器渲染 JS，成功率接近 100%，但资源密集。

---

## 适应性设计

四个维度的适应性：
- **域名适应性**：根据域名选择优先策略
- **内容适应性**：发现有 JSON-LD articleBody 则立即返回
- **错误适应性**：超时提前返回，CAPTCHA 转人工
- **成本/收益适应性**：第 1-3 次迭代快速尝试，4-5 中速，6-7 高成本

---

## 学习价值

- **对抗性问题的通用解法**：准备多个备选而非赌单一方法
- **成本优化**：按时间成本升序排列尝试
- **防御性编程**：多维度验证所有返回内容
- **域名特化**：根据已知特征选择最优策略
- **优雅降级**：失败时自动升级到更复杂的方法
- **人机协作**：CAPTCHA 等场景识别后交由用户处理

---

## 参考

- 原始实现：`qiaomu-anything-to-notebooklm/scripts/fetch_url.sh`
- 灵感来源：Bypass Paywalls Clean（开源浏览器插件）
- 相关概念：Cascade Fallback Pattern, Adaptive Systems, Adversarial Robustness
