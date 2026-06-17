"""
WeChat article scraper using webworms BaseScraper + browser for image extraction.
"""
import json
import logging
import os
import tempfile
from base import BaseScraper

logger = logging.getLogger(__name__)


class WeChatImageScraper(BaseScraper):
    """
    Scraper for WeChat image-only articles.
    Uses browser to bypass WeChat auth wall, extracts image data-src URLs,
    then downloads them.

    Since WeChat blocks requests-based access, use this with a browser
    to get the `data-src` URLs first, then pass them to this scraper
    for batch download.
    """

    def __init__(self, output_dir: str | None = None, **kwargs):
        super().__init__(**kwargs)
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix='wechat_imgs_')
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def fetch_images(self, image_urls: list[str]) -> list[dict]:
        """Download images and return metadata."""
        results = []
        for i, url in enumerate(image_urls):
            resp = self.get(url)
            if resp and len(resp.content) > 5000:
                img_path = os.path.join(self.output_dir, f'img_{i:02d}.jpg')
                results.append({
                    'index': i,
                    'url': url,
                    'size_kb': len(resp.content) // 1024,
                    'path': img_path,
                })
                with open(img_path, 'wb') as f:
                    f.write(resp.content)
        return results


# Usage example:
# 1. Use browser to extract URLs:
#    browser_console -> document.querySelectorAll('#js_content img[data-src]')
# 2. Pass to scraper:
#    scraper = WeChatImageScraper(name="wechat", base_url="https://mp.weixin.qq.com")
#    images = scraper.fetch_images(urls)
#    print(f"Downloaded {len(images)} images")
