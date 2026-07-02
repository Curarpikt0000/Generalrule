# 项目上下文日志

> 每 session 或重要变更后更新此日志，记录决策、事实配置、进展和待办。

---

## 2026-06-17

### 决策
- 项目初始化，首批上下文快照迁移

### 事实配置
- **项目名称**: YouTube 视频自动化（杂志视频流水线）
- **项目根目录**: `~/hermesagent/Youtube video/`
- **主入口**: `magazine/scan_and_process.py`
- **核心流水线**: Drive 扫描音频 → 转录 → Block 生成 → Imagen AI 配图 → 视频渲染 → 上传 YouTube

### 状态摘要
| 项目 | 状态 |
|------|------|
| 上次 pipeline 运行 | 2026-06-17 全天（3 个视频新上传 + 之前的 30 个已在凌晨完成） |
| 已处理文件总数 | 358 条记录（processed.txt） |
| 6/17 新增上传 | Wallstreet Journal_20260601, New Yorker_20260601, Astronomy Now_20260501, National Geographic Traveller_20260601 |
| Drive 存储 | SA 账户存储配额已满（403 storageQuotaExceeded） |
| 600s cron timeout 不足 | render 需 15-25min，Drive/YT 上传在 cron 窗口内无法完成（自动续跑机制正常） |
| 积压 5 个文件堵在 drive_upload | Barron's_20260601, Science_20260514, Economist_20260530, New Scientist_20260523, Wallstreet Journal_20260528 |
| YouTube 配额使用 | 6/17 凌晨达到 99.1%（49,548/50,000 units），午夜后自动重置 |

## 2026-06-18

### 状态摘要
| 项目 | 状态 |
|------|------|
| YouTube API 配额 | 6/18 整天维持在 99.1%（50,000 units 中已用 49,548），所有上传暂停 |
| 总扫描音频 | 254 个 |
| YouTube 已有视频 | 247 个 |
| 今日已上传 | 30 个（6/18 凌晨配额重置后完成，之后再次耗尽） |
| 待续传（render 已完成，等上传） | 7 个 |
| 新待处理 | 23 个新音频文件 |
| Drive OAuth 凭证 | 仍过期（需运行 reauth_drive.py 恢复） |
| 需人工处理的 NEEDS_REUPLOAD | Foreign Affairs_20250901, Wallstreet Journal_20260228（重复）, Foreign Affairs_20260101 |
| 重试队列（旧配额超限） | Wallstreet Journal_20260302/20260228/20260312, Barron's_20260316 |
| Drive 素材缺失 | 20 个视频（已在 YouTube 上，需 backfill） |

### 进展
- 6/18 凌晨配额重置后先行上传播了 30 个视频，之后配额再次耗尽
- 所有后续 cron 轮次均跳过了上传步骤（仅完成扫描+对账）
- WSJ_20260528 和 New Scientist_20260530 渲染完成但 Drive 上传失败（OAuth 过期 + SA 无配额）

### 待办
- 待 Pacific 午夜配额重置后自动续传 7 个已完成视频 + 处理 23 个新文件
- 运行 `reauth_drive.py` 恢复 Drive 上传能力
- 考虑 backfill 20 个缺 Drive 素材的已有视频

## 2026-06-19

### 状态摘要
| 项目 | 状态 |
|------|------|
| YouTube API 配额 | 6/18 使用 26,424/50,000 units（52.8%）— 配额已重置，但无新上传执行 |
| processed.txt 总记录 | 358 条，其中 291 条有 YT URL |
| 最近成功上传 | 6/17 22:36 手动会话上传 4 个视频（WSJ_20260601, New Yorker_20260601, Astronomy Now_20260501, National Geographic Traveller_20260601） |
| 积压（active_runs） | 9 个文件处于不同阶段 |
| Drive OAuth 凭证 | 仍过期（需运行 reauth_drive.py） |
| YouTube OAuth token | 6/15 已过期，需重新认证 |

### active_runs 明细
- Wallstreet Journal_20260519: DL✓ TR✓ BL✓ IM✓ RE✓ DU❌ → 6/19 Drive OAuth 重新授权后已重跑
- Wallstreet Journal_20260528: DL✓ TR✓ BL✓ IM✓ RE✓ DU❌ → 同上
- New Scientist_20260530: DL✓ TR✓ BL✓ IM✓ RE✓ DU❌ → 同上
- Wallstreet Journal_20260602: DL✓ TR✓ BL✓ IM✓ RE✓ DU❌ → 同上
- Times_20260608: DL✓ TR✓ BL✓ IM✓ RE❌（无视频流，需重渲染）
- Economist_20260530: DL✓ TR✓ BL✓ IM✓ RE✓ DU✅ YT✅
- Barron's_20260601: DL✓ TR✓ BL✓ IM✓ RE✓ DU✅ YT✅
- Science_20260514: DL✓ TR✓ BL✓ IM✓ RE✓ DU✅ YT✅
- New Scientist_20260523: DL✓ TR✓ BL✓ IM✓ RE:-（未完成）
- Wallstreet Journal_20260604: DL✓（新下载，其余未执行）

