#!/usr/bin/env python3
"""
scan_and_process.py — 全自动 YouTube 流水线扫描处理器
每小时 cron 触发：
1. 扫描 Drive 所有杂志音频文件
2. 对比 processed.txt + YouTube 找出真正未处理文件
3. 有未处理文件 → 启动完整流水线
4. 无未处理文件 → 安静退出

依赖：
- SA: ~/hermesagent/Youtube video/hermes-infra-prod-9c5abf6aefe8.json
- YouTube token: ~/.youtube-mcp/token.json
- 所有子脚本：gen_blocks.py gen_images.py render_video.py upload_video.py

用法：
  python3 scan_and_process.py
"""

import json, os, sys, re, io, time, hashlib, subprocess

# ── Drive ID 标签（嵌入 YouTube description，作为唯一 key）────────────
DRIVE_ID_TAG_RE = re.compile(r'\[drive_id:([A-Za-z0-9_\-]+)\]')
from datetime import datetime, timezone, timedelta
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
import requests as req_lib

# ── YouTube API 配额追踪（替代写死的 MAX_UPLOADS_PER_DAY）──────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quota_tracker import get_tracker as _get_qt, quota_consume, quota_report

# ── 路径常量 ─────────────────────────────────────
BASE = os.path.expanduser("~/hermesagent/Youtube video/magazine")
SA_PATH = os.path.expanduser("~/hermesagent/Youtube video/hermes-infra-prod-9c5abf6aefe8.json")
PROCESSED = os.path.join(BASE, "processed.txt")
YT_TOKEN = os.path.expanduser("~/.youtube-mcp/token.json")
GEN_BLOCKS = os.path.join(BASE, "gen_blocks.py")
RENDER_VIDEO = os.path.join(BASE, "render_video.py")
UPLOAD_VIDEO = os.path.join(BASE, "upload_video.py")
# ⚠️ 2026-05-19 修复：模板现在放在 magazine 目录，而非不存在的 ~/.hermes 路径
GEN_IMAGES_DARK = os.path.join(BASE, "gen_images.py")
GEN_IMAGES_NOTEBOOKLM = os.path.join(BASE, "gen_images_notebooklm.py")
# 📋 2026-05-19 新增：完整可追溯日志（每行一条视频的所有元素 ID）
PROCESS_LOG  = os.path.join(BASE, "process_log.jsonl")
# 🔄 断点续传：每步完成后立即写入，崩溃/quota 后下次可恢复
ACTIVE_RUNS  = os.path.join(BASE, "active_runs.json")

# 流水线六步，顺序固定
STEP_ORDER = ['download', 'transcribe', 'blocks', 'images', 'render', 'drive_upload', 'upload']
# ⚠️ MAX_UPLOADS_PER_DAY 已废弃 — 改由 quota_tracker 动态计算

# ── Telegram 报警 ─────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8685844314:AAHmqHY-8syyD2wC4bMQz3Pr5kIQV8dgjq0')
TELEGRAM_CHAT_ID   = os.environ.get('TELEGRAM_CHAT_ID',   '8722510089')

# 每步对应的可检查脚本（出错时告知用户去哪里修）
_STEP_SCRIPT = {
    'download':     'scan_and_process.py → download_audio()',
    'transcribe':   'scan_and_process.py → transcribe()  [Whisper]',
    'blocks':       'gen_blocks.py',
    'images':       'gen_images.py / gen_images_notebooklm.py',
    'render':       'render_video.py',
    'drive_upload': 'scan_and_process.py → upload_assets_to_drive()',
    'upload':       'upload_video.py',
}

def send_telegram(msg: str, level: str = 'info') -> None:
    """向 Telegram 推送流水线通知（失败不影响主流程）。
    level: 'ok' | 'info' | 'warn' | 'error' | 'quota' | 'crash'
    """
    icon = {'ok': '✅', 'info': 'ℹ️', 'warn': '⚠️',
            'error': '🔴', 'quota': '⛔', 'crash': '💥'}.get(level, 'ℹ️')
    text = f"{icon} *Hermes Pipeline*\n{msg}"
    try:
        req_lib.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={'chat_id': TELEGRAM_CHAT_ID, 'text': text,
                  'parse_mode': 'Markdown', 'disable_web_page_preview': True},
            timeout=10
        )
    except Exception:
        pass  # 报警失败不中断主流程


def _notify_step_failure(run: dict, step: str, error_detail: str) -> None:
    """格式化步骤失败报告并发送到 Telegram，供用户快速定位问题脚本。"""
    mag   = run.get('magazine', '?')
    fname = run.get('audio_filename', '?')
    dt    = run.get('date', '?')
    script = _STEP_SCRIPT.get(step, step)
    step_idx = STEP_ORDER.index(step) + 1 if step in STEP_ORDER else '?'

    # 截断错误详情防止消息过长
    err_short = (error_detail or '').strip()[-400:]

    msg = (
        f"*步骤失败: {step}* (第{step_idx}/{len(STEP_ORDER)}步)\n\n"
        f"📁 `{fname}`\n"
        f"📰 {mag}  {dt}\n\n"
        f"🔧 需要检查: `{script}`\n\n"
        f"🔴 错误:\n```\n{err_short}\n```\n\n"
        f"📋 查看完整日志:\n`~/hermesagent/Youtube\\ video/magazine/process_log.jsonl`\n\n"
        f"♻️  修复后运行:\n`python3 ~/hermesagent/Youtube\\ video/magazine/scan_and_process.py`"
    )
    send_telegram(msg, level='error')

# ════════════════════════════════════════════════════════════
#  质检门控（QC Gates）— 每个步骤完成后必须通过，失败即停止
# ════════════════════════════════════════════════════════════

_GCP_PROJECT  = 'even-electron-494805-s9'  # 正确项目 ID（非 hermes-infra-prod）
_GCP_LOCATION = 'us-central1'
_GEMINI_MODEL = 'gemini-2.5-flash'        # GA 稳定别名，不加版本后缀，支持 Vision，停用日期 ≥ 2026-10-16


def _ai_check_image(image_path: str, purpose: str) -> tuple:
    """
    用 Gemini Vision 验证图片有实际内容（非黑屏/纯色/空白）。
    返回 (passed: bool, detail: str)。
    QC 自身失败时返回 (True, "AI质检异常") — 网络错误不阻断流程。
    """
    try:
        import base64, requests as _req
        from google.oauth2 import service_account as _sa
        import google.auth.transport.requests as _gatr

        with open(image_path, 'rb') as f:
            raw = f.read()
        b64  = base64.b64encode(raw).decode()
        mime = 'image/png' if image_path.endswith('.png') else 'image/jpeg'

        sa_creds = _sa.Credentials.from_service_account_file(
            SA_PATH, scopes=['https://www.googleapis.com/auth/cloud-platform'])
        sa_creds.refresh(_gatr.Request())

        payload = {
            "contents": [{"parts": [
                {"text": (
                    f"用途：{purpose}\n"
                    "请判断这张图片：\n"
                    "PASS — 有实际内容的AI生成插图（人物/场景/物体/信息图，展示杂志主题）\n"
                    "FAIL — 黑屏/纯黑/纯白/纯色/空白/纯色渐变/明显错误或损坏图像\n"
                    "只回答 PASS 或 FAIL，然后一句话说明（不超过30字）。"
                )},
                {"inline_data": {"mime_type": mime, "data": b64}}
            ]}],
            "generationConfig": {"maxOutputTokens": 80, "temperature": 0.0}
        }
        # 尝试多个模型名，防止单个版本 404
        # 注：gemini-2.0-flash 2026-06-01 停用，gemini-1.5-flash-* 已全面下线
        _models_to_try = [_GEMINI_MODEL, 'gemini-2.5-flash-preview-05-20', 'gemini-2.5-pro', 'gemini-2.0-flash']
        last_err = None
        for _model in _models_to_try:
            url = (f"https://{_GCP_LOCATION}-aiplatform.googleapis.com/v1/projects/{_GCP_PROJECT}"
                   f"/locations/{_GCP_LOCATION}/publishers/google/models/{_model}:generateContent")
            try:
                resp = _req.post(url, headers={"Authorization": f"Bearer {sa_creds.token}"},
                                 json=payload, timeout=30)
                if resp.status_code == 404:
                    last_err = f"404 {_model}"
                    continue
                resp.raise_for_status()
                text   = resp.json()['candidates'][0]['content']['parts'][0]['text'].strip()
                passed = text.upper().startswith('PASS')
                return passed, text
            except Exception as e:
                last_err = str(e)
                if '404' in str(e):
                    continue
                break
        return True, f"AI质检异常(跳过): {last_err}"
    except Exception as e:
        return True, f"AI质检异常(跳过): {e}"


def _qc_download(run: dict, audio_path: str) -> tuple:
    """质检：音频下载 — 文件存在、大小≥1MB、ffprobe有效音频、时长≥120s"""
    if not os.path.exists(audio_path):
        return False, f"文件不存在: {audio_path}"
    size = os.path.getsize(audio_path)
    if size < 1_000_000:
        return False, f"文件太小 ({size//1024} KB < 1 MB)，可能下载不完整"
    checks = [f"大小 {size//(1024*1024)} MB ✓"]
    try:
        r = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_type',
             '-of', 'csv=p=0', audio_path],
            capture_output=True, text=True, timeout=15)
        lines = r.stdout.strip().split('\n')
        if not any('audio' in l for l in lines):
            return False, f"文件无音频流 (ffprobe: {r.stdout[:100]})"
        checks.append("有音频流 ✓")
        for l in reversed(lines):
            try:
                dur = float(l.strip())
                if dur < 120:
                    return False, f"音频时长过短 ({dur:.0f}s < 120s)"
                checks.append(f"时长 {dur:.0f}s ✓")
                break
            except ValueError:
                continue
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        checks.append(f"ffprobe跳过: {e}")
    return True, " | ".join(checks)


def _qc_transcribe(run: dict, transcript_path: str) -> tuple:
    """质检：转录文件 — 存在、≥500bytes、内容≥200字、非乱码"""
    if not os.path.exists(transcript_path):
        return False, f"转录文件不存在: {transcript_path}"
    size = os.path.getsize(transcript_path)
    if size < 500:
        return False, f"转录文件太小 ({size} bytes < 500)，可能为空"
    try:
        with open(transcript_path, encoding='utf-8') as f:
            text = f.read().strip()
    except Exception as e:
        return False, f"无法读取转录文件: {e}"
    if len(text) < 200:
        return False, f"转录内容过短 ({len(text)} chars < 200)"
    unique_chars = len(set(text.replace(' ', '').replace('\n', '')))
    if unique_chars < 20:
        return False, f"转录内容疑似乱码 (只有 {unique_chars} 种不同字符)"
    return True, f"{len(text)} 字 | {len(text.split())} 词 | {unique_chars} 种字符 ✓"


