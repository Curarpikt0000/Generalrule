---
name: youtube-reviewer
description: 每完成一个 YouTube Automation 阶段后调用，通过 delegate_task 启动 Claude Sonnet 子代理进行质检
version: 2.17.0
modified: 2026-05-18 - Added dual magazine+date matching bugfix; added backfill-description-tags reference; added scan-date-matching-bug reference; added backlog-wsj-20260302 reference
tags: [youtube, review, qa, delegation]
---

# 最终目标
生成可以直接发布到 YouTube 的横版视频（16:9），配合 Bloomberg 杂志音频，
向中文观众展示宏观经济内容分析。
每一个阶段的输出，必须从"这个东西放进最终 YouTube 视频里，观众看了会满意吗"来判断。

# 调用方式

delegate_task(
    prompt="""
你是 YouTube 内容质检员。唯一标准：
这个输出放进最终 YouTube 视频里，观众看了会满意吗？

最终视频规格：
- 平台：YouTube，横版 16:9，1920×1080
- 语言：中文内容，中文观众
- 风格：电影质感，专业财经频道水准
- 音频：Bloomberg 杂志音频同步

审查以下输出：
{粘贴 Worker 本阶段的完整输出}

各阶段质检标准：

【转录阶段】
- 文字总量合理（33分钟音频 > 5000字）
- 无明显乱码或段落缺失
- 中文表达自然，无机器翻译腔

【Block JSON 阶段】
分段原则：每个 block 必须是一个完整的"故事单元"——
有独立的叙事弧线（背景→冲突→结论），不能是零散观点堆砌。

质检标准：
- 5-10个 block，每个 block 对应音频中一个独立话题/故事
- 每个 block 的 summary 必须足够完整，让画师仅凭这段文字
  就能设计出一张信息图——包含核心论点、关键数据、视觉隐喻方向
- summary 字数：每个 block 不少于 150 字（推荐 200+ 字，带具体数据）
- 分段边界清晰：block 之间话题不重叠，逻辑不跳跃
- keywords 3-5个，能概括该 block 的视觉主题
- JSON 格式正确可解析

判断标准：
把每个 block 的 summary 单独读，如果能清楚知道"这段讲了什么故事、
有什么数据支撑、可以画什么图"，才算 APPROVED。
否则 RETRY，要求补充具体数据和视觉描述。

⚠️ **Block JSON 时间格式陷阱**（2026-05-14 新增）：
生成 blocks 时，`start_time` 和 `end_time` 必须以 `"HH:MM:SS"` 字符串格式输出。
如果 delegate_task 以整数秒数输出（如 `"start_time": 125`），必须修正为 `"00:02:05"`。
修正方法：
```python
def secs_to_hms(s):
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return f'{h:02d}:{m:02d}:{sec:02d}'

for b in blocks:
    if isinstance(b.get('start_time'), int):
        b['start_time'] = secs_to_hms(b['start_time'])
        b['end_time'] = secs_to_hms(b['end_time'])
```
总时长 = last_end_time 转换为秒数 = ffprobe 音频时长（取整）。
**生成后必须验证**：最后一秒的 end_time 转换后应等于音频时长。

⚠️ **Block 1 预告陷阱**（2026-05-14 新增）：
视频开篇 block 常写成"全篇预告"，把后续 blocks 的核心悬念和数据都提前泄露。
这导致 Block 1 与后续 blocks 结构性内容重叠，观众前几分钟听完全部悬念。

**质检时必须检查：**
- Block 1 的 summary 是否只聚焦开场画面/钩子，不提前泄露后续 blocks 的核心论点和数据
- 如果 Block 1 的 summary 包含了后续 block 的数据，要求删掉
- Block 1 应以开放式悬念结尾，而非结论式预告
- **keywords 与 summary 必须同步**：修改 summary 后同步更新 keywords，
  删掉后续 block 才涉及的话题关键词

⚠️ **JSON 编码陷阱（已踩坑）**：
- Block summary 中的中文双引号（" "）会导致 JSON 解析失败
- Python json.dump() 会自动转义，但如果手写 JSON 字符串容易漏
- 始终用 Python dict + json.dump(ensure_ascii=False) 写入
- 写完后用 python3 -m json.tool 或 json.loads() 验证
- 如果手动编辑 JSON，summary 中的引号用「」代替

📐 Block JSON v5 格式规范（2026-05 确立）：
每个 block 包含且仅包含以下 **7 个字段**，字段名必须完全匹配：

```json
{
  "title": "中文标题（不要用 block_id 字段）",
  "argument": "一句话核心观点（不要用 topic 字段）",
  "start_time": "00:00:00",  /* 必须 HH:MM:SS 字符串格式，不是整数秒数！*/
  "end_time": "00:02:05",    /* 必须 HH:MM:SS 字符串格式，不是整数秒数！*/
  "summary": "中文叙述 ≥200字，含核心故事+具体数据+视觉方向",
  "keywords": ["关键词1", "关键词2", "关键词3"],
  "visual_prompt": "英文 prompt 用于图像生成 API，含具体视觉隐喻 + 1-2个关键数据视觉呈现"
}
```

⚠️ **字段名陷阱**（2026-05-14 踩坑 2 次）：
- ❌ 不要用 `block_id` 代替 `title`
- ❌ 不要用 `topic` 代替 `argument`
- ❌ 不要用 `id` 代替 `title`
- ❌ `start_time`/`end_time` 必须是 `"HH:MM:SS"` 字符串，**不是**整数秒数
- 验证：写入后用 `python3 -c "import json; json.load(open('file.json'))"` 检查

📐 **Block JSON core_topic 字段**（2026-05-15 确立）：
每个 Block JSON 文件应包含顶层字段 `core_topic`，用于封面视觉隐喻选择：
```json
{
  "core_topic": "economy_domino",
  "blocks": [...]
}
```
core_topic 映射表见 references/cover-metaphor-mapping.md。
该字段在封面生成脚本中读取以选择正确的视觉 prompt。
每个 visual_prompt 末尾必须追加以下内容（不要遗漏）：
```
Shot on ARRI Alexa cinema camera, anamorphic lens bokeh, 
shallow depth of field, foreground elements slightly out of focus,
dramatic volumetric lighting with visible light rays,
cinematic color grading, deep shadows with rich blacks,
film grain texture, ultra-realistic photographic quality,
16:9 cinematic aspect ratio
```

【图片阶段】（最严格）
⚠️ 历史教训：2026-05 曾用 Pillow-only 纯色文字图，被用户退回重做。
必须使用两步法：图像生成 API 做背景 + Pillow 叠加文字。

每张图的目标：观众在视频里看到这张图，0.5秒内就知道这个 block 在讲什么。

硬性要求（任何一条不满足直接 RETRY）：
- 尺寸必须是 1920×1080（横版 16:9）
- 无中文乱码
- 图片主题与对应 block 的核心论点直接相关

内容质量要求：
- 图片必须是信息图风格：有视觉化的数据、图表元素、或强烈的隐喻画面
- 不接受 Pillow-only 纯色背景 + 文字的组合（那是 PPT，不是信息图）
- 每张图应包含该 block 的 1-2 个关键数据或核心概念的视觉呈现
- 底部论点条文字清晰，字号足够在手机屏幕上可读
- 整体观感：Bloomberg、经济学人级别的信息图水准

图片生成流程（两步法：图像生成API做背景 + Pillow叠加文字）
禁止 Pillow-only 纯色文字方案，也禁止让 Imagen 直接渲染文字到图中）

图像生成后端优先级（按用户偏好排列）：
- ✦ Vertex AI Imagen 3：首选，已验证可用。SA路径见 references/vertex-ai-imagen.md
  注意：SA 路径在 /Users/chaojin/hermesagent/Youtube video/ 下，不是跟目录
- ✦ FAL.ai (Flux Pro)：备选，但 FAL_KEY 可能未配置。见 references/fal-image-generation.md

第一步：调用图像生成 API 生成电影质感背景图
- 从 block JSON 的 `visual_prompt` 字段读取视觉描述（该字段在 v5 格式中）
- 内容图 prompt 模板——使用 NotebookLM 暖白风格（见 references/notebooklm-style-guide.md）：
  ```
  NotebookLM clean editorial infographic style, warm ivory and cream background,
  muted earth tones, sage green and terracotta accents, soft natural lighting,
  minimalist composition, elegant magazine infographic aesthetic,
  16:9 landscape 1920x1080,
  [从 block['visual_prompt'] 读取, 但确保不含展板/文档/屏幕元素],
  NO TEXT, NO LETTERS, NO NUMBERS, NO WORDS, NO CAPTIONS, NO LABELS anywhere in the image.
  Pure visual background only.
  ```
- 封面图（cover）的 prompt 模板：
  ```
  NotebookLM clean editorial infographic style, warm ivory and cream background,
  muted earth tones, sage green and terracotta accents, soft natural lighting,
  minimalist composition, elegant magazine cover,
  abstract financial world visualization, macro economy theme,
  soft geometric shapes, editorial photography aesthetic,
  NO TEXT, NO LETTERS, NO NUMBERS, NO WORDS, NO LABELS anywhere in image.
  ```
- 封面 prompt 必须包含 "NO TEXT, NO LETTERS"，用封面专用模板

第二步：用 Pillow 在生成的背景图上叠加中文文字
⚠️ macOS 字体路径：/System/Library/Fonts/STHeiti Medium.ttc（不要用 /usr/share/fonts/）
   Linux 服务器用 NotoSansCJK

内容图布局规范（1920×1080）：
- 左侧橙色竖线：x=80, y=80~1000, 宽6px, 颜色 #F0A500
- 标题：左上 x=110, y=80, STHeiti Medium 72px, 白色 + 2px黑色描边（用 dx,dy 循环实现）
- 底部半透明黑色条：y=900~1080, rgba(0,0,0,0.75)
- 底部论点一句话：x=110, y=930, STHeiti Medium 48px, 白色 + 1px黑色描边
- 右下：不显示时间戳（时间戳只保留在 JSON 的 start_time/end_time 字段中）

### 封面图布局规范（2026-05-14 更新 — 极简版）

⚠️ 用户明确要求：封面**只放杂志名称 + 日期**，不要放所有 topic block 的标题/简介列表（遮住画面、看不清）。

所有杂志统一布局：
1. 杂志名（如"New Yorker"/"华尔街日报"）：左上角大号，橙色 #FFC832 / 黄色，带描边
2. 日期（YYYY年MM月DD日）：下方或右侧，白色/柔和灰色，中等字号
3. 背景：Imagen 生成的深色电影质感图
4. 无底部条/无 argument 总结/无 block 标题列表
5. 不显示进度/页码

**命名规范：**
- 封面：{Magazine}_{日期}_cover.png
- 内容图：{Magazine}_{日期}_block_{编号}.png (编号 01-99)

【视频阶段】
- 时长与音频完全匹配
- 音画同步，偏差 < 0.5秒
- 画面切换节奏自然
- 整体观感：专业财经 YouTube 频道水准

【Drive 上传阶段】
- 文件存在于正确路径
- 命名符合 {杂志名}_{日期} 规范

输出格式只能是以下三种之一：
APPROVED：[一句话说明为什么达到 YouTube 发布标准]
RETRY：[具体问题 + Worker 必须执行的修改指令]
ESCALATE：[需要用户介入的原因]
    """,
    model="claude-sonnet-4-6",
    provider="anthropic",
    max_turns=3,
    toolsets=[]
)

# 收到结果后的处理
- APPROVED → 继续下一阶段，不打扰用户
- RETRY → 按指令重做，最多重做 2 次后再次质检
- ESCALATE → 立即通知用户，停止流程

## 风格确认策略（2026-05-15 更新 — 用户授权全自动模式）

用户已明确授权：**不需要逐张确认封面/图片风格**。所有文件自动生成、自动上传，用户会定期查看频道，有问题时主动反馈。

⚠️ 仅当**首次使用全新风格**（如从深色切到全新的视觉语言）时，才发第1张封面给用户快速确认。同杂志后续文件直接沿用。

# ⚠️ 自主执行规则（2026-05-17 用户强调 — 全自动模式）
用户已明确要求：
1. **处理队列内所有剩余文件直到全部完成**，中间不要停下
2. **不要在每期完成后询问是否继续** — 自动开始下一个
3. **只在 ESCALATE 或发生错误时联系用户**
4. **每完成一期发一条简短完成通知**（含链接），立即开始下一个，不等回复
5. **不需要用户确认封面风格/图片风格/任何中间步骤** — 全自动
6. 不等待用户回复。不询问"要不要继续"
7. 如果遇到非致命错误（如Imagen 429、临时网络波动），自动重试，不中断流水线
8. 如果遇到致命错误（配额用尽、ESCALATE），记录后停下来通知用户

## 串行处理规则（用户严格要求）
虽然处理是串行的，但可以在当前文件处理过程中**提前下载后续文件**（下载是纯网络I/O，不会引发配额冲突）：
```python
# 在图片生成/视频渲染的后台等待期间，启动预下载
python3 -c "
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
SA_PATH = '/Users/chaojin/hermesagent/Youtube video/hermes-infra-prod-9c5abf6aefe8.json'
creds = service_account.Credentials.from_service_account_file(SA_PATH, scopes=['https://www.googleapis.com/auth/drive'])
service = build('drive', 'v3', credentials=creds, cache_discovery=False)
for fid, fname in files:
    OUT = f'/tmp/{fname}.mp3'
    if os.path.exists(OUT) and os.path.getsize(OUT) > 1024*1024: continue
    ...download...
```
这可以节省每文件 30-60 秒的下载等待时间。

## ⚠️ 标题格式（用户偏好 — 2026-05-14 多次踩坑后明确）

**必须格式：** `《杂志名称》YYYY年MM月DD日[解读/深度解读] - 关键词1、关键词2、关键词3`

- 杂志名用《》括起来
- 日期：YYYY年MM月DD日（不要用 YYYY.MM / YYYY-MM-DD 等变体）
- 统一用"解读"或"深度解读"，不要用"深度解析""中文解读""中文播客"等
- 关键词：从 blocks JSON 的 title/argument 提炼 3-5 个，顿号分隔
- ❌ 不要用 `｜` 符号、双标题、点击式/标题党用语
- ❌ 不要用机翻式或感叹式标题

**对比示例（已踩坑）：**
| ✅ 正确 | ❌ 错误 |
|---------|---------|
| 《华尔街日报》2026年4月10日深度解读 - 教授当园丁、HOA超房贷、生育率1.57 | 一把美工刀摧毁1800万防沙堤...成为时代最危险的慢性毒药 |
| 《纽约客》2026年4月27日解读 - 数据炼狱、WWE治国、失败博物馆、AI永生 | 数据炼狱、WWE治国与失败博物馆——数字时代的脆弱救赎｜New Yorker中文解读 |

**修正方法**（已有视频改标题）：
```python
# GET current snippet first to preserve categoryId
r = youtube.videos().list(part='snippet,status', id=video_id).execute()
snippet = r['items'][0]['snippet']
snippet['title'] = new_title
youtube.videos().update(part='snippet,status', body={
    'id': video_id, 'snippet': snippet, 'status': r['items'][0]['status']
}).execute()
```
注意：PUT 时必须传递**完整 snippet**（含 categoryId 等必填字段），只传 title 会 400 错误。

## ⚠️ 上传方式选择（2026-05-17 更新）

### upload_video.py 为首选，但有已知 bug
使用 `~/hermesagent/Youtube video/magazine/upload_video.py` 处理：Token refresh、缩略图压缩、防重复检查、每日配额检查。

⚠️ **upload_video.py 文件可能不存在**（2026-05-17 session 验证）：`~/hermesagent/Youtube video/magazine/upload_video.py` 和 `~/magazine/scripts/upload_video.py` 均可能不存在。当找不到时，不要尝试创建——直接用 ad-hoc 上传脚本替代，覆盖所有必需项即可。

⚠️ **upload_video.py 已知 bug（2026-05-17 发现）**：
- **缩略图 RGBA 模式问题**：cover.png 以 RGBA 保存时，上传缩略图报 `cannot write mode RGBA as JPEG`。原因是内部代码未做 RGBA→RGB 转换。遇到此错误时，用脚本手动上传缩略图。
- **--check 模式 bug**：`python3 upload_video.py --check` 报 `required` 参数错误无法独立运行。用 YouTube API 脚本手动检查配额。
- **emoji 触发安全扫描**：--description 中不要包含 emoji 字符（Unicode 变体选择器被 Hermes TIRITH 标记）。

### Ad-hoc 上传脚本适用场景
当 upload_video.py 的 bugs 影响到上传时（RGBA 问题、--check 问题），可以编写专用上传脚本作为替代。**确保专用脚本同样覆盖**：
- ✅ Token 刷新（refresh_token 机制）
- ✅ 缩略图压缩（1280×720 JPEG < 1.9MB）
- ✅ 缩略图 race condition 处理（上传后等 20s 再设置）
- ✅ processed.txt 记录追加
- ✅ 每日配额检查（playlistItems API）
- ✅ PDF 封面叠加（流水线最后一步）

**2026-05-17 验证**：ad-hoc 上传脚本成功上传 2 个 Atlantic 视频（含 PDF 封面叠加 + 缩略图 + 配额检查），所有功能覆盖。优先用 upload_video.py，在它出问题时可以用脚本替代——只要覆盖所有 checkmark 项。

### 常用上传代码模板
```python
# Step 1: Initiate resumable upload
r = req_lib.post(
    "https://www.googleapis.com/upload/youtube/v3/videos?part=snippet,status&uploadType=resumable",
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
             "X-Upload-Content-Length": str(file_size), "X-Upload-Content-Type": "video/mp4"},
    json=body_json, timeout=30)
if "exceeded" in r.text: break  # quota full
upload_url = r.headers["Location"]

# Step 2: Upload file bytes
with open(video_path, "rb") as vf:
    r2 = req_lib.put(upload_url, data=vf.read(),
        headers={"Content-Length": str(file_size), "Content-Type": "video/mp4"}, timeout=600)
video_id = r2.json()["id"]

# Step 3: Wait then thumbnail
import time; time.sleep(20)
cover = Image.open(cover_path).convert('RGB').resize((1280, 720), Image.LANCZOS)
buf = io.BytesIO()
for q in range(92, 10, -5):
    buf.seek(0); buf.truncate()
    cover.save(buf, 'JPEG', quality=q, optimize=True)
    if buf.tell() < 1900 * 1024: break
req_lib.post(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={video_id}",
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'image/jpeg'},
    data=buf.getvalue(), timeout=30)
```

