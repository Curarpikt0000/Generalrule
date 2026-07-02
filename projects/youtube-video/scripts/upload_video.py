#!/usr/bin/env python3
"""
统一的 YouTube 上传脚本。
功能：
- 单文件上传
- 先检查 processed.txt 防重复
- 检查今天已上传数量
- 重试机制（防网络波动）
- 自动压缩缩略图
"""

import json, os, sys, io, time, re, csv
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from PIL import Image
import requests as req_lib

CONFIG = {
    "token_path": os.path.expanduser("~/.youtube-mcp/token.json"),
    "processed_file": os.path.expanduser("~/hermesagent/Youtube video/magazine/processed.txt"),
    "max_daily_uploads": 100,  # 每日上限，避免触发配额
}

def get_token():
    with open(CONFIG["token_path"]) as f:
        td = json.load(f)
    creds = Credentials(
        token=td["token"],
        refresh_token=td["refresh_token"],
        token_uri=td["token_uri"],
        client_id=td["client_id"],
        client_secret=td["client_secret"],
        scopes=td["scopes"],
    )
    creds.refresh(Request())
    return creds.token

_today_count_cache = None  # 进程内缓存，避免每次上传都调 playlistItems API

def get_today_upload_count():
    """检查今天已上传到频道的视频数量（进程内缓存，避免重复 API 调用）"""
    global _today_count_cache
    if _today_count_cache is not None:
        return _today_count_cache
    token = get_token()
    r = req_lib.get(
        "https://www.googleapis.com/youtube/v3/channels?part=contentDetails&mine=true",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    if r.status_code != 200:
        return 0
    uploads_playlist = r.json()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    
    today = datetime.now().strftime("%Y-%m-%d")
    count = 0
    page_token = None
    while True:
        params = {"part": "snippet", "playlistId": uploads_playlist, "maxResults": 50}
        if page_token:
            params["pageToken"] = page_token
        r2 = req_lib.get(
            "https://www.googleapis.com/youtube/v3/playlistItems",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=10,
        )
        if r2.status_code != 200:
            break
        data = r2.json()
        for item in data.get("items", []):
            if item["snippet"]["publishedAt"][:10] == today:
                count += 1
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    _today_count_cache = count
    return count


def increment_today_count():
    """上传成功后递增本地缓存，避免重新查询 API"""
    global _today_count_cache
    if _today_count_cache is not None:
        _today_count_cache += 1

def check_already_uploaded(drive_id):
    """
    用 Drive File ID 精确查找 processed.txt。
    只有该行包含 YouTube URL（真正上传成功）才视为"已上传"。
    UPLOAD_COMPLETED_NO_URL / UPLOAD_TIMEOUT 等失败状态视为未上传。
    """
    FAILED_STATUSES = {
        'PENDING_UPLOAD', 'RENDERED_QUOTA_EXCEEDED', 'TRANSCRIBED_BLOCKS_READY_QUOTA_EXCEEDED',
        'UPLOAD_TIMEOUT', 'UPLOAD_FAILED', 'UPLOAD_COMPLETED_NO_URL', 'NO_VIDEO',
    }
    processed = CONFIG["processed_file"]
    if not os.path.exists(processed) or not drive_id:
        return False
    with open(processed) as f:
        for line in f:
            if line.strip().startswith("#") or not line.strip():
                continue
            parts = line.strip().split(",")
            if parts and parts[0].strip() == drive_id:
                status = parts[3].strip() if len(parts) > 3 else ''
                # 跳过失败 / 待重试的状态
                if any(status.startswith(s) for s in FAILED_STATUSES):
                    continue
                # 只有真正成功的 URL 才算
                if 'youtube.com/watch?v=' in status:
                    return True
                # RECOVERED_FROM_YT / SAME_ISSUE_ALREADY_ON_YT 也算已处理
                if status in ('RECOVERED_FROM_YT', 'SAME_ISSUE_ALREADY_ON_YT'):
                    return True
    return False

def upload_video(video_path, cover_path, title, description_tags, blocks=None, drive_id=None, magazine=None, date_str=None):
    """
    上传单个视频到 YouTube（公开）。

    Args:
        video_path:        MP4 文件路径
        cover_path:        封面图片路径（可选）
        title:             视频标题
        description_tags:  {"description": str, "tags": [str], "categoryId": str}
        blocks:            Block JSON 列表（用于构建描述）
        drive_id:          Google Drive File ID（嵌入 description 作为唯一索引）
        magazine:          杂志名（嵌入 description 用于同期去重）
        date_str:          日期字符串 YYYYMMDD（嵌入 description 用于同期去重）

    Returns: (success: bool, video_url: str_or_None, message: str)
    """
    # 前置检查
    if not os.path.exists(video_path):
        return False, None, f"文件不存在: {video_path}"

    file_size = os.path.getsize(video_path)

    # L1: Drive ID 精确去重（快速本地检查）
    if drive_id and check_already_uploaded(drive_id):
        return False, None, f"⚠️ 已跳过（drive_id={drive_id} 在 processed.txt 中已存在）"

    # 将唯一索引标签追加到 description 最底部（内容主体在前，标签不干扰正文）
    base_desc = description_tags.get("description", "").rstrip()
    id_parts = []
    if drive_id:   id_parts.append(f"[drive_id:{drive_id}]")
    if magazine:   id_parts.append(f"[magazine:{magazine}]")
    if date_str:   id_parts.append(f"[date:{date_str}]")
    if id_parts:
        description_tags = dict(description_tags)
        # 内容 → 空行 → 分隔线 → 空行 → 标签（视觉上隔离，不影响正文阅读）
        description_tags["description"] = (
            base_desc + "\n\n.\n\n" + "  ".join(id_parts)
        ).strip()
    
    # 检查每日配额
    today_count = get_today_upload_count()
    if today_count >= CONFIG["max_daily_uploads"]:
        return False, None, f"今天已上传 {today_count} 个视频，超过每日上限 {CONFIG['max_daily_uploads']}"
    
    print(f"📤 今日已上传 {today_count} 个，剩余配额充足")
    
    # 构建 body
    body = {
        "snippet": {
            "title": title[:100],
            "description": description_tags.get("description", "")[:5000],
            "tags": description_tags.get("tags", []),
            "categoryId": description_tags.get("categoryId", "25"),
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        }
    }
    
    with open(CONFIG["token_path"]) as f:
        td = json.load(f)
    
    token = get_token()
    # 429 退避时间：第1次重试等60s，第2次等120s（指数退避）
    _RETRY_WAIT = [60, 120]
    for attempt in range(3):
        if attempt > 0:
            wait = _RETRY_WAIT[attempt - 1]
            print(f"  🔄 重试 {attempt+1}/3（等待 {wait}s 让 YouTube 冷却）...")
            time.sleep(wait)

        creds = Credentials(
            token=token,
            refresh_token=td["refresh_token"],
            token_uri=td["token_uri"],
            client_id=td["client_id"],
            client_secret=td["client_secret"],
            scopes=td["scopes"],
        )
        creds.refresh(Request())
        token = creds.token

        # Step 1: Initiate resumable upload
        r = req_lib.post(
            "https://www.googleapis.com/upload/youtube/v3/videos?part=snippet,status&uploadType=resumable",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-Upload-Content-Length": str(file_size),
                "X-Upload-Content-Type": "video/mp4",
            },
            json=body,
            timeout=30,
        )

        if r.status_code == 400:
            err_msg = r.json().get("error", {}).get("message", "")
            if "exceeded the number of videos" in err_msg:
                return False, None, f"YouTube 每日上传配额已满: {err_msg}"
            return False, None, f"400 错误: {err_msg}"

        if r.status_code == 429:
            print(f"  Init failed: HTTP 429 (rate limit)")
            continue  # 进入退避等待

        if r.status_code != 200:
            print(f"  Init failed: HTTP {r.status_code}")
            continue
        
        upload_url = r.headers.get("Location", "")
        
        # Step 2: Upload file data
        with open(video_path, "rb") as f:
            video_data = f.read()
        
        r2 = req_lib.put(
            upload_url,
            data=video_data,
            headers={"Content-Length": str(len(video_data)), "Content-Type": "video/mp4"},
            timeout=600,
        )
        
        print(f"  → HTTP {r2.status_code}")
        
        if r2.status_code in (200, 201):
            video_id = r2.json().get("id")
            url = f"https://www.youtube.com/watch?v={video_id}"
            increment_today_count()
            print(f"  ✅ {url}")
            
            # Step 3: Upload thumbnail (if available)
            if cover_path and os.path.exists(cover_path):
                try:
                    img = Image.open(cover_path).resize((1280, 720), Image.LANCZOS)
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=85, optimize=True)
                    buf.seek(0)
                    
                    yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
                    media = MediaIoBaseUpload(buf, mimetype="image/jpeg")
                    r3 = yt.thumbnails().set(videoId=video_id, media_body=media).execute()
                    print(f"  🖼 缩略图: ✅")
                except Exception as e:
                    print(f"  ⚠️ 缩略图上载失败: {e}")
            
            return True, url, "上传成功"
        
        # Transient error — retry
        print(f"  Body: {r2.text[:200]}")
    
    return False, None, "RATE_LIMITED: 重试 3 次后仍失败（HTTP 429），今日上传已达限速上限，请明日再试"


