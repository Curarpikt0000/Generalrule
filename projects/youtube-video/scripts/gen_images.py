#!/usr/bin/env python3
"""
gen_images.py — 深色电影风格图片生成器（通用模板）
适用：Economist, WSJ, Barron's, New Yorker, Foreign Affairs, The Atlantic, Times, New Scientist, HBR, NatGeo

用法：
  python3 gen_images.py <blocks_path> <img_dir> --magazine-name <name> --date-str <YYYYMMDD>

封面布局：
  左上：《杂志名》(128px 金色) + 日期 (64px 白色)
  右上：从 Drive 下载对应期 PDF，提取第一页作为封面图（金色细边框）
  背景：Imagen 基于第一 block 内容生成，蓝橙电影科技风
  底部（260px 深色栏）：
    "本期导读" 标签 + 第一个 block 完整 AI summary（3行换行）
"""
import json, os, sys, time, argparse, io
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

SA_PATH    = os.path.expanduser("~/hermesagent/Youtube video/hermes-infra-prod-9c5abf6aefe8.json")
FONT_PATH  = "/System/Library/Fonts/STHeiti Medium.ttc"
FONT_LIGHT = "/System/Library/Fonts/STHeiti Light.ttc"
W, H = 1920, 1080  # 横版强制：所有图片必须 1920×1080，改这里前三思

# ── 横版断言：生成时立即检测，早发现早修复 ──────────────────────────────────
def _assert_landscape(path: str, label: str):
    """保存后立即验证图片为横版且分辨率合格。
    生成时是主防线，QC 是第二道保险。"""
    try:
        with Image.open(path) as img:
            w, h = img.size
        if h > w:
            raise RuntimeError(f"[横版断言失败] {label} 是竖版 ({w}×{h})！"
                               f"请检查 W,H 设置或 compose 函数")
        if w < 1280 or h < 720:
            raise RuntimeError(f"[横版断言失败] {label} 分辨率不足 ({w}×{h}，需≥1280×720)")
    except RuntimeError:
        raise
    except Exception as e:
        print(f"  ⚠️  横版断言无法读取 {label}: {e}")  # PIL 读取异常不阻断，QC 会再查

# ── 杂志中文名映射 ───────────────────────────────────────────────────────────
MAG_CN = {
    "Economist":                     "《经济学人》",
    "economist":                     "《经济学人》",
    "Wallstreet Journal":            "《华尔街日报》",
    "WallstreetJournal":             "《华尔街日报》",
    "wallstreetjournal":             "《华尔街日报》",
    "WSJ":                           "《华尔街日报》",
    "Barron's":                      "《巴伦周刊》",
    "Barrons":                       "《巴伦周刊》",
    "barrons":                       "《巴伦周刊》",
    "New Yorker":                    "《纽约客》",
    "Foreign Affairs":               "《外交事务》",
    "ForeignAffairs":                "《外交事务》",
    "The Atlantic":                  "《大西洋月刊》",
    "Times":                         "《泰晤士报》",
    "New Scientist":                 "《新科学家》",
    "Harvard Business Review":       "《哈佛商业评论》",
    "National Geographic":           "《国家地理》",
    "National Geographic Traveller": "《国家地理旅行者》",
    "NationalGeographicTraveller":   "《国家地理旅行者》",
    "National Geographic History":   "《国家地理历史》",
    "Bloomberg":                     "《彭博商业周刊》",
    "Science":                       "《科学》",
}

# ── 默认 Imagen prompt ───────────────────────────────────────────────────────
DEFAULT_PROMPTS = {
    "《经济学人》":       "Global political chessboard, electric blue twilight over parliament, deep navy and amber",
    "《华尔街日报》":     "Wall Street canyon, stock data streams glowing amber, deep charcoal and molten gold",
    "《巴伦周刊》":       "Golden investment charts rising like mountain ranges, deep navy blue, amber peaks",
    "《纽约客》":         "Moonlit New York rooftop, warm amber gallery light, burgundy and cream tones",
    "《外交事务》":       "Geopolitical globe at night, tectonic plates shifting, deep cobalt and molten gold",
    "《大西洋月刊》":     "Vast ocean at dawn, dark water meets pale gold sky, solitary lighthouse beam",
    "《泰晤士报》":       "Westminster Bridge at dusk, grey Thames reflecting amber lamplight",
    "《新科学家》":       "Quantum particle collision, electric blue-purple plasma, deep black background",
    "《哈佛商业评论》":   "Corporate boardroom at midnight, city lights, deep slate blue and warm amber",
    "《国家地理》":       "Epic wilderness at golden hour, mountain range glowing orange, vivid nature",
    "DEFAULT":            "Cinematic scene, deep chiaroscuro, rich amber and deep blue, epic atmospheric depth",
}


