"""Healio Dermatology RSS 抓取"""

from .rss_source import RSSSource


class HealioSource(RSSSource):
    """Healio Dermatology"""

    def __init__(self, config: dict, global_config: dict):
        super().__init__(
            source_name="Healio Dermatology",
            rss_url=config.get("rss_url", "https://www.healio.com/dermatology/rss"),
            config=config,
            global_config=global_config,
            category="行业资讯",
            language="en",
        )