## ⚠️ 缩略图 race condition（2026-05-14 教训）

Freshly uploaded video returns HTTP 404 on `thumbnails/set` for ~15-30 seconds while YouTube processes the video. **Do NOT re-upload the whole video.** Wait 20s and retry just the thumbnail upload.

The unified `upload_video.py` handles this inside its flow — always use it with `--cover /path/to/cover.png`:
```bash
python3 ~/hermesagent/Youtube video/magazine/upload_video.py /tmp/video.mp4 \
  --title "《杂志》YYYY年MM月DD日解读 - 关键词" \
  --description "...描述..." \
  --tags "标签1,标签2" \
  --category "25" \
  --cover /tmp/ny_images_0420/NewYorker_20260420_cover.png
```

If you get HTTP 404 on thumbnail but video uploaded OK, retry thumbnail separately:
```python
# Wait 20s, then retry thumbnail
import time; time.sleep(20)
# Upload thumbnail directly (not re-upload video)
```

## ⚠️ delegate_task 超时处理（2026-05-18 新增）

**发现**：将完整流水线（图片生成+渲染+上传）通过 `delegate_task` 委托给子代理时，Imagen 3 API 调用（5-15秒/张，8张图=40-120秒，含重试可达5-10分钟）导致子代理频繁超时（600s）。子代理在超时后可能已经完成了部分工作（如转录、blocks JSON、部分图片），但状态被丢弃。

**正确处理流程（2026-05-18 验证）**：
1. **不要在 delegate_task 中做图片生成**——Imagen API 太慢，600s timeout 不够
2. 用 `delegate_task` 仅做分析/质检类任务（如 Review Block JSON）
3. 图片生成+渲染+上传这些长时间操作直接在 `terminal()` 中前台执行，设置 `timeout=600`
4. 或在 cron session 的主 agent 中直接写 Python 脚本执行

**中断恢复**：当 subagent 超时后，检查 `/tmp/` 目录下是否已有部分产出：
- 有 `_transcript.txt` 但无 `_blocks.json` → 需生成 blocks（手动 Python 脚本）
- 有 `_blocks.json` + 图片目录 → 尝试渲染+上传
- 有 `_final.mp4` → 直接上传

继续处理中断的文件时，优先复用已有的中间产出，不要从头开始。

## ⚠️ processed.txt 路径统一（2026-05-18 纠正）

**正确路径**（所有命令和代码模板中必须使用）：
```
~/hermesagent/Youtube video/magazine/processed.txt
```

**旧的错误路径**（仍散落在以下位置，发现时必须修正）：
- ❌ `~/magazine/processed.txt`（展开为 `/Users/chaojin/magazine/processed.txt` — scan_and_reconcile.py 里硬编码了此路径，2026-05-18 已修复）
- ❌ `/Users/chaojin/magazine/processed.txt`

上传脚本路径：
```
~/hermesagent/Youtube video/magazine/upload_video.py
```

所有代码模板中的 `~/magazine/` 路径应视为已废弃。
1. 同一阶段重做超过 2 次仍失败
2. 需要用户账号或物理操作
3. 花费明显超出预期

## ⚠️ 已完成上传历史（已弃用 — 改用实时扫描）

**此表格已弃用。** 频道已增长到 116+ 个视频，静态历史表已无法维护。上传前的重复检查应依赖于：
1. `processed.txt` 的 Drive ID 集合
2. YouTube playlistItems API 的实时日期扫描
3. 两者的并集作为已处理基线

历史教训：2026-05-13 Science 同一个音频被上传了两次（`tuQb9rvBsnU` 和 `pJtEo1MorMY`），原因是两个不同 session 同时跑了上传逻辑。验收标准：同一个音频文件只应生成一个视频。为避免再次发生：
- 上传前先查 processed.txt 看该文件是否已有 YouTube URL
- 如已存在，**不要再上传**，而是通知用户已有视频
- 如果必须重传，先删除旧视频再上传新的
- 删除用：`youtube.videos().delete(id='VIDEO_ID').execute()`

## 视频标题规范（用户偏好 — 2026-05-14 更新）

**必须使用以下格式：**
```
《杂志名称》YYYY年MM月DD日[解读/深度解读] - 关键词1、关键词2、关键词3
```

**规则：**
1. 杂志名用书名号《》包裹
2. 日期格式：YYYY年MM月DD日（如：2026年4月10日）
3. 统一用"解读"或"深度解读"（保持简洁），不用"深度解析""中文解读"等变体
4. 关键词从 blocks JSON 的 title/argument 中提炼，用顿号分隔（不是斜杠/竖线）
5. 包含 3-5 个核心关键词，覆盖该期最重要的几个话题
6. **不要用** `｜` 符号，不要用花哨的副标题/双标题
7. **不要用**机翻式或点击式标题（如"一把美工刀摧毁..."）

**正确示例：**
- ✅ `《华尔街日报》2026年4月10日深度解读 - 教授当园丁、HOA超房贷、生育率1.57`
- ✅ `《纽约客》2026年4月20日解读 - 新奥尔良撞车工厂、Slammers产业链、空心墙隐喻`
- ✅ `《科学》2026年3月刊解读 - AI顺从陷阱、姆潘巴效应、表观遗传与摩擦哲学`

**错误示例（已踩坑）：**
- ❌ `数据炼狱、WWE治国与失败博物馆——数字时代的脆弱救赎｜New Yorker中文解读`
- ❌ `一把美工刀摧毁1800万防沙堤到美伊停火引爆市场：控制幻觉如何成为时代最危险的慢性毒药`
- ❌ `68岁AI高手主动退休！高盛震撼数据：AI真正受害者是老员工｜WSJ深度解析`

**生成方法：**
从 block JSON 中提取各 block 的核心关键词（title/argument），取 3-5 个最相关的用顿号连接。

## 已知陷阱（持续更新）

## ⚠️ YouTube ↔ Drive 音频文件对账（2026-05-17 验证 — 每日 cron 任务第一步）

Drive 中存在多个同名或近名音频文件的副本（同一杂志出现在多个文件夹中），
processed.txt 只记录 Drive 文件 ID，不同文件夹的同名文件有不同的 ID。
直接按 Drive ID 判断「未处理」会误判大量文件为待处理。

**2026-05-17 session 发现的关键模式**：该方法验证筛选后 86 个原始文件→17 个真正未处理。

### ⚠️ Drive 重复文件夹扫描（2026-05-17 发现）

**现象**：`Globalmagzineyoutube/` 下有 16 个文件夹，但某些杂志出现两次（如 Barron's 有 2 个文件夹，Economist 也有 2 个）。其中一个可能是早期版本。

**正确的全量扫描方法**：
```python
mags = [
    ("Barron's", "ID_FOLDER_1"),
    ("Economist", "ID_FOLDER_1"),
    # ... 所有 16 个文件夹都扫描
    # 去重：用 file_id 做唯一键
]

all_audio = {}  # {file_id: {name, size, mag_name, year}}
for mag_name, mag_id in mags:
    years = list_all(service, f"'{mag_id}' in parents and mimeType='application/vnd.google-apps.folder'")
    for yf in years:
        audio_dirs = list_all(service, f"name='audio' and '{yf['id']}' in parents")
        for ad in audio_dirs:
            files = list_all(service, f"'{ad['id']}' in parents and mimeType contains 'audio'")
            for ff in files:
                if ff['id'] not in all_audio:  # 去重！
                    all_audio[ff['id']] = {'name': ff['name'], 'size': int(ff.get('size', 0)), 'mag_name': mag_name, 'year': yf['name']}
```

**验证过的对账方法（每日 cron 任务的第一步）：**
1. 读取 processed.txt 获取已处理的 Drive 文件 ID 集合
2. 扫描 **所有 19 个文件夹**（含重复/第二份文件夹）的 audio/ 子目录，获取所有音频文件 ID
3. 按 Drive 文件 ID 对比找出「未见过的」音频文件
4. 这对账只可靠于 Drive 文件 ID 级别，不能依赖文件名匹配
5. 对于不在 processed.txt 中的文件 ID，检查 /tmp/ 目录看该文件是否已被下载（通过文件名日期匹配）
6. 再在 YouTube 上按日期搜一遍确认是否真的未上传

⚠️ **Duplicate folder scanning nuance（2026-05-18 session 验证）**：某些杂志有 2 个文件夹（如 Economist, Barron's, Science, WSJ, Foreign Affairs）。大多数文件在所有文件夹间相同（不同 Drive ID 但同日期），但某些日期**仅出现在第二份文件夹中**（如 Economist 2nd 文件夹有 20260321、20260328、20250920 在主文件夹不存在的文件）。因此不能只扫描单份文件夹。去重时：先按 Drive ID 去重，再把所有不同 ID 作为「待检查」候选，用 YouTube playlistItems API 按日期二次过滤。

⚠️ **processed.txt 的 Drive ID 可能不正确**（2026-05-18 发现）：当从 /tmp/ 本地音频处理而非从 Drive 下载时，上传脚本记录的是**其他文件的 Drive ID**。例如 `economist_20250920.mp3` 记录成了 `102EOYblbDDc...`（实际是 economist_20260321 的 ID）。这导致未来扫描时 `economist_20250920`（ID: `1X3u_QnS6WShD...`）被识别为"新文件"。**修复方法**：在 processed.txt 中记录正确的 Drive ID（从扫描结果获取），或在扫描时除了检查 Drive ID 也检查日期。

**快速对账脚本模板：**
```python
# Step 1: 读取 processed.txt
processed_ids = set()
with open('/Users/chaojin/hermesagent/Youtube video/magazine/processed.txt') as f:
    for line in f:
        parts = line.split(',')
        if parts[0].strip():
            processed_ids.add(parts[0].strip())

# Step 2: 扫描 Drive 所有 audio/ 目录
from google.oauth2 import service_account
from googleapiclient.discovery import build
SA_PATH = '/Users/chaojin/hermesagent/Youtube video/hermes-infra-prod-9c5abf6aefe8.json'
creds = service_account.Credentials.from_service_account_file(SA_PATH, scopes=['https://www.googleapis.com/auth/drive'])
service = build('drive', 'v3', credentials=creds, cache_discovery=False)

# 遍历 Globalmagzineyoutube/{杂志}/{年份}/audio/
new_files = {}  # {file_id: {name, size, magazine}}
for mag_id in all_magazine_folder_ids:
    years = service.files().list(q=f\"'{mag_id}' in parents and mimeType='vnd.google-apps.folder'\").execute()
    for yf in years['files']:
        audio_dirs = service.files().list(q=f\"name='audio' and '{yf['id']}' in parents\").execute()
        for ad in audio_dirs['files']:
            files = service.files().list(q=f\"'{ad['id']}' in parents and mimeType contains 'audio'\").execute()
            for ff in files['files']:
                if ff['id'] not in processed_ids:
                    new_files[ff['id']] = {'name': ff['name'], 'size': int(ff['size'])}

# Step 3: 对于 each new_file_id，在 YouTube 上按日期确认
today = datetime.now().strftime('%Y-%m-%d')
youtube = build('youtube', 'v3', credentials=youtube_creds)
uploads = youtube.playlistItems().list(part='snippet', playlistId=uploads_id, maxResults=50).execute()
yt_titles = {i['snippet']['title'] for i in uploads['items']}
for fid, info in sorted(new_files.items()):
    # 提取日期，检查 YouTube 上是否有同日期视频
    if date_already_on_youtube(info['name'], yt_titles):
        continue  # 已在 YouTube，跳过
    # 真正的新文件 → 加入处理队列
```

**教训（2026-05-17 踩坑）**：第一次扫描显示 64 个「未处理文件」，但其中大部分已在 YouTube 上（只是用了不同的文件名和 Drive 文件夹路径）。最终通过 YouTube playlistItems API 验证后，真正的新文件只有 22 个。

## ⚠️ 从 blocks JSON 构造 upload 命令（2026-05-18 新增）

每次上传视频时，需要从 blocks JSON 中提取标题和关键词来构造 `upload_video.py` 的命令参数。使用以下方法从 block titles 提取关键词（不要手动编造）：

```python
with open('blocks.json') as f:
    data = json.load(f)
blocks = data.get('blocks', data if isinstance(data, list) else [])
keywords = [b.get('title','').split('：')[0][:6] if '：' in b.get('title','') else b.get('title','')[:6] for b in blocks[:5]]
title_suffix = '、'.join(keywords)
```

最终命令模板：
```bash
cd ~/hermesagent/Youtube\\ video/magazine && python3 upload_video.py /tmp/{SLUG}_final.mp4 \\
  --title "《杂志》YYYY年MM月DD日深度解读 - 关键词1、关键词2、关键词3" \\
  --description "文本描述（纯文本，无emoji，用1. 2. 3. 编号）" \\
  --tags "标签1,标签2" --category 25 \\
  --cover /tmp/{IMG_DIR}/{COVER}.png
```

## ⚠️ Pipeline 停滞/假死诊断协议（2026-05-18 新增）

**场景**：Claude监督或用户报告"81分钟无进展"、"14/15文件完成，卡住"等停滞信号。

**诊断步骤（按顺序执行，不需要问用户）：**

1. **检查 cron job 状态**：`cronjob(action='list')` → 查看 `last_status` 是否为 `ok`
2. **检查 processed.txt 最新条目**：最后几条记录是否有 YouTube URL？
   ```bash
   tail -10 ~/hermesagent/Youtube video/magazine/processed.txt
   ```
3. **校验 YouTube URLs 是否真实存在**：在 YouTube 上搜索对应视频 ID 确认已发布
4. **检查扫描结果**：读取最新 `scan_result.json`（通常在 /tmp/），对比 `truly_new` / `already_on_yt` 分类
5. **关键洞察**：Drive 扫描按 **Drive 文件 ID** 判断"新文件"，但 processed.txt 可能记录了**不同 Drive ID 的同一个文件**。因此 scan_result.json 报告的"新文件"可能是已经处理过的副本。判断标准：**processed.txt 中有 YouTube URL 即视为已处理，不管 Drive ID 是否匹配**

**常见误报原因：**
- Claude监督检测到 cron session 的"最后更新时间"后未看到新的通知 → 但流水线实际已完成
- Drive 扫描报告4个"新文件"但其中3个已有 YouTube 视频（不同 Drive ID 的副本）
- cron session 已完成全部任务并退出 `ok`，但监督者看到的是旧状态的快照

**正确结论的确认方法：**
```bash
# 快速检查流程
grep -i '20260313\|20260304\|20260331\|unknown\|barrons_20260406' processed.txt
# 如果都有 YouTube URL → ✅ 已处理，不是卡死
```

## ⚠️ 相同音频多日期重复陷阱（2026-05-17 发现）

**现象**：Foreign Affairs 2025-01-01 和 2025-07-01 的音频文件内容完全一致（相同转录文本、相同长度、相同 Whisper 输出），但日期标签不同。

**根因**：可能是同一中文播客被上传到 Drive 时标了不同日期，或者备份副本。Drive 文件 ID 不同所以扫描时会被识别为「未处理」文件。

**处理方案：**
1. 转录完成后，计算转录文本的 SHA256 或比较长度 + 前 300 字符
2. 与已处理的转录文本比较（缓存到 /tmp/ 或 processed.txt 备注中）
3. 如果检测到内容一致仅日期不同：生成新封面（新日期+新PDF封面），复用已有 block JSON 和 block 图片
4. 记录到 processed.txt 时标注 (SAME_CONTENT_AS: {original_date})

**快速检测模板（替代完整转录——直接比较音频文件MD5前10MB）：**
```python
import hashlib
# Compare first 10MB of two .mp3 files
hash1 = hashlib.md5(open('file1.mp3','rb').read(10*1024*1024)).hexdigest()
hash2 = hashlib.md5(open('file2.mp3','rb').read(10*1024*1024)).hexdigest()
if hash1 == hash2: print("SAME CONTENT - duplicate!")
```
**优势**：不需要等待 Whisper 转录完成就知道是否重复，节省数分钟。
**何时执行**：下载音频后立即执行，与队列中其他文件的第1个10MB MD5比较。

## ⚠️ scan_and_reconcile.py 脚本维护陷阱（2026-05-17/18 修复）
`scan_and_reconcile.py` 的 import 行有历史遗留 bug：`import datetime` 与 `from datetime import datetime, timezone` 混合使用，导致 `datetime.timedelta` 引用失败。
**修复方法**：确保只用 `from datetime import datetime, timezone, timedelta`，不要同时 `import datetime`。

**第二个 bug（2026-05-18 修复）**：脚本硬编码 `/Users/chaojin/magazine/processed.txt` 读取已处理文件列表，但规范路径是 `/Users/chaojin/hermesagent/Youtube video/magazine/processed.txt`。修复方法：搜索脚本中的旧路径并替换为正确的规范路径。
**教训**：所有引用 processed.txt 的脚本都必须使用规范路径，不得使用 `~/magazine/` 变体。

**快速检测模板：**
```python
def is_duplicate_content(new_transcript_path, existing_transcripts_dir='/tmp/'):
    """Check if this transcript matches any previously processed one"""
    import hashlib, os
    with open(new_transcript_path) as f:
        new_text = f.read()
    new_hash = hashlib.sha256(new_text.encode()).hexdigest()[:16]
    new_prefix = new_text[:300]
    
    # Check all existing transcripts
    for fname in os.listdir(existing_transcripts_dir):
        if fname.endswith('_transcript.txt') and fname != os.path.basename(new_transcript_path):
            with open(os.path.join(existing_transcripts_dir, fname)) as f:
                old_text = f.read()
            if old_text[:300] == new_prefix or hashlib.sha256(old_text.encode()).hexdigest()[:16] == new_hash:
                return True, fname  # Duplicate!
    return False, None
```
with open('/Users/chaojin/hermesagent/Youtube video/magazine/processed.txt') as f:
    for line in f:
        parts = line.split(',')
        if parts[0].strip():
            processed_ids.add(parts[0].strip())

# Step 2: 扫描 Drive 所有 audio/ 目录
from google.oauth2 import service_account
from googleapiclient.discovery import build
SA_PATH = '/Users/chaojin/hermesagent/Youtube video/hermes-infra-prod-9c5abf6aefe8.json'
creds = service_account.Credentials.from_service_account_file(SA_PATH, scopes=['https://www.googleapis.com/auth/drive'])
service = build('drive', 'v3', credentials=creds, cache_discovery=False)