def _qc_blocks(run: dict, blocks_path: str) -> tuple:
    """质检：blocks JSON — 存在、可解析、≥3块、每块有真实标题/时间戳/内容"""
    if not os.path.exists(blocks_path):
        return False, f"blocks JSON 不存在: {blocks_path}"
    try:
        with open(blocks_path, encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return False, f"blocks JSON 解析失败: {e}"
    blocks = data.get('blocks', [])
    if len(blocks) < 3:
        return False, f"blocks 数量不足 ({len(blocks)} < 3)"
    _placeholder = re.compile(
        r'^(段|第)[一二三四五六七八九十\d]+[段节章]?$|^(topic|section|part)\s*\d+$',
        re.IGNORECASE)
    issues = []
    for i, b in enumerate(blocks):
        title   = str(b.get('title', '')).strip()
        content = str(b.get('summary', '') or b.get('content', '') or b.get('argument', '')).strip()
        ts      = b.get('start_time', '') or b.get('timestamp', '')
        if not title:
            issues.append(f"block[{i}] 无 title")
        elif _placeholder.match(title):
            issues.append(f"block[{i}] 标题是占位符: '{title}'")
        if not ts:
            issues.append(f"block[{i}] 无 start_time/timestamp")
        if len(content) < 30:
            issues.append(f"block[{i}] 内容太短 ({len(content)} chars)")
    if issues:
        return False, "blocks质检: " + "; ".join(issues[:3])
    total = sum(len(str(b.get('summary','') or b.get('content','') or b.get('argument','')))
                for b in blocks)
    return True, f"{len(blocks)} blocks | 总内容 {total} 字 ✓"


def _check_image_landscape(path: str, label: str) -> tuple:
    """
    【QC 二道防线】检查图片横版 + 分辨率 ≥ 1280×720。
    主防线：gen_images.py / gen_images_notebooklm.py（W,H=1920×1080 + 保存后断言）。
    此处是安全网：生成时已保证横版，若在 QC 发现竖版说明主防失效需立查。
    返回 (ok, reason)。PIL 不可用时跳过（仅警告）。
    """
    try:
        from PIL import Image
        with Image.open(path) as img:
            w, h = img.size
        if h > w:
            return False, f"{label} 是竖版 ({w}×{h})！必须横版，请检查渲染脚本"
        if w < 1280 or h < 720:
            return False, f"{label} 分辨率不足 ({w}×{h}，需≥1280×720)"
        return True, f"{w}×{h} 横版 ✓"
    except ImportError:
        return True, "PIL不可用，跳过尺寸检查"
    except Exception as e:
        return False, f"{label} 无法读取尺寸: {e}"


def _qc_images(run: dict, img_dir: str, blocks_count: int = 3) -> tuple:
    """质检：图片生成 — thumbnail/cover存在≥30KB、横版≥1280×720、block图≥1张、AI视觉检查"""
    # thumbnail.jpg
    thumb = os.path.join(img_dir, 'thumbnail.jpg')
    if not os.path.exists(thumb):
        return False, "thumbnail.jpg 不存在"
    tsz = os.path.getsize(thumb)
    if tsz < 30_000:
        return False, f"thumbnail.jpg 太小 ({tsz//1024} KB < 30 KB)，疑似黑屏"
    # ── 横版分辨率检查 ────────────────────────────────────────────
    ok, reason = _check_image_landscape(thumb, "thumbnail.jpg")
    if not ok:
        return False, reason
    print(f"      ✅ thumbnail 尺寸: {reason}")

    # cover.png
    cover = os.path.join(img_dir, 'cover.png')
    if not os.path.exists(cover):
        return False, "cover.png 不存在"
    csz = os.path.getsize(cover)
    if csz < 30_000:
        return False, f"cover.png 太小 ({csz//1024} KB < 30 KB)，疑似黑屏"
    ok, reason = _check_image_landscape(cover, "cover.png")
    if not ok:
        return False, reason
    print(f"      ✅ cover 尺寸: {reason}")

    # block 图片数量 + 横版检查
    block_imgs = sorted([f for f in os.listdir(img_dir) if re.match(r'block_\d+\.png$', f)])
    min_exp    = max(1, min(blocks_count, 3))
    if len(block_imgs) < min_exp:
        return False, f"block图片数量不足 ({len(block_imgs)} < {min_exp})"

    # 抽查所有 block 图片的横版（文件大小 + 分辨率）
    portrait_blocks = []
    for bname in block_imgs:
        bpath = os.path.join(img_dir, bname)
        bsz   = os.path.getsize(bpath)
        if bsz < 20_000:
            return False, f"{bname} 太小 ({bsz//1024} KB)，疑似黑屏"
        ok, reason = _check_image_landscape(bpath, bname)
        if not ok:
            portrait_blocks.append(f"{bname}({reason})")
    if portrait_blocks:
        return False, f"block图片存在竖版/分辨率不足: {'; '.join(portrait_blocks[:3])}"

    # AI 视觉质检：thumbnail
    print(f"      🤖 AI质检 thumbnail.jpg ({tsz//1024} KB)...")
    ok, detail = _ai_check_image(thumb, "YouTube封面缩略图")
    if not ok:
        return False, f"thumbnail.jpg AI质检失败: {detail}"
    print(f"      ✅ thumbnail AI: {detail}")

    # AI 视觉质检：cover.png
    print(f"      🤖 AI质检 cover.png ({csz//1024} KB)...")
    ok, detail = _ai_check_image(cover, "视频封面背景图")
    if not ok:
        return False, f"cover.png AI质检失败: {detail}"
    print(f"      ✅ cover AI: {detail}")

    # AI 视觉质检：随机抽一张 block 图（中间那张）
    if block_imgs:
        sample = block_imgs[len(block_imgs) // 2]
        spath  = os.path.join(img_dir, sample)
        ssz    = os.path.getsize(spath)
        print(f"      🤖 AI质检 {sample} ({ssz//1024} KB)...")
        ok, detail = _ai_check_image(spath, "杂志文章配图")
        if not ok:
            return False, f"block图片AI质检失败 ({sample}): {detail}"
        print(f"      ✅ block AI: {detail}")

    return True, f"thumbnail {tsz//1024}KB | cover {csz//1024}KB | {len(block_imgs)}张block图 | 全部横版 ✓"


def _qc_render(run: dict, final_mp4: str) -> tuple:
    """质检：渲染视频 — 存在、≥5MB、ffprobe有视频流、时长≥60s、横版≥1280×720"""
    if not os.path.exists(final_mp4):
        return False, f"MP4不存在: {final_mp4}"
    size = os.path.getsize(final_mp4)
    if size < 5_000_000:
        return False, f"MP4太小 ({size//(1024*1024)} MB < 5 MB)，可能渲染失败"
    checks = [f"大小 {size//(1024*1024)} MB ✓"]
    try:
        # ── 一次 ffprobe 获取 codec_type、时长、分辨率 ────────────────
        r = subprocess.run(
            ['ffprobe', '-v', 'error',
             '-select_streams', 'v:0',
             '-show_entries', 'stream=width,height,codec_type:format=duration',
             '-of', 'csv=p=0', final_mp4],
            capture_output=True, text=True, timeout=20)
        lines = [l.strip() for l in r.stdout.strip().split('\n') if l.strip()]

        # 视频流存在
        if not any('video' in l for l in lines):
            return False, f"MP4无视频流 (ffprobe: {r.stdout[:100]})"
        checks.append("有视频流 ✓")

        # 分辨率 + 横版检查
        vw = vh = 0
        for l in lines:
            parts = l.split(',')
            nums = []
            for p in parts:
                try:
                    nums.append(int(p))
                except ValueError:
                    pass
            if len(nums) >= 2:
                vw, vh = nums[0], nums[1]
                break
        if vw > 0 and vh > 0:
            if vh > vw:
                return False, f"视频是竖版 ({vw}×{vh})！必须横版。请检查 gen_images 和 render_video 的输出尺寸"
            if vw < 1280 or vh < 720:
                return False, f"视频分辨率不足 ({vw}×{vh}，需≥1280×720)"
            checks.append(f"{vw}×{vh} 横版 ✓")
        else:
            checks.append("分辨率未读到（跳过）")

        # 时长
        for l in reversed(lines):
            try:
                dur = float(l)
                if dur < 60:
                    return False, f"视频时长过短 ({dur:.0f}s < 60s)"
                checks.append(f"时长 {dur:.0f}s ✓")
                break
            except ValueError:
                continue
    except subprocess.TimeoutExpired:
        # ffprobe 超时 → 无法验证横版，横版是硬性要求，必须失败
        return False, "ffprobe 超时，无法验证视频横版（请检查 ffmpeg 安装）"
    except FileNotFoundError:
        # ffprobe 未安装 → 同上，不能放行
        return False, "ffprobe 未找到，无法验证视频横版（请安装 ffmpeg）"
    return True, " | ".join(checks)


def _qc_drive_upload(run: dict, drive_assets: dict, mag: str, dt: str) -> tuple:
    """质检：Drive上传 — folder_id存在、文件夹命名规范、MP4/blocks/thumbnail必须上传成功"""
    folder_id = drive_assets.get('folder_id', '')
    if not folder_id:
        return False, "Drive文件夹ID为空（文件夹未创建/找到）"

    # 文件夹命名检查：用规范化 key 做鲁棒匹配（处理大小写/日期格式/分隔符差异）
    folder_name = drive_assets.get('folder_name', '')
    if folder_name:
        expected     = _canonical_folder_name(mag, dt)
        expected_key = _normalize_folder_key(expected, dt)
        actual_key   = _normalize_folder_key(folder_name, dt)
        if actual_key != expected_key:
            return False, (f"文件夹名不符合规范: '{folder_name}'"
                           f" (期望: '{expected}'，规范化后 key='{expected_key}' vs '{actual_key}')")
        if folder_name != expected:
            print(f"      ⚠️ 文件夹命名格式不一致: '{folder_name}' → 期望 '{expected}'（内容正确，可接受）")
    else:
        print(f"      ⚠️ 未获取文件夹名，无法验证命名")

    issues = []
    # MP4 上传（最关键：断点续传依赖）
    if not drive_assets.get('mp4_drive_id'):
        return False, "MP4未上传到Drive (mp4_drive_id为空) — 断点续传无法恢复"
    # blocks JSON
    if not drive_assets.get('blocks_json_id'):
        issues.append("blocks JSON未上传到Drive")
    # thumbnail
    if not drive_assets.get('thumbnail_id'):
        issues.append("thumbnail.jpg未上传到Drive")
    # block 图片
    block_ids = [x for x in drive_assets.get('block_image_ids', []) if x.get('drive_id')]
    if not block_ids:
        issues.append("没有block图片上传到Drive")

    if issues:
        return False, "Drive上传质检: " + "; ".join(issues)

    n = len(block_ids)
    fname = folder_name or (folder_id[:12] + '...')
    return True, f"folder={fname} | MP4✓ | blocks✓ | thumb✓ | {n}张block图✓"


# ── 杂志配置 ─────────────────────────────────────
DARK_TECH_MAGS = {"Economist", "Barron's", "Wallstreet Journal", "New Yorker",
                  "Foreign Affairs", "The Atlantic", "National Geographic",
                  "National Geographic Traveller", "Times", "New Scientist",
                  "Harvard Business Review", "National Geographic History"}
NOTEBOOKLM_MAGS = {"Science", "Bloomberg"}
STYLES = {}  # auto-populated below

def list_all(drive, query, fields='files(id,name,mimeType,size)'):
    """带分页的 Drive 列表"""
    items, pt = [], None
    while True:
        p = {'q': query, 'fields': f'nextPageToken,{fields}'}
        if pt: p['pageToken'] = pt
        r = drive.files().list(**p).execute()
        items.extend(r.get('files', []))
        pt = r.get('nextPageToken')
        if not pt: break
    return items

def get_yt_token():
    """刷新并返回 YouTube access_token"""
    with open(YT_TOKEN) as f:
        d = json.load(f)
    # 如果有 refresh_token 就走刷新
    if d.get('refresh_token'):
        r = req_lib.post(d.get('token_uri', 'https://oauth2.googleapis.com/token'), data={
            'client_id': d['client_id'], 'client_secret': d['client_secret'],
            'refresh_token': d['refresh_token'], 'grant_type': 'refresh_token',
        })
        if r.status_code != 200:
            print(f"  ⚠️ Token refresh failed: {r.status_code}")
            return None
        data = r.json()
        d['access_token'] = d['token'] = data['access_token']
        # 写回 token 文件，避免下次刷新失败（P0 fix）
        try:
            with open(YT_TOKEN, 'w') as fw:
                json.dump(d, fw, indent=2)
        except Exception as e:
            print(f"  ⚠️ 写回 token 文件失败: {e}")
    token = d.get('access_token') or d.get('token', '')
    # 验证
    r = req_lib.get('https://www.googleapis.com/youtube/v3/channels?part=id&mine=true',
                    headers={'Authorization': f'Bearer {token}'}, timeout=10)
    if r.status_code != 200:
        print(f"  ⚠️ YouTube API unavailable (quota?): {r.status_code}")
        return None
    return token


# ── 上传后自动加入播放列表（非致命，失败只记录不中止流水线）─────────────────
_ASSIGN_PL_DIR = os.path.expanduser("~/hermesagent/Youtube video")

def _assign_video_to_playlist(yt_video_id: str, magazine: str) -> bool:
    """
    把刚上传的视频加入对应杂志播放列表。
    复用 assign_youtube_playlists.py 的查找/创建逻辑。
    失败时只 print 警告，不抛异常（不影响主流水线）。
    """
    try:
        import sys as _sys
        if _ASSIGN_PL_DIR not in _sys.path:
            _sys.path.insert(0, _ASSIGN_PL_DIR)
        import assign_youtube_playlists as _apl

        yt = _apl._get_yt_service()
        playlists = _apl._list_all_playlists(yt)
        cn_name = _apl.MAG_CN.get(magazine, f"《{magazine}》")
        pl_id, pl_name = _apl._find_playlist_id(playlists, cn_name, magazine)

        if not pl_id:
            print(f"    📋 播放列表 '{cn_name}' 不存在，自动新建...")
            pl_id = _apl._create_playlist(yt, cn_name, dry_run=False)
            pl_name = cn_name

        # 检查是否已在列表
        existing = _apl._get_playlist_video_ids(yt, pl_id)
        if yt_video_id in existing:
            print(f"    📋 已在播放列表 '{pl_name}'，跳过")
            return True

        deleted_ids = set()
        ok = _apl._add_to_playlist(yt, pl_id, yt_video_id, dry_run=False,
                                   deleted_ids=deleted_ids)
        if ok:
            print(f"    📋 ✅ 已加入播放列表: {pl_name}")
        else:
            print(f"    📋 ⚠️  加入播放列表失败: {pl_name}")
        return ok
    except Exception as e:
        print(f"    📋 ⚠️  加入播放列表时异常（非致命）: {e}")
        return False

MAG_DATE_TAG_RE = re.compile(r'\[magazine:([^\]]+)\]\s*\[date:(\d{8})\]')

def get_yt_uploads(token):
    """
    从 YouTube 获取已上传视频的去重索引，返回三个集合：
      yt_drive_ids  — description 中嵌入的 Drive File ID（精确唯一 key）
      yt_mag_dates  — (magazine_lower, YYYYMMDD) 元组集合（防同期重复上传）
      today_count   — 今日已上传数量
    """
    headers = {'Authorization': f'Bearer {token}'}
    r = req_lib.get('https://www.googleapis.com/youtube/v3/channels?part=contentDetails&mine=True',
                    headers=headers, timeout=10)
    quota_consume('channels.list', 1)   # 1 unit
    if r.status_code != 200:
        return set(), set(), set(), 0
    uploads_id = r.json()['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    today = datetime.now().strftime('%Y-%m-%d')
    yt_drive_ids, yt_mag_dates, yt_ids, today_count = set(), set(), set(), 0
    next_page = None
    while True:
        params = {'part': 'snippet', 'playlistId': uploads_id, 'maxResults': 50}
        if next_page: params['pageToken'] = next_page
        r = req_lib.get('https://www.googleapis.com/youtube/v3/playlistItems',
                        headers=headers, params=params, timeout=10)
        quota_consume('playlistItems.list', 1)   # 1 unit/页
        if r.status_code != 200: break
        data = r.json()
        for item in data.get('items', []):
            vid = item['snippet']['resourceId']['videoId']
            yt_ids.add(vid)
            desc = item['snippet'].get('description', '')
            # 提取 Drive ID 标签
            m = DRIVE_ID_TAG_RE.search(desc)
            if m:
                yt_drive_ids.add(m.group(1))
            # 提取 magazine+date 标签（防同期不同Drive ID重复上传）
            m2 = MAG_DATE_TAG_RE.search(desc)
            if m2:
                yt_mag_dates.add((m2.group(1).lower(), m2.group(2)))
            if item['snippet']['publishedAt'][:10] == today:
                today_count += 1
        next_page = data.get('nextPageToken')
        if not next_page: break
    print(f"   YouTube drive_id 索引: {len(yt_drive_ids)} 条，mag+date 索引: {len(yt_mag_dates)} 条")
    return yt_drive_ids, yt_mag_dates, yt_ids, today_count

def extract_date_from_name(name):
    """
    从文件名提取 YYYYMMDD。
    支持以下格式：
      YYYYMMDD          → 20260228
      YYYY_MM_DD        → 20260228
      YYYY-MM-DD        → 20260228
      YYYYMM&MM         → 20260101（合刊，取第一个月的第1天）
      YYYYMM+MM         → 20260101（同上）
      YYYYMM            → 20260101（月刊，6位，取第1天）
    """
    # 合刊格式：YYYYMM&MM 或 YYYYMM+MM（如 202601&02, 202501&02）
    m = re.search(r'(20\d{2})(\d{2})[&+](\d{2})', name)
    if m:
        return f"{m.group(1)}{m.group(2)}01"
    # 标准格式：YYYY[-_]?MM[-_]?DD（8位或分隔符分开）
    m = re.search(r'(\d{4})[_-]?(\d{2})[_-]?(\d{2})', name)
    if m:
        return m.group(1) + m.group(2) + m.group(3)
    # 月刊格式：YYYYMM（6位，如 202601）→ 取第1天
    m = re.search(r'(?<!\d)(20\d{2})(0[1-9]|1[0-2])(?!\d)', name)
    if m:
        return f"{m.group(1)}{m.group(2)}01"
    return None

def slugify(name):
    """
    文件名转为 slug。
    处理合刊命名（如 Harvard Business Review_202601&02.mp3）：
      1. 先去掉音频扩展名（避免 mp3 出现在 slug 中）
      2. & 替换为 _and_（保留合刊语义，后面统一 re.sub 清理）
    """
    # 去掉音频/视频扩展名
    name = re.sub(r'\.(mp3|mp4|wav|m4a|aac|flac|ogg)$', '', name, flags=re.IGNORECASE)
    # 合刊 & / + → _and_
    name = name.replace('&', '_and_').replace('+', '_and_')
    s = name.lower().replace("'", "").replace(" ", "_").replace("-", "_")
    s = re.sub(r'[^a-z0-9_]', '', s)
    s = s.replace('barron_s_', 'barrons_').replace('wallstreet_journal_', 'wsj_')
    s = s.replace('foreign_affairs_', 'fa_').replace('national_geographic_', 'natgeo_')
    s = re.sub(r'_+', '_', s).strip('_')
    return s

def scan_drive():
    """扫描 Drive，返回 {file_id: {name, mag, year}}"""
    creds = service_account.Credentials.from_service_account_file(
        SA_PATH, scopes=['https://www.googleapis.com/auth/drive'])
    drive = build('drive', 'v3', credentials=creds, cache_discovery=False)
    # 设置 socket/HTTP 超时
    import socket
    socket.setdefaulttimeout(60)
    import httplib2
    drive._http.timeout = 60
    
    # 找根文件夹（带重试）
    import time
    for attempt in range(3):
        try:
            root = drive.files().list(q="name='Globalmagzineyoutube'", fields='files(id)').execute()
            break
        except (TimeoutError, socket.timeout, httplib2.ServerNotFoundError) as e:
            if attempt == 2:
                raise
            print(f"  ⚠️ Drive API timeout (attempt {attempt+1}/3), retrying in {2**attempt}s...")
            time.sleep(2 ** attempt)
    if not root.get('files'):
        print("❌ Globalmagzineyoutube folder not found")
        return {}, None
    ROOT_ID = root['files'][0]['id']
    print(f"  Root: {ROOT_ID}")
    
    # 扫描所有杂志
    all_audio = {}
    mags = list_all(drive, f"'{ROOT_ID}' in parents and mimeType='application/vnd.google-apps.folder'")
    for mf in mags:
        for yf in list_all(drive, f"'{mf['id']}' in parents and mimeType='application/vnd.google-apps.folder'"):
            audio_dirs = list_all(drive, f"name='audio' and '{yf['id']}' in parents and mimeType='application/vnd.google-apps.folder'")
            for ad in audio_dirs:
                for ff in list_all(drive, f"'{ad['id']}' in parents and mimeType contains 'audio'"):
                    if ff['id'] not in all_audio:
                        all_audio[ff['id']] = {
                            'name': ff['name'], 'magazine': mf['name'],
                            'year': yf['name'], 'file_id': ff['id'],
                            'size': int(ff.get('size', 0)),
                        }
    return all_audio, drive

# 标记为"中途失败，需要重试"的状态词（不含 YouTube URL）
_FAILED_STATUSES = {
    'PENDING_UPLOAD',
    'RENDERED_QUOTA_EXCEEDED',
    'TRANSCRIBED_BLOCKS_READY_QUOTA_EXCEEDED',
    'UPLOAD_TIMEOUT',
    'UPLOAD_FAILED',
    'UPLOAD_COMPLETED_NO_URL',
    'NEEDS_REUPLOAD',           # fix_no_url.py 标记：YouTube 上未找到，需重新上传
    'NO_VIDEO',
}


def reconcile(all_audio, yt_drive_ids, yt_mag_dates):
    """
    三层精确去重，无模糊匹配：
      L1. Drive ID 在 processed.txt 且状态为 YouTube URL → 已上传，跳过
          状态为失败词（RENDERED_QUOTA_EXCEEDED 等）→ 视为未完成，重新处理
      L2. Drive ID 在 YouTube description 标签中 → 已上传（补录 processed.txt）
      L3. (magazine, date) 在 YouTube description 标签中 → 同期不同Drive文件已上传
    全部未命中 → 真正需要处理的新文件
    """
    # 读取 processed.txt — 只有包含 YouTube URL 的行才算"真正完成"
    processed_ids = set()   # 已上传到 YouTube 的 drive_id
    retry_ids     = set()   # 有失败状态记录、需要重新处理的 drive_id
    try:
        with open(PROCESSED) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'): continue
                parts = line.split(',', 3)
                if len(parts) < 2: continue
                pid    = parts[0].strip()
                status = parts[3].strip() if len(parts) > 3 else ''
                if not pid: continue
                if 'youtube.com/watch?v=' in status:
                    # 真正上传成功
                    processed_ids.add(pid)
                elif status in ('SAME_ISSUE_ALREADY_ON_YT', 'RECOVERED_FROM_YT'):
                    # 其他合法的"已处理"状态
                    processed_ids.add(pid)
                elif any(status.startswith(s) for s in _FAILED_STATUSES):
                    # 中途失败 → 需要重试（不加入 processed_ids）
                    retry_ids.add(pid)
                    print(f"   ♻️  重试队列: {parts[1].strip()} [{status[:40]}]")
    except FileNotFoundError:
        pass

    new_files = []
    for fid, info in sorted(all_audio.items()):
        mag = info['magazine']
        dt = extract_date_from_name(info['name'])  # YYYYMMDD or None

        # L1: processed.txt 精确匹配
        if fid in processed_ids:
            continue

        # L2: YouTube description 中有此 Drive ID（处理过但 processed.txt 漏记）
        if fid in yt_drive_ids:
            # 补录到 processed.txt，保持一致
            entry = f"{fid},{info['name']},{datetime.now().strftime('%Y-%m-%d')},RECOVERED_FROM_YT\n"
            with open(PROCESSED, 'a') as pf:
                pf.write(entry)
            print(f"   ↩️ L2 补录: {info['name']} (drive_id 已在YouTube)")
            continue

        # L3: 同杂志+同日期已在YouTube（不同Drive ID的同期文件）
        if dt and (mag.lower(), dt) in yt_mag_dates:
            entry = f"{fid},{info['name']},{datetime.now().strftime('%Y-%m-%d')},SAME_ISSUE_ALREADY_ON_YT\n"
            with open(PROCESSED, 'a') as pf:
                pf.write(entry)
            print(f"   ↩️ L3 同期已存在: {mag} {dt}，跳过 {info['name']}")
            continue

        new_files.append(info)
    return new_files

def download_audio(drive, file_id, out_path):
    """
    从 Drive 下载音频文件。
    对 socket 耗尽（Errno 49）/ 网络临时错误最多重试 3 次，每次等待递增。
    """
    import io as _io, time as _time
    from googleapiclient.http import MediaIoBaseDownload

    _SOCKET_ERRS = ('errno 49', "can't assign", 'eaddrnotavail',
                    'connectionerror', 'connection reset', 'broken pipe',
                    'timeout', 'read timeout', 'connect timeout',
                    'remotedisconnected', 'temporarily unavailable')

    for attempt in range(1, 4):
        try:
            if attempt > 1:
                print(f"    下载中 (第{attempt}次重试)...")
            else:
                print(f"    下载中...")
            request = drive.files().get_media(fileId=file_id)
            fh = _io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            with open(out_path, 'wb') as f:
                f.write(fh.getvalue())
            size_mb = os.path.getsize(out_path) / 1024 / 1024
            print(f"    ✅ 下载完成 ({size_mb:.0f} MB)")
            return
        except Exception as e:
            err_low = str(e).lower()
            is_socket_err = any(k in err_low for k in _SOCKET_ERRS)
            if is_socket_err and attempt < 3:
                wait = 30 * attempt  # 30s → 60s
                print(f"    ⚠️ 网络/socket 错误，等 {wait}s 后重试 ({str(e)[:80]})")
                _time.sleep(wait)
            else:
                raise  # 非 socket 错误或已重试 3 次 → 向上抛出

def transcribe(audio_path, slug):
    """Whisper 转录"""
    out_path = f"/tmp/{slug}_transcript.txt"
    if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
        print(f"    ℹ️ 已有转录文件，跳过")
        return out_path
    print(f"    转录中（Whisper small, language=zh）...")
    import whisper
    model = whisper.load_model('small')
    result = model.transcribe(audio_path, language='zh')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(result['text'])
    print(f"    ✅ 转录完成 ({len(result['text'])} chars)")
    return out_path

# ── DeepSeek API（已验证可用，来自 generate_blocks.py）────────────────────
DEEPSEEK_API_KEY = "YOUR_DEEPSEEK_API_KEY"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"


def _gen_chapter_keywords(blocks):
    """用一次 DeepSeek 调用，把章节主题转成4-8字的生动文学意象短语（如"被折断的魔法棒"）"""
    api_key = os.environ.get('DEEPSEEK_API_KEY', DEEPSEEK_API_KEY)
    if not api_key or not blocks:
        return []
    topics = "\n".join(
        f"{i+1}. {b.get('title','')}：{(b.get('argument') or b.get('summary',''))[:80]}"
        for i, b in enumerate(blocks[:6])
    )
    prompt = (
        f"以下是杂志音频的{min(len(blocks),6)}个章节主题：\n{topics}\n\n"
        '请为每个章节生成一个4-8个汉字的生动文学意象短语'
        '（如「被折断的魔法棒」、「戴尔的葬礼氛围」、「AI幽灵的真相」），'
        '要有画面感和冲击力，不要平铺直叙。'
        '只输出短语，用、隔开，最多5个，不要序号，不要解释：'
    )
    try:
        r = req_lib.post(
            DEEPSEEK_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "deepseek-chat",
                  "messages": [{"role": "user", "content": prompt}],
                  "max_tokens": 120, "temperature": 0.7},
            timeout=40)
        if r.status_code == 200:
            text = r.json()["choices"][0]["message"]["content"].strip()
            kws = [k.strip() for k in re.split(r'[、,，\n]', text) if k.strip()]
            print(f"    ✅ 章节关键词: {kws[:5]}")
            return kws[:5]
        else:
            print(f"    ⚠️ 章节关键词 API 失败: {r.status_code}")
    except Exception as e:
        print(f"    ⚠️ 章节关键词生成失败: {e}")
    return []


def _summarize_blocks_for_desc(blocks):
    """
    返回每个 block 的简短 AI 摘要（一句话）。
    优先使用 block 已有的 argument 字段（已是 AI 生成的核心论点），
    fallback 到 summary 前80字。
    不产生额外 API 调用——blocks 生成时已经 AI 摘要过了。
    """
    result = []
    for b in blocks:
        arg = (b.get('argument') or b.get('summary') or '').strip()
        if len(arg) > 80:
            arg = arg[:80] + '…'
        result.append(arg)
    return result


def _generate_blocks_with_ai(transcript, duration, magazine, date_str):
    """调用 DeepSeek API 生成高质量 v5 blocks（来自经过验证的 generate_blocks.py 流程）"""
    api_key = os.environ.get('DEEPSEEK_API_KEY', DEEPSEEK_API_KEY)
    if not api_key:
        print("    ⚠️ DEEPSEEK_API_KEY 未配置，跳过 AI blocks")
        return None

    mins = duration // 60
    secs = duration % 60
    duration_str = f"{mins:02d}:{secs:02d}"

    system_prompt = f"""你是一位专业的播客内容分析师。请根据以下《{magazine}》{date_str}期中文播客的完整转录文本，生成v5 blocks JSON。

要求：
1. 将 {duration} 秒（00:00至{duration_str}）的内容划分为约8-10个逻辑块
2. 每个块包含：title（中文标题）、argument（核心论点）、start_time/end_time（HH:MM:SS格式）、summary（≥200中文字符的详细总结）、keywords（5个关键词）、visual_prompt（英文图像提示词）
3. visual_prompt要充分多样化 - 每块使用不同的构图和色调
   - 构图混合：wide establishing shot / close-up macro / overhead bird's-eye / split-frame dual exposure / low-angle heroic / Dutch angle unsettling / intimate portrait
   - 色调混合：cool blue-teal / warm amber-gold / desaturated noir / vibrant neon / muted earth tones / high-contrast monochrome
   - 每张visual_prompt末尾必须追加"ARRI ALEXA 65, anamorphic lens, cinematic lighting, 8K"作为后缀
   - 每张visual_prompt末尾必须追加"NO TEXT, no title, no on-screen text, no subtitles"作为最终保护语
4. 中文关键词（5个/块）
5. summary必须≥200中文字符，包含具体数据、人名、地名、论据
6. 严格输出纯JSON，不要任何其他文字

总时长：{duration}秒 = {duration_str}

请严格按以下JSON格式输出（只输出JSON，不要markdown代码块标记）：

{{"core_topic": "...", "blocks": [{{"title":"...","argument":"...","start_time":"HH:MM:SS","end_time":"HH:MM:SS","summary":"≥200 Chinese chars","keywords":["kw1","kw2","kw3","kw4","kw5"],"visual_prompt":"... ARRI ALEXA 65, anamorphic lens, cinematic lighting, 8K. NO TEXT, no title, no on-screen text, no subtitles"}}]}}"""

    # 完整转录发给 DeepSeek（不截断，P0 fix）
    # DeepSeek 支持 64K 上下文，不需要截断
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcript}
        ],
        "temperature": 0.3,
        "max_tokens": 8000
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        resp = req_lib.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=120)
        print(f"    DeepSeek API 状态: {resp.status_code}")
        if resp.status_code != 200:
            print(f"    ⚠️ DeepSeek API 失败: {resp.text[:300]}")
            return None
        content = resp.json()["choices"][0]["message"]["content"]
        # 提取 JSON（可能被 markdown 代码块包裹）
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"): content = content[4:]
            content = content.strip()
        data = json.loads(content)
        blocks_raw = data.get("blocks", [])
        core_topic = data.get("core_topic", "")
        print(f"    ✅ DeepSeek API 返回 {len(blocks_raw)} blocks，core_topic='{core_topic}'")
        return core_topic, blocks_raw
    except Exception as e:
        print(f"    ⚠️ DeepSeek API 异常: {e}")
        return None


