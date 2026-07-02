#!/usr/bin/env python3
"""
gen_blocks.py — 独立 blocks JSON 生成器
AI 层级（按优先级）：
  1. DeepSeek API (deepseek-chat)
  2. Vertex AI Gemini via REST (hermes-infra-prod SA，与 gen_images.py 同一凭证)
     模型：gemini-2.0-flash → 失败则 gemini-1.5-pro 重试
  两者均失败 → 脚本退出 1，不写入占位符垃圾数据

用法（两种调用方式均支持）：
  # backfill_drive_assets.py 的调用方式（位置参数）：
  python3 gen_blocks.py <audio_path> <magazine> <date_str> <output_blocks_path>

  # flag 方式：
  python3 gen_blocks.py --audio <mp3> --magazine <mag> --date <YYYYMMDD> --output <json>

输出 JSON 格式：
  {
    "core_topic": "...",
    "blocks": [
      {
        "title": "...", "argument": "...",
        "start_time": "HH:MM:SS", "end_time": "HH:MM:SS",
        "summary": "≥200字中文总结",
        "keywords": ["kw1",...,"kw5"],
        "visual_prompt": "... ARRI ALEXA 65, ..."
      }, ...
    ]
  }
"""

import argparse
import json
import os
import re
import subprocess
import sys

import requests

# ── 凭证 & 常量 ──────────────────────────────────────────────────────────────
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "YOUR_DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

SA_PATH       = os.path.expanduser("~/hermesagent/Youtube video/hermes-infra-prod-9c5abf6aefe8.json")
GCP_PROJECT   = "hermes-infra-prod"
GCP_LOCATION  = "us-central1"
# 首选 gemini-2.0-flash，失败则 fallback 到 gemini-1.5-pro
GEMINI_MODELS = ["gemini-2.0-flash", "gemini-1.5-pro"]

VERTEX_BASE   = f"https://{GCP_LOCATION}-aiplatform.googleapis.com/v1/projects/{GCP_PROJECT}/locations/{GCP_LOCATION}/publishers/google/models"


# ── 系统 Prompt（两个 API 共用）──────────────────────────────────────────────
def _build_system_prompt(magazine: str, date_str: str, duration: int) -> str:
    mins, secs = divmod(duration, 60)
    duration_str = f"{mins:02d}:{secs:02d}"
    return (
        f"你是一位专业的播客内容分析师。请根据以下《{magazine}》{date_str}期中文播客的完整转录文本，"
        f"生成v5 blocks JSON。\n\n"
        f"【核心要求 — 违反则输出无效】\n"
        f"A. summary 和 argument 必须是你用自己语言写的总结，严禁照抄或直接引用原文。\n"
        f"   summary 要像新闻稿或书评段落，逻辑完整，有数据/人名/地名/论据支撑。\n"
        f"B. title 要简洁有力（8-15字），概括本块核心主题，不得是'第X节'或'话题X'。\n"
        f"C. argument 是一句话核心论点（20-40字），总结本块最重要的洞见。\n\n"
        f"详细格式要求：\n"
        f"1. 将 {duration} 秒（00:00至{duration_str}）的内容划分为约8-10个逻辑块\n"
        f"2. 每个块包含：title（中文标题8-15字）、argument（一句话核心论点20-40字）、"
        f"start_time/end_time（HH:MM:SS格式）、summary（≥200中文字符的详细AI总结）、"
        f"keywords（5个关键词）、visual_prompt（英文图像提示词）\n"
        f"3. visual_prompt要充分多样化 — 每块使用不同的构图和色调\n"
        f"   - 构图混合：wide establishing shot / close-up macro / overhead bird's-eye / "
        f"split-frame dual exposure / low-angle heroic / Dutch angle unsettling / intimate portrait\n"
        f"   - 色调混合：cool blue-teal / warm amber-gold / desaturated noir / "
        f"vibrant neon / muted earth tones / high-contrast monochrome\n"
        f"   - 每张visual_prompt末尾必须追加"
        f'"ARRI ALEXA 65, anamorphic lens, cinematic lighting, 8K"作为后缀\n'
        f"   - 每张visual_prompt末尾必须追加"
        f'"NO TEXT, no title, no on-screen text, no subtitles"作为最终保护语\n'
        f"4. 中文关键词（5个/块）\n"
        f"5. summary必须≥200中文字符，必须用自己语言写，包含具体数据、人名、地名、论据\n"
        f"6. 严格输出纯JSON，不要任何其他文字、不要markdown代码块标记\n\n"
        f"总时长：{duration}秒 = {duration_str}\n\n"
        f"JSON格式（只输出JSON）：\n"
        '{{"core_topic": "...", "blocks": [{{"title":"...","argument":"一句话核心论点",'
        '"start_time":"HH:MM:SS","end_time":"HH:MM:SS","summary":"≥200字自己写的总结，非原文",'
        '"keywords":["kw1","kw2","kw3","kw4","kw5"],'
        '"visual_prompt":"... ARRI ALEXA 65, anamorphic lens, cinematic lighting, 8K. '
        'NO TEXT, no title, no on-screen text, no subtitles"}}]}}'
    )