# 遍历 Globalmagzineyoutube/{杂志}/{年份}/audio/
new_files = {}  # {file_id: {name, size, magazine}}
for mag_id in all_magazine_folder_ids:
    years = service.files().list(q=f"'{mag_id}' in parents and mimeType='vnd.google-apps.folder'").execute()
    for yf in years['files']:
        audio_dirs = service.files().list(q=f"name='audio' and '{yf['id']}' in parents").execute()
        for ad in audio_dirs['files']:
            files = service.files().list(q=f"'{ad['id']}' in parents and mimeType contains 'audio'").execute()
            for ff in files['files']:
                if ff['id'] not in processed_ids:
                    new_files[ff['id']] = {'name': ff['name'], 'size': int(ff['size'])}

# Step 3: 对于 each new_file_id，在 YouTube 上按日期确认
today = datetime.now().strftime('%Y-%m-%d')
youtube = build('youtube', 'v3', credentials=youtube_creds)
uploads = youtube.playlistItems().list(part='snippet', playlistId=uploads_id, maxResults=50).execute()
yt_titles = {i['snippet']['title'] for i in uploads['items']}
for fid, info in sorted(new_files.items()):
    # 提取日期，检查 YouTube 上是否有同日期视频
    if date_already_on_youtube(info['name'], yt_titles):
        continue  # 已在 YouTube，跳过
    # 真正的新文件 → 加入处理队列
```

**教训（2026-05-17 踩坑）**：第一次扫描显示 64 个「未处理文件」，但其中大部分已在 YouTube 上（只是用了不同的文件名和 Drive 文件夹路径）。最终通过 YouTube playlistItems API 验证后，真正的新文件只有 22 个。

## ⚠️ 静态未处理文件列表已弃用（2026-05-18 清理）

**不要维护静态未处理文件列表。** 此技能之前曾错误地维护了一个8个"未处理文件"的静态列表，但所有8个文件早在该列表编写时就已经上传到 YouTube。静态列表会快速过时，误导后续 cron 运行。

**正确做法：** 每次 cron 运行必须从头执行 Drive ID 扫描 + YouTube 日期对比对账，不要依赖任何静态清单或缓存摘要。只有实时全量对账才能可靠判断"真正未处理"的文件。

## ⚠️ 无 API 配额时的去重技巧（2026-05-18 验证）

**场景**：当 YouTube API 配额耗尽（每天 10,000 点）时，无法通过 `playlistItems().list()` 查询已经上传的视频。但 Drive 扫描可能报告几十个"新文件"（实际上是不同 Drive ID 的副本）。

**解决方案**：建立 processed.txt 的 **日期→YouTube ID 映射表**，绕过配额限制完成去重：

```python
# Step 1: 从 processed.txt 建立 date->yt_id 映射
import re
date_yt = {}
with open('/Users/chaojin/hermesagent/Youtube video/magazine/processed.txt') as f:
    for line in f:
        m = re.search(r'youtube\.com/watch\?v=([a-zA-Z0-9_-]+)', line)
        if m:
            vid = m.group(1)
            # 提取行中的 8 位日期
            for part in line.split(','):
                dates = re.findall(r'(\d{8})', part)
                for d in dates:
                    if d not in date_yt:
                        date_yt[d] = vid

# Step 2: 对每个"新" Drive 文件，按日期查询
for fid, info in sorted(new_files.items()):
    dates = re.findall(r'(\d{8})', info['name'])
    already = any(d in date_yt for d in dates)
    if already:
        # 已有 YouTube 视频，标记为 duplicate ID
        pass  # 写入 processed.txt 标注 (duplicate ID)
    else:
        # 当天真未处理或在配额恢复后需要 YouTube API 确认
        pass
```

**2026-05-18 验证**：当天扫描出 30 个"新" Drive 文件，全部通过日期映射表确认为已处理（YouTube API 配额已耗尽）。这说明日期映射表足够可靠，可以作为 YouTube API 配额耗尽时的 fallback 方案。

**注意事项**：
- 日期映射表只能匹配**同一天**的文件。如果同一音频被标为不同日期（如 Foreign Affairs 2025-01-01 / 2025-07-01），需要更深入的内容比较（MD5/转录比较）。
- 添加 duplicate ID 记录到 processed.txt 时，以 `(duplicate ID)` 注释标注，方便后续审计。
- 此方法依然无法检测"音频内容相同但日期不同"的重复——这种情况下还需要转录或 MD5 比较。

## 相关参考文件
- references/notebooklm-style-guide.md — NotebookLM 暖白信息图风格指南
- references/dark-tech-image-style.md — 深色科技感图片风格指南（2026-05-14 用户确认，默认风格）
- references/barron-style-guide.md — 巴伦周刊（Barron's）风格指南（2026-05-17 新增）
- references/imagen-no-text-prompt-engineering.md — Imagen 3 NO TEXT prompt 工程
- references/visual-prompt-diversity.md — Multi-composition approach — 每个 block 用不同构图和色调
- references/ffmpeg-image-slideshow-video.md — ffmpeg TS 片段视频渲染方案
- references/cover-layout.md — 封面图布局规范
- references/image-qa-checklist.md — 图片质检检查清单
- references/whisper-transcription.md — Whisper 转录配置
- references/fal-image-generation.md — FAL.ai 备选方案
- references/vertex-ai-imagen.md — Vertex AI Imagen 3 配置
- references/batch-pipeline-36-files.md — 36文件批量流水线的完整经验和时间估算
- references/manual-blocks-workflow.md — 手动 Block JSON 生成指南
- references/youtube-vs-drive-reconciliation.md — YouTube视频 ↔ Drive音频对账方法
- references/upload-video-path-confirmed.md — upload_video.py 路径确认（2026-05-18 验证）

## ⚠️ 转录文件名变体对标（2026-05-17 新增）

**陷阱**：同一个文件的转录文本可能以不同命名变体存在。例如 `WSJ_20260304_transcript.txt` 和 `wallstreetjournal_20260304_transcript.txt` 是同一内容但命名不同。

**根因**：不同 session 用了不同的 slug 命名规则：
| slug 格式 | 示例 |
|-----------|------|
| `wallstreetjournal` | wallstreetjournal_20260303 |
| `WSJ` | WSJ_20260304 |
| `barrons` | barrons_20260119 |
| `foreignaffairs` | foreignaffairs_20250501 |

**处理方案**：
1. 写 blocks/生成图片时，先按所有可能的命名变体查找已有文件
2. 找到后创建 symlink：`ln -sf /tmp/WSJ_20260304_transcript.txt /tmp/wallstreetjournal_20260304_transcript.txt`
3. 统一沿用 `/tmp/{杂志slug}_{YYYYMMDD}_transcript.txt` 格式
4. 杂志 slug 规则：全小写、去空格/连字符/引号（如 `barron's` → `barrons`）

## ⚠️ upload_video.py 描述文本触发安全扫描（2026-05-17 发现）

**现象**：当描述（--description）中包含 emoji 字符（如 🕸️ 🐭 1️⃣ 等）时，Hermes terminal 安全扫描器可能检测到 Unicode 变体选择器并阻止执行。

**解决方案**：在 upload 命令的 --description 中**不要包含 emoji 字符**。用纯文本代替：
```bash
# ❌ 会触发安全扫描
--description "本期内容：\n🕸️ 超级蛛丝...\n1️⃣ 第一段..."
# ✅ 安全
--description "本期内容：\n超级蛛丝...\n1. 第一段..."
```

**根因**：emoji 序列中的 Unicode 变体选择器（VS1-256）被 Hermes TIRITH 安全扫描器标记。不影响上传后 YouTube 侧显示。

**PIPELINE CHECKLIST — 上传前必须检查：**
1. --description 中不含任何 emoji 字符（用纯文本数字编号代替）
2. --title 使用《》书名号包裹杂志名
3. --tags 不含特殊字符（#号在生产环境中自动添加，不需要手动加）

## ⚠️ Imagen 3 SDK 废弃警告（2026-05-17 发现）
从 `vertexai.preview.vision_models` 导入 `ImageGenerationModel` 时会显示废弃警告（2025年6月起标记废弃，2026年6月移除）。当前仍可用。当API开始返回错误时备选：
- 迁移到 `vertexai.image_generation`（新SDK路径）
- 使用 FAL.ai (Flux Pro) 备选（见 references/fal-image-generation.md）
- 使用 Imagen REST API 直接调用

## ⚠️ Imagen 3 429 Quota 处理（2026-05-15 更新）
- 遇到 429 Quota exceeded 时，等待 60 秒后重试，最多重试 10 次
- 配额在等待后会间歇性恢复，无需申请提升
- 必须实现自动重试逻辑，不要因为 429 跳过任何 block 的生成
- 重试代码模板：
```python
for attempt in range(10):
    try:
        response = model.generate_images(...)
        break
    except Exception as e:
        if '429' in str(e):
            time.sleep(60)
        else:
            raise
```

## ⚠️ Imagen 3 静默空响应（2026-05-15 踩坑）
**现象**：`response.images[0]._pil_image` 抛出 `IndexError: list index out of range`。
**根因**：Imagen 的 safety filter 在检测到敏感内容时静默返回空列表 `[]`，不抛异常。

**常见触发场景**：prompt 包含以下元素时 silent block 概率高：
- 人物面部、儿童、学生（如 "child sitting", "classroom", "students"）→ 必须用抽象、无人的替代隐喻
- 暴力元素、武器、战争场景（如 "missile", "soldier", "weapon"）
- 政治敏感物品、国旗、现实政治人物
- 宗教符号、裸体、医疗手术场面
- ⚠️ **拳击台/擂台场景**（如 "boxing ring", "fighter in trunks"）→ 2026-05-17 被 blocked，改用抽象几何替代
- ⚠️ **地下基础设施/管道/下水道场景**（如 "underground pipes", "infrastructure"）→ 2026-05-17 被 blocked，改用水面倒影/天空视角替代
- ⚠️ **硬币/货币/金库场景**（如 "silver coins", "cascading coins", "vault with money"）→ 2026-05-18 Barron's prompt 被 blocked，改用抽象几何+数字界面替代
- ⚠️ **金融图表/股市截图/证券文件**（如 "stock certificates", "trading graphs"）→ 2026-05-18 安全过滤，改用水墨质感抽象曲线替代
- ⚠️ **穿越时空/历史与现代并置**（如 "16th century coin next to modern"）→ 被安全过滤，用抽象古董+数字光效替代
- ⚠️ **"shattered defense systems", "crumbling corporate logos" 等過於具象的戰爭/崩潰描寫** → 2026-05-17 WSJ 0303 封面生成被 blocked，改為 "abstract financial and geometric patterns" + "soft curved lines" 後成功
- ⚠️ **"shattered glass", "transparent glass cube" 等玻璃裂縫/破碎場景** → 2026-05-18 Barron's block_01 prompt 被 blocked，改用 gradient fallback。替代方案：用「漂浮幾何形狀 + 柔和光線」替代玻璃碎裂描寫。
- ⚠️ **"market crash", "war economy" 等直接的经济/战争描述** → 同上，改为抽象几何 + 浮动物体后通过

**处理方案**：生成图片后检查 `response.images` 是否为空，为空则使用纯色背景回退：
```python
response = model.generate_images(prompt=...)
if not response.images:
    print(f"  ⚠️ {label}: safety filter blocked, using fallback")
    return None  # caller will create solid-color bg
bg = response.images[0]._pil_image.resize((1920, 1080))
```

**⚠️ Safety filter fallback 质量陷阱（2026-05-18 新增）**：
当 safety filter 多次 blocked 后 fallback 到旧图片时，应：
1. 检查旧图片是否也是 Imagen 3 生成的（>200KB = Imagen, <100KB = Pillow-only）
2. 如果是 Pillow-only 旧图，生成渐变背景替代：
   ```python
   from PIL import ImageDraw
   bg = Image.new('RGB', (1920, 1080), (10, 15, 30))
   draw = ImageDraw.Draw(bg)
   for y in range(1080):
       r = int(10 + (y/1080)*20)
       g = int(15 + (y/1080)*25)
       b = int(30 + (y/1080)*15)
       draw.line([(0,y), (1920,y)], fill=(r,g,b))
   ```
3. 区分"Imagen blocked, fallback 到旧 Imagen 图"和"Imagen blocked, fallback 到纯色图"
4. 记录 blocked prompt 内容到日志以便后续优化

**安全视觉 prompt 写法指南**（2026-05-17+18 验证）：
当需要避免人物、儿童、硬币、货币、历史物品等被安全过滤的主题时，使用纯抽象物体+几何图案+数字界面元素替代：
```python
# ❌ 会被 blocking 的 prompt（含 "child"、"classroom"、"silver coins"、 "stock certificates"）
"16th century silver coin with King Henry VIII profile..."
# ✅ 安全 prompt（无人物、无货币、纯抽象几何）
"Abstract circular metallic forms in dark space, subtle geometric patterns suggesting ancient craftsmanship, floating rings with warm amber glow, no text, no people, no currency visible..."
```

**2026-05-18 已验证的安全写法**：Imagen 3 的 safety filter 对以下元素极为敏感—— 
- ❌ 任何形式的人物/人群/剪影/面部
- ❌ 货币/硬币/纸币/金库/金条
- ❌ 历史人物/国王/政治人物/标志性建筑
- ❌ 财务报表/股价图/证券文件/证书
- ❌ 战争/武器/军事装备
- ❌ 具体企业LOGO/品牌商标
- ✅ 抽象几何形状、漂浮物体、光影效果、自然景观、科技设备（无品牌）、建筑外观（非标志性）

核心策略：**用空场景+抽象几何+数字光效**替代所有具象/可能触发过滤的元素。
```python
# ❌ 会被 blocking 的 prompt（含 "child"、"classroom"、"student"）
"A child sitting inside a transparent glass cubicle surrounded by screens..."

# ✅ 安全 prompt（无人物，纯抽象物体）
"An empty transparent glass cube floating in dark space, surrounded by glowing progress bars and digital point counters, no people visible..."
```

方案：用"空场景 + 具象物体 + 数字界面元素"替代人物互动场景描述。建筑物、科技设备、自然景观、抽象几何图形通常不会被过滤。

## ⚠️ Imagen 3 图片亮度
- Imagen 3 默认生成赛博朋克暗调风格（70-80% 像素亮度 < 40/255）
- 必须用 Pillow 做后处理：brightness 1.8x + contrast 1.4x + color 1.3x
- 亮度增强后文字层需要重新叠加
- 见 references/image-qa-checklist.md 中的亮度检查标准

## ⚠️ 图片目录残留旧格式文件陷阱（2026-05-18 新增）

**现象**：渲染视频时 concat.txt 包含比实际 block 数更多的图片文件，导致视频画面切换错误（如 5 个 block 却有 11 张图）。

**根因**：`{slug}_images/` 目录中可能同时存在旧格式图片（`block_1.png`, `block_2.png`）和新格式图片（`block_01.png`, `block_02.png`）。render 脚本按字母排序时，`block_01.png` 和 `block_1.png` 都会被选中。

**处理方案**：
1. 生成新图片前**先清理旧图片**：
   ```python
   # 在 gen_images 脚本开头
   import glob, os
   img_dir = f'/tmp/{slug}_images'
   if os.path.exists(img_dir):
       for f in glob.glob(os.path.join(img_dir, 'block_*.png')):
           # 只保留双位数格式 block_01.png（新格式），删除 block_1.png（旧格式）
           if '_cover' in f or len(os.path.basename(f)) < 12:
               os.remove(f)
   ```
2. render 脚本应只匹配 `block_` 开头且长度 > 9 的文件（避免匹配旧格式）
3. 每次 gen_images 运行前，用 rm 清理所有旧格式文件

**陷阱**：某些旧格式生成的 cover.png 可能是 1080×1920（竖版/portrait）而非 1920×1080（横版/landscape）。这会导致视频渲染时 concat demuxer 输出格式异常或封面被压扁。

**生成后强制验证**：
```python
from PIL import Image
img = Image.open('/tmp/cover.png')
assert img.size == (1920, 1080), f"Cover must be 1920x1080, got {img.size}"
# 如果不是横版，用 Pillow 重新创建深色底图
if img.size != (1920, 1080):
    bg = Image.new('RGB', (1920, 1080), (10, 15, 30))
    img.thumbnail((1600, 900), Image.LANCZOS)
    x = (1920 - img.width) // 2
    y = (1080 - img.height) // 2
    bg.paste(img, (x, y))
    bg.save('/tmp/cover.png')
```

## ⚠️ ffmpeg concat demuxer 图片格式陷阱（2026-05-15踩坑）

**现象**：ffmpeg concat demuxer 输出 `Invalid PNG signature 0xFFD8FFE000104A46`（即 JPEG 文件被当成 PNG 解析）。

**根因**：concat.txt 中写了 `file 'cover.png'` 但实际文件是 JPEG 格式（Pillow 的 `save('cover.png')` 可能写入了 JPEG 编码的数据）。

**正确做法**：统一使用一种图片格式，不混用。concat.txt 中的 `file` 路径扩展名必须与实际文件格式匹配。

## ✅ Block JSON 生成：两种方案按场景选择（2026-05-17 更新）

2026-05-17 验证：**两种方案都可靠，按场景选择**。本session用 `delegate_task` 一次生成了 8 个文件的 blocks JSON（FA/WSJ/Econ/Science/New Scientist），全部一次通过验证，未出现字段名错误或时间格式问题。

### 方案 A：delegate_task 批量生成（多文件时推荐）

**适用场景**：有多个文件需要同时处理时。本session 8个blocks并行生成，总耗时约 8-14 分钟。

**prompt 关键约束**（必须包含，缺一不可）：
1. 明确要求 v5 格式的 7 个字段（`title`, `argument`, `start_time`, `end_time`, `summary`, `keywords`, `visual_prompt`）
2. 明确要求 `start_time`/`end_time` 为 `"HH:MM:SS"` 字符串格式（HH=分钟），**不是**整数秒
3. 明确要求 summary ≥200 字中文
4. 明确要求每个 visual_prompt 末尾追加 ARRI Alexa camera 后缀
5. 明确要求顶层 `core_topic` 字段
6. 明确要求 `json.dump(ensure_ascii=False, indent=2)` 写入
7. 提供音频时长（来自 ffprobe）作为时间基准