### 进展
- 6/18 22:00-23:00 手动运行 reauth_drive.py 重新授权 Drive OAuth（curarpikt00@gmail.com）
- 6/19 09:33 手动启动 pipeline 重跑，续传 4 个堵在 drive_upload 的视频
- 4 个堵在 drive_upload 文件的 status：WSJ 20260519/20260528/20260602, NS 20260530

### 待办（更新 2026-06-19）
1. ~~运行 reauth_drive.py 恢复 Drive 上传~~ ✅ 已完成
2. ~~手动 pipeline 运行完成后检查 4 个视频是否成功 drive_upload → YouTube upload~~ ✅ 全部上传
3. ~~Times_20260608 需重新渲染（render QC 无视频流）~~ ✅ 修复并上传成功
4. YouTube token 续期（若仍过期）

## 2026-06-20

### 状态摘要
| 项目 | 状态 |
|------|------|
| YouTube API 配额 | 49,549/50,000 (99.1%) — 6/20 凌晨配额重置后完成 6 个上传，再次耗尽 |
| 6/19 上传数 | **18 个** — 6/19 18:00 cron 批量上传（含积压的 5 个 drive_upload 续传） |
| 6/20 上传数 | **6 个**（配额耗尽前完成） |
| 最近上传 | Times_20260608 ✅（修复 render bug 后上传）、Astronomy_20260601、New Yorker_20260525、WSJ_60521/60526/National Geographic 20260601 |
| processed.txt | 382 条记录 |
| active_runs | 4 个残留项（economist/barrons/science/new_scientist_20260523，疑似未清理但已完成） |
| Drive OAuth | ✅ 已修复（6/19 reauth_drive.py 后恢复） |
| Times_20260608 render | ✅ **已修复**（2026-06-17 concat.txt bug — 短音频 gap 计算后进行重新渲染） |

### 进展
- 6/19 18:00 cron 完成批量上传：18 个视频全部上传到 YouTube
- **Times_20260608**：原 render 失败（concat bug，缺失 duration 行）→ 手动修复重渲染→ Drive 上传→ YouTube 上传全部完成
- 6/20 06:00 cron 继续处理，再上传 6 个视频，配额耗尽后停止
- **所有历史积压全部清空**（drive_upload 堵的 4 个 + Times render 问题全部解决）

### 待办
- 待配额重置后继续处理新扫描的音频
- 清理 active_runs.json 中 4 个残留项的冗余数据
- 考虑每天更早开始 pipeline 以尽量用完每日配额

## 2026-06-24

### 状态摘要
| 项目 | 状态 |
|------|------|
| YouTube API 配额 | 上次检测约 99.1% 耗尽（6/20 后未查新值） |
| 6/20 后新增上传 | **2 个** — WSJ 20260522 (00:03), WSJ 20260523 (00:10) — 均为 2026-06-24 凌晨完成 |
| processed.txt | **384 条记录**（+2 自 6/20 快照），其中 **317 条有 YT URL** |
| active_runs | 4 个残留项（Economist_20260530, Barron's_20260601, Science_20260514, New Scientist_20260523），步骤全空但 yt 不全，疑为 pipeline 中途清理失败 |
| 6/19-6/20 批量上传数 | 7 个于 6/19 夜间 + 6 个于 6/20 06:00 = **13 个**（含修复后的 Times_20260608） |

### 进展
- pipeline cron 在 6/21-6/23 期间持续自动运行，处理新扫描的音频
- 6/24 凌晨 00:03-00:10 完成 2 个新视频上传（WSJ 20260522, WSJ 20260523）
- 所有历史积压已清空，pipeline 进入正常持续运行状态

### 活跃状态评估
当前 pipeline 运行正常、稳定。无阻塞积压。之前历史性的 drive_upload、render、token 三大问题均以解决。

## 2026-06-25

### 活跃状态评估
| 项目 | 状态 |
|------|------|
| YouTube pipeline cron | ✅ 持续运行（6/24 只停美债 7 个 cron，YouTube pipeline 不受影响） |
| 封面批量替换进度 | 已完成 45 个（offset 0-45），剩余约 150 个待处理 — 由 `batch_fix_covers.py` 管理 |
| 封面替换日志 | `cover_batch_log.json`（记录每个已完成视频，自动跳过已删除已替换） |
| Imagen rate limit | 每 5 个封面触发一次 429，自动等待 60s 重试，处理速度约 5 个/3-5分钟 |
| 安全拦截 | 个别视频因 Imagen safety block 使用渐变备用图（自动 fallback） |
| PDF cover fetch | 因 `convert` 命令缺失，部分视频 PDF cover fetch 出错，自动 fallback 到占位框 |

### 无其他变更
- AGENTS.md 核心规则、历史教训全部准确 ✅
- 无新的 pipeline 代码修改、配置变更
- 无新的历史教训

## 2026-06-26