def main():
    """CLI 入口"""
    import argparse
    parser = argparse.ArgumentParser(description="上传视频到 YouTube")
    parser.add_argument("video", help="MP4 文件路径")
    parser.add_argument("--title", required=True, help="视频标题")
    parser.add_argument("--description", default="", help="视频描述")
    parser.add_argument("--tags", default="", help="逗号分隔的标签")
    parser.add_argument("--category", default="25", help="类别 ID (默认 25=新闻)")
    parser.add_argument("--cover", default="", help="封面图片路径")
    parser.add_argument("--check", action="store_true", help="只检查今天上传数量，不上传")
    parser.add_argument("--drive-id", default="", help="Google Drive File ID（嵌入 description 作为唯一索引）")
    parser.add_argument("--magazine", default="", help="杂志名（嵌入 description 用于同期去重）")
    parser.add_argument("--date", default="", help="日期 YYYYMMDD（嵌入 description 用于同期去重）")
    parser.add_argument("--id-tags-file", default="", help="从文件读取 id_tags（由 scan_and_process.py 生成）")

    args = parser.parse_args()

    if args.check:
        count = get_today_upload_count()
        print(f"今天已上传: {count} 个视频")
        return

    # 支持从 sidecar 文件读取 id_tags
    drive_id, magazine, date_str = args.drive_id, args.magazine, args.date
    if args.id_tags_file and os.path.exists(args.id_tags_file):
        with open(args.id_tags_file) as tf:
            for line in tf:
                line = line.strip()
                if line.startswith("[drive_id:"):
                    drive_id = line[10:-1]
                elif line.startswith("[magazine:"):
                    magazine = line[10:-1]
                elif line.startswith("[date:"):
                    date_str = line[6:-1]

    success, url, msg = upload_video(
        args.video,
        args.cover,
        args.title,
        {
            "description": args.description,
            "tags": [t.strip() for t in args.tags.split(",") if t.strip()],
            "categoryId": args.category,
        },
        drive_id=drive_id,
        magazine=magazine,
        date_str=date_str,
    )
    
    if success:
        print(f"\n🎉 {msg}")
        print(f"🔗 {url}")
    else:
        print(f"\n❌ {msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()