# ── 字体 ─────────────────────────────────────────────────────────────────────
def load_font(size):
    for path in [FONT_PATH, FONT_LIGHT]:
        try: return ImageFont.truetype(path, size)
        except: pass
    return ImageFont.load_default()


# ── 渐变背景（fallback）────────────────────────────────────────────────────
def make_gradient_bg():
    bg = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / H
        r = int(8  + t * 12)
        g = int(12 + t * 15)
        b = int(40 + t * 20)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    return bg


# ── Imagen 背景生成 ───────────────────────────────────────────────────────────
def gen_imagen_bg(prompt, label="bg"):
    try:
        from google.oauth2 import service_account
        import vertexai
        from vertexai.preview.vision_models import ImageGenerationModel
        sa = service_account.Credentials.from_service_account_file(SA_PATH)
        vertexai.init(project="hermes-infra-prod", location="us-central1", credentials=sa)
        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
        full = (f"{prompt}, Shot on ARRI Alexa cinema camera, anamorphic lens bokeh, "
                "shallow depth of field, dramatic volumetric lighting with visible light rays, "
                "cinematic color grading, deep shadows with rich blacks, film grain texture, "
                "16:9 cinematic aspect ratio, electric blue and warm amber color palette, "
                "NO TEXT, NO LETTERS, NO NUMBERS, NO WORDS, NO SPEECH BUBBLES, "
                "NO DOCUMENTS, NO SCREENS, NO PANELS, NO SIGNS anywhere. Pure visual background only.")
        # 安全 fallback prompt：当 safety block 触发时使用更抽象的描述
        fallback_prompts = [
            full,
            (f"Abstract cinematic visualization, dramatic chiaroscuro lighting, "
             "deep blue ocean and warm amber accents, editorial photography style, "
             "NO TEXT, NO LETTERS, NO NUMBERS. Pure visual background only."),
            (DEFAULT_PROMPTS.get("DEFAULT") +
             ", Shot on ARRI Alexa, anamorphic lens, cinematic color grading, "
             "NO TEXT, NO LETTERS, NO NUMBERS anywhere. Pure visual background only."),
        ]
        for attempt in range(5):
            try:
                # 前两次用原 prompt，之后用 fallback
                current_prompt = fallback_prompts[min(attempt, len(fallback_prompts)-1)]
                resp = model.generate_images(
                    prompt=current_prompt, number_of_images=1,
                    aspect_ratio="16:9",
                    safety_filter_level="block_some",
                    person_generation="dont_allow"
                )
                if resp.images:
                    img = resp.images[0]._pil_image.resize((W, H))
                    img = ImageEnhance.Brightness(img).enhance(1.05)
                    img = ImageEnhance.Contrast(img).enhance(1.15)
                    print(f"  ✅ Imagen OK: {label} (attempt={attempt+1})")
                    return img
                # safety block → 重试更抽象的 prompt
                print(f"  ⚠️  Imagen safety block: {label} attempt={attempt+1}，换 fallback prompt 重试")
                time.sleep(5)
                continue
            except Exception as e:
                if "429" in str(e):
                    w = min(60*(attempt+1), 240)
                    print(f"  ⏳ 429 rate-limit, wait {w}s")
                    time.sleep(w)
                else:
                    print(f"  ⚠️  Imagen error ({label}): {str(e)[:120]}")
                    # 非 429 错误也重试一次 fallback
                    if attempt < len(fallback_prompts) - 1:
                        print(f"  🔄 换 fallback prompt 重试...")
                        time.sleep(10)
                        continue
                    return None
    except Exception as e:
        print(f"  ⚠️  Imagen setup error: {e}")
    return None