**验证步骤**（生成后必须执行）：
```python
python3 -c "
import json
with open('/tmp/file.json') as f:
    d = json.load(f)
# Handle list vs dict wrapper
blocks = d if isinstance(d, list) else d.get('blocks', [])
required = {'title','argument','start_time','end_time','summary','keywords','visual_prompt'}
ok = True
for i, b in enumerate(blocks):
    missing = required - set(b.keys())
    if missing: print(f'Block {i}: missing {missing}'); ok = False
    for key in ('start_time','end_time'):
        val = b[key]
        if isinstance(val, int) or ':' not in str(val):
            print(f'Block {i}: {key} format wrong: {repr(val)}'); ok = False
    if len(b.get('summary','')) < 150:
        print(f'Block {i}: summary short ({len(b[\"summary\"])}c)'); ok = False
    if len(b.get('keywords',[])) > 5 or len(b.get('keywords',[])) < 3:
        print(f'Block {i}: keywords {len(b[\"keywords\"])}'); ok = False
print('ALL OK' if ok else 'ISSUES FOUND')
"
```

**已知边缘情况**：
- delegate_task 可能输出裸列表 `[{},{}]` 而非 `{"blocks":[{},{}]}` — 用 `isinstance(d, list)` 检测并包装
- 子代理可能输出 `topic` 或 `block_id` 代替 `argument`/`title` — 在 prompt 中**强调不要用这些字段名**
- 时间格式有时输出整数秒 — prompt 中明确要求 `"HH:MM:SS"` 字符串，并用**示例**说明 `"00:03:00"` = 3分钟

### 方案 B：手动 Python 脚本（单文件时更可控）

**适用场景**：只有1-2个文件，或需要精确控制每个block的时间分配时。

```python
# gen_blocks_YYYYMMDD.py — 单一用途脚本
import json, subprocess

# 1. 获取音频时长
r = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','json', audio_path], ...)
duration = int(float(...))

# 2. 根据转录文本手动分块，估算时间比例
blocks = [
    {
        "title": "中文标题",
        "argument": "一句话核心观点",
        "start_time": "00:00:00",
        "end_time": "05:27:00",  # HH:MM:SS 格式，HH=分钟
        "summary": "≥200字，含故事+数据+视觉方向",
        "keywords": ["关键词1", "关键词2", "关键词3", "关键词4", "关键词5"],
        "visual_prompt": "英文prompt，含视觉隐喻"
    },
]
# 3. 验证总时间匹配
# 4. 用 json.dump(ensure_ascii=False) 写入
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump({"core_topic": "...", "blocks": blocks}, f, ensure_ascii=False, indent=2)
```

**优势**：
- 精确控制每个 block 的时间分配
- 可版本控制每个文件的 gen_blocks 脚本
- 无 delegate_task 开销

### 时间估算方法（两种方案通用）
1. 读取转录文本完整内容
2. 按话题切换点手动划出 block 边界
3. 根据**内容占比**估算每个 block 的时间（不是按字符数均分！）
4. 最后一秒的 end_time 必须等于 ffprobe 音频时长（取整）
5. 验证：`sum(block_durations) == audio_duration`

### 示例
- **Economist 2025-12-13**（901秒/15min）：7 block，手动分配 130-130-130-120-130-130-131 秒
- **Economist 2025-12-20**（1308秒/21min48s）：6 block，手动分配 327-229-209-183-162-198 秒
- **Foreign Affairs 2025-05-01**（1189s/19m49s，delegate_task生成）：7 block，topic: 大国勾兑→GDP幻觉→200倍差距→无菌玻璃房→最后的晚餐→冰工厂→时代错位

## ⚠️ Block JSON生成 — delegate_task中断时的fallback策略（2026-05-17 新增）

当用 `delegate_task` 生成 Block JSON 被中断（interrupted/超时）时，不要重新delegate。用以下方法**手动生成**：

1. 读取转录文本，按内容话题手动划分block边界
2. 用ffprobe获取音频总时长（秒数）
3. 根据字符位置比例估算每个block的时间分配
4. 用 Python script 直接写 JSON（用json.dump, ensure_ascii=False）
5. 避免 f-string 转义陷阱 — 把带引号的复杂表达式提取为变量

手动生成示例脚本框架（可复用）：
```python
import json, subprocess
r = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','json', audio_path], capture_output=True,text=True,timeout=10)
duration = int(float(json.loads(r.stdout)['format']['duration']))
# 按内容手动分块
blocks = [{"title": "...", "argument": "...", "start_time": "00:00:00", "end_time": "03:30:00", ...}]
# 验证最后一帧时间
last_sec = duration
blocks[-1]['end_time'] = f'{last_sec//60:02d}:{last_sec%60:02d}:00'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump({"core_topic": "...", "blocks": blocks}, f, ensure_ascii=False, indent=2)
```

**f-string转义陷阱（已踩坑）**：在写Python脚本时，f-string中的嵌套引号要避免使用反斜杠`\"`，改用变量引用或format()。
```python
# ❌ 错误 — f-string + 反斜杠引号
print(f'Block {b[\"title\"]}')  # SyntaxError
# ✅ 正确 — 提取变量
t = b['title']; print(f'Block {t}')
```

delegate_task 生成 v5 Block JSON 时有时直接输出 **裸列表**（`[{...},{...}]`）而不是 `{"blocks":[...]}` 的 dict 格式。触发 `TypeError: list indices must be integers or slices, not str`。

**验证方法：**
```python
with open('file.json') as f:
    d = json.load(f)
if isinstance(d, list):
    d = {"core_topic": "economy_domino", "blocks": d}
```

## ⚠️ upload_video.py 今日上传计数偶发不准确（2026-05-15）

偶尔错误报告 `今日已上传 0 个`（即使已上传多个）。因 API 缓存延迟。不影响上传，`剩余配额充足` 时即可继续。

## ⚠️ upload_video.py --check 模式 bug（2026-05-17 发现）

`--check` 模式本身有 bug：argparse 将 `video` 参数设为 required 且 `--title` 也设为 required，
导致 `python3 ~/hermesagent/Youtube video/magazine/upload_video.py --check` 直接报错退出，无法独立作为配额检查工具。

**解决方案**：直接用 python 脚本手动检查配额（2026-05-17 验证可用）：
```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

creds = Credentials(...)
youtube = build('youtube', 'v3', credentials=creds, cache_discovery=False)

ch = youtube.channels().list(part='contentDetails', mine=True).execute()
uploads_id = ch['items'][0]['contentDetails']['relatedPlaylists']['uploads']

today = '2026-05-17'
items = youtube.playlistItems().list(part='snippet', playlistId=uploads_id, maxResults=50).execute()
count = sum(1 for i in items['items'] if i['snippet']['publishedAt'][:10] == today)
print(f'Today uploads: {count}, remaining: {50-count}')
```

## ⚠️ Hermes 重启/中断恢复协议（2026-05-17 多次踩坑后确立）

当 Hermes 或系统重启后，后台进程全部丢失。恢复流程：

1. **检查 processed.txt** — 看哪些文件已标记完成（YouTube URL存在）
2. **检查 /tmp 目录** — 看哪些阶段已完成：
   - 有 `.mp3` 但无 `_transcript.txt` → 需要重新下载+转录
   - 有 `_transcript.txt` 但无 `_blocks.json` → 需要生成 blocks
   - 有 `_blocks.json` 但无视频文件 → 检查图片目录 `econ_images_{MMDD}/`
   - 部分图片存在 → 只用补缺失的block图，然后PDF叠加+渲染+上传
3. **写独立的resume脚本** — 只做未完成的步骤，不重复已完成的

**⚠️ Whisper 转录超时处理（2026-05-17 验证）：CPU 转录耗时约 5-10 分钟/文件**
Whisper small model 跑 30-45MB MP3 文件（20-25min 音频）在 CPU 上需要约 5-10 分钟。terminal(timeout=600) 可能还是不够。

**已验证的可靠方法**：用 `terminal(background=true, notify_on_complete=true)` + 轮询文件系统检查输出文件。不要依赖 stdout 输出（后台进程 output buffering 问题详见上节）。

```python
# 启动
terminal(background=true, notify_on_complete=true, command=f"python3 -u -c 'import whisper; m=whisper.load_model(\"small\"); r=m.transcribe(\"/tmp/audio.mp3\", language=\"zh\"); open(\"/tmp/audio_transcript.txt\",\"w\").write(r[\"text\"])'")

# 后面轮询检查：
python3 -c "import os; print('OK' if os.path.exists('/tmp/audio_transcript.txt') and os.path.getsize(p)>1000 else 'WAITING')"
```

如果前台 timeout 但实际已完成（文件已写入），不用重新运行。验证方式是检查 `/tmp/` 中对应 `_transcript.txt` 文件是否存在且 >1000 字符。

**检测并发 Whisper 进程的方法**：
```bash
ps aux | grep whisper | grep -v grep
ps -p <PID> -o pid,etime,%cpu -p <PID>  # 检查运行时间和CPU使用率
```

**三步并行转录策略**（2026-05-17 验证可将 7 个文件的转录时间从 70min 减到 10min）：
不要逐个转录文件。同时启动 3 个 Whisper 后台进程，每个处理 2-3 个文件：
```python
# 批次1: barrons_20260406 + natgeotraveller (2 files)
# 批次2: newscientist_20260207 + newscientist_20260214 (2 files)
# 批次3: science_20260326 + WSJ_20260304 + WSJ_20260331 (3 files)
```
注意：每个进程独立加载模型到内存（~2-3GB RAM 各），确保系统内存充足。

### ⚠️ Hermes 重启/中断恢复加速技巧（2026-05-17 验证）

**快速上传优先策略**：每次 cron 启动时，先扫描 `/tmp/` 中所有带 `_final.mp4` 的文件 → 立即上传（这些已经渲染完成，最快）。在等待上传的间隙同时扫描 blocks/transcript/images 状态并启动后台处理。

**扫描清单**：
- 有 `_final.mp4` → 立即上传（跳过渲染）
- 有 `_blocks.json` 但无 `_final.mp4` → 检查图片目录是否存在
  - 图片齐全 → 渲染视频
  - 图片不全 → 生成缺失的图片（用 gen_images.py 逐个补）
- 有 `_transcript.txt` 但无 `_blocks.json` → 需要生成 blocks
- 只有 `.mp3` → 需要完整流水线

**2026-05-17 验证**：此策略让 6 个文件在 15 分钟内完成上传（已有 _final.mp4），同时在后台并行启动 3 个 Imagen 图片生成进程。统计 `/tmp/` 中的文件比重新扫描 Drive 更快。
- 扫描 `/tmp/` 中所有带 `_final.mp4` 的文件 → 跳过渲染，直接上传
- 扫描所有带 `_blocks.json` 的文件 → 跳过转录+分块，直接进入图片生成
- 扫描所有带图片目录的 → 跳过图片生成，进入 PDF 叠加+渲染
- 注意 `_blocks.json` 可能使用旧格式（v1-v4，含 `id`/`duration_sec` 字段而非 v5）。旧格式视频已渲染完成时可以上传，无需重新生成 blocks。
- **先上传最快的文件**（已有 `_final.mp4` 的），在等待上传时启动后台转录

**Pillow链式调用陷阱**（2026-05-17 踩坑）：`Image.new("RGB",(W,H),(0,0,0)).paste(img_rgba,(0,0),img_rgba).save(path)` 中的 `.paste()` 返回 `None`，不是修改后的图像对象。**必须分步写**：
```python
# ❌ 错误 — paste返回None，.save()报AttributeError
Image.new("RGB",(W,H),(0,0,0)).paste(img_rgba,(0,0),img_rgba).save(path)
# ✅ 正确 — 分步
final = Image.new("RGB", (W,H), (0,0,0))
final.paste(img_rgba, (0,0), img_rgba)
final.save(path)
```

**f-string 转义陷阱**（2026-05-17 踩坑）：Python 3.12+ 的 f-string 中不允使用 `\\"` 转义引号。应该提取变量：
```python
# ❌ 错误 — SyntaxError
print(f'Block {i}: summary={len(b["summary"])}c')
# ✅ 正确
s = b['summary']
print(f'Block {i}: summary={len(s)}c')
```

## ⚠️ Hermes 后台终端限制（2026-05-12 更新）
- `run_local_server()` 在 Hermes TUI 后台终端中无法弹出浏览器
- `input()` 在后台进程中也无法交互（stderr 无 tty）
- 解决方案：要么用 pty 模式运行（仍不可靠），要么用 youtube-studio-mcp 的独立 OAuth 流程
- 如果必须用 OAuth API 方式，需要用户自己在本地终端跑上传脚本

## ⚠️ 后台进程 output buffering（2026-05-17 新增 — Imagen 3 图片生成）

**现象**：使用 `background=true` + `notify_on_complete=true` 启动图片生成脚本时，`process(action='log')` 返回空输出长达 5+ 分钟，即使进程实际上正在运行并生成图片。

**根因**：
1. Hermes 后台终端默认使用 `bash -lic` 包装命令，启用行缓冲而非无缓冲模式
2. Python 的 stdout 在有 pipe 时默认使用块缓冲（block buffering，4KB~8KB block）
3. Imagen 3 API 调用间隔较长，每张图的输出可能在几十秒内不足一个 buffer block
4. 输出被缓冲直到进程结束或 buffer 满了才可见

**解决方案**：
1. **不要依赖后台进程 (`background=true`) 做 Imagen 3 图片生成**。它需要实时输出查看进度。
2. 改为前台（foreground）模式运行，设置 `timeout=600` — 前台命令在完成后立刻返回
3. 如果需要后台运行，在 Python 中强制无缓冲输出：
   ```python
   # 在脚本开头添加
   import sys
   sys.stdout.reconfigure(line_buffering=True)  # Python 3.7+
   # 或直接用 print(..., flush=True)
   ```
4. 或通过环境变量 `PYTHONUNBUFFERED=1` 启动：
   ```python
   os.environ['PYTHONUNBUFFERED'] = '1'
   ```
5. 替代方案：后台进程不依赖 stdout，而是通过写入文件系统报告进度
   ```python
   # writer.py
   with open('/tmp/progress.txt', 'a') as f:
       f.write(f'{time.time()}: {label} done\n')
   ```
   主进程轮询文件变化

**推荐做法**：Imagen 3 图片生成（8-10张图，约5-10分钟）用前台模式执行，timeout=600。输出实时可见。视频渲染（2-3分钟）同样用前台。

## ⚠️ Drive API 分页查询陷阱（2026-05-17 发现）

**现象**：Service Account 的 `files().list()` 查询有时返回 0 个文件，但实际有 16+ 个文件夹。

**根因**：当同时设置 `pageSize=100` 或 `pageSize=200` 时，某些情况下 Google Drive API 返回空结果。去掉 `pageSize` 参数（使用默认值）后恢复正常。

**正确的扫描模式**：
```python
# ❌ 有时返回 0 文件
r = service.files().list(q=q, fields='files(id,name)', pageSize=100).execute()

# ✅ 始终工作（使用默认 pageSize）
r = service.files().list(q=q, fields='files(id,name)').execute()
```

**推荐的安全分页模式**（已验证）：
```python
def list_all(svc, q):
    files = []
    pt = None
    while True:
        params = {'q': q, 'fields': 'files(id,name,mimeType,size),nextPageToken'}
        if pt: params['pageToken'] = pt
        r = svc.files().list(**params).execute()  # 不给 pageSize！
        files.extend(r.get('files', []))
        pt = r.get('nextPageToken')
        if not pt: break
    return files
```

**调试技巧**：如果查询返回 0 文件但确定有内容，先执行最简化查询（无 pageSize、无 mimeType 过滤），确认 SA 能访问数据后再逐步加条件。

## ⚠️ Drive 根文件夹 ID 可能变化（2026-05-18 新增）

**现象**：`Globalmagzineyoutube` 文件夹的 ID 从 `1R-cmHrvqjYYbGFx8PCxQayZ8cpnn2c-F` 变为 `1tOVhkClasjoGUxtKIzyskFoGi3Zs1zy4`。

**根因**不明（可能是 Google Drive 同步或重建导致的 ID 变更）。这会导致硬编码根 ID 的扫描脚本返回 404。

**教训**：**每次 cron 运行时不要硬编码根文件夹 ID。** 启动时先通过文件夹名查询找到正确的 ID：

```python
# 不要硬编码：
# ROOT_ID = '1R-cmHrvqjYYbGFx8PCxQayZ8cpnn2c-F'  # ❌ 可能过时

# 应走名称查询：
root = svc.files().list(q="name='Globalmagzineyoutube'", fields='files(id)').execute()
if not root.get('files'): raise Exception('Globalmagzineyoutube folder not found!')
ROOT_ID = root['files'][0]['id']
```

这应作为每次扫描的第一步进行验证。硬编码 ID 的风险是会无声地返回 404，从而误判"没有杂志文件夹 = 没有新文件"。
每次开始处理新文件前，先读取 `~/hermesagent/Youtube video/magazine/processed.txt` 避免重复处理。
上传成功后立即追加记录（两种格式均可，保持统一即可）：
```bash
# 格式1（有DriveFileID）：
echo "DriveFileID,Economist_YYYYMMDD.mp3,$(date +%Y-%m-%d),https://www.youtube.com/watch?v=VIDEO_ID" >> ~/hermesagent/Youtube video/magazine/processed.txt

# 格式2（无DriveFileID，当从/tmp本地音频处理时）：
echo ",economist_YYYYMMDD.mp3,2026-05-15,https://www.youtube.com/watch?v=VIDEO_ID" >> ~/hermesagent/Youtube video/magazine/processed.txt
```

## ⚠️ Block JSON delegate_task 可能输出列表而非 dict（2026-05-15新增）

delegate_task 生成 v5 Block JSON 时有时直接输出 **裸列表**（`[{...},{...}]`）而不是 `{"core_topic":"...","blocks":[{...}]}` 的 dict 格式。

这会导致 gen 脚本中 `data["blocks"]` 抛出 `TypeError: list indices must be integers or slices, not str`。

**验证方法：**
```python
with open('file.json') as f:
    d = json.load(f)
if isinstance(d, list):
    # ❌ 裸列表，需要包装
    d = {"core_topic": "economy_domino", "blocks": d}
    with open('file.json', 'w') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
elif isinstance(d, dict) and "blocks" not in d:
    print("❌ Missing 'blocks' key")
```

**预防：** delegate_task prompt 中明确要求输出 dict 格式，并在验证步骤检查是否为 dict。

## ⚠️ ffmpeg concat demuxer 图片格式陷阱（2026-05-15踩坑）

**现象**：ffmpeg concat demuxer 输出 `Invalid PNG signature 0xFFD8FFE000104A46`（即 JPEG 文件被当成 PNG 解析）。

