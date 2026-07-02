# YouTube 杂志视频全自动流水线 — 项目 Docker

> YouTube 杂志视频全自动流水线：从 Google Drive 扫描音频 → DeepSeek 转录 → Block 生成 → Imagen AI 配图 → ffmpeg 渲染 → Drive 资产上传 → YouTube 上传。
> 本目录是 SSOT（单一真实来源），commit 到 Generalrule 后，新 agent 启动时 git pull 即可开工。

---

## 快速启动（新 agent）

1. `git pull` 本仓库（Generalrule）
2. `cd projects/youtube-docker/`
3. 读 `AGENTS.md` → `lessons.md` → `skill/SKILL.md`
4. 检查 cron 是否注册（参照 `cron/` 目录下的配置）
5. 确保 OAuth token 有效（`~/.youtube-mcp/token.json` + `~/hermesagent/Youtube video/hermes-infra-prod-9c5abf6aefe8.json`）
6. 开工

## 目录结构

```
youtube-docker/
├── README.md              ← 本文件（项目简介+启动指南）
├── AGENTS.md              ← 项目 AGENTS.md（知识包索引+核心指针）
├── context-log.md         ← 最近上下文快照（每晚自动更新）
├── lessons.md             ← 踩坑大全（所有关键教训合集）
├── todo.md                ← 待办事项
│
├── skill/                 ← 项目 skill 本体
│   ├── SKILL.md           ← youtube-automation skill（全流程规格）
│   └── magazine-pipeline-ops.md  ← magazine-pipeline-operations skill（运维操作）
│
├── scripts/               ← 关键脚本（pipeline 核心代码）
│   ├── scan_and_process.py      ← 全流程入口脚本
│   ├── gen_blocks.py            ← 分块转录+总结生成
│   ├── gen_images.py            ← Imagen AI 图片生成
│   ├── render_video.py          ← ffmpeg 视频渲染
│   ├── upload_video.py          ← YouTube 上传
│   ├── backfill_drive_assets.py ← 补齐旧视频的 Drive 素材
│   ├── reauth_drive.py          ← Drive OAuth 重新授权
│   └── reauth_youtube.py        ← YouTube OAuth 重新授权
│
└── cron/                  ← cron 配置快照
    ├── youtube-pipeline.json
    └── context-compression.json
```

## 核心调度

| 时间 (JST) | 任务 | cron job ID |
|---|---|---|
| 09:00 每周一 | 上周视频加入 Playlist | `33265cef768d` |
| 02:15 每日 | YouTube 上下文快照压缩 | `a5eba8e83857` |

## 核心流水线

```
Drive 扫描音频 → DeepSeek 转录 → Block 生成 (JSON)
→ Imagen AI 图片生成 → ffmpeg 视频渲染
→ Drive 资产上传 → YouTube 上传
```

**主入口**：`scripts/scan_and_process.py`（magazine/ 目录下的全流程脚本）

**完整流程：**
1. **Drive 扫描**：扫描 `Globalmagzineyoutube/*/audio/*.mp3` 查找未处理的音频文件
2. **DeepSeek 转录**：将音频文件转录为文字
3. **Block 生成**：按内容分块，每块生成总结 + 时间戳 → `{slug}_blocks_v5.json`
4. **Imagen 配图**：为每段 block 生成配图 → `block_01.png ... block_NN.png` + `thumbnail.jpg`
5. **ffmpeg 渲染**：将图片 + 字幕 + 背景音乐渲染为最终视频 → `{slug}_final.mp4`
6. **Drive 上传**：将 blocks JSON、所有 block 图片、视频上传到 `Globalmagzineyoutube/{magazine}/{year}/video/{magazine}_{YYYYMMDD}/`
7. **YouTube 上传**：将最终视频上传到 YouTube 频道

**状态追踪：** `magazine/processed.txt`（只追加，永不删除）
**活跃运行：** `magazine/active_runs.json`
**处理日志：** `magazine/process_log.jsonl`

## 外部服务