# ── 从 block 内容生成内容相关的 Imagen prompt ────────────────────────────────
def build_cover_prompt(blocks, def_prompt):
    if blocks:
        first = blocks[0]
        content = (first.get('argument') or first.get('summary') or '').strip()
        if len(content) > 30:
            return (
                f"Cinematic visualization of: {content[:120]}. "
                "Electric deep blue ocean of data and light, warm amber and gold accents, "
                "technology meets global finance, dramatic chiaroscuro, IMAX cinematography"
            )
    return def_prompt


# ── PDF 第一页渲染为 PIL Image ────────────────────────────────────────────────
def _render_pdf_first_page(pdf_bytes: bytes):
    """渲染 PDF 第一页（封面）为 PIL Image，优先 PyMuPDF，fallback pdf2image"""
    # 方法1：PyMuPDF (fitz)
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if len(doc) == 0:
            return None
        page = doc[0]
        mat = fitz.Matrix(2.0, 2.0)   # 2x zoom ≈ 144 DPI，足够清晰
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        print(f"  ✅ PDF rendered via PyMuPDF: {img.size}")
        return img.convert("RGBA")
    except ImportError:
        pass
    except Exception as e:
        print(f"  ⚠️  PyMuPDF error: {e}")

    # 方法2：pdf2image
    try:
        from pdf2image import convert_from_bytes
        pages = convert_from_bytes(pdf_bytes, first_page=1, last_page=1, dpi=150)
        if pages:
            img = pages[0]
            print(f"  ✅ PDF rendered via pdf2image: {img.size}")
            return img.convert("RGBA")
    except ImportError:
        pass
    except Exception as e:
        print(f"  ⚠️  pdf2image error: {e}")

    print("  ⚠️  PDF rendering failed (install pymupdf: pip install pymupdf)")
    return None


# ── 从 drive_cover_map.json 找到对应 PDF 并下载 ─────────────────────────────
def fetch_drive_cover(magazine_name: str, date_str: str = "",
                      cover_map_path: str = None):
    """
    1. 读 drive_cover_map.json
    2. 按 magazine + date_str 匹配 PDF 文件
    3. 从 Drive 下载 PDF
    4. 提取第一页渲染为 PIL Image
    """
    default_map = os.path.expanduser("~/hermesagent/drive_cover_map.json")
    map_path = cover_map_path or default_map
    if not os.path.exists(map_path):
        print(f"  ℹ️  drive_cover_map.json 不存在，跳过封面图")
        return None

    try:
        with open(map_path) as f:
            covers = json.load(f)
    except Exception as e:
        print(f"  ⚠️  读取 cover_map 失败: {e}")
        return None

    # 匹配逻辑：magazine 名称相同 + name 里包含 date_str
    # 支持双月刊命名（如 "202601&02"）→ 先精确匹配，再尝试 YYYYMM 前缀匹配
    match = None
    fallback = None
    mag_lower = magazine_name.lower().replace("'", "").replace(" ", "")
    yyyymm = date_str[:6] if date_str and len(date_str) >= 6 else ""

    for c in covers:
        c_mag = c.get('magazine', '').lower().replace("'", "").replace(" ", "")
        c_name = c.get('name', '')
        if c_mag != mag_lower:
            continue
        if date_str and date_str in c_name:
            match = c      # 精确匹配（YYYYMMDD 在文件名中）
            break
        if yyyymm and yyyymm in c_name and not match:
            match = c      # YYYYMM 前缀匹配（双月刊 202601&02 型）
        if not fallback:
            fallback = c   # 取该杂志第一个作为兜底

    match = match or fallback

    if not match:
        print(f"  ℹ️  未找到 {magazine_name} {date_str} 的 PDF 封面")
        return None

    print(f"  📄 匹配到 PDF: {match['name']} (id={match['id']})")

    # 下载 PDF
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseDownload

        sa = service_account.Credentials.from_service_account_file(
            SA_PATH, scopes=['https://www.googleapis.com/auth/drive.readonly'])
        drive = build('drive', 'v3', credentials=sa, cache_discovery=False)

        buf = io.BytesIO()
        req = drive.files().get_media(fileId=match['id'])
        dl = MediaIoBaseDownload(buf, req)
        done = False
        while not done:
            _, done = dl.next_chunk()
        pdf_bytes = buf.getvalue()
        print(f"  📥 PDF 下载完成: {len(pdf_bytes)//1024} KB")

        return _render_pdf_first_page(pdf_bytes)

    except Exception as e:
        print(f"  ⚠️  PDF 下载失败: {e}")
        return None


