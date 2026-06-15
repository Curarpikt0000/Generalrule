# BaseScraper 基类说明

`scripts/wechat_scraper.py` 引用了 `from base import BaseScraper`。
BaseScraper 是一个轻量 Python 工具基类，内置于 webworms skill 框架中（webworms 自己有实现，但 Hermes 等 agent 用终端直接调 requests 时不需要导入）。

**安装 webworms 后 BaseScraper 的位置：**
- Hermes: `~/.hermes/skills/research/webworms/`（但当前版本 BaseScraper 未单独打包为 .py 文件——agent 解析 SKILL.md 后在终端中直接调用代码，不需要此 import）
- 其他 agent（Antigravity / Claude Code）：解析 SKILL.md 中的代码片段直接使用，不依赖 BaseScraper import

**BaseScraper 的行为（在 SKILL.md 中已描述）：**
- `self.can_fetch(url)` — 自动检查 robots.txt
- `self.get(url)` — 内置 2s 频率限制 + 3 次自动重试
- 继承自 `BaseScraper` 的子类只用手动实现 `fetch()` 方法

**如果其他 agent 需要完整的 BaseScraper 实现：**

建议直接用 SKILL.md 中描述的方式在代码中内联实现，或参考下述最小实现：

```python
import requests
import time
import logging
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class BaseScraper:
    """Minimal BaseScraper implementation for standalone use."""

    def __init__(self, name: str = "scraper", base_url: str = None,
                 user_agent: str = "Mozilla/5.0 (compatible; webworms/1.0)"):
        self.name = name
        self.base_url = base_url
        self.user_agent = user_agent
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self._last_request = 0.0
        self._rp = None
        if base_url:
            self._rp = RobotFileParser()
            self._rp.set_url(f"{base_url}/robots.txt")
            try:
                self._rp.read()
            except Exception:
                self._rp = None

    def can_fetch(self, url: str) -> bool:
        if self._rp is None:
            return True
        return self._rp.can_fetch(self.user_agent, url)

    def get(self, url: str, **kwargs) -> requests.Response | None:
        if not self.can_fetch(url):
            logger.warning(f"robots.txt disallows: {url}")
            return None
        # Rate limit: 2s minimum between requests
        elapsed = time.time() - self._last_request
        if elapsed < 2.0:
            time.sleep(2.0 - elapsed)
        for attempt in range(3):
            try:
                resp = self.session.get(url, timeout=30, **kwargs)
                resp.raise_for_status()
                self._last_request = time.time()
                return resp
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt+1}/3 failed: {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)
        return None

    def fetch(self) -> list[dict]:
        raise NotImplementedError
```
