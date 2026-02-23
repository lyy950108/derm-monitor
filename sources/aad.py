"""AAD (美国皮肤病学会) 指南抓取"""

import logging
from typing import List

from bs4 import BeautifulSoup

from .base import Article, BaseSource

logger = logging.getLogger(__name__)


class AADSource(BaseSource):
    """AAD 临床指南"""

    DEFAULT_URL = "https://www.aad.org/member/clinical-quality/guidelines"

    @property
    def name(self) -> str:
        return "AAD (美国皮肤病学会)"

    @property
    def category(self) -> str:
        return "指南更新"

    def fetch(self) -> List[Article]:
        url = self.config.get("url", self.DEFAULT_URL)
        logger.info(f"[{self.name}] 正在抓取: {url}")

        resp = self._get(url)
        soup = BeautifulSoup(resp.text, "lxml")

        articles = []

        # AAD 指南页面结构 — 尝试多种选择器以适应页面变化
        selectors = [
            "div.guideline-item",
            "div.content-list-item",
            "li.guideline",
            "div.card",
            "article",
        ]

        items = []
        for selector in selectors:
            items = soup.select(selector)
            if items:
                logger.debug(f"[{self.name}] 使用选择器: {selector}, 找到 {len(items)} 项")
                break

        if not items:
            # 回退: 抓取所有包含 guideline 相关链接的 <a> 标签
            links = soup.find_all("a", href=True)
            for link in links:
                href = link["href"]
                text = link.get_text(strip=True)
                if text and ("guideline" in href.lower() or "guideline" in text.lower()):
                    full_url = href if href.startswith("http") else f"https://www.aad.org{href}"
                    articles.append(Article(
                        title=text,
                        url=full_url,
                        source=self.name,
                        category=self.category,
                        language="en",
                    ))
            return articles[:self.max_articles]

        for item in items[:self.max_articles]:
            # 提取标题和链接
            link_tag = item.find("a", href=True)
            if not link_tag:
                continue

            title = link_tag.get_text(strip=True)
            href = link_tag["href"]
            full_url = href if href.startswith("http") else f"https://www.aad.org{href}"

            # 提取摘要
            summary_tag = item.find("p") or item.find("div", class_="description")
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
