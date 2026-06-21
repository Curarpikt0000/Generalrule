#!/usr/bin/env python3
"""
tools/gfinance_research.py

Google Finance Beta 「研究 AI」二次验证抓取。
利用用户已登录的 Chrome profile（cookies），所以无需重新认证。

调用方：FiHeroBot 通过终端在"二次验证模式"下调用本脚本。
设计原则：按需触发，不是每次都跑。SOUL §二次验证模式 控制触发。

用法：
    # 取文本答案 (JSON)
    python3 tools/gfinance_research.py "今日美股是不是在高位？"

    # 同时截图
    python3 tools/gfinance_research.py "..." --screenshot /tmp/gfinance.png

    # 指定 chrome profile（如不用默认）
    python3 tools/gfinance_research.py "..." --chrome-profile ~/.gfinance-chrome-profile

输出（stdout, JSON）：
{
  "question": "...",
  "answer_text": "...",       // Google AI 的回答原文
  "sources_count": N,         // Google AI 引用源数
  "screenshot": "/tmp/...",   // 如指定 --screenshot
  "duration_seconds": X.X,
  "timestamp": "2026-05-29T...",
  "url": "https://www.google.com/finance/...",
  "error": null               // or 错误描述
}

退出码：
  0 = 成功
  2 = 抓取失败（answer_text 为 null，error 非 null）
  其他 = 脚本本身错误（依赖/参数）

依赖：
  pip install playwright
  playwright install chromium    # 或不装 chromium，下面 channel='chrome' 直接用本机 Chrome

§2.10 显式失败：所有错误必须明示返回，禁止用印象填。
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print(json.dumps({
        "error": "playwright not installed. Run: pip install playwright && playwright install chromium",
    }, ensure_ascii=False))
    sys.exit(1)

# 默认指向用户主 Chrome profile —— ⚠️ 这会和正在运行的 Chrome 冲突
# 推荐用户先 cp 一份到独立目录，参考脚本头部说明
DEFAULT_CHROME_PROFILE = os.path.expanduser(
    "~/Library/Application Support/Google/Chrome"
)
GFINANCE_URL = "https://www.google.com/finance/"


def fetch(
    question: str,
    screenshot_path: str | None = None,
    chrome_profile: str = DEFAULT_CHROME_PROFILE,
    timeout_ms: int = 60_000,
    headless: bool = False,
) -> dict:
    """
    打开 Google Finance，输入问题到「研究」输入框，等待 AI 回答，抓取文本。

    headless=False：Google 较容易识别 headless 自动化，默认 headful（会弹 Chrome 窗口）。
    """
    start = time.time()
    result: dict = {
        "question": question,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "answer_text": None,
        "sources_count": 0,
        "screenshot": None,
        "url": None,
        "duration_seconds": None,
        "error": None,
    }

    with sync_playwright() as p:
        # launch_persistent_context 复用用户 Chrome session（cookies / Google 登录）
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir=chrome_profile,
                headless=headless,
                channel="chrome",  # 用真 Chrome 而不是下载的 chromium（cookies 来源）
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            )
        except Exception as e:
            result["error"] = (
                f"无法启动 Chrome（profile 可能被占用）: {type(e).__name__}: {e}"
                "\n如果 Chrome 已打开，请先关掉，或用 cp 复制一份独立 profile："
                "\n  mkdir -p ~/.gfinance-chrome-profile && "
                f"cp -R '{chrome_profile}/Default'/* ~/.gfinance-chrome-profile/"
                "\n然后 --chrome-profile ~/.gfinance-chrome-profile 跑本脚本。"
            )
            result["duration_seconds"] = round(time.time() - start, 1)
            return result

        page = None
        try:
            page = context.new_page()
            page.goto(
                GFINANCE_URL,
                wait_until="domcontentloaded",
                timeout=timeout_ms,
            )
            result["url"] = page.url
            try:
                result["page_title"] = page.title()
            except Exception:
                pass

            # 先等一下让 JS 渲染
            time.sleep(3)

            # 验证已登录（检查右上角是否有 Sign in 链接）
            try:
                signin_count = page.locator('a:has-text("Sign in"), a:has-text("登录")').count()
                avatar_count = page.locator('a[aria-label*="Google 账号"], a[aria-label*="Google Account"], img[alt*="Profile"]').count()
                result["debug_login_state"] = {
                    "signin_button_count": signin_count,
                    "avatar_count": avatar_count,
                }
                if signin_count > 0 and avatar_count == 0:
                    result["error"] = (
                        "未登录 Google 账号（右上角显示 Sign in 按钮）。"
                        "排查：① 确认 --chrome-profile 指向的 Default 子目录里有 Cookies 文件 "
                        "② 该 Chrome profile 是不是 curarpikt00@gmail.com 那个 "
                        "③ Google session 可能过期，需手动重新登录一次。"
                    )
                    return result
            except Exception as e:
                result.setdefault("warnings", []).append(f"login check failed: {e}")

            if "accounts.google.com" in page.url or "signin" in page.url.lower():
                result["error"] = "页面跳到了 Google 登录页 — cookies 无效或过期"
                return result

            # ⚠️ 关键步骤（2026-05-29 实测）：URL /beta 只是页面外观，
            # 真正激活 AI 研究面板需要手动点右上角"Beta 版"toggle。
            # 幂等：若已在 Beta 状态（有 ✓ 标记）则不重复点。
            try:
                # 先看当前 Beta toggle 状态
                beta_toggle_candidates = [
                    'button:has-text("Beta 版")',
                    'a:has-text("Beta 版")',
                    '[role="button"]:has-text("Beta")',
                    'button:has-text("Beta")',
                ]
                beta_clicked = False
                already_beta = False
                for sel in beta_toggle_candidates:
                    try:
                        beta_elem = page.locator(sel).first
                        if not beta_elem.is_visible(timeout=1500):
                            continue
                        # 检查是否已是 Beta 状态：文本里有 ✓，或 aria-pressed=true，或父元素 selected
                        elem_text = beta_elem.inner_text()
                        aria_pressed = beta_elem.get_attribute("aria-pressed") or ""
                        aria_selected = beta_elem.get_attribute("aria-selected") or ""
                        if "✓" in elem_text or "✔" in elem_text or aria_pressed == "true" or aria_selected == "true":
                            already_beta = True
                            result["debug_beta_state"] = f"already beta (text='{elem_text}', aria_pressed={aria_pressed})"
                            break
                        # 没标记，需要点
                        beta_elem.click()
                        beta_clicked = True
                        result["debug_beta_state"] = f"clicked Beta toggle via {sel}"
                        time.sleep(2)  # 等切换完成
                        break
                    except PlaywrightTimeout:
                        continue
                    except Exception as e:
                        result.setdefault("warnings", []).append(f"beta toggle candidate {sel}: {e}")
                        continue
                if not beta_clicked and not already_beta:
                    result.setdefault("warnings", []).append(
                        "找不到 Beta 版 toggle 按钮 — 可能 URL /beta 已经直接进入 Beta，或 toggle 文本变了"
                    )
            except Exception as e:
                result.setdefault("warnings", []).append(f"beta toggle 处理异常: {e}")

            # 找右侧"研究"输入框
            # ⚠️ selector 是初版猜测，Google 改版可能失效——失败时输出 debug_inputs 看实际 DOM
            candidate_selectors = [
                'textarea[placeholder*="提出任何问题"]',
                'textarea[aria-label*="提出"]',
                'input[placeholder*="提出任何问题"]',
                'textarea[placeholder*="Ask"]',
                'textarea[aria-label*="Research"]',
                'textarea[aria-label*="Ask"]',
                'div[contenteditable="true"]',
                '[role="textbox"]',
                '[role="searchbox"]',
            ]
            input_box = None
            for sel in candidate_selectors:
                loc = page.locator(sel).first
                try:
                    loc.wait_for(timeout=3_000, state="visible")
                    input_box = loc
                    result["debug_selector_used"] = sel
                    break
                except PlaywrightTimeout:
                    continue

            if input_box is None:
                # Dump 所有 textarea / input / 可编辑元素，看 Google 实际用了什么 selector
                debug_inputs = []
                for sel in [
                    'textarea', 'input[type="text"]', 'input:not([type])',
                    '[role="textbox"]', '[role="searchbox"]',
                    'div[contenteditable="true"]', 'div[contenteditable=""]',
                ]:
                    try:
                        locs = page.locator(sel)
                        n = locs.count()
                        for i in range(min(n, 10)):
                            try:
                                elem = locs.nth(i)
                                debug_inputs.append({
                                    "selector": sel,
                                    "index": i,
                                    "placeholder": elem.get_attribute("placeholder"),
                                    "aria_label": elem.get_attribute("aria-label"),
                                    "name": elem.get_attribute("name"),
                                    "role": elem.get_attribute("role"),
                                    "visible": elem.is_visible(),
                                })
                            except Exception:
                                pass
                    except Exception:
                        pass
                result["debug_inputs"] = debug_inputs
                result["error"] = (
                    "找不到「研究」输入框。看 debug_inputs 字段列的所有 input/textarea，"
                    "找哪个对应右侧'提出任何问题'输入框，把它的 selector 反馈给 Cowork。"
                )
                return result

            input_box.click()
            input_box.fill(question)
            time.sleep(0.5)  # 让填字稳定

            # ⚠️ 这是 Gemini chat 风格 UI，Enter 通常是换行不是提交。
            # 必须点右下角的 send 按钮（一般是向上箭头图标）。
            # 策略：先找输入框附近的 send 按钮，再退到全页找。

            send_button = None
            send_button_method = None

            # 1) 先找输入框父容器里的按钮（form 或最近的 div）
            try:
                # input_box 周围的容器
                container = input_box.locator(
                    'xpath=ancestor::*[self::form or self::div][1]'
                ).first
                near_btns = container.locator('button')
                btn_count = near_btns.count()
                # 找最像 send 的：有 aria-label 含发送/提交/send/submit/搜索 的优先；
                # 没有就选最后一个 button（一般 send 在最右边）
                for i in range(btn_count):
                    b = near_btns.nth(i)
                    try:
                        aria = (b.get_attribute("aria-label") or "").lower()
                        if any(kw in aria for kw in ["发送", "send", "提交", "submit", "搜索", "search", "询问", "ask"]):
                            send_button = b
                            send_button_method = f"container button[{i}] aria='{aria}'"
                            break
                    except Exception:
                        continue
                if send_button is None and btn_count > 0:
                    send_button = near_btns.nth(btn_count - 1)
                    send_button_method = f"container last button[{btn_count-1}]"
            except Exception as e:
                result.setdefault("warnings", []).append(f"container button search failed: {e}")

            # 2) 全页找 send 按钮兜底
            if send_button is None:
                for btn_sel in [
                    'button[aria-label*="发送"]', 'button[aria-label*="Send"]',
                    'button[aria-label*="提交"]', 'button[aria-label*="Submit"]',
                    'button[aria-label*="询问"]', 'button[aria-label*="搜索"]',
                    'button[aria-label*="Ask"]', 'button[aria-label*="Search"]',
                    '[role="button"][aria-label*="发送"]',
                    'button:has(svg[aria-label*="arrow_upward"])',
                    'button[type="submit"]',
                ]:
                    try:
                        btn = page.locator(btn_sel).first
                        btn.wait_for(timeout=1500, state="visible")
                        send_button = btn
                        send_button_method = btn_sel
                        break
                    except PlaywrightTimeout:
                        continue
                    except Exception:
                        continue

            # 3) 点 send button；如果还找不到才退到 Enter
            submit_success = False
            if send_button is not None:
                try:
                    send_button.click()
                    submit_success = True
                    result["debug_submit_method"] = f"button click: {send_button_method}"
                except Exception as e:
                    result.setdefault("warnings", []).append(f"send button click failed: {e}")

            if not submit_success:
                try:
                    input_box.press("Enter")
                    submit_success = True
                    result["debug_submit_method"] = "Enter (fallback)"
                except Exception:
                    pass

            if not submit_success:
                result["error"] = "send 按钮和 Enter 都失败"
                return result

            # 检测页面转场：欢迎页消失 / 输入框被清空 / URL 变 / 新内容出现
            # 等最多 10 秒
            transition_detected = False
            for _ in range(20):
                try:
                    welcome_visible = page.locator(
                        ':text("您可以向我咨询"), :text("您可以向我提出")'
                    ).first.is_visible(timeout=500)
                except Exception:
                    welcome_visible = False
                try:
                    current_input = input_box.input_value() if input_box else ""
                except Exception:
                    current_input = ""
                if not welcome_visible or (current_input == "" and question != ""):
                    transition_detected = True
                    break
                time.sleep(0.5)
            result["debug_transition_detected"] = transition_detected
            if not transition_detected:
                result.setdefault("warnings", []).append(
                    "等了 10s 没看到页面转场 —— 提交可能没生效，但继续尝试读答案"
                )

            # ⚠️ 关键步骤（2026-05-29 实测）：研究面板默认是右侧窄栏，
            # AI 答案被挤在一起 Hermes 难抓。点右上角"展开"按钮把面板放大成全屏视图。
            # 幂等：尝试找展开按钮，找不到就跳过（已展开或 UI 变）
            try:
                expand_candidates = [
                    'button:has-text("展开")',  # v7: 文本匹配（图标 ligature 是 expand_content）
                    'button[aria-label*="展开"]',
                    'button[aria-label*="放大"]',
                    'button[aria-label*="全屏"]',
                    'button[aria-label*="Expand"]',
                    'button[aria-label*="Fullscreen"]',
                    'button[aria-label*="Maximize"]',
                    'button[aria-label*="Full screen"]',
                    'button[aria-label*="enlarge"]',
                    'button:has-text("expand_content")',  # 图标 ligature
                ]
                expand_clicked = False
                for sel in expand_candidates:
                    try:
                        btn = page.locator(sel).first
                        if not btn.is_visible(timeout=1500):
                            continue
                        btn.click()
                        expand_clicked = True
                        result["debug_expand_method"] = sel
                        time.sleep(2)  # 等动画完成
                        break
                    except PlaywrightTimeout:
                        continue
                    except Exception:
                        continue
                if not expand_clicked:
                    result.setdefault("warnings", []).append(
                        "找不到 '展开' 按钮 —— 答案可能被挤在小面板里。"
                    )
                    result["debug_expand_method"] = "not found"
                else:
                    # 展开后再等一下确保 DOM 渲染完
                    time.sleep(1.5)
            except Exception as e:
                result.setdefault("warnings", []).append(f"展开按钮处理异常: {e}")

            # v7: 智能定位答案 region——找含用户问题文本的 [role="region"]
            # 实测 2026-05-29：Google Finance Beta 把答案放在右侧 [role="region"][1]，
            # 该 region 同时含问题原文 + "N 个网站" 引用计数 + 答案正文
            import re as _re

            def find_answer_region(_page, q, min_content_chars=50):
                """找含用户问题且有最多正文的 [role='region']"""
                regions = _page.locator('[role="region"]')
                cands = []
                for i in range(regions.count()):
                    try:
                        elem = regions.nth(i)
                        txt = elem.inner_text()
                        # 必须含问题前缀
                        if q[:15] not in txt:
                            continue
                        # 跳过太短（仅有问题没答案）
                        if len(txt) < min_content_chars:
                            continue
                        cands.append((len(txt), i, elem))
                    except Exception:
                        continue
                if not cands:
                    return None, None
                cands.sort(key=lambda x: -x[0])
                return cands[0][2], cands[0][1]

            # 重试：AI 可能还在生成，等几次
            answer_locator, answer_region_idx = None, None
            for delay in [0, 2, 3, 5, 5, 5]:  # 累计最多等 20 秒
                if delay > 0:
                    time.sleep(delay)
                answer_locator, answer_region_idx = find_answer_region(page, question, min_content_chars=80)
                if answer_locator is not None:
                    break
            result["debug_find_answer_total_wait"] = sum([0, 2, 3, 5, 5, 5][: ([0, 2, 3, 5, 5, 5].index(delay) + 1) if answer_locator else 6])
            if answer_locator is not None:
                result["debug_answer_selector"] = f'[role="region"][{answer_region_idx}] (smart)'
            else:
                # 兜底：旧的 selector 列表
                answer_candidates = [
                    '[role="article"]',
                    '[data-research-answer]',
                    '.research-answer',
                    '[aria-live="polite"]',
                    '[aria-live="assertive"]',
                    'div[data-message-id]',
                    'main [role="region"]',
                ]
                for sel in answer_candidates:
                    loc = page.locator(sel).last
                    try:
                        loc.wait_for(timeout=timeout_ms // len(answer_candidates), state="visible")
                        answer_locator = loc
                        result["debug_answer_selector"] = f"{sel} (fallback)"
                        break
                    except PlaywrightTimeout:
                        continue

            if answer_locator is None:
                result["error"] = "无法定位答案 region（智能 + 旧 fallback 都失败）"
                return result

            # 轮询直到答案稳定 —— 关键：检测内容停止变化才认为生成完毕
            # 最多等 max_wait 秒；每 2 秒读一次；若 stable_threshold 秒无变化就退出
            max_wait_seconds = 60
            poll_interval = 2
            stable_threshold = 6
            last_text = ""
            stable_seconds = 0
            elapsed = 0
            text_history = []
            while elapsed < max_wait_seconds:
                try:
                    current_text = answer_locator.inner_text()
                except Exception:
                    current_text = ""
                text_history.append({"t": elapsed, "len": len(current_text), "head": current_text[:60]})
                if current_text == last_text and len(current_text) > 10:
                    stable_seconds += poll_interval
                    if stable_seconds >= stable_threshold:
                        break
                else:
                    stable_seconds = 0
                    last_text = current_text
                time.sleep(poll_interval)
                elapsed += poll_interval

            result["debug_text_history"] = text_history[-10:]  # 末 10 个采样
            result["debug_elapsed_for_answer"] = elapsed

            try:
                raw_text = answer_locator.inner_text()
                # v7: 清洗答案——去掉 UI 噪音、提取 sources_count
                # Material Symbols 图标 ligature 在 inner_text 里以"图标名字"出现，需要剥掉

                _UI_NOISE = {
                    'link', 'expand_content', 'collapse_content', 'edit_square',
                    'notes_spark', 'prompt_suggestion', 'open_in_new',
                    'arrow_upward', 'arrow_downward', 'arrow_forward', 'arrow_back',
                    '展开', '收起', '发起新消息串', '会话历史记录', '新建列表',
                    '研究',
                }
                _DATE_RE = _re.compile(r'^[A-Z][a-z]+ \d+, \d+:\d+ [AP]M$')
                _SRC_RE = _re.compile(r'^(\d+)\s*个(网站|网页)$')

                # 提取 sources count
                sources_found = 0
                m = _re.search(r'(\d+)\s*个(网站|网页)', raw_text)
                if m:
                    sources_found = int(m.group(1))

                # 找用户问题位置，从问题之后开始才是真答案
                q_idx = raw_text.find(question)
                body = raw_text[q_idx + len(question):] if q_idx != -1 else raw_text

                cleaned_lines = []
                for line in body.split('\n'):
                    l = line.strip()
                    if not l:
                        continue
                    if l in _UI_NOISE:
                        continue
                    if _DATE_RE.match(l):
                        continue
                    if _SRC_RE.match(l):
                        continue
                    cleaned_lines.append(l)
                cleaned = '\n'.join(cleaned_lines).strip()

                # 占位文字检测——清洗后如果还是空或就是占位，仍算失败
                if not cleaned or cleaned in ("已就绪", "Ready", "ready"):
                    result["error"] = (
                        f"清洗后答案为空。raw_text 前 300 字：{raw_text[:300]!r}"
                    )
                    result["debug_raw_answer_head"] = raw_text[:500]
                else:
                    result["answer_text"] = cleaned
                    result["sources_count"] = sources_found
                    result["debug_raw_answer_len"] = len(raw_text)
                    result["debug_cleaned_answer_len"] = len(cleaned)
            except Exception as e:
                result["error"] = f"读取/清洗答案失败: {e}"

            # 数引用源
            try:
                sources = page.locator('a[data-source], [data-research-source], .citation, a[href*="ref"]')
                result["sources_count"] = sources.count()
            except Exception:
                pass

            if screenshot_path:
                try:
                    page.screenshot(path=screenshot_path, full_page=False)
                    result["screenshot"] = screenshot_path
                except Exception as e:
                    # 不致命，截图失败不影响主结果
                    result.setdefault("warnings", []).append(f"screenshot failed: {e}")

        except PlaywrightTimeout as e:
            result["error"] = f"timeout: {e}"
        except Exception as e:
            result["error"] = f"{type(e).__name__}: {e}"
        finally:
            # 始终尝试截图 —— 即使失败也能看页面状态
            if screenshot_path and page is not None and result.get("screenshot") is None:
                try:
                    page.screenshot(path=screenshot_path, full_page=True)
                    result["screenshot"] = screenshot_path
                except Exception as e:
                    result.setdefault("warnings", []).append(f"screenshot (final) failed: {e}")
            try:
                context.close()
            except Exception:
                pass

    result["duration_seconds"] = round(time.time() - start, 1)
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Google Finance Beta 研究 AI 二次验证抓取",
    )
    parser.add_argument("question", help="要问 Google Finance 研究 AI 的问题（中文/英文均可）")
    parser.add_argument("--screenshot", help="截图保存路径（可选）", default=None)
    parser.add_argument(
        "--chrome-profile",
        help="Chrome user data dir（默认 ~/Library/Application Support/Google/Chrome）",
        default=DEFAULT_CHROME_PROFILE,
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=60_000,
        help="单步超时毫秒数（默认 60000）",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="跑 headless 模式（默认 headful，更不容易被 Google 拦截）",
    )
    args = parser.parse_args()

    result = fetch(
        question=args.question,
        screenshot_path=args.screenshot,
        chrome_profile=args.chrome_profile,
        timeout_ms=args.timeout_ms,
        headless=args.headless,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("answer_text") and not result.get("error") else 2)


if __name__ == "__main__":
    main()
