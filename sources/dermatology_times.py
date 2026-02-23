"""Dermatology Times RSS 抓取"""

from .rss_source import RSSSource


class DermatologyTimesSource(RSSSource):
    """Dermatology Times"""

    def __init__(self, config: dict, global_config: dict):
        super().__init__(
            source_name="Dermatology Times",
            rss_url=config.get("rss_url", "https://www.dermatologytimes.com/rss"),
            config=config,
            global_config=global_config,
            category="行业资讯",
            language="en",
        )
