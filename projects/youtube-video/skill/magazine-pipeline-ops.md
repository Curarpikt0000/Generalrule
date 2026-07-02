---
name: magazine-pipeline-operations
title: Magazine Pipeline Operations
domain: devops
keywords: [youtube, magazine, pipeline, launchd, drive, service-account, oauth, drive-file-scope, launchctl, dedup, hybrid-drive, block-json, timing-fix, recovered-from-yt, backfill-whisper-timeout, vfr-requeue, video-deletion, thumbnail-update]
description: Deploy, run, and troubleshoot the magazine YouTube pipeline. Covers launchd deployment, SA-only drive uploads, processed.txt dedup, and pipeline lifecycle.
---

# Magazine Pipeline Operations

## Triggers
- User asks to start/stop/manage the magazine pipeline
- Pipeline failures during `upload_assets_to_drive`
- Setting up launchd for periodic pipeline runs
- User says "run the pipeline" or "trigger pipeline manually"
- Block JSON timestamps are in wrong format ("00:MM:SS" instead of "MM:SS:00")
- User asks to "重新扫所有视频封面" / check all covers / replace covers / 统一封面风格
- User asks about pipeline status / health check ("有成功吗", "管道在跑吗") — see `references/pipeline-noise-output-signals.md` for distinguishing real issues from harmless backlog noise
- User sees pipeline cron output with 20-item `videofacereviewer` backlog warning — see `references/pipeline-noise-output-signals.md` (this is a non-actionable noise signal, not an error)
- User reports "Drive 根目录有乱放的文件" — see `references/drive-structure-audit.md` for SA-based recursive scan methodology; see `references/time-clustering-recovery.md` for `createdTime`-based batch recovery of unnamed assets (block_xx.png, cover.png, thumbnail.jpg). **Before running any cleanup**, load `references/magazine-name-aliases.md` into the filename parser — many files use abbreviation prefixes (wsj→Wallstreet Journal, natgeo→National Geographic) that the strict full-name regex misses. See `references/drive-root-structure-audit-2026-06-27.md` for real-world audit with 99.4% clustering accuracy (326→324 correctly paired).
- User asks "6月17日后新增了什么" or similar time-window audit — use `references/drive-structure-audit.md` pattern with `createdTime` filter. For pairing unnamed assets (block_xx.png, cover.png) with their video, see `references/time-clustering-recovery.md`. Apply `references/magazine-name-aliases.md` mapping for abbreviated filenames.

## Overview

The magazine YouTube pipeline runs via `scan_and_process.py` in `~/hermesagent/Youtube video/magazine/`. It is scheduled by launchd and triggered by `run_magazine_pipeline.sh`.

Components:
- `~/hermesagent/com.hermes.magazine-pipeline.plist` — launchd plist (source)
- `~/Library/LaunchAgents/com.hermes.magazine-pipeline.plist` — user-level launchd plist (target)
- `~/hermesagent/run_magazine_pipeline.sh` — shell wrapper
- `~/hermesagent/Youtube video/magazine/scan_and_process.py` — main pipeline script
- Logs: `~/hermesagent/Youtube video/magazine/logs/pipeline_YYYYMMDD_HHMMSS.log`

## Deployment Steps

```bash
# 1. Copy plist to launch agents
cp ~/hermesagent/com.hermes.magazine-pipeline.plist ~/Library/LaunchAgents/

# 2. Load and start
launchctl load ~/Library/LaunchAgents/com.hermes.magazine-pipeline.plist
launchctl start com.hermes.magazine-pipeline

# 3. Verify
launchctl list | grep magazine
```

## Manual Trigger

Run the shell wrapper directly:
```bash
bash ~/hermesagent/run_magazine_pipeline.sh
```

Or run the Python script directly for more control:
```bash
cd ~/hermesagent/Youtube video/magazine
python3 scan_and_process.py
```

## Pitfalls

### 1. ❌ CORRECTED 2026-06-26: Service Account CAN update existing files; OAuth needed for creates

**SA 存储配额为 0**（不是无限）。`hermes-bot@hermes-infra-prod.iam.gserviceaccount.com` 返回 403 `storageQuotaExceeded` 对于 CREATE 操作。