def generate_blocks(transcript_path, audio_path, slug, magazine="", date_str=""):
    """生成 block JSON（AI 优先，降级到简单分块）"""
    out_path = f"/tmp/{slug}_blocks.json"
    if os.path.exists(out_path) and os.path.getsize(out_path) > 500:
        # 检测是否是旧的占位符 blocks
        try:
            with open(out_path) as f:
                existing = json.load(f)
            first_title = existing.get('blocks', [{}])[0].get('title', '') if existing.get('blocks') else ''
            _is_placeholder = (
                re.match(r'^(段|第)\s*\d', first_title) or
                re.match(r'^话题\s*\d', first_title) or
                first_title in ('', '话题', 'topic')
            )
            if existing.get('blocks') and _is_placeholder:
                print(f"    ⚠️ 发现占位符 blocks（标题='{first_title}'），重新生成...")
                os.remove(out_path)
            else:
                print(f"    ℹ️ 已有 blocks JSON，跳过")
                return out_path
        except:
            pass

    print(f"    生成 blocks JSON（AI 分析）...")
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                        '-of', 'json', audio_path], capture_output=True, text=True, timeout=30)
    duration = int(float(json.loads(r.stdout)['format']['duration']))

    with open(transcript_path) as f:
        text = f.read()

    core_topic = ""
    blocks = None

    # 尝试 AI 生成（DeepSeek API）
    ai_result = _generate_blocks_with_ai(text, duration, magazine, date_str)
    if ai_result:
        core_topic, blocks_raw = ai_result
        blocks = []
        n = len(blocks_raw)
        for i, b in enumerate(blocks_raw):
            # DeepSeek 返回 HH:MM:SS 格式；兼容旧的 start_pct/end_pct
            if b.get("start_time") and b.get("end_time"):
                st = b["start_time"]
                et = b["end_time"]
            else:
                sp = b.get("start_pct", i / n)
                ep = b.get("end_pct", (i + 1) / n)
                ss = int(duration * sp); se = int(duration * ep)
                st = f"{ss//3600:02d}:{(ss%3600)//60:02d}:{ss%60:02d}"
                et = f"{se//3600:02d}:{(se%3600)//60:02d}:{se%60:02d}"
            blocks.append({
                'title': b.get('title', f'段{i+1}'),
                'argument': b.get('argument', ''),
                'summary': b.get('summary', ''),
                'keywords': b.get('keywords', []),
                'start_time': st,
                'end_time': et,
                'visual_prompt': b.get('visual_prompt', ''),
            })

    # 降级：简单均匀分块
    if not blocks:
        print(f"    ℹ️ 使用简单分块（AI 不可用）...")
        n_blocks = min(7, max(5, duration // 180))
        chars = len(text)
        block_size = chars // n_blocks
        # 从杂志名生成有意义的默认 visual_prompt
        mag_prompts = {
            "Economist": "Global political scene at dusk, dramatic blue lighting, world map perspective, chiaroscuro",
            "Wallstreet Journal": "Financial district canyon at golden hour, amber and deep blue contrast, cinematic",
            "New Yorker": "Elegant urban cultural scene, warm gallery light, sophisticated amber tones",
            "Barron's": "Abstract wealth visualization, golden investment charts, deep navy background",
            "Science": "Bioluminescent laboratory scene, teal and gold DNA structures, scientific precision",
            "Bloomberg": "Global economy visualization, warm amber data streams, minimalist editorial",
        }
        default_vp = mag_prompts.get(magazine, "Dramatic cinematic scene, deep contrast lighting, rich amber and blue palette")
        blocks = []
        for i in range(n_blocks):
            ss = i * (duration // n_blocks); se = (i+1) * (duration // n_blocks)
            blocks.append({
                'title': f"第{i+1}章", 'argument': '',
                'start_time': f"{ss//60:02d}:{ss%60:02d}:00",
                'end_time': f"{se//60:02d}:{se%60:02d}:00",
                'summary': text[i*(chars//n_blocks):(i+1)*(chars//n_blocks)].strip()[:200],
                'keywords': [], 'visual_prompt': default_vp,
            })

    result = {'core_topic': core_topic or magazine, 'transcript': text, 'blocks': blocks}
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"    ✅ Blocks JSON 已生成 ({len(blocks)} blocks, {duration}s，转录 {len(text)} 字)")
    return out_path

MAG_CN_MAP = {
    "Economist": "经济学人", "Wallstreet Journal": "华尔街日报",
    "Barron's": "巴伦周刊", "Barrons": "巴伦周刊",
    "New Yorker": "纽约客", "Bloomberg": "彭博商业周刊",
    "Science": "科学", "New Scientist": "新科学家",
    "Foreign Affairs": "外交事务", "The Atlantic": "大西洋月刊",
    "Times": "泰晤士报", "Harvard Business Review": "哈佛商业评论",
    "National Geographic": "国家地理",
    "National Geographic Traveller": "国家地理旅行者",
    "National Geographic History": "国家地理历史",
}


def process_one_file(info, drive, existing_run_state=None, backfill_mode=False):
    """
    处理单个音频文件的完整六步流水线。

    断点续传逻辑：
      - existing_run_state != None → 上次中断，从上次失败步骤继续
      - 每步完成后立即写 active_runs.json（防止意外崩溃丢失进度）
      - /tmp 文件丢失时，优先从 Drive 素材目录恢复，避免重头来
      - YouTube quota 超限时返回 'quota_exceeded'，不 crash，进度保留

    返回值：
      'ok'             — 全部完成
      'quota_exceeded' — upload 因 quota 停止，其余步骤均已保存
      'failed'         — 不可恢复的失败（下载失败、渲染失败等）
    """
    fname = info['name']
    mag   = info['magazine']
    fid   = info['file_id']
    dt    = extract_date_from_name(fname) or 'unknown'
    slug  = slugify(fname.replace('.mp3', ''))

    # ── 最顶层去重：processed.txt 中若已有 YouTube URL，立即跳过 ──────────────
    # backfill_mode=True 时跳过此检查：backfill 的目的是补 Drive 素材，
    # 文件必然已在 processed.txt，步骤 7 内部会自动跳过 YouTube 重传。
    if not backfill_mode:
        try:
            with open(PROCESSED, encoding='utf-8', errors='replace') as _pf_top:
                for _pl_top in _pf_top:
                    _p_top = _pl_top.strip().split(',', 3)
                    if len(_p_top) >= 4 and _p_top[0].strip() == fid:
                        _st = _p_top[3].strip()
                        if 'youtube.com' in _st or 'youtu.be' in _st:
                            _url = _st.split()[0]
                            print(f"\n⏭️  [跳过] {fname} — processed.txt 已有 YT URL: {_url}")
                            return 'ok'
        except FileNotFoundError:
            pass   # processed.txt 不存在，正常继续
        except Exception as _e_top:
            print(f"    ⚠️  processed.txt 预检查异常（继续处理）: {_e_top}")

    # ── 初始化 / 恢复 run_state ────────────────────────────
    if existing_run_state:
        run = existing_run_state
        print(f"\n♻️  断点续传: {fname} [{mag}]")
        _print_run_status(run)
    else:
        run = {
            'audio_drive_id': fid,
            'audio_filename':  fname,
            'magazine':        mag,
            'date':            dt,
            'slug':            slug,
            'year':            info.get('year', dt[:4] if len(dt) >= 4 else '2026'),
            'started_at':      _now(),
            'last_updated':    _now(),
            'steps':           {},
            'drive_assets':    {},
            'yt_url':          '',
            'yt_title':        '',
        }
        save_active_run(run)
        print(f"\n📄 新任务: {fname} [{mag}]")

    # ── 本地路径（确定性，基于 slug）──────────────────────
    audio_path      = f"/tmp/{slug}.mp3"
    transcript_path = f"/tmp/{slug}_transcript.txt"
    blocks_path_tmp = f"/tmp/{slug}_blocks.json"
    img_dir         = f"/tmp/{slug}_images"
    final_mp4       = f"/tmp/{mag}_{dt}_final.mp4"

    # ═══════════════════════════════════════════════════════
    #  步骤 1: 下载
    # ═══════════════════════════════════════════════════════
    if _step_ok(run, 'download'):
        print(f"    ✅ [跳过] download — 已完成")
        # /tmp 可能被清：恢复音频
        if not (os.path.exists(audio_path) and os.path.getsize(audio_path) > 100000):
            print(f"    ♻️  /tmp 音频丢失，重新下载...")
            try:
                download_audio(drive, fid, audio_path)
            except Exception as e:
                print(f"    ❌ 重新下载失败: {e}")
                _notify_step_failure(run, 'download', str(e))
                return 'failed'
    else:
        # 本地残留可直接用
        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 100000:
            print(f"    ℹ️ 本地已有音频，直接使用")
            _mark_step(run, 'download', local_path=audio_path)
        else:
            try:
                download_audio(drive, fid, audio_path)
                _mark_step(run, 'download', local_path=audio_path,
                           size_mb=os.path.getsize(audio_path)//(1024*1024))
            except Exception as e:
                _mark_step_failed(run, 'download', error=str(e))
                print(f"    ❌ 下载失败，停止: {e}")
                _notify_step_failure(run, 'download', str(e))
                return 'failed'

        # ── QC: 下载质检 ──────────────────────────────────────
        print(f"    🔍 QC [download] 质检中...")
        qc_ok, qc_detail = _qc_download(run, audio_path)
        if not qc_ok:
            _mark_step_failed(run, 'download', error=f"QC: {qc_detail}")
            print(f"    ❌ QC [download] 失败: {qc_detail}")
            _notify_step_failure(run, 'download', f"QC失败: {qc_detail}")
            return 'failed'
        print(f"    ✅ QC [download]: {qc_detail}")

    # ═══════════════════════════════════════════════════════
    #  步骤 2: 转录
    # ═══════════════════════════════════════════════════════
    transcript_chars = run['steps'].get('transcribe', {}).get('chars', 0)

    if _step_ok(run, 'transcribe'):
        print(f"    ✅ [跳过] transcribe — 已完成 ({transcript_chars} 字)")
        # 转录文件丢失则重建（Whisper 比较快，不单独存 Drive）
        if not (os.path.exists(transcript_path) and os.path.getsize(transcript_path) > 100):
            print(f"    ♻️  转录文件丢失，重新转录...")
            try:
                transcribe(audio_path, slug)
            except Exception as e:
                print(f"    ⚠️ 重新转录失败: {e}（继续尝试后续步骤）")
    else:
        try:
            tp = transcribe(audio_path, slug)
            with open(tp, encoding='utf-8') as tf:
                transcript_chars = len(tf.read())
            _mark_step(run, 'transcribe', local_path=tp, chars=transcript_chars)
        except Exception as e:
            _mark_step_failed(run, 'transcribe', error=str(e))
            print(f"    ❌ 转录失败: {e}")
            return 'failed'

        # ── QC: 转录质检 ──────────────────────────────────────
        print(f"    🔍 QC [transcribe] 质检中...")
        qc_ok, qc_detail = _qc_transcribe(run, transcript_path)
        if not qc_ok:
            _mark_step_failed(run, 'transcribe', error=f"QC: {qc_detail}")
            print(f"    ❌ QC [transcribe] 失败: {qc_detail}")
            _notify_step_failure(run, 'transcribe', f"QC失败: {qc_detail}")
            return 'failed'
        print(f"    ✅ QC [transcribe]: {qc_detail}")

    # ═══════════════════════════════════════════════════════
    #  步骤 3: 生成 blocks
    # ═══════════════════════════════════════════════════════
    blocks_data  = {'core_topic': '', 'blocks': []}
    blocks_path  = blocks_path_tmp

    # ── blocks 步骤：统一加载 + 强制 QC + 自动重新生成 ──────────────
    # 无论来自缓存/Drive恢复/新生成，都必须通过 QC，否则强制重新生成
    _blocks_loaded = False
    if _step_ok(run, 'blocks'):
        count = run['steps']['blocks'].get('count', 0)
        print(f"    ✅ [跳过] blocks — 已完成 ({count} blocks)")
        bid = run.get('drive_assets', {}).get('blocks_json_id', '')
        if not recover_artifact(blocks_path_tmp, drive, bid, 'blocks JSON'):
            print(f"    ♻️  blocks 文件不可恢复，重新生成...")
            try:
                blocks_path = generate_blocks(transcript_path, audio_path, slug, magazine=mag, date_str=dt)
            except Exception as e:
                print(f"    ⚠️ blocks 重生成失败: {e}")
        try:
            with open(blocks_path, encoding='utf-8') as bf:
                blocks_data = json.load(bf)
            _blocks_loaded = True
        except Exception:
            pass
    else:
        # 尝试从 Drive 恢复（第二次及以后运行，Drive 资产可能已上传）
        bid = run.get('drive_assets', {}).get('blocks_json_id', '')
        recovered = recover_artifact(blocks_path_tmp, drive, bid, 'blocks JSON')
        if recovered:
            try:
                with open(blocks_path_tmp, encoding='utf-8') as bf:
                    blocks_data = json.load(bf)
                _mark_step(run, 'blocks', local_path=blocks_path_tmp,
                           count=len(blocks_data.get('blocks', [])),
                           core_topic=blocks_data.get('core_topic', ''),
                           source='drive_recovered')
                _blocks_loaded = True
            except Exception:
                recovered = False

        if not recovered:
            try:
                blocks_path = generate_blocks(transcript_path, audio_path, slug, magazine=mag, date_str=dt)
                with open(blocks_path, encoding='utf-8') as bf:
                    blocks_data = json.load(bf)
                _mark_step(run, 'blocks', local_path=blocks_path,
                           count=len(blocks_data.get('blocks', [])),
                           core_topic=blocks_data.get('core_topic', ''))
                _blocks_loaded = True
            except Exception as e:
                _mark_step_failed(run, 'blocks', error=str(e))
                print(f"    ❌ Blocks 生成失败: {e}")
                _notify_step_failure(run, 'blocks', str(e))
                return 'failed'

    # ── QC: blocks 质检（始终运行，无论来源）────────────────────────
    print(f"    🔍 QC [blocks] 质检中...")
    qc_ok, qc_detail = _qc_blocks(run, blocks_path)
    if not qc_ok:
        # 缓存/Drive恢复文件可能是旧占位符 → 删缓存，强制重新生成一次
        print(f"    ⚠️ QC [blocks] 失败({qc_detail})，删缓存 → 强制重新生成...")
        if os.path.exists(blocks_path):
            os.remove(blocks_path)
        run['steps'].pop('blocks', None)   # 清除完成状态
        save_active_run(run)
        try:
            blocks_path = generate_blocks(transcript_path, audio_path, slug, magazine=mag, date_str=dt)
            with open(blocks_path, encoding='utf-8') as bf:
                blocks_data = json.load(bf)
            _mark_step(run, 'blocks', local_path=blocks_path,
                       count=len(blocks_data.get('blocks', [])),
                       core_topic=blocks_data.get('core_topic', ''),
                       source='regenerated_after_qc_fail')
            qc_ok, qc_detail = _qc_blocks(run, blocks_path)
        except Exception as e:
            qc_ok, qc_detail = False, str(e)
    if not qc_ok:
        _mark_step_failed(run, 'blocks', error=f"QC: {qc_detail}")
        print(f"    ❌ QC [blocks] 最终失败: {qc_detail}")
        _notify_step_failure(run, 'blocks', f"QC失败: {qc_detail}")
        return 'failed'
    print(f"    ✅ QC [blocks]: {qc_detail}")

    # ═══════════════════════════════════════════════════════
    #  步骤 4: 生成图片
    # ═══════════════════════════════════════════════════════
    os.makedirs(img_dir, exist_ok=True)

    if _step_ok(run, 'images'):
        expected = run['steps']['images'].get('count', 1)
        n_local  = len([f for f in os.listdir(img_dir) if f.endswith('.png')]) if os.path.isdir(img_dir) else 0
        print(f"    ✅ [跳过] images — 已完成 ({expected} 张)")
        # 图片不足时从 Drive 恢复
        if n_local < expected:
            print(f"    ♻️  本地图片不完整 ({n_local}/{expected})，从 Drive 恢复...")
            da = run.get('drive_assets', {})
            for item in da.get('block_image_ids', []):
                lp = os.path.join(img_dir, item['filename'])
                recover_artifact(lp, drive, item['drive_id'], item['filename'])
            if da.get('cover_id'):
                recover_artifact(os.path.join(img_dir, 'cover.png'),
                                 drive, da['cover_id'], 'cover.png')
            if da.get('thumbnail_id'):
                recover_artifact(os.path.join(img_dir, 'thumbnail.jpg'),
                                 drive, da['thumbnail_id'], 'thumbnail.jpg')
    else:
        style      = 'notebooklm' if mag in NOTEBOOKLM_MAGS else 'dark'
        gen_script = GEN_IMAGES_DARK if style == 'dark' else GEN_IMAGES_NOTEBOOKLM
        date_only  = extract_date_from_name(fname) or dt

        if not os.path.exists(gen_script):
            _mark_step_failed(run, 'images', error=f'script not found: {gen_script}')
            print(f"    ❌ 图片脚本不存在: {gen_script}")
            # 图片失败不中断——用空帧渲染也好过丢失这期
        else:
            # ── 注入 overall_summary（供封面底部文字用）─────────────────────
            try:
                with open(blocks_path, encoding='utf-8') as _bf:
                    _bdata = json.load(_bf)
                if not _bdata.get('overall_summary'):
                    _blks = _bdata.get('blocks', [])
                    _snippets = "\n".join(
                        f"第{i+1}节：{(b.get('argument') or b.get('summary',''))[:200]}"
                        for i, b in enumerate(_blks)
                    )
                    _prompt = (
                        f"以下是一期英文杂志播客共{len(_blks)}节的中文摘录，"
                        "请用一句话（不超过40字）高度概括本期核心主题，直接输出：\n\n"
                        + _snippets
                    )
                    _api_key = os.environ.get('DEEPSEEK_API_KEY', DEEPSEEK_API_KEY)
                    try:
                        import requests as _req
                        _r = _req.post(
                            DEEPSEEK_API_URL,
                            headers={"Authorization": f"Bearer {_api_key}",
                                     "Content-Type": "application/json"},
                            json={"model": "deepseek-chat",
                                  "messages": [{"role": "user", "content": _prompt}],
                                  "max_tokens": 80, "temperature": 0.3},
                            timeout=60)
                        if _r.status_code == 200:
                            _summary = _r.json()["choices"][0]["message"]["content"].strip()
                            _bdata['overall_summary'] = _summary
                            with open(blocks_path, 'w', encoding='utf-8') as _bf2:
                                json.dump(_bdata, _bf2, ensure_ascii=False)
                            print(f"    ✅ overall_summary 注入: {_summary[:40]}")
                    except Exception as _se:
                        print(f"    ⚠️  overall_summary 生成失败（不中断）: {_se}")
            except Exception as _be:
                print(f"    ⚠️  blocks 注入跳过: {_be}")

            # ── 封面背景缓存路径 ─────────────────────────────────────────────
            _imagen_cache = os.path.expanduser("~/hermesagent/Youtube video/imagen_cache")
            os.makedirs(_imagen_cache, exist_ok=True)
            import re as _re
            _safe_mag  = _re.sub(r"[^\w]", "_", mag)
            _bg_cache  = os.path.join(_imagen_cache, f"{_safe_mag}_{date_only}_bg.png")
            _cover_map = os.path.expanduser("~/hermesagent/Youtube video/drive_cover_map.json")

            try:
                _gen_cmd = ['python3', gen_script, blocks_path, img_dir,
                            '--magazine-name', mag, '--date-str', date_only,
                            '--save-bg', _bg_cache,
                            '--cover-map', _cover_map]
                # 如果缓存背景图已存在，直接复用，跳过 Imagen API 调用
                # gen_images.py 用 --bg-img；gen_images_notebooklm.py 通过 --save-bg 自行读取缓存
                if os.path.exists(_bg_cache) and style == 'dark':
                    _gen_cmd += ['--bg-img', _bg_cache]
                    print(f"    ♻️  复用 Imagen 背景缓存: {os.path.basename(_bg_cache)}")
                r = subprocess.run(_gen_cmd, timeout=900, capture_output=True, text=True)
                if r.returncode == 0:
                    n_imgs = len([f for f in os.listdir(img_dir) if f.endswith('.png')])
                    _mark_step(run, 'images', local_dir=img_dir, count=n_imgs)
                    print(f"    ✅ 图片生成完成 ({n_imgs} 张)")

                    # ── 质量门控：封面/缩略图必须 > 50 KB ────────────────────
                    for _qf in ('thumbnail.jpg', 'cover.png'):
                        _qpath = os.path.join(img_dir, _qf)
                        if os.path.exists(_qpath):
                            _qsz = os.path.getsize(_qpath)
                            if _qsz < 50 * 1024:
                                print(f"    ⚠️ 质量警告：{_qf} 只有 {_qsz//1024} KB（< 50 KB），可能是纯色背景")
                            else:
                                print(f"    ✅ 质量检查通过：{_qf} ({_qsz//1024} KB)")

                    # ── 生成 mag_cover.jpg（PDF 封面截图）──────────────────────
                    # 需要 mag_id / year_id，先通过 SA 查找
                    try:
                        from google.oauth2 import service_account as _sa_mod
                        _sa_creds = _sa_mod.Credentials.from_service_account_file(
                            SA_PATH, scopes=['https://www.googleapis.com/auth/drive'])
                        _drive_sa_tmp = build('drive', 'v3', credentials=_sa_creds, cache_discovery=False)
                        _root_r = _drive_sa_tmp.files().list(
                            q="name='Globalmagzineyoutube'", fields='files(id)').execute()
                        _root_id = _root_r['files'][0]['id'] if _root_r.get('files') else ''
                        _mag_r = _drive_sa_tmp.files().list(
                            q=f"name='{_dq(mag)}' and '{_root_id}' in parents "
                              f"and mimeType='application/vnd.google-apps.folder'",
                            fields='files(id)').execute() if _root_id else {'files': []}
                        _mag_id_tmp = _mag_r['files'][0]['id'] if _mag_r.get('files') else ''
                        _yr_id_tmp = ''
                        if _mag_id_tmp:
                            _yr_r = _drive_sa_tmp.files().list(
                                q=f"name='{dt[:4]}' and '{_mag_id_tmp}' in parents "
                                  f"and mimeType='application/vnd.google-apps.folder'",
                                fields='files(id)').execute()
                            _yr_id_tmp = _yr_r['files'][0]['id'] if _yr_r.get('files') else ''
                        if _mag_id_tmp:
                            _gen_mag_cover(_drive_sa_tmp, _mag_id_tmp, _yr_id_tmp, mag, dt, img_dir)
                    except Exception as _mc_e:
                        print(f"    ⚠️ mag_cover 生成跳过: {_mc_e}")
                else:
                    err = (r.stderr or r.stdout)[-300:]
                    _mark_step_failed(run, 'images', error=err)
                    print(f"    ❌ 图片生成失败 (exit={r.returncode})")
                    _notify_step_failure(run, 'images', f"gen_images.py exit={r.returncode}: {err}")
                    return 'failed'
            except subprocess.TimeoutExpired:
                _mark_step_failed(run, 'images', error='timeout 900s')
                print(f"    ❌ 图片生成超时（900s）")
                _notify_step_failure(run, 'images', 'gen_images.py timeout after 900s')
                return 'failed'
            except Exception as e:
                _mark_step_failed(run, 'images', error=str(e))
                print(f"    ❌ 图片生成异常: {e}")
                _notify_step_failure(run, 'images', str(e))
                return 'failed'

        # ── QC: 图片质检（包含 Gemini AI 视觉检查）────────────────
        blocks_count = len(blocks_data.get('blocks', []))
        print(f"    🔍 QC [images] 质检中（含 AI 视觉检查）...")
        qc_ok, qc_detail = _qc_images(run, img_dir, blocks_count)
        if not qc_ok:
            _mark_step_failed(run, 'images', error=f"QC: {qc_detail}")
            print(f"    ❌ QC [images] 失败: {qc_detail}")
            _notify_step_failure(run, 'images', f"QC失败: {qc_detail}")
            return 'failed'
        print(f"    ✅ QC [images]: {qc_detail}")

    # ═══════════════════════════════════════════════════════
    #  步骤 5: 渲染视频
    # ═══════════════════════════════════════════════════════
    if _step_ok(run, 'render'):
        size_mb = run['steps']['render'].get('size_mb', 0)
        print(f"    ✅ [跳过] render — 已完成 ({size_mb} MB)")
        # 视频文件丢失则重渲染
        if not (os.path.exists(final_mp4) and os.path.getsize(final_mp4) > 1000000):
            print(f"    ♻️  /tmp 视频丢失，重新渲染...")
            try:
                # 确保 render_video.py 能找到 blocks JSON（它按 {mag}_{dt} 格式查找）
                render_blocks = f"/tmp/{mag}_{dt}_blocks.json"
                if not os.path.exists(render_blocks) and os.path.exists(blocks_path_tmp):
                    try:
                        os.symlink(blocks_path_tmp, render_blocks)
                    except OSError:
                        import shutil; shutil.copy2(blocks_path_tmp, render_blocks)
                subprocess.run(['python3', RENDER_VIDEO, mag, dt, audio_path, img_dir],
                               timeout=600)
                if not (os.path.exists(final_mp4) and os.path.getsize(final_mp4) > 1000000):
                    print(f"    ❌ 重渲染失败")
                    _notify_step_failure(run, 'render', 'Re-render output missing or too small')
                    return 'failed'
            except Exception as e:
                print(f"    ❌ 重渲染异常: {e}")
                _notify_step_failure(run, 'render', str(e))
                return 'failed'
    else:
        if not os.path.exists(RENDER_VIDEO):
            _mark_step_failed(run, 'render', error='render_video.py not found')
            print(f"    ❌ render_video.py 不存在")
            _notify_step_failure(run, 'render', f'render_video.py not found at {RENDER_VIDEO}')
            return 'failed'
        # 本地残留视频可直接用 —— 但若 blocks 是 QC 失败后重新生成的，
        # 旧视频内容（段1/话题1占位符）已过期，必须强制重渲染。
        _blocks_regenerated = (run.get('steps', {}).get('blocks', {}).get('source')
                               == 'regenerated_after_qc_fail')
        if os.path.exists(final_mp4) and os.path.getsize(final_mp4) > 1000000 and not _blocks_regenerated:
            size_mb = os.path.getsize(final_mp4) // (1024*1024)
            _mark_step(run, 'render', local_path=final_mp4, size_mb=size_mb)
            print(f"    ℹ️ 使用本地残留视频 ({size_mb} MB)")
        elif _blocks_regenerated and os.path.exists(final_mp4):
            print(f"    ℹ️ blocks 已重新生成（旧视频含占位符），强制重渲染...")
            os.remove(final_mp4)  # 删旧视频，走下面的正常渲染分支
        else:
            print(f"    渲染视频中...")
            try:
                # render_video.py 期望: python3 render_video.py <magazine> <date> <audio_path> [image_dir]
                # 输出文件名格式: /tmp/{magazine}_{date}_final.mp4
                # blocks JSON 在 /tmp/{mag}_{dt}_blocks.json — 从 slug 路径建软链接
                render_blocks = f"/tmp/{mag}_{dt}_blocks.json"
                if not os.path.exists(render_blocks) and os.path.exists(blocks_path_tmp):
                    try:
                        os.symlink(blocks_path_tmp, render_blocks)
                    except OSError:
                        import shutil; shutil.copy2(blocks_path_tmp, render_blocks)
                render_args = ['python3', RENDER_VIDEO, mag, dt, audio_path, img_dir]
                result = subprocess.run(render_args, timeout=600)
                if os.path.exists(final_mp4) and os.path.getsize(final_mp4) > 1000000:
                    size_mb = os.path.getsize(final_mp4) // (1024*1024)
                    _mark_step(run, 'render', local_path=final_mp4, size_mb=size_mb)
                    print(f"    ✅ 视频渲染完成 ({size_mb} MB)")
                else:
                    _mark_step_failed(run, 'render', error='output missing or too small')
                    print(f"    ❌ 渲染失败（输出文件不存在或太小）")
                    _notify_step_failure(run, 'render', 'render output missing or too small after render_video.py')
                    return 'failed'
            except subprocess.TimeoutExpired:
                _mark_step_failed(run, 'render', error='timeout 600s')
                print(f"    ❌ 渲染超时")
                _notify_step_failure(run, 'render', 'render_video.py timeout after 600s')
                return 'failed'
            except Exception as e:
                _mark_step_failed(run, 'render', error=str(e))
                print(f"    ❌ 渲染异常: {e}")
                _notify_step_failure(run, 'render', str(e))
                return 'failed'

        # ── QC: 渲染质检 ──────────────────────────────────────
        print(f"    🔍 QC [render] 质检中...")
        qc_ok, qc_detail = _qc_render(run, final_mp4)
        if not qc_ok:
            _mark_step_failed(run, 'render', error=f"QC: {qc_detail}")
            print(f"    ❌ QC [render] 失败: {qc_detail}")
            _notify_step_failure(run, 'render', f"QC失败: {qc_detail}")
            return 'failed'
        print(f"    ✅ QC [render]: {qc_detail}")

    # ═══════════════════════════════════════════════════════
    #  步骤 6: 上传所有素材到 Drive（MP4 + 图片 + blocks JSON）
    #  必须在 YouTube 上传之前完成，这样 quota 耗尽后下次可直接从 Drive 恢复 MP4
    # ═══════════════════════════════════════════════════════
    if _step_ok(run, 'drive_upload'):
        print(f"    ✅ [跳过] drive_upload — 已完成")
        # /tmp MP4 丢失时，从 Drive 恢复（避免重新渲染）
        mp4_drive_id = run.get('drive_assets', {}).get('mp4_drive_id', '')
        if not (os.path.exists(final_mp4) and os.path.getsize(final_mp4) > 1000000):
            if mp4_drive_id:
                print(f"    ♻️  /tmp MP4 丢失，从 Drive 恢复...")
                recover_artifact(final_mp4, drive, mp4_drive_id, f"{slug}_final.mp4")
            else:
                print(f"    ⚠️  MP4 不在 Drive，需要重新渲染")
                _mark_step_failed(run, 'drive_upload', error='mp4_not_on_drive')
                # 降级：重新渲染
                render_blocks = f"/tmp/{mag}_{dt}_blocks.json"
                if not os.path.exists(render_blocks) and os.path.exists(blocks_path_tmp):
                    try: os.symlink(blocks_path_tmp, render_blocks)
                    except OSError: import shutil; shutil.copy2(blocks_path_tmp, render_blocks)
                subprocess.run(['python3', RENDER_VIDEO, mag, dt, audio_path, img_dir], timeout=600)
    else:
        print(f"    📂 上传所有素材到 Drive（MP4 + 图片 + blocks JSON）...")
        drive_assets = upload_assets_to_drive(
            info, img_dir, blocks_path, slug, final_mp4=final_mp4)
        run['drive_assets'] = drive_assets
        if drive_assets.get('folder_id'):
            _n_files = (len(drive_assets.get('block_image_ids', [])) + 3  # cover/thumbnail/blocks
                        + (1 if drive_assets.get('mp4_drive_id') else 0)
                        + (1 if drive_assets.get('mag_cover_id') else 0))
            _mark_step(run, 'drive_upload',
                       folder_id=drive_assets.get('folder_id', ''),
                       folder_name=drive_assets.get('folder_name', ''),
                       mp4_drive_id=drive_assets.get('mp4_drive_id', ''),
                       mag_cover_id=drive_assets.get('mag_cover_id', ''),
                       files_count=_n_files)
        else:
            _mark_step_failed(run, 'drive_upload', error='upload_assets_returned_empty')
            print(f"    ❌ Drive 素材上传失败（upload_assets_to_drive 返回空结果）")
            _notify_step_failure(run, 'drive_upload', 'upload_assets_to_drive returned empty — 检查 OAuth/SA 权限和 Drive 配额')
            return 'drive_partial'

        # ── QC: Drive 上传质检 ────────────────────────────────
        print(f"    🔍 QC [drive_upload] 质检中...")
        qc_ok, qc_detail = _qc_drive_upload(run, drive_assets, mag, dt)
        if not qc_ok:
            _mark_step_failed(run, 'drive_upload', error=f"QC: {qc_detail}")
            print(f"    ❌ QC [drive_upload] 失败: {qc_detail}")
            _notify_step_failure(run, 'drive_upload', f"QC失败: {qc_detail}")
            return 'drive_partial'
        print(f"    ✅ QC [drive_upload]: {qc_detail}")

    # ═══════════════════════════════════════════════════════
    #  步骤 7: 上传 YouTube
    # ═══════════════════════════════════════════════════════
    yt_url   = run.get('yt_url', '')
    yt_title = run.get('yt_title', '')

    # ── 在调用 upload_video.py 之前，先从 processed.txt 查找已有 YT URL ──────
    # backfill 场景：视频已在 YouTube，只是来补 Drive 素材，不需要重复上传
    if not yt_url:
        try:
            with open(PROCESSED, encoding='utf-8', errors='replace') as _pf:
                for _pl in _pf:
                    _parts = _pl.strip().split(',', 3)
                    if len(_parts) >= 4 and _parts[0].strip() == fid:
                        _existing_status = _parts[3].strip()
                        if 'youtube.com' in _existing_status or 'youtu.be' in _existing_status:
                            yt_url = _existing_status.split()[0]  # 取第一个 token（URL）
                            run['yt_url'] = yt_url
                            _mark_step(run, 'upload', yt_url=yt_url, source='recovered_from_processed_txt')
                            print(f"    ✅ [跳过] upload — processed.txt 已有 YT URL: {yt_url}")
                            break
        except FileNotFoundError:
            pass
        except Exception as _e_upload:
            print(f"    ⚠️  upload pre-check 异常: {_e_upload}")

    if _step_ok(run, 'upload') and yt_url:
        print(f"    ✅ [跳过] upload — 已完成: {yt_url}")
    else:
        # 构建标题
        mag_cn = MAG_CN_MAP.get(mag, mag)
        def _fmt_date_cn(s):
            s = str(s).replace("-", "").replace("_", "")
            return f"{s[:4]}年{s[4:6]}月{s[6:8]}日" if len(s) == 8 else s
        # 合刊检测：从原始文件名识别 YYYYMM&MM 或 YYYYMM+MM 格式
        _raw_fname   = info.get('name', '')
        _combined_m  = re.search(r'(20\d{2})(\d{2})[&+](\d{2})', _raw_fname)
        if _combined_m:
            _cy, _cm1, _cm2 = _combined_m.group(1), _combined_m.group(2), _combined_m.group(3)
            date_cn = f"{_cy}年{_cm1}-{_cm2}月合刊"
        elif dt != 'unknown':
            date_cn = _fmt_date_cn(dt)
        else:
            date_cn = ''
        core_topic = blocks_data.get('core_topic', '')
        # 过滤无意义的 core_topic（DeepSeek 有时返回 "general" / "通用" 等）
        _bad_topics = {'general', 'general topic', 'topic', '通用', '综合', '本期',
                       mag.lower(), mag_cn.lower(), mag_cn.strip('《》').lower()}
        if core_topic.strip().lower() in _bad_topics or not core_topic.strip():
            core_topic = ''
        # ── 生成章节关键词（文学意象短语）────────────────────────────────────
        _chapter_kws = _gen_chapter_keywords(blocks_data.get('blocks', []))

        # ── 构建标题：《杂志》YYYY年MM月DD日深度解读 - kw1、kw2、kw3 ──────────
        title_base = f"《{mag_cn}》{date_cn}深度解读"
        if _chapter_kws:
            yt_title = (title_base + " - " + "、".join(_chapter_kws))[:100]
        else:
            # fallback：用 core_topic 或第一个 block 标题
            _fb_kw = core_topic
            if not _fb_kw and blocks_data.get('blocks'):
                for _b in blocks_data['blocks'][:3]:
                    _bt = _b.get('title', '')
                    if _bt and not _bt.startswith('段') and not _bt.startswith('第'):
                        _fb_kw = _bt
                        break
            yt_title = (title_base + (f" - {_fb_kw}" if _fb_kw else ""))[:100]
        run['yt_title'] = yt_title
        save_active_run(run)
        print(f"    标题: {yt_title}")

        # 封面
        cover_path = os.path.join(img_dir, "thumbnail.jpg")
        if not os.path.exists(cover_path):
            cover_path = os.path.join(img_dir, "cover.png")
        if not os.path.exists(cover_path):
            cover_path = ""

        # 构建 description：每个章节含时间戳 + AI核心论点（argument字段）
        # ⚠️ 不在此处添加 [drive_id:] 标签 — upload_video.py 会通过 --drive-id 参数追加
        _blocks_list = blocks_data.get('blocks', [])
        _block_summaries = _summarize_blocks_for_desc(_blocks_list)
        topic_lines = []
        for _i, _b in enumerate(_blocks_list[:8]):
            _title = _b.get('title', '')
            # 跳过占位符标题
            if not _title or _title.startswith('段') or _title.startswith('第') or 'topic' in _title.lower():
                continue
            _ts    = _b.get('start_time', '')
            _short = _block_summaries[_i] if _i < len(_block_summaries) else ''
            ts_prefix = f"[{_ts}] " if _ts else ""
            topic_lines.append(f"{ts_prefix}【{_title}】{_short}" if _short else f"{ts_prefix}【{_title}】")
        if topic_lines:
            desc_body = (
                f"《{mag_cn}》{date_cn} 深度解读\n\n"
                + "\n".join(topic_lines)
                + "\n\n订阅频道获取更多内容。"
            )
        else:
            desc_body = (
                f"《{mag_cn}》{date_cn} 深度解读\n\n"
                f"本期解读全球一流杂志最新内容，带你了解世界。\n\n"
                f"订阅频道获取更多内容。"
            )
        description = desc_body
        upload_cmd = [
            'python3', UPLOAD_VIDEO, final_mp4,
            '--title', yt_title, '--description', description,
            '--category', '25', '--drive-id', fid, '--magazine', mag, '--date', dt,
        ]
        if cover_path:
            upload_cmd += ['--cover', cover_path]

        print(f"    📤 上传 YouTube...")
        try:
            result = subprocess.run(upload_cmd, capture_output=True, text=True, timeout=900)
            output = result.stdout + result.stderr
            print(output[-600:] if len(output) > 600 else output)

            # quota 检测 — 最优先
            if _is_quota_error(output):
                _mark_step_failed(run, 'upload', error='quotaExceeded — 明日自动重试')
                print(f"\n    ⛔ YouTube 配额耗尽！进度已保存，下次运行自动续传。")
                send_telegram(
                    f"⛔ *YouTube 配额耗尽*\n\n"
                    f"📁 `{fname}`\n📰 {mag}  {dt}\n\n"
                    f"进度已保存，明日 cron 自动续传。",
                    level='quota'
                )
                return 'quota_exceeded'

            # 提取 YouTube URL
            for line in output.split('\n'):
                if 'youtube.com/watch?v=' in line:
                    m = re.search(r'https://www\.youtube\.com/watch\?v=[\w-]+', line)
                    if m:
                        yt_url = m.group(0)
                        break

            # 如果 upload_video.py 输出了"已跳过"，说明该文件已在 processed.txt
            # 此时从 processed.txt 回捞真实 YT URL，避免写 UPLOAD_COMPLETED_NO_URL
            if not yt_url and ('已跳过' in output or 'SKIP' in output.upper()):
                try:
                    with open(PROCESSED) as _pf2:
                        for _pl2 in _pf2:
                            _parts2 = _pl2.strip().split(',', 3)
                            if len(_parts2) >= 4 and _parts2[0].strip() == fid:
                                _st2 = _parts2[3].strip()
                                if 'youtube.com' in _st2 or 'youtu.be' in _st2:
                                    yt_url = _st2.split()[0]
                                    break
                except Exception:
                    pass

            if yt_url:
                run['yt_url'] = yt_url
                prev_att = run['steps'].get('upload', {}).get('attempts', 0)
                _mark_step(run, 'upload', yt_url=yt_url, attempts=prev_att + 1)
                print(f"    ✅ 上传成功: {yt_url}")
                # 只有当 processed.txt 中还没有这个 Drive ID 的 URL 时才追加
                _already_logged = False
                try:
                    with open(PROCESSED) as _pf3:
                        for _pl3 in _pf3:
                            _p3 = _pl3.strip().split(',', 3)
                            if len(_p3) >= 4 and _p3[0].strip() == fid and ('youtube.com' in _p3[3] or 'youtu.be' in _p3[3]):
                                _already_logged = True
                                break
                except Exception:
                    pass
                if not _already_logged:
                    with open(PROCESSED, 'a') as f:
                        f.write(f"{fid},{fname},{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{yt_url}\n")
                # ── 上传后自动加入播放列表 ─────────────────────────────────────
                import re as _re_pl
                _yt_id_m = _re_pl.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", yt_url)
                if _yt_id_m:
                    _assign_video_to_playlist(_yt_id_m.group(1), mag)
            else:
                _mark_step_failed(run, 'upload', error='no YouTube URL in output')
                print(f"    ⚠️ 上传完成但未解析到 URL")
                # 只有当 processed.txt 中尚无此 Drive ID 的任何记录时才写 NO_URL
                _has_any_record = any(
                    l.strip().startswith(fid) for l in open(PROCESSED)
                ) if os.path.exists(PROCESSED) else False
                if not _has_any_record:
                    with open(PROCESSED, 'a') as f:
                        f.write(f"{fid},{fname},{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},UPLOAD_COMPLETED_NO_URL\n")

        except subprocess.TimeoutExpired:
            _mark_step_failed(run, 'upload', error='timeout 900s')
            print(f"    ❌ 上传超时（15分钟）")
            with open(PROCESSED, 'a') as f:
                f.write(f"{fid},{fname},{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},UPLOAD_TIMEOUT\n")
            _notify_step_failure(run, 'upload', 'upload_video.py timeout after 900s')
            return 'failed'
        except Exception as e:
            _mark_step_failed(run, 'upload', error=str(e))
            print(f"    ❌ 上传异常: {e}")
            _notify_step_failure(run, 'upload', str(e))
            return 'failed'

    # ═══════════════════════════════════════════════════════
    #  完成：写最终日志 + 清理 active_runs
    # ═══════════════════════════════════════════════════════
    drive_assets = run.get('drive_assets', {})   # 已在步骤6中写入

    completed_steps = [s for s in STEP_ORDER if _step_ok(run, s)]
    pipeline_status = 'completed' if set(STEP_ORDER) == set(completed_steps) else 'partial'

    write_process_log(
        info, yt_url, yt_title, transcript_chars, blocks_data,
        img_dir, drive_assets, pipeline_status,
        notes=f"steps_ok={','.join(completed_steps)}",
        run_state=run,
    )

    # 若 Drive 上传失败但其他步骤全部 ok，返回 'drive_partial'
    # 让 backfill 知道该条目需要重新补齐 Drive 素材
    # ⚠️ P0 fix: 必须在 remove_active_run() 前检查，否则 run 状态已丢失
    drive_step_ok = _step_ok(run, 'drive_upload')

    remove_active_run(fid)   # 从 active_runs 移除（任务完结，在 drive_partial 检查后）

    if not drive_step_ok:
        print(f"    ⚠️  完成（Drive 素材缺失）: {yt_title}")
        return 'drive_partial'

    print(f"    🎉 完成: {yt_title}")
    return 'ok'

# ════════════════════════════════════════════════════════════
#  断点续传：active_runs.json 状态管理
# ════════════════════════════════════════════════════════════

def _now():
    return datetime.now().isoformat(timespec='seconds')


def load_active_runs():
    """读取 active_runs.json → {drive_id: run_state}"""
    if not os.path.exists(ACTIVE_RUNS):
        return {}
    try:
        with open(ACTIVE_RUNS, encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ active_runs.json 读取失败: {e}")
        return {}


def _save_active_runs(runs):
    """原子写入 active_runs.json（先写 .tmp，再 replace）"""
    tmp = ACTIVE_RUNS + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(runs, f, ensure_ascii=False, indent=2)
    os.replace(tmp, ACTIVE_RUNS)


def save_active_run(run_state):
    """更新/插入单条 run_state"""
    runs = load_active_runs()
    runs[run_state['audio_drive_id']] = run_state
    _save_active_runs(runs)


def remove_active_run(drive_id):
    """任务完成或彻底失败后，从 active_runs 移除"""
    runs = load_active_runs()
    runs.pop(drive_id, None)
    _save_active_runs(runs)


def _step_ok(run_state, step_name):
    """判断该步骤是否已成功完成"""
    return run_state.get('steps', {}).get(step_name, {}).get('status') == 'ok'


def _mark_step(run_state, step_name, **kwargs):
    """标记步骤成功，立即持久化"""
    steps = run_state.setdefault('steps', {})
    prev  = steps.get(step_name, {})
    steps[step_name] = {
        'status':       'ok',
        'completed_at': _now(),
        'attempts':     prev.get('attempts', 0) + 1,
        **kwargs,
    }
    run_state['last_updated'] = _now()
    save_active_run(run_state)


def _mark_step_failed(run_state, step_name, error='', **kwargs):
    """标记步骤失败，立即持久化"""
    steps = run_state.setdefault('steps', {})
    prev  = steps.get(step_name, {})
    steps[step_name] = {
        'status':    'failed',
        'failed_at': _now(),
        'error':     str(error)[:400],
        'attempts':  prev.get('attempts', 0) + 1,
        **kwargs,
    }
    run_state['last_updated'] = _now()
    save_active_run(run_state)


def _classify_error(error_str: str) -> str:
    """
    根据错误信息将失败分类，决定重试策略。
    返回值：
      'code_bug'     — 代码/参数 bug，立刻报警，1次即停（需修复代码）
      'auth'         — 认证/权限/配额问题，立刻报警，1次即停
      'quality'      — QC 质量门控失败（文件太小/黑屏），只重置当前步骤立刻重试
      'drive_partial'— Drive 上传部分成功（仅缺 MP4），只重置 drive_upload 立刻重试
      'transient'    — 网络/超时/临时错误，等 6 小时重试
    """
    e = (error_str or '').lower()
    if any(k in e for k in ('unrecognized argument', 'syntaxerror', 'importerror',
                             'modulenotfounderror', 'attributeerror', 'script not found',
                             'no such file or directory', 'cannot find')):
        return 'code_bug'
    if any(k in e for k in ('403', 'unauthorized', 'invalid_grant', 'oauth',
                             'quota exceeded', 'insufficientpermissions',
                             'accessnotconfigured', 'forbidden')):
        return 'auth'
    if any(k in e for k in ('mp4未上传到drive', 'mp4_drive_id为空', 'upload_assets_returned_empty')):
        return 'drive_partial'
    if any(k in e for k in ('太小', 'mp4太小', 'qc:', 'missing or too small',
                             'thumbnail.jpg 太小', 'cover.png 太小', 'qc失败')):
        return 'quality'
    if any(k in e for k in ('timeout', 'timeoutexpired', '429', 'rate limit',
                             'connectionerror', 'remotedisconnected', 'connection reset',
                             'temporarily unavailable', 'unavailable', 'broken pipe',
                             'read timeout', 'connect timeout', 'socket',
                             'errno 49', "can't assign", 'eaddrnotavail',  # macOS port exhaustion
                             'errno 32', 'errno 104', 'errno 111')):       # broken pipe / refused
        return 'transient'
    return 'transient'  # 未知错误默认当作 transient


def _sanitize_active_run(run: dict) -> bool:
    """
    每次 cron 运行时对 active_runs 条目做两类修复，返回是否做过修改。

    ① 幻像步骤检测（步骤=ok 但 /tmp 文件已消失）
       → 重置该步骤及所有下游步骤，从最早丢失处断点续跑。

    ② 按错误分类决定重试策略（steps=failed）：

       分类          触发条件                     策略
       ----------    -------------------------    --------------------------------
       code_bug      参数错/ImportError 等        1次即报警+abandoned（须修代码）
       auth          403/OAuth/配额               1次即报警+abandoned（须检权限）
       quality       QC太小/黑屏等                立刻重置当前步骤，不等6h；≥3次报警
       drive_partial 仅缺 MP4 Drive ID            立刻重置 drive_upload；≥3次报警
       transient     超时/网络/未知               等6h后重置重试；≥3次报警+abandoned

    设计原则：只重置受影响步骤；不改 drive_assets（Drive 已上传的不重新上传）。
    """
    MAX_ALERT_RETRIES = 3   # 达到此次数发报警
    RETRY_AFTER_HOURS = 6

    steps   = run.get('steps', {})
    slug    = run.get('slug', '?')
    mag     = run.get('magazine', '?')
    dt      = run.get('date', '?')
    changed = False

    # ── 每步期待的 /tmp 文件（用于幻像检测）──────────────────
    audio_path      = f"/tmp/{slug}.mp3"
    transcript_path = f"/tmp/{slug}_transcript.txt"
    blocks_path_tmp = f"/tmp/{slug}_blocks.json"
    img_dir         = f"/tmp/{slug}_images"
    final_mp4       = f"/tmp/{mag}_{dt}_final.mp4"

    _step_files = {
        'download':     lambda: os.path.exists(audio_path)      and os.path.getsize(audio_path) > 1_000_000,
        'transcribe':   lambda: os.path.exists(transcript_path) and os.path.getsize(transcript_path) > 0,
        'blocks':       lambda: os.path.exists(blocks_path_tmp) and os.path.getsize(blocks_path_tmp) > 0,
        'images':       lambda: os.path.isdir(img_dir) and len([f for f in os.listdir(img_dir) if f.endswith('.png')]) > 0,
        'render':       lambda: os.path.exists(final_mp4) and os.path.getsize(final_mp4) > 5_000_000,
        'drive_upload': lambda: bool(run.get('drive_assets', {}).get('mp4_drive_id')),
    }

    def _alert_abandoned(step, attempts, error, reason):
        steps[step] = {**steps.get(step, {}), 'status': 'abandoned'}
        nonlocal changed; changed = True
        msg = (
            f"🚨 *任务需要人工处理* [{reason}]\n\n"
            f"📁 `{run.get('audio_filename','?')}`\n"
            f"📰 {mag}  {dt}  步骤: `{step}`\n\n"
            f"❌ 已重试 {attempts} 次（分类: {reason}）\n"
            f"错误: `{str(error)[:250]}`\n\n"
            f"修复后在 active_runs.json 中重置该条目的 `{step}` 步骤即可继续。"
        )
        send_telegram(msg, level='error')
        print(f"    🚨 [sanitize] {step} → abandoned ({reason}, {attempts}次)")

    # ① 幻像步骤检测：从最早的步骤开始，发现丢失立即级联清除
    found_stale = False
    for step in STEP_ORDER:
        if steps.get(step, {}).get('status') != 'ok':
            continue
        check = _step_files.get(step)
        if check is None:
            continue
        if not found_stale and not check():
            found_stale = True
            print(f"    ⚠️  [sanitize] {step} 标记ok但/tmp已消失 → 级联重置从 {step} 断点续跑")
        if found_stale:
            steps.pop(step, None)
            changed = True

    # ② 按错误分类处理 failed 步骤
    for step in STEP_ORDER:
        s = steps.get(step, {})
        if s.get('status') != 'failed':
            continue

        attempts  = s.get('attempts', 1)
        error_str = s.get('error', '')
        failed_at = s.get('failed_at', '')
        category  = _classify_error(error_str)

        hours_since = 999.0
        if failed_at:
            try:
                from datetime import datetime as _dt2
                hours_since = (datetime.now() - _dt2.fromisoformat(failed_at)).total_seconds() / 3600
            except Exception:
                pass

        if category == 'code_bug':
            # 代码 bug：1次即报警，不自动重试（须修代码后手动重置）
            _alert_abandoned(step, attempts, error_str, 'code_bug')

        elif category == 'auth':
            # 认证/权限：1次即报警，不自动重试
            _alert_abandoned(step, attempts, error_str, 'auth')

        elif category == 'quality':
            # QC 质量失败：立刻重置当前步骤重试（不等6h）
            if attempts >= MAX_ALERT_RETRIES:
                _alert_abandoned(step, attempts, error_str, 'quality')
            else:
                steps.pop(step, None)
                changed = True
                print(f"    🔄 [sanitize] {step} 质量QC失败，立刻重置重试 (已试{attempts}次)")

        elif category == 'drive_partial':
            # Drive 仅缺 MP4：立刻重置 drive_upload
            if attempts >= MAX_ALERT_RETRIES:
                _alert_abandoned(step, attempts, error_str, 'drive_partial')
            else:
                steps.pop(step, None)
                changed = True
                print(f"    🔄 [sanitize] drive_upload 仅缺MP4，立刻重置重试 (已试{attempts}次)")

        else:
            # transient（超时/网络/未知）：等6h后重置
            if attempts >= MAX_ALERT_RETRIES:
                _alert_abandoned(step, attempts, error_str, 'transient')
            elif hours_since >= RETRY_AFTER_HOURS:
                steps.pop(step, None)
                changed = True
                print(f"    🔄 [sanitize] {step} 暂时性失败超{RETRY_AFTER_HOURS}h，重置重试 (已试{attempts}次)")
            else:
                print(f"    ⏳ [sanitize] {step} 失败({category})，距上次{hours_since:.1f}h，等待{RETRY_AFTER_HOURS}h后重试")

    if changed:
        run['steps'] = steps
        run['last_updated'] = _now()
        save_active_run(run)
    return changed


def recover_artifact(local_path, drive_client, drive_file_id, label='file'):
    """
    优先使用本地文件。
    本地缺失时从 Drive 下载（/tmp 被清后可恢复素材）。
    返回 True 表示文件可用，False 表示无法恢复。
    """
    if local_path and os.path.exists(local_path) and os.path.getsize(local_path) > 0:
        return True
    if drive_file_id and drive_client:
        try:
            from googleapiclient.http import MediaIoBaseDownload
            print(f"    ♻️  从 Drive 恢复 {label} → {local_path}")
            request = drive_client.files().get_media(fileId=drive_file_id)
            fh = io.BytesIO()
            dl = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = dl.next_chunk()
            os.makedirs(os.path.dirname(local_path) if os.path.dirname(local_path) else '.', exist_ok=True)
            with open(local_path, 'wb') as out:
                out.write(fh.getvalue())
            print(f"    ✅ 恢复成功 ({os.path.getsize(local_path)//1024} KB)")
            return True
        except Exception as e:
            print(f"    ❌ Drive 恢复失败 ({label}): {e}")
    return False


def _is_quota_error(text):
    """检测输出中是否包含 YouTube quota 超限信号"""
    t = text.lower()
    return ('quotaexceeded' in t or 'uploadlimitexceeded' in t or
            ('quota' in t and 'exceeded' in t) or
            'daily limit' in t or 'rateLimitExceeded' in text)


def _print_run_status(run_state):
    """打印已完成/失败的步骤摘要"""
    for s in STEP_ORDER:
        info = run_state.get('steps', {}).get(s, {})
        st   = info.get('status', 'pending')
        icon = '✅' if st == 'ok' else ('❌' if st == 'failed' else '⏳')
        err  = f"  ← {info['error'][:60]}" if st == 'failed' else ''
        att  = f" (尝试×{info['attempts']})" if info.get('attempts', 0) > 1 else ''
        print(f"      {icon} {s}{att}{err}")


def _find_or_create_drive_folder(drive, name, parent_id):
    """在 Drive 中查找（或创建）指定名称的子文件夹，返回其 ID。
    用于年份文件夹（2025/2026）等基础目录。
    ⚠️ 不要用于 video 文件夹 — 请用 _find_existing_video_folder()。"""
    q = f"name='{_dq(name)}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    r = drive.files().list(q=q, fields='files(id)').execute()
    if r.get('files'):
        return r['files'][0]['id']
    meta = {'name': name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id]}
    f = drive.files().create(body=meta, fields='id').execute()
    return f['id']


def _find_existing_video_folder(drive, year_id):
    """
    在 year_id 目录下查找名为 'video' 的文件夹。
    【只找，不创建】—— 避免产生重复的 video 文件夹。

    规则：
      - 找到 1 个 → 直接返回其 ID
      - 找到多个 → 警告并使用最早创建的那个（最稳定）
      - 找不到   → 允许创建（第一次新杂志/新年份）并记录日志
    """
    q = (f"name='video' and '{year_id}' in parents "
         f"and mimeType='application/vnd.google-apps.folder' and trashed=false")
    r = drive.files().list(
        q=q, fields='files(id,name,createdTime)',
        orderBy='createdTime').execute()
    folders = r.get('files', [])

    if len(folders) == 0:
        # 完全找不到 video 文件夹 → 允许创建（新杂志首次上传）
        print(f"    ℹ️  未找到 video 文件夹，创建新的（year_id={year_id}）")
        meta = {'name': 'video',
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [year_id]}
        f = drive.files().create(body=meta, fields='id').execute()
        return f['id']

    if len(folders) > 1:
        # 有多个重复 video 文件夹 → 警告，使用最旧的
        ids = [f['id'] for f in folders]
        print(f"    ⚠️  发现 {len(folders)} 个 video 文件夹（{ids}），"
              f"使用最早创建的: {folders[0]['id']}")
        print(f"       请运行 fix_drive_video_folders.py 合并重复文件夹！")

    return folders[0]['id']


def _dq(s: str) -> str:
    """Drive API query 字符串转义：单引号必须用 \\' 转义，否则含 Barron's 等名称会 400。"""
    return s.replace("\\", "\\\\").replace("'", "\\'")


def _canonical_folder_name(mag, dt):
    """
    生成规范的 Drive 日期文件夹名：{Magazine}_{YYYYMMDD}
    保留原始大小写，空格→下划线，撇号→下划线，其他特殊字符→下划线。
    例：Wallstreet Journal → Wallstreet_Journal_20260425
        Barron's          → Barron_s_20260425
    """
    mag_part = re.sub(r"[^\w]", "_", mag).strip("_")
    return f"{mag_part}_{dt}"


def _extract_date_from_folder(folder_name: str, hint_yyyymmdd: str = '') -> str:
    """
    从 Drive 文件夹名中提取日期，返回 YYYYMMDD 字符串。
    处理所有常见格式：
      YYYYMMDD          → 20260228（直接）
      YYYY_MM_DD        → 20260228
      YYYY-MM-DD        → 20260228
      DD_MM_YYYY        → 20260228（日在前，月<=12）
      MM_DD_YYYY        → 20260228（月在前，歧义时用 hint 消歧）
      YYYYMM&MM         → 20260101（合刊，取第一个月第1天）
      YYYYMM            → 20260101（月刊，6位）
    返回空字符串表示无法提取。
    """
    # 合刊格式：YYYYMM&MM（如 202601&02）
    m = re.search(r'(20\d{2})(\d{2})[&+](\d{2})', folder_name)
    if m:
        return f"{m.group(1)}{m.group(2)}01"

    # 优先：8位连续数字 YYYYMMDD
    m = re.search(r'(\d{8})', folder_name)
    if m:
        s = m.group(1)
        yyyy, mm, dd = s[:4], s[4:6], s[6:8]
        if 1 <= int(mm) <= 12 and 1 <= int(dd) <= 31:
            return s

    # 4位年份 + 两组2位数字（YYYY_MM_DD 或 YYYY-MM-DD）
    m = re.search(r'(20\d{2})[_\-](\d{2})[_\-](\d{2})', folder_name)
    if m:
        yyyy, a, b = m.group(1), m.group(2), m.group(3)
        if 1 <= int(a) <= 12 and 1 <= int(b) <= 31:
            return f"{yyyy}{a}{b}"   # YYYY_MM_DD
        if 1 <= int(b) <= 12 and 1 <= int(a) <= 31:
            return f"{yyyy}{b}{a}"   # YYYY_DD_MM (罕见)

    # 两组2位 + 4位年份（DD_MM_YYYY 或 MM_DD_YYYY）
    m = re.search(r'(\d{2})[_\-](\d{2})[_\-](20\d{2})', folder_name)
    if m:
        a, b, yyyy = m.group(1), m.group(2), m.group(3)
        ia, ib = int(a), int(b)
        # 消歧：如果 a > 12，只能是 DD_MM
        if ia > 12:
            return f"{yyyy}{b}{a}"   # DD_MM_YYYY
        # 如果 b > 12，只能是 MM_DD
        if ib > 12:
            return f"{yyyy}{a}{b}"   # MM_DD_YYYY
        # 两者都 <= 12，用 hint 消歧
        if hint_yyyymmdd:
            hint_mm = hint_yyyymmdd[4:6]
            hint_dd = hint_yyyymmdd[6:8]
            if a == hint_mm and b == hint_dd:
                return f"{yyyy}{a}{b}"   # MM_DD
            if a == hint_dd and b == hint_mm:
                return f"{yyyy}{b}{a}"   # DD_MM
        # 无 hint：假设 MM_DD（英文出版物惯例）
        return f"{yyyy}{a}{b}"

    # 月刊格式：YYYYMM（6位连续，如文件夹名含 202601）
    m = re.search(r'(?<!\d)(20\d{2})(0[1-9]|1[0-2])(?!\d)', folder_name)
    if m:
        return f"{m.group(1)}{m.group(2)}01"

    return ''


def _normalize_folder_key(folder_name: str, hint_yyyymmdd: str = '') -> str:
    """
    把任意格式的 Drive 文件夹名规范化为 lowercase 无分隔符 key，用于模糊匹配。
    例：
      'New_Scientist_20260228'     → 'newscientist20260228'
      'new_scientist_20260228'     → 'newscientist20260228'
      'NewScientist_2026_02_28'    → 'newscientist20260228'
      'economist_28_02_2026'       → 'economist20260228'
    """
    date_part = _extract_date_from_folder(folder_name, hint_yyyymmdd)
    # 去掉日期、分隔符、特殊字符后的剩余部分作为杂志 key
    stripped = re.sub(r'[\d_\-\s]', '', folder_name).lower()
    stripped = re.sub(r'[^\w]', '', stripped)
    return f"{stripped}{date_part}"


def _find_drive_folder_robust(drive_fs, expected_mag: str, expected_dt: str,
                               parent_id: str) -> tuple:
    """
    在 parent_id 目录下找与 (expected_mag, expected_dt) 匹配的文件夹。
    匹配策略：
      1. 精确匹配 canonical_name（最快）
      2. 精确匹配 old_slug（向后兼容）
      3. 列出所有子文件夹，用规范化 key 做模糊匹配（处理大小写/日期格式差异）
    返回 (folder_id, folder_name, found: bool)
    """
    canonical = _canonical_folder_name(expected_mag, expected_dt)
    # 旧 slug 格式（lowercase，空格→下划线）
    old_slug   = re.sub(r'[^\w]', '_', expected_mag.lower()).strip('_') + '_' + expected_dt

    # 策略1：精确找 canonical
    r = drive_fs.files().list(
        q=f"name='{_dq(canonical)}' and '{parent_id}' in parents "
          f"and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields='files(id,name)').execute().get('files', [])
    if r:
        return r[0]['id'], r[0]['name'], True

    # 策略2：精确找 old_slug（大小写不敏感由 Drive 自己的精确 name= 处理）
    if old_slug != canonical:
        r2 = drive_fs.files().list(
            q=f"name='{_dq(old_slug)}' and '{parent_id}' in parents "
              f"and mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields='files(id,name)').execute().get('files', [])
        if r2:
            return r2[0]['id'], r2[0]['name'], True

    # 策略3：列出所有子文件夹，用规范化 key 比对
    # 用日期数字缩小搜索范围（Drive 不支持正则，用 contains 近似）
    dt_digits = expected_dt  # YYYYMMDD
    all_folders = drive_fs.files().list(
        q=f"'{parent_id}' in parents "
          f"and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields='files(id,name)', pageSize=100).execute().get('files', [])

    target_key = _normalize_folder_key(canonical, expected_dt)
    for folder in all_folders:
        folder_key = _normalize_folder_key(folder['name'], expected_dt)
        if folder_key == target_key:
            print(f"    🔍 模糊匹配文件夹: '{folder['name']}' → 规范名 '{canonical}'")
            return folder['id'], folder['name'], True

    return '', '', False


def _gen_mag_cover(drive_sa, mag_id, year_id, mag, dt, img_dir):
    """
    从 Drive 的 {magazine}/{year}/ 文件夹查找 PDF，提取第一页生成 mag_cover.jpg。
    返回本地 mag_cover.jpg 路径，失败返回 ''。
    优先级：PyMuPDF > pdf2image > ImageMagick convert
    """
    cover_path = os.path.join(img_dir, "mag_cover.jpg")
    if os.path.exists(cover_path) and os.path.getsize(cover_path) > 10000:
        print(f"    ℹ️  mag_cover.jpg 已存在，跳过")
        return cover_path

    # 在 year_id 下直接找 PDF（不递归进 audio/ 和 video/ 子目录）
    pdfs = []
    try:
        pdfs = drive_sa.files().list(
            q=f"'{year_id}' in parents and mimeType='application/pdf' and trashed=false",
            fields='files(id,name,size)', pageSize=10).execute().get('files', [])
    except Exception:
        pass
    # 备选：在 mag_id 直接下找（跨年情况）
    if not pdfs:
        try:
            pdfs = drive_sa.files().list(
                q=f"'{mag_id}' in parents and mimeType='application/pdf' and trashed=false",
                fields='files(id,name,size)', pageSize=10).execute().get('files', [])
        except Exception:
            pass

    if not pdfs:
        print(f"    ⚠️  Drive 中未找到 PDF，mag_cover 跳过")
        return ''

    # 优先选文件名含 dt 日期的 PDF，否则取最后一个
    chosen = next((p for p in pdfs if dt in p['name'].replace('-', '').replace('_', '')), pdfs[-1])
    size_mb = int(chosen.get('size', 0)) // (1024 * 1024)
    print(f"    📄 找到 PDF: {chosen['name']} ({size_mb} MB)，提取封面...")

    pdf_tmp = f"/tmp/{re.sub(r'[^a-z0-9]', '_', mag.lower())}_{dt}_src.pdf"
    try:
        from googleapiclient.http import MediaIoBaseDownload
        req = drive_sa.files().get_media(fileId=chosen['id'])
        fh = io.BytesIO()
        dl = MediaIoBaseDownload(fh, req)
        done = False
        while not done:
            _, done = dl.next_chunk()
        with open(pdf_tmp, 'wb') as f:
            f.write(fh.getvalue())
    except Exception as e:
        print(f"    ⚠️  PDF 下载失败: {e}")
        return ''

    try:
        # 优先：PyMuPDF
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_tmp)
            pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2))
            png_tmp = pdf_tmp.replace('.pdf', '_p1.png')
            pix.save(png_tmp)
            doc.close()
            from PIL import Image
            img = Image.open(png_tmp).convert('RGB')
            img.thumbnail((1280, 1280))
            img.save(cover_path, 'JPEG', quality=85)
            os.remove(png_tmp)
            print(f"    ✅ mag_cover.jpg 生成完成 (PyMuPDF, {os.path.getsize(cover_path)//1024} KB)")
            return cover_path
        except ImportError:
            pass

        # 备选：pdf2image
        try:
            from pdf2image import convert_from_path
            imgs = convert_from_path(pdf_tmp, first_page=1, last_page=1, dpi=150)
            if imgs:
                imgs[0].convert('RGB').save(cover_path, 'JPEG', quality=85)
                print(f"    ✅ mag_cover.jpg 生成完成 (pdf2image)")
                return cover_path
        except ImportError:
            pass

        # 备选：ImageMagick convert
        r = subprocess.run(
            ['convert', '-density', '150', f'{pdf_tmp}[0]', '-quality', '85', cover_path],
            capture_output=True, timeout=60)
        if r.returncode == 0 and os.path.exists(cover_path) and os.path.getsize(cover_path) > 5000:
            print(f"    ✅ mag_cover.jpg 生成完成 (ImageMagick)")
            return cover_path

        print(f"    ⚠️  mag_cover 生成失败（fitz/pdf2image/convert 均不可用）")
        return ''
    except Exception as e:
        print(f"    ⚠️  mag_cover 生成异常: {e}")
        return ''
    finally:
        try:
            os.remove(pdf_tmp)
        except Exception:
            pass


def _get_oauth_drive_client():
    """创建使用 OAuth token（个人 Drive 存储配额）的 drive client，支持自动刷新 access token"""
    from google.oauth2.credentials import Credentials
    import google.auth.transport.requests as _ga_req
    token_path = os.path.expanduser("~/.drive-upload-token.json")
    if not os.path.exists(token_path):
        print("    ⚠️ OAuth token 文件不存在，请运行 reauth_drive.py 重新授权")
        return None
    try:
        with open(token_path) as f:
            token_data = json.load(f)
        creds = Credentials.from_authorized_user_info(token_data)

        # 若 access token 过期但 refresh token 有效，自动刷新
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                try:
                    creds.refresh(_ga_req.Request())
                    # 写回最新 token，避免下次再刷新
                    with open(token_path, 'w') as fw:
                        fw.write(creds.to_json())
                    print("    🔄 OAuth access token 已自动刷新")
                except Exception as re_err:
                    err_msg = str(re_err)
                    if 'invalid_grant' in err_msg.lower():
                        print("    ❌ OAuth refresh token 已撤销，请运行 reauth_drive.py 重新授权")
                    else:
                        print(f"    ⚠️ OAuth token 刷新失败: {err_msg[:120]}")
                    return None
            else:
                print("    ⚠️ OAuth token 无效且无法刷新，请运行 reauth_drive.py 重新授权")
                return None

        return build('drive', 'v3', credentials=creds, cache_discovery=False)
    except Exception as e:
        print(f"    ⚠️ OAuth client 创建失败: {e}")
        return None


def upload_assets_to_drive(audio_info, img_dir, blocks_path, slug, final_mp4=None):
    """
    将本次生产的所有素材上传到 Drive，结构为：
      Globalmagzineyoutube/[magazine]/[year]/video/[slug]/
        cover.png, thumbnail.jpg, block_01.png … block_NN.png,
        [slug]_blocks_v5.json, [slug]_final.mp4

    返回 dict:
      {
        'folder_id':      Drive 文件夹 ID,
        'cover_id':       Drive 封面 ID,
        'thumbnail_id':   Drive 缩略图 ID,
        'blocks_json_id': Drive blocks JSON ID,
        'mp4_drive_id':   Drive 渲染视频 ID,       ← 新增，用于断点续传恢复
        'block_image_ids': [Drive ID for block_01, block_02, …],
      }
    或在失败时返回 {}（不中断主流程）
    """
    from googleapiclient.http import MediaFileUpload
    from google.oauth2 import service_account

    try:
        # SA：用于只读文件夹查找（能看见所有目录）
        sa_creds = service_account.Credentials.from_service_account_file(
            SA_PATH, scopes=['https://www.googleapis.com/auth/drive'])
        drive_fs = build('drive', 'v3', credentials=sa_creds, cache_discovery=False)

        # 优先用 OAuth（有存储配额），回退到 SA（只读/无配额）
        oauth_drive = _get_oauth_drive_client()
        if oauth_drive:
            drive_upload = oauth_drive
            print("    🔑 使用 OAuth（个人存储配额）上传")
        else:
            drive_upload = drive_fs
            print("    🔑 OAuth 不可用，回退 SA（可能无存储配额）")
        mag  = audio_info['magazine']
        year = audio_info.get('year', datetime.now().strftime('%Y'))

        # ── 用 SA 找根目录 → 杂志目录 → 年份目录 ──────────────────
        root_r = drive_fs.files().list(q="name='Globalmagzineyoutube'", fields='files(id)').execute()
        if not root_r.get('files'):
            print("    ⚠️ Drive 根目录未找到，跳过资产上传")
            return {}
        root_id = root_r['files'][0]['id']

        # 杂志文件夹（已存在）
        mag_r = drive_fs.files().list(
            q=f"name='{_dq(mag)}' and '{root_id}' in parents and mimeType='application/vnd.google-apps.folder'",
            fields='files(id)').execute()
        if not mag_r.get('files'):
            print(f"    ⚠️ 杂志文件夹 '{mag}' 未找到，跳过资产上传")
            return {}
        mag_id = mag_r['files'][0]['id']

        # 年份文件夹（找或创建）
        year_id = _find_or_create_drive_folder(drive_fs, year, mag_id)
        if not year_id:
            print(f"    ⚠️ 年份文件夹 '{year}' 找不到且无法创建，跳过资产上传")
            return {}

        # video/ 文件夹：【只找，不创建】
        # 规则：若已有 video 文件夹则复用（即使是 SA 创建或用户创建），
        #       若有多个则使用最旧的那个（最有可能是主文件夹）。
        # 若完全找不到 video 文件夹，才允许创建（见下方 fallback）。
        video_dir_id = _find_existing_video_folder(drive_fs, year_id)

        # ── 规范的日期文件夹名 ──────────────────────────────────────────
        # 格式：{Magazine}_{YYYYMMDD}，例如 Wallstreet_Journal_20260403
        dt = extract_date_from_name(audio_info['name']) or audio_info.get('date', '')
        canonical_name = _canonical_folder_name(mag, dt)

        # 三段式鲁棒查找：精确canonical → 精确old_slug → 全列表模糊匹配
        slug_dir_id, folder_display, found = _find_drive_folder_robust(
            drive_fs, mag, dt, video_dir_id)
        if found:
            if folder_display != canonical_name:
                print(f"    ℹ️  复用已有文件夹（{folder_display}），规范名为 {canonical_name}")
        else:
            # 不存在任何格式的文件夹 → 创建规范名
            slug_dir_id = _find_or_create_drive_folder(drive_fs, canonical_name, video_dir_id)
            folder_display = canonical_name

        print(f"    📂 Drive 素材目录: Globalmagzineyoutube/{mag}/{year}/video/{folder_display}/")

        result = {'folder_id': slug_dir_id, 'folder_name': folder_display,
                  'cover_id': '', 'thumbnail_id': '',
                  'blocks_json_id': '', 'mp4_drive_id': '', 'block_image_ids': [],
                  'mag_cover_id': ''}

        def _upload_file(local_path, drive_name, mime):
            """上传单个文件，如已存在则覆盖，返回 Drive ID。
            策略：存在文件→SA update；新文件→OAuth create（无 parent，SA 移入目标文件夹）→回退 SA。
            失败时返回空字符串，不抛异常"""
            if not local_path or not os.path.exists(local_path):
                return ''
            try:
                # 用 SA 检查是否已存在同名文件（SA 能看到所有文件）
                ex = drive_fs.files().list(
                    q=f"name='{_dq(drive_name)}' and '{slug_dir_id}' in parents and trashed=false",
                    fields='files(id)').execute()
                media = MediaFileUpload(local_path, mimetype=mime, resumable=False)

                if ex.get('files'):
                    # 已存在 → SA update（已有文件不耗配额）
                    fid = ex['files'][0]['id']
                    drive_fs.files().update(fileId=fid, media_body=media).execute()
                else:
                    # 新文件 → 优先 OAuth create（有存储配额），后 SA 移入目标文件夹
                    meta = {'name': drive_name}
                    try:
                        # OAuth 创建文件（无 parents 避免 drive.file 范围限制）
                        f = drive_upload.files().create(body=meta, media_body=media, fields='id').execute()
                        fid = f['id']
                        # SA 移入目标文件夹（SA 能访问所有文件夹）
                        try:
                            drive_fs.files().update(fileId=fid, addParents=slug_dir_id, fields='id').execute()
                        except Exception as mv_e:
                            print(f"      ⚠️ 无法移入目标文件夹: {mv_e}")
                    except Exception as oauth_e:
                        # OAuth 失败 → 回退到 SA
                        print(f"      ⚠️ OAuth 上传失败，回退 SA（可能无配额）: {oauth_e}")
                        meta['parents'] = [slug_dir_id]
                        f = drive_fs.files().create(body=meta, media_body=media, fields='id').execute()
                        fid = f['id']

                size_kb = os.path.getsize(local_path) // 1024
                print(f"      ↑ {drive_name} ({size_kb} KB) → {fid}")
                return fid
            except Exception as e:
                print(f"      ⚠️ 上传失败 {drive_name}: {e}")
                return ''

        # 封面
        cover_local = os.path.join(img_dir, 'cover.png')
        result['cover_id'] = _upload_file(cover_local, 'cover.png', 'image/png')

        # 缩略图
        thumb_local = os.path.join(img_dir, 'thumbnail.jpg')
        result['thumbnail_id'] = _upload_file(thumb_local, 'thumbnail.jpg', 'image/jpeg')

        # Blocks JSON
        if blocks_path and os.path.exists(blocks_path):
            bname = f"{slug}_blocks_v5.json"
            result['blocks_json_id'] = _upload_file(blocks_path, bname, 'application/json')

        # Block 图片 block_01.png … block_NN.png（按序排列）
        block_imgs = sorted(
            [f for f in os.listdir(img_dir) if re.match(r'block_\d+\.png', f)]
        ) if os.path.isdir(img_dir) else []
        for bimg in block_imgs:
            local_p = os.path.join(img_dir, bimg)
            bid = _upload_file(local_p, bimg, 'image/png')
            result['block_image_ids'].append({'filename': bimg, 'drive_id': bid})

        # 渲染好的 MP4（最关键：用于断点续传，quota 耗尽后直接从 Drive 拉，不重渲染）
        if final_mp4 and os.path.exists(final_mp4):
            mp4_name = f"{slug}_final.mp4"
            result['mp4_drive_id'] = _upload_file(final_mp4, mp4_name, 'video/mp4')

        # ⑤ mag_cover.jpg — 杂志 PDF 封面（第一页截图）
        # 找 mag_id 和 year_id（已在上方解析）
        mag_cover_local = os.path.join(img_dir, 'mag_cover.jpg')
        if os.path.exists(mag_cover_local) and os.path.getsize(mag_cover_local) > 5000:
            result['mag_cover_id'] = _upload_file(mag_cover_local, 'mag_cover.jpg', 'image/jpeg')
        else:
            print(f"    ℹ️  mag_cover.jpg 不存在或太小，尝试从 PDF 生成...")
            generated = _gen_mag_cover(drive_fs, mag_id, year_id, mag, dt, img_dir)
            if generated:
                result['mag_cover_id'] = _upload_file(generated, 'mag_cover.jpg', 'image/jpeg')
            else:
                print(f"    ⚠️  mag_cover 不可用（PDF 未找到或生成失败），跳过")

        n_block_imgs = len(block_imgs)
        n_assets = (1 if result['cover_id'] else 0) + (1 if result['thumbnail_id'] else 0) + \
                   (1 if result['blocks_json_id'] else 0) + n_block_imgs + \
                   (1 if result['mp4_drive_id'] else 0) + (1 if result['mag_cover_id'] else 0)
        print(f"    ✅ Drive 资产上传完成：{n_assets} 个文件（含MP4、mag_cover）")
        return result

    except Exception as e:
        print(f"    ⚠️ Drive 资产上传异常（不影响主流程）: {e}")
        import traceback; traceback.print_exc()
        return {}


def write_process_log(
    audio_info,       # info dict from scan_drive()
    yt_url,           # "https://www.youtube.com/watch?v=XXXXX"
    yt_title,         # YouTube 标题
    transcript_chars, # int
    blocks_data,      # parsed blocks JSON dict ({"core_topic":…,"blocks":[…]})
    img_dir,          # local image directory path
    drive_assets,     # dict returned by upload_assets_to_drive()
    pipeline_status,  # "completed" | "upload_failed" | "no_video" etc.
    notes="",
    run_state=None,   # active_run dict（含 steps 详情）
):
    """
    向 process_log.jsonl 追加一条完整可追溯记录。
    包含每个步骤的状态、耗时、错误信息（通过 run_state.steps 传入）。
    日志只追加，永不删除。
    """
    mag   = audio_info['magazine']
    fname = audio_info['name']
    fid   = audio_info['file_id']
    dt    = extract_date_from_name(fname) or 'unknown'

    # 提取 YouTube 视频 ID
    yt_vid_id = ''
    if yt_url and 'watch?v=' in yt_url:
        yt_vid_id = yt_url.split('watch?v=')[-1].split('&')[0]

    # 构建 blocks 条目（含图片 Drive ID 对照）
    block_id_map = {item['filename']: item['drive_id']
                    for item in drive_assets.get('block_image_ids', [])}

    blocks_log = []
    for i, b in enumerate(blocks_data.get('blocks', []), 1):
        img_filename = f"block_{i:02d}.png"
        img_local    = os.path.join(img_dir, img_filename) if img_dir else ''
        blocks_log.append({
            'index':          i,
            'title':          b.get('title', ''),
            'argument':       b.get('argument', ''),
            'summary':        b.get('summary', ''),
            'keywords':       b.get('keywords', []),
            'start_time':     b.get('start_time', ''),
            'end_time':       b.get('end_time', ''),
            'visual_prompt':  b.get('visual_prompt', ''),
            'image_local':    img_local,
            'image_drive_id': block_id_map.get(img_filename, ''),
        })

    # 从 run_state 提取步骤详情
    steps_summary = {}
    if run_state and run_state.get('steps'):
        for s in STEP_ORDER:
            si = run_state['steps'].get(s, {})
            steps_summary[s] = {
                'status':       si.get('status', 'pending'),
                'attempts':     si.get('attempts', 0),
                'completed_at': si.get('completed_at', ''),
                'failed_at':    si.get('failed_at', ''),
                'error':        si.get('error', ''),
            }

    entry = {
        'logged_at':        datetime.now().isoformat(timespec='seconds'),
        'magazine':         mag,
        'date':             dt,
        'audio_filename':   fname,
        'audio_drive_id':   fid,
        'youtube_video_id': yt_vid_id,
        'youtube_url':      yt_url or '',
        'youtube_title':    yt_title,
        'transcript_chars': transcript_chars,
        'core_topic':       blocks_data.get('core_topic', ''),
        'blocks_count':     len(blocks_log),
        'blocks':           blocks_log,
        # 步骤追踪（精确定位失败发生在哪步）
        'steps':            steps_summary,
        # Drive 资产
        'drive_video_folder_id': drive_assets.get('folder_id', ''),
        'cover_drive_id':        drive_assets.get('cover_id', ''),
        'thumbnail_drive_id':    drive_assets.get('thumbnail_id', ''),
        'blocks_json_drive_id':  drive_assets.get('blocks_json_id', ''),
        'mp4_drive_id':          drive_assets.get('mp4_drive_id', ''),
        # 状态
        'pipeline_status': pipeline_status,
        'notes':           notes,
    }

    with open(PROCESS_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    print(f"    📋 process_log.jsonl ← {mag} {dt} ({pipeline_status})")
    return entry


LOCK_FILE = '/tmp/scan_and_process.lock'

def _acquire_lock() -> bool:
    """
    防止并行 cron 实例同时运行。
    写入 PID lockfile；若已有 lockfile 且对应进程仍在运行 → 返回 False（本次直接退出）。
    """
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE) as _lf:
                old_pid = int(_lf.read().strip())
            # 检查进程是否仍存在（kill -0 不杀进程，只检查存在性）
            os.kill(old_pid, 0)
            # 进程存在 → 上一个实例仍在运行
            print(f"⏭️  检测到 scan_and_process 已在运行 (PID={old_pid})，本次跳过。")
            return False
        except (ValueError, ProcessLookupError, PermissionError):
            # PID 文件损坏，或进程已退出（stale lock）→ 清除并继续
            print(f"ℹ️  清除过期 lockfile (PID={old_pid if 'old_pid' in dir() else '?'})")
            os.remove(LOCK_FILE)
    # 写入当前 PID
    with open(LOCK_FILE, 'w') as _lf:
        _lf.write(str(os.getpid()))
    return True


def _release_lock():
    """释放 lockfile（main 结束时调用）"""
    try:
        if os.path.exists(LOCK_FILE):
            with open(LOCK_FILE) as _lf:
                pid = int(_lf.read().strip())
            if pid == os.getpid():
                os.remove(LOCK_FILE)
    except Exception:
        pass


def main():
    # ── 防并行：同一时间只允许一个实例运行 ────────────────────────────────
    if not _acquire_lock():
        return

    start = datetime.now()
    print(f"\n{'='*55}")
    print(f"🔍 YouTube 流水线启动: {start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}")

    # ── Phase -1: 检查 vfr_needs_repipeline.json（videofacereviewer 标记的无素材视频）─
    _VFR_REQUEUE = os.path.expanduser("~/hermesagent/Youtube video/vfr_needs_repipeline.json")
    if os.path.exists(_VFR_REQUEUE):
        try:
            with open(_VFR_REQUEUE) as _f:
                _requeue_list = json.load(_f)
            if _requeue_list:
                print(f"\n⚠️  videofacereviewer 发现 {len(_requeue_list)} 个视频 Drive 无素材，需重新处理：")
                for _rq in _requeue_list:
                    print(f"   🔄 {_rq.get('magazine','')}_{_rq.get('date','')}  "
                          f"audio_drive_id={_rq.get('audio_drive_id','')[:20]}…  "
                          f"yt={_rq.get('youtube_video_id','')}")
                print(f"   ℹ️  这些视频已在 YouTube，将重新生成 Drive 素材并更新封面。")
                print(f"   ℹ️  当 processed.txt 中去除其 YouTube URL 后，下次 pipeline 将重新处理。")
                print(f"   ℹ️  如需自动触发，请手动在 processed.txt 中将对应行状态改为 NEEDS_REUPLOAD。")
        except Exception as _e:
            print(f"   ⚠️ 读取重处理队列失败: {_e}")

    # ── Phase 0: 读取未完成任务（断点续传优先）─────────────
    print("\n♻️  检查 active_runs.json（未完成任务）...")
    active_runs  = load_active_runs()

    # ── 自动清理幻像步骤 + 6小时失败重试 ──────────────────────
    for aid, rs in list(active_runs.items()):
        _sanitize_active_run(rs)
    # 重新加载（sanitize 已原子写入）
    active_runs = load_active_runs()

    resume_queue = []
    for aid, rs in active_runs.items():
        all_done = all(_step_ok(rs, s) for s in STEP_ORDER)
        # abandoned 步骤视为"需要人工"，跳过自动续传
        has_abandoned = any(rs.get('steps', {}).get(s, {}).get('status') == 'abandoned'
                            for s in STEP_ORDER)
        if not all_done and not has_abandoned:
            resume_queue.append(rs)
            failed_steps = [s for s in STEP_ORDER if rs.get('steps', {}).get(s, {}).get('status') == 'failed']
            ok_steps     = [s for s in STEP_ORDER if _step_ok(rs, s)]
            print(f"   ⏸  {rs.get('audio_filename','?')} — ok={ok_steps}, failed={failed_steps}")
        elif has_abandoned:
            print(f"   🚨 {rs.get('audio_filename','?')} — 有 abandoned 步骤，跳过（等待人工处理）")

    if resume_queue:
        print(f"   → {len(resume_queue)} 个任务需要续传")
    else:
        print(f"   → 无未完成任务")

    # ── Phase 1: 扫描 Drive ────────────────────────────────
    print("\n📡 扫描 Drive...")
    all_audio, drive = scan_drive()
    if not all_audio:
        print("❌ Drive 扫描失败或无音频文件")
        sys.exit(1)
    print(f"   Drive 音频总数: {len(all_audio)}")

    # ── Phase 2: 连接 YouTube API ──────────────────────────
    print("\n🔑 连接 YouTube API...")
    token = get_yt_token()
    yt_drive_ids, yt_mag_dates, yt_ids, today_count = set(), set(), set(), 0
    if token:
        yt_drive_ids, yt_mag_dates, yt_ids, today_count = get_yt_uploads(token)
        print(f"   YouTube 视频总数: {len(yt_ids)}, 今日已上传: {today_count}")
    else:
        print(f"   ⚠️ YouTube API 不可用（配额超限?）将只基于 processed.txt 判断")

    # ── Phase 3: 对账，找新文件 ───────────────────────────
    print("\n⚖️  对账（L1:processed.txt / L2:YT drive_id / L3:YT mag+date）...")
    new_files = reconcile(all_audio, yt_drive_ids, yt_mag_dates)
    # 排除已在 active_runs 中的（避免重复创建）
    active_ids = set(active_runs.keys())
    new_files  = [f for f in new_files if f['file_id'] not in active_ids]
    print(f"   未完成续传任务: {len(resume_queue)} 个")
    print(f"   新文件待处理:   {len(new_files)} 个")

    if not resume_queue and not new_files:
        print("\n✅ 无任务，流水线安静退出")
        return

    # ── Phase 4: 处理（续传优先，再处理新文件）────────────
    quota_exceeded = False
    ok_count = fail_count = skip_count = 0

    # 打印配额报告
    qt = _get_qt()
    print(f"\n{quota_report()}")
    max_uploads_this_run = qt.max_uploads_possible()
    print(f"   本轮最多可上传: {max_uploads_this_run} 个视频\n")
    uploads_this_run = 0

    # 4a. 续传未完成任务
    if resume_queue:
        print(f"\n🔁 续传 {len(resume_queue)} 个未完成任务...")
    for i, rs in enumerate(resume_queue, 1):
        if quota_exceeded:
            print(f"   ⛔ quota 停止，跳过剩余续传")
            skip_count += len(resume_queue) - i + 1
            break
        if not qt.can_upload():
            print(f"\n⚠️ YouTube API 配额不足（剩余 {qt.remaining()} units，每视频需 ~{qt.max_uploads_possible()} 个位置），停止")
            skip_count += len(resume_queue) - i + 1
            break

        # 从 all_audio 查找 info dict；若 Drive 扫描没找到则用 run_state 重建
        fid = rs['audio_drive_id']
        info = all_audio.get(fid, {
            'name':      rs['audio_filename'],
            'magazine':  rs['magazine'],
            'file_id':   fid,
            'year':      rs.get('year', rs['date'][:4] if rs.get('date') else '2026'),
            'size':      0,
        })
        print(f"\n--- [续传 {i}/{len(resume_queue)}] ---")
        status = process_one_file(info, drive, existing_run_state=rs)

        if status == 'quota_exceeded':
            quota_exceeded = True
        elif status == 'ok':
            ok_count += 1
            uploads_this_run += 1
            quota_consume('videos.insert', 1)     # 1600 units
            quota_consume('thumbnails.set', 1)    #   50 units
        else:
            fail_count += 1

    # 4b. 新文件
    if new_files and not quota_exceeded:
        print(f"\n🔧 处理 {len(new_files)} 个新文件...")
    for i, info in enumerate(new_files, 1):
        if quota_exceeded:
            print(f"   ⛔ quota 停止，剩余 {len(new_files)-i+1} 个新文件留待下次")
            skip_count += len(new_files) - i + 1
            break
        if not qt.can_upload():
            rem = qt.remaining()
            print(f"\n⚠️ YouTube API 配额不足（剩余 {rem:,} units，每视频需 ~1,660 units），停止")
            print(f"   配额每日太平洋时间午夜重置，下次 cron 自动继续")
            skip_count += len(new_files) - i + 1
            break

        print(f"\n--- [新文件 {i}/{len(new_files)}] ---")
        status = process_one_file(info, drive)

        if status == 'quota_exceeded':
            quota_exceeded = True
        elif status == 'ok':
            ok_count += 1
            uploads_this_run += 1
            quota_consume('videos.insert', 1)     # 1600 units
            quota_consume('thumbnails.set', 1)    #   50 units
        else:
            fail_count += 1

    # ── 汇总 ──────────────────────────────────────────────
    elapsed = (datetime.now() - start).total_seconds()
    print(f"\n{'='*55}")
    print(f"✅ 流水线结束  耗时 {elapsed:.0f}s")
    print(f"   成功: {ok_count}  失败: {fail_count}  跳过: {skip_count}")
    if quota_exceeded:
        remaining_tasks = len([rs for rs in load_active_runs().values()
                         if not all(_step_ok(rs, s) for s in STEP_ORDER)])
        print(f"   ⛔ YouTube quota 耗尽，{remaining_tasks} 个任务已保存进度，明日自动续传")
    # 最终配额报告
    print(f"\n{quota_report()}")
    print(f"{'='*55}")

    # ── Telegram 汇总通知 ────────────────────────────────────────────
    run_date = start.strftime('%m-%d %H:%M')
    if fail_count == 0 and ok_count == 0 and not quota_exceeded:
        pass  # 无任务，安静退出，不发通知
    elif fail_count > 0 and ok_count == 0:
        send_telegram(
            f"*本轮全部失败* ({run_date})\n\n"
            f"❌ 失败: {fail_count}  ✅ 成功: {ok_count}  ⏭ 跳过: {skip_count}\n"
            f"耗时: {elapsed:.0f}s\n\n"
            f"请检查:\n`~/hermesagent/Youtube\\ video/magazine/process_log.jsonl`\n"
            f"`~/hermesagent/Youtube\\ video/magazine/active_runs.json`",
            level='error'
        )
    elif fail_count > 0:
        send_telegram(
            f"*本轮部分失败* ({run_date})\n\n"
            f"✅ 成功: {ok_count}  ❌ 失败: {fail_count}  ⏭ 跳过: {skip_count}\n"
            f"耗时: {elapsed:.0f}s",
            level='warn'
        )
    elif quota_exceeded:
        remaining_tasks = len([rs for rs in load_active_runs().values()
                                if not all(_step_ok(rs, s) for s in STEP_ORDER)])
        send_telegram(
            f"⛔ *配额耗尽* ({run_date})\n\n"
            f"✅ 本轮成功: {ok_count}\n"
            f"🔄 待续传: {remaining_tasks} 个（明日 cron 自动继续）",
            level='quota'
        )
    else:
        send_telegram(
            f"*本轮完成* ({run_date})\n\n"
            f"✅ 成功上传: {ok_count} 个视频\n"
            f"⏭ 跳过: {skip_count}  耗时: {elapsed:.0f}s",
            level='ok'
        )

    # ── 释放 lockfile ────────────────────────────────────────────────
    _release_lock()


if __name__ == '__main__':
    try:
        main()
    except Exception as _crash_e:
        import traceback as _tb_mod
        _tb_str = _tb_mod.format_exc()[-1200:]
        send_telegram(
            f"*Pipeline 崩溃！*\n\n"
            f"未捕获异常导致脚本意外退出。\n\n"
            f"需要检查: `scan\\_and\\_process.py`\n\n"
            f"```\n{_tb_str}\n```\n\n"
            f"手动运行排查:\n"
            f"`python3 ~/hermesagent/Youtube\\ video/magazine/scan_and_process.py`",
            level='crash'
        )
        raise
    finally:
        # 确保异常时也能释放 lockfile
        _release_lock()