# ── 描边文字 ──────────────────────────────────────────────────────────────────
def stroke(draw, xy, text, font, fill=(240,240,240), sfill=(0,0,0), sw=2):
    x, y = xy
    for dx in range(-sw, sw+1):
        for dy in range(-sw, sw+1):
            if dx or dy: draw.text((x+dx, y+dy), text, font=font, fill=sfill)
    draw.text((x, y), text, font=font, fill=fill)


# ── 右上角封面图嵌入（PDF 第一页裁剪为 2:3 竖版）────────────────────────────
def paste_cover_thumbnail(ov: Image.Image, cover_img: Image.Image,
                          box_w: int = 220, box_h: int = 310,
                          margin: int = 36) -> None:
    cw, ch = cover_img.size
    target_ratio = box_w / box_h
    src_ratio = cw / ch
    if src_ratio > target_ratio:
        new_w = int(ch * target_ratio)
        left = (cw - new_w) // 2
        cover_img = cover_img.crop((left, 0, left + new_w, ch))
    else:
        new_h = int(cw / target_ratio)
        cover_img = cover_img.crop((0, 0, cw, new_h))

    thumb = cover_img.resize((box_w, box_h), Image.LANCZOS)
    # 金色边框（3px）
    bordered = Image.new("RGBA", (box_w + 6, box_h + 6), (240, 165, 0, 255))
    bordered.paste(thumb, (3, 3))
    bx = W - (box_w + 6) - margin
    by = margin
    ov.paste(bordered, (bx, by), bordered)


