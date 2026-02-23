"""翻译模块 — 英文标题自动翻译为中文"""

import hashlib
import json
import logging
import random
import time
from typing import List

import requests

from sources.base import Article

logger = logging.getLogger(__name__)


class Translator:
    """翻译器，支持多种后端"""

    def __init__(self, config: dict):
        self.config = config
        self.provider = config.get("provider", "google_free")

    def translate_articles(self, articles: List[Article]) -> List[Article]:
        """翻译所有英文文章的标题"""
        for article in articles:
            if article.language == "en" and article.title:
                try:
                    article.title_zh = self._translate(article.title)
                    time.sleep(0.5)  # 避免频率限制
                except Exception as e:
                    logger.warning(f"翻译失败 [{article.title[:40]}]: {e}")
                    article.title_zh = article.title  # 回退到原文
            elif article.language == "zh":
                article.title_zh = article.title  # 中文文章不需要翻译
        return articles

    def _translate(self, text: str) -> str:
        """根据配置选择翻译后端"""
        if self.provider == "baidu":
            return self._translate_baidu(text)
        elif self.provider == "deepl":
            return self._translate_deepl(text)
        else:
            return self._translate_google_free(text)

    # ---- Google Translate 免费接口 ----
    def _translate_google_free(self, text: str) -> str:
        """
        使用 Google Translate 免费接口。
        注意: 此接口无官方保证，高频使用可能被限制。
        """
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "en",
            "tl": "zh-CN",
            "dt": "t",
            "q": text,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        result = resp.json()

        # 结果格式: [[["翻译结果", "原文", ...], ...], ...]
        translated = ""
        if result and result[0]:
            for segment in result[0]:
                if segment[0]:
                    translated += segment[0]

        return translated or text

    # ---- 百度翻译 API ----
    def _translate_baidu(self, text: str) -> str:
        """百度翻译 API (需要 app_id 和 secret_key)"""
        baidu_cfg = self.config.get("baidu", {})
        app_id = baidu_cfg.get("app_id", "")
        secret_key = baidu_cfg.get("secret_key", "")

        if not app_id or not secret_key:
            logger.error("百度翻译未配置 app_id / secret_key，回退到 Google Free")
            return self._translate_google_free(text)

        salt = str(random.randint(32768, 65536))
        sign_str = f"{app_id}{text}{salt}{secret_key}"
        sign = hashlib.md5(sign_str.encode()).hexdigest()

        url = "https://fanyi-api.baidu.com/api/trans/vip/translate"
        params = {
            "q": text,
            "from": "en",
            "to": "zh",
            "appid": app_id,
            "salt": salt,
            "sign": sign,
        }

        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        result = resp.json()

        if "trans_result" in result:
            return result["trans_result"][0]["dst"]
        else:
            logger.warning(f"百度翻译返回错误: {result}")
            return text

    # ---- DeepL API ----
    def _translate_deepl(self, text: str) -> str:
        """DeepL 翻译 API"""
        deepl_cfg = self.config.get("deepl", {})
        api_key = deepl_cfg.get("api_key", "")

        if not api_key:
            logger.error("DeepL 未配置 api_key，回退到 Google Free")
            return self._translate_google_free(text)

        # 免费版用 api-free.deepl.com，付费版用 api.deepl.com
        base_url = "https://api-free.deepl.com" if api_key.endswith(":fx") else "https://api.deepl.com"
        url = f"{base_url}/v2/translate"

        resp = requests.post(url, data={
            "auth_key": api_key,
            "text": text,
            "source_lang": "EN",
            "target_lang": "ZH",
        }, timeout=10)
        resp.raise_for_status()
        result = resp.json()

        translations = result.get("translations", [])
        if translations:
            return translations[0]["text"]
        return text
