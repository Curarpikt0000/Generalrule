#!/usr/bin/env python3
"""
Render video from block images + audio using ffmpeg concat demuxer.
Scans for cover/block images with flexible naming, parses HH:MM:SS timestamps,
and renders with -t to match audio duration exactly.

Usage:
  python3 render_video.py <magazine_slug> <date> <audio_path> [image_dir]

Examples:
  python3 render_video.py Economist 20260314 /tmp/Economist_20260314.mp3
  python3 render_video.py Science 20260312 /tmp/Science_20260312.mp3 /tmp/Science_20260312_images

Auto-detects:
  - Blocks JSON: /tmp/{slug}_{date}_blocks.json (tries multiple naming variants)
  - Cover: {image_dir}/{slug}_{date}_cover.png, cover.png, cover_with_pdf.png, cover_final.png
  - Blocks: {image_dir}/{slug}_{date}_block_{NN}.png, block_{NN}.png
"""
import json, os, subprocess

def ts_to_sec(t):
    """Parse timestamp string to seconds.

    Supports three formats emitted by different versions of generate_blocks.py:
      - New (standard HH:MM:SS):  '00:18:24' → 0*3600 + 18*60 + 24 = 1104s  ✅
      - DeepSeek (MM:SS):         '18:24'    → 18*60 + 24 = 1104s            ✅
      - Old (MM:SS:frames):       '22:41:00' → 22*60 + 41 = 1361s            ✅

    Primary formula uses true HH:MM:SS.  render_video() will fall back to the
    old MM:SS:frames formula if the primary result diverges from audio duration.
    """
    parts = str(t).split(':')
    if len(parts) == 3:
        # Standard HH:MM:SS — correct for blocks generated after 2026-05-19
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    elif len(parts) == 2:
        # MM:SS format — used by DeepSeek-generated blocks
        return int(parts[0]) * 60 + int(parts[1])
    return int(float(t))

