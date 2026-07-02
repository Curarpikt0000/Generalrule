#!/usr/bin/env python3
"""
backfill_drive_assets.py — 为已上传 YouTube 视频补齐 Drive 素材

直接复用 scan_and_process.py 的 process_one_file() 流水线，
不再维护任何重复的 pipeline 逻辑。

用法：
  python3 backfill_drive_assets.py                   # 处理最多 5 条
  python3 backfill_drive_assets.py --max 10          # 处理最多 10 条
  python3 backfill_drive_assets.py --mag "Barron's"  # 只处理某杂志
  python3 backfill_drive_assets.py --dry-run         # 预览，不执行
"""

import argparse
import json
import os
import sys

# ── 直接 import scan_and_process 的流水线函数 ────────────────────────────────
BASE = os.path.expanduser("~/hermesagent/Youtube video/magazine")
sys.path.insert(0, BASE)

import scan_and_process as sap

REQUEUE_FILE       = os.path.expanduser("~/hermesagent/Youtube video/vfr_needs_repipeline.json")
COMPLETED_LOG      = os.path.expanduser("~/hermesagent/Youtube video/backfill_completed.json")
SA_PATH            = os.path.expanduser("~/hermesagent/Youtube video/hermes-infra-prod-9c5abf6aefe8.json")
PORTRAIT_FILE      = os.path.expanduser("~/hermesagent/Youtube video/portrait_needs_rerender.json")
ACTIVE_RUNS_PATH   = os.path.join(BASE, "active_runs.json")
ASSIGN_PL_DIR      = os.path.expanduser("~/hermesagent/Youtube video")

MAG_CN = {
    "Economist":                     "《经济学人》",
    "Wallstreet Journal":            "《华尔街日报》",
    "Barron's":                      "《巴伦周刊》",
    "New Yorker":                    "《纽约客》",
    "Foreign Affairs":               "《外交事务》",
    "The Atlantic":                  "《大西洋月刊》",
    "Times":                         "《泰晤士报》",
    "New Scientist":                 "《新科学家》",
    "Harvard Business Review":       "《哈佛商业评论》",
    "National Geographic":           "《国家地理》",
    "National Geographic Traveller": "《国家地理旅行者》",
    "National Geographic History":   "《国家地理历史》",
    "Bloomberg":                     "《彭博商业周刊》",
    "Science":                       "《科学》",
}


def _build_info(entry: dict) -> dict:
    """
    把 vfr_needs_repipeline.json 的条目转成 process_one_file() 期望的 info dict。
    info 需要: name, magazine, file_id, year, size
    """
    mag  = entry.get("magazine", "Unknown")
    dt   = entry.get("date", "00000000")       # YYYYMMDD
    fid  = entry.get("audio_drive_id", "")
    year = dt[:4] if len(dt) >= 4 else "2026"

    # 构造一个合理的文件名（slug 格式），用于 /tmp 路径和日志
    mag_safe = mag.replace("'", "").replace(" ", "_")
    filename = f"{mag_safe}_{dt}.mp3"

    return {
        "name":     filename,
        "magazine": mag,
        "file_id":  fid,
        "year":     year,
        "size":     0,
    }


