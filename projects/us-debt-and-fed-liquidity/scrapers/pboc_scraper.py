"""
PBoC 公开市场操作 + 货币政策抓取。

PBoC 官网是静态 HTML（GBK 编码），无 JS 渲染。
注意：response.encoding 必须手动设 'gbk'，否则解析乱码。

主要源：
- 公开市场业务交易公告列表：http://www.pbc.gov.cn/zhengcehuobisi/125207/125213/125431/125475/index.html
- 货币政策司新闻：http://www.pbc.gov.cn/goutongjiaoliu/113456/113469/index.html

L-2026-06-02：已修正 URL 指向正确的 OMO 交易公告页面。
GBK 编码产出的乱码文本中汉字不可直接匹配，改用数字模式提取。
"""
import re
import requests
from datetime import date
from typing import Optional

from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
}

PBOC_OMO_LIST_URL = "http://www.pbc.gov.cn/zhengcehuobisi/125207/125213/125431/125475/index.html"
PBOC_OMO_BASE = "http://www.pbc.gov.cn/zhengcehuobisi/125207/125213/125431/125475"


def _fetch_gbk(url: str, timeout: int = 20) -> BeautifulSoup:
    """GBK 解码 + soup 化。"""
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.encoding = "gbk"
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def fetch_omo_latest() -> Optional[dict]:
    """
    抓取 PBoC 公开市场操作最新交易公告。
    GBK 编码导致汉字乱码，故用数字模式和可打印字符提取。

    Returns:
        {"date", "投放_亿", "到期_亿", "净投放_亿", "利率_pct", "期限", "url"}
    """
    soup = _fetch_gbk(PBOC_OMO_LIST_URL)

    # Find latest OMO announcement link
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        title = a.get_text(strip=True)
        if "/125475/2026" in href and title.strip():
            links.append((href, title))

    if not links:
        return None

    href, _ = links[0]
    if href.startswith("/"):
        full_url = "http://www.pbc.gov.cn" + href
    else:
        full_url = href

    detail_soup = _fetch_gbk(full_url)
    text = detail_soup.get_text(" ", strip=True)

    # Extract OMO amount: num before "浜垮厓" (GBK garbled "亿元")
    投放 = None
    m = re.search(r"(\d+)\s*浜垮厓", text)
    if not m:
        m = re.search(r"(\d+)\s*亿元", text)
    if m:
        投放 = float(m.group(1))

    # Extract rate: table shows "1.40%" literally
    利率 = None
    m = re.search(r"(\d+\.\d+)\s*%", text)
    if m:
        利率 = float(m.group(1))

    # Extract tenor: <number> 天
    期限 = None
    m = re.search(r"(\d+)\s*[天日]", text)
    if m:
        期限 = f"{m.group(1)}D"

    # Extract date from meta: content="2026-06-02"
    日期 = date.today().isoformat()
    m = re.search(r'content="(\d{4}-\d{2}-\d{2})', text)
    if m:
        日期 = m.group(1)

    # Fallback: search in raw HTML
    if 投放 is None:
        html = detail_soup.prettify()
        m = re.search(r"(\d+)\s*亿元", html)
        if m:
            投放 = float(m.group(1))
    if 利率 is None:
        html = detail_soup.prettify()
        m = re.search(r"(\d+\.\d+)\s*%", html)
        if m:
            利率 = float(m.group(1))

    return {
        "date": 日期,
        "投放_亿": 投放 or 0.0,
        "到期_亿": None,
        "净投放_亿": 投放 or 0.0,
        "利率_pct": 利率,
        "期限": 期限 or "7D",
        "url": full_url,
    }


def fetch_dr007() -> Optional[float]:
    """DR007（银行间 7 天回购利率）。返回 None 暂缺。"""
    return None


def fetch_a_share_margin() -> Optional[float]:
    """A 股两融余额（万亿）。返回 None 暂缺。"""
    return None


if __name__ == "__main__":
    import json
    result = fetch_omo_latest()
    print(json.dumps(result, indent=2, ensure_ascii=False))