def render_video(magazine, date, blocks_path, image_dir, audio_path):
    with open(blocks_path) as f:
        data = json.load(f)
    blocks = data.get('blocks', data if isinstance(data, list) else None) or data

    r = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','json', audio_path],
                       capture_output=True, text=True, timeout=10)
    try:
        audio_dur = int(float(json.loads(r.stdout)['format']['duration']))
    except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
        print(f"Error: cannot read audio duration from {audio_path}: {e}")
        print(f"  ffprobe stderr: {r.stderr[:200]}")
        return None

    # Use module-level ts_to_sec — DO NOT reassign this name inside the function
    _ts = ts_to_sec
    last_end = _ts(blocks[-1].get('end_time', 0))
    if abs(last_end - audio_dur) > 5:
        print(f"WARNING: blocks end_time={last_end}s vs audio duration={audio_dur}s")
        print(f"  Check time format. If blocks use MM:SS format (not HH:MM:SS),")
        print(f"  use: int(parts[0])*60 + int(parts[1]) instead.")
        # Fallback: old MM:SS:frames format (blocks from pipeline before 2026-05-19)
        # where HH field = minutes, MM field = seconds, SS = frames (ignored)
        def alt_ts(t):
            parts = str(t).split(':')
            if len(parts) == 3:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            return int(float(t))
        alt_end = alt_ts(blocks[-1].get('end_time', 0))
        if abs(alt_end - audio_dur) <= 5:
            print(f"  ALT parsing matches (old MM:SS format). Using fallback.")
            _ts = alt_ts
        else:
            print(f"  Neither HH:MM:SS nor MM:SS:frames matches audio duration ({audio_dur}s).")
            print(f"  Primary gave {last_end}s, fallback gave {alt_end}s.")
            # Last-resort: proportional scaling — stretch all timestamps so total = audio_dur
            # This handles Drive-recovered blocks with truncated/wrong timestamps.
            # Slide transitions will be proportionally scaled; video still renders correctly.
            best_end = last_end if last_end > alt_end else alt_end
            if best_end > 0:
                scale = audio_dur / best_end
                print(f"  SCALE fallback: multiplying all timestamps by {scale:.3f} (best_end={best_end}s → {audio_dur}s)")
                _base_ts = _ts if last_end >= alt_end else alt_ts
                def _ts(t, _b=_base_ts, _s=scale):  # noqa: F811
                    return int(_b(t) * _s)
            else:
                print(f"  Cannot recover — best_end=0. Skipping.")
                return None

    concat_lines = []
    cover_candidates = [
        os.path.join(image_dir, f'{magazine}_{date}_cover.png'),
        os.path.join(image_dir, 'cover.png'),
        os.path.join(image_dir, 'cover_with_pdf.png'),
        os.path.join(image_dir, 'cover_final.png'),
    ]
    cover_path = next((c for c in cover_candidates if os.path.exists(c)), None)
    if cover_path:
        concat_lines.extend([f"file '{cover_path}'", "duration 5"])

    for i, block in enumerate(blocks):
        block_candidates = [
            os.path.join(image_dir, f'{magazine}_{date}_block_{i+1:02d}.png'),
            os.path.join(image_dir, f'block_{i+1:02d}.png'),
            os.path.join(image_dir, f'block_{i+1}.png'),
        ]
        bp = next((c for c in block_candidates if os.path.exists(c)), None)
        if bp:
            dur = _ts(block.get('end_time', 0)) - _ts(block.get('start_time', 0))
            dur = max(dur, 5)
            concat_lines.extend([f"file '{bp}'", f"duration {dur}"])

    if concat_lines:
        # Bug fix 2026-06-17: append(file) + duration instead of duplicating last file line.
        # The last block's duration may not align exactly with audio_dur — fill remaining gap.
        last_file_line = concat_lines[-2]
        total_concat_dur = 5  # cover duration
        for j in range(1, len(concat_lines), 2):
            dur_str = concat_lines[j].replace('duration ', '')
            try:
                total_concat_dur += int(dur_str)
            except ValueError:
                try:
                    total_concat_dur += float(dur_str)
                except ValueError:
                    pass
        gap = audio_dur - total_concat_dur
        if gap > 0:
            concat_lines.append(last_file_line)
            concat_lines.append(f'duration {int(gap)}')
        elif gap < 0:
            # Total concat exceeds audio — trim last block duration
            excess = -gap
            last_dur_line_idx = len(concat_lines) - 1
            last_dur = int(concat_lines[last_dur_line_idx].replace('duration ', ''))
            concat_lines[last_dur_line_idx] = f'duration {max(last_dur - excess, 5)}'
    else:
        # No blocks found but we still need something — single-image fallback
        print("WARNING: no images found for concat, using cover as fallback")
        concat_lines = [f"file '{cover_path}'", f'duration {audio_dur}']

    with open(os.path.join(image_dir, 'concat.txt'), 'w') as f:
        f.write('\n'.join(concat_lines))

    output = f'/tmp/{magazine}_{date}_final.mp4'
    # 强制输出 1920×1080 横版：scale 填满后 pad 补黑边，再 fps=30
    # 这是渲染层的横版保险；主防在 gen_images.py（W,H=1920,1080）
    vf = 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30'
    cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', os.path.join(image_dir, 'concat.txt'),
           '-i', audio_path, '-c:v', 'libx264', '-c:a', 'aac', '-b:a', '192k',
           '-t', str(audio_dur), '-pix_fmt', 'yuv420p', '-preset', 'fast', '-crf', '23', '-vf', vf, output]

    print(f"Render {output} ({audio_dur}s, {len(blocks)} blocks)...")
    r2 = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if os.path.exists(output):
        sz = os.path.getsize(output)
        print(f"Done: {sz/1024/1024:.0f} MB")
        # Verify moov atom is present (corruption check)
        r3 = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',output],
                           capture_output=True, text=True, timeout=5)
        if r3.stdout.strip():
            print(f"Verified: {float(r3.stdout.strip()):.0f}s")
        else:
            print(f"WARNING: moov atom missing, file corrupted: {r3.stderr[:200]}")
        return output
    print(f"Error: {r2.stderr[:300]}")
    return None

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 4:
        print(__doc__); sys.exit(1)
    mag, date, audio = sys.argv[1], sys.argv[2], sys.argv[3]
    img_dir = sys.argv[4] if len(sys.argv) > 4 else f'/tmp/{mag}_{date}_images'
    for p in [f'/tmp/{mag}_{date}_blocks.json', f'/tmp/{mag.lower()}_{date}_blocks.json']:
        if os.path.exists(p) and render_video(mag, date, p, img_dir, audio):
            break
