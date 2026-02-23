"""微信公众号抓取 (通过搜狗微信搜索)"""

import logging
import time
from typing import List

from bs4 import BeautifulSoup

from .base import Article, BaseSource

logger = logging.getLogger(__name__)


class WechatSogouSource(BaseSource):
    """
    通过搜狗微信搜索抓取公众号文章。

    注意事项:
    - 搜狗微信搜索有反爬机制，频繁请求会触发验证码
    - 建议每日仅运行 1-2 次
    - 如被封禁，可手动在浏览器访问搜狗微信搜索获取 Cookie 后填入配置
    - 更稳定的替代方案: 使用 WeRSS 等第三方服务将公众号转为 RSS

    替代方案配置示例 (在 config.yaml 中):
    wechat:
      method: "rss"   # 使用第三方 RSS 服务
      rss_feeds:
        - name: "皮肤科杨希川教授"
          url: "https://werss.app/feeds/xxx"
        - name: "中华皮肤科杂志"
          url: "https://werss.app/feeds/yyy"
    """

    SOGOU_SEARCH_URL = "https://weixin.sogou.com/weixin"

    @property
    def name(self) -> str:
        return "微信公众号"

    @property
    def category(self) -> str:
        return "微信公众号"

    def fetch(self) -> List[Article]:
        accounts = self.config.get("accounts", [])
        if not accounts:
            logger.warning(f"[{self.name}] 未配置公众号列表")
            return []

        all_articles = []

        for account in accounts:
            account_name = account.get("name", "")
            keyword = account.get("keyword", account_name)

            try:
                articles = self._search_account(account_name, keyword)
                all_articles.extend(articles)
            except Exception as e:
                logger.error(f"[{self.name}] 抓取 {account_name} 失败: {e}")

            # 请求间隔，避免触发反爬
            time.sleep(self.delay + 2)

        return all_articles

    def _search_account(self, account_name: str, keyword: str) -> List[Article]:
        """搜索指定公众号的文章"""
        logger.info(f"[{self.name}] 正在搜索公众号: {account_name}")

        params = {
            "type": "2",   # 搜索文章 (type=1 为搜索公众号)
            "query": keyword,
            "ie": "utf8",
            "s_from": "input",
        }

        try:
            resp = self._get(self.SOGOU_SEARCH_URL, params=params)
        except Exception as e:
            logger.warning(f"[{self.name}] 搜狗请求失败 (可能触发反爬): {e}")
            return []

        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")

        articles = []

        # 搜狗微信搜索结果结构
        results = soup.select("div.txt-box") or soup.select("ul.news-list li")

        for item in results[:self.max_articles]:
            link_tag = item.find("a", href=True)
            if not link_tag:
                continue

            title = link_tag.get_text(strip=True)
            url = link_tag["href"]

            # 搜狗返回的链接可能是中间跳转链接
            if not url.startswith("http"):
                url = f"https://weixin.sogou.com{url}"

            # 提取来源公众号名
            source_tag = item.find("a", class_="account") or item.find("span", class_="s-p")
            source_name = source_tag.get_text(strip=True) if source_tag else account_name

            # 提取摘要
            summary_tag = item.find("p", class_="txt-info") or item.find("p")
            summary = summary_tag.get_text(strip=True)[:200] if summary_tag else ""

            if title:
                articles.append(Article(
                    title=title,
                    url=url,
                    source=f"微信公众号 · {source_name}",
                    category=self.category,
                    summary=summary,
                    language="zh",
                ))

        return articles
