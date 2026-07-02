"""
Investing.com 反爬抓取器（JGB / TONAR 备用源）。

策略：
1. User-Agent 池轮换
2. 复用 cookie（首次访问获取，后续带 session）
3. 请求间隔 5-8 秒
4. 失败 raise，由调用方写入 logs/ 并显式失败（遵循 §2.10）
"""
import random
import time
import requests
from typing import Optional

UA_POOL = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
]


class InvestingClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = random.choice(UA_POOL)
        self.session.headers["Accept-Language"] = "en-US,en;q=0.9"

    def fetch_html(self, url: str, *, wait: float = 6.0) -> str:
        time.sleep(wait + random.uniform(0, 2))
        self.session.headers["User-Agent"] = random.choice(UA_POOL)
        r = self.session.get(url, timeout=20)
        if r.status_code == 403:
            raise PermissionError(f"Investing.com 403 — 触发反爬。换 IP 或加长 wait. URL={url}")
        r.raise_for_status()
        return r.text

    def fetch_jgb_yield(self, maturity_y: int) -> Optional[float]:
        """
        抓取日债收益率（备用源）。返回最新值（百分比）。
        优先使用 MoF Japan，此处仅作降级。
        """
        url = f"https://www.investing.com/rates-bonds/japan-{maturity_y}-year-bond-yield"
        html = self.fetch_html(url)
        # 真实场景用 BeautifulSoup 解析 instrument-price-last
        # 这里只给框架，实际解析见 Hermes 运行时
        # import bs4; soup = bs4.BeautifulSoup(html, "html.parser")
        # return float(soup.select_one("[data-test='instrument-price-last']").text.replace(",", ""))
        raise NotImplementedError("由 Hermes 实际运行时填充 BeautifulSoup 解析")


if __name__ == "__main__":
    c = InvestingClient()
    print(c.fetch_jgb_yield(10))