def _parse_ai_response(content: str, duration: int) -> tuple[str, list] | None:
    """从 AI 返回文本中解析 core_topic + blocks list。失败返回 None。"""
    # 剥离可能的 markdown 代码块
    text = content.strip()
    if "```" in text:
        parts = text.split("```")
        # 取第一个被包裹的代码块
        text = parts[1] if len(parts) > 1 else parts[0]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # 尝试提取第一个 { ... } 块
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if not m:
            return None
        try:
            data = json.loads(m.group(0))
        except Exception:
            return None

    blocks_raw = data.get("blocks", [])
    core_topic = data.get("core_topic", "")
    if not blocks_raw:
        return None

    n = len(blocks_raw)
    blocks = []
    for i, b in enumerate(blocks_raw):
        if b.get("start_time") and b.get("end_time"):
            st, et = b["start_time"], b["end_time"]
        else:
            sp = b.get("start_pct", i / n)
            ep = b.get("end_pct", (i + 1) / n)
            ss = int(duration * sp)
            se = int(duration * ep)
            st = f"{ss//3600:02d}:{(ss%3600)//60:02d}:{ss%60:02d}"
            et = f"{se//3600:02d}:{(se%3600)//60:02d}:{se%60:02d}"
        blocks.append({
            "title":        b.get("title", f"段{i+1}"),
            "argument":     b.get("argument", ""),
            "summary":      b.get("summary", ""),
            "keywords":     b.get("keywords", []),
            "start_time":   st,
            "end_time":     et,
            "visual_prompt": b.get("visual_prompt", ""),
        })
    return core_topic, blocks


# ── API 1：DeepSeek ────────────────────────────────────────────────────────
def call_deepseek(transcript: str, duration: int, magazine: str, date_str: str):
    """返回 (core_topic, blocks) 或 None。"""
    if not DEEPSEEK_API_KEY:
        print("  ⚠️  DEEPSEEK_API_KEY 未配置，跳过")
        return None

    system_prompt = _build_system_prompt(magazine, date_str, duration)
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": transcript},   # 完整转录，不截断
        ],
        "temperature": 0.3,
        "max_tokens": 8000,
    }
    try:
        resp = requests.post(
            DEEPSEEK_API_URL,
            json=payload,
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                     "Content-Type": "application/json"},
            timeout=120,
        )
        print(f"  DeepSeek 状态码: {resp.status_code}")
        if resp.status_code != 200:
            print(f"  ⚠️  DeepSeek 失败: {resp.text[:300]}")
            return None
        content = resp.json()["choices"][0]["message"]["content"]
        result = _parse_ai_response(content, duration)
        if result:
            core_topic, blocks = result
            print(f"  ✅ DeepSeek 成功: {len(blocks)} blocks，core_topic='{core_topic}'")
            return result
        print("  ⚠️  DeepSeek 返回内容无法解析为有效 blocks")
        return None
    except Exception as e:
        print(f"  ⚠️  DeepSeek 异常: {e}")
        return None