**重要区分**：
- **SA CREATE 文件** → ❌ 403 无存储配额
- **SA UPDATE 已有文件** → ✅ 可行，零存储成本（不耗配额）
- **OAuth CREATE 文件** → ✅ 可行（需要有效 refresh_token）
- **OAuth UPDATE 已有文件** → ✅ 也可行

**Drive 上传策略（2026-06-26 修正版）：**
- SA → 遍历文件夹 / 搜索文件 / **update 已有文件**（如 thumbnail.jpg 覆盖）
- OAuth → 创建新文件（create with `drive.file` scope）
- SA + OAuth 混合：OAuth create（无 parent）→ SA 移入目标文件夹（move with `addParents`）

**OAuth token 过期处理：**
当 `~/.drive-upload-token.json` 的 refresh_token 失效时（Google 验证页面返回 403 `access_denied`），两个方案：
1. 手动重跑 OAuth：`python3 ~/hermesagent/Youtube\ video/reauth_drive.py`
2. 若只是 update thumbnails 等已有文件 → SA update 可绕过 OAuth

### 17. Reauth Script Path & Execution Mode

The reauth script lives at:
```
~/hermesagent/Youtube video/reauth_drive.py
```

It is **NOT on PATH** — `reauth_drive.py` alone produces `zsh: command not found`. Always use the full path or run from the script directory:

```bash
# Preferred (no exec bit needed):
python3 ~/hermesagent/Youtube\ video/reauth_drive.py

# Or after chmod +x:
~/hermesagent/Youtube\ video/reauth_drive.py
```

**Which Google account to auth with**: curarpikt00@gmail.com. **Which client to use: 825033890920** (the YouTube project, which is Google-verified). The `910102927961` client (`client_secret_910102927961-q4sjmldfq8f2kpd6hv4hiuod7spp0610.json`) **returns 403 access_denied** because it has not passed Google verification — the app name "Youtubevideo" triggers the unverified-app warning. The verified client is: `client_secret_825033890920-1h4sd9fgomqo80s05uoepelvl8ab5g44.apps.googleusercontent.com.json` (from project 825033890920, the same one used by YouTube OAuth). Save token to `~/.drive-upload-token.json`.

