"""文章去重存储 — 避免重复推送"""

import json
import logging
import os
from datetime import datetime
from typing import List, Set

from sources.base import Article

logger = logging.getLogger(__name__)


class Storage:
    """基于 JSON 文件的已读文章存储"""

    def __init__(self, config: dict):
        self.db_path = config.get("storage", {}).get("db_path", "data/seen_articles.json")
        self.max_history = config.get("storage", {}).get("max_history", 5000)
        self._seen_ids: Set[str] = set()
        self._load()

    def _load(self):
        """加载已读记录"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._seen_ids = set(data.get("seen_ids", []))
                logger.info(f"已加载 {len(self._seen_ids)} 条历史记录")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"加载历史记录失败: {e}")
                self._seen_ids = set()
        else:
            self._seen_ids = set()

    def _save(self):
        """保存已读记录"""
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)

        # 保留最近的 max_history 条
        seen_list = list(self._seen_ids)
        if len(seen_list) > self.max_history:
            seen_list = seen_list[-self.max_history:]
            self._seen_ids = set(seen_list)

        data = {
            "seen_ids": seen_list,
            "last_updated": datetime.now().isoformat(),
        }
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def filter_new(self, articles: List[Article]) -> List[Article]:
        """过滤出未推送过的新文章"""
        new_articles = []
        for article in articles:
            uid = article.unique_id
            if uid not in self._seen_ids:
                new_articles.append(article)
        logger.info(f"共 {len(articles)} 篇文章，其中 {len(new_articles)} 篇为新文章")
        return new_articles

    def mark_seen(self, articles: List[Article]):
        """标记文章为已推送"""
        for article in articles:
            self._seen_ids.add(article.unique_id)
        self._save()
        logger.info(f"已标记 {len(articles)} 篇文章为已推送")