# ── API 2：Vertex AI Gemini（REST，用 SA 凭证）───────────────────────────────
def _get_vertex_token() -> str:
    """用 SA 文件获取 Google Cloud access token。"""
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request as GoogleAuthRequest

    creds = service_account.Credentials.from_service_account_file(
        SA_PATH,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    creds.refresh(GoogleAuthRequest())
    return creds.token


def call_vertex_gemini(transcript: str, duration: int, magazine: str, date_str: str):
    """
    依次尝试 GEMINI_MODELS 列表中的模型（gemini-2.0-flash → gemini-1.5-pro）。
    返回 (core_topic, blocks) 或 None。
    """
    try:
        token = _get_vertex_token()
    except Exception as e:
        print(f"  ⚠️  Vertex AI token 获取失败: {e}")
        return None

    system_prompt = _build_system_prompt(magazine, date_str, duration)
    # Gemini 不支持独立 system role，把 system prompt 放入 first user turn
    combined_prompt = system_prompt + "\n\n---\n转录文本（完整）：\n" + transcript  # 完整转录，不截断

    vertex_payload = {
        "contents": [{"role": "user", "parts": [{"text": combined_prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 8192,
        },
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    for model_name in GEMINI_MODELS:
        url = f"{VERTEX_BASE}/{model_name}:generateContent"
        print(f"  🤖 尝试 Vertex AI Gemini: {model_name}...")
        try:
            resp = requests.post(url, json=vertex_payload, headers=headers, timeout=120)
            print(f"     状态码: {resp.status_code}")
            if resp.status_code != 200:
                print(f"     ⚠️  失败: {resp.text[:300]}")
                continue

            data = resp.json()
            # Vertex AI Gemini 返回结构：candidates[0].content.parts[0].text
            content = (data.get("candidates", [{}])[0]
                          .get("content", {})
                          .get("parts", [{}])[0]
                          .get("text", ""))
            if not content:
                print(f"     ⚠️  返回内容为空")
                continue

            result = _parse_ai_response(content, duration)
            if result:
                core_topic, blocks = result
                print(f"  ✅ Vertex AI Gemini ({model_name}) 成功: {len(blocks)} blocks")
                return result
            print(f"     ⚠️  返回内容无法解析为有效 blocks")
        except Exception as e:
            print(f"     ⚠️  {model_name} 异常: {e}")

    return None


# ── 工具函数 ──────────────────────────────────────────────────────────────────
def get_audio_duration(audio_path: str) -> int:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "json", audio_path],
        capture_output=True, text=True, timeout=30,
    )
    try:
        return int(float(json.loads(r.stdout)["format"]["duration"]))
    except Exception:
        return 0


def get_transcript(audio_path: str, transcript_hint: str = "") -> str:
    """复用已有转录文件，否则用 Whisper small 重新转录。
    transcript_hint: 调用方传入的已知转录路径（最高优先级）。
    """
    stem = os.path.splitext(os.path.basename(audio_path))[0]
    audio_dir = os.path.dirname(audio_path)
    candidates = [
        transcript_hint,                                           # 调用方显式传入（最高优先）
        os.path.join(audio_dir, f"{stem}_transcript.txt"),        # backfill 的命名约定
        os.path.join(audio_dir, f"{stem}.txt"),                   # 备选
        f"/tmp/{stem}_transcript.txt",
        f"/tmp/{stem}.txt",
    ]
    for p in candidates:
        if not p:
            continue
        if os.path.exists(p) and os.path.getsize(p) > 50:
            with open(p, encoding="utf-8") as f:
                text = f.read().strip()
            if text:
                print(f"  ✅ 复用已有转录: {p} ({len(text)} 字符)")
                return text

    print("  ⚙️  未找到转录文件，启动 Whisper small 转录...")
    out_txt = f"/tmp/{stem}_transcript.txt"
    whisper_code = (
        "import whisper, sys\n"
        "model = whisper.load_model('small')\n"
        "result = model.transcribe('"
        + audio_path.replace("'", "\\'")
        + "', language='zh', fp16=False)\n"
        "open('"
        + out_txt.replace("'", "\\'")
        + "', 'w').write(result['text'])\n"
        "print(f'转录 {len(result[\"text\"])} 字符')\n"
    )
    r = subprocess.run(
        ["python3", "-c", whisper_code],
        capture_output=True, text=True, timeout=1800,
    )
    if r.returncode == 0 and os.path.exists(out_txt):
        with open(out_txt, encoding="utf-8") as f:
            text = f.read()
        print(f"  ✅ Whisper 转录完成 ({len(text)} 字符)")
        return text

    print(f"  ⚠️  Whisper 转录失败: {(r.stderr or r.stdout)[-300:]}")
    return ""


# ── 主函数 ────────────────────────────────────────────────────────────────────
def generate_blocks(audio_path: str, magazine: str, date_str: str, output_path: str,
                    transcript_hint: str = "") -> bool:
    """
    生成 blocks JSON 并写入 output_path。
    尝试顺序：DeepSeek → Vertex AI Gemini（2.0-flash → 1.5-pro）
    两者均失败 → 返回 False，不写入占位符
    """
    # 已有有效 blocks 文件则跳过
    if os.path.exists(output_path) and os.path.getsize(output_path) > 500:
        try:
            with open(output_path, encoding="utf-8") as f:
                existing = json.load(f)
            first_title = (existing.get("blocks") or [{}])[0].get("title", "")
            is_placeholder = (
                re.match(r"^(段|第)\s*\d", first_title)
                or re.match(r"^话题\s*\d", first_title)
                or first_title in ("", "话题", "topic")
            )
            if existing.get("blocks") and not is_placeholder:
                print(f"  ✅ 已有有效 blocks ({len(existing['blocks'])} 块)，跳过")
                return True
            print(f"  ⚠️  检测到占位符 blocks（title='{first_title}'），重新生成...")
            os.remove(output_path)
        except Exception:
            pass

    # 1. 获取音频时长
    duration = get_audio_duration(audio_path)
    if duration <= 0:
        print(f"  ⚠️  无法获取音频时长，使用默认 1800s")
        duration = 1800

    # 2. 获取转录文本
    transcript = get_transcript(audio_path, transcript_hint=transcript_hint)
    if not transcript:
        print("  ❌ 转录文本为空，无法生成 blocks")
        return False

    # 3. 尝试 DeepSeek
    print(f"\n  [API 1/2] DeepSeek...")
    result = call_deepseek(transcript, duration, magazine, date_str)

    # 4. 失败则尝试 Vertex AI Gemini
    if not result:
        print(f"\n  [API 2/2] Vertex AI Gemini (项目: {GCP_PROJECT})...")
        result = call_vertex_gemini(transcript, duration, magazine, date_str)

    # 5. 两者均失败 → 退出
    if not result:
        print("  ❌ DeepSeek 和 Vertex AI Gemini 均失败，不生成占位符，退出")
        return False

    core_topic, blocks = result

    # 6. 写出 JSON（包含完整转录原文，供后续 QC 和回查使用）
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    out = {
        "core_topic": core_topic,
        "transcript": transcript,   # 完整逐字转录原文，永久存档
        "blocks": blocks,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"  ✅ blocks 写出: {output_path} ({len(blocks)} 块，core_topic='{core_topic}'，转录 {len(transcript)} 字)")
    return True


def main():
    # 位置参数模式：gen_blocks.py <audio> <mag> <date> <output> [transcript_path]
    if len(sys.argv) >= 5 and not sys.argv[1].startswith("--"):
        audio_path       = sys.argv[1]
        magazine         = sys.argv[2]
        date_str         = sys.argv[3]
        output_path      = sys.argv[4]
        transcript_hint  = sys.argv[5] if len(sys.argv) >= 6 else ""
    else:
        parser = argparse.ArgumentParser(description="生成 v5 blocks JSON（DeepSeek → Vertex AI Gemini）")
        parser.add_argument("--audio",      required=True,  help="音频文件路径 (.mp3)")
        parser.add_argument("--magazine",   required=True,  help="杂志英文名")
        parser.add_argument("--date",       required=True,  help="日期 YYYYMMDD")
        parser.add_argument("--output",     required=True,  help="输出 blocks JSON 路径")
        parser.add_argument("--transcript", default="",     help="已有转录文件路径（可选，跳过 Whisper）")
        args = parser.parse_args()
        audio_path      = args.audio
        magazine        = args.magazine
        date_str        = args.date
        output_path     = args.output
        transcript_hint = args.transcript

    print(f"🔧 gen_blocks.py: {magazine} {date_str}")
    print(f"   音频: {audio_path}")
    print(f"   输出: {output_path}")

    success = generate_blocks(audio_path, magazine, date_str, output_path,
                              transcript_hint=transcript_hint)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
