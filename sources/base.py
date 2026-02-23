"""信息源抓取基类"""

import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class Article:
    """统一的文章数据结构"""
    title: str                              # 原始标题
    title_zh: str = ""                      # 中文标题 (翻译后)
    url: str = ""                           # 文章链接
    source: str = ""                        # 来源名称
    category: str = "行业资讯"              # 分类: 指南更新 / 行业资讯 / 微信公众号
    summary: str = ""                       # 摘要
    pub_date: Optional[datetime] = None     # 发布日期
    language: str = "en"                    # 原始语言: en / zh
    tags: List[str] = field(default_factory=list)

    @property
    def unique_id(self) -> str:
        """用于去重的唯一标识"""
        return f"{self.source}::{self.url or self.title}"


class BaseSource(ABC):
    """所有信息源的基类"""

    def __init__(self, config: dict, global_config: dict):
        self.config = config
        self.global_config = global_config
        self.timeout = global_config.get("fetch", {}).get("timeout", 30)
        self.max_articles = global_config.get("fetch", {}).get("max_articles_per_source", 20)
        self.delay = global_config.get("fetch", {}).get("delay_between_requests", 2)
        self.retry_count = global_config.get("fetch", {}).get("retry", 3)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": global_config.get("fetch", {}).get(
                "user_agent",
                "DermMonitor/1.0 (Medical Research Bot)"
            )
        })

    @property
    @abstractmethod
    def name(self) -> str:
        """信息源名称"""
        ...

    @property
    def category(self) -> str:
        return "行业资讯"

    @abstractmethod
    def fetch(self) -> List[Article]:
        """抓取文章列表，子类必须实现"""
        ...

    def _get(self, url: str, **kwargs) -> requests.Response:
        """带重试的 GET 请求"""
        for attempt in range(1, self.retry_count + 1):
            try:
                resp = self.session.get(url, timeout=self.timeout, **kwargs)
                resp.raise_for_status()
                return resp
            except requests.RequestException as e:
                logger.warning(f"[{self.name}] 请求失败 (第{attempt}次): {e}")
                if attempt < self.retry_count:
                    time.sleep(self.delay * attempt)
                else:
                    raise
        raise RuntimeError("Unreachable")

    def safe_fetch(self) -> List[Article]:
        """安全抓取，捕获异常不影响其他源"""
        try:
            articles = self.fetch()
            logger.info(f"[{self.name}] 成功抓取 {len(articles)} 篇文章")
            return articles
        except Exception as e:
            logger.error(f"[{self.name}] 抓取失败: {e}", exc_info=True)
            return []