**Forcing reauth with the correct client:**
```bash
cd ~/hermesagent/Youtube\\ video
python3 -c "
from google_auth_oauthlib.flow import InstalledAppFlow
import os
flow = InstalledAppFlow.from_client_secrets_file(
    'client_secret_825033890920-1h4sd9fgomqo80s05uoepelvl8ab5g44.apps.googleusercontent.com.json',
    ['https://www.googleapis.com/auth/drive.file']
)
creds = flow.run_local_server(port=0, prompt='consent')
with open(os.path.expanduser('~/.drive-upload-token.json'), 'w') as f:
    f.write(creds.to_json())
print('OK')
"

### 18. Backfill Repipeline Queue Scope (vfr_needs_repipeline.json)

The `vfr_needs_repipeline.json` file tracks videos that need full re-processing (transcript → blocks → render → upload). It does **NOT** track videos that completed render but failed on drive_upload. 

Videos that were rendered successfully but failed at drive_upload:
- Are NOT in `vfr_needs_repipeline.json`
- Are NOT in `processed.txt` (no URL recorded if drive_upload failed)
- Are NOT in the backfill script's automatic scan (it checks processed.txt + repipeline queue only)
- Their video folders may have been deleted by cleanup routines

**To re-run drive_upload for these orphaned videos**: You need their YouTube video ID and magazine+date. Either:
1. Use `backfill_drive_assets.py` if the video folder still exists in the magazine directory tree
2. Create a manual entry in `vfr_needs_repipeline.json` for full re-processing
3. Or directly run the drive_upload segment of `process_one_file()` if you have the audio Drive ID

**Tracking files for completed uploads**:
- `processed.txt` — format: `drive_id,filename,timestamp,youtube_url`
- `backfill_completed.json` — format: `[{magazine, date, youtube_video_id, audio_drive_id, processed_at}]`
- `vfr_needs_repipeline.json` — format: `[{audio_drive_id, magazine, date, reason}]`

### 2. Drive API network timeout crash (scan_drive phase)

**Fix applied 2026-06-27.** Pipeline crashes at startup with:
```
TimeoutError: The read operation timed out
```
Trace: `scan_drive()` → `drive.files().list()` → httplib2 → SSL `_read_status()` → `recv_into()` timeout.

**Root cause**: Transient network issue — Drive API HTTPS connection stalls during SSL read phase. NOT a code bug, quota, or credential problem.

**Symptom in cron output**: `scan_and_process.py` starts, prints "Root: {folder_id}", then crashes at the next Drive API call with `TimeoutError`/`ssl.py` traceback. Script exits with code 1.

**Fix in scan_and_process.py `scan_drive()` (2026-06-27):**
- Added `socket.setdefaulttimeout(60)` and `drive._http.timeout = 60` — prevents indefinite hangs
- Added 3-attempt retry loop with exponential backoff (1s, 2s, 4s) around the root folder lookup
- Catches: `TimeoutError`, `socket.timeout`, `httplib2.ServerNotFoundError`
- Only the root folder lookup is retried (single call); the full folder tree scan (`list_all` calls) still uses the 60s socket timeout but does NOT retry individually — the total scan makes too many API calls for per-call retry to be practical

**Verification**: Run `scan_drive()` standalone. It returns a dict keyed by Drive file ID (not a list). Typical count: ~250 audio files.

### 3. Per-file timeout + graceful skip
Each `_upload_file` call is individually try/except-wrapped. Individual file failure never aborts the batch.

### 3. 600s cron timeout is insufficient for render
Pipeline cron runs with 600s timeout, but render takes 15-25 minutes (900-1500s). Drive upload + YouTube upload never complete within this window. When running via terminal, use `background=true` with a generous timeout, or accept that multiple cron cycles are needed per file.

### 4. UPLOAD_COMPLETED_NO_URL deadlock (processed.txt poison)
When YouTube upload succeeds but response parsing fails, pipeline writes sentinel to processed.txt. Later runs skip because `check_already_uploaded()` matches on drive_id without checking URL format. Fix: dedup check should distinguish real URLs from error sentinels.

### 5. RENDERED_QUOTA_EXCEEDED vs TRANSCRIBED_BLOCKS_READY_QUOTA_EXCEEDED
Intermediate statuses in processed.txt that block re-processing. Same fix as #3.

### 6. YouTube custom thumbnails 403 forbidden (unresolved)
`thumbnails.set` returns 403 when channel hasn't completed the custom thumbnail permission gate. NOT a quota issue. Fix: verify YouTube channel at https://www.youtube.com/verify or manually upload one thumbnail via YouTube Studio UI.

### 7. Pipeline timeout when run via terminal
Pipeline can take 10+ minutes per file. Use `terminal(background=true, notify_on_complete=true)` for manual runs.

### 8. QuotaTracker vs real YouTube quota discrepancy
Failed upload parse means `quota_consume()` is never called, undercounting real usage. Use `today_count` from `get_yt_uploads()` as reliable daily cap instead.

### 9. Resume queue bloat
Each failed upload creates duplicate entries in `active_runs.json`. Recovery: check if files exist on YouTube, clear active_runs.json if needed.

### 10. YouTube dedup audit + clean workflow
2-step: audit via `check_youtube_dupes.py`, clean via `dedup_youtube.py`. Duration match verification mandatory before any delete.

### 11. launchd migration run-at-load behavior
Plist `RunAtLoad` = false. Manual start only. `StartInterval` 21600s (6 hours) after first manual start.

### 12. Block JSON timing format
Subagents persistently output wrong format: `00:MM:SS` instead of `MM:SS:00`. Mandatory post-generation fix script in references.

### 13. active_runs.json surgery after token revocation
Reset `drive_upload.status` from `failed` to `pending` after fixing auth, set `attempts` to 0.

### 14. YouTube OAuth token refresh (before cron runs)
YouTube token (`~/.youtube-mcp/token.json`) expires ~1 hour after last use. Pipeline calls to `videos.list`, `playlistItems.list`, and `thumbnails.set` return `HTTP 401 Unauthorized`. Fix: use the `refresh_token` field in token.json to get a new access_token without re-OAuth. See `references/youtube-token-refresh.md` for the exact code and verification script.

**Diagnosis**: 401 on first API call → token almost certainly expired. Do not re-run the pipeline until token is refreshed.

**Token is NOT the same as Drive token** (`~/.drive-upload-token.json`). Two separate Google OAuth tokens for two different APIs.

### 15. RECOVERED_FROM_YT video deletion & retransmit
Search uploads playlist → confirm via videos.list → delete via videos.delete → purge from processed.txt → re-enqueue in vfr_needs_repipeline.json → run pipeline.

### 16. "MP4无视频流" / "MP4太小" = render_video.py concat bug  
**CORRECTED 2026-06-17.** `render_video.py` line 115-116 had `concat_lines.append(concat_lines[-2])` which duplicated the last block's `file` line without a `duration` line, corrupting the ffmpeg concat input. This affects short videos (4-6 blocks) most visibly — longer videos may coincidentally pass.  
**Symptom check:** look at the last 3 lines of the video's `concat.txt` — if the penultimate and antepenultimate lines are both `file 'block_NN.png'` with no `duration` between them, that's this bug.  
**Fix:** already applied to `render_video.py`. See `references/concat-txt-bug.md` for the full diagnosis and corrected replacement.  
**Emergency workaround (if fix isn't deployed):** manually rewrite concat.txt, removing the duplicate last line and computing `audio_dur - total_concat_dur` gap, then re-run `render_video.py` directly.

### 17. mid-turn user steering
User can send out-of-band instructions mid-process. When they say "stop all attempts" and give a single precise command, prioritize their exact instruction over the original plan.

### 19. vfr_resume 模式（videofacereviewer.py）videoNotFound 404 死循环

**发现于 2026-06-24**。`vfr_resume` 模式的 `videofacereviewer.py` 在处理旧视频（从 processed.txt 恢复的 YouTube URL）时，全部失败在封面上传步骤。每条日志：
```
❌ 封面上传失败: <HttpError 404 ... reason: 'videoNotFound' ...>
```
**根因**：这些旧视频的 YouTube URL 来自 processed.txt 或 RECOVERED_FROM_YT，视频可能已被删除、设为不公开/私有，或 token 权限不足以访问。但脚本没有检查视频是否仍存在，而是直接尝试 `thumbnails.set`，全部 404。

**影响**：vfr_resume 一次性处理了 417 个条目，**0 个真正上传成功** — 全部是封面更新失败。日志显示"处理中"但不产生新视频。

**诊断方法**：
```bash
# 检查 vfr_resume 日志中有没有真正的新视频上传（而非封面修复）
grep -E "✅ 视频已上传|视频上传失败|封面上传失败" ~/hermesagent/Youtube\ video/magazine/logs/vfr_resume_stdout.log | sort | uniq -c | sort -rn