| 服务 | 认证方式 | 关键文件 |
|---|---|---|
| **YouTube Data API** | OAuth 2.0 (用户凭证) | `~/.youtube-mcp/token.json`（需含 refresh_token） |
| **Google Drive** | OAuth 2.0 (用户凭证) + Service Account (只读 fallback) | `~/hermesagent/Youtube video/hermes-infra-prod-9c5abf6aefe8.json` |
| **DeepSeek API** | API Key | 转录 + block 生成 |
| **Imagen (Google Vertex AI)** | GCP Service Account | AI 配图生成 |
| **ffmpeg** | 本地系统 | 视频渲染 |

### ⚠️ Token 注意事项
- **YouTube OAuth**：token 必须包含 `refresh_token` 字段。过期后运行 `reauth_youtube.py` 重新授权。
- **Drive OAuth**：SA 存储配额为 0（非无限），OAuth 凭证也过期失效。优先使用 OAuth 用户凭证上传，SA 只用于读/list。OAuth token 过期后运行 `reauth_drive.py`。
- **Drive API 偶发 SSL 超时**：`scan_drive()` 必须加 socket 超时 + 重试；SDK 默认不设超时，需显式设 `drive._http.timeout`。

### Drive 资产规范
每个视频必须有 **5 类文件**，存放在：
```
Globalmagzineyoutube/{magazine}/{year}/video/{magazine}_{YYYYMMDD}/
```
1. `{slug}_blocks_v5.json` — 转录原文 + 分 block 总结 + 时间戳
2. `block_01.png … block_NN.png` — 每段 block 配图（Imagen 生成）
3. `thumbnail.jpg` — YouTube 封面缩略图（1280×720）
4. `mag_cover.jpg` — 杂志 PDF 第一页截图（⚠️ 当前未自动生成，需手动补充）
5. `{slug}_final.mp4` — 最终渲染视频

## 三层去重协议

上传前必须经过三重验证，防止重复上传：

| 层级 | 方法 | 说明 |
|---|---|---|
| **L1** | 本地 `processed.txt` | 检查视频 slug（`{magazine}_{YYYYMMDD}`）是否已存在 |
| **L2** | YouTube description 搜索 | 搜索频道所有视频 description 是否已包含该 slug |
| **L3** | YouTube 视频列表验证 | 按日期/标题匹配频道已有视频 |

**历史教训**：2026-05-18 因未执行精确去重，导致 59 次重复上传尝试，23 个重复视频进入 YouTube，配额耗尽。之后必须使用精确去重，不用模糊匹配。

## 关键教训（除非你读过 `lessons.md`，否则一定会踩的坑）

1. **三层去重，缺一不可** — L1 本地 → L2 description 搜索 → L3 视频列表，不满足任何一层则跳过
2. **PENDING_UPLOAD 状态已被禁止** — 只记录成功或跳过，不记录待处理状态
3. **竖版视频自动检测** — 所有 QC 必须检查图片和渲染结果是否为横版（≥16:9），否则 pipeline 立即中止
4. **Drive 资产缺失修复** — 旧版 pipeline 从未上传 Drive，运行 `backfill_drive_assets.py` 补齐（每次最多 5 个）
5. **SA Drive 存储配额为 0** — 只能用 OAuth 凭证上传，SA 只读/list
6. **concat.txt 音频时长 > 图片总时长** — 必须计算 gap 后补正确 duration，gap 负数时修剪最后一帧时长
7. **active_runs.json 幽灵状态** — 步骤标记 ok 但 /tmp 文件已清理时，`_sanitize_active_run()` 在每次 cron 开始时检测 /tmp 文件存在性，缺失则级联重置
8. **drive_recovered blocks 时间戳全为 0** — 每段最小 5s 导致总视频极短。检查 blocks JSON 的 end_time 字段，发现全 0 则重置所有步骤
9. **macOS 大量 Drive 下载后 Errno 49 socket 耗尽** — `download_audio()` 加 3 次重试（30s/60s）；backfill 每条间隔 `sleep(8)` 释放 TIME_WAIT
10. **326 个 pipeline 输出文件散落在 Drive 根目录** — 必须写入对应子目录，不要经过 root