# ── 文本换行（按字符宽度，中文每字一格）───────────────────────────────────────
def wrap_text(text: str, max_chars: int = 36) -> list:
    """将长文本按 max_chars 字符换行，在中文标点处断行优先"""
    lines = []
    while len(text) > max_chars:
        # 优先在标点处断行
        cut = max_chars
        for i in range(max_chars - 1, max_chars // 2, -1):
            if text[i] in '，。、；：！？':
                cut = i + 1
                break
        lines.append(text[:cut])
        text = text[cut:]
    if text:
        lines.append(text)
    return lines


# ── 构建封面 ──────────────────────────────────────────────────────────────────
def compose_cover(bg, mag_cn, date_disp, titles, core="", blocks=None,
                  cover_img=None, overall_summary=""):
    c = bg.copy().convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    # ── 左侧橙色竖条（全高）────────────────────────────────────────────────
    d.rectangle([52, 32, 61, H], fill=(240, 165, 0, 230))

    # ── 顶部半透明背景（留出右上角给封面图）────────────────────────────────
    right_margin = 300 if cover_img else 80
    hw = min(len(mag_cn) * 60 + 120, W - right_margin)
    hbg = Image.new("RGBA", (hw, 250), (5, 5, 15, 210))
    ov.paste(hbg, (52, 32), hbg)

    # ── 杂志名（128px 金色）────────────────────────────────────────────────
    stroke(d, (80, 38), mag_cn, load_font(128), fill=(240, 165, 0), sw=2)

    # ── 日期（64px 白色）───────────────────────────────────────────────────
    stroke(d, (80, 180), date_disp, load_font(64), fill=(230, 230, 230), sw=1)

    # ── 右上角：PDF 第一页封面图 ────────────────────────────────────────────
    if cover_img:
        paste_cover_thumbnail(ov, cover_img, box_w=220, box_h=310, margin=36)

    # ── 底部栏（260px，显示第一个 block 完整 AI summary）────────────────────
    bar_h = 260
    by = H - bar_h
    bar = Image.new("RGBA", (W, bar_h), (5, 5, 15, 225))
    ov.paste(bar, (0, by), bar)

    # "本期导读" 标签
    stroke(d, (80, by + 10), "本期导读", load_font(36), fill=(240, 165, 0), sw=1)

    # 底部文字：优先用全文 AI 总结，fallback 到第一 block 原始文本
    summary_text = overall_summary.strip() if overall_summary else ""
    if not summary_text and blocks:
        first = blocks[0]
        summary_text = (first.get('argument') or first.get('summary') or '').strip()

    if summary_text:
        # 换行处理（每行 34 字）
        lines = wrap_text(summary_text, max_chars=34)
        y = by + 58
        for i, line in enumerate(lines[:3]):  # 最多显示3行
            stroke(d, (80, y), line, load_font(46), fill=(235, 235, 235), sw=1)
            y += 62
        if len(lines) > 3:
            # 第三行末尾加省略号
            pass  # 已通过 wrap_text 截断

    c.paste(ov, (0, 0), ov)
    return c.convert("RGB")


# ── 构建分块图（block slide）───────────────────────────────────────────────
def compose_block(bg, block, idx, total):
    c = bg.copy().convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    d.rectangle([68, 60, 76, H - 220], fill=(240, 165, 0, 230))

    title = block.get("title", "")
    if (not title or title.startswith('段') or title.startswith('第')
            or 'topic' in title.lower()):
        title = f"第 {idx} 节"

    tbw = min(len(title) * 56 + 160, W - 200)
    tbg = Image.new("RGBA", (tbw, 115), (5, 5, 15, 195))
    ov.paste(tbg, (84, 54), tbg)
    stroke(d, (100, 60), title, load_font(82), sw=2)
    d.text((W - 120, 20), f"{idx}/{total}", font=load_font(38),
           fill=(200, 200, 200, 150))

    by = H - 205
    bar = Image.new("RGBA", (W, 218), (0, 0, 0, 210))
    ov.paste(bar, (0, by - 12), bar)

    # 显示文字优先用 summary（AI生成的详细总结），fallback 到 argument（核心论点）
    # summary 是 AI 用自己语言写的段落总结，不是原文摘录
    summ = block.get("summary", "").strip()
    arg  = block.get("argument", "").strip()
    display_text = summ if summ else arg   # summary 优先
    # 截取前120字用于显示（保持画面简洁）
    display_text = display_text[:120] if len(display_text) > 120 else display_text

    if display_text:
        y = by + 18
        lines = []
        text = display_text
        while len(text) > 44:
            cut = text.rfind("，", 0, 49)
            cut = cut if cut > 20 else 44
            lines.append(text[:cut + 1])
            text = text[cut + 1:]
        if text:
            lines.append(text)
        for line in lines[:2]:
            stroke(d, (100, y), line, load_font(50), sw=1)
            y += 66

    c.paste(ov, (0, 0), ov)
    return c.convert("RGB")


# ── 日期格式化 ────────────────────────────────────────────────────────────────
def fmt_date(s):
    s = str(s).replace("-", "").replace("_", "")
    if len(s) == 8: return f"{s[:4]}年{s[4:6]}月{s[6:8]}日"
    if len(s) == 6: return f"{s[:4]}年{s[4:6]}月"
    return s


# ── 主函数 ────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser()
    p.add_argument("blocks_path")
    p.add_argument("img_dir")
    p.add_argument("--magazine-name", default="")
    p.add_argument("--date-str", default="")
    p.add_argument("--no-imagen", action="store_true")
    p.add_argument("--cover-img", default="", help="预下载的封面图路径（可选）")
    p.add_argument("--cover-map", default="", help="drive_cover_map.json 路径")
    p.add_argument("--cover-only", action="store_true", help="只生成封面图，跳过 block 图片（remake 时加速用）")
    p.add_argument("--bg-img", default="", help="直接使用此 PNG 作为背景（跳过 Imagen 和渐变生成）")
    p.add_argument("--save-bg", default="", help="将生成的 Imagen/渐变背景保存到此路径（供下次缓存复用）")
    args = p.parse_args()

    os.makedirs(args.img_dir, exist_ok=True)

    with open(args.blocks_path, encoding="utf-8") as f:
        data = json.load(f)
    blocks = data.get("blocks", data if isinstance(data, list) else [])
    overall_summary = data.get("overall_summary", "") if isinstance(data, dict) else ""

    mag_raw = args.magazine_name
    mag_cn = MAG_CN.get(mag_raw, f"《{mag_raw}》" if mag_raw else "《杂志》")
    date_disp = fmt_date(args.date_str) if args.date_str else ""
    def_prompt = DEFAULT_PROMPTS.get(mag_cn, DEFAULT_PROMPTS["DEFAULT"])

    print(f"\n=== 生成图片: {mag_cn} {date_disp} ({len(blocks)} blocks) ===")

    # ── 1. 获取杂志封面图（PDF 第一页）───────────────────────────────────────
    cover_img = None
    if args.cover_img and os.path.exists(args.cover_img):
        try:
            cover_img = Image.open(args.cover_img).convert("RGBA")
            print(f"  📌 使用本地封面图: {args.cover_img}")
        except Exception as e:
            print(f"  ⚠️  本地封面图读取失败: {e}")
    else:
        # 始终尝试从 Drive 获取 PDF 封面（与 Imagen 背景生成无关）
        cover_img = fetch_drive_cover(mag_raw, args.date_str,
                                      args.cover_map or None)

    # ── 2. 封面背景：缓存 bg → Imagen → 渐变 ────────────────────────────────
    bg = None
    BG_MIN_BYTES = 100_000  # <100KB = 纯色fallback，强制重新生成
    if args.bg_img and os.path.exists(args.bg_img):
        bg_size = os.path.getsize(args.bg_img)
        if bg_size < BG_MIN_BYTES:
            print(f"  ⚠️  背景缓存太小({bg_size//1024}KB<100KB)，视为fallback，重新生成")
        else:
            try:
                bg = Image.open(args.bg_img).convert("RGB").resize((W, H), Image.LANCZOS)
                print(f"  📌 使用缓存背景: {args.bg_img}")
            except Exception as e:
                print(f"  ⚠️  缓存背景读取失败: {e}")
    if bg is None:
        cover_prompt = build_cover_prompt(blocks, def_prompt)
        bg = (None if args.no_imagen else gen_imagen_bg(cover_prompt, "cover")) or make_gradient_bg()
        # 若需要保存背景供下次缓存
        if args.save_bg and bg:
            try:
                os.makedirs(os.path.dirname(args.save_bg) or ".", exist_ok=True)
                bg.save(args.save_bg)
                print(f"  💾 背景已缓存: {args.save_bg}")
            except Exception as e:
                print(f"  ⚠️  背景保存失败: {e}")

    # ── 3. 合成封面 ───────────────────────────────────────────────────────────
    cover = compose_cover(
        bg, mag_cn, date_disp,
        [b.get("title", "") for b in blocks],
        core=data.get("core_topic", "") if isinstance(data, dict) else "",
        blocks=blocks,
        cover_img=cover_img,
        overall_summary=overall_summary,
    )
    cover_path = os.path.join(args.img_dir, "cover.png")
    cover.save(cover_path)
    _assert_landscape(cover_path, "cover.png")
    thumb_path = os.path.join(args.img_dir, "thumbnail.jpg")
    cover.resize((1280, 720), Image.LANCZOS).save(thumb_path, "JPEG", quality=92)
    _assert_landscape(thumb_path, "thumbnail.jpg")
    print("  ✅ cover.png + thumbnail.jpg saved (横版验证通过)")

    # ── 4. 每个 block 图 ──────────────────────────────────────────────────────
    if args.cover_only:
        print("  ℹ️  --cover-only: 跳过 block 图片生成")
        print(f"\n=== DONE: {len(os.listdir(args.img_dir))} files ===")
        return

    for i, block in enumerate(blocks):
        lbl = f"block_{i+1:02d}"
        print(f"=== {lbl}: {block.get('title','')[:30]} ===")
        vp = block.get("visual_prompt", "") or def_prompt
        if (not vp or "待补充" in vp
                or vp.startswith("Abstract geometric")
                or len(vp) < 15):
            vp = def_prompt
        if "Shot on ARRI" in vp:
            vp = vp[:vp.index("Shot on ARRI")].strip().rstrip(",")
        bg = (None if args.no_imagen else gen_imagen_bg(vp, lbl)) or make_gradient_bg()
        block_path = os.path.join(args.img_dir, f"{lbl}.png")
        compose_block(bg, block, i + 1, len(blocks)).save(block_path)
        _assert_landscape(block_path, f"{lbl}.png")
        print(f"  ✅ {lbl}.png saved (横版验证通过)")
        time.sleep(1.5)

    print(f"\n=== DONE: {len(os.listdir(args.img_dir))} files ===")


if __name__ == "__main__":
    main()