def _log_completed(mag, dt, yt_video_id, info):
    """
    把成功 backfill 的条目追加写入 backfill_completed.json。
    供 update_youtube_thumbnails.py 读取，批量刷新 YouTube 封面。
    """
    import datetime
    try:
        if os.path.exists(COMPLETED_LOG):
            with open(COMPLETED_LOG, encoding='utf-8') as f:
                log = json.load(f)
        else:
            log = []

        # 避免重复记录同一 youtube_video_id
        existing_yt_ids = {e.get('youtube_video_id') for e in log}
        if yt_video_id in existing_yt_ids:
            return

        log.append({
            "magazine":         mag,
            "date":             dt,
            "youtube_video_id": yt_video_id,
            "audio_drive_id":   info.get("file_id", ""),
            "processed_at":     datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        with open(COMPLETED_LOG, 'w', encoding='utf-8') as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"    ⚠️  backfill_completed.json 写入失败: {e}")


def _assign_to_playlist(yt_video_id: str, magazine: str):
    """把视频加入对应杂志播放列表（非致命）。"""
    try:
        if ASSIGN_PL_DIR not in sys.path:
            sys.path.insert(0, ASSIGN_PL_DIR)
        import assign_youtube_playlists as _apl
        yt_svc = _apl._get_yt_service()
        playlists = _apl._list_all_playlists(yt_svc)
        cn_name = _apl.MAG_CN.get(magazine, f"《{magazine}》")
        pl_id, pl_name = _apl._find_playlist_id(playlists, cn_name, magazine)
        if not pl_id:
            pl_id = _apl._create_playlist(yt_svc, cn_name, dry_run=False)
            pl_name = cn_name
        existing = _apl._get_playlist_video_ids(yt_svc, pl_id)
        if yt_video_id in existing:
            print(f"    📋 已在播放列表 '{pl_name}'，跳过")
            return
        deleted_ids = set()
        ok = _apl._add_to_playlist(yt_svc, pl_id, yt_video_id,
                                   dry_run=False, deleted_ids=deleted_ids)
        if ok:
            print(f"    📋 ✅ 已加入播放列表: {pl_name}")
        else:
            print(f"    📋 ⚠️  加入播放列表失败")
    except Exception as e:
        print(f"    📋 ⚠️  加入播放列表时异常（非致命）: {e}")


def _reset_steps_for_rerender(slug):
    """
    重置 active_runs.json 中指定 slug 的 images / render / drive_upload 步骤，
    保留 download / transcribe / blocks（不浪费已完成的工作）。
    下次 process_one_file() 会从 images 步骤重新运行，强制生成横版图片和视频。
    """
    if not os.path.exists(ACTIVE_RUNS_PATH):
        print(f"    ℹ️  active_runs.json 不存在，无需重置")
        return False
    try:
        with open(ACTIVE_RUNS_PATH, encoding='utf-8') as f:
            runs = json.load(f)
        if slug not in runs:
            print(f"    ℹ️  {slug} 不在 active_runs.json 中（可能首次运行），无需重置")
            return False
        run = runs[slug]
        steps = run.get('steps', {})
        cleared = []
        for step in ('images', 'render', 'drive_upload', 'upload'):
            if step in steps:
                del steps[step]
                cleared.append(step)
        runs[slug]['steps'] = steps
        with open(ACTIVE_RUNS_PATH, 'w', encoding='utf-8') as f:
            json.dump(runs, f, ensure_ascii=False, indent=2)
        if cleared:
            print(f"    ♻️  已重置 {slug} 的步骤: {cleared}")
        return True
    except Exception as e:
        print(f"    ⚠️  重置 active_runs.json 失败: {e}")
        return False


def _run_portrait_rerender(args):
    """
    --portrait-rerender 模式：
      1. 读取 portrait_needs_rerender.json（由 youtubevideoQC.py 在发现竖版 MP4 时写入）
      2. 对每条记录，重置 active_runs.json 的 images/render/drive_upload/upload 步骤
      3. 调用 sap.process_one_file() 重新生成横版图片 + 渲染视频 + 上传 Drive
      4. 成功后从 portrait_needs_rerender.json 移除
      5. 视频内容替换由 youtubevideoQC.py --reupload-video 在下一次运行时处理
    """
    import time as _time

    if not os.path.exists(PORTRAIT_FILE):
        print("✅ portrait_needs_rerender.json 不存在，无需处理")
        return

    with open(PORTRAIT_FILE, encoding='utf-8') as f:
        portrait_queue = json.load(f)

    if not portrait_queue:
        print("✅ portrait_needs_rerender.json 为空，无需处理")
        return

    candidates = portrait_queue
    if args.mag:
        candidates = [v for v in candidates if v.get("magazine", "").lower() == args.mag.lower()]

    print(f"\n{'='*60}")
    print(f"🔄 竖版重渲染模式: {len(candidates)} 条（本次最多 {args.max} 条）")
    print(f"{'='*60}")

    if args.dry_run:
        print("[dry-run] 将重渲染以下视频:")
        for v in candidates[:args.max]:
            cn = MAG_CN.get(v.get("magazine", ""), v.get("magazine", ""))
            print(f"  {cn} {v.get('date','')}  yt={v.get('youtube_video_id','')}")
        return

    # ── 初始化 Drive SA client ────────────────────────────────────────────────
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    sa_creds = service_account.Credentials.from_service_account_file(
        SA_PATH, scopes=["https://www.googleapis.com/auth/drive"])
    drive = build("drive", "v3", credentials=sa_creds, cache_discovery=False)

    done_keys = []   # (magazine, date) 元组
    ok_count  = 0
    fail_count = 0

    for idx, entry in enumerate(candidates[:args.max]):
        mag = entry.get("magazine", "?")
        dt  = entry.get("date", "?")
        yt  = entry.get("youtube_video_id", "")
        cn  = MAG_CN.get(mag, mag)

        if idx > 0:
            _time.sleep(8)

        print(f"\n{'='*60}")
        print(f"🔄 重渲染 [{idx+1}/{min(len(candidates), args.max)}]: {cn} {dt}  (yt={yt})")

        # 构造 slug（与 scan_and_process.py 保持一致）
        mag_safe = mag.replace("'", "").replace(" ", "_")
        slug = f"{mag_safe}_{dt}"

        # 重置 active_runs 步骤：images/render/drive_upload/upload
        _reset_steps_for_rerender(slug)

        info = _build_info(entry)

        # backfill_mode=True：不重新上传到 YouTube（那由 youtubevideoQC.py 负责）
        status = sap.process_one_file(info, drive, backfill_mode=True)

        if status in ("ok", "drive_partial"):
            ok_count += 1
            done_keys.append((mag, dt))
            print(f"  ✅ 重渲染完成: {cn} {dt}  (status={status})")
            print(f"     → 下次运行 youtubevideoQC.py --reupload-video 将上传新视频并替换旧版")
            # 确保原视频仍在播放列表中（如尚未加入则补加）
            if yt:
                _assign_to_playlist(yt, mag)
        elif status == "quota_exceeded":
            print(f"  ⛔ YouTube 配额耗尽，停止处理剩余条目")
            fail_count += 1
            break
        else:
            fail_count += 1
            print(f"  ❌ 失败: {cn} {dt} (status={status})")

    # 从 portrait 队列中移除已成功重渲染的条目
    if done_keys:
        done_set = set(done_keys)
        remaining = [v for v in portrait_queue
                     if (v.get('magazine'), v.get('date')) not in done_set]
        with open(PORTRAIT_FILE, 'w', encoding='utf-8') as f:
            json.dump(remaining, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 重渲染: 成功 {ok_count} | 失败 {fail_count}")
        print(f"   portrait_needs_rerender.json 剩余 {len(remaining)} 条")
    else:
        print(f"\n⚠️  本次 0 条成功  失败: {fail_count} 条")

    if fail_count == 0 and ok_count > 0:
        print(f"\n💡 下一步: 运行 youtubevideoQC.py --reupload-video 将新横版视频上传到 YouTube")


def main():
    p = argparse.ArgumentParser(description="补齐已上传视频的 Drive 素材（复用 scan_and_process 流水线）")
    p.add_argument("--max",               type=int, default=5,  help="单次最多处理条数（默认 5）")
    p.add_argument("--mag",               type=str, default="", help="只处理指定杂志（英文名）")
    p.add_argument("--dry-run",           action="store_true",  help="预览将处理哪些条目，不实际执行")
    p.add_argument("--portrait-rerender", action="store_true",
                   help="重新渲染 portrait_needs_rerender.json 中的竖版视频（重置 images/render 步骤后重跑）")
    args = p.parse_args()

    # ── 竖版重渲染模式 ───────────────────────────────────────────────────────────
    if args.portrait_rerender:
        _run_portrait_rerender(args)
        return

    if not os.path.exists(REQUEUE_FILE):
        print("✅ vfr_needs_repipeline.json 不存在，无需处理")
        return

    with open(REQUEUE_FILE) as f:
        queue = json.load(f)

    # 只处理有 audio_drive_id 的条目
    candidates = [v for v in queue if v.get("audio_drive_id")]
    if args.mag:
        candidates = [v for v in candidates if
                      v.get("magazine", "").lower() == args.mag.lower()]

    if not candidates:
        print("✅ 所有条目都有 audio_drive_id，无需扫描\n没有可处理的条目")
        return

    print(f"\n{'='*60}")
    print(f"📋 待处理: {len(candidates)} 条（本次最多 {args.max} 条）")
    print(f"{'='*60}")

    if args.dry_run:
        print("[dry-run] 将处理以下视频:")
        for v in candidates[:args.max]:
            cn = MAG_CN.get(v.get("magazine", ""), v.get("magazine", ""))
            print(f"  {cn} {v.get('date','')}  yt={v.get('youtube_video_id','')}")
        return

    # ── 初始化 Drive SA client（复用 sap 的函数）────────────────────────────
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    sa_creds = service_account.Credentials.from_service_account_file(
        SA_PATH, scopes=["https://www.googleapis.com/auth/drive"])
    drive = build("drive", "v3", credentials=sa_creds, cache_discovery=False)

    done_ids  = []
    ok_count  = 0
    fail_count = 0

    import time as _time
    for idx, entry in enumerate(candidates[:args.max]):
        mag = entry.get("magazine", "?")
        dt  = entry.get("date", "?")
        yt  = entry.get("youtube_video_id", "")
        cn  = MAG_CN.get(mag, mag)

        # ── 每条之间等待 8s，让 macOS 释放 TIME_WAIT socket（防 Errno 49）────
        if idx > 0:
            _time.sleep(8)

        print(f"\n{'='*60}")
        print(f"🎬 处理 [{idx+1}/{min(len(candidates), args.max)}]: {cn} {dt}  (yt={yt})")

        info = _build_info(entry)

        # backfill_mode=True：跳过顶部去重，步骤7内部自动跳过YouTube重传
        status = sap.process_one_file(info, drive, backfill_mode=True)

        if status == "ok":
            ok_count += 1
            done_ids.append(entry.get("audio_drive_id", ""))
            print(f"  ✅ 完成: {cn} {dt}")
            # ── 写入完成日志（供后续批量刷新 YouTube 封面使用）──────────────
            _log_completed(mag, dt, yt, info)
            # ── 确保视频在播放列表中（backfill_mode 跳过了上传步骤）──────────
            if yt:
                _assign_to_playlist(yt, mag)
        elif status == "drive_partial":
            # Drive 上传失败，YouTube 已上传——保留在队列中，下次重试 Drive 上传
            fail_count += 1
            print(f"  ⚠️  Drive 素材缺失，保留队列待重试: {cn} {dt}")
        elif status == "quota_exceeded":
            print(f"  ⛔ YouTube 配额耗尽，停止处理剩余条目")
            fail_count += 1
            break
        else:
            fail_count += 1
            print(f"  ❌ 失败: {cn} {dt} (status={status})")

    # 从队列移除已成功处理的条目
    if done_ids:
        remaining = [v for v in queue if v.get("audio_drive_id", "") not in done_ids]
        with open(REQUEUE_FILE, "w") as f:
            json.dump(remaining, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 成功: {ok_count} 条  失败: {fail_count} 条")
        print(f"   vfr_needs_repipeline.json 剩余 {len(remaining)} 条")
    else:
        print(f"\n⚠️  本次 0 条成功  失败: {fail_count} 条")

    print(f"\n💡 下次运行继续处理剩余条目")


if __name__ == "__main__":
    main()
