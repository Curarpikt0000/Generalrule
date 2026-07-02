# SIFO §8 模块详细实现笔记（v2 迁移版）

> 本文件从 `comex-report` devops skill 迁移而来，是 2026-05-29 会话期间 Chao 提供的 SIFO 模块原始规范。
> 核心内容已合并入 `comex-daily-report` SKILL.md §8。此文件保留原始 session 详细数据供参考。

## 变量提取详细值（2026-05-29 session）

### 变量 r: 3-Month Term SOFR
- 之前错误：抓了 NY Fed 隔夜 SOFR (3.62%) 和 SOFR 90d rolling avg (3.58%)。
- 正确：r = CME Group Benchmark Administration 发布的 3M Term SOFR。后续使用 FRED DGS3MO 作为代理。

### 变量 F: Section62 PDF 提取
- URL: `https://raw.githubusercontent.com/Curarpikt0000/Daily_Metal-OI-CME_Notion/main/downloads/Section62_Metals_Futures_YYYY-MM-DD.pdf`
- GC AUG26 settlement = $4,488.00
- SI JUL26 settlement = $74.930
- PL JUL26 settlement = $1,933.40

### 变量 USDCNY
- XE mid-rate (6.77) 不可信赖
- CFETS 中间价：5/28 = 6.8240, 5/29 = 6.8176

### 变量 S_phy
- Au99.99 收盘: 961.82 元/克（好于 Au(T+D) 的 961.20）
- Ag(T+D) 收盘: 17,822.00 元/千克
- Pt99.95 收盘: 474.25 元/克

## 变量提取技巧
- SGE 官网「数据资讯→历史行情数据→每日行情」
- CFETS 历史: chinamoney.com.cn → 历史数据标签
- Section62: pdftotext -layout → 定位 COMEX GOLD FUTURES 段 → AUG26 行