**根因**：concat.txt 中写了 `file 'cover.png'` 但实际文件是 JPEG 格式（Pillow 的 `save('cover.png')` 可能写入了 JPEG 编码的数据）。

**正确做法**：要么用 `file` 命令验证实际格式后写对扩展名，要么统一用 JPEG（`.jpg`）并保持 concat.txt 一致。

**推荐**：所有图片统一用 JPEG（`-f image2` 格式兼容性好）：
```python
# 保存为 JPEG
img.save(path, "JPEG", quality=92)
# concat.txt 中写 file '...jpg'
```

## ⚠️ upload_video.py 缩略图 RGBA 模式问题（2026-05-17 发现）

**现象**：`upload_video.py` 的 `--cover` 参数接受 PNG，但上传缩略图时报告 `cannot write mode RGBA as JPEG`。

**根因**：cover.png 以 RGBA 模式保存（含透明通道），但 YouTube thumbnail 需要 JPEG（不含 alpha）。`upload_video.py` 内部压缩代码未做 RGBA→RGB 转换。

**临时修复**（每次上传后单独上传缩略图）：
```python
from PIL import Image
import io, requests

cover = Image.open('/tmp/cover.png').convert('RGB')  # ← 关键：convert to RGB
cover_resized = cover.resize((1280, 720), Image.LANCZOS)
buf = io.BytesIO()
for q in range(92, 10, -5):
    buf.seek(0); buf.truncate()
    cover_resized.save(buf, 'JPEG', quality=q, optimize=True)
    if buf.tell() < 1900 * 1024: break

r = requests.post(
    f'https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={video_id}',
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'image/jpeg'},
    data=buf.getvalue(), timeout=30
)
```

**永久修复**（改进 upload_video.py）：在缩略图压缩函数入口处加 `.convert('RGB')`。当前 `~/hermesagent/Youtube video/magazine/upload_video.py` 尚未修复。

## ⚠️ processed.txt 记录可能不完整（2026-05-16 发现）

**现象**：channel 上有 32 个视频，但 processed.txt 仅记录了 20+ 条。NY 0302、0309、0323、0420 在 YouTube 上但 processed.txt 缺失记录。

**建议**：pipeline 启动前同时：
1. 读取 processed.txt
2. 从 YouTube 拉取 playlistItems
3. 取并集作为已处理基线
**不影响上传**——只要 `剩余配额充足` 就可以继续上传。

## ⚠️ upload_video.py 参数注意（2026-05-15）
`upload_video.py` **没有 `--privacy` 参数**，默认 public。不要传 `--privacy`。
完整命令：
```bash
cd ~/magazine && python3 upload_video.py /tmp/video.mp4 \\
  --title "《杂志》..." \\
  --description "..." \\
  --tags "..." \\
  --category 25 \\
  --cover /tmp/cover.png
```

## ⚠️ Google Drive 下载认证（2026-05-15 更新：用服务账号代替 ADC）

### 环境
Drive ADC（Application Default Credentials）的 scope 可能过期或被限制，`drive_token.pickle` 也可能失效。

### 可靠方案：用服务账号 JSON 直接下载

Imagen 3 使用的服务账号（`hermes-infra-prod-9c5abf6aefe8.json`）也能访问 Drive：

```python
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SA_PATH = "/Users/chaojin/hermesagent/Youtube video/hermes-infra-prod-9c5abf6aefe8.json"
creds = service_account.Credentials.from_service_account_file(
    SA_PATH, scopes=['https://www.googleapis.com/auth/drive']
)
service = build('drive', 'v3', credentials=creds, cache_discovery=False)

request = service.files().get_media(fileId=FILE_ID)
fh = io.BytesIO()
downloader = MediaIoBaseDownload(fh, request)
done = False
while not done:
    status, done = downloader.next_chunk()

with open('/tmp/output.mp3', 'wb') as f:
    f.write(fh.getvalue())
```

### 旧方案（不推荐）
- `~/Claudcode/magazine-podcast/drive_token.pickle` — 可能过期
- `~/Claudcode/magazine-podcast/drive.py` 使用 ADC — scope 可能不够
- Swift NSFileCoordinator — 仅限 macOS 且需要本地 CloudStorage 同步

## 🎨 风格选择：按杂志切换（2026-05-14 更新）
## 🎨 风格选择：深色科技感 — 电影极简版（2026-05-14 更新）

2026-05-14 用户从 NotebookLM 暖白风格先后改为深色科技感，然后进一步要求**更简洁的封面 + 更具电影冲击力的图片**。

**当前默认风格（电影极简版）**：
- 深蓝/黑背景为主，橙色/黄色突出主题
- ARRI Alexa cinema camera 电影质感，16:9 1920×1080
- **封面只放杂志名称 + 日期，不放 block 标题列表**
- 内容图：有视觉冲击力，信息图风格带数据视觉化
- Shot on ARRI Alexa cinema camera, anamorphic lens bokeh, shallow depth of field
- 见 references/dark-tech-image-style.md

**旧风格**（不再使用）：
- ~~NotebookLM 暖白编辑信息图风格~~
- ~~深色科技感带cyan青色发光和block标题列表~~
- ~~赛博朋克暗调风格~~

### 封面设计原则（2026-05-15 更新 — 深色主视觉+核心Summary版）

#### 三要素
1. **深色主视觉元素**（浅色高光，紧扣核心故事的视觉隐喻，占画面主体）
2. **核心故事Summary**（1-2句，简短有力，位于封面中下方，半透明底条）
3. **杂志名 + 日期**（左上角大号，橙色 #FFC832 / 黄色）

#### 布局规范（1920×1080）
```
┌──────────────────────┬──────────┐
│ 经济学人              │  📔      │  ← 左上角杂志名，橙色#FFC832，96px，黑色描边
│ 2026年4月4日          │  杂志    │  ← 右上角叠放原始杂志封面图
│                      │  封面    │    约占全图20%，带白色细边框
│                      │  (20%)   │
│                      │          │
│   ┌──── 深色主视觉 ──┘          │  ← Imagen生成的紧扣核心故事的视觉隐喻图
│   │ （流沙+导弹+人脑芯片）        │    浅色高光，暗蓝/黑基调
│   └─────────────────────────────┘
│                                  │
│ ┌────────────────────────────┐   │
│ │ 从850枚战斧到砸碎下颌骨：   │   │  ← 核心故事Summary，1-2句
│ │ 三个平行宇宙共通的流沙困境   │   │    白色文字，48-56px
│ └────────────────────────────┘   │  ← 半透明黑底条 rgba(0,0,0,0.65)
└──────────────────────────────────┘
```

#### 具体规则
- **封面必须包含核心故事Summary**（1-2句，从 blocks JSON 的 core_topic 或 Block 1 的 summary 中提炼）
- Summary 文字位于画面中下方（约 y=800-900），半透明黑底条上，白色文字
- 字数：20-40字，高度概括本期核心论点
- **背景图**（Imagen 生成）：深色主调（暗蓝/黑）+ 浅色高光视觉元素，紧扣核心故事视觉隐喻
- **杂志名**：左上角大号橙色 #FFC832 / 黄色，带黑色描边（dx,dy循环），STHeiti Medium 96px
- **日期**：杂志名下方，白色/柔和灰色，STHeiti Medium 48px
- **所有文字（杂志名、日期、Summary）都在 Pillow 阶段叠加，不要求 Imagen 渲染文字**

## ⚠️ 封面PDF叠加验证（2026-05-17 强制 — 必须执行，不可遗漏）

**封面生成流程的最后一个步骤必须是PDF封面叠加。** 2026-05-17 用户报告5个文件（Econ 2025-09-27、Econ 2026-04-18、Econ 2026-05-02、Econ 2026-05-09、Econ 2026-05-16）缺少PDF封面在右上角，流水线生成了cover.png但遗漏了最后的叠加步骤。

⚠️ **这条规则曾经连续被违反多次，用户已明确要求吸取教训。** 所有后续处理中，PDF封面叠加是封面生成的**必需步骤**，不是可选。

### 流水线中强制执行
「图片生成」阶段的**最后一步**必须是PDF封面叠加。渲染视频前必须完成。不可跳过：

1. **查找对应PDF**：在 Drive 的 `Globalmagzineyoutube/{杂志}/{年份}/` 下搜索日期匹配的PDF
2. **下载并提取封面**：用 Drive API 下载 → `qlmanage -t -s 1920 -o /tmp {pdf_path}` 提取第一页
3. **叠加到右上角**：高度=封面的50%（~540px），宽度等比（不超过55%宽度），检测已有杂志元素先擦除（variance > 500）
4. **保存覆盖原始cover.png**：直接覆盖原来的 cover.png 文件（不要在文件名加后缀）
5. **生成缩略图**：1280×720 JPEG < 1.9MB
6. **记录使用了哪个PDF**：在 processed.txt 备注中注明 (PDF: {filename})

### 验证方法（上传后检查）
每个视频上传至 YouTube 后，检查缩略图右上角是否有PDF封面叠加。
如果上传后发现缺少，用 retroactive-cover-fix.md 的工作流立即修复。

### 常见PDF查找匹配规则
| 音频日期 | 可能的PDF文件名格式 | 示例 |
|---------|-------------------|------|
| 2026-04-18 | `...1804...` / `...0418...` / `...04-18...` | `The Economist UK_1804.pdf` |
| 2026-05-02 | `...2504...` / `...0502...` / `...05-02...` | `The Economist (Web Edition)_2504.pdf` |
| 2026-05-09 | `...0509...` / `...05-09...` | `Economist-2026-05-09-PDF WEB.pdf` |
| 2026-05-16 | `...0516...` / `...05-16...` | `Economist 20260516.pdf` |
| 2026-03-01 | `National Geographic_2026MM.pdf` | `National Geographic_202603.pdf` |
| 2026-03-05 | `Science_2026MM.pdf` | `Science_202603.pdf` |
| 2026-03-12 | `Science_2026MM.pdf` | `Science_202603.pdf` |
| 2026-meta | 国家地理 PDF | `National Geographic_2026{MM}.pdf`（按月而非按日） |
| 2026-meta | 科学 PDF | `Science_2026{MM}.pdf`（同样按月命名） |
| 2026-02-01 | Bloomberg PDF | `Bloomberg Businessweek_202602.pdf`（按月命名 `Bloomberg Businessweek_2026{MM}.pdf`） |

**注意**：国家地理和科学的 PDF 是按**月**命名的（`National Geographic_202603.pdf`、`Science_202603.pdf`），而音频是按日命名的（`National Geographic_20260301.mp3`、`Science_20260305.mp3`）。查找 PDF 时，从音频日期中提取年月部分匹配即可。

PDF可能不在根目录，而在 `{杂志}/{年份}/` 子文件夹中。

**封面上的所有文字必须使用全中文，禁止中英混用。** 此规则适用于封面图上的文案，不影响 YouTube 标题、描述和标签。

- **杂志名必须用中文全称：** `纽约客`（不是 `NewYorker` / `New Yorker`）、`经济学人`（不是 `The Economist` / `Economist`）、`华尔街日报`（不是 `Wallstreet Journal`）、`科学`（不是 `Science`）、`彭博商业周刊`（不是 `Bloomberg`）、`巴伦周刊`（不是 `Barron's` / `Barron`）
- **日期格式：** `YYYY年M月D日`（如 `2026年3月16日`），不用 `YYYY-MM-DD`、`2026.02.02` 或中英混合格式
- **底部 Summary：** 全中文，1-2句，20-40字

**Imagen 生成背景图时必须严格禁止任何文字：**

Imagen 经常在背景图中生成英文字母或杂志封面缩略图元素，必须用最严格的 NO TEXT prompt 阻止：
```
NO TEXT, NO LETTERS, NO NUMBERS, NO WORDS, NO CAPTIONS, NO LABELS, 
NO magazine covers, NO newspaper, NO documents, NO screens, 
NO English text, NO Chinese text, NO any text anywhere in the image. 
Pure visual background only. Completely empty of any text or letters.
```

**所有文字（杂志名、日期、Summary）100% 在 Pillow 阶段叠加，Imagen 只生成纯背景。**

**已有视频封面修复流程**（2026-05-16 新增）：
当发现历史视频封面有英文文字时：
1. 用 Imagen 重新生成纯背景图（严格 NO TEXT + NO magazine elements）
2. 通过 Pillow 叠加全中文文字（杂志名、日期、底部Summary）
3. 叠加 PDF 封面到右上角（540px 高，等比缩放，检测已有内容并擦除）
4. 上传新缩略图到 YouTube（1280×720 JPEG < 1.9MB）
5. 如有重复视频，删除旧版本


#### 右上角叠加原始杂志封面图（2026-05-15 用户要求）



```python
from PIL import Image

def add_magazine_overlay(cover_path, mag_png_path):
    """Add magazine cover to top-right corner of YouTube cover"""
    cover = Image.open(cover_path).convert('RGBA')
    mag = Image.open(mag_png_path).convert('RGBA')
    
    # ⚠️ CRITICAL: Keep original aspect ratio! DO NOT squish to fixed dimensions.
    # Magazine height = 50% of cover height (~540px for 1080p) — user specified "放大一倍" from old 25%
    target_h = int(cover.height * 0.50)  # ~540px
    target_w = int(target_h * mag.width / mag.height)  # Auto-calculate width to preserve ratio!
    
    # Cap width at 55% of cover to avoid covering too much of the main visual
    max_w = int(cover.width * 0.55)
    if target_w > max_w:
        target_w = max_w
        target_h = int(target_w * mag.height / mag.width)
    
    mag_resized = mag.resize((target_w, target_h), Image.LANCZOS)
    
    # 右上角位置，20px边距
    x = cover.width - target_w - 20
    y = 20
    
    # 白色细边框 (2px)
    border_img = Image.new('RGBA', (target_w + 4, target_h + 4), (255, 255, 255, 200))
    cover.paste(border_img, (x - 2, y - 2), border_img)
    
    # 粘贴杂志封面
    cover.paste(mag_resized, (x, y), mag_resized)
    
    # 转回 RGB 保存
    rgb = Image.new('RGB', (1920, 1080), (0,0,0))
    rgb.paste(cover, (0,0), cover)
    rgb.save(cover_path)
```

PDF封面提取方法（macOS）：
```python
import subprocess
# 1. 从 Drive 下载 PDF
# 2. 用 qlmanage 提取第一页为 PNG
subprocess.run(['qlmanage', '-t', '-s', '1920', '-o', '/tmp', pdf_path])
# ⚠️ macOS 15: qlmanage 输出为 /tmp/{basename}.pdf.png，不是 {pdf_path}.png
# 例如 pdf_path='/tmp/econ/econ_2026-04-18.pdf' 时输出为 /tmp/econ_2026-04-18.pdf.png
basename = os.path.basename(pdf_path)
generated = os.path.join("/tmp", basename + ".png")
```

PDF 文件在 Drive 中的位置：`Globalmagzineyoutube/{杂志}/{年份}/` 下，文件名包含日期。
靠模糊匹配找到对应期刊的 PDF（日期格式多种：`2025.02.22`, `TE-2025-05-10`, `The Economist_20260404` 等）。

**⚠️ 注意事项：**
- PDF 封面覆盖在 Imagen 生成的封面背景之上，所有文字（杂志名、日期、Summary）在封面叠加**之后**再加
- 封面图会被缩小，所以原始 PDF 分辨率越高越好
- 封面覆盖仅应用于**封面图**，content blocks 不变
- 整体：高端 YouTube 封面感，有呼吸感/留白，不杂乱
- ❌ 不要放所有 block 的标题列表（会遮住画面）
- ❌ 不要放页码/进度条
- ❌ 不要二次叠加（Imagen 杂志 + PDF 封面）
- ❌ 不要压扁竖版封面

**💥 2026-05-15 踩坑：封面双重叠加**

**现象**：14个封面中6个出现了**两次杂志封面叠在一起**（Imagen生成的视觉元素中的杂志 + 后来加的PDF封面）。

**根因**：之前的 gen 脚本在 Imagen 生成的封面图中**本身已经包含了一个杂志封面缩略图**(作为视觉隐喻元素的一部分)。后续代码又在同一位置叠加了 PDF 封面，造成双重叠加。

**修复方案**（2026-05-15 已验证 6/6 成功）：
```
1. 检查原始封面右上角(1516,20 起 384×216 区域)是否有杂志封面元素
   → 采样像素方差检测法：variance > 500 说明有内容
2. 如果有 → 用周围背景色填充该区域，再叠 PDF 封面
3. 如果没有 → 直接叠 PDF 封面
4. 缩略图 1280x720 JPEG quality 90 → YouTube API thumbnail.set()
```

**正确流程：**
```python
def fix_and_overlay(cover_path, pdf_cover_path, output_path):
    img = Image.open(cover_path).convert("RGB")
    # 1. 检测右上角是否有杂志封面元素
    bg_samples = [img.getpixel((x, y)) for x,y in samples]
    variance = sum((p[0]-avg_r)**2 + ...)/len(pixels)  # >500 = HAS_MAG
    # 2. 如果有，用背景色填充
    if has_magazine:
        for y in range(y_s, min(y_s+216, H)):
            for x in range(x_s, min(x_s+384, W)):
                img.putpixel((x, y), bg_color)
    # 3. 叠 PDF 封面到同一个位置
    mag_resized = Image.open(pdf_cover_path).resize((384, 216), LANCZOS)
    img.paste(mag_resized, (1516, 20))
    # 4. 保存上传
    thumb = img.resize((1280, 720)).save(output, "JPEG", quality=90)
```

**通用规则（永久有效）：**
- 每次只叠**一次**竖版 PDF 封面到右上角
- 如果原始封面是 Imagen 生成的 → **检查后再叠**
- 如果是纯 Pillow 封面（WSJ/New Yorker 等）→ 直接叠，无需检测

#### 封面 Summary Pillow 叠加代码模板

在现有 Imagen 背景图上叠加核心故事 Summary：

```python
from PIL import Image, ImageDraw, ImageFont

cover = Image.open('/tmp/econ_20260404_cover.png')
draw = ImageDraw.Draw(cover)
W, H = 1920, 1080

font_summary = ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc', 56)

# 从 blocks JSON 的 core_topic 提炼
summary_lines = [
    '从850枚战斧到砸碎下颌骨：',
    '三个平行宇宙共通的流沙困境',
]

# 半透明底条（中下方位置）
overlay = Image.new('RGBA', (W, 140), (0, 0, 0, 180))
cover.paste(overlay, (0, H-220), overlay)

# Summary 白色文字，带黑色描边
y = H - 200
for line in summary_lines:
    for dx, dy in [(-1,-1),(1,-1),(-1,1),(1,1)]:
        draw.text((80+dx, y+dy), line, font=font_summary, fill=(0,0,0))
    draw.text((80, y), line, font=font_summary, fill=(255, 255, 255))
    y += 68

cover.save('/tmp/econ_20260404_cover.png')
```

