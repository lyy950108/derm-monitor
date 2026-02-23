"""医学界皮肤频道 抓取"""

import logging
from typing import List

from bs4 import BeautifulSoup

from .base import Article, BaseSource

logger = logging.getLogger(__name__)


class YixuejieSource(BaseSource):
    """医学界皮肤频道"""

    DEFAULT_URL = "https://www.medlive.cn/derma/listInfo.html"

    @property
    def name(self) -> str:
        return "医学界皮肤频道"

    @property
    def category(self) -> str:
        return "行业资讯"

    def fetch(self) -> List[Article]:
        url = self.config.get("url", self.DEFAULT_URL)
        logger.info(f"[{self.name}] 正在抓取: {url}")

        resp = self._get(url)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "lxml")

        articles = []

        # 医学界常见列表结构
        selectors = [
            "div.article-list-item",
            "ul.list-group li",
            "div.news-list-item",
            "div.info-list li",
            "div.list-content li",
        ]

        items = []
        for selector in selectors:
            items = soup.select(selector)
            if items:
                break

        if not items:
            # 回退: 提取所有正文区域的链接
            links = soup.find_all("a", href=True)
            for link in links:
                text = link.get_text(strip=True)
                href = link["href"]
                if text and len(text) > 8 and ("derma" in href or "info" in href or "article" in href):
                    full_url = href if href.startswith("http") else f"https://www.medlive.cn{href}"
                    articles.append(Article(
                        title=text,
                        url=full_url,
                        source=self.name,
                        category=self.category,
                        language="zh",
                    ))
            return articles[:self.max_articles]

        for item in items[:self.max_articles]:
            link_tag = item.find("a", href=True)
            if not link_tag:
                continue

            title = link_tag.get_text(strip=True)
            href = link_tag["href"]
            full_url = href if href.startswith("http") else f"https://www.medlive.cn{href}"

            summary_tag = item.find("p", class_="summary") or item.find("p")
            summary = summary_tag.get_text(strip=True)[:300] if summary_tag else ""

            if title:
                articles.append(Article(
                    title=title,
                    url=full_url,
                    source=self.name,
                    category=self.category,
                    summary=summary,
                    language="zh",
                ))

        return articles
