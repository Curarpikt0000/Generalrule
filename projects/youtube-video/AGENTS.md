# YouTube 视频自动化 — AGENTS.md

## 项目名
YouTube 视频自动化（杂志视频流水线）

## 核心描述
从 Google Drive 扫描音频文件 → 转录成文字 → 生成 blocks 结构化内容 → Imagen AI 配图 → 渲染最终视频 → 上传到 YouTube。

**主入口**：`magazine/scan_and_process.py`（全流程入口脚本）

## 整个流水线（Pipeline）
```
Drive 扫描音频 → DeepSeek 转录 → Block 生成 (JSON) → Imagen 生成图片
→ 视频渲染 (ffmpeg) → Drive 资产上传 → YouTube 上传
```

## 🔑 重要指针

| 项目 | 路径 |
|---|---|
| **项目 AGENTS.md** | `~/hermesagent/Youtube video/AGENTS.md` |
| **上下文快照** | `~/hermesagent/Youtube video/docs/context-log.md` |
| 根全局规则 | `~/hermesagent/Hermes General Rule & Protocol/CLAUDE.md` |
| 主入口脚本 | `magazine/scan_and_process.py` |
| 状态跟踪 | `magazine/processed.txt`（只追加，永不删除） |
| 活跃运行 | `magazine/active_runs.json` |
| 处理日志 | `magazine/process_log.jsonl` |
| 日程调度 | `scheduled-tasks/` |
| 视频输出 | `magazine_outputs/` |
| AI 图片缓存 | `imagen_cache/` |
| YouTube OAuth | `~/.youtube-mcp/token.json` |
| Drive SA Key | `~/hermesagent/Youtube video/hermes-infra-prod-9c5abf6aefe8.json` |

## 关键文件

| 文件 | 用途 |
|---|---|
| `backfill_drive_assets.py` | 补齐旧视频的 Drive 素材（每次最多 5 个） |
| `drive_organizer.py` | Drive 文件夹整理 + 审计 |
| `vfr_needs_repipeline.json` | backfill 任务队列（缺 Drive 素材的视频） |
| `portrait_needs_rerender.json` | 竖版视频的重新渲染队列 |
| `drive_audit_report.json` | Drive 文件夹审计结果 |
| `fix_covers_unified.py` | 统一修复封面缩略图 |
| `assign_youtube_playlists.py` | 批量分配 YouTube 播放列表 |
|| `batch_regen_covers.py` | 临时脚本：批量重新生成 27 个视频封面（Imagen→Pillow→Drive→YT） |
|| `cover_audit_report.csv` | 封面文字审计报告 |

## ⚠️ 核心规则

1. **三层去重**（L1 本地 processed.txt → L2 YouTube description 搜索 → L3 YouTube 视频列表验证）
2. **根目录写入禁令**：所有文件必须写到本项目目录内，禁止写入 `~/Documents/` / `~/Desktop/` 等
3. **每次启动必须阅读**：`CLAUDE.md`（全局规则），`magazine/PIPELINE_SPEC.md`，`magazine/CRITICAL_BUG_LESSON_20260518.md`
4. **竖版视频检测**：QC 必须检查所有图片和渲染结果是否为横版（≥16:9），否则 pipeline 立即中止
5. **Drive 资产规范**：每个视频必须有 5 类文件（JSON blocks, block 图片, thumbnail, mag_cover, final MP4）

## 📋 历史教训
| 日期 | 问题 | 教训 |
|---|---|---|
| 2026-05-18 | 59次重复上传尝试，23个重复视频，配额耗尽 | 三层精确去重，不用模糊匹配 |
| 2026-05-19 | PENDING_UPLOAD 积压 21 个，从未上传 | 禁止 PENDING 状态，只记录成功或跳过 |
| 2026-05-22 | 根目录积累 26 个游离文件 | 新文件必须写入对应子目录 |
| 2026-05-23 | 旧 Pipeline 渲染竖版视频混入 YouTube | 所有 QC 必须检查横版分辨率 |
| 2026-06-16 | **SA Drive 存储配额为 0（非无限），OAuth 凭证也过期失效** | **Drive 上传需用 OAuth 用户凭证；OAuth token 过期后需手动运行 `reauth_drive.py`。pipeline 应优先使用 OAuth（SA 只用来读/list）。** |
| 2026-06-17 | **render_video.py concat.txt 生成 bug** | **短音频视频渲染时音频时长 > 图片总时长时，必须计算 gap 后补正确 duration，gap 负数时修剪最后一帧时长。QC 检查必须验证 concat.txt 的 file/duration 行数配对。** |
| 2026-06-27 | Drive API 偶发 SSL 超时导致 pipeline 整个崩溃 | `scan_drive()` 必须加 socket 超时 + 重试；SDK 默认不设超时，需要显式设 `drive._http.timeout` |
| 2026-06-27 | 326 个 pipeline 输出文件散落在 Drive 根目录 | 文件必须写入对应子目录；新脚本应直接在目标目录创建文件，不要经过 root |

## 📅 每日 cron 自动压缩上下文
见 `scheduled-tasks/` 目录中的调度任务配置。