注意：Summary 文字在 Imagen 背景图生成后叠加，不要在 Imagen prompt 中要求渲染文字。
```python
cover_prompt = f""""{视觉隐喻描述（从blocks JSON的core_topic和Block1的visual_prompt提炼）},
dark cinematic background, deep rich blacks and amber/gold highlights,
dramatic volumetric lighting, shallow depth of field,
NO TEXT, NO LETTERS, NO NUMBERS, NO WORDS, NO CAPTIONS, NO LABELS anywhere in the image.
Pure visual background only."""
```

#### 核心话题→视觉隐喻映射表

`core_topic` 字段使用**中文描述**（从 blocks 内容提炼的一句话），不使用抽象 key。以下按话题类型提供视觉隐喻方向：

| 话题类型 | 视觉隐喻 | 示例中文 core_topic |
|---------|---------|-------------------|
| AI / 科技垄断 | 玻璃房/数字保险箱 + 芯片/数据流 + 少数人围坐 | 数字玻璃房：AI巨头的VIP俱乐部 |
| 经济连锁反应/贸易战 | 骨牌被推倒 + 关税高墙 + 全球供应链 | 常识失灵时代：从稀土战争到雨林悖论 |
| 能源/地缘政治 | 霍尔木兹海峡 + 油轮/化肥船+ 封锁链 | 控制权幻觉：从代码到粮食 |
| 政治/权力 | 权杖/天平 + 暗影/剪影 + 军事直升机 | 马杜罗被抓：权力幻觉的崩塌 |
| 社会/民生/关系 | 人群/城市剪影 + 光纤网络 + 孤立个体 | 关系大衰退：一亿单身 |
| 金融/市场 | K线图/数字瀑布 + 光柱 + 破碎的眼镜 | 繁荣幻觉：无衰退病 |
| 环境/气候 | 冰川融化/火焰 + 数据可视化 + 雨林 | 雨林悖论：3万亿生态资产 |
| 医疗/健康 | DNA双螺旋 + 显微镜光晕 | — |
| 历史/文化 | 古老物件 + 现代碎片对照 | 错位时代：用旧地图找新大陆 |

**规则：** core_topic = 封面底部 Summary 的源素材，应是一句 20-40 字中文描述，作为封面中下方半透明底条上的文字。

### 内容图风格要求（电影极简版）

**⚠️ 用户明确要求：visual_prompt 必须生成更多元的深度画面（2026-05-16）**
每个 block 的 visual_prompt 应使用不同的构图和色调，详见 `references/visual-prompt-diversity.md`。
禁止在连续 block 中使用相同角度或色系的 prompt。

所有内容图的 **visual_prompt** 末尾必须追加：
```
Shot on ARRI Alexa cinema camera, anamorphic lens bokeh, 
shallow depth of field, foreground elements slightly out of focus,
dramatic volumetric lighting with visible light rays,
cinematic color grading, deep shadows with rich blacks,
film grain texture, ultra-realistic photographic quality,
16:9 cinematic aspect ratio
```

色彩方案更新：
- 背景：深蓝/黑，冷色调科技感
- 强调色：橙色 #FFC832 / 黄色（突出主题关键词）
- 青色仅用作辅助点缀（不再作为主强调色）
- 整体更接近 Bloomberg 双色极简风格（深色 + 暖橙）

### 判定规则
| 杂志 | 中文名 | 风格 | core_topic |
|------|--------|------|------------|
| Bloomberg | 彭博商业周刊 | NotebookLM 暖白 | economy_domino |
| Science | 科学 | NotebookLM 暖白 | health_environment |
| Wallstreet Journal | 华尔街日报 | 深色科技感 · 电影极简版 | finance |
| Economist | 经济学人 | 深色科技感 · 电影极简版 | economy_domino |
| New Yorker | 纽约客 | 深色科技感 · 电影极简版 | society |
| Barron's | 巴伦周刊 | 深色科技感 · 电影极简版 | finance |
| Foreign Affairs | 外交事务 | 深色科技感 · 电影极简版 | politics_power |
| The Atlantic | 大西洋月刊 | 深色科技感 · 电影极简版 | society |
| National Geographic Traveller | 国家地理旅行者 | 深色科技感 · 电影极简版 | society |
| New Scientist | 新科学家 | 深色科技感 · 电影极简版 | health_environment |
| Times | 泰晤士报 | 深色科技感 · 电影极简版 | society |
| National Geographic | 国家地理 | 深色科技感 · 电影极简版 | environment |
| National Geographic Traveller | 国家地理旅行者 | 深色科技感 · 电影极简版 | society |

## ⚠️ 【2026-05-17 教训】禁止在 ~/ 根目录创建文件

**所有文件必须放在 ~/hermesagent/ 下的项目子文件夹中，禁止在 /Users/chaojin/ 根目录创建任何文件或文件夹。**

| 项目 | 正确路径 |
|------|---------|
| YouTube/magazine 脚本 | `~/hermesagent/Youtube video/magazine/` |
| processed.txt | `~/hermesagent/Youtube video/magazine/processed.txt` |
| upload_video.py | `~/hermesagent/Youtube video/magazine/upload_video.py` |
| 调试脚本 | `~/hermesagent/Youtube video/magazine/_debug_scripts/` |
| scan_and_process.py | `~/hermesagent/Youtube video/magazine/scan_and_process.py` — 全自动流水线扫描处理器（cron用） |
| Anything-to-Notion | `~/hermesagent/Anything-to-Notion/` |

**禁止行为：**
- ❌ `~/magazine/` — 已迁移，不要再使用
- ❌ `~/check_*.py`、`~/run_*.py` 等根目录脚本
- ❌ 在 `/Users/chaojin/` 直下创建任何文件

临时文件仍然可以用 `/tmp/`（系统自动清理），其他所有项目文件必须走 `~/hermesagent/`。

## ⚠️ 所有音频都是中文内容（2026-05-14 确认）

该频道的所有音频文件（WSJ、Bloomberg、Science、New Yorker、Economist）均以中文播客形式录制。Whisper 转录时必须指定 `language='zh'`，即使 New Yorker 是英语杂志，中文播客版本仍需用中文模式。

**错误做法**（已踩坑）：
```python
result = model.transcribe('/tmp/audio.mp3', language='en')  # ❌ 中文内容用英文模式会产生中英混杂的乱码
```

**正确做法**：
```python
result = model.transcribe('/tmp/audio.mp3', language='zh')  # ✅ 所有音频都用中文模式
```

## ⚠️ Whisper SRT 输出失败 bug（2026-05-13 新增）

**现象**：`whisper file.mp3 --model small --output_format srt` 命令行模式下，SRT 文件经常写入失败（0 字节或根本不会创建），但 `--output_format txt` 始终正常。多次重试（在不同进程中）结果相同。Hermes 后台终端的 pipe 缓冲和 `tail` 命令可能加剧此问题。

**根因猜测**：Whisper CLI 的 SRT writer 在输出到 pipe 时文件描述符处理存在竞态条件，或 `shutil.move` 在并发情况下失败。

**解决方案**：用 Python API 直接调用 whisper 库，手动写 SRT：
```python
import whisper
model = whisper.load_model('small')
result = model.transcribe('/tmp/audio.mp3')
lines = []
for i, seg in enumerate(result['segments'], 1):
    start, end = seg['start'], seg['end']
    def fmt(t):
        h = int(t//3600); m = int((t%3600)//60)
        s = int(t%60); ms = int((t-int(t))*1000)
        return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
    lines.append(str(i))
    lines.append(f'{fmt(start)} --> {fmt(end)}')
    lines.append(seg['text'].strip())
    lines.append('')
with open('/tmp/output.srt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
```

## ⚠️ v5 Block JSON 生成陷阱（2026-05-14 多次踩坑）

**现象**：使用 `delegate_task` 生成 v5 blocks JSON 时，子代理经常输出错误字段名：
- ❌ 用 `block_id`/`topic` 代替 `title`/`argument`
- ❌ 用秒数（如 `0`/`180`）代替 `"HH:MM:SS"` 格式
- ❌ 额外字段（`id`, `topic` 等）未清理

**根因**：子代理参考了旧格式的 blocks 或其他不兼容的模板。

**解决方案**：生成后立即运行验证脚本：
```python
python3 -c "
import json
with open('/path/to/blocks.json') as f:
    blocks = json.load(f)
required = {'title','argument','start_time','end_time','summary','keywords','visual_prompt'}
for i, b in enumerate(blocks):
    missing = required - set(b.keys())
    if missing:
        print(f'Block {i}: missing {missing}')
    # Check time format
    for key in ('start_time','end_time'):
        val = b[key]
        if isinstance(val, int) or not ':' in str(val):
            print(f'Block {i}: {key} format wrong: {repr(val)}')
    # Check summary length
    if len(b.get('summary','')) < 150:
        print(f'Block {i}: summary too short ({len(b[\"summary\"])} chars)')
    if len(b.get('keywords',[])) > 7 or len(b.get('keywords',[])) < 3:
        print(f'Block {i}: keywords count {len(b[\"keywords\"])}')
"
```

**修复命令**（字段重命名 + 时间格式转换）：
```python
for b in blocks:
    if 'id' in b: b['title'] = b.pop('id')
    if 'topic' in b: b['argument'] = b.pop('topic')
    if isinstance(b['start_time'], int):
        h=b['start_time']//3600; m=(b['start_time']%3600)//60; s=b['start_time']%60
        b['start_time'] = f'{h:02d}:{m:02d}:{s:02d}'
    if isinstance(b['end_time'], int):
        h=b['end_time']//3600; m=(b['end_time']%3600)//60; s=b['end_time']%60
        b['end_time'] = f'{h:02d}:{m:02d}:{s:02d}'
```

## ⚠️ Whisper 转录语言选择（中英双播客）

New Yorker 中文播客的转录需要用 `language='zh'` 而非 `language='en'`。如果先用英文模式转录中文内容，会输出混乱的中英混杂文字。
- Bloomberg/Science/WSJ 中文播客 → `language='zh'`
- 如果内容未知，先读取转录前几行判断语言再决定


## ⚠️ Block JSON 时间估算方法（无 SRT 时）

当 SRT 文件不可用时（转录以 txt 输出），可以通过以下方法估算 block 时间：
1. 从之前 Whisper stdout 输出中收集零散的时间戳锚点
2. 根据转录文本行数比例分配总时长（总时长从 `ffprobe` 获取）
3. 结合内容逻辑分段边界（话题切换点）校准时间
4. 质检 APPROVED 后即可进入图片生成，时间精度在误差 ±10 秒内不影响视频渲染

2026-05-13 Science 案例验证：16:27 音频，6 block，估算时间与最终 SRT 生成的视频完全对齐。

## ⚠️ Imagen 3 NO TEXT 严格规范（2026-05-12 更新）
**这步是多次踩坑的教训。Imagen 会在背景图里生成英文文字。**
必须把这一串写进 prompt 末尾，缺一不可：
```
NO TEXT, NO LETTERS, NO NUMBERS, NO WORDS, NO CAPTIONS, NO LABELS anywhere in the image.
Pure visual background only.
```

如果 visual_prompt 包含"展板/文档/屏幕/对比"等可能被解读为文字载体的元素：
```
NO TEXT, NO LETTERS, NO NUMBERS, NO DOCUMENTS, 
NO SCREENS, NO PANELS, NO CAPTIONS, NO LABELS anywhere in image.
```

见 references/imagen-no-text-prompt-engineering.md

## 🎬 视频渲染：ffmpeg 图片幻灯方案（2026-05-13 更新）

### ⚠️ Block JSON 时间格式解析方法（2026-05-15 踩坑）

Block JSON 中的 `start_time` / `end_time` 使用 `HH:MM:SS` 格式但含义为 **MM:SS**（小时字段实际上代表分钟，因为音频通常 < 1 小时）。

示例：`04:10:00` = 4分10秒 = 250s，`28:04:00` = 28分4秒 = 1684s

```python
def blocks_time_to_seconds(t):
    """Parse 'HH:MM:SS' where HH is actually minutes for short audio"""
    parts = t.split(':')
    mm = int(parts[0])  # 实际是 minutes
    ss = int(parts[1])  # 实际是 seconds
    return mm * 60 + ss

# 验证：最后一帧的 end_time 应等于音频时长
times = [blocks_time_to_seconds(b['start_time']) for b in blocks]
times.append(blocks_time_to_seconds(blocks[-1]['end_time']))
audio_duration = int(ffprobe_duration)  # 从 ffprobe 获取
assert times[-1] == audio_duration, f"Mismatch: {times[-1]} != {audio_duration}"
block_durations = [times[i+1] - times[i] for i in range(len(times)-1)]
print(f'Block durations: {block_durations}, total: {sum(block_durations)}s')
```

### ⚠️ delegate_task 时间格式双重陷阱（2026-05-18 踩坑）

**现象**：delegate_task 生成的 blocks 可能使用 `HH:MM:SS` 中 HH=实际小时（如 `00:04:15` = 4m15s），与 skill 定义的 HH=分钟（`04:15:00` = 4m15s）格式不一致。两种格式在数值上不同：
- HH=小时：`00:04:15` → `0*3600 + 4*60 + 15` = 255s
- HH=分钟：`04:15:00` → `4*60 + 15` = 255s

虽然总秒数相同，但格式不同会导致 render 脚本的 `int(parts[0])*60` 解析错误。

**修复方法**：delegate_task prompt 中必须包含明确的时间格式示例：
```
时间格式示例：
- 3分30秒 → "03:30:00"
- 22分33秒 → "22:33:00"
- 不写 "00:03:30" 这种 HH=小时格式
```

**生成后的双重验证**（2026-05-18 新增）：
```python
# 验证1：format check - 分钟部分不应超过音频总时长÷60
last_end = blocks[-1]['end_time']
minutes_part = int(last_end.split(':')[0])
audio_minutes = audio_duration // 60
if minutes_part > audio_minutes + 5:
    print(f"⚠️ 时间格式可能错误: last_end={last_end}, 音频约{audio_minutes}m")

# 验证2：parse check - ts_to_sec(last_end) == audio_duration
parsed = int(last_end.split(':')[0]) * 60 + int(last_end.split(':')[1])
assert parsed == audio_duration, f"Parse mismatch: {parsed} != {audio_duration}"
```

## ⚠️ render_video.py 时间解析 bug（已修复 2026-05-18）

⚠️ **历史问题（2026-05-18 修复）**：旧版 `ts_to_sec()` 使用 `int(parts[0]) * 60 + int(parts[1]) * 60 + int(parts[2])`，導致 `"24:23:00"` 被解析為 2820s 而非 1463s（double-count of minutes）。

**修复**：改用 `int(parts[0]) * 60 + int(parts[1])`（HH=分鐘, MM=秒, SS=幀率/忽略）。

**驗證方法**：渲染後用 ffprobe 檢查輸出時長是否等於音頻時長：
```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 output.mp4
```
render_video.py 在渲染後會自動執行此驗證。

### concat 文件总时长验证（2026-05-15 验证）
创建 concat.txt 后，用 awk 快速验证总时长与音频是否匹配：
```bash
echo "Concat: $(awk '/^duration/{s+=$2}END{print s+0}' concat.txt)s"
AUDIO_DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 audio.mp3)
echo "Audio: ${AUDIO_DURATION%.*}s"
```
concat 总时长应略大于音频时长（因 ffmpeg 用 `-t` 截断）。相差超过 5 秒说明 block 时间分配有误。

比逐片段生成 TS 更简单，无需临时文件清理。

**⚠️ 踩坑教训（2026-05-14）**：`-shortest` 在 concat demuxer 中不可靠。
当 concat 总时长 > 音频时长时，`-shortest` 不会正确截断，导致视频比音频长 10+ 秒。
**解决方案**：使用 `-t <音频时长秒数>` 替代 `-shortest`。

**正确方法**：
```bash
# 1. 创建 concat.txt
echo "file 'cover.png'" > concat.txt
echo "duration 5" >> concat.txt           # cover 5秒
for img in block_01.png block_02.png ...; do
  echo "file '$img'" >> concat.txt
  echo "duration $SECONDS" >> concat.txt   # 每个block的秒数
done
echo "file 'last_block.png'" >> concat.txt # ffmpeg要求最后一帧重复

# 2. 获取音频时长
AUDIO_DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 audio.mp3)
AUDIO_DURATION=${AUDIO_DURATION%.*}  # 取整

# 3. 渲染（用 -t 替代 -shortest）
ffmpeg -y -f concat -safe 0 -i concat.txt \
  -i audio.mp3 \
  -c:v libx264 -c:a aac -b:a 192k \
  -t $AUDIO_DURATION \
  -pix_fmt yuv420p -preset fast -crf 23 -vf fps=30 \
  output.mp4
```

**关键**：用 `-t <seconds>` 而非 `-shortest`；`-vf fps=30` 确保帧率一致。

### 方案二（备选）：ffmpeg TS 片段方案
- moviepy 处理 18min 视频会超时（>600s）且音频越界报错
- 正确方案：ffmpeg 逐图片生成 mpegts 片段 + concat 合并
  （~3分钟渲染 18min 1080p 视频）
- 见 references/ffmpeg-image-slideshow-video.md

## 🚨 YouTube 每日上传配额限制（2026-05-13 踩坑 / 2026-05-17 更新上限）

**现象**：连续上传 5+ 视频时，第 3-5 个视频收到 400 错误：
```
"The user has exceeded the number of videos they may upload"
```

**根因**：YouTube 频道有**每日上传数量软限制**，未验证或新频道通常 1-3 个/天，已验证账号约 50-100 个/天。注意这是频道级别的限制，**不同于** Google Cloud Project 的 API 配额（10,000 points/天）。

**2026-05-17 实际验证**：当天成功上传了 63 个视频后才遇到 `max_daily_uploads` 脚本限制，且 YouTube API 在 63 次后仍接受新的 resumable upload session。实际配额上限可能为 100/天。可以安全地将 `upload_video.py` 的 `max_daily_uploads` 设为 100。

**加重因素**：如果上传失败重试时**重新发起新的 resumable upload session**（而非恢复旧 session），每次重试也算一次配额消耗。2026-05-13 WSJ 案例中，503 后重试 3 次导致 1 个文件占用了 4 个上传配额。

