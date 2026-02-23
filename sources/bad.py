"""BAD (英国皮肤科协会) 指南抓取"""

import logging
from typing import List

from bs4 import BeautifulSoup

from .base import Article, BaseSource

logger = logging.getLogger(__name__)


class BADSource(BaseSource):
    """BAD 临床指南"""

    DEFAULT_URL = "https://www.bad.org.uk/clinical-standards/clinical-guidelines"

    @property
    def name(self) -> str:
        return "BAD (英国皮肤科协会)"

    @property
    def category(self) -> str:
        return "指南更新"

    def fetch(self) -> List[Article]:
        url = self.config.get("url", self.DEFAULT_URL)
        logger.info(f"[{self.name}] 正在抓取: {url}")

        resp = self._get(url)
        soup = BeautifulSoup(resp.text, "lxml")

        articles = []

        # BAD 指南页面选择器
        selectors = [
            "div.guideline-card",
            "div.card",
            "li.guideline-item",
            "div.content-item",
            "article",
        ]

        items = []
        for selector in selectors:
            items = soup.select(selector)
            if items:
                break

        if not items:
            # 回退: 查找指南相关链接
            links = soup.find_all("a", href=True)
            for link in links:
                href = link["href"]
                text = link.get_text(strip=True)
                if text and len(text) > 10 and (
                    "guideline" in href.lower() or
                    "guideline" in text.lower() or
                    "/clinical-standards/" in href.lower()
                ):
                    full_url = href if href.startswith("http") else f"https://www.bad.org.uk{href}"
                    articles.append(Article(
                        title=text,
                        url=full_url,
                        source=self.name,
                        category=self.category,
                        language="en",
                    ))
            return articles[:self.max_articles]

        for item in items[:self.max_articles]:
            link_tag = item.find("a", href=True)
            if not link_tag:
                continue

            title = link_tag.get_text(strip=True)
            href = link_tag["href"]
            full_url = href if href.startswith("http") else f"https://www.bad.org.uk{href}"

            summary_tag = item.find("p")
            summary = summary_tag.get_text(strip=True)[:300] if summary_tag else ""

            if title:
                articles.append(Article(
                    title=title,
                    url=full_url,
                    source=self.name,
                    category=self.category,
                    summary=summary,
                    language="en",
                ))

        return articles