### 状态摘要
| 项目 | 状态 |
|------|------|
| 封面批量重制 | 27 个视频全部生成并上传到 YouTube ✅ |
| YouTube 封面更新 | ✅ 全部 27 个 |
| Drive 封面覆盖 | ✅ 24 个（3 个因 OAuth vs SA 文件权限问题创建在 root，未移入目标文件夹） |
| batch_regen_covers_log.json | 仅存 1 条日志（后续 run 未持久化完整日志） |
| 使用的脚本 | `batch_regen_covers.py`（临时脚本，在项目根目录） |

### 进展
- 6/26 用户确认 27 个视频的封面需要重新生成
- 编写 `batch_regen_covers.py` — 每个视频：Imagen 生成背景 → Pillow 合成杂志名+日期文字 → 上传到 Drive 对应目录 → YouTube API 更新封面（thumbnails.set）
- 全部 27 个视频的封面成功上传到 YouTube
- 24 个同时覆盖了 Drive 里对应目标文件夹的 `thumbnail.jpg`
- 3 个视频（hQaAiBRETcA、SPM2HAz_CLI、12eKeNqs7d8）的 Drive 文件被 OAuth token（`drive.file` 范围）创建在 root，因 SA 无权限移入目标文件夹
- OAuth 重新授权为 `drive`（完整范围）超时，未完成

### 待办
- 需手动登录 curarpikt00 邮箱将 root 中孤立 thumbnail.jpg 移入对应视频文件夹

## 2026-06-27

### 状态摘要
| 项目 | 状态 |
|------|------|
| Pipeline | ✅ 修复完成并恢复运行 |
| Pipeline 崩溃原因 | Drive API HTTPS SSL 读超时（网络波动），非代码 bug |
| scan_drive() 加固 | ✅ 60s socket/HTTP 超时 + 3 次重试（指数退避） |
| Pipeline 重跑结果 | 31s 正常完成，0 新文件，4 个续传全部跳过（已在 processed.txt） |
| Drive 根目录清理 | ✅ 326 个文件 + 1 个文件夹全部归位 |
| root 中孤立文件 | 0 个游离文件，0 个游离文件夹 |
| 清理脚本保留 | `drive_root_cleanup.py`、`delete_orphan_thumbnails.py`、`dry_run_v3.py`（在项目根目录） |

### 决策
- **Pipeline 加固**：`scan_drive()` 中根文件夹查询增加 `socket.setdefaulttimeout(60)` + `drive._http.timeout = 60` + 3 次重试（捕获 TimeoutError/socket.timeout/httplib2.ServerNotFoundError），指数退避 1s/2s/4s
- **不要**再次遇到 SSL 管道断开时让 pipeline 崩溃，重试会自动恢复
- **Drive 根目录清理**：所有 pipeline 输出文件（final.mp4、thumbnail.jpg、blocks JSON 等）默认都放到了根目录 → 已全部整理到 `Globalmagzineyoutube/{magazine}/video/{year}/{magazine}_{date}/` 子目录

### 事实配置
- `scan_drive()` 内重试逻辑：attempt 0-2，退避 `2**attempt` 秒
- 清理后 Drive 根目录仅保留 9 个正常文件夹（Globalmagzineyoutube、HermesProduction、JOB related、PPT 模版、Takeout、Youtube and movie、全球市场研报、投资分析、易经）

### 历史教训
| 日期 | 问题 | 教训 |
|------|------|------|
| 2026-06-27 | Drive API 偶发 SSL 超时导致 pipeline 整个崩溃 | `scan_drive()` 必须加 socket 超时 + 重试；SDK 默认不设超时，需要显式设 `drive._http.timeout` |
| 2026-06-27 | 326 个 pipeline 输出文件散落在 Drive 根目录 | 文件必须写入对应子目录；`batch_regen_covers.py` 的 Drive 上传逻辑需要更新（新脚本应直接在目标目录创建文件，不要经过 root） |

## 2026-06-30

### 活跃状态评估
| 项目 | 状态 |
|------|------|
| Pipeline 流水线 cron | ✅ 旧的每6小时 no_agent 流水线 cron (`97a976d4ece3`) 已从系统中删除 |
| 上下文压缩 cron (`a5eba8e83857`) | ✅ 保留（每个项目标配的 02:15 快照压缩） |
| vfr_needs_repipeline.json | 仍存在（20 个 Drive 缺素材的视频），pipeline 启动时只读打印，不处理 |
| playlist 分配 cron (`33265cef768d`) | ✅ 每周一自动运行，正常 |
| 最近 pipeline 运行 | 正常（成功:4 失败:0 跳过:0，每次约 32s）|

### 决策
- **旧 cron 已删除**：旧的每6小时 no_agent 流水线 cron 已在6/30会话中被用户确认删除。项目只保留上下文压缩 cron + playlist allocation cron。
- **vfr_needs_repipeline.json** 属于 2026-06-10 生成的旧 backlog（drive_audit_report 后剩余未处理的 20 个视频），pipeline 只读不操作。如需消费需运行 `backfill_drive_assets.py`。

### 待办
- `vfr_needs_repipeline.json` 中 20 个视频的 Drive 素材状态需人工确认后再决定是否清理文件或继续 backfill