# 检查 resume 模式覆盖了多少条目
grep -c "==============================================================" ~/hermesagent/Youtube\ video/magazine/logs/vfr_resume_stdout.log

# 检查 processed.txt 最新成功记录
tail -5 ~/hermesagent/Youtube\ video/magazine/processed.txt | grep "youtube.com/watch\|youtu.be/"
```

**修复方案**：
- `thumbnails.set` 之前先调用 `videos.list`（by id）验证视频是否存在
- 404 时跳过封面更新，记录警告，不阻塞后续流程
- 对 processed.txt 中的 `RECOVERED_FROM_YT` 条目，需要重新上传视频（不是只补封面）

### 20. Pipeline launchd plist 可能丢失

杂志管道的 launchd plist 文件（`com.hermes.magazine-pipeline.plist`）可能因系统重启、清理或其他原因丢失。检查方法：

```bash
# 检查 plist 是否已加载
launchctl list | grep magazine

# 检查源文件是否存在
ls -la ~/hermesagent/com.hermes.magazine-pipeline.plist

# 检查 target 是否存在
ls -la ~/Library/LaunchAgents/com.hermes.magazine-pipeline.plist
```

如果找不到，需要重新部署（见上方 Deployment Steps）。

管道 cron 停止后，新上传到 Drive 的音频文件不会被自动扫描处理。检查标志：processed.txt 最后一条记录的时间距今超过 24 小时。

#### 23. 根目录散落文件/游离文件夹（pipeline 上传 fallback bug）

**发现于 2026-06-27 Drive 审计**。用户的个人 Drive（curarpikt00@gmail.com）根目录有**326 个游离文件**和 **1 个游离文件夹** `Times_20260608`。

**根因**：pipeline 的 OAuth Drive 上传代码在目标文件夹（`Globalmagzineyoutube/{magazine}/video/{year}/{magazine}_{date}/`）不存在时，**未创建目标文件夹，而是直接 fallback 到根目录**。具体：
- `upload_assets_to_drive()` 尝试定位目标文件夹路径
- 当 `{magazine}/video/{year}/` 路径中的某个层级不存在时，代码没有调用 `drive.files().create(body={'name': ..., 'mimeType': 'application/vnd.google-apps.folder', 'parents': [...]})` 创建缺失的文件夹
- 而是静默地跳过文件夹定位，把文件创建在根目录
- 这导致 block_*.png、blocks_v5.json、final.mp4 散落在根目录

**受影响的杂志**：`Times` 杂志（`Globalmagzineyoutube/Times/` 下没有 `video/` 目录）。检查发现其他杂志（Bloomberg、Science 等）的 video/ 目录存在，故未受影响。Times 的 video/ 目录可能被遗漏创建。

### 23a. 文件名别名不匹配（wsj→Wallstreet Journal, natgeo→National Geographic）

**发现于 2026-06-27**。pipeline 或整理脚本的文件名解析逻辑依赖严格的杂志名全称匹配（如 `wallstreet_journal_20260518`），但实际文件名使用缩写（`wsj_20260518_blocks_v5.json`）。这导致文件无法被识别归属。

**完整别名映射表见**：`references/magazine-name-aliases.md`（21 条映射，按前缀长度排序）

**影响**：没有别名映射时，以 `wsj_` 或 `natgeo_` 开头的文件会被归类为"无法识别"，留在根目录。

**修复方法**：在任何驱动级文件名解析函数中，先加载 `references/magazine-name-aliases.md` 的映射表作为第一步，正则匹配前将缩写先映射到标准名。

**审计方法确认 Drive 根目录状态：**
```bash
# 统计根目录游离文件（需 OAuth）
python3 -c "
from google.oauth2.credentials import Credentials
import pickle, json
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
creds = pickle.load(open('/Users/chaojin/Claudcode/magazine-podcast/drive_token.pickle', 'rb'))
if creds.expired: creds.refresh(Request())
drive = build('drive', 'v3', credentials=creds, cache_discovery=False)
files = drive.files().list(q=\"'root' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed=false\", pageSize=500, fields='files(name)').execute()
print(f'Root-level files: {len(files.get(\"files\", []))}')
folds = drive.files().list(q=\"'root' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false\", fields='files(name)').execute()
print(f'Root-level folders: {len(folds.get(\"files\", []))}')
for f in folds.get('files', []):
    print(f'  📁 {f[\"name\"]}')
"

# 检查特定杂志是否有 video/ 子目录
drive.files().list(q="name='Times' and '1tOVhkClasjoGUxtKIzyskFoGi3Zs1zy4' in parents", fields='files(id)').execute()
→ 然后查该杂志的子文件夹中是否有名为 'video' 的文件夹
```

**整理方案**（尚待用户确认，未执行）：
1. 创建缺失的 `Globalmagzineyoutube/Times/video/2026/` 路径
2. 将 `Times_20260608` 根目录文件夹移入 `video/2026/Times_20260608/`
3. 对 326 个根目录游离文件，按文件名中的 `{magazine}_{YYYYMMDD}` 模式匹配，逐个归入对应杂志/年份/日期文件夹
4. 若文件名不含杂志/日期信息（如 `block_01.png` 孤立文件），无法自动归类，需人工判断

**代码修复方向**（待实施）：
`scan_and_process.py` 中的 `upload_assets_to_drive()` 应在定位目标路径时，对路径中不存在的每一级文件夹自动创建（递归 mkdir 语义），而不是 fallback 到根目录。

## 22. 批量替换旧视频封面（batch cover fix）

当需要统一频道上所有视频封面时，使用两个脚本：

**旧版（2026-06-24）：** `batch_fix_covers.py` — 仅记录封面列表到 `cover_batch_log.json`，不执行上传。  
**新版（2026-06-26）：** `batch_regen_covers.py` — 全自动一站式：Imagen 3.0 生成背景 → Pillow 合成杂志名/日期/摘要 → Drive upload（SA update + OAuth create hybrid） → YouTube thumbnail.set。

**batch_regen_covers.py 路径：** `~/hermesagent/Youtube video/batch_regen_covers.py`  
**日志：** `~/hermesagent/Youtube video/batch_regen_covers_log.json`  
**参考详情：** `references/batch-cover-regen-2026-06-26.md`（完整工作流和陷阱记录）


排查管道"有没有在运行"时，按顺序查：
1. `launchctl list | grep magazine` — plist 是否加载
2. `ls ~/Library/LaunchAgents/com.hermes.magazine-pipeline.plist` — plist 是否存在
3. `tail -5 ~/hermesagent/Youtube\ video/magazine/processed.txt` — 最近成功记录
4. `grep "2026-06" processed.txt | grep -c "youtube.com/watch\|youtu.be/"` — 当月成功数
5. `grep -c "youtube.com/watch\|youtu.be/" processed.txt` — 累计成功总数
6. `ls ~/hermesagent/Youtube\ video/magazine/logs/pipeline_*.log 2>/dev/null \| wc -l` — pipeline 日志数

典型结论模式："有成功在产出，但不多。processed.txt 共 N 行，M 个有有效 URL。6月成功 X 个。最后一次成功是 YYYY-MM-DD HH:MM。但 vfr_resume 那波旧视频补素材全部失败在封面 404，新视频的 cron 管道可能没在跑。"

### 18. Pipeline quota check blocks drive_upload (doesn't need YT quota)
The pipeline's resume loop and new-file loop call `qt.can_upload()` before processing ANY item, including items that only need `drive_upload` (not YouTube upload). Since `drive_upload` uses Google Drive OAuth (not YouTube API), it is **not quota-gated** and should run regardless of YouTube quota.

**Failure pattern**: Videos that completed render (RE✓) but failed on `drive_upload` get stuck when YouTube quota is exhausted. Quota check (`remaining < ~1660 units`) breaks the entire loop before reaching the `drive_upload` step at line 1541. These videos remain with:
- `drive_upload` step **missing** from `active_runs.json` (field never written, not even as failed)
- Drive folder and block images may be uploaded (via earlier SA path) but MP4 and cover are missing
- `processed.txt` has no entry for them
- No YouTube URL

**Recovery script**: `~/hermesagent/Youtube video/magazine/references/drive-upload-backfill.py` (see reference) directly calls `upload_assets_to_drive()` via OAuth, skips YouTube quota check. Run after fixing Drive OAuth token:
```bash
python3 ~/hermesagent/Youtube\ video/magazine/references/drive-upload-backfill.py
```

**Manual entry in active_runs.json** (alternative): Add a `drive_upload` step with `status: "failed"` so the resume loop picks it up on next run (if quota is available):
```json
"drive_upload": {
  "status": "failed",
  "attempts": 0,
  "error": "skipped_by_quota_gate"
}
```
Then restart the pipeline once quota resets.

**Permanent fix idea** (if script maintainer): Split the resume loop into two passes — first pass runs `drive_upload` for any file that has render✅ + YT URL missing (no quota cost). Second pass handles YouTube upload (quota-gated).

## Verification

After deployment:
```bash
launchctl list | grep magazine
ls -t ~/hermesagent/Youtube video/magazine/logs/pipeline_*.log | head -1 | xargs tail -30
tail -50 ~/hermesagent/Youtube video/magazine/logs/launchd_stderr.log
```

## User Interaction Style (Chao Jin)
- When running the pipeline, the user wants raw output posted verbatim
- Do not reload/poll the pipeline mid-run. Run once and return output.
- The user corrects technical assertions. Trust the user over defaults.
- When user says "stop all attempts" and gives one precise command, execute exactly that — do not improvise or continue the original plan.
- **Stick to the current project's scope.** When user asks about YouTube pipeline, do not confuse it with other projects (e.g. US Debt cron jobs, COMEX reports). They are separate projects with separate folders, skills, and context. User will tell you which project they mean.
- **Pipeline health check response format**: When user asks "有成功吗" or similar pipeline status check, reply with a compact summary. Format: first line = verdict sentence ("有成功在产出" / "管道停了" / "全部失败"), then bullet-point numbers (processed.txt 总数 / 含 URL 数 / 当月成功数 / 最后一次时间). No verbose explanation of individual failures unless user asks for it. User will drill down if needed.
