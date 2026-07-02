#!/usr/bin/env python3
"""AtN 写入脚本：从 /tmp/atn_raw.md 和 /tmp/atn_body.md 写入 Notion"""
import sys, json, os, re
from pathlib import Path
from datetime import date
import requests
import opencc

# ── 配置 ──────────────────────────────────────────────────────────────
DATABASE_ID = "35547eb5-fd3c-81db-bff3-c50275484e33"

# 从 .env 读 Notion token
def load_env():
    env = {}
    env_path = Path.home() / ".hermes/.env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env

ENV = load_env()
NOTION_TOKEN = ENV.get("NOTION_TOKEN") or ENV.get("NOTION_API_KEY") or os.environ.get("NOTION_TOKEN")

if not NOTION_TOKEN:
    print("❌ NOTION_TOKEN 不存在，请检查 ~/.hermes/.env")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

# ── 读取文件 ──────────────────────────────────────────────────────────
raw_path  = Path("/tmp/atn_raw.md")
body_path = Path("/tmp/atn_body.md")

# 从 frontmatter 提取元数据
fm = {}
if raw_path.exists():
    raw = raw_path.read_text()
    parts = raw.split("---")
    if len(parts) >= 3:
        for line in parts[1].splitlines():
            if ": " in line:
                k, v = line.split(": ", 1)
                fm[k.strip()] = v.strip()

title      = fm.get("title", "Untitled")
source_url = fm.get("source_url", "")

print(f"📄 标题: {title}")
print(f"🔗 来源: {source_url}")

# 读取正文
if not body_path.exists():
    print("❌ /tmp/atn_body.md 不存在")
    sys.exit(1)

body = body_path.read_text()

# 清理转义字符
body = body.replace('\\*\\*', '**')
body = body.replace('\\*', '*')
body = body.replace('\\#', '#')
body = body.replace('\\`', '`')

print(f"📊 正文字符数: {len(body)}")

# ── 繁转简 ──────────────────────────────────────────────────────────────
converter = opencc.OpenCC('t2s')
body = converter.convert(body)
print(f"📝 繁转简完成: {len(body)} 字符")

# ── 连续文本分段 ────────────────────────────────────────────────────────
# Whisper 转录输出时常没有标点符号，按 max_len 切分为段落
# 每个段落作为一个 Notion paragraph block
def split_into_paragraphs(text, max_len=700):
    # 先按常见的自然断点尝试拆分（标点、空格、换行）
    segments = re.split(r'(?<=[，,、。！？；; \n])\s*', text)
    segments = [s.strip() for s in segments if s.strip()]

    # 如果 segments 太少（没标点），按 max_len 直接切
    if len(segments) <= 2:
        segments = []
        i = 0
        while i < len(text):
            end = min(i + max_len, len(text))
            if end < len(text):
                space_pos = text.rfind(' ', i + max_len - 100, end + 100)
                if space_pos > i:
                    end = space_pos + 1
            segments.append(text[i:end].strip())
            i = end
    else:
        # 有标点时合并成段落（不超过 max_len）
        merged = []
        current = ""
        for s in segments:
            if len(current) + len(s) + 1 > max_len and current:
                merged.append(current)
                current = s
            else:
                current = (current + " " + s).strip() if current else s
        if current:
            merged.append(current)
        segments = merged

    # 确保没有任何段落超过 2000 字符（Notion 限制）
    final = []
    for seg in segments:
        if len(seg) > 2000:
            for j in range(0, len(seg), 1900):
                final.append(seg[j:j+1900].strip())
        else:
            final.append(seg)
    return final

paragraphs = split_into_paragraphs(body)
print(f"📝 段落数: {len(paragraphs)}")

# ── 创建 Notion page（单 page，段落作为 children blocks）─────────────────
props = {
    "Title":  {"title": [{"text": {"content": title}}]},
    "Rating": {"select": {"name": "📥 待读"}},
}
if source_url:
    props["Source"] = {"url": source_url}
if date.today():
    props["Date Captured"] = {"date": {"start": str(date.today())}}

# 构造 children: 每个段落一个 paragraph block
children = []
for para in paragraphs:
    children.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": para}}]
        }
    })

# Notion 一次最多 100 blocks
page_resp = requests.post(
    "https://api.notion.com/v1/pages",
    headers=HEADERS,
    json={
        "parent": {"database_id": DATABASE_ID},
        "properties": props,
        "children": children[:100],
    }
)

if page_resp.status_code != 200:
    print("❌ 创建页面失败:", page_resp.text[:300])
    sys.exit(1)

page = page_resp.json()
page_id = page["id"]
print(f"✅ 页面已创建: {page_id}")

# ── 分批追加剩余 blocks ───────────────────────────────────────────────
for i in range(100, len(children), 100):
    batch = children[i:i+100]
    r = requests.patch(
        f"https://api.notion.com/v1/blocks/{page_id}/children",
        headers=HEADERS,
        json={"children": batch}
    )
    print(f"  追加 {i}~{i+len(batch)}/{len(children)}: {r.status_code}")

print(f"🎉 完成！共 {len(children)} 个段落")
print(f"🔗 https://notion.so/{page_id.replace('-','')}")