**解决方案**：
1. 上传前用 API 检查今天已上传数量：
   ```python
   # Get today's upload count from playlistItems
   today = datetime.now().strftime("%Y-%m-%d")
   uploads_playlist = channels()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
   items = playlistItems().list(playlistId=uploads_playlist, maxResults=50).execute()
   count = sum(1 for i in items["items"] if i["snippet"]["publishedAt"][:10] == today)
   ```
2. 设置 `max_daily_uploads = 50`（保守值）并在超出时跳过
3. 上传重试时，**只恢复 session**（用 `resume_uri`），不新建
4. 如果要用 requests 直接 resumable upload，每次 Init 成功后保存 `Location` header 用于恢复

**配额重置**：每天 UTC 午夜（JST 09:00）重置。配额超限后只能等第二天。

## ⚠️ YouTube 上传失败：SSL read timeout / requests-based fallback（2026-05-13 新增）

**现象**：18-26MB 视频文件上传时，反复出现 `TimeoutError: The read operation timed out`。错误发生在 `socket.readinto` → `ssl.read` 层，非 API 认证错误。小文件（Science 的 53MB 成功过）和大文件（WSJ 的 18-26MB 全失败）无固定规律。

**已确认**：
- 网络到 YouTube API 正常（curl 测试 0.09s 响应）
- GET 请求（video.list）正常工作
- 仅 PUT（resumable upload chunk）超时
- 使用 `youtube_mcp.YouTubeAuth` 与 `googleapiclient.Credentials` 两种 auth 方式均失败

**排查线索**：
- 之前 Science 53MB 上传成功（用 youtube_mcp.YouTubeAuth），同一天 WSJ 上传失败
- 可能是 YouTube 上传区域服务器波动，或日本网络出口到特定上传节点的 TCP 连接不稳定
- 超时时间 600 秒不够——26MB 上传可能因慢速连接需要更长时间

**推荐方案：用 `requests` 库替代 googleapiclient 的 resumable upload**

当 googleapiclient 的 httplib2 持续 SSL timeout 时，直接用 `requests` 手动实现 Resumable Upload 协议更可靠：

```python
import requests as req_lib

# Step 1: Initiate upload session
r = req_lib.post(
    "https://www.googleapis.com/upload/youtube/v3/videos?part=snippet,status&uploadType=resumable",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Upload-Content-Length": str(file_size),
        "X-Upload-Content-Type": "video/mp4",
    },
    json=body_json,
    timeout=30
)
if r.status_code != 200:
    if "exceeded the number of videos" in r.text:
        # DAILY QUOTA EXCEEDED — stop, wait for next day
        break

upload_url = r.headers.get("Location", "")

# Step 2: Upload file bytes in one PUT (requests handles TCP internally)
with open(video_path, "rb") as f:
    video_data = f.read()
r2 = req_lib.put(
    upload_url,
    data=video_data,
    headers={"Content-Length": str(len(video_data)), "Content-Type": "video/mp4"},
    timeout=600
)

if r2.status_code in (200, 201):
    video_id = r2.json().get("id")
```

⚠️ **每次 Init 都会消耗一次上传配额！** 如果 Step 1 成功但 Step 2 失败，该次上传配额仍被消耗。因此建议：
- 最多重试 3 次
- 如果连续 3 次均失败，记录并跳过，**不要无限重试**
- 每次重试间隔至少 5 秒

**其他备选方案**：
1. 让用户在本地终端跑上传（更好的网络连接）
2. 用 `youtube-studio-mcp` 的 MCP 工具上传（尚未实测）
3. 隔天重试（配额重置）

## ⚠️ Google OAuth Drive scope 授权陷阱（2026-05-15 踩坑）

**现象**：用 OOB (Out of Band) 流程请求 Drive scope 时返回 `Error 403: access_denied`。

**根因**：使用中的 client_secret (`825033890920-...`) 所属的 Google Cloud 项目 **未通过 Google 验证**。只有被添加为「测试用户」的账号才能授权。当前 test users 里只有 `hunterhunter00@gmail.com`。

**解决方案**：
1. 在 Google Cloud Console → APIs & Services → OAuth consent screen → Test users 添加 `curarpikt00@gmail.com`
2. 也可以换用已授权的 YouTube OAuth token（但它的 scopes 只有 YouTube，没有 Drive）
3. 或用 YouTube 的 scope 重新授权时**追加 Drive scope**：在 YouTube Auth 流程的 scopes 列表中加上 `'https://www.googleapis.com/auth/drive.file'`

## ⚠️ YouTube OAuth Token 刷新（2026-05-18 更新 — 新增 SimpleCreds fallback 模式）

### 症状
上传时收到 `401: Request had invalid authentication credentials. Expected OAuth 2 access token`。
token 过期时间通常在 1 小时。

### ⚠️ Token 可能缺少 refresh_token（2026-05-18 踩坑）

**现象**：token.json 只有 `access_token` 和 `token`，没有 `refresh_token`、`client_id`、`client_secret`、`token_uri`。
所有 `load_yt_token()` 脚本报 `KeyError: 'refresh_token'`。

**根因**：youtube-mcp 包的 OAuth 流程可能产生无 refresh_token 的 token（取决于 auth code 请求是否包含 `access_type='offline'`）。

**诊断方法**：
```bash
cat ~/.youtube-mcp/token.json | python3 -m json.tool | grep -E 'refresh|client|token_uri'
```
如果只显示 `"refresh_token_expires_in"` 但没有 `"refresh_token"`，说明缺少 refresh_token。

**解决方案**：
1. **获取新 token**：重新运行 OAuth 授权，确保浏览器授权时选择 `hunterhunter00@gmail.com`
2. **重新授权脚本**：
   ```bash
   cd ~/hermesagent/Youtube\ video/magazine/
   YOUTUBE_MCP_CLIENT_SECRET=~/hermesagent/Youtube\ video/client_secret_825033890920-1h4sd9fgomqo80s05uoepelvl8ab5g44.apps.googleusercontent.com.json \
   python3 ~/.hermes/skills/youtube-automation/scripts/auth_youtube.py
   ```
3. **token 文件格式**（带 refresh_token 的正确格式）：
   ```json
   {
     "access_token": "ya29...",
     "token": "ya29...",
     "refresh_token": "1//0e...",
     "client_id": "825033890920-...",
     "client_secret": "GOCSPX-...",
     "token_uri": "https://oauth2.googleapis.com/token",
     "scopes": ["https://www.googleapis.com/auth/youtube"]
   }
   ```

**脚本兼容性修复**：所有 `load_yt_token()` / `load_yt_creds()` 函数应增加 fallback 分支：
```python
def load_yt_token():
    with open(TOKEN_PATH) as f:
        td = json.load(f)
    access_token = td.get("access_token") or td.get("token", "")
    if td.get("refresh_token") and td.get("token_uri"):
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        creds = Credentials(token=access_token, refresh_token=td["refresh_token"],
            token_uri=td["token_uri"], client_id=td.get("client_id",""),
            client_secret=td.get("client_secret",""), scopes=td.get("scopes",[]))
        creds.refresh(Request())
        return creds
    else:
        # Fallback: return raw token as simple object
        class SimpleCreds:
            def __init__(self, token): self.token = token
        return SimpleCreds(access_token)
```
此 fallback 仅支持不需要 `creds.authorize()` 的操作（如 requests 直接调用）。
`googleapiclient.discovery.build(credentials=creds)` 需要 `authorize()` 方法，所以 SimpleCreds 不能用 googleapiclient。

### 症状
⚠️ **另一个症状**：`playlistItems().list()` 返回 0 items（即使频道有 60+ 视频）。见到此情况先刷新 token，不要假设频道为空。

### 检查 token 状态
```bash
python3 -c "
import json
with open('/Users/chaojin/.youtube-mcp/token.json') as f:
    d = json.load(f)
print('expiry:', d.get('expiry'))
print('has refresh_token:', 'refresh_token' in d)
print('has client_id:', 'client_id' in d)
print('token len:', len(d.get('access_token') or d.get('token') or ''))
"
```

### ⚠️ Token 无 refresh_token / SimpleCreds 回退（2026-05-18 踩坑）
**问题**：当前 token.json 可能只有 `access_token`/`token`，没有 `refresh_token`、`client_id`、`client_secret`、`token_uri`。此时：
1. `Credentials(refresh_token=...)` 报 KeyError
2. `googleapiclient.build(credentials=creds)` 报 `'SimpleCreds' object has no attribute 'authorize'`

**解决方案**：使用 SimpleCreds 回退 + requests 库替代 googleapiclient：

```python
def load_yt_token():
    with open(TOKEN_PATH) as f:
        td = json.load(f)
    access_token = td.get("access_token") or td.get("token", "")
    if td.get("refresh_token") and td.get("token_uri"):
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        creds = Credentials(
            token=access_token, refresh_token=td["refresh_token"],
            token_uri=td["token_uri"], client_id=td.get("client_id",""),
            client_secret=td.get("client_secret",""), scopes=td.get("scopes",[]),
        )
        creds.refresh(Request())
        return creds
    else:
        class SimpleCreds:
            def __init__(self, token): self.token = token
        return SimpleCreds(access_token)
```

**⚠️ 关键限制**：SimpleCreds 只有 `.token`，没有 `.authorize()` 方法。
- ❌ 不能用于 `googleapiclient.build(credentials=creds)`
- ✅ 必须直接用 `requests` 库传 `Bearer` header
- ⚠️ `upload_thumbnail()` 和 `dedup_youtube.py` 中的上传/删除函数必须用 `requests` 而非 googleapiclient

详见 `references/youtube-token-refresh.md`。

### 刷新方法（有 refresh_token 时）

### 注意
- token 文件路径：`~/.youtube-mcp/token.json`
- 文件包含 `token`、`refresh_token`、`client_id`、`client_secret`、`expiry` 等字段
- 刷新后 `access_token` 和 `token` 两个字段都应该更新（上传脚本读的是 `access_token`）
- 不需要用户打开浏览器，refresh_token 是 long-lived 的，可直接在后台刷新

## 🚀 YouTube 上传方式（2026-05-12 更新）

### 当前推荐：youtube-studio-mcp Auth + googleapiclient 直传

**使用方式**：安装 `youtube-studio-mcp` 后，利用其 `youtube_mcp.auth.YouTubeAuth` 做 OAuth 授权，
然后用 `googleapiclient` 直接上传。首次授权需在本地终端跑一次，后续 token 持久化。

完整流程：
1. 安装：`pip3 install youtube-studio-mcp`
2. 授权脚本（本地终端跑一次）：
   ```python
   import os
   os.environ["YOUTUBE_MCP_CLIENT_SECRET"] = "/path/to/client_secret.json"
   from youtube_mcp.auth import YouTubeAuth
   auth = YouTubeAuth()
   creds = auth.authenticate()  # 自动弹出浏览器
   ```
3. 上传脚本（可在 Hermes 后台跑，因为有已持久化的 token）：
   ```python
   from youtube_mcp.auth import YouTubeAuth
   from googleapiclient.http import MediaFileUpload
   auth = YouTubeAuth()
   youtube = auth.build_youtube_service()
   media = MediaFileUpload(file_path, resumable=True)
   body = {"snippet": {"title": title, "description": desc, "categoryId": "25"}, "status": {"privacyStatus": "public"}}
   video = youtube.videos().insert(part="snippet,status", body=body, media_body=media).execute()
   # 设置缩略图
   thumb_media = MediaFileUpload(thumbnail_path)
   youtube.thumbnails().set(videoId=video_id, media_body=thumb_media).execute()
   ```

**新 Google Cloud 项目提醒**：
- 新 client_secret 需要先在 Google Cloud Console 中 **启用 YouTube Data API v3**
  打开 https://console.developers.google.com/apis/api/youtube.googleapis.com/overview?project={PROJECT_ID}
  点"启用"，等 2-3 分钟生效
- OAuth 同意屏幕需要把测试用户（hunterhunter00@gmail.com）加入列表

参见 `references/youtube-studio-mcp.md` 获取完整参考。

| 方式 | 状态 | 场景 |
|------|------|------|
| youtube-studio-mcp auth + googleapiclient 直传 | ✅ 推荐 | OAuth 首次授权需本地终端，上传可在 Hermes 后台 |
| youtube-studio-mcp MCP server 集成 | 🔄 待验证 | MCP 集成模式（尚未实测） |

### Client Secret 文件位置
```
~/hermesagent/Youtube video/client_secret_825033890920-1h4sd9fgomqo80s05uoepelvl8ab5g44.apps.googleusercontent.com.json
```

新 client_secret（910102927961 项目）已弃用。

### 🎨 纯 Pillow 图片方案（备选/批量方案，2026-05-13 验证）

当 Imagen 3 quota 不足或需要批量生成大量图片时（如一次 35 张），可以使用纯 Pillow 图片方案：

**何时使用**：
- Imagen 3 quota 耗尽且无法等待
- 批量生成 >10 张图（纯 Pillow 可以在几秒内生成 35 张）
- 快速原型、用户预览阶段

**风格设计**：
- 封面使用深色 + 金色/品牌色（如 WSJ 深蓝底 + 黄条）
- 内容图使用深暖色背景（#14192D）+ 左侧品牌色竖线 + 白色大标题 + 金黄色副标题
- 底部统一品牌条（品牌色全宽底边条 + 品牌名标签）
- 字体：STHeiti Medium（标题 72px）/ STHeiti Light（副标题 42px）

**⚠️ 用户偏好**：2026-05 用户对 Science 使用了 NotebookLM 暖白信息图方案（两步法），对 WSJ 使用深色方案。不同杂志可以用不同风格。但纯 Pillow 方案应作为"预览/快速原型"使用，最终发布视频建议走两步法。

**最佳实践**（2026-05-13 WSJ 批量验证）：
```python
def draw_cover(filename, date_str, n_blocks):
    img = Image.new('RGB', (W, H), color=(10, 20, 50))  # 深色品牌底
    draw = ImageDraw.Draw(img)
    # 顶部品牌条
    draw.rectangle([0, 0, W, 8], fill=(255, 200, 50))
    # 杂志名大标题
    draw.text((80, 100), "华尔街日报", fill=(255, 200, 50), font=big_font)
    # 日期
    draw.text((80, 240), f"深度解读 · {date}", fill=(200, 200, 200), font=date_font)
    # 分隔线
    draw.rectangle([80, 300, 500, 304], fill=(255, 200, 50))
    # 底部品牌条
    draw.rectangle([0, H-60, W, H], fill=(255, 200, 50))

def draw_block(filename, title, argument, i, n):
    img = Image.new('RGB', (W, H), color=(20, 25, 45))
    draw = ImageDraw.Draw(img)
    # 进度条
    draw.rectangle([progress_x, 30, progress_x+200, 34], fill=(60,60,80))
    fill_w = int(200 * i / n)
    draw.rectangle([progress_x, 30, progress_x+fill_w, 34], fill=(255,200,50))
    # 左侧金色竖线
    draw.rectangle([60, 180, 64, 360], fill=(255, 200, 50))
    # 标题
    draw.text((100, 180), title, fill=(255,255,255), font=title_font)
    # 核心论点
    draw.text((100, 290), argument, fill=(255,200,50), font=arg_font)
    # 底部品牌条
    draw.rectangle([0, H-60, W, H], fill=(255, 200, 50))
```

## ⚠️ 后台进程 ~ 路径不展开（2026-05-13 新增）

**现象**：在后台进程（或 sourced 的脚本）中，Python 的 `open('~/path/file.txt', 'w')` 会报 `FileNotFoundError`，因为 `~` 不会被 shell 展开。

**解决方案**：始终用绝对路径或 `os.path.expanduser()`：
```python
# ❌ 错误：后台进程不会展开 ~
with open('~/magazine/file.txt', 'w') as f: ...
# ✅ 正确：显式展开
with open(os.path.expanduser('~/magazine/file.txt'), 'w') as f: ...
# ✅ 更安全：直接写绝对路径
with open('/Users/chaojin/magazine/file.txt', 'w') as f: ...
```

## ⚠️ 缩略图上传大小限制（2026-05-13 新增）
## ⚠️ 缩略图上传方法选择（2026-05-18 新增）

**上传缩略图必须用 `requests` 库，不要用 `googleapiclient`**。

原因：
- 当token没有 `refresh_token` 时（`SimpleCreds` 模式），`googleapiclient.build(credentials=SimpleCreds)` 会报 `'SimpleCreds' object has no attribute 'authorize'`
- `requests` 带 `Bearer` header 的 POST 方式兼容所有 token 格式

```python
# ✅ 正确 — 用 requests
import requests as req
buf = io.BytesIO()
img.resize((1280, 720), Image.LANCZOS).save(buf, "JPEG", quality=90)
r = req.post(
    f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={video_id}",
    headers={"Authorization": f"Bearer {creds.token}", "Content-Type": "image/jpeg"},
    data=buf.getvalue(), timeout=30
)

# ❌ 错误 — 用 googleapiclient。当creds是SimpleCreds时崩溃：
# yt = build("youtube", "v3", credentials=creds)  # AttributeError!
```

**现象**：直接上传 1920×1080 PNG 缩略图（~2.0MB）会收到 `MediaUploadSizeError: Media larger than: 2097152`（2MB 限制）。

同上

**现象**：直接上传 1920×1080 PNG 缩略图（~2.0MB）会收到 `MediaUploadSizeError: Media larger than: 2097152`（2MB 限制）。

**解决方案**：上传前用 Pillow 压缩：
```python
from PIL import Image
img = Image.open(cover_png_path)
img = img.resize((1280, 720), Image.LANCZOS)  # 降低分辨率
buf = io.BytesIO()
for quality in range(85, 10, -5):  # 逐级降低品质直到 < 1.9MB
    buf.seek(0); buf.truncate()
    img.save(buf, format='JPEG', quality=quality, optimize=True)
    if buf.tell() < 1900 * 1024: break
with open('/tmp/thumbnail.jpg', 'wb') as f: f.write(buf.getvalue())
# 然后上传 JPEG 格式
from googleapiclient.http import MediaFileUpload
thumb_media = MediaFileUpload('/tmp/thumbnail.jpg', mimetype='image/jpeg')
youtube.thumbnails().set(videoId=video_id, media_body=thumb_media).execute()
```

### 📋 YouTube Category ID 指南

