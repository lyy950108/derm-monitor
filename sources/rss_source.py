"""通用 RSS 抓取器"""

import logging
from datetime import datetime
from typing import List

import feedparser

from .base import Article, BaseSource

logger = logging.getLogger(__name__)


class RSSSource(BaseSource):
    """通用 RSS 信息源"""

    def __init__(self, source_name: str, rss_url: str,
                 config: dict, global_config: dict,
                 category: str = "行业资讯", language: str = "en"):
        super().__init__(config, global_config)
        self._name = source_name
        self.rss_url = rss_url
        self._category = category
        self._language = language

    @property
    def name(self) -> str:
        return self._name

    @property
    def category(self) -> str:
        return self._category

    def fetch(self) -> List[Article]:
        logger.info(f"[{self.name}] 正在抓取 RSS: {self.rss_url}")
        feed = feedparser.parse(self.rss_url)

        if feed.bozo and not feed.entries:
            logger.warning(f"[{self.name}] RSS 解析异常: {feed.bozo_exception}")
            return []

        articles = []
        for entry in feed.entries[:self.max_articles]:
            pub_date = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    pub_date = datetime(*entry.published_parsed[:6])
                except (TypeError, ValueError):
                    pass

            summary = ""
            if hasattr(entry, "summary"):
                # 去除 HTML 标签的简易方式
                import re
                summary = re.sub(r"<[^>]+>", "", entry.summary or "")[:300]

            articles.append(Article(
                title=entry.get("title", "无标题"),
                url=entry.get("link", ""),
                source=self.name,
                category=self._category,
                summary=summary,
                pub_date=pub_date,
                language=self._language,
            ))

        return articles
