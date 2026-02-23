"""中华医学会皮肤性病学分会 抓取"""

import logging
from typing import List

from bs4 import BeautifulSoup

from .base import Article, BaseSource

logger = logging.getLogger(__name__)


class ChineseDermSource(BaseSource):
    """中华医学会皮肤性病学分会"""

    DEFAULT_URL = "https://www.csdcma.com/"

    @property
    def name(self) -> str:
        return "中华医学会皮肤性病学分会"

    @property
    def category(self) -> str:
        return "指南更新"

    def fetch(self) -> List[Article]:
        url = self.config.get("url", self.DEFAULT_URL)
        logger.info(f"[{self.name}] 正在抓取: {url}")

        resp = self._get(url)
        resp.encoding = resp.apparent_encoding  # 自动检测中文编码
        soup = BeautifulSoup(resp.text, "lxml")

        articles = []

        # 尝试常见的中文医学网站列表结构
        selectors = [
            "ul.news-list li",
            "div.news-item",
            "div.list-item",
            "ul.article-list li",
            "div.content-list li",
        ]

        items = []
        for selector in selectors:
            items = soup.select(selector)
            if items:
                break

        if not items:
            # 回退: 查找所有含有指南/共识/规范关键词的链接
            keywords = ["指南", "共识", "规范", "标准", "通知", "学术", "会议"]
            links = soup.find_all("a", href=True)
            for link in links:
                text = link.get_text(strip=True)
                if text and len(text) > 5:
                    href = link["href"]
                    full_url = href if href.startswith("http") else f"{url.rstrip('/')}/{href.lstrip('/')}"
                    articles.append(Article(
                        title=text,
                        url=full_url,
                        source=self.name,
                        category=self.category,
                        language="zh",
                    ))
            # 优先返回含关键词的
            keyword_articles = [a for a in articles if any(k in a.title for k in keywords)]
            if keyword_articles:
                return keyword_articles[:self.max_articles]
            return articles[:self.max_articles]

        for item in items[:self.max_articles]:
            link_tag = item.find("a", href=True)
            if not link_tag:
                continue
            title = link_tag.get_text(strip=True)
            href = link_tag["href"]
            full_url = href if href.startswith("http") else f"{url.rstrip('/')}/{href.lstrip('/')}"

            # 尝试提取日期
            date_tag = item.find("span", class_=lambda c: c and "date" in c) if item else None
            date_text = date_tag.get_text(strip=True) if date_tag else ""

            if title:
                articles.append(Article(
                    title=title,
                    url=full_url,
                    source=self.name,
                    category=self.category,
                    summary=date_text,
                    language="zh",
                ))

        return articles
