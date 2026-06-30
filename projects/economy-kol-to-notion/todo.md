# TODO — Economy-KOL-to-Notion

## ✅ 已完成（2026-06-20/21）
- [x] 项目骨架 + 密钥(Notion/Exa/Tavily) + 真实浏览器(Chrome,@reboot自愈) + gh push凭证
- [x] Step1 SSOT 重建 kol_registry.json (75 KOL)
- [x] Step2 历史回溯 75 KOL 从 2025-11-01 (净增 412 条, 1603→2015)
- [x] Step3 75 KOL 丰富 profile 写入 Notion List page 正文 (75/75)
- [x] Step4 需求① 新颖性判断写进 skill §3.4
- [x] Step5 Dashboard 5项改进 + 加权评分 (已 push + 线上验证)
- [x] Step6 建 4 个 cron (日09:00/推送09:30/周一周报/归档03:15 JST)
- [x] Step7 skill 同步 ub-branch + main (已 push)

## ⏳ 待 Chao 决策
- [ ] **anu_anand**: Chao说是印度占星师,但搜不到此名占星师,疑为 Abhigya Anand(已在registry)笔误。暂 active=false。待确认:删此条 or 给准确身份
- [ ] **郑博建→郑博见**: 显示名已更正,Notion select 沿用'郑博建'拼写。是否要改 Notion select?

## 🔄 日常运行(cron 自动)
- 每工作日 09:00 自动追踪新观点 → 09:30 推送 dashboard
- 周一 09:00 周报 | 每日 03:15 上下文归档
- 新增 KOL: 走 skill §七 7步 onboarding