| 杂志 | 推荐 Category | ID |
|------|---------------|----|
| Bloomberg | News & Politics | 25 |
| Science | Education | 27 |
| Economist | News & Politics | 25 |
| New Yorker | Entertainment | 24 |
| Barron's (巴伦周刊) | News & Politics | 25 |
| Foreign Affairs (外交事务) | News & Politics | 25 |
| National Geographic Traveller (国家地理旅行者) | Education | 27 |
| The Atlantic (大西洋月刊) | News & Politics | 25 |
| Times (泰晤士报) | News & Politics | 25 |
| New Scientist (新科学家) | Science & Technology | 28 |
| National Geographic (国家地理) | Education | 27 |

2026-05-13 Science 上传验证：Category 27 = Education 正确，内容为中文科普播客。

## ⚠️ Google Drive 下载认证（2026-05-15 更新：用服务账号代替 ADC）

### 环境
Drive ADC（Application Default Credentials）的 scope 可能过期或被限制，`drive_token.pickle` 也可能失效。
**已验证的可靠方案**：用 Imagen 3 的服务账号 JSON 直接下载 Drive 文件。

详见 `references/drive-sa-download.md`。

### 快速下载模板
```python
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

SA_PATH = "/Users/chaojin/hermesagent/Youtube video/hermes-infra-prod-9c5abf6aefe8.json"
creds = service_account.Credentials.from_service_account_file(SA_PATH, scopes=['https://www.googleapis.com/auth/drive'])
service = build('drive', 'v3', credentials=creds, cache_discovery=False)

# Download
request = service.files().get_media(fileId=FILE_ID)
fh = io.BytesIO()
downloader = MediaIoBaseDownload(fh, request)
done = False
while not done:
    status, done = downloader.next_chunk()
with open('/tmp/output.mp3', 'wb') as f:
    f.write(fh.getvalue())
```

### 扫描文件夹
`scripts/scan_drive_audio.py` 已更新为使用服务账号。

## 📁 可复用脚本

skill 目录下的脚本文件（`~/.hermes/skills/youtube-automation/scripts/`）：
- **`check_youtube_quota.py`** — ... (existing content)
```
...
```

## 📁 可复用模板

skill 目录下的模板文件（`~/.hermes/skills/youtube-automation/templates/`）：
- **`gen_blocks.py`** — 手动 Block JSON 生成模板，含 ffprobe 时长获取、inline 字段验证、时间总长匹配断言。复制为 `gen_blocks_{magazine}_{date}.py` 后编辑。
- **`gen_images.py`** — 两步法图片生成模板（**暗色科技感风格**，适用于Econ/WSJ/NY/Barron's等）。Imagen 3 背景 + Pillow 文字 + PDF 封面叠加 + 缩略图。含暗色渐变回退方案和 429 重试。
- **`gen_images_notebooklm.py`** — 两步法图片生成模板（**NotebookLM 暖白信息图风格**，适用于Science/Bloomberg）。Imagen 3 暖白背景 + Pillow 文字（深色/暖色文字）+ PDF 封面叠加 + 缩略图。含暖白渐变回退方案和 429 重试。
- **`render_video.py`** — ffmpeg concat 视频渲染模板。自动检测封面图和 block 图片，解析 HH:MM:SS 时间戳，用 `-t` 精确匹配音频时长。用法：`python3 render_video.py <slug> <YYYYMMDD> <audio_path> [image_dir]`。无需手动写 concat.txt。
- **`ad-hoc-upload-script-pattern.md`** — 独立上传脚本模板，适用于 security scanner blocking 或 upload_video.py bug 时。含 token 获取、配额检查、resumable upload、缩略图上传、processed.txt 记录全流程。<!-- TEMPLATE_INDEX_END -->

## 📁 参考文件索引

skill 目录下的 reference 文件。新文件会自动被 `skill_view()` 列出：

| 文件 | 内容 |
|------|------|
| `references/manual-blocks-step-by-step-2026-05-17.md` | 本session三个文件的手动分块实战案例（Foreign Affairs + The Atlantic） |
| `references/background-image-generation.md` | 后台进程运行Imagen时的策略：poll等待 vs 文件检查、预下载技巧 |
| `references/pre-download-strategy.md` | 在图片生成后台等待期间预下载后续音频文件的策略 |
| `references/drive-root-id-change-2026-05-18.md` | Drive 根文件夹ID变更的记录和查证方法 |
| `references/scan-date-matching-bug-2026-05-18.md` | 对账脚本日期-only匹配导致跨杂志误判的bug和修复（2026-05-18） |
| `references/backfill-description-tags.md` | 给存量视频回填三标签去重信息的工作流 |
| `references/backlog-wsj-20260302.md` | WSJ 2026-03-02 待处理文件记录（false-match遗漏） |
| `references/backlog-items.md` | 当前待处理文件列表（如需添加） |
| `references/reconciliation-date-matching.md` | 杂志名归一化+日期匹配对账法（2026-05-18 验证：34→7的真正新文件筛选） |
| `references/bloomberg-notebooklm-2026-05-18.md` | Bloomberg 20260201 首次流水线处理实录（NotebookLM暖白风格、Imagen安全模式、PDF命名） |
  ```
- **`auth_youtube.py`** — 首次 OAuth 授权脚本，在有桌面环境的终端跑一次，自动打开浏览器
- **`change_privacy.py`** — 修改已有视频的隐私状态（private/unlisted/public）。传入 video ID 即可。
- **`scan_drive_audio.py`** — 扫描 Google Drive 中所有杂志文件夹的 audio 目录，汇总音频文件列表。
- **`scan_and_reconcile.py`** — 全量扫描 + YouTube 对账二合一。遍历 16 个杂志文件夹的所有年份 audio/ 子目录，读取 processed.txt，检查 YouTube playlistItems，输出真正未处理的新文件列表（含今日配额剩余）。是每日 cron 任务的第一步。使用方式: `python3 scripts/scan_and_reconcile.py --output /tmp/scan_result.json`
- **`upload_video.py`** — 改进版上传脚本，使用 `requests` 替代 googleapiclient 的 httplib2 以避免 SSL timeout。内置防重复检查、每日配额检查、3 次重试、自动缩略图压缩。
  ```bash
  python3 scripts/upload_video.py /tmp/video.mp4 \\
    --title "视频标题" --description "描述" --tags "标签" \\
    --category 25 --cover /tmp/cover.png
  # 仅检查今日配额
  python3 scripts/upload_video.py --check
  ```
- **`upload_to_youtube.py`** — 原始上传脚本（用 googleapiclient）。
- **`upload_to_youtube.py`** — YouTube 上传脚本（CLI 参数化），支持 title/description/thumbnail/category/privacy
  缩略图自动压缩：如 PNG > 1.9MB 自动压缩为 1280x720 JPEG
  ```bash
  YOUTUBE_MCP_CLIENT_SECRET="/path/to/client_secret.json" python3 scripts/upload_to_youtube.py \
    /tmp/video.mp4 \
    --title "视频标题" \
    --description "描述文字" \
    --thumbnail /tmp/cover.png \
    --category 25 \
    --privacy public
  ```
    /tmp/video.mp4 \
    --title "视频标题" \
    --description "描述文字" \
    --thumbnail /tmp/cover.png \
    --category 25 \
    --privacy public
  ```
- **`generate_dark_tech_images.py`** — 深色科技感两步法生成图片（2026-05-14 新增）。适用于 WSJ/New Yorker/Economist 等使用深色科技感风格的杂志。用法见文件头部注释。
- **`generate_block_images.py`** — 两步法生成图片（Imagen 3 背景 + Pillow 文字叠加）
  支持多杂志：通过 `--magazine-name` 和 `--date-str` 自定义封面
  ```bash
  # Bloomberg 封面+所有 block
  python3 scripts/generate_block_images.py blocks.json /tmp/output --cover-only

  # Science 杂志（不同封面 prompt）
  python3 scripts/generate_block_images.py blocks.json /tmp/science_images \
    --cover-only \
    --magazine-name "Science" \
    --date-str "2026.03" \
    --cover-prompt "NotebookLM clean editorial infographic style, ... abstract scientific visualization, DNA helix and quantum physics motifs, ..."
  ```

## 📋 已处理音频追踪

每次开始处理音频前，先读取 `~/hermesagent/Youtube video/magazine/processed.txt`，对比扫描结果跳过已处理的。
处理完成后，自动将记录追加到 `~/hermesagent/Youtube video/magazine/processed.txt`。

文件格式：
```
Drive文件ID,文件名,处理时间,YouTube视频链接
```

详见 `references/drive-scanning.md`。

## 🔄 完整自动化流程（Drive 到 YouTube）

用户定义的完整 Pipeline 架构：

```
每天 JST 09:00 (cron 触发)
    │
    ├── 1. 扫描 Drive → Globalmagzineyoutube/*/audio/*.mp3
    │     对比 processed.txt → 找出未处理文件
    │
    ├── 2. 对每个新文件执行 Pipeline:
    │     下载(Drive API) → 转录(Whisper zh) → Block JSON → 
    │     图片(Imagen 3两步法) → 视频(ffmpeg concat) → 
    │     上传(upload_video.py)
    │     串行执行，一个完成才到下一个
    │
    └── 3. 记录到 processed.txt
```

**Cron job 已创建**（2026-05-15）：
- 名称：YouTube自动Pipeline - 每日扫描处理
- 时间：每天 JST 09:00
- 触发后自动扫描、处理、上传
- 结果发送到 Telegram 群组

**手动触发**：`hermes cron run YouTube完整流水线`

**现有 cron job（2026-05-18 更新）**：
- `97a976d4ece3` — YouTube 完整流水线 - 每小时全自动处理
- 每小时整点执行 `scan_and_process.py`
- 不再使用双 job 模式（LLM扫描 + drive_scan.py）

详见 `references/cron-architecture-2026-05-18.md`

**音频源：** Google Drive（不是本地目录）
**临时工作目录：** `~/magazine/`（下载、处理用，不做持久存储）
**已处理追踪：** `~/hermesagent/Youtube video/magazine/processed.txt`

详见 `references/drive-scanning.md`。

## 📁 Drive 上传保存（用户要求 — 2026-05-15 新增）

每次完成视频处理后，**必须**将所有素材上传到 Drive：
视频文件(.mp4)、封面图(cover.png)、所有block图(block_01~.png)、blocks JSON、转录文本

存放路径：
`Globalmagzineyoutube/{杂志名}/{年份}/video/{杂志名}_{日期}/`

示例：`Globalmagzineyoutube/Economist/2026/video/Economist_2026-04-04/`

如果 folder 不存在，用 Drive API 创建。
上传完后，在本地的 `~/hermesagent/Youtube video/magazine/processed.txt` 追加记录。

### ⚠️ Drive 上传文件命名规范（2026-05-15 用户校正）

**不能用 `video.mp4` / `cover.png` 作为文件名**——多个 issue 的文件名必须能区分。

**正确命名规则：**

| 文件类型 | 命名格式 | 示例 |
|---------|---------|------|
| 视频 | `{杂志}_{YYYY-MM-DD}.mp4` | `Economist_2026-04-04.mp4` |
| 封面 | `{杂志}_{YYYY-MM-DD}_cover.png` | `Economist_2026-04-04_cover.png` |
| Block图 | `{杂志}_{YYYY-MM-DD}_block_{编号}.png` | `Economist_2026-04-04_block_01.png` |
| Blocks JSON | `{杂志}_{YYYY-MM-DD}_blocks.json` | `Economist_2026-04-04_blocks.json` |
| 转录文本 | `{杂志}_{YYYY-MM-DD}_transcript.txt` | `Economist_2026-04-04_transcript.txt` |

文件夹名：`{杂志}_{YYYY-MM-DD}`（与视频文件前缀一致）

完整路径示例：
```
Globalmagzineyoutube/Economist/2026/video/Economist_2026-04-04/
├── Economist_2026-04-04.mp4
├── Economist_2026-04-04_cover.png
├── Economist_2026-04-04_block_01.png
├── Economist_2026-04-04_block_02.png
├── ...
└── Economist_2026-04-04_transcript.txt
```

⚠️ **上传后不可用 `video.mp4` 命名**——即使文件夹名已经叫 `Economist_2026-04-04`，文件本身也要带杂志名+日期。

### ⚠️ Drive OAuth 用户 Token 上传方案（2026-05-15 已验证）

**当 SA 无存储配额时**，可用 OAuth 用户 token 配合 `drive.file` scope 上传：

```python
# 1. 获取 Drive OAuth token（一次性的浏览器授权）
# 使用独立的桌面应用 client_secret + OOB redirect
flow = Flow.from_client_secrets_file(
    client_secret_path,
    scopes=['https://www.googleapis.com/auth/drive.file'],
    redirect_uri='urn:ietf:wg:oauth:2.0:oob'
)
auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
print(f'Open: {auth_url}')
# 用户浏览器授权后粘贴验证码
code = input('Enter code: ')
flow.fetch_token(code=code)
creds = flow.credentials
# 保存到 ~/.drive-upload-token.json

# 2. 刷新 token 并上传
creds.refresh(Request())
token = creds.token

# 3. 用 multipart upload 上传文件
def upload_file(filepath, parent_id, name):
    boundary='-------'+os.urandom(16).hex()
    meta=json.dumps({'name': name, 'parents': [parent_id]})
    with open(filepath,'rb') as f: fdata=f.read()
    body=(('--'+boundary+'\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n'+meta+'\r\n--'+boundary+'\r\nContent-Type: application/octet-stream\r\n\r\n').encode()+fdata+('\r\n--'+boundary+'--\r\n').encode())
    r=req_lib.post('https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': f'multipart/related; boundary={boundary}', 'Content-Length': str(len(body))},
        data=body, timeout=120)
    return r.status_code in (200, 201)

def ensure_folder(name, parent_id):
    q = req_lib.utils.quote(f"name='{name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false")
    r = req_lib.get(f'https://www.googleapis.com/drive/v3/files?q={q}&fields=files(id)',
        headers={'Authorization': f'Bearer {token}'}, timeout=10)
    if r.json().get('files'): return r.json()['files'][0]['id']
    r2 = req_lib.post('https://www.googleapis.com/drive/v3/files',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        json={'name': name, 'parents': [parent_id], 'mimeType': 'application/vnd.google-apps.folder'}, timeout=10)
    return r2.json()['id']
```

⚠️ `drive.file` scope 只能访问该 app 创建或打开的文件，**不能列出已有文件夹**。但是可以**指定 parent ID 创建文件**在已有文件夹下（只要知道 ID）。

⚠️ **Token 路径**：`/Users/chaojin/.drive-upload-token.json`

### ⚠️ Service account Drive 上传陷阱（2026-05-15 踩坑）

**现象**：Service account 使用 `ResumableUploadError: Service Accounts do not have storage quota` (HTTP 403)。

**根因**：Service account 是独立无配额账号，没有 my-Drive 存储空间。它只能：
1. 写入 **Shared Drive**（共享云端硬盘）— 前提是文件夹已转为共享盘
2. 或者被添加为**编辑者**后，在 have storage 的账号下写入
3. 或者通过 **OAuth 2.0 delegation**（域管理员授权）

**解决方案**（按优先级）：

**方案 A：把 service account 添加为共享盘/文件夹的 Editor**
- SA 邮箱：`hermes-bot@hermes-infra-prod.iam.gserviceaccount.com`
- 请在 Drive 中把该邮箱添加为 `Globalmagzineyoutube` 文件夹的 Editor
- 生效后 SA 可直接写入，用下面的模板上传

**方案 B：本地保存（无需 SA 权限的 fallback）**
```python
import shutil, os
OUT_DIR = f'/Users/chaojin/Documents/hermes_output/{magazine}/{year}/video/{magazine}_{date}'
os.makedirs(OUT_DIR, exist_ok=True)
shutil.copy2('/tmp/video.mp4', os.path.join(OUT_DIR, 'video.mp4'))
shutil.copy2('/tmp/cover.png', os.path.join(OUT_DIR, 'cover.png'))
# etc.
```
用户手动从 Documents/hermes_output/ 移动到 Drive。
❗ 不要使用 `cp` 到 `/Users/chaojin/Library/CloudStorage/GoogleDrive-.../` 路径——Apple File Provider 会报 "Resource deadlock avoided" 错误。

**方案 C：用 rclone 上传**
```bash
# First time config:
rclone config  # 选择 Google Drive, OAuth 授权
# Then upload:
rclone copy /tmp/local_dir/ remote:Globalmagzineyoutube/Economist/2026/video/
```
rclone 需要一次性的 OAuth 授权（用户本地终端运行）。如果已配置则可以直接用。

### ⚠️ Drive 文件命名规范（2026-05-15 用户校正 — 必须遵守）
每次 Imagen 3 调用约 5-15 秒，8 张图（1 cover + 7 blocks）约 40-120 秒
加上重试时间，总耗时可能 5-10 分钟
所以默认用后台进程（background=true）执行，等 notify_on_complete

---

## 📂 Absorbed from `youtube-upload-pipeline` (2026-05-15 Consolidation)

The following reference files were merged from the `youtube-upload-pipeline` skill into this umbrella:

| Reference File | What It Covers |
|---|---|
| `references/blocks-json-generation-prompt.md` | Proven system prompt template for v5 Blocks JSON generation (≥100 CN chars, zero-RETRY across 4 NY files) |
| `references/blocks-json-validation.md` | Validation checklist: char count, summary structure, block boundaries, image prompt style, duration |
| `references/google-drive-api-download.md` | Drive API download script (bypasses File Provider deadlock) |
| `references/imagen-safety-filter-workaround.md` | Person-generated prompts → silent empty images; fallback to object-focused prompts. Updated 2026-05-17 with 5 new blocked patterns. |
| `references/new-yorker-audio-file-ids.md` | All NY audio file IDs in Google Drive with status tracking |
| `references/ny-onepass-render-pitfalls.md` | Batch bugs: concat I/O, var scope, duration mismatch, thumbnail race, upload var scope |
| `references/youtube-upload-limits.md` | YouTube channel-level upload restrictions and verification requirements |

### Cover Overlay Pillow Template

The Pillow overlay template for simplified covers (orange magazine name + cyan date on dark bar) is now canonically in the SKILL.md above under the **Cover overlay code template** section. The key constants:

- Bar height: 18% of image height
- Magazine name: Arial Bold, 6% of height, orange (255,180,50)
- Date: Arial, 3% of height, cyan (0,210,255)
- Amber accent line at bar top edge (255,170,40)
- 字体：STHeiti Medium（标题 72px）/ STHeiti Light（副标题 42px）